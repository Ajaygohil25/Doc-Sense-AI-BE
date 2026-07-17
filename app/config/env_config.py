from pydantic import model_validator
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
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_S3_BUCKET_NAME: str | None = None

    SOCKETIO_CORS_ORIGINS: str = "*"
    SOCKETIO_USE_REDIS: bool = False
    SOCKETIO_REDIS_URL: str = "redis://localhost:6379"
    SOCKETIO_PING_TIMEOUT: int = 25
    SOCKETIO_PING_INTERVAL: int = 5

    @model_validator(mode="after")
    def validate_s3_configuration(self):
        if not self.IS_ON_S3:
            return self

        required_settings = ("AWS_REGION", "AWS_S3_BUCKET_NAME")
        missing_settings = [
            setting_name
            for setting_name in required_settings
            if not getattr(self, setting_name)
        ]
        if missing_settings:
            raise ValueError(
                f"S3 storage requires: {', '.join(missing_settings)}"
            )

        has_access_key = bool(self.AWS_ACCESS_KEY_ID)
        has_secret_key = bool(self.AWS_SECRET_ACCESS_KEY)
        if has_access_key != has_secret_key:
            raise ValueError(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be provided together"
            )

        return self

    class Config:
        env_file = ".env"


settings = Settings()
