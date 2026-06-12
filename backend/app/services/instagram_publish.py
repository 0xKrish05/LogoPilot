"""Instagram Reels publishing via the Instagram (Login API) Graph endpoints.

Flow (Content Publishing API):
1. POST /{ig_user_id}/media        -> creates a media container from a public
                                      video_url (media_type=REELS).
2. GET  /{container_id}            -> poll status_code until FINISHED.
3. POST /{ig_user_id}/media_publish -> publishes the container.
4. GET  /{media_id}?fields=permalink -> the final reel URL stored on the item.

Requires an Instagram Professional/Business account connected via OAuth with
the instagram_business_content_publish scope (see api/routes/instagram.py).
"""

import time

import httpx

IG_GRAPH_API = "https://graph.instagram.com/v21.0"

CONTAINER_POLL_INTERVAL_SECONDS = 10
CONTAINER_TIMEOUT_SECONDS = 600  # IG video processing can take a few minutes


class InstagramPublishError(RuntimeError):
    pass


def _error_message(data: dict) -> str:
    err = data.get("error") or {}
    return err.get("error_user_msg") or err.get("message") or str(data)


def publish_reel(
    ig_user_id: str,
    access_token: str,
    video_url: str,
    caption: str | None = None,
    cover_url: str | None = None,
) -> tuple[str, str]:
    """Publishes a reel and returns (media_id, permalink)."""
    with httpx.Client(timeout=60) as client:
        params: dict = {
            "media_type": "REELS",
            "video_url": video_url,
            "access_token": access_token,
        }
        if caption:
            params["caption"] = caption
        if cover_url:
            params["cover_url"] = cover_url

        resp = client.post(f"{IG_GRAPH_API}/{ig_user_id}/media", params=params)
        data = resp.json()
        container_id = data.get("id")
        if not container_id:
            raise InstagramPublishError(f"Container creation failed: {_error_message(data)}")

        deadline = time.monotonic() + CONTAINER_TIMEOUT_SECONDS
        while True:
            resp = client.get(
                f"{IG_GRAPH_API}/{container_id}",
                params={"fields": "status_code,status", "access_token": access_token},
            )
            data = resp.json()
            status_code = data.get("status_code")
            if status_code == "FINISHED":
                break
            if status_code in ("ERROR", "EXPIRED"):
                raise InstagramPublishError(
                    f"Container processing failed ({status_code}): {data.get('status') or _error_message(data)}"
                )
            if time.monotonic() > deadline:
                raise InstagramPublishError("Timed out waiting for Instagram to process the video")
            time.sleep(CONTAINER_POLL_INTERVAL_SECONDS)

        resp = client.post(
            f"{IG_GRAPH_API}/{ig_user_id}/media_publish",
            params={"creation_id": container_id, "access_token": access_token},
        )
        data = resp.json()
        media_id = data.get("id")
        if not media_id:
            raise InstagramPublishError(f"Publish failed: {_error_message(data)}")

        resp = client.get(
            f"{IG_GRAPH_API}/{media_id}",
            params={"fields": "permalink", "access_token": access_token},
        )
        permalink = resp.json().get("permalink") or f"https://www.instagram.com/p/{media_id}/"

        return media_id, permalink
