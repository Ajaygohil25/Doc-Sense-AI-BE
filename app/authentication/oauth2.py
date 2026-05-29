from typing import Annotated
from fastapi import Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from app.authentication.token_management import verify_access_token
from app.core.constants import NOT_AUTHORIZED
from app.core.database import get_db

class OAuth2EmailRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        email: str = Form(...),  # renamed from username → email
        password: str = Form(...),
        scope: str = Form(""),
        client_id: str | None = Form(None),
        client_secret: str | None = Form(None),
    ):
        super().__init__(username=email, password=password, scope=scope,
                         client_id=client_id, client_secret=client_secret)
        self.username = email  # store separately if you want

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/sign-in")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
    """ This function check there is a valid token in the request."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=NOT_AUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    )

    return await verify_access_token(db, token, credentials_exception)
