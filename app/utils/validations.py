import io
import re
from fastapi import HTTPException
from starlette import status
from app.core.constants import INVALID_EMAIL, INVALID_PASSWORD, USER_ALREADY_EXISTS, INVALID_USER, USER_NOT_FOUND, \
    INVALID_CONTACT
from app.models.user_model import User
from app.repositories.user_repositories import get_user_by_mail_id
import pandas as pd


async def validate_email(email: str, db=None, is_exception = False):
    """ This function validate email input"""
    if not re.fullmatch(r'^[\w.-]+@[\w.-]+\.\w{2,4}$', email):
        return False
    else:
        if is_exception:
            user_data = await get_user_by_mail_id(email, db)
            if user_data:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                detail=USER_ALREADY_EXISTS.format(email))
    return True

def validate_password(password: str):
    """ This function validates password."""
    if not re.fullmatch(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
        return False
    return True

def validate_us_contact_number(contact_number: str):
    """Validate US contact number (10 digits, optional country code, dashes, spaces, or parentheses).

        This will accept numbers like 1234567890, (123) 456-7890, +1 123-456-7890, etc.

    """
    pattern = re.compile(r'^(\+1\s?)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}$')
    if not pattern.fullmatch(contact_number):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_CONTACT)
    return True

async def validate_input(values, db):
    """ This function validates input data."""

    if not await validate_email(values.email, db, is_exception=True):
        raise HTTPException(status_code=400, detail = INVALID_EMAIL)

    if not validate_password(values.password):
        raise HTTPException(status_code=400, detail = INVALID_PASSWORD)
    return True

async def validate_login_input(email: str, password: str):
    """ This function validates login input data."""
    if not await validate_email(email):
        raise HTTPException(status_code=400, detail=INVALID_EMAIL)
    if not validate_password(password):
        raise HTTPException(status_code=400, detail=INVALID_PASSWORD)
    return True


def is_valid_user(db, user_id, is_exception = True):
    """ This function check for a turf owner id is valid or not. """
    user_data = db.query(User).filter(User.id == user_id).first()

    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=USER_NOT_FOUND)

    if is_exception and  not user_data.is_active or not user_data.is_verified:
            raise  HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = INVALID_USER)

    return user_data


def is_valid_string_input(string):
    """ This function validates string input for not having any special characters."""
    regex = re.compile(r'[^a-zA-Z\s\/\-,\.]')

    if regex.search(string):
        return False

    return True

async def is_valid_file(file):
    """ This function validates a file type whether it is csv and excel or not.
    Also checks for the fields exist or not."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload pdf file.")

    return True