# Copilot Instructions for tskbridge-api

## Project Overview
tskbridge-api is a healthcare task management API designed to bridge task tracking between multiple healthcare systems. This project operates under HITRUST compliance requirements and must adhere to USA healthcare industry standards and security practices.

## Technology Stack

### Backend Framework & Database
- **Language**: Python 3.9+
- **Web Framework**: Flask 2.3.2+
- **ORM**: SQLAlchemy 2.0.23+
- **Database**: PostgreSQL 12+ (production), SQLite (development)
- **Connection Pooling**: SQLAlchemy with connection pooling
- **Migration Tool**: Alembic (for database schema versioning)

### Security & Authentication
- **Authentication**: OAuth 2.0 / JWT with RS256 signing
- **Authorization**: Role-Based Access Control (RBAC)
- **Encryption**: TLS 1.2+ for all data in transit
- **Data at Rest**: AES-256 encryption for sensitive PHI (Protected Health Information)
- **Secret Management**: Environment-based, never hardcode secrets
- **CORS**: Restrict to approved healthcare system domains only

### Healthcare Standards
- **HL7 FHIR**: Support for FHIR R4 resource exchange
- **HIPAA**: Full HIPAA BAA compliance
- **HITRUST**: HITRUST CSF v9.6.1 certification framework compliance
- **Data Classification**: All data classified as PII/PHI by default

## Architecture Conventions

### Project Structure
```
src/
├── projects/           # Projects domain module
│   ├── __init__.py
│   ├── model.py       # SQLAlchemy models
│   ├── service.py     # Business logic layer
│   └── routes.py      # API endpoints
├── database.py        # Database configuration & session management
├── auth/              # Authentication & authorization
├── audit/             # Audit logging for HIPAA compliance
└── utils/             # Shared utilities
```

### Layered Architecture
1. **API Layer** (routes.py): HTTP request handling, input validation
2. **Service Layer** (service.py): Business logic, domain rules, transactions
3. **Data Layer** (model.py): Database models, ORM entities
4. **Infrastructure**: Database connections, caching, external integrations

### Design Patterns
- **Repository Pattern**: For data access abstraction
- **Service Pattern**: For business logic encapsulation
- **Dependency Injection**: Use constructor injection for testability
- **Factory Pattern**: For complex object creation
- **Singleton Pattern**: For database sessions and configuration

## Coding Standards for USA Healthcare

### Code Style
- **Language**: Python PEP 8 with Black formatter (line length: 100)
- **Type Hints**: Required for all functions and class methods
- **Docstrings**: Google-style docstrings for all public functions
- **Comments**: Focus on "why" not "what"; explain business logic and HIPAA implications

### Naming Conventions
```python
# Constants (UPPERCASE_WITH_UNDERSCORES)
MAX_SESSION_TIMEOUT = 1800  # 30 minutes per HIPAA recommendations
ENCRYPTION_ALGORITHM = "AES-256"

# Classes (PascalCase)
class ProjectService:
    pass

class HealthcareEntity:
    pass

# Functions/Methods (snake_case)
def get_project_by_team(team_id: int) -> List[Project]:
    pass

# Private attributes (_prefix)
self._session = None
self._audit_logger = None
```

### Healthcare-Specific Requirements
- **Immutable Audit Trails**: All healthcare operations must be logged and immutable
- **Timestamp Precision**: Use UTC timestamps with millisecond precision
- **Data Retention**: Implement retention policies per HIPAA (6 years minimum for healthcare records)
- **Anonymization**: Support data anonymization for research purposes
- **Encryption Keys**: Rotate encryption keys per HITRUST requirements
- **Error Messages**: Never expose PHI or system details in error responses

## Security Rules (HITRUST Compliant)

### Authentication & Session Management
```python
# Session timeouts per HITRUST standards
SESSION_TIMEOUT_MINUTES = 15  # Inactivity timeout
MAX_SESSION_DURATION_HOURS = 8  # Absolute maximum
FAILED_LOGIN_ATTEMPTS = 3  # Lock after 3 attempts
LOCKOUT_DURATION_MINUTES = 30  # Account lockout duration
PASSWORD_MIN_LENGTH = 12
PASSWORD_COMPLEXITY = True  # Require uppercase, lowercase, numbers, special chars
```

### Data Protection
- **Encryption in Transit**: Enforce TLS 1.2+ (no TLS 1.0/1.1)
- **Encryption at Rest**: AES-256 for all PHI columns
- **Hashing Algorithms**: Use bcrypt/Argon2 for password hashing (never SHA1/MD5)
- **API Keys**: Rotate quarterly minimum
- **Database Credentials**: Use environment variables, never in code
- **Secrets Scanning**: Enable pre-commit hooks to prevent secret leakage

