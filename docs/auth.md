# YasinFeed - Authentication & Security Layer

The YasinFeed Authentication & Security Layer provides a lightweight, modular, and highly secure subsystem for user/session/token management, API key validation, role-based authorization, and rate-limiting within the YasinFeed Core.

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

### API Key Validation
- Direct API key authentication is supported via both the `X-API-Key` header and the `Authorization: Key <api_key>` header format.
- A secure admin API key can be defined in configuration for direct machine-to-machine integrations.

---

## 2. Permission Model

YasinFeed implements a role-based access control (RBAC) permission model mapping roles to specific system permissions:

| Role | Permissions | Description |
|---|---|---|
| `admin` | `read:articles`, `write:articles`, `read:sources`, `write:sources`, `read:scheduler`, `write:scheduler`, `read:stats`, `admin` | Full read/write access to all resources and management APIs. |
| `viewer` | `read:articles`, `read:stats` | Read-only access to compiled feeds, articles, and dashboard statistics. |

Enforced permissions on REST API endpoints when security is enabled:
- `GET /api/articles` / `GET /api/feed` -> Requires `read:articles`
- `GET /api/sources` -> Requires `read:sources`
- `GET /api/scheduler` -> Requires `read:scheduler`
- `GET /api/stats` -> Requires `read:stats`

---

## 3. Configuration Options

Configure the security settings inside the `config/config.yaml` file under the `api.security` section:

```yaml
api:
  host: 127.0.0.1
  port: 8000
  security:
    enabled: true                  # Set to true to enforce authentication and permissions
    rate_limit_per_minute: 60      # Max requests per minute per IP address
    admin_api_key: "my-secure-key" # Machine-to-machine Admin API key
    token_expiry_hours: 24         # Duration of session tokens in hours
```

---

## 4. Rate Limiting Middleware

A rolling-window IP-based rate limiting foundation is integrated directly into the API request handler. When the limit is exceeded, the server responds with a standard `429 Too Many Requests` status code and JSON payload.

---

## 5. Security Headers

To protect clients and prevent exploits, the REST server automatically injects strong security headers in all JSON responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HSTS)
- Standard CORS headers enabling safe integration.
