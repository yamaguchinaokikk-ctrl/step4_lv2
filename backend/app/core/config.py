from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    db_ssl_mode: str = "REQUIRED"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_hours: int = 8

    login_max_failed_attempts: int = 5
    login_lockout_minutes: int = 15

    environment: str = "development"

    @property
    def database_url(self) -> str:
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?ssl_verify_cert=true"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
