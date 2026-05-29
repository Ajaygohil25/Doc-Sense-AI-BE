from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user_schemas import TokenSchema
from app.services.refresh_token_service import RefreshTokenService

router = APIRouter(
    tags=["Token"],
    prefix="/api/v1/token"
)

@router.post("/verify-access-token")
async def verify_token(
        token_data: TokenSchema,
        db: AsyncSession = Depends(get_db)
):
    """ API endpoint for verifying access"""
    refresh_token_service = RefreshTokenService(db)
    return await refresh_token_service.verify_access_token_service(token_data)


@router.post("/generate-access-token")
async def create_token_on_refresh_token(
        refresh_token_data: TokenSchema,
        db: AsyncSession = Depends(get_db)
):
    """ API for creating a new access token."""
    refresh_token_service = RefreshTokenService(db)
    return await refresh_token_service.create_access_token_on_refresh_token_service(refresh_token_data)

