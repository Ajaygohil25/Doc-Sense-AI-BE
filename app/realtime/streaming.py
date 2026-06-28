import asyncio
from collections.abc import AsyncIterator, Iterator

STREAM_RESPONSE_CHUNK_SIZE = 24
STREAM_RESPONSE_CHUNK_DELAY_SECONDS = 0.1


async def stream_chain_response(chain, question: str) -> AsyncIterator[str]:
    """
    Streams text chunks from a LangChain runnable.
    Falls back to non-streaming invocation for chains/models that do not support streaming.
    """
    astream = getattr(chain, "astream", None)
    if callable(astream):
        async for chunk in astream(question):
            text = chunk_to_text(chunk)
            for text_chunk in split_text_for_stream(text):
                yield text_chunk
        return

    stream = getattr(chain, "stream", None)
    if callable(stream):
        chunks = await asyncio.to_thread(lambda: list(stream(question)))
        for chunk in chunks:
            text = chunk_to_text(chunk)
            for text_chunk in split_text_for_stream(text):
                yield text_chunk
        return

    response = await asyncio.to_thread(chain.invoke, question)
    text = chunk_to_text(response)
    for text_chunk in split_text_for_stream(text):
        yield text_chunk


def chunk_to_text(chunk) -> str:
    if chunk is None:
        return ""

    if isinstance(chunk, str):
        return chunk

    if isinstance(chunk, dict):
        for key in ("answer", "content", "text", "response", "output"):
            value = chunk.get(key)
            if isinstance(value, str):
                return value
            if value is not None:
                return str(value)

    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content

    if content is not None:
        return str(content)

    return str(chunk)


def split_text_for_stream(
    text: str,
    max_chunk_size: int = STREAM_RESPONSE_CHUNK_SIZE,
) -> Iterator[str]:
    if not text:
        return

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + max_chunk_size, text_length)

        if end < text_length:
            split_at = text.rfind(" ", start + 1, end + 1)
            if split_at > start:
                end = split_at + 1

        yield text[start:end]
        start = end
