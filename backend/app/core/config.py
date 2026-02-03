from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    cg_db_user: str = "cg_user"
    cg_db_password: str = ""
    cg_db_name: str = "commonground"
    cg_db_host: str = "cg-db"
    cg_db_port: int = 5432

    # Redis
    redis_url: str = "redis://cg-redis:6379/0"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    # Platform
    platform_name: str = "Common Ground"
    platform_url: str = "https://commonground.preview.forge-dev.com"
    environment: str = "development"

    # Council AI Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Founder
    founder_email: str = "founder@commonground.ai"
    founder_handle: str = "jason"

    # Moderation
    auto_mod_spam_threshold: float = 0.85
    flag_threshold_hide: int = 5
    flag_threshold_remove: int = 10

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
