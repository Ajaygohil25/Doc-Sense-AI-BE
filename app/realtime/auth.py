import logging
from urllib.parse import parse_qs

from fastapi import HTTPException

from app.authentication.token_management import verify_access_token
from app.core.database import AsyncSessionLocal, get_transaction_session

logger = logging.getLogger("app.realtime.auth")


def _strip_bearer_prefix(token: str | None) -> str | None:
    if not token:
        return None

    token = token.strip()
    if token.lower().startswith("bearer "):
        return token[7:].strip()

    return token or None


def _get_first_query_value(environ: dict, *keys: str) -> str | None:
    query_string = environ.get("QUERY_STRING") if environ else None
    if not query_string:
        return None

    query_values = parse_qs(query_string)
    for key in keys:
        values = query_values.get(key)
        if values:
            return values[0]

    return None


async def authenticate_socket(environ: dict, auth: dict = None) -> dict | None:
    """
    Validates a connection handshake by verifying the JWT access token.
    Checks auth payload first, falling back to HTTP headers and query parameters.
    
    Returns a dictionary of validated token claims (user_id, email) on success, or None on failure.
    """
    token = None

    if auth:
        token = (
            auth.get("token")
            or auth.get("access_token")
            or auth.get("Access-Token")
            or auth.get("authorization")
            or auth.get("Authorization")
        )

    # Try extracting from headers in WS connection environment
    if not token and environ:
        token = (
            environ.get("HTTP_ACCESS_TOKEN")
            or environ.get("HTTP_AUTHORIZATION")
        )

    if not token and environ:
        token = _get_first_query_value(
            environ,
            "token",
            "access_token",
            "Access-Token",
            "authorization",
            "Authorization",
        )

    token = _strip_bearer_prefix(token)

    if not token:
        logger.warning("Authentication failed: No token provided in handshake auth, headers, or query parameters.")
        return None
        
    try:
        async with get_transaction_session(AsyncSessionLocal) as db:
            credentials_exception = HTTPException(
                status_code=401,
                detail="Not authorized to perform this action, please sign-in again!"
            )
            # verify_access_token returns a TokenData object
            token_data = await verify_access_token(
                db=db,
                token=token,
                credentials_exception=credentials_exception,
                check_refresh=False
            )

            # Authentication successful! Return safe session claims.
            return {
                "user_id": str(token_data.user_id),
                "email": token_data.email
            }

    except Exception as e:
        logger.warning(f"Authentication failed: Invalid or expired token: {e}")
        return None