### Access Control
```python
# RBAC roles for healthcare
ROLES = {
    "admin": ["create", "read", "update", "delete", "audit"],
    "clinician": ["read", "create_own", "update_own"],
    "viewer": ["read"],
    "auditor": ["audit_read"],
}

# Principle of Least Privilege (PoLP)
# Users only get minimum permissions required for their role
```

### Audit Logging
```python
# All sensitive operations must be logged
@audit_log(action="CREATE_PROJECT", risk_level="medium")
def create_project(self, name: str, team_id: int) -> Project:
    # Audit log automatically captures:
    # - User ID and role
    # - Timestamp (UTC)
    # - Action performed
    # - Data accessed/modified (with PHI masked)
    # - IP address and device fingerprint
    # - Outcome (success/failure)
    pass
```

### Input Validation & Output Encoding
```python
# Always validate input
from pydantic import BaseModel, Field, validator

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    team_id: int = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('name')
    def sanitize_name(cls, v):
        # Remove potentially dangerous characters
        return v.strip()[:255]
```

### HITRUST Specific Controls
- **Risk Assessment**: Perform risk assessment for all data flows
- **Vulnerability Scanning**: Weekly automated scanning
- **Penetration Testing**: Quarterly by qualified external team
- **Incident Response**: Document and report any security incidents within 24 hours
- **Business Continuity**: RTO ≤ 4 hours, RPO ≤ 1 hour for healthcare data
- **Backup & Recovery**: Encrypted backups, tested recovery quarterly

## Testing Expectations

### Test Coverage Requirements
- **Minimum Coverage**: 85% code coverage for all modules
- **Critical Paths**: 100% coverage for authentication, authorization, and audit logging
- **Healthcare Logic**: 100% coverage for all HIPAA-related business logic

### Test Types

#### Unit Tests
```python
# Test individual functions in isolation
# Location: tests/unit/projects/test_service.py
def test_create_project_success():
    """Verify project creation with valid input."""
    service = ProjectService(mock_db)
    result = service.create(
        name="Oncology Tasks",
        team_id=1,
        description="Cancer care workflow"
    )
    assert result.id is not None
    assert result.status == ProjectStatus.ACTIVE
    assert result.name == "Oncology Tasks"

def test_create_project_validates_input():
    """Verify input validation prevents invalid projects."""
    service = ProjectService(mock_db)
    with pytest.raises(ValueError):
        service.create(name="", team_id=1)  # Empty name rejected

def test_update_status_audit_logged():
    """Verify status updates are recorded in audit log."""
    service = ProjectService(mock_db_with_audit)
    service.update_status(project_id=1, status=ProjectStatus.COMPLETED)
    
    # Verify audit entry created
    audit_log = mock_audit_logger.get_last_entry()
    assert audit_log.action == "UPDATE_PROJECT_STATUS"
    assert audit_log.user_id == current_user.id
    assert audit_log.timestamp is not None
```

#### Integration Tests
```python
# Test interactions between components
# Location: tests/integration/test_project_workflow.py
def test_project_creation_to_completion_workflow(db_session):
    """Test complete project lifecycle with real database."""
    # Setup
    team_id = create_test_team()
    
    # Create project
    service = ProjectService(db_session)
    project = service.create(
        name="Patient Discharge",
        team_id=team_id,
        description="Discharge workflow"
    )
    
    # Verify creation
    retrieved = service.get_by_id(project.id)
    assert retrieved is not None
    
    # Update status
    updated = service.update_status(project.id, ProjectStatus.COMPLETED)
    assert updated.status == ProjectStatus.COMPLETED
    
    # Verify audit trail
    assert check_audit_trail_exists(
        action="CREATE_PROJECT",
        resource_id=project.id,
        team_id=team_id
    )
```

#### Security Tests
```python
# Test security controls
# Location: tests/security/test_healthcare_compliance.py
def test_phi_never_logged_in_plaintext():
    """Verify PHI is masked in logs."""
    service = ProjectService(mock_db)
    project = Project(id=1, name="John Doe - Oncology", team_id=1)
    
    service.update_status(project.id, ProjectStatus.ACTIVE)
    logs = get_application_logs()
    
    # PHI should be masked or redacted
    for log in logs:
        assert "John Doe" not in log.message
        assert "Oncology" in log.message  # Non-PHI data OK

def test_sql_injection_prevention():
    """Verify parameterized queries prevent SQL injection."""
    service = ProjectService(real_db)
    
    # Attempt SQL injection
    malicious_input = "'; DROP TABLE projects; --"
    result = service.get_by_team(team_id=malicious_input)
    
    # Should handle gracefully, not execute injection
    assert result == []
    
    # Verify table still exists
    assert "projects" in get_database_tables()

def test_authentication_bypass_prevention():
    """Verify authorization cannot be bypassed."""
    # User with 'viewer' role attempts 'delete'
    service = ProjectService(mock_db)
    
    with pytest.raises(PermissionError):
        service.delete(project_id=1)  # Should fail for 'viewer' role
```

