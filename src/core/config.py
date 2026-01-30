from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )


class AppSettings(BaseConfig):
    app_title: str = "add_product_to_order"
    app_host: str = "0.0.0.0"
    app_port: int
    app_log_level: str = "info"
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@add_product_to_order_db:5432/postgres",
        env="DATABASE_URL",
    )


settings = AppSettings()
