# tskbridge-api Technical Specification

## 1. Overview

**tskbridge-api** is a healthcare task management API designed to bridge task tracking between multiple healthcare systems while maintaining strict HITRUST CSF v9.6.1 compliance and HIPAA BAA standards. The API enables secure, auditable project and task management across federated healthcare environments.

### Key Constraints
- **Data Classification**: All data classified as PII/PHI by default
- **Encryption**: AES-256 at rest, TLS 1.2+ in transit (no TLS 1.0/1.1)
- **Audit**: Immutable, timestamped audit trail for all operations
- **Session**: 15-minute inactivity timeout, 8-hour absolute maximum per HITRUST
- **Authentication**: OAuth 2.0 / JWT with RS256 signing
- **Authorization**: Role-Based Access Control (RBAC) with Principle of Least Privilege

---

## 2. Data Models

### 2.1 Project

**Storage Location**: `projects` table (PostgreSQL/SQLite)

**Fields**:
| Field | Type | Nullable | Indexed | Constraints | Notes |
|-------|------|----------|---------|-------------|-------|
| `id` | `INTEGER` | NO | YES (PK) | Auto-increment | Primary key |
| `name` | `VARCHAR(255)` | NO | NO | Non-empty | Project display name (PHI) |
| `description` | `VARCHAR(1000)` | YES | NO | — | Optional detailed description (PHI) |
| `team_id` | `INTEGER` | NO | YES | Foreign key to teams | Team ownership; enables multi-tenancy |
| `status` | `ENUM` | NO | YES | `{active, paused, completed, archived}` | Project lifecycle state; immutable transitions (see 2.2) |
| `created_at` | `DATETIME` | NO | YES | UTC, millisecond precision | Immutable creation timestamp |
| `updated_at` | `DATETIME` | NO | YES | UTC, onupdate trigger | Auto-updated on modification |

**Serialization (to_dict)**:
```python
{
  "id": int,
  "name": str,
  "description": str | null,
  "team_id": int,
  "status": str,  # e.g., "active"
  "created_at": str,  # ISO 8601
  "updated_at": str   # ISO 8601
}
```

**Encryption Requirements**:
- `name`, `description` → AES-256 encrypted at rest (PHI fields)
- Indexing must use deterministic encryption (preserved for queries)

---

### 2.2 ProjectStatus Enum

**Valid States**:
```
ACTIVE = "active"
PAUSED = "paused"
COMPLETED = "completed"
ARCHIVED = "archived"
```

**State Transitions** (immutability constraints):
- `ACTIVE` → `PAUSED`, `COMPLETED`, `ARCHIVED` ✓
- `PAUSED` → `ACTIVE`, `COMPLETED`, `ARCHIVED` ✓
- `COMPLETED` → `ARCHIVED` ✓ (terminal, no reversals)
- `ARCHIVED` → (no transitions; terminal state)

**Validation**: Reject invalid transitions at service layer with audit logging.

---

## 3. API Contracts

### 3.1 Create Project

**Endpoint**: `POST /projects`

**Authentication**: Required (JWT Bearer token with `create` permission)

**Authorization**: User must have `create` role or higher; must belong to target team

**Request**:
```json
{
  "name": "string (1-255 chars, required)",
  "description": "string (0-1000 chars, optional)",
  "team_id": "integer (required)",
  "status": "string (optional, default: 'active')"
}
```

