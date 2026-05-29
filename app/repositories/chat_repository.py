
from fastapi import HTTPException
from sqlalchemy import select

from app.core.logging import get_logger
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
        chat_rooms = await db.execute(select(ChatRoom).
                                      where(ChatRoom.file_id == file_id,
                                            ChatRoom.created_by == user_id))
        return chat_rooms.scalars().all()
    except Exception as e:
        logger.error(f"Error in getting chat room by file id repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))