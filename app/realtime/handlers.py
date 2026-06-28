import logging

from socketio.exceptions import ConnectionRefusedError

from app.realtime.auth import authenticate_socket
from app.realtime.emitters import emit_socket_event
from app.realtime.services import ChatSocketService
from app.realtime.socket_server import sio
from app.utils.socket_validations import (
    socket_error_payload,
    validate_socket_session_data,
)

logger = logging.getLogger("app.realtime.handlers")

ALLOWED_CHANNEL_PREFIXES = ("public_", "channel_")


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
    Allows an authenticated user to join an explicitly allowed room/channel.
    """
    session, validation_error = await validate_socket_session_data(sid, data, sio)

    if validation_error:
        return

    channel_id = data.get("channel_id")
    if not channel_id:
        await sio.emit(
            "error",
            socket_error_payload("Missing channel_id"),
            to=sid,
        )
        return

    user_id = session["user_id"]
    if not is_channel_join_allowed(channel_id, user_id):
        logger.warning(
            f"Unauthorized room join attempt: user_id={user_id} tried to join room={channel_id}"
        )
        await sio.emit(
            "error",
            socket_error_payload(
                "Forbidden: You do not have access to this channel.",
                code="FORBIDDEN",
            ),
            to=sid,
        )
        return

    await sio.enter_room(sid, channel_id)
    logger.info(f"User {user_id} (sid={sid}) joined channel: {channel_id}")
    await sio.emit("channel_joined", {"channel_id": channel_id}, to=sid)


@sio.event
async def leave_channel(sid, data):
    """
    Allows a user to leave a room/channel, except their private user room.
    """
    session, validation_error = await validate_socket_session_data(sid, data, sio)

    if validation_error:
        return

    channel_id = data.get("channel_id")
    if not channel_id:
        await sio.emit(
            "error",
            socket_error_payload("Missing channel_id"),
            to=sid,
        )
        return

    user_id = session["user_id"]
    if channel_id == f"user_{user_id}":
        await sio.emit(
            "error",
            socket_error_payload(
                "Cannot leave your private user channel.",
                code="FORBIDDEN",
            ),
            to=sid,
        )
        return

    await sio.leave_room(sid, channel_id)
    logger.info(f"User {user_id} (sid={sid}) left channel: {channel_id}")
    await sio.emit("channel_left", {"channel_id": channel_id}, to=sid)


@sio.event
async def ask_question(sid, data):
    """
    Handles user questions about uploaded documents via Socket.IO.
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

    service = ChatSocketService()
    user_id = session["user_id"]

    async for socket_event in service.ask_question_events(data, session):
        await emit_socket_event(sid, user_id, socket_event)


def is_channel_join_allowed(channel_id: str, user_id: str) -> bool:
    if channel_id == f"user_{user_id}":
        return True

    if channel_id.startswith("user_"):
        return False

    return channel_id.startswith(ALLOWED_CHANNEL_PREFIXES)
