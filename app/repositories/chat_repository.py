from fastapi import HTTPException
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.chat_message_model import ChatMessage, ChatSenderEnum
from app.models.chat_room_model import ChatRoom

logger = get_logger(__name__)


async def create_chat_room(db, file_id, user_id):
    try:
        chat_room = ChatRoom(file_id=file_id)
        db.add(chat_room)
        chat_room.created_by = user_id
        await db.commit()
        await db.refresh(chat_room)
        return chat_room
    except Exception as e:
        logger.error(f"Error in creating chat room repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_room_by_file_id(db, file_id, user_id):
    try:
        chat_rooms = await db.execute(
            select(ChatRoom).where(
                ChatRoom.file_id == file_id,
                ChatRoom.created_by == user_id,
            )
        )
        return chat_rooms.scalars().all()
    except Exception as e:
        logger.error(f"Error in getting chat room by file id repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_default_chat_room(db, file_id, user_id):
    try:
        chat_room = await db.execute(
            select(ChatRoom)
            .where(ChatRoom.file_id == file_id)
            .where(ChatRoom.created_by == user_id)
            .order_by(ChatRoom.created_at.asc())
            .limit(1)
        )
        return chat_room.scalars().one_or_none()
    except Exception as e:
        logger.exception(f"Exception while getting default chatroom repository: {e}")


async def store_question_and_its_response_to_chat_message_model(db_session, chat_room_id, question, response):
    try:
        user_message = ChatMessage(
            room_id=chat_room_id,
            sender=ChatSenderEnum.USER,
            message=question,
        )
        assistant_message = ChatMessage(
            room_id=chat_room_id,
            sender=ChatSenderEnum.ASSISTANT,
            message=response,
        )

        db_session.add_all([user_message, assistant_message])
        await db_session.flush()
        return user_message, assistant_message
    except Exception as e:
        logger.error(f"Error storing chat messages repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))
