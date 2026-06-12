import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import settings

_app = None


def normalize_private_key(key: str) -> str:
    # env-file round-trips can escape "\n" into "\\n" (or deeper); collapse
    # any run of backslashes before an "n" back into a real newline
    key = key.replace("\r\n", "\n")
    while "\\\\n" in key:
        key = key.replace("\\\\n", "\\n")
    return key.replace("\\n", "\n")


def get_firebase_app():
    global _app
    if _app is None:
        cred = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "private_key": normalize_private_key(settings.firebase_private_key),
                "client_email": settings.firebase_client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
        _app = firebase_admin.initialize_app(cred)
    return _app


def verify_id_token(id_token: str) -> dict:
    """Verifies a Firebase ID token from the frontend Google Sign-In flow.
    Returns the decoded token containing at least 'uid' and 'email'."""
    get_firebase_app()
    return auth.verify_id_token(id_token)
