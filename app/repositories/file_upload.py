from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.constants import INITIATED_STATUS_PENDING
from app.core.logging import get_logger
from app.models.file_upload_model import FileUploadModel

logger = get_logger(__name__)


async def input_file_upload_repository(file_name, db, user_id, is_on_s3_bucket):
    try:
        file_upload = FileUploadModel(
            file_name=file_name,
            status=INITIATED_STATUS_PENDING,
            uploaded_by=user_id,
            is_on_s3_bucket = is_on_s3_bucket
        )
        file_upload.created_by = user_id
        db.add(file_upload)
        await db.commit()
        await db.refresh(file_upload)
        return file_upload
    except Exception as e:
        logger.error(f"Error in uploading file repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_upload_file_history_repository(db: AsyncSession, user_id, limit: int, offset: int):
    """
       Retrieve the history of uploaded files, ordered by creation date in descending order.

       Args:
           db: An asynchronous SQLAlchemy session.
           user_id: Id of the user
           limit: Maximum number of records to return.
           offset: Number of records to skip.

       Returns:
           A tuple containing (list of file upload records, total count).

       Raises:
           HTTPException: If an error occurs during the database query.
       """
    try:
        # Get total count
        total_stmt = select(func.count(FileUploadModel.id   ))
        total = (await db.execute(total_stmt)).scalar_one()

        # Get paginated items
        items_stmt = (
            select(FileUploadModel)
            .where(FileUploadModel.uploaded_by == user_id)
            .options(joinedload(FileUploadModel.user))
            .order_by(FileUploadModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = (await db.execute(items_stmt)).scalars().all()

        return items, total

    except Exception as e:
        await db.rollback()
        logger.error(f"Error in uploading file repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_upload_file_history_by_id(db: AsyncSession, upload_file_id):
    """
       Retrieve the upload file history by a specific file ID.

       Args:
           db: An asynchronous SQLAlchemy session.
           upload_file_id: The ID of the uploaded file to retrieve.

       Returns:
           The file upload record if found, otherwise None.

       Raises:
           HTTPException: If an error occurs during the database query.
       """

    try:
        result = await db.execute(
            select(FileUploadModel)
            .where(FileUploadModel.id == upload_file_id)
            .options(joinedload(FileUploadModel.user))
        )
        return result.scalar_one_or_none()

    except Exception as e:
        await db.rollback()
        logger.error(f"Error in uploading file repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_file_upload_status_repository(db: AsyncSession, file_id, status):
    """
       Update the status of an uploaded file.

       Args:
           db: An asynchronous SQLAlchemy session.
           file_id: The ID of the uploaded file to update.
           status: The new status to set for the uploaded file.

       Returns:
           The updated file upload record if found and updated, otherwise None.

       Raises:
           HTTPException: If an error occurs during the database query.
       """
    try:
        result = await db.execute(
            select(FileUploadModel)
            .where(FileUploadModel.id == file_id)
        )
        file_upload = result.scalar_one_or_none()

        if file_upload is None:
            return None

        file_upload.status = status
        await db.flush()
        return file_upload

    except Exception as e:
        await db.rollback()
        logger.error(f"Error in updating file upload status repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))