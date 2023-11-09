from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    REDIS_HOST: str
    REDIS_PORT: int
    ACCESS_TOKEN_TTL: int
    REFRESH_TOKEN_TTL: int
    ELASTIC_HOST: str
    ELASTIC_PORT: int

    ACCOUNT_REGISTER_URL: str
    ACCOUNT_LOGIN_URL: str
    NOTIFICATION_CODE_SENDER_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


@lru_cache
def get_settings():
    return settings
