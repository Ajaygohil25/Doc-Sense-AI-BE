import asyncio
import logging
from socketio.exceptions import ConnectionRefusedError

from app.rag.query import get_chat_model
from app.realtime.socket_server import sio
from app.realtime.auth import authenticate_socket
from app.rag.retriever import get_retriever
from app.rag.chain import build_rag_chain
from app.core.database import get_transaction_session, AsyncSessionLocal
from app.repositories.chat_repository import (
    get_default_chat_room,
    store_question_and_its_response_to_chat_message_model,
)
from app.repositories.file_upload import get_upload_file_history_by_id
from app.utils.socket_validations import (
    socket_error_payload,
    validate_question_data,
    validate_socket_session_data,
)

logger = logging.getLogger("app.realtime.handlers")

@sio.event
async def connect(sid, environ, auth=None):
    """
    Handler for connection handshake.
    Authenticates the client and establishes the connection.
    """
    logger.info(f"Incoming connection request: sid={sid}")
    
    session_data = await authenticate_socket(environ, auth)

    if not session_data:
        logger.warning(f"Connection refused: Authentication failed for sid={sid}")
        raise ConnectionRefusedError("Authentication failed: Invalid or missing token")
        
    await sio.save_session(sid, session_data)
    
    # Auto-join the user's private room to enable direct emits across instances
    user_id = session_data["user_id"]
    user_room = f"user_{user_id}"
    await sio.enter_room(sid, user_room)
    
    logger.info(f"Connection established: sid={sid}, user_id={user_id}, joined room={user_room}")
    await sio.emit("connected", {"sid": sid, "user_id": user_id}, to=sid)

@sio.event
async def disconnect(sid):
    """
    Handler for client disconnection.
    """
    try:
        session = await sio.get_session(sid)
        user_id = session.get("user_id") if session else "unknown"
        logger.info(f"Client disconnected: sid={sid}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Error during disconnect logging for sid={sid}: {e}")

@sio.event
async def join_channel(sid, data):
    """
    Allows an authenticated user to join a room/channel.
    """
    session, validation_error = await validate_socket_session_data(sid, data, sio)

    if validation_error:
        return  # Validation function already emitted error response

    channel_id = data.get("channel_id")
    if not channel_id:
        await sio.emit("error", {"message": "Missing channel_id"}, to=sid)
        return
        
    # Enforce room/channel authorization
    # If the channel is a user-specific room, ensure only that user can join it
    user_id = session["user_id"]
    if channel_id.startswith("user_") and channel_id != f"user_{user_id}":
        logger.warning(f"Unauthorized room join attempt: user_id={user_id} tried to join room={channel_id}")
        await sio.emit("error", {"message": "Forbidden: You do not have access to this channel."}, to=sid)
        return
        
    await sio.enter_room(sid, channel_id)
    logger.info(f"User {user_id} (sid={sid}) joined channel: {channel_id}")
    await sio.emit("channel_joined", {"channel_id": channel_id}, to=sid)

@sio.event
async def leave_channel(sid, data):
    """
    Allows a user to leave a room/channel.
    """
    session = await sio.get_session(sid)
    if not session:
        return
        
    if not isinstance(data, dict):
        return
        
    channel_id = data.get("channel_id")
    if not channel_id:
        return
        
    await sio.leave_room(sid, channel_id)
    logger.info(f"User {session['user_id']} (sid={sid}) left channel: {channel_id}")
    await sio.emit("channel_left", {"channel_id": channel_id}, to=sid)

