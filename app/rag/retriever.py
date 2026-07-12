from langchain_chroma import Chroma
from langchain_core.retrievers import BaseRetriever

from app.rag.embeddings import get_embeddings

DEFAULT_VECTOR_STORE_DIR = "vector_store"


def get_vector_store(persist_directory: str = DEFAULT_VECTOR_STORE_DIR) -> Chroma:
    """Open the persisting Chroma vector store."""
    return Chroma(
        collection_name="rag_collection",
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
    )


def get_retriever(
    file_id,
    user_id,
    persist_directory: str = DEFAULT_VECTOR_STORE_DIR,
    k: int = 3,
) -> BaseRetriever:
    """Create a similarity retriever over the persisted store."""
    db = get_vector_store(persist_directory=persist_directory)
    return db.as_retriever(search_type="similarity", search_kwargs={
        "k": k,
        "filter": {
            "$and": [
                {"file_id": str(file_id)},
                {"user_id": str(user_id)},
            ]
        }
    })


def get_project_retriever(
    project_id,
    user_id,
    persist_directory: str = DEFAULT_VECTOR_STORE_DIR,
    k: int = 5,
) -> BaseRetriever:
    """Create a similarity retriever over all files in a project."""
    db = get_vector_store(persist_directory=persist_directory)
    return db.as_retriever(search_type="similarity", search_kwargs={
        "k": k,
        "filter": {
            "$and": [
                {"project_id": str(project_id)},
                {"user_id": str(user_id)},
            ]
        }
    })
