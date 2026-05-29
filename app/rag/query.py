from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from app.config.env_config import settings
from app.rag.chain import build_rag_chain
from app.rag.retriever import get_retriever

DEFAULT_QUERY = "What is the difference between a list and a tuple in Python?"


def get_chat_model() -> ChatHuggingFace:
    token = settings.HUGGING_FACE_HUB_API_TOKEN
    if not token:
        raise ValueError("Missing HUGGINGFACEHUB_API_TOKEN in environment.")

    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen3-Coder-Next",
        huggingfacehub_api_token=token,
        max_new_tokens=256,
        temperature=0.2,
    )
    return ChatHuggingFace(llm=llm)



