from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.core.constants import INVALID_REQUEST_PAYLOAD, \
    UNEXPECTED_ERROR_MESSAGE
from app.schemas.base_schema import APIResponse


def add_exception_handlers(app: FastAPI):
    """
    Registers custom exception handlers for the FastAPI application.

    This function adds handlers for HTTP exceptions, request validation errors,
    and general exceptions to provide consistent error responses.

    Args:
        app: The FastAPI application instance to which the exception handlers will be added.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Intercepts FastAPI HTTPExceptions and wraps in APIResponse"""
        return APIResponse.error_response(
            error_message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handles request validation errors"""
        return APIResponse.error_response(
            error_message=INVALID_REQUEST_PAYLOAD,
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catches all unhandled exceptions"""
        return APIResponse.error_response(
            error_message=UNEXPECTED_ERROR_MESSAGE,
            status_code=500,
        )

class S3ServiceUnavailableError(Exception):
    """Custom exception for S3 service unavailability"""
    pass