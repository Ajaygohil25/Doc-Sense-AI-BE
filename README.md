# Doc Sense AI Backend

FastAPI backend for Doc Sense AI, an authenticated PDF retrieval-augmented generation (RAG) application. The service supports individual-document chat and owner-scoped projects that combine multiple PDFs into one searchable knowledge base.

REST endpoints and authenticated Socket.IO run from the same ASGI application and port.

## Features

- Email/password registration and OAuth2-compatible sign-in
- JWT access and refresh tokens, token verification, logout, and token blacklisting
- User profile and password management
- Owner-scoped PDF uploads and paginated document history
- Background PDF ingestion, text chunking, embeddings, and persistent Chroma storage
- Document-scoped chat rooms and conversation history
- Owner-scoped projects with multiple PDF files and multiple chat rooms
- Project-level retrieval across all successfully ingested project files
- REST question endpoints and streaming Socket.IO question responses
- PostgreSQL persistence through async SQLAlchemy
- Alembic database migrations
- Local or S3-backed PDF storage with temporary S3 ingestion files
- Optional Redis-backed Socket.IO client management

## How It Works

1. An authenticated user uploads a PDF directly or adds it to a project.
2. The API validates the PDF, saves it locally or in S3, and creates an `Initiated` database record.
3. A FastAPI background task marks the file `Ingested`, loads the PDF, splits its text, and creates embeddings. S3 objects are downloaded to a temporary file for this step and removed afterward.
4. Chroma stores each chunk with its user, file, and optional project scope.
5. Successful ingestion changes the file status to `Success`; failures change it to `Failed`.
6. A chat request retrieves only chunks owned by the authenticated user and matching the requested file or project.
7. The LangChain RAG chain sends the retrieved context to the configured Hugging Face model and stores the conversation.

Individual file ingestion creates a default file chat room. Project creation creates a default project chat room immediately, before any project files are uploaded.

## Tech Stack

- Python 3.11+
- FastAPI and Uvicorn
- python-socketio
- Pydantic Settings
- SQLAlchemy 2 with asyncpg
- PostgreSQL and Alembic
- LangChain
- Hugging Face Inference API
- Hugging Face sentence-transformers embeddings
- ChromaDB
- PyPDF
- Pytest and pytest-asyncio
- Redis (optional for multi-process Socket.IO deployments)

## Prerequisites

- Python 3.11 or newer
- PostgreSQL
- A Hugging Face access token with access to the configured inference model
- An AWS S3 bucket when `IS_ON_S3=true`
- Redis only when `SOCKETIO_USE_REDIS=true`

The default RAG configuration uses:

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` on CPU
- Chat model: `Qwen/Qwen3-Coder-Next` through `HuggingFaceEndpoint`
- Vector collection: `rag_collection`
- Local vector directory: `vector_store/`

## Local Setup

### 1. Create a virtual environment

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The requirements include the RAG, embedding, and CUDA stacks, so installation can be large. CUDA packages are skipped on Windows but not on macOS; macOS developers may need to remove or replace the NVIDIA/CUDA-specific requirement lines before installation.

### 3. Create PostgreSQL databases

Create separate development and test databases. The names are examples and may be changed as long as the URLs in `.env` match.

```sql
CREATE DATABASE doc_sense_ai;
CREATE DATABASE doc_sense_ai_test;
```

Never point `TEST_DATABASE_URL` at a development or production database. The test suite creates and drops all known tables at session scope.

### 4. Configure environment variables

Create `.env` in the repository root. All non-Socket.IO fields below are required by `app/config/env_config.py` during application import, even when a related feature is not actively used.

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/doc_sense_ai
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_NAME=doc_sense_ai
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/doc_sense_ai_test

SIGN_IN_URL=http://localhost:5173/login
HASH_KEY=replace-with-a-long-random-secret
HASH_ALGO=HS256
ACCESS_TOKEN_EXPIRE_TIME=1
REFRESH_TOKEN_EXPIRE_TIME=24
RESET_TOKEN_EXPIRE_MINUTES=30
RESET_TOKEN_SECRET_KEY=replace-with-another-long-random-secret
FORGOT_PASSWORD_URL=http://localhost:5173/reset-password?token=

MAIL_USERNAME=your-mail-username
MAIL_PASSWORD=your-mail-password
MAIL_FROM=no-reply@example.com
MAIL_PORT=465
MAIL_SERVER=smtp.example.com

HUGGING_FACE_HUB_API_TOKEN=hf_replace_with_your_token

IS_ON_S3=false
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=doc-sense-pdfs

SOCKETIO_CORS_ORIGINS=http://localhost:5173
SOCKETIO_USE_REDIS=false
SOCKETIO_REDIS_URL=redis://localhost:6379
SOCKETIO_PING_TIMEOUT=25
SOCKETIO_PING_INTERVAL=5
```

