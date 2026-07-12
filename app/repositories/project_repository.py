from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.project_model import ProjectModel

logger = get_logger(__name__)


async def create_project(db, name, description, owner_id):
    try:
        project = ProjectModel(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        project.created_by = owner_id
        db.add(project)
        await db.flush()
        return project
    except Exception as e:
        logger.error(f"Error creating project repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_projects_for_user(db, user_id):
    try:
        result = await db.execute(
            select(ProjectModel)
            .where(ProjectModel.owner_id == user_id)
            .order_by(ProjectModel.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing projects repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_project_by_id_for_user(db, project_id, user_id):
    try:
        result = await db.execute(
            select(ProjectModel)
            .where(
                ProjectModel.id == project_id,
                ProjectModel.owner_id == user_id,
            )
        )
        return result.scalars().one_or_none()
    except Exception as e:
        logger.error(f"Error getting project repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_project_detail_for_user(db, project_id, user_id):
    try:
        result = await db.execute(
            select(ProjectModel)
            .where(
                ProjectModel.id == project_id,
                ProjectModel.owner_id == user_id,
            )
            .options(
                selectinload(ProjectModel.files),
                selectinload(ProjectModel.chat_rooms),
            )
        )
        return result.scalars().one_or_none()
    except Exception as e:
        logger.error(f"Error getting project detail repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))
