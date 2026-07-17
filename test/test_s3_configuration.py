import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock

from app.config.env_config import Settings
from app.services import s3_service


def make_settings(**overrides) -> Settings:
    values = {
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost/app",
        "DATABASE_USERNAME": "postgres",
        "DATABASE_PASSWORD": "postgres",
        "DATABASE_HOST": "localhost",
        "DATABASE_NAME": "app",
        "TEST_DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost/app_test",
        "SIGN_IN_URL": "http://localhost:5173/login",
        "HASH_KEY": "hash-secret",
        "HASH_ALGO": "HS256",
        "ACCESS_TOKEN_EXPIRE_TIME": "1",
        "REFRESH_TOKEN_EXPIRE_TIME": "24",
        "RESET_TOKEN_EXPIRE_MINUTES": "30",
        "RESET_TOKEN_SECRET_KEY": "reset-secret",
        "FORGOT_PASSWORD_URL": "http://localhost:5173/reset-password?token=",
        "MAIL_USERNAME": "mail-user",
        "MAIL_PASSWORD": "mail-password",
        "MAIL_FROM": "no-reply@example.com",
        "MAIL_PORT": "465",
        "MAIL_SERVER": "smtp.example.com",
        "HUGGING_FACE_HUB_API_TOKEN": "hf-token",
        "IS_ON_S3": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_s3_settings_are_optional_when_s3_is_disabled():
    configured = make_settings()

    assert configured.AWS_ACCESS_KEY_ID is None
    assert configured.AWS_SECRET_ACCESS_KEY is None
    assert configured.AWS_REGION is None
    assert configured.AWS_S3_BUCKET_NAME is None


def test_s3_requires_region_and_bucket_when_enabled():
    with pytest.raises(ValidationError, match="AWS_REGION, AWS_S3_BUCKET_NAME"):
        make_settings(IS_ON_S3=True)


def test_s3_accepts_default_aws_credential_chain():
    configured = make_settings(
        IS_ON_S3=True,
        AWS_REGION="us-east-1",
        AWS_S3_BUCKET_NAME="doc-sense-pdfs",
    )

    assert configured.IS_ON_S3 is True
    assert configured.AWS_ACCESS_KEY_ID is None
    assert configured.AWS_SECRET_ACCESS_KEY is None


def test_s3_requires_access_key_and_secret_as_a_pair():
    with pytest.raises(ValidationError, match="must be provided together"):
        make_settings(
            IS_ON_S3=True,
            AWS_ACCESS_KEY_ID="access-key",
            AWS_REGION="us-east-1",
            AWS_S3_BUCKET_NAME="doc-sense-pdfs",
        )


def test_s3_service_omits_empty_credentials_for_default_credential_chain(monkeypatch):
    boto_client = MagicMock()
    monkeypatch.setattr(s3_service.settings, "AWS_ACCESS_KEY_ID", "")
    monkeypatch.setattr(s3_service.settings, "AWS_SECRET_ACCESS_KEY", "")
    monkeypatch.setattr(s3_service.settings, "AWS_REGION", "us-east-1")
    monkeypatch.setattr(s3_service.settings, "AWS_S3_BUCKET_NAME", "doc-sense-pdfs")
    monkeypatch.setattr(s3_service.boto3, "client", boto_client)

    configured_service = s3_service.S3Service()

    boto_client.assert_called_once_with("s3", region_name="us-east-1")
    assert configured_service.bucket_name == "doc-sense-pdfs"


def test_s3_service_passes_explicit_credential_pair(monkeypatch):
    boto_client = MagicMock()
    monkeypatch.setattr(s3_service.settings, "AWS_ACCESS_KEY_ID", "access-key")
    monkeypatch.setattr(s3_service.settings, "AWS_SECRET_ACCESS_KEY", "secret-key")
    monkeypatch.setattr(s3_service.settings, "AWS_REGION", "us-east-1")
    monkeypatch.setattr(s3_service.settings, "AWS_S3_BUCKET_NAME", "doc-sense-pdfs")
    monkeypatch.setattr(s3_service.boto3, "client", boto_client)

    s3_service.S3Service()

    boto_client.assert_called_once_with(
        "s3",
        aws_access_key_id="access-key",
        aws_secret_access_key="secret-key",
        region_name="us-east-1",
    )