`ACCESS_TOKEN_EXPIRE_TIME` and `REFRESH_TOKEN_EXPIRE_TIME` are interpreted as hours. `RESET_TOKEN_EXPIRE_MINUTES` is interpreted as minutes.

Use `IS_ON_S3=false` to store uploads under `Uploaded files/`. To use S3, set `IS_ON_S3=true` and provide `AWS_REGION` and `AWS_S3_BUCKET_NAME`. `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` must be supplied together, or both can remain empty so Boto3 uses its default credential chain, such as an IAM role or local AWS profile.

### 5. Apply migrations

```bash
alembic upgrade head
```

Alembic is already initialized in this repository. Do not run `alembic init` again.

### 6. Start the application

```bash
uvicorn main:socket_app --reload
```

Use `main:socket_app`, not `main:app`, so REST and Socket.IO are both available.

Local endpoints:

- API origin: `http://localhost:8000`
- Health check: `http://localhost:8000/health-check`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Socket.IO path: `http://localhost:8000/socket.io`

## Environment Variable Reference

| Group | Variables | Purpose |
| --- | --- | --- |
| Database | `DATABASE_URL`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_NAME` | Development database configuration |
| Tests | `TEST_DATABASE_URL` | Isolated database used by Pytest |
| JWT | `HASH_KEY`, `HASH_ALGO`, `ACCESS_TOKEN_EXPIRE_TIME`, `REFRESH_TOKEN_EXPIRE_TIME` | Token signing and expiration |
| Password reset | `RESET_TOKEN_EXPIRE_MINUTES`, `RESET_TOKEN_SECRET_KEY`, `FORGOT_PASSWORD_URL` | Reset-token generation and frontend link |
| Frontend link | `SIGN_IN_URL` | Required setting loaded by `UserService`; currently not used to build a response |
| Mail | `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_PORT`, `MAIL_SERVER` | SMTP configuration |
| RAG | `HUGGING_FACE_HUB_API_TOKEN` | Hugging Face inference authentication |
| Storage | `IS_ON_S3` | Chooses local or S3-backed PDF storage |
| AWS S3 | `AWS_REGION`, `AWS_S3_BUCKET_NAME` | Required bucket location and name when S3 mode is enabled |
| AWS credentials | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Optional explicit credential pair; omit both to use Boto3's default credential chain |
| Socket.IO | `SOCKETIO_CORS_ORIGINS` | `*` or a comma-separated list of allowed origins |
| Socket.IO | `SOCKETIO_USE_REDIS`, `SOCKETIO_REDIS_URL` | Optional shared client manager |
| Socket.IO | `SOCKETIO_PING_TIMEOUT`, `SOCKETIO_PING_INTERVAL` | Connection heartbeat timing in seconds |

The committed `.sample-env` contains the complete configuration template. Replace its example credentials and secrets before use.

## REST API

Protected endpoints require:

```http
Authorization: Bearer <access-token>
```

Most endpoints return the shared response envelope:

```json
{
  "success": true,
  "message": "Operation completed",
  "error": null,
  "data": {}
}
```

Sign-in is an exception and returns the token/user object directly.

### Health

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health-check` | No | Basic process health response |