**Response (201 Created)**:
```json
{
  "id": integer,
  "name": "string",
  "description": "string | null",
  "team_id": integer,
  "status": "string",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

**Error Responses**:
| Status | Code | Message |
|--------|------|---------|
| 400 | `INVALID_INPUT` | Missing/invalid required fields; name empty or >255 chars |
| 401 | `UNAUTHORIZED` | Missing/invalid JWT token |
| 403 | `FORBIDDEN` | User lacks `create` permission or not in team |
| 409 | `CONFLICT` | Duplicate project (if business rule enforces per-team uniqueness) |
| 500 | `INTERNAL_ERROR` | Database error (never expose PHI or system details) |

**Audit**: Log `CREATE_PROJECT` action with user_id, team_id, project_id, timestamp, IP address.

---

### 3.2 Get Project

**Endpoint**: `GET /projects/:id`

**Authentication**: Required

**Authorization**: User must have `read` permission; must belong to project's team

**Response (200 OK)**:
```json
{
  "id": integer,
  "name": "string",
  "description": "string | null",
  "team_id": integer,
  "status": "string",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

**Error Responses**:
| Status | Code | Message |
|--------|------|---------|
| 401 | `UNAUTHORIZED` | Missing/invalid JWT |
| 403 | `FORBIDDEN` | User not in team |
| 404 | `NOT_FOUND` | Project does not exist (generic message; no PHI) |
| 500 | `INTERNAL_ERROR` | Database error |

**Audit**: Log `READ_PROJECT` action only on success.

---

### 3.3 Update Project Status

**Endpoint**: `PATCH /projects/:id/status`

**Authentication**: Required

**Authorization**: User must have `update` permission; must be team admin or project owner

**Request**:
```json
{
  "status": "string (required, one of: paused, completed, archived)"
}
```

**Response (200 OK)**:
```json
{
  "id": integer,
  "name": "string",
  "description": "string | null",
  "team_id": integer,
  "status": "string",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

**Error Responses**:
| Status | Code | Message |
|--------|------|---------|
| 400 | `INVALID_STATE_TRANSITION` | Transition not allowed (e.g., `COMPLETED` → `ACTIVE`) |
| 401 | `UNAUTHORIZED` | Missing/invalid JWT |
| 403 | `FORBIDDEN` | User lacks `update` permission |
| 404 | `NOT_FOUND` | Project does not exist |
| 500 | `INTERNAL_ERROR` | Database error |

**Validation**: Verify transition via ProjectStatus state machine before update.

**Audit**: Log `UPDATE_PROJECT_STATUS` with old_status, new_status, user_id, project_id, timestamp.

---

### 3.4 List Projects by Team

**Endpoint**: `GET /projects/team/:team_id`

**Authentication**: Required

**Authorization**: User must have `read` permission and belong to specified team

**Query Parameters**:
```
limit: integer (optional, default: 100, max: 1000)
offset: integer (optional, default: 0)
status: string (optional, filter by status; comma-separated)
```

**Response (200 OK)**:
```json
{
  "projects": [
    {
      "id": integer,
      "name": "string",
      "description": "string | null",
      "team_id": integer,
      "status": "string",
      "created_at": "ISO 8601",
      "updated_at": "ISO 8601"
    }
  ],
  "total": integer,
  "limit": integer,
  "offset": integer
}
```

**Audit**: Log `LIST_PROJECTS` action with team_id, user_id, result_count.

---

### 3.5 Delete Project

**Endpoint**: `DELETE /projects/:id`

**Authentication**: Required

**Authorization**: User must have `delete` permission; must be team admin

**Response (204 No Content)**: No body

**Error Responses**:
| Status | Code | Message |
|--------|------|---------|
| 401 | `UNAUTHORIZED` | Missing/invalid JWT |
| 403 | `FORBIDDEN` | User lacks `delete` permission |
| 404 | `NOT_FOUND` | Project does not exist |
| 500 | `INTERNAL_ERROR` | Database error |

**Audit**: Log `DELETE_PROJECT` with project_id, team_id, user_id, timestamp (before deletion, for immutability).

---

## 4. Integration Points with ProjectService

### 4.1 Service Layer Responsibilities

**ProjectService** (in `src/projects/service.py`) handles:
1. **Business Logic**: Enforce state transitions, team ownership, field validation
2. **Database Transactions**: All CRUD wrapped in try/except with rollback on SQLAlchemyError
3. **Audit Logging**: Inject audit events before/after mutations
4. **Data Validation**: Sanitize inputs; reject >255 char names, invalid statuses
5. **Error Translation**: Convert SQLAlchemyError to domain-specific ValueError

**Method Signatures**:

```python
def create(
    name: str,
    team_id: int,
    description: Optional[str] = None,
    status: ProjectStatus = ProjectStatus.ACTIVE,
) -> Project:
    """Create project; validate name length, team existence."""

def get_by_id(project_id: int) -> Optional[Project]:
    """Retrieve project or None if not found."""

def get_by_team(team_id: int) -> List[Project]:
    """List all projects for team; used by authorization checks."""

def update_status(
    project_id: int,
    status: ProjectStatus,
) -> Optional[Project]:
    """Change project status; validate state transition first."""

def delete(project_id: int) -> bool:
    """Delete project; log before removal for audit trail."""

def list_all(limit: int = 100, offset: int = 0) -> List[Project]:
    """Paginated list of all projects (super-admin only)."""
```

### 4.2 Route Layer to Service Binding

**Route Layer** (`routes.py`, to be implemented):
- Dependency inject SessionLocal via `get_db()`
- Instantiate `ProjectService(db)` per request
- Call service methods and translate responses to HTTP
- Pass context (user_id, team_id, role) to audit decorator
- Never expose SQLAlchemyError details in response body

```python
from flask import Blueprint, request, jsonify
from src.database import get_db
from src.projects import ProjectService

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('', methods=['POST'])
@require_auth
def create_project():
    db = next(get_db())
    service = ProjectService(db)
    payload = request.json
    # Validate, call service, audit, respond
```

### 4.3 Authentication/Authorization Integration

**Pattern**: Use decorator/middleware for auth checks:
```python
@require_auth(role=['create', 'update', 'delete'])
@require_team_membership(team_id_param='team_id')
def endpoint(...)
```

**Roles** (RBAC):
```python
ROLES = {
    "admin": ["create", "read", "update", "delete", "audit"],
    "clinician": ["read", "create_own", "update_own"],
    "viewer": ["read"],
    "auditor": ["audit_read"],
}
```

---

## 5. Constraints & Validation Rules

### 5.1 Field Validation

| Field | Rule | Error |
|-------|------|-------|
| `name` | 1–255 chars, non-empty, no leading/trailing whitespace | `INVALID_INPUT` |
| `description` | 0–1000 chars, optional | `INVALID_INPUT` |
| `team_id` | Positive integer; must exist in teams table | `INVALID_INPUT` / `NOT_FOUND` |
| `status` | One of {active, paused, completed, archived} | `INVALID_INPUT` |

### 5.2 Immutability Rules

- **created_at**: Read-only; set at creation, never modified
- **Project Record**: Once created, cannot be "undeleted" (soft-delete optional; hard-delete is terminal)
- **Audit Trail**: All mutations logged immutably (append-only audit table); audit records cannot be modified
- **Status Transitions**: Enforced at service layer; invalid transitions rejected with audit event

### 5.3 Authorization Rules

- **Creation**: User must have `create` role AND belong to target team
- **Read**: User must have `read` role AND belong to project's team
- **Update**: User must have `update` role AND be team admin or project owner
- **Delete**: User must have `delete` role AND be team admin
- **List by Team**: User must belong to team AND have `read` role

### 5.4 Data Isolation

- **Team Isolation**: Queries filtered by `team_id`; no cross-team visibility
- **Row-Level Security (RLS)**: PostgreSQL RLS policies enforce team boundaries at DB layer (future enhancement)
- **Encryption**: PHI fields encrypted; queries use deterministic encryption keys

### 5.5 Audit Logging Requirements

**All mutations** (`create`, `update_status`, `delete`) log:
- Action type (e.g., `CREATE_PROJECT`)
- User ID, Team ID, Project ID
- Old/new values (for status updates)
- Timestamp (UTC, millisecond precision)
- IP address / user agent
- Status (success/failure + reason)

**Format** (immutable append-only table):
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    status VARCHAR(20),  -- 'success', 'failure'
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT UTC_TIMESTAMP
);
```

---

## 6. Error Handling & Response Contracts

**Standard Error Response**:
```json
{
  "error": {
    "code": "string",
    "message": "string (user-friendly, no PHI)",
    "request_id": "uuid (for tracing)"
  }
}
```

**Never include in error responses**:
- SQL error details
- File paths or system configuration
- PHI or PII
- Stack traces (log server-side only)

---

## 7. Security Headers & Transport

**HTTPS**: Enforce TLS 1.2+ only; reject TLS 1.0/1.1

**Headers**:
- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains`
- `X-Content-Type-Options`: `nosniff`
- `X-Frame-Options`: `DENY`
- `X-XSS-Protection`: `1; mode=block`
- `Content-Security-Policy`: Restrict to healthcare system domains

**CORS**: Whitelist only approved healthcare system origins; no wildcard.

---

## 8. Database Schema

**PostgreSQL/SQLite Initialization** (via `init_db()` in `src/database.py`):

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    team_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE INDEX idx_projects_team_id ON projects(team_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);
```

**Connection Pooling** (src/database.py):
- SQLite: StaticPool, check_same_thread=False
- PostgreSQL: pool_size=10, max_overflow=20, pool_pre_ping=True

---

## 9. Implementation Roadmap

1. **Phase 1**: Routes layer for CRUD endpoints, integrate ProjectService
2. **Phase 2**: Auth middleware (JWT validation, team membership checks)
3. **Phase 3**: Audit logging decorator and immutable audit table
4. **Phase 4**: Encryption at rest (AES-256 for name/description)
5. **Phase 5**: FHIR R4 integration points for healthcare system bridges
6. **Phase 6**: HITRUST CSF compliance validation and documentation

---

## 10. Testing Strategy

- **Unit Tests**: ProjectService methods in isolation (mocked DB)
- **Integration Tests**: Routes + ProjectService + real SQLite DB
- **Audit Tests**: Verify all mutations logged correctly
- **Security Tests**: Unauthorized access attempts, input validation, encryption
- **Performance Tests**: Pagination limits, query indexes

**Test Location**: `tests/` directory (pytest + fixtures in `conftest.py`)

