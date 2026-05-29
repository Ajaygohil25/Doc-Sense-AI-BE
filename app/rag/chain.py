from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from app.rag.prompts import get_rag_prompt
from app.utils.util_functions import parse_page_content


def build_rag_chain(retriever, model):
    """Build a RAG chain from retriever + chat model."""
    prompt = get_rag_prompt()

    return (
        RunnableParallel(
            {
                "context": retriever | RunnableLambda(parse_page_content),
                "question": RunnablePassthrough(),
            }
        )
        | prompt
        | model
        | StrOutputParser()
    )
