from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.database import TestAsyncSessionLocal
from app.core.constants import SUCCESS_STATUS
from app.models.chat_message_model import ChatMessage, ChatSenderEnum
from app.models.chat_room_model import ChatRoom
from app.models.file_upload_model import FileUploadModel


async def create_uploaded_file(user_id, status=SUCCESS_STATUS):
    async with TestAsyncSessionLocal() as db_session:
        upload = FileUploadModel(
            file_name=f"chat-test-{uuid4()}.pdf",
            status=status,
            uploaded_by=user_id,
            is_on_s3_bucket=False,
        )
        upload.created_by = user_id
        db_session.add(upload)
        await db_session.commit()
        await db_session.refresh(upload)
        return upload


async def create_room(file_id, user_id, name="Default chat"):
    async with TestAsyncSessionLocal() as db_session:
        room = ChatRoom(file_id=file_id, name=name)
        room.created_by = user_id
        db_session.add(room)
        await db_session.commit()
        await db_session.refresh(room)
        return room


@pytest.mark.asyncio
async def test_create_and_list_named_chat_rooms(test_db, async_client, create_user, user_token, header):
    upload = await create_uploaded_file(create_user.id)
    header["Authorization"] = f"Bearer {user_token}"

    create_response = await async_client.post(
        "/api/v1/chat/create-chat-room",
        json={"file_id": str(upload.id), "name": "Policy questions"},
        headers=header,
    )

    assert create_response.status_code == 201
    create_data = create_response.json()["data"]["chat_room"]
    assert create_data["file_id"] == str(upload.id)
    assert create_data["name"] == "Policy questions"

    list_response = await async_client.get(
        f"/api/v1/chat/get-chat-rooms-by-file-id/{upload.id}",
        headers=header,
    )

    assert list_response.status_code == 200
    rooms = list_response.json()["data"]["chat_rooms"]
    assert rooms[0]["id"] == create_data["id"]
    assert rooms[0]["name"] == "Policy questions"


@pytest.mark.asyncio
async def test_create_chat_room_requires_name(test_db, async_client, create_user, user_token, header):
    upload = await create_uploaded_file(create_user.id)
    header["Authorization"] = f"Bearer {user_token}"

    response = await async_client.post(
        "/api/v1/chat/create-chat-room",
        json={"file_id": str(upload.id), "name": "   "},
        headers=header,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_message_history_requires_room_ownership(test_db, async_client, create_user, user_token, header):
    upload = await create_uploaded_file(create_user.id)
    foreign_room = await create_room(upload.id, uuid4(), name="Other user's room")
    header["Authorization"] = f"Bearer {user_token}"

    response = await async_client.get(
        f"/api/v1/chat/get-chat-messages-by-room-id/{foreign_room.id}",
        headers=header,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rest_ask_question_stores_messages(test_db, async_client, create_user, user_token, header):
    upload = await create_uploaded_file(create_user.id)
    room = await create_room(upload.id, create_user.id, name="REST fallback")
    header["Authorization"] = f"Bearer {user_token}"

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "REST answer"

    with patch("app.services.chat_service.get_retriever", return_value=MagicMock()), \
         patch("app.services.chat_service.get_chat_model", return_value=MagicMock()), \
         patch("app.services.chat_service.build_rag_chain", return_value=mock_chain):
        response = await async_client.post(
            "/api/v1/chat/ask-question",
            json={
                "file_id": str(upload.id),
                "chat_room_id": str(room.id),
                "question": "Summarize this file",
            },
            headers=header,
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["chat_room_id"] == str(room.id)
    assert data["response"] == "REST answer"

    async with TestAsyncSessionLocal() as db_session:
        result = await db_session.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room.id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = result.scalars().all()

    assert [message.sender for message in messages] == [
        ChatSenderEnum.USER,
        ChatSenderEnum.ASSISTANT,
    ]
    assert messages[0].message == "Summarize this file"
    assert messages[1].message == "REST answer"
