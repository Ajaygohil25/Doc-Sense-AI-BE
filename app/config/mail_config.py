from fastapi_mail import ConnectionConfig
from app.config.env_config import settings


def get_mail_config():
    conf = ConnectionConfig(
        MAIL_USERNAME = settings.MAIL_USERNAME,
        MAIL_PASSWORD = settings.MAIL_PASSWORD,
        MAIL_FROM = settings.MAIL_FROM,
        MAIL_PORT = int(settings.MAIL_PORT),
        MAIL_SERVER = settings.MAIL_SERVER,
        MAIL_STARTTLS = False,
        MAIL_SSL_TLS = True,
        USE_CREDENTIALS = True,
        VALIDATE_CERTS = True,
        TEMPLATE_FOLDER = "app/templates"
    )
    return conf