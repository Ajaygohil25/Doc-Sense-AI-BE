import asyncio
import os
from functools import partial
from uuid import UUID

from fastapi import HTTPException

from app.config.env_config import settings
from app.core.constants import FILE_UPLOAD_SUCCESS, UNEXPECTED_ERROR, UNEXPECTED_ERROR_MESSAGE
from app.core.logging import get_logger
from app.rag.chain import build_rag_chain
from app.rag.ingest import ingest
from app.rag.query import get_chat_model
from app.rag.retriever import get_project_retriever
from app.repositories.chat_repository import (
    create_project_chat_room,
    get_chat_messages_by_room_id,
    get_chat_room_by_project_id,
    get_chat_room_for_project_and_user,
    store_question_and_its_response_to_chat_message_model,
)
from app.repositories.file_upload import (
    get_project_files_repository,
    input_file_upload_repository,
)
from app.repositories.project_repository import (
    create_project,
    get_project_by_id_for_user,
    get_project_detail_for_user,
    get_projects_for_user,
)
from app.schemas.base_schema import APIResponse
from app.schemas.chat_schema import (
    ChatMessageResponse,
    ChatMessageSchema,
    ChatRoomListResponse,
    ChatRoomResponse,
)
from app.schemas.project_schema import (
    ProjectDetailResponse,
    ProjectFileResponse,
    ProjectListResponse,
    ProjectQuestionResponse,
    ProjectResponse,
)
from app.services.s3_service import S3Service
from app.utils.socket_validations import is_injection_attempt
from app.utils.util_functions import save_file_to_disk
from app.utils.validations import is_valid_file

logger = get_logger(__name__)


