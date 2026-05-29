from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_NAME: str
    TEST_DATABASE_URL: str

    SIGN_IN_URL: str
    HASH_KEY: str
    HASH_ALGO: str
    ACCESS_TOKEN_EXPIRE_TIME: str
    REFRESH_TOKEN_EXPIRE_TIME: str
    RESET_TOKEN_EXPIRE_MINUTES: str
    RESET_TOKEN_SECRET_KEY: str
    FORGOT_PASSWORD_URL: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: str
    MAIL_SERVER: str

    HUGGING_FACE_HUB_API_TOKEN: str

    IS_ON_S3: bool

    SOCKETIO_CORS_ORIGINS: str = "*"
    SOCKETIO_USE_REDIS: bool = False
    SOCKETIO_REDIS_URL: str = "redis://localhost:6379"
    SOCKETIO_PING_TIMEOUT: int = 25
    SOCKETIO_PING_INTERVAL: int = 5

    class Config:
        env_file = ".env"


settings = Settings()