### Users and authentication

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/user/sign-up` | No | Register a user |
| `POST` | `/api/v1/user/sign-in` | No | Sign in with OAuth2 form fields `username` and `password` |
| `PATCH` | `/api/v1/user/change-password` | Yes | Change the current password and blacklist the access token |
| `POST` | `/api/v1/user/forgot-password` | No | Create a password-reset token |
| `POST` | `/api/v1/user/reset-password?token=...` | No | Reset a password using the token |
| `POST` | `/api/v1/user/logout` | Yes | Blacklist access and refresh tokens |
| `PATCH` | `/api/v1/user/update-profile` | Yes | Update first and/or last name |
| `GET` | `/api/v1/user/profile` | Yes | Return the current user profile |
| `POST` | `/api/v1/token/verify-access-token` | No | Verify an access token supplied in JSON |
| `POST` | `/api/v1/token/generate-access-token` | No | Exchange a refresh token for new tokens |

Sign-in consumes `application/x-www-form-urlencoded`, not JSON.

### Individual documents

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/dashboard/file-upload` | Upload one PDF as multipart form field `file` |
| `GET` | `/api/v1/dashboard/get-file-upload-history?page=1&page_size=20` | Return the current user's paginated upload history |
| `GET` | `/api/v1/dashboard/get-file-by-id/{upload_file_id}` | Return one owned upload |
| `POST` | `/api/v1/chat/create-chat-room` | Create a named room for an owned file |
| `GET` | `/api/v1/chat/get-chat-rooms-by-file-id/{file_id}` | List file chat rooms |
| `GET` | `/api/v1/chat/get-chat-messages-by-room-id/{room_id}` | Return room history |
| `POST` | `/api/v1/chat/ask-question` | Ask a synchronous REST question about one file |

### Projects

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/projects` | Create a project and its default chat room |
| `GET` | `/api/v1/projects` | List projects owned by the current user |
| `GET` | `/api/v1/projects/{project_id}` | Return project details, files, and rooms |
| `POST` | `/api/v1/projects/{project_id}/files` | Upload one PDF to an owned project |
| `GET` | `/api/v1/projects/{project_id}/files` | List project files |
| `POST` | `/api/v1/projects/{project_id}/chat-rooms` | Create a named project room |
| `GET` | `/api/v1/projects/{project_id}/chat-rooms` | List project rooms |
| `GET` | `/api/v1/projects/{project_id}/chat-rooms/{room_id}/messages` | Return project-room history |
| `POST` | `/api/v1/projects/{project_id}/ask-question` | Ask a synchronous REST question across the project |

Project, file, and room lookups are scoped to the authenticated owner.

## Socket.IO Contract

### Connection

Connect to the backend origin with path `/socket.io`. Supply a valid access token in the Socket.IO auth object:

```js
io('http://localhost:8000', {
  path: '/socket.io',
  auth: { token: accessToken },
})
```

The server also accepts the access token from `Authorization`/`Access-Token` headers or supported query parameters. A successful connection emits `connected` with the socket and user IDs.


Sending both `file_id` and `project_id`, or neither, produces a validation error. The requested file/project and room must belong to the authenticated user.

### Server events

| Event | Purpose |
| --- | --- |
| `connected` | Confirms an authenticated connection |
| `chat_message_created` | Returns the stored user message |
| `question_response_start` | Marks the beginning of a streamed answer |
| `question_response_chunk` | Delivers one answer chunk |
| `question_response_end` | Delivers the completed answer at stream end |
| `question_response` | Final compatibility response and request completion signal |
| `error` | Returns validation, authorization, or RAG errors |
| `channel_joined` | Confirms `join_channel` |
| `channel_left` | Confirms `leave_channel` |

The server automatically joins each socket to its private `user_<user_id>` room. Explicit channel joins are limited to that user's own room or channel names beginning with `public_` or `channel_`.

## PDF and RAG Behavior

- Upload validation requires a case-insensitive `.pdf` filename, `application/pdf` content type, and a `%PDF-` signature within the first 1,024 bytes.
- The backend rejects PDFs larger than 20 MB with HTTP `413`; the frontend enforces the same limit before upload.
- Ingestion runs as an in-process FastAPI background task, not a durable job queue.
- Local PDFs are written to `Uploaded files/` with the upload UUID appended to the filename.
- S3 PDFs are downloaded to a securely created temporary file for ingestion and the temporary file is removed on success or failure.
- Chroma data is persisted under `vector_store/`.
- File retrieval filters by `file_id` and `user_id` and returns up to three similar chunks.
- Project retrieval filters by `project_id` and `user_id` and returns up to five similar chunks.
- The prompt instructs the model to answer only from retrieved document context. The Socket.IO flow also supplies recent room history.
- Basic rule-based prompt-injection screening is applied before questions reach the model.

## Project Structure

```text
app/
  api/v1/             REST route modules
  authentication/     Password hashing, JWT creation, and OAuth2 dependencies
  config/             Environment and mail configuration
  core/               Database, constants, logging, and shared infrastructure
  exceptions/         Application exception handlers
  models/             SQLAlchemy models
  rag/                PDF ingestion, retrieval, prompts, chains, and model setup
  realtime/           Socket.IO server, auth, handlers, events, and streaming
  repositories/       Database access functions
  schemas/            Pydantic request and response models
  services/           User, file, project, chat, token, and storage services
  utils/              Input, file, and Socket.IO validation