#### Performance Tests
```python
# Location: tests/performance/test_healthcare_sla.py
def test_project_retrieval_sla():
    """Verify sub-100ms response for get_by_team."""
    service = ProjectService(db_session)
    
    start = time.time()
    results = service.get_by_team(team_id=1)
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    assert elapsed < 100, f"Query took {elapsed}ms, SLA is 100ms"

def test_bulk_operations_within_timeout():
    """Verify bulk operations complete within session timeout."""
    service = ProjectService(db_session)
    
    start = time.time()
    for i in range(1000):
        service.create(
            name=f"Project {i}",
            team_id=1,
            description="Bulk test"
        )
    elapsed = time.time() - start
    
    # 1000 inserts should complete within 30 seconds
    assert elapsed < 30
```

### Acceptance Criteria
All code must meet these criteria before merging:

1. **Functionality**
   - ✅ All new features have passing unit tests
   - ✅ Integration tests verify end-to-end workflows
   - ✅ Code passes type checking (`mypy --strict`)
   - ✅ No unhandled exceptions in error paths

2. **Healthcare Compliance**
   - ✅ Audit logging implemented for all sensitive operations
   - ✅ PHI is never logged, displayed, or cached without encryption
   - ✅ Input validation prevents invalid data entry
   - ✅ Output encoding prevents injection attacks
   - ✅ HIPAA privacy rule compliance verified

3. **Security**
   - ✅ Authentication and authorization enforced
   - ✅ Secrets not hardcoded or in version control
   - ✅ HITRUST controls implemented per requirement
   - ✅ Security tests pass (SQL injection, auth bypass, etc.)
   - ✅ No high/critical vulnerabilities in dependencies

4. **Code Quality**
   - ✅ Code passes Black formatter (100 char line length)
   - ✅ Passes flake8 linter (with healthcare rules)
   - ✅ Test coverage ≥ 85% (100% for critical paths)
   - ✅ All functions have type hints and docstrings
   - ✅ No TODOs or FIXMEs in production code

5. **Performance & Reliability**
   - ✅ API responses within SLA (< 200ms for most operations)
   - ✅ Database queries optimized with appropriate indexes
   - ✅ Connection pooling configured for production
   - ✅ Error handling with appropriate HTTP status codes
   - ✅ Graceful degradation under load

## Testing Commands

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test category
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/security/          # Security tests only
pytest tests/performance/       # Performance tests only

# Run type checking
mypy --strict src/

# Run linting
flake8 src/

# Format code
black --line-length 100 src/

# Check for security vulnerabilities
bandit -r src/
safety check

# Generate coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

## Healthcare-Specific Validation Examples

```python
# Validate healthcare-specific requirements
class ProjectService:
    def create(self, name: str, team_id: int, description: Optional[str] = None) -> Project:
        """Create project with healthcare compliance checks."""
        
        # Input validation
        if not name or len(name) > 255:
            raise ValueError("Project name required, max 255 characters")
        
        if team_id <= 0:
            raise ValueError("Valid team_id required")
        
        # Create with audit trail
        project = Project(
            name=name.strip(),
            description=description,
            team_id=team_id,
            status=ProjectStatus.ACTIVE
        )
        
        self.db.add(project)
        self.db.commit()
        
        # Mandatory audit log
        self.audit_logger.log(
            action="CREATE_PROJECT",
            resource_id=project.id,
            team_id=team_id,
            user_id=get_current_user().id,
            details={
                "project_name": name,  # Non-PHI safe
                # Never log: patient data, SSN, medical record numbers
            }
        )
        
        return project
```

## Continuous Compliance Monitoring

- **Weekly**: Automated security scanning and vulnerability assessment
- **Monthly**: Code review with healthcare compliance focus
- **Quarterly**: HITRUST audit and penetration testing
- **Annually**: Full HIPAA compliance assessment and RTO/RPO testing

## References

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [HITRUST CSF v9.6.1](https://hitrustalliance.net/csf/)
- [FHIR R4 Specification](https://www.hl7.org/fhir/r4/)
- [OWASP Top 10 for Healthcare](https://owasp.org/www-project-top-ten/)
- [CMS Interoperability Requirements](https://www.cms.gov/Regulations-and-Guidance/Guidance/Interoperability)

---

**Last Updated**: 2026-09-15
**Compliance Framework**: HIPAA BAA + HITRUST CSF v9.6.1
**Maintainer**: tskbridge-api Team
