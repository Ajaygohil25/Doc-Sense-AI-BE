import asyncio

from fastapi.exceptions import HTTPException
from app.core.logging import get_logger
from app.rag.chain import build_rag_chain
from app.rag.query import get_chat_model
from app.rag.retriever import get_retriever
from app.repositories.chat_repository import (
    create_chat_room,
    get_chat_messages_by_room_id,
    get_chat_room_by_file_id,
    get_chat_room_for_file_and_user,
    get_chat_room_for_user,
    store_question_and_its_response_to_chat_message_model,
)
from app.repositories.file_upload import get_upload_file_history_by_id
from app.schemas.base_schema import APIResponse
from app.schemas.chat_schema import (
    ChatMessageResponse,
    ChatMessageSchema,
    ChatQuestionResponse,
    ChatRoomListResponse,
    ChatRoomResponse,
)
from app.utils.socket_validations import is_injection_attempt

logger = get_logger(__name__)


class ChatService:

    def __init__(self, db):
        self.db = db

    async def _get_owned_file(self, file_id, user_id):
        file = await get_upload_file_history_by_id(self.db, file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if file.uploaded_by != user_id:
            raise HTTPException(status_code=403, detail="You are not authorized to access this file")

        return file

    async def _get_owned_room_for_file(self, room_id, file_id, user_id):
        chat_room = await get_chat_room_for_file_and_user(self.db, room_id, file_id, user_id)

        if not chat_room:
            raise HTTPException(status_code=404, detail="Chat room not found")

        return chat_room

    async def create_chat_room_service(self, current_user, payload):
        try:
            file_id = payload.file_id
            user_id = current_user.user_id

            await self._get_owned_file(file_id, user_id)
            chat_room = await create_chat_room(self.db, file_id, user_id, payload.name)

            return APIResponse.success_response(
                message="Chat room created successfully",
                status_code=201,
                data={"chat_room": ChatRoomResponse.model_validate(chat_room)}
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating chat room: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_chat_rooms_by_file_id_service(self, current_user, file_id):
        try:
            await self._get_owned_file(file_id, current_user.user_id)
            chat_rooms = await get_chat_room_by_file_id(self.db, file_id, current_user.user_id)
            payload = ChatRoomListResponse(
                chat_rooms=[ChatRoomResponse.model_validate(room) for room in chat_rooms]
            )

            return APIResponse.success_response(
                message="Chat rooms retrieved successfully",
                status_code=200,
                data=payload
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error retrieving chat rooms: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_chat_messages_by_room_id_service(self, current_user, room_id):
        try:
            chat_room = await get_chat_room_for_user(self.db, room_id, current_user.user_id)

            if not chat_room:
                raise HTTPException(status_code=404, detail="Chat room not found")

            chat_messages = await get_chat_messages_by_room_id(self.db, room_id)

            messages = []

            for message in chat_messages:
                messages.append(
                    ChatMessageSchema(
                        id=message.id,
                        room_id=message.room_id,
                        message=message.message,
                        sender=message.sender.value,
                        created_at=message.created_at
                    )
                )

            payload = ChatMessageResponse(
                messages=messages,
                chat_room_id=room_id
            )

            return APIResponse.success_response(
                message="Chat messages retrieved successfully",
                status_code=200,
                data=payload
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error retrieving chat messages: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def ask_question_service(self, current_user, payload):
        try:
            user_id = current_user.user_id
            await self._get_owned_file(payload.file_id, user_id)
            chat_room = await self._get_owned_room_for_file(payload.chat_room_id, payload.file_id, user_id)

            is_suspicious, reason = is_injection_attempt(payload.question)
            if is_suspicious:
                raise HTTPException(
                    status_code=400,
                    detail=f"I can only answer questions based on the uploaded documents. {reason}",
                )

            retriever = get_retriever(payload.file_id, user_id)
            model = get_chat_model()
            chain = build_rag_chain(retriever=retriever, model=model)
            response = await asyncio.to_thread(chain.invoke, payload.question)
            response_text = response if isinstance(response, str) else str(response)

            await store_question_and_its_response_to_chat_message_model(
                self.db,
                chat_room.id,
                payload.question,
                response_text,
            )

            return APIResponse.success_response(
                message="Question answered successfully",
                status_code=200,
                data=ChatQuestionResponse(
                    file_id=payload.file_id,
                    chat_room_id=chat_room.id,
                    question=payload.question,
                    response=response_text,
                )
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error answering chat question: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
