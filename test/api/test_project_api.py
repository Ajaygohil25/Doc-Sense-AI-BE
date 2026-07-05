import io
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.authentication.hashing import Hash
from app.core.database import TestAsyncSessionLocal
from app.models.chat_message_model import ChatMessage, ChatSenderEnum
from app.models.file_upload_model import FileUploadModel
from app.models.project_model import ProjectModel
from app.models.user_model import User


async def create_foreign_user():
    async with TestAsyncSessionLocal() as db_session:
        user = User(
            first_name="Foreign",
            last_name="Owner",
            email=f"foreign-{uuid4()}@test.com",
            password=Hash.encrypt("Admin@test123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user


async def create_project(owner_id, name="Foreign project"):
    async with TestAsyncSessionLocal() as db_session:
        project = ProjectModel(
            name=name,
            description="Project owned by another user",
            owner_id=owner_id,
        )
        project.created_by = owner_id
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project


@pytest.mark.asyncio
async def test_create_list_and_detail_project_with_default_chat_room(
    test_db,
    async_client,
    create_user,
    user_token,
    header,
):
    header["Authorization"] = f"Bearer {user_token}"

    create_response = await async_client.post(
        "/api/v1/projects",
        json={"name": "Research KB", "description": "Policy and research files"},
        headers=header,
    )

    assert create_response.status_code == 201
    project = create_response.json()["data"]["project"]
    assert project["name"] == "Research KB"
    assert project["description"] == "Policy and research files"
    assert project["owner_id"] == str(create_user.id)
    assert len(project["chat_rooms"]) == 1
    assert project["chat_rooms"][0]["name"] == "Default chat"
    assert project["chat_rooms"][0]["project_id"] == project["id"]
    assert project["chat_rooms"][0]["file_id"] is None

    list_response = await async_client.get("/api/v1/projects", headers=header)
    assert list_response.status_code == 200
    projects = list_response.json()["data"]["projects"]
    assert any(item["id"] == project["id"] for item in projects)

    detail_response = await async_client.get(
        f"/api/v1/projects/{project['id']}",
        headers=header,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]["project"]
    assert detail["id"] == project["id"]
    assert detail["files"] == []
    assert len(detail["chat_rooms"]) == 1

    rooms_response = await async_client.get(
        f"/api/v1/projects/{project['id']}/chat-rooms",
        headers=header,
    )
    assert rooms_response.status_code == 200
    rooms = rooms_response.json()["data"]["chat_rooms"]
    assert len(rooms) == 1
    assert rooms[0]["project_id"] == project["id"]

    messages_response = await async_client.get(
        f"/api/v1/projects/{project['id']}/chat-rooms/{rooms[0]['id']}/messages",
        headers=header,
    )
    assert messages_response.status_code == 200
    assert messages_response.json()["data"]["messages"] == []


@pytest.mark.asyncio
async def test_upload_file_to_project_sets_project_id_and_queues_ingest(
    test_db,
    async_client,
    user_token,
    header,
):
    header["Authorization"] = f"Bearer {user_token}"
    create_response = await async_client.post(
        "/api/v1/projects",
        json={"name": "Upload KB"},
        headers=header,
    )
    project_id = create_response.json()["data"]["project"]["id"]

    with patch("app.services.project_service.ingest") as mock_ingest:
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/files",
            files={"file": ("handbook.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")},
            headers={"Authorization": f"Bearer {user_token}"},
        )

    assert response.status_code == 201
    file_data = response.json()["data"]["file"]
    assert file_data["file_name"] == "handbook.pdf"
    assert file_data["project_id"] == project_id

    async with TestAsyncSessionLocal() as db_session:
        upload = await db_session.get(FileUploadModel, file_data["id"])

    assert str(upload.project_id) == project_id
    assert mock_ingest.call_count == 1
    assert mock_ingest.call_args.kwargs["file_id"] == file_data["id"]
    assert mock_ingest.call_args.kwargs["project_id"] == project_id


@pytest.mark.asyncio
async def test_project_ask_question_uses_project_retriever_and_stores_messages(
    test_db,
    async_client,
    user_token,
    header,
):
    header["Authorization"] = f"Bearer {user_token}"
    create_response = await async_client.post(
        "/api/v1/projects",
        json={"name": "Chat KB"},
        headers=header,
    )
    project = create_response.json()["data"]["project"]
    room_id = project["chat_rooms"][0]["id"]

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "Project answer"

    with patch("app.services.project_service.get_project_retriever", return_value=MagicMock()), \
         patch("app.services.project_service.get_chat_model", return_value=MagicMock()), \
         patch("app.services.project_service.build_rag_chain", return_value=mock_chain):
        response = await async_client.post(
            f"/api/v1/projects/{project['id']}/ask-question",
            json={"chat_room_id": room_id, "question": "Summarize the project"},
            headers=header,
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["project_id"] == project["id"]
    assert data["chat_room_id"] == room_id
    assert data["response"] == "Project answer"

    async with TestAsyncSessionLocal() as db_session:
        result = await db_session.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = result.scalars().all()

    assert [message.sender for message in messages] == [
        ChatSenderEnum.USER,
        ChatSenderEnum.ASSISTANT,
    ]
    assert messages[0].message == "Summarize the project"
    assert messages[1].message == "Project answer"


@pytest.mark.asyncio
async def test_project_routes_require_project_ownership(
    test_db,
    async_client,
    user_token,
    header,
):
    foreign_user = await create_foreign_user()
    foreign_project = await create_project(foreign_user.id)
    header["Authorization"] = f"Bearer {user_token}"

    detail_response = await async_client.get(
        f"/api/v1/projects/{foreign_project.id}",
        headers=header,
    )
    upload_response = await async_client.post(
        f"/api/v1/projects/{foreign_project.id}/files",
        files={"file": ("private.pdf", io.BytesIO(b"%PDF-1.4\n%%EOF"), "application/pdf")},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert detail_response.status_code == 404
    assert upload_response.status_code == 404
