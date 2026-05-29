from datetime import datetime
from typing import Optional, Generic, TypeVar
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# T can be any Pydantic model, dict, list, etc.
T = TypeVar("T")

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[T] = None

    def to_response(self, status_code: int = 200) -> JSONResponse:
        return JSONResponse(status_code=status_code, content=jsonable_encoder(self))

    @classmethod
    def success_response(
            cls,
            data: Optional[T] = None,
            message: str = "Success",
            status_code: int = 200,
    ) -> JSONResponse:
        return cls(
            success=True,
            message=message,
            error=None,
            data=data
        ).to_response(status_code=status_code)

    @classmethod
    def error_response(
            cls,
            error_message: str,
            status_code: int = 400
    ) -> JSONResponse:
        return cls(
            success=False,
            message=None,
            error=error_message,
            data=None
        ).to_response(status_code=status_code)
