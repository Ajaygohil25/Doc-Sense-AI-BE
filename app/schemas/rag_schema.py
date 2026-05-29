from uuid import UUID

from pydantic import BaseModel

class UserQuestionSchema(BaseModel):
    file_id: UUID
    question: str

