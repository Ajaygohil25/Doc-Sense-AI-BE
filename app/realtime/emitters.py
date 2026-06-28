import logging
from dataclasses import dataclass

from app.realtime.socket_server import sio

logger = logging.getLogger("app.realtime.emitters")


@dataclass(frozen=True)
class SocketEvent:
    event: str
    data: dict
    target: str = "user"


def with_request_id(payload: dict, request_id: str | None) -> dict:
    if not request_id:
        return payload

    return {**payload, "request_id": request_id}


def with_request_context(payload: dict, request_id: str | None, chat_room_id=None) -> dict:
    enriched_payload = with_request_id(payload, request_id)

    if chat_room_id:
        enriched_payload = {**enriched_payload, "chat_room_id": str(chat_room_id)}

    return enriched_payload


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


async def emit_socket_event(sid: str, user_id: str, socket_event: SocketEvent):
    if socket_event.target == "sid":
        await sio.emit(socket_event.event, socket_event.data, to=sid)
        return

    await emit_to_user(
        user_id=user_id,
        event=socket_event.event,
        data=socket_event.data,
    )
