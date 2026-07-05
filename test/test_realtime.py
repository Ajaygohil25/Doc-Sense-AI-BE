import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import socketio
import uvicorn
from main import socket_app
from app.config.env_config import settings
from app.models.chat_message_model import ChatSenderEnum
from app.realtime.services.chat_socket_service import ChatSocketService
from app.realtime.auth import _strip_bearer_prefix, _get_first_query_value


def test_socket_auth_strips_bearer_prefix():
    assert _strip_bearer_prefix("Bearer token-value") == "token-value"
    assert _strip_bearer_prefix("token-value") == "token-value"
    assert _strip_bearer_prefix("   ") is None


def test_socket_auth_reads_query_token_values():
    environ = {"QUERY_STRING": "transport=websocket&access_token=query-token"}

    assert _get_first_query_value(environ, "token", "access_token") == "query-token"

@pytest_asyncio.fixture(scope="module")
async def realtime_server(test_db):
    """
    Spins up the combined FastAPI + Socket.IO server in a background thread
    for integration testing.
    """
    import threading
    import time
    from main import app
    from app.core.database import get_db
    from test.conftest import override_get_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    config = uvicorn.Config(socket_app, host="127.0.0.1", port=8999, log_level="debug")
    server = uvicorn.Server(config)
    
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())
        
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    await asyncio.sleep(1.5)  # Wait for uvicorn thread to start and listen
    
    yield "http://127.0.0.1:8999"
    
    server.should_exit = True
    thread.join(timeout=3.0)
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_unauthorized_connection_fails(realtime_server):
    """
    Verifies that connections without a valid token are rejected.
    """
    sio_client = socketio.AsyncClient()
    with pytest.raises(Exception):
        await sio_client.connect(
            realtime_server,
            socketio_path="socket.io",
            auth={"token": "invalid_or_expired_token"}
        )
    
    if sio_client.connected:
        await sio_client.disconnect()

@pytest.mark.asyncio
async def test_authorized_connection_succeeds(realtime_server, user_token, create_user):
    """
    Verifies that connecting with a valid JWT token succeeds, and registers the connection.
    """
    sio_client = socketio.AsyncClient()
    connected_events = []
    
    @sio_client.on("connected")
    def on_connected(data):
        connected_events.append(data)
        
    await sio_client.connect(
        realtime_server,
        socketio_path="socket.io",
        auth={"token": user_token}
    )
    
    await asyncio.sleep(0.2)
    
    assert sio_client.connected
    assert len(connected_events) == 1
    assert connected_events[0]["user_id"] == str(create_user.id)
    
    await sio_client.disconnect()

@pytest.mark.asyncio
async def test_room_join_and_authorization(realtime_server, user_token, create_user):
    """
    Verifies room joining, room emission, and authorization check boundaries.
    """
    sio_client = socketio.AsyncClient()
    joined_events = []
    errors = []
    
    @sio_client.on("channel_joined")
    def on_joined(data):
        joined_events.append(data)
        
    @sio_client.on("error")
    def on_error(data):
        errors.append(data)
        
    await sio_client.connect(
        realtime_server,
        socketio_path="socket.io",
        auth={"token": user_token}
    )
    
    # 1. Join a generic room
    await sio_client.emit("join_channel", {"channel_id": "test_room"})
    await asyncio.sleep(0.2)
    assert len(joined_events) == 1
    assert joined_events[0]["channel_id"] == "test_room"
    
    # 2. Try to join an unauthorized private room of another user
    await sio_client.emit("join_channel", {"channel_id": "user_some_other_uuid"})
    await asyncio.sleep(0.2)
    assert len(errors) == 1
    assert "Forbidden" in errors[0]["message"]
    
    # 3. Join their own personal room (authorized)
    await sio_client.emit("join_channel", {"channel_id": f"user_{create_user.id}"})
    await asyncio.sleep(0.2)
    assert len(joined_events) == 2
    assert joined_events[1]["channel_id"] == f"user_{create_user.id}"
    
    await sio_client.disconnect()

