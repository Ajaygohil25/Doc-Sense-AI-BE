import copy
import uuid
import asyncio

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.testclient import TestClient
from sqlalchemy import select
from app.authentication.hashing import Hash
from app.core.database import TestAsyncSessionLocal, test_engine, Base, get_db
from main import app
from app.models.user_model import User
from test.test_data.user_json_data import user_data_payload
from app.config.env_config import settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Create and manage test database."""
    import app.models.user_model
    import app.models.blacklist_token_model
    import app.models.file_upload_model
    import app.models.password_reset_token_model

    async def create_all():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await create_all()
    try:
        yield
    finally:
        # Drop all tables known to the shared Base on the test engine
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        # Fully dispose connections so nothing lingers
        await test_engine.dispose()


async def override_get_db():
    """Override database dependency for testing."""
    async with TestAsyncSessionLocal() as db:
        yield db


@pytest_asyncio.fixture(scope="session")
async def async_client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module")
async def create_user():
    """Create a test user in the database."""
    async with TestAsyncSessionLocal() as db_session:
        # Check if user already exists
        result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Create new user
        admin_data = copy.deepcopy(user_data_payload)
        admin_data.update({
            "first_name": admin_data.get("first_name") or "ajay",
            "last_name": admin_data.get("last_name") or "admin",
            "email": "admin@test.com",
            "password": Hash.encrypt("Admin@test123"),
        })
        user_data = User(**admin_data)
        db_session.add(user_data)
        await db_session.commit()
        await db_session.refresh(user_data)
        return user_data


@pytest_asyncio.fixture
async def user_token(create_user):
    """Generate a valid JWT token for the test user."""
    import jwt
    import os
    from datetime import datetime, timedelta

    secret_key = settings.HASH_KEY
    algorithm = settings.HASH_ALGO

    # Create token payload
    payload = {
        "sub": create_user.email,
        "user_id": str(create_user.id),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "is_refresh": False
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


@pytest.fixture
def header():
    """Provide a basic header dictionary for requests."""
    return {"Content-Type": "application/json"}