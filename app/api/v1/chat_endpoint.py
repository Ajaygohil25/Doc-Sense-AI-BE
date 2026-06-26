from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.oauth2 import get_current_user
from app.core.database import get_db
from app.schemas.chat_schema import ChatQuestionSchema, ChatRoomSchema
from app.schemas.user_schemas import TokenData
from app.services.chat_service import ChatService

router = APIRouter(
    tags=["Chat"],
    prefix="/api/v1/chat"
)


@router.post("/create-chat-room")
async def create_chat_room(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    payload: ChatRoomSchema
):
    chat_service = ChatService(db)
    return await chat_service.create_chat_room_service(current_user, payload)


@router.get("/get-chat-rooms-by-file-id/{file_id}")
async def get_chat_rooms_by_file_id(
    file_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    chat_service = ChatService(db)
    return await chat_service.get_chat_rooms_by_file_id_service(current_user, file_id)


@router.get("/get-chat-messages-by-room-id/{room_id}")
async def get_chat_messages_by_room_id(
    room_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    chat_service = ChatService(db)
    return await chat_service.get_chat_messages_by_room_id_service(current_user, room_id)


@router.post("/ask-question")
async def ask_question(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    payload: ChatQuestionSchema
):
    chat_service = ChatService(db)
    return await chat_service.ask_question_service(current_user, payload)
