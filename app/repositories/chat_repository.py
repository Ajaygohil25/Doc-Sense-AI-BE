from fastapi import HTTPException
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.chat_message_model import ChatMessage, ChatSenderEnum
from app.models.chat_room_model import ChatRoom

logger = get_logger(__name__)


async def create_chat_room(db, file_id, user_id, name="Default chat"):
    try:
        chat_room = ChatRoom(file_id=file_id, name=name)
        db.add(chat_room)
        chat_room.created_by = user_id
        await db.flush()
        return chat_room
    except Exception as e:
        logger.error(f"Error in creating chat room repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_room_by_file_id(db, file_id, user_id):
    try:
        chat_rooms = await db.execute(
            select(ChatRoom)
            .where(
                ChatRoom.file_id == file_id,
                ChatRoom.created_by == user_id,
            )
            .order_by(ChatRoom.created_at.desc())
        )
        return chat_rooms.scalars().all()
    except Exception as e:
        logger.error(f"Error in getting chat room by file id repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_room_for_file_and_user(db, room_id, file_id, user_id):
    try:
        chat_room = await db.execute(
            select(ChatRoom).where(
                ChatRoom.id == room_id,
                ChatRoom.file_id == file_id,
                ChatRoom.created_by == user_id,
            )
        )
        return chat_room.scalars().one_or_none()
    except Exception as e:
        logger.error(f"Error in getting chat room by room/file/user repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_room_for_user(db, room_id, user_id):
    try:
        chat_room = await db.execute(
            select(ChatRoom).where(
                ChatRoom.id == room_id,
                ChatRoom.created_by == user_id,
            )
        )
        return chat_room.scalars().one_or_none()
    except Exception as e:
        logger.error(f"Error in getting chat room by room/user repository: {e}")
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
        user_message = build_chat_message(chat_room_id, ChatSenderEnum.USER, question)
        assistant_message = build_chat_message(chat_room_id, ChatSenderEnum.ASSISTANT, response)

        db_session.add_all([user_message, assistant_message])
        await db_session.flush()
        return user_message, assistant_message
    except Exception as e:
        logger.error(f"Error storing chat messages repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def build_chat_message(chat_room_id, sender, message):
    if isinstance(sender, str):
        sender = ChatSenderEnum(sender)

    return ChatMessage(
        room_id=chat_room_id,
        sender=sender,
        message=message,
    )


async def store_chat_message(db_session, chat_room_id, sender, message):
    try:
        chat_message = build_chat_message(chat_room_id, sender, message)
        db_session.add(chat_message)
        await db_session.flush()
        return chat_message
    except Exception as e:
        logger.error(f"Error storing chat message repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_messages_by_room_id(db_session, room_id):
    try:
        select_query = await db_session.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return select_query.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching chat messages repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_last_messages_by_room_id(db_session, room_id):
    try:
        select_query = await db_session.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        )
        return select_query.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching chat messages repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))
