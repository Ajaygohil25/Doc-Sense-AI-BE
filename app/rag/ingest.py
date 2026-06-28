from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging import get_logger
from app.rag.embeddings import get_embeddings
from app.rag.retriever import DEFAULT_VECTOR_STORE_DIR
from app.core.constants import INGESTED_STATUS, SUCCESS_STATUS, FAILED_STATUS
from app.core.database import get_transaction_session, AsyncSessionLocal
from app.repositories.chat_repository import create_chat_room
from app.repositories.file_upload import update_file_upload_status_repository

logger = get_logger(__name__)

import chromadb
from langchain_chroma import Chroma


async def ingest(
        pdf_path,
        file_id,
        user_id,
        persist_directory: str = DEFAULT_VECTOR_STORE_DIR,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
) -> None:
    try:
        logger.info(f"Loading PDF: {pdf_path}")

        #  Update the file upload status to 'ingested'
        async with get_transaction_session(AsyncSessionLocal) as db:
            await update_file_upload_status_repository(db, file_id, INGESTED_STATUS)

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_documents(documents)

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "file_id": file_id,
                "user_id": str(user_id),
                "chunk_index": i,
                "source": str(pdf_path),
            })

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
            await create_chat_room(db, file_id, user_id)

        logger.info(f"Created chat room for file_id={file_id}")
        logger.info(f"Successfully ingested {count} chunks for file_id={file_id}")

    except Exception as err:
        logger.error(f"Error ingesting PDF: {err}")

        async with get_transaction_session(AsyncSessionLocal) as db:
            await update_file_upload_status_repository(db, file_id, FAILED_STATUS)