@pytest.mark.asyncio
async def test_room_broadcast(realtime_server, user_token, create_user):
    """
    Verifies that a message emitted to a room reaches all subscribed clients.
    """
    sio_client = socketio.AsyncClient()
    received_broadcasts = []
    
    @sio_client.on("test_broadcast")
    def on_broadcast(data):
        received_broadcasts.append(data)
        
    await sio_client.connect(
        realtime_server,
        socketio_path="socket.io",
        auth={"token": user_token}
    )
    
    # Join test room
    await sio_client.emit("join_channel", {"channel_id": "broadcast_room"})
    await asyncio.sleep(0.2)
    
    # Use our server-side emission helper to broadcast to the room
    from app.realtime.handlers import emit_to_channel
    await emit_to_channel("broadcast_room", "test_broadcast", {"msg": "hello from backend"})
    await asyncio.sleep(0.2)
    
    assert len(received_broadcasts) == 1
    assert received_broadcasts[0]["msg"] == "hello from backend"
    
    await sio_client.disconnect()


@pytest.mark.asyncio
async def test_ask_question_rag(realtime_server, user_token, create_user):
    """
    Verifies that a user can ask a RAG question via Socket.IO and receives streamed chunks.
    """
    sio_client = socketio.AsyncClient()
    replies = []
    stream_starts = []
    stream_chunks = []
    stream_ends = []
    chat_messages = []
    errors = []
    
    class MockStreamingChain:
        async def astream(self, question):
            for chunk in ("Mocked ", "RAG response ", "answer"):
                yield chunk

    @sio_client.on("question_response")
    def on_reply(data):
        replies.append(data)

    @sio_client.on("question_response_start")
    def on_stream_start(data):
        stream_starts.append(data)

    @sio_client.on("question_response_chunk")
    def on_stream_chunk(data):
        stream_chunks.append(data)

    @sio_client.on("question_response_end")
    def on_stream_end(data):
        stream_ends.append(data)

    @sio_client.on("chat_message_created")
    def on_chat_message_created(data):
        chat_messages.append(data)
        
    @sio_client.on("error")
    def on_error(data):
        errors.append(data)
        
    await sio_client.connect(
        realtime_server,
        socketio_path="socket.io",
        auth={"token": user_token}
    )
    
    # Mock retriever, model, and chain to run completely locally without network/Hugging Face
    mock_retriever = MagicMock()
    mock_model = MagicMock()
    mock_chain = MockStreamingChain()
    mock_file = SimpleNamespace(id="dummy_file_id", uploaded_by=str(create_user.id))
    mock_chat_room = SimpleNamespace(id="dummy_chat_room_id")

    async def mock_store_chat_message(db_session, chat_room_id, sender, message):
        return SimpleNamespace(
            id=f"{sender.value}-message-id",
            room_id=chat_room_id,
            sender=sender,
            message=message,
            created_at=datetime(2026, 6, 26, 12, 0, 0),
        )
    
    with patch("app.realtime.services.chat_socket_service.get_retriever", return_value=mock_retriever), \
         patch("app.realtime.services.chat_socket_service.get_chat_model", return_value=mock_model), \
         patch("app.realtime.services.chat_socket_service.build_rag_chain", return_value=mock_chain), \
         patch("app.realtime.services.chat_socket_service.get_upload_file_history_by_id", new=AsyncMock(return_value=mock_file)), \
         patch("app.realtime.services.chat_socket_service.get_chat_room_for_file_and_user", new=AsyncMock(return_value=mock_chat_room)), \
         patch("app.realtime.services.chat_socket_service.store_chat_message", new=AsyncMock(side_effect=mock_store_chat_message)):
         
        await sio_client.emit("ask_question", {
            "file_id": "dummy_file_id",
            "chat_room_id": "dummy_chat_room_id",
            "question": "What is life?",
            "request_id": "request-1",
        })
        await asyncio.sleep(0.5)
        
    assert len(errors) == 0
    assert len(chat_messages) == 1
    assert chat_messages[0]["sender"] == "user"
    assert chat_messages[0]["message"] == "What is life?"
    assert chat_messages[0]["chat_room_id"] == "dummy_chat_room_id"
    assert chat_messages[0]["request_id"] == "request-1"
    assert len(stream_starts) == 1
    assert stream_starts[0]["file_id"] == "dummy_file_id"
    assert stream_starts[0]["chat_room_id"] == "dummy_chat_room_id"
    assert stream_starts[0]["request_id"] == "request-1"
    assert [event["chunk"] for event in stream_chunks] == ["Mocked ", "RAG response ", "answer"]
    assert len(stream_ends) == 1
    assert stream_ends[0]["response"] == "Mocked RAG response answer"
    assert stream_ends[0]["chat_room_id"] == "dummy_chat_room_id"
    assert len(replies) == 1
    assert replies[0]["file_id"] == "dummy_file_id"
    assert replies[0]["chat_room_id"] == "dummy_chat_room_id"
    assert replies[0]["question"] == "What is life?"
    assert replies[0]["response"] == "Mocked RAG response answer"
    
    await sio_client.disconnect()


