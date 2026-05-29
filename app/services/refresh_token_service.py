from fastapi import HTTPException
from starlette import status
from app.authentication.token_management import verify_access_token, create_access_token
from app.core.constants import INVALID_ACCESS_TOKEN, VALID_ACCESS_TOKEN, REFRESH_TOKEN_INVALID, TOKEN_SUB, \
    TOKEN_USER_ID, ROLE_TYPE, TOKENS_CREATED_SUCCESSFULLY
from app.schemas.base_schema import APIResponse
from app.schemas.user_schemas import NewToken


class RefreshTokenService:
    def __init__(self, db):
        self.db = db

    async def verify_access_token_service(self, token_data):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_ACCESS_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
        if await verify_access_token(self.db, token_data.token, credentials_exception):
            return APIResponse.success_response(
                message=VALID_ACCESS_TOKEN
            )
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_ACCESS_TOKEN)

    async def create_access_token_on_refresh_token_service(self, refresh_token_data):
        """ API for creating a new access token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=REFRESH_TOKEN_INVALID,
        )

        token_data = await verify_access_token(
            self.db, refresh_token_data.token,
            credentials_exception,
            check_refresh=True
        )

        if token_data:
            data = {
                TOKEN_SUB: token_data.email,
                TOKEN_USER_ID: str(token_data.user_id),
            }

            new_access_token = create_access_token(data)
            return APIResponse.success_response(
                message=TOKENS_CREATED_SUCCESSFULLY,
                data=NewToken(access_token=new_access_token,
                              refresh_token=refresh_token_data.token,
                              token_type="bearer")
            )

        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=REFRESH_TOKEN_INVALID)
