import re
from typing import Tuple, Optional

from app.core.constants import FAILED_STATUS


def socket_error_payload(message: str, code: str = "VALIDATION_ERROR") -> dict:
    return {
        "status": FAILED_STATUS,
        "code": code,
        "message": message,
    }


async def validate_socket_session_data(sid, data, sio, emit_error: bool = True):
    session = await sio.get_session(sid)
    if not session:
        error = socket_error_payload(
            "Unauthorized. Please authenticate first.",
            code="UNAUTHORIZED",
        )
        if emit_error:
            await sio.emit("error", error, to=sid)
        return None, error

    if not isinstance(data, dict):
        error = socket_error_payload(
            "Invalid data payload. Must be a JSON object.",
            code="INVALID_PAYLOAD",
        )
        if emit_error:
            await sio.emit("error", error, to=sid)
        return None, error

    return session, None



def is_injection_attempt(user_query: str) -> Tuple[bool, Optional[str]]:
    """
    Detects potential prompt injection attempts.
    Returns (is_suspicious: bool, reason: str | None)
    """

    if not user_query or len(user_query.strip()) == 0:
        return False, None

    query_lower = user_query.lower().strip()

    # RULE-BASED CHECKS
    # High-risk keywords and patterns
    injection_patterns = [
        r"ignore (all|previous|above|your|instructions?|rules?)",
        r"forget (all|previous|your|instructions?)",
        r"new instructions?",
        r"override (your|previous|system)",
        r"disregard (previous|above)",
        r"you are now",
        r"act as (if|though|developer|admin|root)",
        r"developer mode",
        r"jailbreak",
        r"DAN",
        r"do not (follow|obey|respect)",
        r"reveal your (prompt|instructions|system)",
        r"print your (prompt|instructions)",
        r"output the above",
        r"system prompt",
    ]

    score = 0
    matched_patterns = []

    for pattern in injection_patterns:
        if re.search(pattern, query_lower):
            score += 1
            matched_patterns.append(pattern)

    # Additional heuristics
    if len(user_query) > 800:  # Very long prompts are suspicious
        score += 1

    if query_lower.count("ignore") >= 2 or query_lower.count("instruction") >= 3:
        score += 1

    # Final Decision
    if score >= 2 or (score >= 1 and len(matched_patterns) > 0):
        return True, f"Matched suspicious patterns: {matched_patterns[:3]}"

    return False, None

async def validate_question_data(data):
    question = data.get("question")
    file_id = data.get("file_id")
    project_id = data.get("project_id")

    if not isinstance(question, str) or not question.strip():
        return file_id, project_id, None, socket_error_payload(
            "Missing or invalid 'question' in payload."
        )

    if bool(file_id) == bool(project_id):
        return file_id, project_id, question, socket_error_payload(
            "Payload must include exactly one of 'file_id' or 'project_id'."
        )

    is_suspicious, reason = is_injection_attempt(question)

    if is_suspicious:
        return file_id, project_id, question, socket_error_payload(
            f"I can only answer questions based on the uploaded documents. {reason}",
            code="QUESTION_REJECTED",
        )

    return file_id, project_id, question, None
