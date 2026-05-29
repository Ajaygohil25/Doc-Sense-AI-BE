import asyncio
import os
from functools import partial
from uuid import UUID

from fastapi import HTTPException

from app.config.env_config import settings
from app.core.constants import (FILE_UPLOAD_SUCCESS, FILE_UPLOAD_HISTORY, FILE_HISTORY_NOT_FOUND,
                                YOU_DONT_HAVE_ENOUGH_PERMISSIONS)
from app.core.constants import (
    LOG_VALIDATE_OR_UPLOAD_FILE_FAILED,
)
from app.core.logging import get_logger
from app.repositories.file_upload import input_file_upload_repository, get_upload_file_history_repository, \
    get_upload_file_history_by_id
from app.repositories.user_repositories import get_user_by_user_id
from app.schemas.base_schema import APIResponse, PaginationMeta
from app.schemas.file_upload_schema import FileUploadResponse, FileUploadedByWithUserId, FileUploadListSchema
from app.services.s3_service import S3Service
from app.utils.util_functions import save_file_to_disk
from app.utils.validations import is_valid_file
from app.rag.ingest import ingest

logger = get_logger(__name__)


class FileService:

    def __init__(self, db):
        self.db = db

    async def upload_file_service(self, file, current_user, background_tasks):
        """
        Handles the file upload process, including validation, saving the file to disk,
        and initiating the reconciliation process in the background.

        Args:
            file: The file object to be uploaded.
            current_user: The user performing the upload.


        Returns:
            APIResponse: A success response containing the file upload details.
        """
        try:
            response_message = FILE_UPLOAD_SUCCESS
            is_on_s3_bucket = settings.IS_ON_S3

            file_name = None
            file_path = None
            file_id = None
            upload_file_obj = None

            # if not searched by sku, validate the file
            if await is_valid_file(file):
                file_name = file.filename
                upload_file_obj = await input_file_upload_repository(file_name, self.db,
                                                                     current_user.user_id, is_on_s3_bucket)
                file_id = upload_file_obj.id

            user_data = await get_user_by_user_id(current_user.user_id, self.db)

            # rename a file with uuid to avoid duplicate file name
            original_name = file_name
            name, ext = os.path.splitext(original_name)
            file_name_with_id = f"{name}_{file_id}{ext}"

            upload_file_obj.file_name = file_name_with_id

            if not is_on_s3_bucket:
                # save a file to disk with a new name
                file_path = await save_file_to_disk(file, upload_dir="Uploaded files", file_name=file_name_with_id)
            else:
                # deploy to s3
                s3_service = S3Service()
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    partial(s3_service.upload_file, file.file, file_name_with_id)
                )

            # add embeddings create process in the background
            background_tasks.add_task(
                ingest,
                pdf_path = file_path,
                file_id = str(file_id),
                user_id = current_user.user_id
            )

            return APIResponse.success_response(
                message=response_message,
                status_code=201,
                data=FileUploadResponse(
                    id=upload_file_obj.id,
                    file_name=upload_file_obj.file_name,
                    status=upload_file_obj.status,
                    created_at=upload_file_obj.created_at,
                    uploaded_by=FileUploadedByWithUserId(
                        user_id=current_user.user_id,
                        first_name=user_data.first_name,
                        last_name=user_data.last_name
                    )
                )
            )

        except HTTPException as e:
            raise e

        except Exception as e:
            logger.exception(LOG_VALIDATE_OR_UPLOAD_FILE_FAILED, getattr(file, "filename", "unknown"))
            raise HTTPException(status_code=400, detail=f"File validation/upload failed: {e}")


    async def get_upload_file_history(self, user_id, page: int = 1, page_size: int = 20):
        try:
            page = max(page, 1)
            page_size = max(page_size, 5)
            offset = (page - 1) * page_size

            file_history_result, total = await get_upload_file_history_repository(self.db, user_id, page_size, offset)

            if not file_history_result:
                return APIResponse.success_response(message="No file history found.", status_code=200, data={})

            # Build the file list by processing each row separately
            file_list = []
            for row in file_history_result:

                file_response = FileUploadResponse(
                    id=row.id,
                    file_name=row.file_name,
                    status=row.status,
                    uploaded_by=FileUploadedByWithUserId(
                        user_id=row.user.id,
                        first_name=(row.user.first_name if row.user else ""),
                        last_name=(row.user.last_name if row.user else "")
                    ),
                    created_at=row.created_at,
                )
                file_list.append(file_response)

            payload = FileUploadListSchema(
                file_list=file_list,
                meta=PaginationMeta(
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=(total + page_size - 1) // page_size if page_size > 0 else 0
                )
            )

            return APIResponse.success_response(
                message=FILE_UPLOAD_HISTORY,
                status_code=200,
                data=payload
            )

        except Exception as e:
            logger.error(f"Error fetching file history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            await self.db.close()

    async def get_upload_file_by_file_id(self, upload_file_id: UUID, user_id):
        try:
            file_history = await get_upload_file_history_by_id(self.db, upload_file_id)

            if not file_history:
                raise HTTPException(status_code=404, detail=FILE_HISTORY_NOT_FOUND)

            if file_history.uploaded_by != user_id:
                raise HTTPException(status_code=401, detail=YOU_DONT_HAVE_ENOUGH_PERMISSIONS)

            return APIResponse.success_response(
                message=FILE_UPLOAD_HISTORY,
                status_code=200,
                data=FileUploadResponse(
                    id=file_history.id,
                    file_name=file_history.file_name,
                    status=file_history.status,
                    created_at=file_history.created_at,
                    uploaded_by=FileUploadedByWithUserId(
                        user_id=file_history.user.id,
                        first_name=(file_history.user.first_name if file_history.user else ""),
                        last_name=(file_history.user.last_name if file_history.user else "")
                    )
                )
            )

        except Exception as e:
            logger.error(f"Error fetching file history: {e}")
            raise e