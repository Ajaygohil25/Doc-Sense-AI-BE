import hmac
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.hashing import Hash
from app.models.blacklist_token_model import BlackListToken
from app.models.password_reset_token_model import PasswordResetTokenModel
from app.models.user_model import User
from app.utils.util_functions import hash_token


async def get_user_by_mail_id(email_id, db):
    """ This method checks user exist or not."""
    try:
        result = await db.execute(select(User).where(User.email == email_id))
        return result.scalar_one_or_none()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_by_user_id(user_id, db):
    """ This method checks user exist or not."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def register_user(user_data, db):
    try:
        user = User(**user_data.model_dump())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await db.close()

async def update_user_password(user_data, new_password, db):
        """ This method updates the user password"""
        try:
            user_data.password = Hash.encrypt(new_password)
            await db.commit()
            await db.refresh(user_data)

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

async def blacklist_token(token, db):
        """ This method blocklists the token by adding it into the database."""
        try:
            access_token = BlackListToken(
                token=token
            )
            db.add(access_token)
            await db.commit()
            await db.refresh(access_token)

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

async def check_if_token_blacklisted(token, db):
    """ This method checks if the token is blocklisted or not."""
    try:
        result = await db.execute(select(BlackListToken).where(BlackListToken.token == token))
        return result.scalar_one_or_none()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def add_reset_password_token(reset_password_token, user_id,token_expire_time, db):
    """ This method checks if the token is blocklisted or not."""
    try:
        reset_password_token = PasswordResetTokenModel(
                user_id=user_id,
                token_hash=reset_password_token,
                expires_at=token_expire_time
        )
        db.add(reset_password_token)
        await db.commit()
        await db.refresh(reset_password_token)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def verify_and_use_token(db: AsyncSession, token: str) -> bool:
    stmt = (
        select(PasswordResetTokenModel)
        .where(
            PasswordResetTokenModel.used == False,
            PasswordResetTokenModel.expires_at > datetime.now(timezone.utc),
        )
        .order_by(PasswordResetTokenModel.created_at.desc())
    )

    result = await db.execute(stmt)
    tokens = result.scalars().all()

    if not tokens:
        return False

    incoming_hash = hash_token(token)

    for row in tokens:
        if hmac.compare_digest(row.token_hash, incoming_hash):
            row.used = True
            await db.commit()
            return row.user_id

    return False
