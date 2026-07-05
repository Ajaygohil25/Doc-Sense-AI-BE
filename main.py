from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import user_endpoints, refresh_token_lifecycle_endpoint, file_upload_endpoint, chat_endpoint, project_endpoint
from app.exceptions.exceptions import add_exception_handlers



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



add_exception_handlers(app=app)
app.include_router(user_endpoints.router)
app.include_router(file_upload_endpoint.router)
app.include_router(chat_endpoint.router)
app.include_router(project_endpoint.router)
app.include_router(refresh_token_lifecycle_endpoint.router)



@app.get("/health-check")
async def root():
    return {"message": "Hello World"}


# Integrate Socket.IO with FastAPI
import socketio
from app.realtime import sio

# Wrap the FastAPI application into Socket.IO's ASGI application.
# This makes both REST routes and real-time Socket.IO run on the same server process/port.
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="socket.io"
)
