async def validate_socket_session_data(sid, data, sio):
    session = await sio.get_session(sid)
    if not session:
        await sio.emit("error", {"message": "Unauthorized. Please authenticate first."}, to=sid)
        return

    if not isinstance(data, dict):
        await sio.emit("error", {"message": "Invalid data payload. Must be a JSON object."}, to=sid)
        return

    return session


import re
from typing import Tuple, Optional


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

async def validate_question_data(data, sio, sid):
    question = data.get("question")
    file_id = data.get("file_id")

    if not question:
        await sio.emit("error", {"message": "Missing 'question' in payload."}, to=sid)
        return None, None

    is_suspicious, reason = is_injection_attempt(question)

    if is_suspicious:
        await sio.emit("error", {"message": f"I can only answer questions based on the uploaded documents. {reason}"}, to=sid)
        return None, None

    if not file_id:
        await sio.emit("error", {"message": "Missing 'file_id' in payload."}, to=sid)
        return None, None

    return question, file_id