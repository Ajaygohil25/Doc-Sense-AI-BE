from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ChatRoomSchema(BaseModel):
    file_id: UUID
