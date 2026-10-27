# 🎓 UniFlow — Complete Backend Architecture & Codebase Deep Dive
> **Target Audience**: Engineers with strong Django REST Framework (DRF) & PostgreSQL background learning FastAPI, Async Python, MongoDB, and Agentic RAG workflows.

---

## 📑 Table of Contents
1. [Overall Backend Architecture & Technology Rationale](#1-overall-backend-architecture--technology-rationale)
   - [Folder & File Layout](#folder--file-layout)
   - [Technology Rationale](#technology-rationale)
   - [FastAPI vs. Django REST Framework (DRF) Mental Mapping](#fastapi-vs-django-rest-framework-drf-mental-mapping)
2. [Complete End-to-End Execution Flows](#2-complete-end-to-end-execution-flows)
   - [Flow A: Standard REST Request (CRUD)](#flow-a-standard-rest-request-crud)
   - [Flow B: File Upload & Background Ingestion](#flow-b-file-upload--background-ingestion)
   - [Flow C: Real-Time SSE Agentic Chat Query](#flow-c-real-time-sse-agentic-chat-query)
3. [MongoDB, Motor & Docker (NoSQL vs. PostgreSQL/pgAdmin)](#3-mongodb-motor--docker-nosql-vs-postgresqlpgadmin)
   - [Why MongoDB & How Schemas/Documents Work](#why-mongodb--how-schemasdocuments-work)
   - [Database Connection & Collection Access](#database-connection--collection-access)
   - [MongoDB in Docker vs. MongoDB Atlas](#mongodb-in-docker-vs-mongodb-atlas)
   - [Development vs. Production Deployments](#development-vs-production-deployments)
4. [Authentication & Authorization Deep Dive](#4-authentication--authorization-deep-dive)
   - [Token Generation & Validation](#token-generation--validation)
   - [Redis User Caching Strategy](#redis-user-caching-strategy)
   - [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
   - [Superadmin Auto-Seeding](#superadmin-auto-seeding)
5. [6-Digit Classroom Code Mechanism](#5-6-digit-classroom-code-mechanism)
   - [Generation & Collision Avoidance](#generation--collision-avoidance)
   - [Joining a Classroom](#joining-a-classroom)
   - [Cascade Deletion Architecture](#cascade-deletion-architecture)
6. [LangGraph Agent Architecture & State Management](#6-langgraph-agent-architecture--state-management)
   - [Agentic Graph vs. Linear Pipeline](#agentic-graph-vs-linear-pipeline)
   - [State Definition & Flow](#state-definition--flow)
   - [The Nodes & Conditional Edges](#the-nodes--conditional-edges)
   - [Why `api/agent` is Placed Inside `api/` vs. Top-Level](#why-apiagent-is-placed-inside-api-vs-top-level)
7. [Celery & Document Ingestion Pipeline](#7-celery--document-ingestion-pipeline)
   - [Why Celery is Mandatory for Heavy Ingestion](#why-celery-is-mandatory-for-heavy-ingestion)
   - [3-Tier PDF Extraction Cascade](#3-tier-pdf-extraction-cascade)
   - [Chunking, Embedding & ChromaDB Upsert](#chunking-embedding--chromadb-upsert)
   - [Real-Time WebSocket Progress Notifications](#real-time-websocket-progress-notifications)

---

# 1. Overall Backend Architecture & Technology Rationale

### Folder & File Layout

The backend directory (`c:\Desktop\UniFlow\backend\`) is structured around clean domain separation, asynchronous performance, and stateful AI orchestration:

```text
backend/
├── main.py                     # FastAPI application factory, lifespan startup/shutdown, middleware, WS routes
├── pyproject.toml / uv.lock     # Modern Python project dependencies & lockfile (managed by uv)
├── .env                         # Environment variables (DB URIs, JWT secrets, Gemini API key pools)
├── storage/                    # Local filesystem storage
│   ├── uploads/                # Permanent file storage partitioned by type (/pdfs, /images, /videos)
│   ├── temp/                   # Temporary incoming chunk buffer for streaming SHA-256 calculation
│   └── chroma/                 # On-disk persistent vector store (ChromaDB)
├── database/                   # Database singleton connection managers
│   ├── mongo.py                # Motor (async MongoDB) client singleton & connection pool
│   ├── chroma.py               # ChromaDB PersistentClient & collection initialization
│   └── redis.py                # Redis asyncio client singleton
├── core/                       # Core system configuration and cross-cutting infrastructure
│   ├── config.py               # Pydantic BaseSettings (reads .env with strict validation)
│   ├── security.py             # Password hashing (bcrypt) & JWT encoding/decoding (PyJWT)
│   ├── celery_app.py           # Celery application configuration (Redis broker/backend, concurrency=1)
│   ├── llm_router.py           # Multi-pool Gemini KeyManager with automatic 429 backoff & rotation
│   └── websocket.py            # WebSocket ConnectionManager with Redis Pub/Sub cross-process broadcaster
├── models/                     # Data contract layer
│   └── schemas.py              # Pydantic v2 schemas for request validation & response serialization
├── api/                        # HTTP & WebSocket delivery layer
│   ├── dependencies.py         # FastAPI dependency injection (Auth, RBAC, Redis cache, Classroom gates)
│   ├── routers/                # Endpoint route controllers
│   │   ├── auth.py             # /api/auth (register, login) & /api/users (me, update, password)
│   │   ├── superadmin.py       # /api/superadmin (provision-teacher, list-teachers, revoke)
│   │   ├── classroom.py        # /api/classrooms (create, list, get, join, delete with cascade)
│   │   ├── upload.py           # /api/upload/file & /api/files (stream upload, download, metadata)
│   │   ├── chat.py             # /api/chat (sessions, history, and SSE AI streaming)
│   │   ├── announcements.py    # /api/classrooms/{id}/announcements (notices & updates)
│   │   ├── calendar.py         # /api/calendar (events, exams, deadlines)
│   │   └── notifications.py    # /api/notifications (user-scoped notifications)
│   ├── services/               # Business logic & background workers
│   │   └── ingestion.py        # 3-tier PDF extraction, chunking, embedding, and Celery task entry
│   └── agent/                  # LangGraph AI Agent orchestration
│       ├── state.py            # TypedDict AgentState & data class definitions
│       ├── nodes.py            # Graph execution nodes (entry, router, embed, retriever, reject, synthesis)
│       └── graph.py            # StateGraph definition, conditional edges, and compiled singleton
└── scripts/                    # Management scripts (e.g., seed_superadmin.py, test_rag.py)
```

---

### Technology Rationale

| Technology | Purpose in UniFlow | Why it was Chosen |
| :--- | :--- | :--- |
| **FastAPI** | REST API & SSE Streaming | Built on ASGI (`asyncio`/`uvicorn`). Native support for async endpoints, dependency injection, streaming responses (Server-Sent Events), and WebSockets. |
| **MongoDB (Motor)** | Primary Database | Flexible NoSQL document model. Allows embedding members in classroom documents, handling dynamic chat histories, and storing JSON file metadata without rigid relational migrations. `Motor` is the non-blocking async MongoDB driver for Python. |
| **Redis** | Caching, Message Broker, Pub/Sub | Serves 3 distinct roles: (1) Broker and result backend for Celery, (2) 5-minute cache for user auth profiles to prevent DB bottlenecks, (3) Pub/Sub broadcaster across worker processes for WebSocket notifications. |
| **Celery** | Background Document Processing | Offloads heavy CPU/IO tasks (PDF parsing, OCR, multimodal AI file upload, vector embeddings) from the HTTP request-response cycle into a dedicated worker queue. |
| **ChromaDB** | Vector Database | Lightweight, embeddable vector store that runs in-process or on-disk (`storage/chroma`), calculating cosine similarity on Gemini embeddings (`models/gemini-embedding-001`) with metadata filtering. |
| **Google Gemini API** | Multimodal LLM & Embeddings | Long context window, fast JSON structured classification via `gemini-2.0-flash-lite`, high-fidelity conversational synthesis, and multimodal PDF parsing. |
| **LangGraph** | AI Orchestrator | Graph-based state machine that conditionally routes queries to fast rejection, conversational reply, ChromaDB RAG, or Web search based on structured intent classification. |
| **Docker** | Infrastructure Orchestration | Standardizes runtime dependencies (MongoDB, Redis, Mongo Express) in isolated containers, ensuring identical dev and prod environments. |

---

### FastAPI vs. Django REST Framework (DRF) Mental Mapping

If you are coming from DRF, here is how concepts directly translate:

| Django / DRF Concept | UniFlow / FastAPI Equivalent in Codebase | Concrete Code Reference |
| :--- | :--- | :--- |
| `settings.py` | `core/config.py` (`Settings` via `pydantic-settings`) | `from core.config import settings` |
| `models.Model` (ORM) | Pydantic Schemas (`models/schemas.py`) + Motor Documents | `db.users.insert_one(doc)` in `api/routers/auth.py` |
| `serializers.Serializer` / `ModelSerializer` | Pydantic `BaseModel` (`models/schemas.py`) | `UserCreate`, `ClassroomResponse` in `models/schemas.py` |
| `views.APIView` / `viewsets.ModelViewSet` | Router route functions decorated with `@router.get`, `@router.post` | `@router.post("/api/classrooms")` in `api/routers/classroom.py` |
| `urls.py` | `app.include_router()` in `main.py` | `app.include_router(classroom.router)` in `main.py:173` |
| `permissions.IsAuthenticated`, `permissions.BasePermission` | FastAPI Dependencies (`Depends()`) in `api/dependencies.py` | `current_user = Depends(require_role("teacher"))` |
| `authentication.BaseAuthentication` | `OAuth2PasswordBearer` + `get_current_user` in `api/dependencies.py` | `api/dependencies.py:19` |
| `django-admin` | **Mongo Express** container (`http://localhost:8081`) or custom `/api/superadmin` router | `docker-compose.yml:38` and `api/routers/superadmin.py` |
| Django Signals (`post_save`, `pre_delete`) | Explicit helper calls or background task dispatches | Cascade delete in `api/routers/classroom.py:262` |
| Celery Tasks in `tasks.py` | Celery Tasks in `api/services/ingestion.py` | `@celery_app.task def process_file_task` in `ingestion.py:408` |
| WSGI (`gunicorn`) | ASGI (`uvicorn main:app --reload`) | `uv run uvicorn main:app` |

---

# 2. Complete End-to-End Execution Flows

### Flow A: Standard REST Request (CRUD)
*Example: Student joins a classroom via `POST /api/classrooms/join`*

```mermaid
sequenceDiagram
    autonumber
    actor Client as Frontend (Next.js)
    participant Auth as api/dependencies.py (get_current_user)
    participant Redis as Redis (User Cache)
    participant Router as api/routers/classroom.py (join_classroom)
    participant Mongo as MongoDB (db.classrooms)

    Client->>Auth: POST /api/classrooms/join (Header: Authorization: Bearer <jwt>)
    Auth->>Auth: decode_access_token(token) -> extracts user_id
    Auth->>Redis: GET user_cache:{user_id}
    alt Cache Hit
        Redis-->>Auth: Cached User JSON
    else Cache Miss
        Auth->>Mongo: db.users.find_one({"user_id": user_id})
        Mongo-->>Auth: User Document
        Auth->>Redis: SETEX user_cache:{user_id} 300 (5 mins)
    end
    Auth-->>Router: Injected current_user dict
    Router->>Router: Validate payload (JoinClassroomBody: 6-char code)
    Router->>Mongo: db.classrooms.find_one({"join_code": "AB12CD"})
    alt Classroom Not Found
        Router-->>Client: 404 Not Found
    else Classroom Found
        Router->>Router: Check if user_id in classroom.members
        Router->>Mongo: db.classrooms.update_one({"$push": {"members": ...}})
        Router-->>Client: 200 OK {"message": "Successfully joined classroom"}
    end
```

---

### Flow B: File Upload & Background Ingestion
*Example: Teacher uploads a 10MB Lecture PDF via `POST /api/upload/file`*

```mermaid
sequenceDiagram
    autonumber
    actor Teacher as Teacher Client
    participant UploadRouter as api/routers/upload.py
    participant TempDisk as storage/temp/
    participant PermDisk as storage/uploads/pdfs/
    participant Mongo as MongoDB (file_metadata)
    participant Celery as Celery Worker (ingestion.py)
    participant Gemini as Google Gemini (File API & Embeddings)
    participant Chroma as ChromaDB (campus_vectors)
    participant WS as WebSocket Hub (websocket.py)

    Teacher->>UploadRouter: POST /api/upload/file (multipart/form-data)
    UploadRouter->>UploadRouter: Verify role == "teacher" & classroom membership
    UploadRouter->>TempDisk: Stream chunks (8KB) & compute SHA-256 on the fly
    UploadRouter->>Mongo: Check deduplication: db.file_metadata.find_one({"sha256_hash": hash})
    UploadRouter->>PermDisk: Move temp file to storage/uploads/pdfs/{file_id}.pdf
    UploadRouter->>Mongo: Insert metadata doc (status: "pending")
    UploadRouter->>Celery: process_file_task.delay(file_id) (Pushed to Redis Queue)
    UploadRouter-->>Teacher: 202 Accepted {"file_id": "...", "status": "pending"}

    Note over Celery: Asynchronous execution in separate process
    Celery->>Mongo: db.file_metadata.find_one({"file_id": file_id})
    Celery->>Mongo: Update status -> "processing"
    Celery->>Gemini: Tier 1: Upload to Gemini File API & Extract Text/LaTeX/Tables
    alt Tier 1 Fails
        Celery->>Celery: Tier 2: Fallback to Docling Markdown extraction
    end
    Celery->>Celery: RecursiveCharacterTextSplitter (800 chars, 100 overlap)
    Celery->>Gemini: Batch Embed chunks (models/gemini-embedding-001)
    Celery->>Chroma: collection.upsert(ids, embeddings, metadatas, documents)
    Celery->>Mongo: Update status -> "completed", chunk_count: N
    Celery->>WS: manager.publish_update(classroom_id, {"type": "file_processed"})
    WS-->>Teacher: WebSocket notification to all classroom students & teacher
```

---

### Flow C: Real-Time SSE Agentic Chat Query
*Example: Student asks "Explain backpropagation from unit 3 notes" via `POST /api/chat/sessions/{id}/message`*

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student Client
    participant ChatRouter as api/routers/chat.py
    participant LangGraph as api/agent/graph.py (StateGraph)
    participant Nodes as api/agent/nodes.py
    participant Chroma as ChromaDB
    participant Synthesis as nodes.py:synthesis_node_stream
    participant Mongo as MongoDB (chat_history)

    Student->>ChatRouter: POST /api/chat/sessions/{session_id}/message
    ChatRouter->>ChatRouter: Initialize AgentState dictionary
    ChatRouter-->>Student: SSE Stream Header (text/event-stream)
    
    ChatRouter->>LangGraph: compiled_graph.astream(initial_state)
    
    LangGraph->>Nodes: entry_node (loads user profile, enrolled classrooms, last 6 chat messages)
    ChatRouter-->>Student: data: {"t": "status", "d": "Understanding your question..."}
    
    LangGraph->>Nodes: router_node (Gemini Flash JSON classification)
    Nodes-->>LangGraph: RouterOutput(intent="RAG_SEARCH")
    ChatRouter-->>Student: data: {"t": "status", "d": "Searching knowledge base..."}
    
    LangGraph->>Nodes: embed_node (generates 768-dim query vector)
    
    LangGraph->>Nodes: retriever_vector_node (ChromaDB query with classroom filter)
    Nodes->>Chroma: collection.query(where={"classroom_id": target_cls})
    Chroma-->>Nodes: Top 8 chunks with cosine distances
    Nodes->>Nodes: Filter by RELEVANCE_THRESHOLD (0.35) -> used_sources
    ChatRouter-->>Student: data: {"t": "thought", "d": "Found 4 relevant sections."}
    
    LangGraph-->>ChatRouter: Graph Execution Completed (Final AgentState)
    
    ChatRouter->>Synthesis: synthesis_node_stream(final_state)
    loop Token by Token Streaming
        Synthesis-->>ChatRouter: Chunk text
        ChatRouter-->>Student: data: {"t": "token", "d": "Backpropagation"}
    end
    
    ChatRouter-->>Student: data: {"t": "sources", "d": [{"file_name": "Unit3.pdf", "page": 4}]}
    ChatRouter-->>Student: data: {"t": "done", "d": ""}
    ChatRouter->>Mongo: db.chat_history.insert_many([user_msg, assistant_msg])
```

---

# 3. MongoDB, Motor & Docker (NoSQL vs. PostgreSQL/pgAdmin)

### Why MongoDB & How Schemas/Documents Work

In DRF with PostgreSQL, you declare tables statically in `models.py` and run migrations:
```python
# Django ORM / PostgreSQL style:
class Classroom(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
```

In **UniFlow**, the data layer uses **MongoDB** via **Motor** (`AsyncIOMotorClient`). MongoDB is schema-less at the database engine level, but **strictly typed at the application level using Pydantic v2**:

1. **Request validation & Response contracts**: Defined in [`backend/models/schemas.py`](file:///c:/Desktop/UniFlow/backend/models/schemas.py).
2. **Direct Document Dictionaries**: Data is saved as BSON/JSON dictionaries in MongoDB collections.
3. **No Migration Files**: You don't run `makemigrations` or `migrate`. Adding a new field to a document requires simply updating the Pydantic schema and writing the field in the router dictionary.

#### Schema Example Comparison:
In PostgreSQL, a many-to-many relationship (Users in Classrooms) requires a join table (`classroom_members`). In UniFlow's MongoDB architecture, members are **embedded directly** as a list of sub-documents inside the classroom document:

```json
// MongoDB "classrooms" collection document:
{
  "_id": ObjectId("65dfa1..."),
  "classroom_id": "cls_8a7b6c5d4e3f",
  "name": "Distributed Systems 2026",
  "description": "CS401 Lecture Series",
  "subject": "Computer Science",
  "join_code": "XY98ZT",
  "created_by": "tea_1a2b3c4d5e6f",
  "members": [
    {
      "user_id": "tea_1a2b3c4d5e6f",
      "role": "teacher",
      "joined_at": ISODate("2026-08-17T10:00:00Z")
    },
    {
      "user_id": "stu_9f8e7d6c5b4a",
      "role": "student",
      "joined_at": ISODate("2026-08-17T10:15:00Z")
    }
  ],
  "created_at": ISODate("2026-08-17T10:00:00Z"),
  "updated_at": ISODate("2026-08-17T10:15:00Z")
}
```

---

### Database Connection & Collection Access

MongoDB connection is managed in [`backend/database/mongo.py`](file:///c:/Desktop/UniFlow/backend/database/mongo.py):
```python
client = AsyncIOMotorClient(
    settings.MONGO_URI,
    maxPoolSize=20,
    minPoolSize=2,
    connectTimeoutMS=5000,
    serverSelectionTimeoutMS=5000,
)
db = client[settings.MONGO_DB]
```

To access collections across any router or service, you import `get_db`:
```python
from database.mongo import get_db

db = get_db()
user = await db.users.find_one({"email": email})
await db.file_metadata.insert_one(doc)
```

#### Collections and their Indexes:
During startup in [`backend/main.py:68-100`](file:///c:/Desktop/UniFlow/backend/main.py#L68-L100), the app explicitly ensures indexes to maintain O(1) lookups and enforce uniqueness:
- `db.users`: Index on `email` (unique), `user_id` (unique)
- `db.classrooms`: Index on `classroom_id` (unique), `join_code` (unique), `members.user_id` (multi-key index)
- `db.file_metadata`: Index on `sha256_hash` (unique), `file_id` (unique), compound `(classroom_id, uploaded_at)`
- `db.chat_sessions`: Index on `session_id` (unique), compound `(user_id, updated_at)`
- `db.chat_history`: Compound index on `(session_id, timestamp)`

---

### MongoDB in Docker vs. MongoDB Atlas

| Aspect | Local Docker Container (`docker-compose.yml`) | Managed Cloud (MongoDB Atlas) |
| :--- | :--- | :--- |
| **Where it runs** | Locally inside Docker engine on your machine. | Fully managed AWS/GCP/Azure cloud cluster. |
| **Connection URI** | `mongodb://localhost:27017` | `mongodb+srv://user:pass@cluster0.abc.mongodb.net/uniflow` |
| **GUI Inspection Tool** | **Mongo Express** container at `http://localhost:8081` (similar to pgAdmin for Postgres). | Atlas Cloud Dashboard or MongoDB Compass. |
| **Data Persistence** | Stored in Docker named volume `mongodb_data:/data/db`. Preserved across restarts unless deleted with `docker-compose down -v`. | Managed automated cloud backups and multi-region replication. |
| **Best Used For** | Zero-cost, isolated local development without internet dependency. | Production deployment, high availability, clustering. |

---

### Development vs. Production Deployments

In development, [`docker-compose.yml`](file:///c:/Desktop/UniFlow/docker-compose.yml) spins up MongoDB, Redis, and Mongo Express:
```yaml
services:
  mongodb:
    image: mongo:7.0
    container_name: uniflow_mongo
    ports: ["27017:27017"]
    volumes: [mongodb_data:/data/db]

  redis:
    image: redis/redis-stack-server:latest
    ports: ["6379:6379"]
    volumes: [redis_data:/data]

  mongo-express:
    image: mongo-express:1.0.2
    ports: ["8081:8081"]
    environment:
      ME_CONFIG_MONGODB_SERVER: mongodb
```

**Switching to Production:**
1. You only need to change the `MONGO_URI` and `CELERY_BROKER_URL` environment variables in `.env` (pointing to MongoDB Atlas and Managed Redis).
2. Set a 32+ character `JWT_SECRET` (the startup lifespan in `main.py:58` will abort if default insecure secrets are used).
3. The application logic remains 100% identical.

---

# 4. Authentication & Authorization Deep Dive

### Token Generation & Validation

Authentication is built using standard **OAuth2 Bearer Tokens (JWT)** with **bcrypt** password hashing:

1. **Registration** (`POST /api/auth/register` in [`backend/api/routers/auth.py:37`](file:///c:/Desktop/UniFlow/backend/api/routers/auth.py#L37)):
   - Self-registration is restricted to students.
   - User ID is generated with a role prefix: `stu_` + 12-char hex (e.g., `stu_a1b2c3d4e5f6`).
   - Password is hashed with `bcrypt.hashpw()` in [`backend/core/security.py:14`](file:///c:/Desktop/UniFlow/backend/core/security.py#L14).

2. **Login** (`POST /api/auth/login` in [`backend/api/routers/auth.py:82`](file:///c:/Desktop/UniFlow/backend/api/routers/auth.py#L82)):
   - Accepts standard `OAuth2PasswordRequestForm` (`username` = email, `password` = password).
   - Validates bcrypt hash via `verify_password()`.
   - Generates JWT access token with payload containing `user_id`, `role`, and expiration (7 days).

3. **Token Extraction in Requests** ([`backend/api/dependencies.py:19`](file:///c:/Desktop/UniFlow/backend/api/dependencies.py#L19)):
   - `get_current_user` extracts the bearer token from the `Authorization: Bearer <token>` header or `?token=` query param (used for WebSocket handshakes and direct file download tags).
   - `decode_access_token()` verifies the cryptographic signature with `settings.JWT_SECRET` and algorithm `HS256`.

---

### Redis User Caching Strategy

In high-traffic systems, hitting the primary database on every single API request to authenticate the user degrades performance. UniFlow implements a **Redis Read-Through User Cache** with automated cache invalidation in [`backend/api/dependencies.py:31-99`](file:///c:/Desktop/UniFlow/backend/api/dependencies.py#L31-L99):

```mermaid
graph TD
    A[Incoming Request with JWT] --> B[decode_access_token -> user_id]
    B --> C{Check Redis: user_cache:user_id}
    C -->|Hit| D[Return User Dict instantly ~0.5ms]
    C -->|Miss| E[Query MongoDB: db.users.find_one]
    E --> F[Write to Redis: SETEX user_cache:user_id 300s]
    F --> D
    
    G[User updates profile / password] --> H[invalidate_user_cache: Redis DEL user_cache:user_id]
```

---

### Role-Based Access Control (RBAC)

UniFlow supports three distinct roles (`RoleEnum` in [`backend/models/schemas.py:13`](file:///c:/Desktop/UniFlow/backend/models/schemas.py#L13)):
- `superadmin`: Global control (can provision teachers, list/delete all classrooms, bypass membership checks).
- `teacher`: Can create classrooms, upload files, post announcements, create exams/events.
- `student`: Can self-register, join classrooms with a 6-digit code, chat with the AI assistant, read materials.

Authorization is enforced using a higher-order dependency factory `require_role()` in [`backend/api/dependencies.py:104`](file:///c:/Desktop/UniFlow/backend/api/dependencies.py#L104):

```python
# Example: Only teachers or superadmins can upload files:
@router.post("/api/upload/file")
async def upload_file(
    current_user: dict = Depends(require_role("teacher", "superadmin"))
):
    ...
```

For classroom-specific operations, [`require_classroom_member`](file:///c:/Desktop/UniFlow/backend/api/dependencies.py#L141) verifies that the user's `user_id` is present in the classroom's `members` array.

---

### Superadmin Auto-Seeding

On server startup, [`main.py:26`](file:///c:/Desktop/UniFlow/backend/main.py#L26) executes `_seed_superadmin()`:
- Checks if a user with `role: "superadmin"` exists.
- If not, creates an account using `settings.SUPERADMIN_EMAIL` and `settings.SUPERADMIN_PASSWORD` with ID prefix `adm_`.
- Teachers cannot self-register; they are provisioned exclusively by the superadmin via `POST /api/superadmin/provision-teacher`.

---

# 5. 6-Digit Classroom Code Mechanism

### Generation & Collision Avoidance

When a teacher creates a classroom (`POST /api/classrooms` in [`backend/api/routers/classroom.py:47`](file:///c:/Desktop/UniFlow/backend/api/routers/classroom.py#L47)):

1. `_generate_join_code()` generates a cryptographically secure 6-character uppercase alphanumeric string using `secrets.choice`:
   ```python
   def _generate_join_code(length: int = 6) -> str:
       alphabet = string.ascii_uppercase + string.digits  # 36 characters (36^6 = ~2.17 Billion combinations)
       return "".join(secrets.choice(alphabet) for _ in range(length))
   ```
2. **Collision Retry Loop**: It checks MongoDB for collisions up to 10 times:
   ```python
   for _ in range(10):
       join_code = _generate_join_code()
       if not await db.classrooms.find_one({"join_code": join_code}):
           break
   ```
3. A unique MongoDB index (`db.classrooms.create_index("join_code", unique=True)`) prevents race condition duplicates at the database level.

---

### Joining a Classroom

When a student enters a code (`POST /api/classrooms/join` in [`backend/api/routers/classroom.py:194`](file:///c:/Desktop/UniFlow/backend/api/routers/classroom.py#L194)):

1. Cleans the code: `join_code = body.join_code.upper().strip()`.
2. Queries `classroom = await db.classrooms.find_one({"join_code": join_code})`. If not found, returns `404 Invalid join code`.
3. **Idempotency Guard**: Checks if `current_user["user_id"]` is already in `classroom["members"]`. If so, returns early without duplicating.
4. **Atomic Push**: Uses MongoDB's atomic `$push` operator to append the student to the array:
   ```python
   await db.classrooms.update_one(
       {"classroom_id": classroom["classroom_id"]},
       {
           "$push": {
               "members": {
                   "user_id": user_id,
                   "role": current_user["role"],
                   "joined_at": datetime.now(timezone.utc),
               }
           },
           "$set": {"updated_at": datetime.now(timezone.utc)},
       },
   )
   ```

---

### Cascade Deletion Architecture

When a teacher or superadmin deletes a classroom (`DELETE /api/classrooms/{id}` in [`backend/api/routers/classroom.py:241`](file:///c:/Desktop/UniFlow/backend/api/routers/classroom.py#L241)), a 5-step cascade executes to prevent orphan data:

1. **Disk & ChromaDB Cleanup**: Iterates all files in `db.file_metadata` for this classroom, deletes physical files from `storage/uploads/`, and calls `collection.delete(where={"file_id": f["file_id"]})` in ChromaDB.
2. **File Metadata Cleanup**: `await db.file_metadata.delete_many({"classroom_id": classroom_id})`.
3. **Chat Cascade**: Deletes all `db.chat_sessions` and related `db.chat_history` records.
4. **Announcements Cleanup**: `await db.announcements.delete_many({"classroom_id": classroom_id})`.
5. **Classroom Deletion**: `await db.classrooms.delete_one({"classroom_id": classroom_id})`.

---

# 6. LangGraph Agent Architecture & State Management

### Agentic Graph vs. Linear Pipeline

In a basic RAG application, every query blindly goes through:
`Query -> Embedding -> Vector Search -> LLM Synthesis`

This creates high latency and wastes API costs on greetings or out-of-scope questions. UniFlow uses a **LangGraph StateGraph** ([`backend/api/agent/graph.py`](file:///c:/Desktop/UniFlow/backend/api/agent/graph.py)) that inspects intent first:

```mermaid
graph TD
    START([START]) --> entry[Node 1: entry_node<br/>Load Profile, History & Context]
    entry --> router[Node 2: router_node<br/>Gemini Flash JSON Classification]
    
    router -->|OUT_OF_SCOPE| reject[Node 3: fast_reject_node<br/>Hardcoded $0 Refusal]
    router -->|CONVERSATIONAL| END_CONV([END -> SSE Synthesis only])
    router -->|RAG_SEARCH / DEEP_STUDY| embed[Node 4: embed_node<br/>Gemini Embedding-001]
    router -->|WEB_SEARCH| embed
    
    embed -->|RAG_SEARCH| retriever[Node 5A: retriever_vector_node<br/>ChromaDB Cosine Search + Threshold]
    embed -->|WEB_SEARCH| web[Node 5B: web_search_node<br/>DuckDuckGo Real-Time Search]
    
    retriever --> END([END])
    web --> END
    reject --> END
```

---

### State Definition & Flow

The agent's state is modeled in [`backend/api/agent/state.py`](file:///c:/Desktop/UniFlow/backend/api/agent/state.py) and typed as `AgentState` in [`backend/api/agent/nodes.py:50`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L50):

- **Input Context**: `query`, `session_id`, `user_id`, `scope_classroom_id`, `file_id`.
- **Enrichment Data**: `user_profile` (role & enrolled classrooms), `classroom_context` (subject & description), `chat_history` (last 6 messages).
- **Router Output**: `intent` (`RAG_SEARCH`, `WEB_SEARCH`, `DEEP_STUDY`, `CONVERSATIONAL`, `OUT_OF_SCOPE`), `confidence`, `reasoning`.
- **Retrieval Results**: `query_embedding`, `retrieved_chunks`, `used_sources` (only threshold-passing chunks), `web_search_results`.

---

### The Nodes & Conditional Edges

1. **`entry_node`** ([`nodes.py:108`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L108)): Fetches user info and chat history from MongoDB. **Does not call any embedding API**.
2. **`router_node`** ([`nodes.py:170`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L170)): Calls `gemini-2.0-flash-lite` in strict JSON mode with zero temperature. Classifies intent.
3. **`fast_reject_node`** ([`nodes.py:320`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L320)): Formulates a polite rejection grounded in the classroom subject (e.g. "I'm CampusAI, designed to help you with Operating Systems..."). **Zero LLM cost, zero embedding cost**.
4. **`embed_node`** ([`nodes.py:345`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L345)): Runs only when retrieval is required, calling `models/gemini-embedding-001`.
5. **`retriever_vector_node`** ([`nodes.py:394`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L394)):
   - Queries ChromaDB with strict classroom metadata filtering (`{"classroom_id": {"$eq": target_cls}}`).
   - Filters out chunks with cosine similarity below `RELEVANCE_THRESHOLD = 0.35`.
   - Emits `used_sources` with exact filename and page citations.
6. **`synthesis_node_stream`** ([`nodes.py:642`](file:///c:/Desktop/UniFlow/backend/api/agent/nodes.py#L642)):
   - **Important architectural detail**: This is an async generator, **not** inside the LangGraph compilation.
   - It is driven directly by the SSE route in [`chat.py:283`](file:///c:/Desktop/UniFlow/backend/api/routers/chat.py#L283) to yield tokens in real time to the browser as they stream from Gemini.

---

### Why `api/agent` is Placed Inside `api/` vs. Top-Level

In standard multi-tier software engineering, developers often ask whether `agent` belongs in a top-level `rag/` folder or inside `api/`. In UniFlow:

1. **Delivery-Tightly Coupled**: The LangGraph state directly consumes HTTP session state, classroom scoping parameters, and user claims created in the `api/` layer.
2. **Streaming Synchronization**: The SSE streaming protocol in `api/routers/chat.py` iterates over `compiled_graph.astream()` step-by-step to emit real-time UI events (`t: "status"`, `t: "thought"`).
3. **Dependency Direction**: `api/agent/nodes.py` imports `database/mongo.py`, `database/chroma.py`, and `core/llm_router.py`. Placing `agent` inside `api/` ensures that `core/` and `database/` remain low-level shared foundations with no circular dependencies.

---

# 7. Celery & Document Ingestion Pipeline

### Why Celery is Mandatory for Heavy Ingestion

FastAPI provides a lightweight `BackgroundTasks` feature, but running document ingestion inside FastAPI's event loop has major flaws:
- **Memory Pressure**: Deep learning models (like IBM Docling) consume 1-2 GB of RAM during PDF parsing.
- **Process Blocking**: CPU-intensive parsing and large batch embeddings starve the FastAPI async loop, causing HTTP timeouts for other users.
- **Process Termination**: If the web server restarts or crashes, all in-flight `BackgroundTasks` are permanently lost.

**Celery (`core/celery_app.py`)** runs as an isolated worker process (`uniflow_worker`). Configured with:
- `worker_concurrency=1` and `-P solo` on Windows to prevent RAM exhaustion.
- `task_acks_late=True` and `task_reject_on_worker_lost=True` so dropped tasks are automatically re-queued.
- `autoretry_for=(RuntimeError, Exception)` with exponential backoff.

---

### 3-Tier PDF Extraction Cascade

In [`backend/api/services/ingestion.py`](file:///c:/Desktop/UniFlow/backend/api/services/ingestion.py), document extraction uses a 3-tier cascade:

```mermaid
graph TD
    A[New PDF Upload] --> T1{Tier 1: Gemini File API}
    T1 -->|Success: Multimodal, LaTeX, Tables| DONE[Text Ready]
    T1 -->|Fails / Rate-limited| T2{Tier 2: IBM Docling}
    T2 -->|Success: Markdown & Tables| DONE
    T2 -->|Fails / Uninstalled| T3{Tier 3: PyMuPDF}
    T3 -->|Plain text only| WARN[Text Ready with UI Warning]
    T3 -->|Fails| ERR[Task Failed & Celery Retry]
```

1. **Tier 1 (Gemini File API)**: Uploads PDF directly to Google Gemini's multimodal API. Extracts complex layouts, tables, block LaTeX math, and diagram descriptions. Cleans up the uploaded file from Gemini storage immediately after.
2. **Tier 2 (Docling)**: Local CPU-based Markdown extraction. Parses document hierarchy and basic tables.
3. **Tier 3 (PyMuPDF - fitz)**: Fast, text-only fallback. Flags `extraction_warning` in metadata so the student knows complex figures may be missing.

---

### Chunking, Embedding & ChromaDB Upsert

Once text is extracted:

1. **Recursive Splitting** ([`ingestion.py:270`](file:///c:/Desktop/UniFlow/backend/api/services/ingestion.py#L270)):
   - `chunk_size = 800` characters.
   - `chunk_overlap = 100` characters (preserves boundary context).
2. **Batch Embedding** ([`ingestion.py:288`](file:///c:/Desktop/UniFlow/backend/api/services/ingestion.py#L288)):
   - Batches chunks in groups of 50.
   - Calls `models/gemini-embedding-001` with `task_type="RETRIEVAL_DOCUMENT"`.
   - Uses the dedicated `INGESTION` key pool with automatic 429 exponential backoff.
3. **ChromaDB Upsert** ([`ingestion.py:342`](file:///c:/Desktop/UniFlow/backend/api/services/ingestion.py#L342)):
   - Generates deterministic chunk IDs: `{file_id}_c1`, `{file_id}_c2`, etc.
   - Saves document text, vector embeddings, and metadata (`file_id`, `classroom_id`, `file_type`, `extraction_method`).
4. **Status Update in MongoDB**: Sets `processing.status = "completed"` and records `chunk_count`.

---

### Real-Time WebSocket Progress Notifications

When ingestion finishes, Celery publishes a message via Redis Pub/Sub ([`ingestion.py:369`](file:///c:/Desktop/UniFlow/backend/api/services/ingestion.py#L369)):

```python
await manager.publish_update(classroom_id, {
    "type": "file_processed",
    "file_id": file_id,
    "status": "ready",
    "extraction_method": extraction_method,
})
```

The WebSocket manager ([`backend/core/websocket.py`](file:///c:/Desktop/UniFlow/backend/core/websocket.py)) listens to the Redis channel `classroom_updates` and pushes the JSON payload to all connected browser WebSockets in that classroom without polling.

---

## 🎯 Summary Checklist

- **APIs & Routing**: FastAPI with asynchronous route handlers in `api/routers/`.
- **Data Persistence**: MongoDB (Motor async driver) for flexible JSON documents + ChromaDB for vector embeddings.
- **Cache & Message Broker**: Redis Stack handling user auth caching, Celery queues, and Pub/Sub WebSocket events.
- **Heavy Ingestion**: Celery worker running a 3-tier fallback cascade (Gemini File API -> Docling -> PyMuPDF).
- **AI Agentic Flow**: LangGraph StateGraph handling intent gating, selective embedding, semantic search, and per-token SSE synthesis.
- **Security & Authorization**: PyJWT + bcrypt, Redis caching, RBAC dependencies (`require_role`), and classroom membership gates.
