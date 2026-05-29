from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from fastapi import HTTPException
from jwt import DecodeError
from sqlalchemy import select
from starlette import status
from app.core.constants import EXPIRES, REFRESH_TOKEN_REQUIRED, IS_REFRESH, ACCESS_TOKEN_REQUIRED, TOKEN_EXPIRED
from app.config.env_config import settings
from app.models.blacklist_token_model import BlackListToken
from app.schemas.user_schemas import TokenData

SECRET_KEY = settings.HASH_KEY
ALGORITHM = settings.HASH_ALGO


def create_access_token(data: dict, refresh=False, custom_token=False, access_token_expire_time =settings.ACCESS_TOKEN_EXPIRE_TIME):
    """ This function creates an access token and refresh token for the given data."""

    ACCESS_TOKEN_EXPIRE_TIME = access_token_expire_time
    REFRESH_TOKEN_EXPIRE_TIME = settings.REFRESH_TOKEN_EXPIRE_TIME
    to_encode = data.copy()

    if custom_token:
        expire = datetime.now(timezone.utc) + timedelta(minutes=int(access_token_expire_time))
    elif refresh:
        expire = datetime.now(timezone.utc) + timedelta(hours=int(REFRESH_TOKEN_EXPIRE_TIME))
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=int(ACCESS_TOKEN_EXPIRE_TIME))

    to_encode.update({EXPIRES: expire})
    to_encode.update({IS_REFRESH: refresh})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_access_token(db, token, credentials_exception, check_refresh=False):
    """ This function verifies the token, If access token is invalid then raise exception """
    try:
        output = await db.execute(
            select(BlackListToken).where(BlackListToken.token == token)
        )
        blacklisted_token = output.scalar_one_or_none()

        if blacklisted_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=TOKEN_EXPIRED)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")
        user_id: UUID = payload.get("user_id")

        is_refresh = payload.get("is_refresh")

        if not email:
            raise credentials_exception

        if check_refresh:
            if not is_refresh:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=REFRESH_TOKEN_REQUIRED)
        else:
            if is_refresh:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ACCESS_TOKEN_REQUIRED)

        return TokenData(email=email, user_id=user_id)

    except jwt.ExpiredSignatureError:
        raise credentials_exception

    except DecodeError:
        raise credentials_exception
