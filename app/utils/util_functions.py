import hashlib
import hmac
import os
import secrets
from decimal import Decimal

import aiofiles
from fastapi import HTTPException

from app.config.env_config import settings


def generate_token():
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    key = settings.RESET_TOKEN_SECRET_KEY
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

async def save_file_to_disk(file, upload_dir, file_name):
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file_name)
    try:
        # reset a pointer in case it was read before
        await file.seek(0)

        async with aiofiles.open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # read in 1MB chunks
                await buffer.write(chunk)

        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


def parse_page_content(docs):
    """ Get the page content from the retrieved docs"""
    context_text = "\n\n".join(doc.page_content for doc in docs)
    return context_text