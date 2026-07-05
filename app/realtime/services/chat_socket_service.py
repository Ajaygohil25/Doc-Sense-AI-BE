import asyncio
import logging
from collections.abc import AsyncIterator

from app.core.database import AsyncSessionLocal, get_transaction_session
from app.models.chat_message_model import ChatSenderEnum
from app.rag.chain import build_rag_chain
from app.rag.query import get_chat_model
from app.rag.retriever import get_project_retriever, get_retriever
from app.realtime.emitters import SocketEvent, with_request_context
from app.realtime.streaming import (
    STREAM_RESPONSE_CHUNK_DELAY_SECONDS,
    stream_chain_response,
)
from app.repositories.chat_repository import (
    get_chat_room_for_file_and_user,
    get_chat_room_for_project_and_user,
    get_default_chat_room,
    get_default_project_chat_room,
    get_last_messages_by_room_id,
    store_chat_message,
    store_question_and_its_response_to_chat_message_model,
)
from app.repositories.file_upload import get_upload_file_history_by_id
from app.repositories.project_repository import get_project_by_id_for_user
from app.utils.socket_validations import socket_error_payload, validate_question_data

logger = logging.getLogger("app.realtime.services.chat_socket_service")


class ChatSocketService:
    async def ask_question_events(self, data: dict, session: dict) -> AsyncIterator[SocketEvent]:
        question_context = await self.build_question_context(data, session)

        if question_context is None:
            return

        if question_context.get("error"):
            yield SocketEvent("error", question_context["error"], target="sid")
            return

        file_id = question_context.get("file_id")
        project_id = question_context.get("project_id")
        question = question_context["question"]
        request_id = question_context["request_id"]
        effective_chat_room_id = question_context["effective_chat_room_id"]
        user_id = question_context["user_id"]
        is_project_scope = bool(project_id)

        try:
            previous_messages = await self.fetch_previous_messages(
                room_id=effective_chat_room_id,
            )
            
            user_message = await self.store_chat_message(
                effective_chat_room_id,
                ChatSenderEnum.USER,
                question,
            )

            yield SocketEvent(
                "chat_message_created",
                chat_message_payload(
                    user_message,
                    file_id=file_id,
                    project_id=project_id,
                    request_id=request_id,
                ),
            )

            retriever = (
                get_project_retriever(project_id, user_id)
                if is_project_scope
                else get_retriever(file_id, user_id)
            )
            model = get_chat_model()
            chain = build_rag_chain(
                retriever=retriever,
                model=model,
                prev_message_context=previous_messages,
            )

            response_parts = []
            stream_base_payload = {
                "chat_room_id": str(effective_chat_room_id),
                "question": question,
            }
            if is_project_scope:
                stream_base_payload["project_id"] = str(project_id)
            else:
                stream_base_payload["file_id"] = str(file_id)

            if request_id:
                stream_base_payload["request_id"] = request_id

            yield SocketEvent("question_response_start", stream_base_payload)

            async for response_chunk in stream_chain_response(chain, question):
                response_parts.append(response_chunk)
                yield SocketEvent(
                    "question_response_chunk",
                    {
                        **stream_base_payload,
                        "chunk": response_chunk,
                    },
                )
                await asyncio.sleep(STREAM_RESPONSE_CHUNK_DELAY_SECONDS)

            response = "".join(response_parts)
            response_payload = {
                "chat_room_id": str(effective_chat_room_id),
                "question": question,
                "response": response,
            }
            if is_project_scope:
                response_payload["project_id"] = str(project_id)
            else:
                response_payload["file_id"] = str(file_id)

            if request_id:
                response_payload["request_id"] = request_id

            await self.store_chat_message(
                effective_chat_room_id,
                ChatSenderEnum.ASSISTANT,
                response,
            )

            yield SocketEvent("question_response_end", response_payload)
            yield SocketEvent("question_response", response_payload)

            logger.info(
                f"RAG question resolved via Socket.IO: "
                f"user_id={user_id}, file_id={file_id}, project_id={project_id}, request_id={request_id}"
            )

        except Exception as e:
            logger.info(
                f"Error processing RAG question via Socket.IO "
                f"for user_id={user_id}, request_id={request_id}: {e}",
                exc_info=True,
            )
            yield SocketEvent(
                "error",
                with_request_context(
                    socket_error_payload(
                        f"Failed to generate response: {str(e)}",
                        code="RAG_RESPONSE_FAILED",
                    ),
                    request_id,
                    effective_chat_room_id,
                ),
                target="sid",
            )

    async def build_question_context(self, data: dict, session: dict) -> dict | None:
        request_id = data.get("request_id")
        requested_chat_room_id = data.get("chat_room_id")
        file_id, project_id, question, question_validation_error = await validate_question_data(data)
        user_id = session["user_id"]
        effective_chat_room_id = requested_chat_room_id

        async with get_transaction_session(AsyncSessionLocal) as db_session:
            if question_validation_error and bool(file_id) == bool(project_id):
                return {
                    "error": with_request_context(
                        question_validation_error,
                        request_id,
                        requested_chat_room_id,
                    )
                }

            if file_id:
                file = await get_upload_file_history_by_id(db_session, file_id)

                if not file:
                    return {
                        "error": with_request_context(
                            socket_error_payload("File not found.", code="FILE_NOT_FOUND"),
                            request_id,
                            requested_chat_room_id,
                        )
                    }

                if str(getattr(file, "uploaded_by", user_id)) != str(user_id):
                    return {
                        "error": with_request_context(
                            socket_error_payload(
                                "Forbidden: You do not have access to this file.",
                                code="FORBIDDEN",
                            ),
                            request_id,
                            requested_chat_room_id,
                        )
                    }

                if requested_chat_room_id:
                    chat_room = await get_chat_room_for_file_and_user(
                        db_session,
                        requested_chat_room_id,
                        file_id,
                        user_id,
                    )
                    effective_chat_room_id = chat_room.id if chat_room else None
                else:
                    default_chat_room = await get_default_chat_room(db_session, file_id, user_id)
                    effective_chat_room_id = default_chat_room.id if default_chat_room else None
            else:
                project = await get_project_by_id_for_user(db_session, project_id, user_id)

                if not project:
                    return {
                        "error": with_request_context(
                            socket_error_payload("Project not found.", code="PROJECT_NOT_FOUND"),
                            request_id,
                            requested_chat_room_id,
                        )
                    }

                if requested_chat_room_id:
                    chat_room = await get_chat_room_for_project_and_user(
                        db_session,
                        requested_chat_room_id,
                        project_id,
                        user_id,
                    )
                    effective_chat_room_id = chat_room.id if chat_room else None
                else:
                    default_chat_room = await get_default_project_chat_room(db_session, project_id, user_id)
                    effective_chat_room_id = default_chat_room.id if default_chat_room else None

            if not effective_chat_room_id:
                return {
                    "error": with_request_context(
                        socket_error_payload(
                            "Chat room not found.",
                            code="CHAT_ROOM_NOT_FOUND",
                        ),
                        request_id,
                        requested_chat_room_id,
                    )
                }

            if question_validation_error:
                if question:
                    await store_question_and_its_response_to_chat_message_model(
                        db_session,
                        effective_chat_room_id,
                        question,
                        question_validation_error["message"],
                    )

                return {
                    "error": with_request_context(
                        question_validation_error,
                        request_id,
                        effective_chat_room_id,
                    )
                }

        return {
            "file_id": file_id,
            "project_id": project_id,
            "question": question,
            "request_id": request_id,
            "effective_chat_room_id": effective_chat_room_id,
            "user_id": user_id,
        }

    async def fetch_previous_messages(self, room_id):
        """Fetches the last 10 messages in chronological order for LLM context."""
        async with get_transaction_session(AsyncSessionLocal) as db_session:
            chat_messages = await get_last_messages_by_room_id(db_session, room_id)

        if not chat_messages:
            logger.info("No chat message history found for the room")
            return None

        message_context = []
        for message in reversed(chat_messages):
            message_context.append(
                {
                    "sender": message.sender,
                    "message": message.message,
                    "created_at": message.created_at,
                }
            )

        return message_context

    async def store_chat_message(self, chat_room_id, sender, message):
        async with get_transaction_session(AsyncSessionLocal) as db_session:
            return await store_chat_message(
                db_session,
                chat_room_id,
                sender,
                message,
            )


def chat_message_payload(chat_message, file_id=None, project_id=None, request_id: str | None = None) -> dict:
    created_at = chat_message.created_at
    payload = {
        "id": str(chat_message.id),
        "chat_room_id": str(chat_message.room_id),
        "room_id": str(chat_message.room_id),
        "sender": chat_message.sender.value,
        "message": chat_message.message,
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else None,
    }

    if project_id:
        payload["project_id"] = str(project_id)
    else:
        payload["file_id"] = str(file_id)

    if request_id:
        payload["request_id"] = request_id

    return payload
