from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    MAIL_FROM: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_FROM_NAME: str
    MAIL_USERNAME: str
    DOMAIN: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CLIENT_ID: str

    model_config = SettingsConfigDict(env_file='.env')


setting = Settings()