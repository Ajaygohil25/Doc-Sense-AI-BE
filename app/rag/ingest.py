import asyncio
from contextlib import asynccontextmanager
import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging import get_logger
from app.rag.embeddings import get_embeddings
from app.rag.retriever import DEFAULT_VECTOR_STORE_DIR
from app.core.constants import INGESTED_STATUS, SUCCESS_STATUS, FAILED_STATUS
from app.core.database import get_transaction_session, AsyncSessionLocal
from app.repositories.chat_repository import create_chat_room
from app.repositories.file_upload import update_file_upload_status_repository
from app.services.s3_service import S3Service

logger = get_logger(__name__)

import chromadb
from langchain_chroma import Chroma


@asynccontextmanager
async def pdf_source(pdf_path, s3_object_name=None):
    """Yield a local PDF path, materializing and cleaning up S3 objects."""
    if pdf_path:
        yield pdf_path
        return

    if not s3_object_name:
        raise ValueError("Either pdf_path or s3_object_name is required for ingestion")

    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix="doc-sense-ingest-",
        suffix=".pdf",
    )
    os.close(file_descriptor)

    try:
        downloaded = await asyncio.to_thread(
            S3Service().download_file,
            s3_object_name,
            temporary_path,
        )
        if not downloaded:
            raise RuntimeError("Failed to download PDF from S3 for ingestion")

        yield temporary_path
    finally:
        try:
            os.remove(temporary_path)
        except FileNotFoundError:
            pass


async def ingest(
        pdf_path,
        file_id,
        user_id,
        project_id=None,
        s3_object_name=None,
        persist_directory: str = DEFAULT_VECTOR_STORE_DIR,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
) -> None:
    try:
        logger.info(
            f"Loading PDF for file_id={file_id} from "
            f"{'S3' if s3_object_name else 'local storage'}"
        )

        #  Update the file upload status to 'ingested'
        async with get_transaction_session(AsyncSessionLocal) as db:
            await update_file_upload_status_repository(db, file_id, INGESTED_STATUS)

        async with pdf_source(pdf_path, s3_object_name) as resolved_pdf_path:
            loader = PyPDFLoader(resolved_pdf_path)
            documents = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            chunks = splitter.split_documents(documents)

            for i, chunk in enumerate(chunks):
                metadata = {
                    "file_id": file_id,
                    "user_id": str(user_id),
                    "chunk_index": i,
                    "source": str(s3_object_name or resolved_pdf_path),
                }
                if project_id:
                    metadata["project_id"] = str(project_id)
                chunk.metadata.update(metadata)

            embeddings = get_embeddings()

            # Use PersistentClient explicitly - more reliable
            client = chromadb.PersistentClient(path=persist_directory)

            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                client=client,
                collection_name="rag_collection",  # Explicit name (very important!)
                persist_directory=persist_directory,
            )

            count = vectorstore._collection.count()

        async with get_transaction_session(AsyncSessionLocal) as db:
            await update_file_upload_status_repository(db, file_id, SUCCESS_STATUS)
            if not project_id:
                await create_chat_room(db, file_id, user_id)

        if not project_id:
            logger.info(f"Created chat room for file_id={file_id}")
        logger.info(f"Successfully ingested {count} chunks for file_id={file_id}")

    except Exception as err:
        logger.error(f"Error ingesting PDF: {err}")

        async with get_transaction_session(AsyncSessionLocal) as db:
            await update_file_upload_status_repository(db, file_id, FAILED_STATUS)
