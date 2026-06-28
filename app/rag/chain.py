from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from app.rag.prompts import get_rag_prompt
from app.utils.util_functions import parse_page_content


def build_rag_chain(retriever, model, prev_message_context=None):
    """Build a RAG chain from retriever + chat model."""
    prompt = get_rag_prompt()
    previous_messages = format_previous_messages(prev_message_context)

    return (
        RunnableParallel(
            {
                "previous_message_contex": RunnableLambda(lambda _: previous_messages),
                "context": retriever | RunnableLambda(parse_page_content),
                "question": RunnablePassthrough(),
            }
        )
        | prompt
        | model
        | StrOutputParser()
    )


def format_previous_messages(messages):
    if not messages:
        return "No previous messages."

    formatted_messages = []

    for message in messages:
        sender = message.get("sender", "unknown")
        sender_value = getattr(sender, "value", sender)
        message_text = message.get("message", "")
        formatted_messages.append(f"{sender_value}: {message_text}")

    return "\n".join(formatted_messages)
