from langchain_huggingface import HuggingFaceEmbeddings

def get_embeddings() -> HuggingFaceEmbeddings:
    """Return the embedding model used for both ingest and query."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