alembic/               Migration environment and revisions
docs/                  Detailed Socket.IO and frontend integration notes
test/                  API, RAG, authentication, and realtime tests
Uploaded files/        Local uploaded PDFs (runtime data)
vector_store/          Persistent Chroma data (runtime data)
main.py                FastAPI and Socket.IO ASGI entry point
```

## Testing

Ensure PostgreSQL is running and `TEST_DATABASE_URL` points to a disposable test database, then run:

```bash
python -m pytest
```

Targeted examples:

```bash
python -m pytest test/api/test_project_api.py -v
python -m pytest test/test_realtime.py -v
python -m pytest test/test_project_retriever.py -v
python -m pytest test/test_file_validation.py test/test_s3_configuration.py test/test_s3_ingestion.py test/test_s3_upload_wiring.py -q
```

Pytest configuration is in `pytest.ini`; tests are discovered under `test/` and async mode is enabled automatically.

## Production Notes

- Replace all example secrets and database credentials.
- Restrict both FastAPI CORS and `SOCKETIO_CORS_ORIGINS` to trusted frontend origins.
- Serve the application behind HTTPS so JWTs are not sent over plaintext connections.
- Run `alembic upgrade head` during deployment before starting new application code.
- Persist and back up PostgreSQL, `vector_store/`, and the chosen upload storage.
- Use Redis-backed Socket.IO management before running multiple application workers.
- Move ingestion to a durable task queue before relying on it for long-running or high-volume workloads.

## Current Operational Constraints

- In-process background ingestion is not retried if the server stops during processing.
- REST CORS is currently configured with wildcard origins in `main.py`; tighten it before production use.

## Troubleshooting

### Upload remains `Ingested` or changes to `Failed`

- Check the server logs for PDF loader, embedding, Chroma, or database errors.
- For local storage, confirm the uploaded PDF is readable and exists under `Uploaded files/`.
- For S3 storage, confirm the object exists and the application identity can call `s3:GetObject` on the configured bucket.
- Confirm the process can write to `vector_store/`.
- Confirm model dependencies installed successfully.

### S3 upload fails

- Confirm `IS_ON_S3=true`, `AWS_REGION`, and `AWS_S3_BUCKET_NAME` are set.
- If explicit credentials are used, provide both `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.
- If explicit credentials are omitted, confirm Boto3 can obtain credentials from an IAM role, environment, or local AWS profile.
- Confirm the application identity can call `s3:PutObject` and `s3:GetObject` for the configured bucket.

### Questions fail to generate an answer

- Confirm `HUGGING_FACE_HUB_API_TOKEN` is valid.
- Confirm the configured Hugging Face model is available to the token.
- Wait for the relevant upload status to become `Success`.
- Confirm the room belongs to the selected file or project.

### REST works but Socket.IO does not

- Start `main:socket_app`, not `main:app`.
- Check the frontend origin against `SOCKETIO_CORS_ORIGINS`.
- Confirm the handshake includes a non-refresh JWT access token.
- If Redis mode is enabled, confirm Redis is reachable at `SOCKETIO_REDIS_URL`.
