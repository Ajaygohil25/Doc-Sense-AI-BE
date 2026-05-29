from fastapi.exceptions import HTTPException
from app.core.logging import get_logger
from app.repositories.chat_repository import create_chat_room, get_chat_room_by_file_id
from app.repositories.file_upload import get_upload_file_history_by_id
from app.schemas.base_schema import APIResponse

logger = get_logger(__name__)


class ChatService:

    def __init__(self, db):
        self.db = db

    async def create_chat_room_service(self, current_user, payload):
        try:
            # validate file id and use id to create chat room
            file_id = payload.file_id
            user_id = current_user.user_id

            file = await get_upload_file_history_by_id(self.db, file_id)

            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            # Check if the user is the owner of the file
            if file.uploaded_by != user_id:
                raise HTTPException(status_code=401, detail="You are not authorized to access this file")

            chat_room = await create_chat_room(self.db, file_id, user_id)

            return APIResponse.success_response(message="Chat room created successfully",
                                                status_code=201,
                                                data={
                                                    "file_id": file_id,
                                                    "chat_room_id": str(chat_room.id)
                                                })

        except Exception as e:
            logger.exception("Error creating chat room", e)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_chat_rooms_by_file_id_service(self, current_user, file_id):
        try:
            chat_rooms = await get_chat_room_by_file_id(self.db, file_id, current_user.user_id)

            return APIResponse.success_response(message="Chat rooms retrieved successfully",
                                                status_code=200,
                                                data=chat_rooms)
        except Exception as e:
            logger.exception("Error retrieving chat rooms", e)
            raise HTTPException(status_code=500, detail="Internal server error")