class ProjectService:
    def __init__(self, db):
        self.db = db

    async def _get_owned_project(self, project_id, user_id):
        project = await get_project_by_id_for_user(self.db, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    async def _get_owned_project_room(self, project_id, room_id, user_id):
        chat_room = await get_chat_room_for_project_and_user(self.db, room_id, project_id, user_id)
        if not chat_room:
            raise HTTPException(status_code=404, detail="Chat room not found")
        return chat_room

    async def create_project_service(self, current_user, payload):
        try:
            user_id = current_user.user_id
            project = await create_project(self.db, payload.name, payload.description, user_id)
            chat_room = await create_project_chat_room(self.db, project.id, user_id)
            await self.db.refresh(project)
            await self.db.refresh(chat_room)

            project_response = ProjectDetailResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                owner_id=project.owner_id,
                created_at=project.created_at,
                files=[],
                chat_rooms=[ChatRoomResponse.model_validate(chat_room)],
            )

            return APIResponse.success_response(
                message="Project created successfully",
                status_code=201,
                data={"project": project_response},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating project: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def list_projects_service(self, current_user):
        try:
            projects = await get_projects_for_user(self.db, current_user.user_id)
            payload = ProjectListResponse(
                projects=[ProjectResponse.model_validate(project) for project in projects]
            )
            return APIResponse.success_response(
                message="Projects retrieved successfully",
                status_code=200,
                data=payload,
            )
        except Exception as e:
            logger.exception(f"Error listing projects: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def get_project_detail_service(self, current_user, project_id: UUID):
        try:
            project = await get_project_detail_for_user(self.db, project_id, current_user.user_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            payload = self._project_detail_payload(project)
            return APIResponse.success_response(
                message="Project retrieved successfully",
                status_code=200,
                data={"project": payload},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting project detail: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def upload_project_file_service(self, project_id: UUID, file, current_user, background_tasks):
        try:
            user_id = current_user.user_id
            await self._get_owned_project(project_id, user_id)
            is_on_s3_bucket = settings.IS_ON_S3

            if await is_valid_file(file):
                upload_file_obj = await input_file_upload_repository(
                    file.filename,
                    self.db,
                    user_id,
                    is_on_s3_bucket,
                    project_id=project_id,
                )

            original_name = upload_file_obj.file_name
            name, ext = os.path.splitext(original_name)
            file_name_with_id = f"{name}_{upload_file_obj.id}{ext}"
            upload_file_obj.file_name = file_name_with_id

            file_path = None
            s3_object_name = None
            if not is_on_s3_bucket:
                file_path = await save_file_to_disk(file, upload_dir="Uploaded files", file_name=file_name_with_id)
            else:
                s3_service = S3Service()
                loop = asyncio.get_running_loop()
                uploaded = await loop.run_in_executor(
                    None,
                    partial(s3_service.upload_file, file.file, file_name_with_id),
                )
                if not uploaded:
                    raise HTTPException(
                        status_code=502,
                        detail="Failed to upload PDF to S3.",
                    )
                s3_object_name = file_name_with_id

            background_tasks.add_task(
                ingest,
                pdf_path=file_path,
                s3_object_name=s3_object_name,
                file_id=str(upload_file_obj.id),
                user_id=user_id,
                project_id=str(project_id),
            )

            return APIResponse.success_response(
                message=FILE_UPLOAD_SUCCESS,
                status_code=201,
                data={"file": ProjectFileResponse.model_validate(upload_file_obj)},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error uploading project file: {e}")
            raise HTTPException(status_code=400, detail=f"File validation/upload failed: {e}")

    async def list_project_files_service(self, current_user, project_id: UUID):
        try:
            await self._get_owned_project(project_id, current_user.user_id)
            files = await get_project_files_repository(self.db, project_id, current_user.user_id)
            return APIResponse.success_response(
                message="Project files retrieved successfully",
                status_code=200,
                data={"files": [ProjectFileResponse.model_validate(file) for file in files]},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error listing project files: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def create_project_chat_room_service(self, current_user, project_id: UUID, payload):
        try:
            await self._get_owned_project(project_id, current_user.user_id)
            chat_room = await create_project_chat_room(self.db, project_id, current_user.user_id, payload.name)
            await self.db.refresh(chat_room)

            return APIResponse.success_response(
                message="Chat room created successfully",
                status_code=201,
                data={"chat_room": ChatRoomResponse.model_validate(chat_room)},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating project chat room: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def list_project_chat_rooms_service(self, current_user, project_id: UUID):
        try:
            await self._get_owned_project(project_id, current_user.user_id)
            chat_rooms = await get_chat_room_by_project_id(self.db, project_id, current_user.user_id)
            payload = ChatRoomListResponse(
                chat_rooms=[ChatRoomResponse.model_validate(room) for room in chat_rooms]
            )
            return APIResponse.success_response(
                message="Chat rooms retrieved successfully",
                status_code=200,
                data=payload,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error listing project chat rooms: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def get_project_chat_messages_service(self, current_user, project_id: UUID, room_id: UUID):
        try:
            await self._get_owned_project(project_id, current_user.user_id)
            await self._get_owned_project_room(project_id, room_id, current_user.user_id)
            chat_messages = await get_chat_messages_by_room_id(self.db, room_id)

            payload = ChatMessageResponse(
                messages=[
                    ChatMessageSchema(
                        id=message.id,
                        room_id=message.room_id,
                        message=message.message,
                        sender=message.sender.value,
                        created_at=message.created_at,
                    )
                    for message in chat_messages
                ],
                chat_room_id=room_id,
            )
            return APIResponse.success_response(
                message="Chat messages retrieved successfully",
                status_code=200,
                data=payload,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting project chat messages: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    async def ask_project_question_service(self, current_user, project_id: UUID, payload):
        try:
            user_id = current_user.user_id
            await self._get_owned_project(project_id, user_id)
            chat_room = await self._get_owned_project_room(project_id, payload.chat_room_id, user_id)

            is_suspicious, reason = is_injection_attempt(payload.question)
            if is_suspicious:
                raise HTTPException(
                    status_code=400,
                    detail=f"I can only answer questions based on the uploaded documents. {reason}",
                )

            retriever = get_project_retriever(project_id, user_id)
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
                data=ProjectQuestionResponse(
                    project_id=project_id,
                    chat_room_id=chat_room.id,
                    question=payload.question,
                    response=response_text,
                ),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error answering project question: {e}")
            raise HTTPException(status_code=500, detail=UNEXPECTED_ERROR_MESSAGE)

    def _project_detail_payload(self, project):
        return ProjectDetailResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            created_at=project.created_at,
            files=[ProjectFileResponse.model_validate(file) for file in project.files],
            chat_rooms=[ChatRoomResponse.model_validate(room) for room in project.chat_rooms],
        )
