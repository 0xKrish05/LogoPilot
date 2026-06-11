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

GRAPH_API = "https://graph.facebook.com/v19.0"
OAUTH_DIALOG = "https://www.facebook.com/v19.0/dialog/oauth"
SCOPES = "instagram_basic,instagram_content_publish,pages_show_list,business_management"


@router.get("/connect")
async def connect_instagram(user: User = Depends(get_current_user)):
    """Returns the Facebook OAuth URL the frontend should redirect the user to."""
    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": SCOPES,
        "response_type": "code",
        "state": str(user.id),
    }
    return {"url": f"{OAUTH_DIALOG}?{urlencode(params)}"}


@router.get("/callback")
async def instagram_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """Meta redirects here after the user approves/denies access."""
    frontend_base = settings.frontend_base_url or "http://15.135.74.108:3000"

    if error or not code or not state:
        return RedirectResponse(f"{frontend_base}/accounts?error=access_denied")

    try:
        user_id = uuid.UUID(state)
    except ValueError:
        return RedirectResponse(f"{frontend_base}/accounts?error=invalid_state")

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for a short-lived user access token.
        token_resp = await client.get(
            f"{GRAPH_API}/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
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
            f"{GRAPH_API}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        long_data = long_resp.json()
        long_token = long_data.get("access_token", short_token)

        # 3. List the user's Facebook Pages.
        pages_resp = await client.get(
            f"{GRAPH_API}/me/accounts",
            params={"access_token": long_token, "fields": "id,name,access_token"},
        )
        pages = pages_resp.json().get("data", [])

        connected = []
        for page in pages:
            page_id = page["id"]
            page_token = page.get("access_token", long_token)

            ig_resp = await client.get(
                f"{GRAPH_API}/{page_id}",
                params={"fields": "instagram_business_account", "access_token": page_token},
            )
            ig_data = ig_resp.json().get("instagram_business_account")
            if not ig_data:
                continue

            ig_user_id = ig_data["id"]

            profile_resp = await client.get(
                f"{GRAPH_API}/{ig_user_id}",
                params={"fields": "username", "access_token": page_token},
            )
            username = profile_resp.json().get("username", ig_user_id)

            connected.append((ig_user_id, username, page_id, page_token))

    if not connected:
        return RedirectResponse(f"{frontend_base}/accounts?error=no_instagram_account")

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

        for ig_user_id, username, page_id, page_token in connected:
            if existing_count >= plan.max_instagram_accounts:
                break

            result = await db.execute(
                select(InstagramAccount).where(
                    InstagramAccount.user_id == user.id,
                    InstagramAccount.ig_user_id == ig_user_id,
                )
            )
            account = result.scalar_one_or_none()
            if account is None:
                account = InstagramAccount(user_id=user.id, ig_user_id=ig_user_id)
                db.add(account)
                existing_count += 1

            account.username = username
            account.facebook_page_id = page_id
            account.access_token_encrypted = encrypt_secret(page_token)
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
