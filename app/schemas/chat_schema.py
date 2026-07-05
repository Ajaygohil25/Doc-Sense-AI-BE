from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

class ChatRoomSchema(BaseModel):
    file_id: UUID
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


class ChatRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID | None = None
    project_id: UUID | None = None
    name: str
    created_at: datetime


class ChatRoomListResponse(BaseModel):
    chat_rooms: list[ChatRoomResponse]


class ChatQuestionSchema(BaseModel):
    file_id: UUID
    chat_room_id: UUID
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("Question is required")
        return question

class ChatMessageSchema(BaseModel):
    id: UUID
    room_id: UUID
    message: str
    sender: str
    created_at: datetime


class ChatMessageResponse(BaseModel):
    messages: list[ChatMessageSchema]
    chat_room_id: UUID


class ChatQuestionResponse(BaseModel):
    file_id: UUID
    chat_room_id: UUID
    question: str
    response: str