@pytest.mark.asyncio
async def test_ask_question_rejects_mismatched_chat_room(realtime_server, user_token, create_user):
    """
    Verifies that Socket.IO questions cannot target a chat room outside the selected file/user scope.
    """
    sio_client = socketio.AsyncClient()
    errors = []

    @sio_client.on("error")
    def on_error(data):
        errors.append(data)

    await sio_client.connect(
        realtime_server,
        socketio_path="socket.io",
        auth={"token": user_token}
    )

    mock_file = SimpleNamespace(id="dummy_file_id", uploaded_by=str(create_user.id))

    with patch("app.realtime.services.chat_socket_service.get_upload_file_history_by_id", new=AsyncMock(return_value=mock_file)), \
         patch("app.realtime.services.chat_socket_service.get_chat_room_for_file_and_user", new=AsyncMock(return_value=None)):

        await sio_client.emit("ask_question", {
            "file_id": "dummy_file_id",
            "chat_room_id": "wrong_room_id",
            "question": "What is life?",
            "request_id": "request-mismatch",
        })
        await asyncio.sleep(0.2)

    assert len(errors) == 1
    assert errors[0]["code"] == "CHAT_ROOM_NOT_FOUND"
    assert errors[0]["chat_room_id"] == "wrong_room_id"
    assert errors[0]["request_id"] == "request-mismatch"

    await sio_client.disconnect()


@pytest.mark.asyncio
async def test_project_ask_question_events_include_project_id(create_user):
    class MockStreamingChain:
        async def astream(self, question):
            for chunk in ("Project ", "answer"):
                yield chunk

    service = ChatSocketService()
    project_id = "project-1"
    room_id = "project-room-1"
    session = {"user_id": str(create_user.id)}
    mock_project = SimpleNamespace(id=project_id, owner_id=str(create_user.id))
    mock_chat_room = SimpleNamespace(id=room_id)

    @asynccontextmanager
    async def fake_transaction_session(_session_factory):
        yield MagicMock()

    async def mock_store_chat_message(db_session, chat_room_id, sender, message):
        return SimpleNamespace(
            id=f"{sender.value}-message-id",
            room_id=chat_room_id,
            sender=sender,
            message=message,
            created_at=datetime(2026, 6, 26, 12, 0, 0),
        )

    with patch("app.realtime.services.chat_socket_service.get_project_by_id_for_user", new=AsyncMock(return_value=mock_project)), \
         patch("app.realtime.services.chat_socket_service.get_chat_room_for_project_and_user", new=AsyncMock(return_value=mock_chat_room)), \
         patch("app.realtime.services.chat_socket_service.get_project_retriever", return_value=MagicMock()), \
         patch("app.realtime.services.chat_socket_service.get_chat_model", return_value=MagicMock()), \
         patch("app.realtime.services.chat_socket_service.build_rag_chain", return_value=MockStreamingChain()), \
         patch("app.realtime.services.chat_socket_service.store_chat_message", new=AsyncMock(side_effect=mock_store_chat_message)), \
         patch("app.realtime.services.chat_socket_service.get_transaction_session", fake_transaction_session), \
         patch.object(service, "fetch_previous_messages", new=AsyncMock(return_value=None)):
        events = [
            event async for event in service.ask_question_events(
                {
                    "project_id": project_id,
                    "chat_room_id": room_id,
                    "question": "What is in this project?",
                    "request_id": "project-request-1",
                },
                session,
            )
        ]

    event_names = [event.event for event in events]
    assert event_names == [
        "chat_message_created",
        "question_response_start",
        "question_response_chunk",
        "question_response_chunk",
        "question_response_end",
        "question_response",
    ]
    assert events[0].data["project_id"] == project_id
    assert events[0].data["sender"] == ChatSenderEnum.USER.value
    assert events[1].data["project_id"] == project_id
    assert events[-1].data["project_id"] == project_id
    assert events[-1].data["chat_room_id"] == room_id
    assert events[-1].data["response"] == "Project answer"
