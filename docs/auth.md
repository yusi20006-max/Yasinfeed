# YasinFeed - Authentication Layer

The YasinFeed Authentication Layer provides a lightweight, modular, and highly secure subsystem for user and session/token management within the YasinFeed Core.

---

## 1. Security Design & Best Practices

YasinFeed prioritizes security and minimal dependencies, enabling native, zero-dependency out-of-the-box support for environments like Termux on Android and standard Linux.

### Password Hashing (PBKDF2)
- Passwords are never stored in plain text.
- Passwords are securely hashed using Python's standard library `hashlib.pbkdf2_hmac` with **SHA-256**.
- Every user gets a cryptographically secure random **16-byte salt** generated via `os.urandom`.
- The hashing algorithm utilizes a default iteration count of **100,000**, protecting against brute-force and rainbow table attacks.

### Session Token Generation
- Session keys are high-entropy **256-bit secure random hexadecimal tokens** (64 hex characters) generated using `secrets.token_hex`.
- Tokens have a configurable expiration window (default is 24 hours).
- Expired tokens are automatically recognized as invalid and invalidated upon access.

---

## 2. Configuration Options

Configure the authentication layer within the `config/config.yaml` file under the `auth` section:

```yaml
auth:
  token_expiry_hours: 24       # Expiration window for generated session tokens
  min_password_length: 8       # Minimum character length allowed for user registration
  pbkdf2_iterations: 100000    # Iterations count used for PBKDF2 hashing
```

---

## 3. Storage Data Models & Schemas

The authentication layer integrates directly with the Storage Module supporting both `SQLiteStorage` and `JSONStorage` backends.

### User Model
```python
@dataclass
class User:
    id: str               # Unique UUIDv4 string
    username: str         # Unique username
    password_hash: str    # Hex-encoded PBKDF2-SHA256 password hash
    salt: str             # Hex-encoded unique salt
    created_at: datetime  # Time of registration
```

### Session Model
```python
@dataclass
class Session:
    token: str            # High-entropy random token hex
    user_id: str          # Owner user ID
    expires_at: datetime  # Session expiration timestamp
    created_at: datetime  # Session creation timestamp
```

### SQLite Schema Definitions
```sql
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

---

## 4. API Layer Integration

The API module (`yasinfeed/api/__init__.py`) provides simulated, REST-compliant endpoint handlers mapping directly to underlying `AuthModule` actions.

### Register User
**Method:** `handle_register(self, request_data: dict) -> tuple`
- Simulates `POST /api/auth/register`
- Expects `username` and `password` in payload.
- Returns status code `201` on success, `400` on validation failure / duplicate username, or `500` on server error.

### User Login
**Method:** `handle_login(self, request_data: dict) -> tuple`
- Simulates `POST /api/auth/login`
- Verifies password against hashed values.
- On success, returns `200` with the generated session `token` and `expires_at` timestamp. Returns `401` on invalid credentials.

### Protected Endpoint Check
**Method:** `handle_get_articles(self, headers: dict) -> tuple`
- Simulates `GET /api/feed`
- Requires `Authorization: Bearer <token>` header.
- On successful validation of token, returns the requested content items. Returns `401` if token is missing, invalid, or expired.
