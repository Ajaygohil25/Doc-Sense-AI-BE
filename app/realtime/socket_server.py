import logging
import socketio
from app.config.env_config import settings

logger = logging.getLogger("app.realtime.socket_server")

# Setup Socket.IO Client Manager (Redis) if configured
client_manager = None
if settings.SOCKETIO_USE_REDIS:
    logger.info(f"Setting up AsyncRedisManager with URL: {settings.SOCKETIO_REDIS_URL}")
    try:
        client_manager = socketio.AsyncRedisManager(settings.SOCKETIO_REDIS_URL)
    except Exception as e:
        logger.error(f"Failed to create AsyncRedisManager: {e}. Falling back to default in-memory manager.")

# Parse allowed origins for CORS
cors_origins = settings.SOCKETIO_CORS_ORIGINS
if cors_origins == "*":
    allowed_origins = "*"
else:
    # Handle comma-separated list of origins
    allowed_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    if len(allowed_origins) == 1:
        allowed_origins = allowed_origins[0]

# Initialize Socket.IO Async Server
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=client_manager,
    cors_allowed_origins=allowed_origins,
    ping_timeout=settings.SOCKETIO_PING_TIMEOUT,
    ping_interval=settings.SOCKETIO_PING_INTERVAL,
)
