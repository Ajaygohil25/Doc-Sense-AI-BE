import asyncio
import os
from logging.config import fileConfig
from alembic import context
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from app.config.env_config import settings
from app.core.database import Base
from app.models.user_model import User
from app.models.blacklist_token_model import BlackListToken
from app.models.password_reset_token_model import PasswordResetTokenModel
from app.models.file_upload_model import FileUploadModel



load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with env variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def get_url() -> str:
    url = settings.DATABASE_URL
    print(">>> Alembic connecting to:", url)
    return url

async def run_migrations_online():
    """Run migrations in 'online' mode with async engine."""
    connectable = create_async_engine(get_url(), future=True, pool_pre_ping=True)

    async with connectable.connect() as connection:

        def do_run_migrations(sync_connection):
            context.configure(
                connection=sync_connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)


def run_async_migrations():
    asyncio.run(run_migrations_online())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_async_migrations()
