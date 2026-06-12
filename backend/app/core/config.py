from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    secret_key: str = "changeme"
    master_admin_email: str = ""

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    firebase_project_id: str = ""
    firebase_client_email: str = ""
    firebase_private_key: str = ""

    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = ""
    frontend_base_url: str = ""

    instagram_app_id: str = ""
    instagram_app_secret: str = ""

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    cryptomus_api_key: str = ""
    cryptomus_merchant_id: str = ""
    maxelpay_api_key: str = ""
    maxelpay_secret_key: str = ""

    cookie_encryption_key: str = ""

    temp_storage_path: str = "/tmp/media"


settings = Settings()
