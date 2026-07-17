import asyncio
from datetime import datetime, timezone
from tempfile import SpooledTemporaryFile
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException
from starlette.datastructures import Headers, UploadFile

from app.services import file_upload_service, project_service


def make_upload() -> UploadFile:
    file_object = SpooledTemporaryFile()
    file_object.write(b"%PDF-1.7\n%%EOF")
    file_object.seek(0)
    return UploadFile(
        file_object,
        filename="document.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )


def make_upload_record(project_id=None):
    return SimpleNamespace(
        id=uuid4(),
        file_name="document.pdf",
        status="Initiated",
        project_id=project_id,
        created_at=datetime.now(timezone.utc),
    )


def run_executor_inline(monkeypatch):
    loop = asyncio.get_running_loop()

    def run_in_executor(_executor, callback):
        future = loop.create_future()
        try:
            future.set_result(callback())
        except Exception as error:
            future.set_exception(error)
        return future

    monkeypatch.setattr(loop, "run_in_executor", run_in_executor)


@pytest.mark.asyncio
async def test_individual_s3_upload_queues_ingestion_with_object_name(monkeypatch):
    run_executor_inline(monkeypatch)
    upload_record = make_upload_record()
    s3_service = MagicMock()
    s3_service.upload_file.return_value = True
    background_tasks = BackgroundTasks()
    user_id = uuid4()

    monkeypatch.setattr(file_upload_service.settings, "IS_ON_S3", True)
    monkeypatch.setattr(file_upload_service, "is_valid_file", AsyncMock(return_value=True))
    monkeypatch.setattr(
        file_upload_service,
        "input_file_upload_repository",
        AsyncMock(return_value=upload_record),
    )
    monkeypatch.setattr(
        file_upload_service,
        "get_user_by_user_id",
        AsyncMock(return_value=SimpleNamespace(first_name="Test", last_name="User")),
    )
    monkeypatch.setattr(file_upload_service, "S3Service", lambda: s3_service)

    await file_upload_service.FileService(MagicMock()).upload_file_service(
        make_upload(),
        SimpleNamespace(user_id=user_id),
        background_tasks,
    )

    assert len(background_tasks.tasks) == 1
    ingest_task = background_tasks.tasks[0]
    assert ingest_task.kwargs["pdf_path"] is None
    assert ingest_task.kwargs["s3_object_name"] == upload_record.file_name
    s3_service.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_project_s3_upload_queues_ingestion_with_object_name(monkeypatch):
    run_executor_inline(monkeypatch)
    project_id = uuid4()
    upload_record = make_upload_record(project_id=project_id)
    s3_service = MagicMock()
    s3_service.upload_file.return_value = True
    background_tasks = BackgroundTasks()
    service = project_service.ProjectService(MagicMock())
    service._get_owned_project = AsyncMock(return_value=SimpleNamespace(id=project_id))

    monkeypatch.setattr(project_service.settings, "IS_ON_S3", True)
    monkeypatch.setattr(project_service, "is_valid_file", AsyncMock(return_value=True))
    monkeypatch.setattr(
        project_service,
        "input_file_upload_repository",
        AsyncMock(return_value=upload_record),
    )
    monkeypatch.setattr(project_service, "S3Service", lambda: s3_service)

    await service.upload_project_file_service(
        project_id,
        make_upload(),
        SimpleNamespace(user_id=uuid4()),
        background_tasks,
    )

    assert len(background_tasks.tasks) == 1
    ingest_task = background_tasks.tasks[0]
    assert ingest_task.kwargs["pdf_path"] is None
    assert ingest_task.kwargs["s3_object_name"] == upload_record.file_name
    assert ingest_task.kwargs["project_id"] == str(project_id)
    s3_service.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_s3_upload_failure_returns_bad_gateway(monkeypatch):
    run_executor_inline(monkeypatch)
    upload_record = make_upload_record()
    s3_service = MagicMock()
    s3_service.upload_file.return_value = False

    monkeypatch.setattr(file_upload_service.settings, "IS_ON_S3", True)
    monkeypatch.setattr(file_upload_service, "is_valid_file", AsyncMock(return_value=True))
    monkeypatch.setattr(
        file_upload_service,
        "input_file_upload_repository",
        AsyncMock(return_value=upload_record),
    )
    monkeypatch.setattr(
        file_upload_service,
        "get_user_by_user_id",
        AsyncMock(return_value=SimpleNamespace(first_name="Test", last_name="User")),
    )
    monkeypatch.setattr(file_upload_service, "S3Service", lambda: s3_service)

    with pytest.raises(HTTPException, match="Failed to upload PDF to S3") as exc_info:
        await file_upload_service.FileService(MagicMock()).upload_file_service(
            make_upload(),
            SimpleNamespace(user_id=uuid4()),
            BackgroundTasks(),
        )

    assert exc_info.value.status_code == 502
