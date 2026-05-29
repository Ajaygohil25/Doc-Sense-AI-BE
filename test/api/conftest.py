import pytest
from app.authentication.token_management import create_access_token
from app.core.constants import TOKEN_SUB, TOKEN_USER_ID, ROLE_TYPE


def token(user):
    access_token = create_access_token(
        data={
            TOKEN_SUB: user.email,
            TOKEN_USER_ID: str(user.id),
        }
    )
    return access_token


@pytest.fixture(scope="module")
def user_token(create_user):
    """ This fixture login customer and generate access token. """
    return token(create_user)


@pytest.fixture(scope="module")
def header():
    return {"Authorization": ""}
