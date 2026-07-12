from datetime import datetime
import re
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer

from app.schemas.chat_schema import ChatRoomResponse


class ProjectCreateSchema(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Project name is required")
        if len(name) > 120:
            raise ValueError("Project name must be 120 characters or fewer")
        return name

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        return description or None


class ProjectFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    status: str
    project_id: UUID | None = None
    created_at: datetime

    @model_serializer
    def serialize_model(self):
        pattern = r"_[0-9a-fA-F-]{36}"
        cleaned_filename = re.sub(pattern, "", self.file_name)

        return {
            "id": self.id,
            "file_name": cleaned_filename,
            "status": self.status,
            "project_id": self.project_id,
            "created_at": self.created_at.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
        }


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    files: list[ProjectFileResponse] = Field(default_factory=list)
    chat_rooms: list[ChatRoomResponse] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


class ProjectChatRoomCreateSchema(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Chat room name is required")
        if len(name) > 120:
            raise ValueError("Chat room name must be 120 characters or fewer")
        return name


class ProjectQuestionSchema(BaseModel):
    chat_room_id: UUID
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question is required")
        return question


class ProjectQuestionResponse(BaseModel):
    project_id: UUID
    chat_room_id: UUID
    question: str
    response: str
