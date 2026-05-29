import logging

from fastapi import HTTPException

from app.authentication.token_management import verify_access_token

logger = logging.getLogger("app.realtime.auth")

async def authenticate_socket(environ: dict, auth: dict = None) -> dict | None:
    """
    Validates a connection handshake by verifying the JWT access token.
    Checks auth payload first, falling back to HTTP headers and query parameters.
    
    Returns a dictionary of validated token claims (user_id, email) on success, or None on failure.
    """
    token = None

    if auth:
        token = auth.get("token")

    # Try extracting from headers in WS connection environment
    if not token and environ:
        auth_header = environ.get("HTTP_ACCESS_TOKEN")
        if auth_header:
            token = auth_header
            

    if not token:
        logger.warning("Authentication failed: No token provided in handshake auth, headers, or query parameters.")
        return None
        
    try:
        # Dynamically resolve the database session dependency (supports testing overrides)
        from main import app
        from app.core.database import get_db

        db_resolver = app.dependency_overrides.get(get_db, get_db)

        async for db in db_resolver():
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
