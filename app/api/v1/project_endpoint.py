from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.oauth2 import get_current_user
from app.core.database import get_db
from app.schemas.project_schema import (
    ProjectChatRoomCreateSchema,
    ProjectCreateSchema,
    ProjectQuestionSchema,
)
from app.schemas.user_schemas import TokenData
from app.services.project_service import ProjectService

router = APIRouter(
    tags=["Projects"],
    prefix="/api/v1/projects",
)


@router.post("")
async def create_project(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    payload: ProjectCreateSchema,
):
    project_service = ProjectService(db)
    return await project_service.create_project_service(current_user, payload)


@router.get("")
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    project_service = ProjectService(db)
    return await project_service.list_projects_service(current_user)


@router.get("/{project_id}")
async def get_project_detail(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    project_service = ProjectService(db)
    return await project_service.get_project_detail_service(current_user, project_id)


@router.post("/{project_id}/files")
async def upload_project_file(
    project_id: UUID,
    file: Annotated[UploadFile, File(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    project_service = ProjectService(db)
    return await project_service.upload_project_file_service(project_id, file, current_user, background_tasks)


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    project_service = ProjectService(db)
    return await project_service.list_project_files_service(current_user, project_id)


@router.post("/{project_id}/chat-rooms")
async def create_project_chat_room(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    payload: ProjectChatRoomCreateSchema,
):
    project_service = ProjectService(db)
    return await project_service.create_project_chat_room_service(current_user, project_id, payload)


@router.get("/{project_id}/chat-rooms")
async def list_project_chat_rooms(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    project_service = ProjectService(db)
    return await project_service.list_project_chat_rooms_service(current_user, project_id)


@router.get("/{project_id}/chat-rooms/{room_id}/messages")
async def get_project_chat_messages(
    project_id: UUID,
    room_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    project_service = ProjectService(db)
    return await project_service.get_project_chat_messages_service(current_user, project_id, room_id)


@router.post("/{project_id}/ask-question")
async def ask_project_question(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    payload: ProjectQuestionSchema,
):
    project_service = ProjectService(db)
    return await project_service.ask_project_question_service(current_user, project_id, payload)
