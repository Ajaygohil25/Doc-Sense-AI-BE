from datetime import datetime
import re
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, model_serializer

from app.schemas.base_schema import PaginationMeta


class FileUploadedByWithUserId(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str


class FileUploadResponse(BaseModel):
    id: UUID
    file_name: str
    status: str
    created_at: datetime
    uploaded_by: FileUploadedByWithUserId

    @model_serializer
    def serialize_model(self):
        # Remove "_<uuid>" from the filename if present
        pattern = r"_[0-9a-fA-F-]{36}"
        cleaned_filename = re.sub(pattern, "", self.file_name)

        return {
            "id": self.id,
            "file_name": cleaned_filename,
            "status": self.status,
            "created_at": self.created_at.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
            "uploaded_by": self.uploaded_by,
        }

    class Config:
        from_attributes = True

class FileUploadListSchema(BaseModel):
    file_list: list[FileUploadResponse]
    meta: PaginationMeta