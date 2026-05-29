import os
from unittest.mock import patch

import jwt
import pytest
from dotenv import load_dotenv

from app.core.database import TestAsyncSessionLocal
from app.models.user_model import User
from test.test_data.user_json_data import (
    user_login_payload,
    update_user_payload,
    forget_password_payload,
    invalid_password_payload,
    invalid_email_payload,
    invalid_update_user_payload,
    invalid_reset_password_payload,
    invalid_confirm_password,
    reset_password_payload,
    invalid_mail_user_payload,
    user_data_api_payload,
    invalid_password_user_payload,
)


def decode_token(token: str):
    """Helper function to decode JWT tokens."""
    load_dotenv()
    secret_key = os.environ.get("HASH_KEY")
    algorithm = os.environ.get("HASH_ALGO")
    return jwt.decode(token, secret_key, algorithms=[algorithm])


async def get_user_from_db_async(email: str):
    """Async helper function to fetch user data from the database."""
    from sqlalchemy import select

    async with TestAsyncSessionLocal() as db_session:
        result = await db_session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "data_payload, expected_status",
    [
        (user_data_api_payload, 201),
        (invalid_mail_user_payload, 400),
        (invalid_password_user_payload, 400),
    ],
)
async def test_create_user(test_db, async_client, data_payload, expected_status):
    response = await async_client.post("/api/v1/user/sign-up", json=data_payload)
    assert response.status_code == expected_status

    if response.status_code == 201:
        response_data = response.json()
        # Updated to match APIResponse format
        assert response_data["success"] is True
        assert "created successfully" in response_data["message"].lower()

        user_data = await get_user_from_db_async(user_data_api_payload.get("email"))
        assert user_data.first_name == user_data_api_payload.get("first_name")
        assert user_data.last_name == user_data_api_payload.get("last_name")
        assert user_data.email == user_data_api_payload.get("email")

    else:
        print(response.json())


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "login_payload, expected_status",
    [
        (user_login_payload, 200),
        (invalid_password_payload, 400),
        (invalid_email_payload, 404),
    ],
)
async def test_login_user(test_db, login_payload, create_user, expected_status, async_client):
    response = await async_client.post("/api/v1/user/sign-in", json=login_payload)
    assert response.status_code == expected_status

    if response.status_code == 200:
        response_data = response.json()
        # Updated to match APIResponse format
        assert response_data["success"] is True
        assert "data" in response_data

        # Access tokens from the data field
        token_data = response_data["data"]
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]

        access_token_payload = decode_token(access_token)
        refresh_token_payload = decode_token(refresh_token)

        assert login_payload.get("email") == access_token_payload.get("sub")
        assert not access_token_payload.get("is_refresh")
        assert login_payload.get("email") == refresh_token_payload.get("sub")
        assert refresh_token_payload.get("is_refresh")


@pytest.mark.asyncio
async def test_get_user_data(test_db, async_client, user_token, header):
    header["Authorization"] = f"Bearer {user_token}"
    response = await async_client.get("/api/v1/user/profile", headers=header)

    assert response.status_code == 200
    response_data = response.json()

    # Updated to match APIResponse format
    assert response_data["success"] is True
    assert "data" in response_data

    user_profile_data = response_data["data"]
    token_payload = decode_token(user_token)
    user_data = await get_user_from_db_async(token_payload.get("sub"))

    assert user_profile_data["first_name"] == user_data.first_name
    assert user_profile_data["last_name"] == user_data.last_name
    assert user_profile_data["email"] == user_data.email


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (update_user_payload, 200),
        (invalid_update_user_payload, 400),
    ],
)
async def test_update_profile(test_db, async_client, payload, expected_status, user_token, header):
    header["Authorization"] = f"Bearer {user_token}"
    response = await async_client.patch("/api/v1/user/update-profile", json=payload, headers=header)
    assert response.status_code == expected_status

    if response.status_code == 200:
        response_data = response.json()
        assert response_data["success"] is True
        assert "message" in response_data
        assert isinstance(response_data["message"], str)


@pytest.mark.asyncio
async def test_update_profile_invalid_token(test_db, async_client, header):
    header["Authorization"] = "Bearer invalid_token"
    response = await async_client.patch("/api/v1/user/update-profile", json=update_user_payload, headers=header)
    assert response.status_code == 401

    response_data = response.json()
    # Updated to match APIResponse format
    assert response_data == {
        "success": False,
        "message": None,
        "error": "Not authorized to perform this action, please Sing-in again !",
        "data": None
    }


@pytest.mark.asyncio
async def test_forgot_password(test_db, async_client):
    with patch("app.services.user_service.send_mail"):
        response = await async_client.post("/api/v1/user/forgot-password", json=forget_password_payload)
        assert response.status_code == 200

        response_data = response.json()
        # Updated to match APIResponse format
        assert response_data["success"] is True
        assert "email" in response_data["message"].lower() and "sent" in response_data["message"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (invalid_reset_password_payload, 400),
        (invalid_confirm_password, 400),
        (reset_password_payload, 200),
    ],
)
async def test_reset_password(test_db, async_client, payload, expected_status, user_token, header):
    header["Authorization"] = f"Bearer {user_token}"
    response = await async_client.patch("/api/v1/user/change-password", json=payload, headers=header)
    print("response print",response.json())
    print("response print",response.status_code)
    print("expected status",expected_status)

    assert response.status_code == expected_status

    if response.status_code == 200:
        response_data = response.json()
        # Updated to match APIResponse format
        assert response_data["success"] is True
        assert "password" in response_data["message"].lower() and "changed" in response_data["message"].lower()
        # Check if sign-in URL is in the response data
        if "data" in response_data and response_data["data"]:
            assert "sign-in" in str(response_data["data"]).lower()