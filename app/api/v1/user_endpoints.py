from typing import Annotated
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.authentication.oauth2 import get_current_user, oauth2_scheme
from app.core.constants import PROFILE_RETRIEVED_SUCCESSFULLY
from app.core.database import get_db
from app.repositories.user_repositories import get_user_by_mail_id
from app.schemas.base_schema import APIResponse
from app.schemas.user_schemas import UserSchema, TokenData, ChangePasswordSchema, ResetPasswordSchema, UserMail, \
    LoginSchema, \
    LogoutSchema, UserResponse, UpdateUserSchema, UserLoginSchema
from app.services.user_service import UserService

router = APIRouter(
    tags=["users"],
    prefix="/api/v1/user"
)


@router.post("/sign-up")
async def create_user(request_data: UserSchema,
                      db: AsyncSession = Depends(get_db)):
    """API end point to handle user sign-up."""
    user_service = UserService(db)
    return await user_service.register_user_service(request_data)


@router.post("/sign-in")
async def login_user(
        background_tasks: BackgroundTasks,
        login_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """API end point to handle user login."""
    user_service = UserService(db)
    return await user_service.login_user_service(login_data)


@router.patch("/change-password")
async def change_password(
        token: Annotated[str, Depends(oauth2_scheme)],
        request_data: ChangePasswordSchema,
        current_user: TokenData = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """API end point to handle user password reset."""
    user_service = UserService(db)
    return await user_service.change_password_service(token, request_data, current_user.email)


@router.post("/forgot-password")
async def forgot_password(
        request_data: UserMail,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """ API end point to handle forgot password functionality."""
    user_service = UserService(db)
    return await user_service.forgot_user_password(request_data, background_tasks)


@router.post("/reset-password")
async def reset_forgot_password(request_data: ResetPasswordSchema,
                                token,
                                db: AsyncSession = Depends(get_db),
                                ):
    """API end point to handle reset password after forgot password."""
    user_service = UserService(db)
    return await user_service.reset_password_service(request_data, token)


@router.post("/logout")
async def logout_user(
        tokens: LogoutSchema,
        db: AsyncSession = Depends(get_db),
        current_user: TokenData = Depends(get_current_user)):
    """API end point to handle user logout."""

    user_service = UserService(db)
    return await user_service.logout_current_user(tokens)


@router.patch("/update-profile")
async def update_profile(
        update_data: UpdateUserSchema,
        current_user: TokenData = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """ API endpoint for updating a profile."""
    user_service = UserService(db)
    return await user_service.update_user_profile(update_data, current_user)


@router.get("/profile", response_model=APIResponse[UserResponse])
async def show_profile(
        current_user: TokenData = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_mail_id(current_user.email, db)
    return APIResponse.success_response(
        data=UserResponse.model_validate(
            user, from_attributes=True),
        message=PROFILE_RETRIEVED_SUCCESSFULLY)
