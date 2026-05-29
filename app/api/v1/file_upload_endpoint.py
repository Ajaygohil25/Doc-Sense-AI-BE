from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.oauth2 import get_current_user
from app.core.database import get_db
from app.schemas.user_schemas import TokenData
from app.services.file_upload_service import FileService

router = APIRouter(
    tags=["Dashboard"],
    prefix="/api/v1/dashboard"
)


@router.post("/file-upload")
async def input_file_upload_endpoint(
        file: Annotated[UploadFile, File(...)],
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[TokenData, Depends(get_current_user)],
        background_tasks: BackgroundTasks = BackgroundTasks()
):
    dashboard_service = FileService(db)
    return await dashboard_service.upload_file_service(file, current_user, background_tasks)


@router.get("/get-file-upload-history")
async def get_file_upload_history_endpoint(
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[TokenData, Depends(get_current_user)],
        page: int = 1,
        page_size: int = 20
):
    file_service = FileService(db)
    return await file_service.get_upload_file_history(current_user.user_id, page, page_size)


@router.get("/get-file-by-id/{upload_file_id}")
async def get_file_upload_history_by_file_id_endpoint(
        upload_file_id: UUID,
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[TokenData, Depends(get_current_user)]
):
    file_service = FileService(db)
    return await file_service.get_upload_file_by_file_id(upload_file_id, current_user.user_id)