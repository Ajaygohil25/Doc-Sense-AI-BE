from datetime import datetime, timedelta, timezone
from fastapi import BackgroundTasks, HTTPException
from starlette import status

from app.authentication.hashing import Hash
from app.authentication.token_management import create_access_token, verify_access_token
from app.config.env_config import settings
from app.core.constants import (INVALID_PASSWORD, USER_CREATED, SING_IN, USER_NOT_FOUND, TOKEN_SUB, TOKEN_USER_ID,
                                PASSWORD_DOES_NOT_MATCH, \
                                PASSWORD_SHOULD_NOT_BE_SAME, PASSWORD_CHANGED, \
                                FORGOT_PASSWORD_SUB, EMAIL_SENT, MESSAGE, TOKEN_EXPIRED, WWW_AUTHENTICATE,
                                NEW_PASSWORD_NOT_SAME, LOGOUT_SUCCESS, \
                                INVALID_CURRENT_PASSWORD, INCORRECT_CREDENTIALS, NO_DATA_TO_UPDATE,
                                INVALID_NAME, USER_DATA_UPDATED, ROLE_TYPE, FORGOT_PASSWORD_CONTENT, ACCESS_TOKEN,
                                BEARER, INVALID_TOKEN_OR_ALREADY_LOGOUT, LOGIN_SUCCESS)
from app.core.send_mail_service import send_mail
from app.repositories.user_repositories import register_user, get_user_by_mail_id, update_user_password, \
    blacklist_token, check_if_token_blacklisted, add_reset_password_token, verify_and_use_token, get_user_by_user_id
from app.schemas.base_schema import APIResponse
from app.schemas.user_schemas import Token
from app.utils.util_functions import generate_token, hash_token
from app.utils.validations import validate_input, validate_password, validate_login_input, is_valid_string_input


class UserService:
    def __init__(self, db):
        self.db = db
        self.sign_in_url = settings.SIGN_IN_URL

    async def register_user_service(self, request_data):
        """This method adds a new user to the database."""
        if await validate_input(request_data, self.db):
            encrypted_password = Hash.encrypt(request_data.password)
            request_data.password = encrypted_password

            await register_user(request_data, self.db)

            return APIResponse.success_response(message=USER_CREATED,
                                                status_code=status.HTTP_201_CREATED)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    async def login_user_service(self, login_data):
        """ This method authenticates a user and generates an access token."""
        input_email = login_data.username
        input_password = login_data.password

        if await validate_login_input(input_email, input_password):
            user_data = await get_user_by_mail_id(input_email, self.db)

            if not user_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)

            if Hash.verify_password(input_password, user_data.password):
                access_token = create_access_token(
                    data={
                        TOKEN_SUB: input_email,
                        TOKEN_USER_ID: str(user_data.id),
                    }
                )

                refresh_token = create_access_token(
                    data={
                        TOKEN_SUB: input_email,
                        TOKEN_USER_ID: str(user_data.id),
                    },
                    refresh=True
                )

                token = Token(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    user_id=user_data.id,
                    email=user_data.email,
                    first_name=user_data.first_name,
                    last_name=user_data.last_name
                )

                return token
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INCORRECT_CREDENTIALS)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    async def change_password_service(self, token, request_data, email_id):
        """ This method reset the password of an existing user."""

        user_data = await get_user_by_mail_id(email_id, self.db)

        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)

        if (validate_password(request_data.new_password) and
                validate_password(request_data.confirm_password)
                and validate_password(request_data.current_password)):

            if request_data.new_password != request_data.confirm_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=PASSWORD_DOES_NOT_MATCH)

            if Hash.verify_password(request_data.current_password, user_data.password):

                if request_data.new_password == request_data.current_password:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=PASSWORD_SHOULD_NOT_BE_SAME)

                await update_user_password(user_data, request_data.new_password, self.db)
                await blacklist_token(token, db=self.db)

                return APIResponse.success_response(
                    message=PASSWORD_CHANGED,
                    data={
                        SING_IN: self.sign_in_url
                    }
                )
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail=INVALID_CURRENT_PASSWORD)

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_PASSWORD)

    async def forgot_user_password(self, request_data, background_tasks):
        """This method handle the forgot password process."""

        user_data = await get_user_by_mail_id(request_data.email, self.db)

        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)

        token = generate_token()

        await add_reset_password_token(
            reset_password_token=hash_token(token),
            token_expire_time=datetime.now(timezone.utc) + timedelta(minutes=int(settings.RESET_TOKEN_EXPIRE_MINUTES)),
            user_id=user_data.id,
            db=self.db
        )

        FORGOT_PASSWORD_URL = settings.FORGOT_PASSWORD_URL

        # TODO: Replace credentials in the env and uncomment this code to enable email sending
        # background_tasks.add_task(send_mail, request_data.email,
        #                           FORGOT_PASSWORD_SUB,
        #                           FORGOT_PASSWORD_CONTENT + FORGOT_PASSWORD_URL + token)

        return APIResponse.success_response(
            message=EMAIL_SENT
        )

    async def reset_password_service(self, request_data, token):
        """ This method reset the password with a secret token of forgot password."""

        user_id = await verify_and_use_token(self.db, token)

        if not user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=TOKEN_EXPIRED)

        user_data = await get_user_by_user_id(user_id, self.db)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)

        if validate_password(request_data.new_password) and validate_password(request_data.confirm_password):

            if request_data.new_password == request_data.confirm_password:
                await update_user_password(user_data, request_data.new_password, db=self.db)

                return APIResponse.success_response(
                    message=PASSWORD_CHANGED
                )
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=NEW_PASSWORD_NOT_SAME)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_PASSWORD)

    async def logout_current_user(self, tokens):
        """ This method logs out the current user."""

        if await check_if_token_blacklisted(tokens.access_token, self.db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN_OR_ALREADY_LOGOUT,
                headers={WWW_AUTHENTICATE: BEARER},
            )

        if await check_if_token_blacklisted(tokens.refresh_token, self.db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN_OR_ALREADY_LOGOUT,
                headers={WWW_AUTHENTICATE: BEARER},
            )

        await blacklist_token(tokens.access_token, self.db)
        await blacklist_token(tokens.refresh_token, self.db)

        return APIResponse.success_response(message=LOGOUT_SUCCESS)

    async def update_user_profile(self, update_data, current_user):
        """This method updates the user profile."""
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=NO_DATA_TO_UPDATE)

        user_data = await get_user_by_mail_id(current_user.email, self.db)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)

        updated = False

        if update_data.first_name:
            if not is_valid_string_input(update_data.first_name):
                raise HTTPException(status_code=400, detail=INVALID_NAME)
            user_data.first_name = update_data.first_name
            updated = True

        if update_data.last_name:
            if not is_valid_string_input(update_data.last_name):
                raise HTTPException(status_code=400, detail=INVALID_NAME)
            user_data.last_name = update_data.last_name
            updated = True

        if not updated:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=NO_DATA_TO_UPDATE)

        user_data.updated_by = current_user.user_id
        user_data.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(user_data)

        return APIResponse.success_response(message=USER_DATA_UPDATED)
