import asyncio
import pytest
import pytest_asyncio
import socketio
import uvicorn
from main import socket_app
from app.config.env_config import settings

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
    Verifies that a user can ask a RAG question via Socket.IO and receives the reply.
    """
    from unittest.mock import patch, MagicMock
    
    sio_client = socketio.AsyncClient()
    replies = []
    errors = []
    
    @sio_client.on("question_response")
    def on_reply(data):
        replies.append(data)
        
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
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "Mocked RAG response answer"
    
    with patch("app.realtime.handlers.get_retriever", return_value=mock_retriever), \
         patch("app.realtime.handlers.get_chat_model", return_value=mock_model), \
         patch("app.realtime.handlers.build_rag_chain", return_value=mock_chain):
         
        await sio_client.emit("ask_question", {"file_id": "dummy_file_id", "question": "What is life?"})
        await asyncio.sleep(0.5)
        
    assert len(errors) == 0
    assert len(replies) == 1
    assert replies[0]["file_id"] == "dummy_file_id"
    assert replies[0]["question"] == "What is life?"
    assert replies[0]["response"] == "Mocked RAG response answer"
    
    await sio_client.disconnect()