@sio.event
async def ask_question(sid, data):
    """
    Handles user asking questions about uploaded documents via Socket.IO.
    Queries the RAG pipeline asynchronously and emits the response.
    
    Enhanced to support request_id for frontend message matching.
    """
    session, validation_error = await validate_socket_session_data(
        sid,
        data,
        sio,
        emit_error=False,
    )

    if validation_error:
        await sio.emit("error", validation_error, to=sid)
        return
        

    request_id = data.get("request_id")  # NEW: Message ID from frontend
    chat_room_id = data.get("chat_room_id")
    file_id, question, question_validation_error = await validate_question_data(data)
    user_id = session["user_id"]
    effective_chat_room_id = chat_room_id

    async with get_transaction_session(AsyncSessionLocal) as db_session:
        file = await get_upload_file_history_by_id(db_session, file_id) if file_id else None

        if file_id and not chat_room_id:
            default_chat_room = await get_default_chat_room(db_session, file_id, user_id)
            effective_chat_room_id = default_chat_room.id if default_chat_room else None

        if question_validation_error:
            if question and effective_chat_room_id:
                await store_question_and_its_response_to_chat_message_model(
                    db_session,
                    effective_chat_room_id,
                    question,
                    question_validation_error["message"],
                )

            await sio.emit(
                "error",
                with_request_id(question_validation_error, request_id),
                to=sid,
            )
            return

        if not file:
            await sio.emit(
                "error",
                with_request_id(
                    socket_error_payload("File not found.", code="FILE_NOT_FOUND"),
                    request_id,
                ),
                to=sid,
            )
            return  # NEW: Add return to prevent further execution

        if not effective_chat_room_id:
            await sio.emit(
                "error",
                with_request_id(
                    socket_error_payload(
                        "Chat room not found.",
                        code="CHAT_ROOM_NOT_FOUND",
                    ),
                    request_id,
                ),
                to=sid,
            )
            return

    user_id = session["user_id"]

    try:
        # Build the RAG chain dynamically
        retriever = get_retriever(file_id, user_id)
        model = get_chat_model()
        chain = build_rag_chain(retriever=retriever, model=model)
        
        # Invoke the chain in a background thread to prevent event loop blocking
        response = await asyncio.to_thread(chain.invoke, question)

        response_payload = {
            "file_id": file_id,
            "question": question,
            "response": response
        }
        stored_response = response if isinstance(response, str) else str(response)

        # Store question and its response to db
        async with get_transaction_session(AsyncSessionLocal) as db_session:
            await store_question_and_its_response_to_chat_message_model(
                db_session,
                effective_chat_room_id,
                question,
                stored_response,
            )

        # Include request_id if provided
        if request_id:
            response_payload["request_id"] = request_id

        user_id = session["user_id"]

        # Emit successful response
        await emit_to_user(
            user_id=user_id,
            event="question_response",
            data=response_payload,
        )

        logger.info(
            f"RAG question resolved via Socket.IO: "
            f"user_id={user_id}, file_id={file_id}, "
            f"request_id={request_id}"
        )
        
    except Exception as e:
        logger.error(
            f"Error processing RAG question via Socket.IO "
            f"for user_id={user_id}, request_id={request_id}: {e}",
            exc_info=True
        )
        await sio.emit(
            "error", 
            with_request_id(
                socket_error_payload(
                    f"Failed to generate response: {str(e)}",
                    code="RAG_RESPONSE_FAILED",
                ),
                request_id,
            ),
            to=sid
        )


# --- Helper Functions for Server-Initiated Emits ---

def with_request_id(payload: dict, request_id: str | None) -> dict:
    if not request_id:
        return payload

    return {**payload, "request_id": request_id}


async def emit_to_user(user_id: str, event: str, data: dict):
    """
    Emits an event directly to all active connections of a specific user.
    Uses the auto-joined user-specific room.
    """
    room_name = f"user_{user_id}"
    logger.debug(f"Emitting event '{event}' to user '{user_id}' via room '{room_name}'")
    await sio.emit(event, data, room=room_name)

async def emit_to_channel(channel_id: str, event: str, data: dict, skip_sid: str = None):
    """
    Emits an event to all users subscribed to a channel.
    Optionally skips a specific socket ID (e.g., the sender).
    """
    logger.debug(f"Emitting event '{event}' to channel '{channel_id}'")
    await sio.emit(event, data, room=channel_id, skip_sid=skip_sid)
