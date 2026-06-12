import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import encrypt_secret
from app.db.session import AsyncSessionLocal, get_db
from app.models.instagram_account import InstagramAccount
from app.models.user import User
from app.services.plan_limits import get_active_plan

router = APIRouter(prefix="/instagram", tags=["instagram"])

IG_OAUTH_DIALOG = "https://www.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
IG_GRAPH_API = "https://graph.instagram.com/v21.0"
SCOPES = (
    "instagram_business_basic,instagram_business_content_publish,"
    "instagram_business_manage_comments,instagram_business_manage_messages"
)


@router.get("/connect")
async def connect_instagram(user: User = Depends(get_current_user)):
    """Returns the Instagram Business Login OAuth URL the frontend should redirect to."""
    params = {
        "client_id": settings.instagram_app_id,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": SCOPES,
        "response_type": "code",
        "state": str(user.id),
    }
    return {"url": f"{IG_OAUTH_DIALOG}?{urlencode(params)}"}


@router.get("/callback")
async def instagram_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """Instagram redirects here after the user approves/denies access."""
    frontend_base = settings.frontend_base_url or "http://15.135.74.108:3000"

    if error or not code or not state:
        return RedirectResponse(f"{frontend_base}/accounts?error=access_denied")

    try:
        user_id = uuid.UUID(state)
    except ValueError:
        return RedirectResponse(f"{frontend_base}/accounts?error=invalid_state")

    # Instagram sometimes appends "#_" to the returned code.
    code = code.rstrip("#_")

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for a short-lived user access token.
        token_resp = await client.post(
            IG_TOKEN_URL,
            data={
                "client_id": settings.instagram_app_id,
                "client_secret": settings.instagram_app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": settings.meta_redirect_uri,
                "code": code,
            },
        )
        token_data = token_resp.json()
        short_token = token_data.get("access_token")
        if not short_token:
            return RedirectResponse(f"{frontend_base}/accounts?error=token_exchange_failed")

        # 2. Exchange for a long-lived token (~60 days).
        long_resp = await client.get(
            f"{IG_GRAPH_API}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.instagram_app_secret,
                "access_token": short_token,
            },
        )
        long_data = long_resp.json()
        long_token = long_data.get("access_token", short_token)
        expires_in = long_data.get("expires_in")

        # 3. Fetch the connected Instagram professional account's profile.
        profile_resp = await client.get(
            f"{IG_GRAPH_API}/me",
            params={"fields": "user_id,username", "access_token": long_token},
        )
        profile = profile_resp.json()
        ig_user_id = profile.get("user_id") or profile.get("id")
        username = profile.get("username")

    if not ig_user_id or not username:
        return RedirectResponse(f"{frontend_base}/accounts?error=no_instagram_account")

    token_expires_at = None
    if expires_in:
        from datetime import datetime, timedelta, timezone

        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return RedirectResponse(f"{frontend_base}/accounts?error=user_not_found")

        plan = await get_active_plan(db, user)
        existing_count = await db.execute(
            select(func.count(InstagramAccount.id)).where(InstagramAccount.user_id == user.id)
        )
        existing_count = existing_count.scalar_one()

        result = await db.execute(
            select(InstagramAccount).where(
                InstagramAccount.user_id == user.id,
                InstagramAccount.ig_user_id == str(ig_user_id),
            )
        )
        account = result.scalar_one_or_none()
        if account is None:
            if existing_count >= plan.max_instagram_accounts:
                return RedirectResponse(f"{frontend_base}/accounts?error=account_limit_reached")
            account = InstagramAccount(user_id=user.id, ig_user_id=str(ig_user_id))
            db.add(account)

        account.username = username
        account.access_token_encrypted = encrypt_secret(long_token)
        account.token_expires_at = token_expires_at
        account.is_active = True

        await db.commit()

    return RedirectResponse(f"{frontend_base}/accounts?connected=1")


@router.get("/accounts")
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InstagramAccount).where(InstagramAccount.user_id == user.id)
    )
    accounts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "ig_user_id": a.ig_user_id,
            "username": a.username,
            "is_active": a.is_active,
            "created_at": a.created_at,
        }
        for a in accounts
    ]


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InstagramAccount).where(
            InstagramAccount.id == account_id, InstagramAccount.user_id == user.id
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    await db.delete(account)
    await db.commit()
