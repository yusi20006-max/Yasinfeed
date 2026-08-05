# YasinFeed REST API Layer

This document describes the design, integration, and endpoints of the REST API Layer implemented in YasinFeed.

---

## Architectural Principles

The API module (`yasinfeed/api`) is designed to serve as a high-performance, zero-dependency, and lightweight query/delivery layer for external integrations, such as PWA frontends or control panels.

### Termux & Linux Compatibility
To maintain absolute out-of-the-box compatibility with Linux and Termux on Android, the API layer is implemented using Python's standard `http.server` library (utilizing `ThreadingHTTPServer` and `BaseHTTPRequestHandler`). It operates without third-party frameworks like Flask or FastAPI, keeping the codebase lightweight and highly portable.

---

## Engine & Module Integration

The API module runs in a non-blocking, multi-threaded environment.

1. **Lifecycle Management**: When the YasinFeed engine starts, `ApiModule.start()` is called, which boots the HTTP server on a background daemon thread (`YasinFeedAPIHTTPServer`) to handle requests concurrently. On shutdown, `ApiModule.stop()` gracefully triggers `server.shutdown()` and `server.server_close()`.
2. **Dynamic Binding**: By default, the API binds to the configured host and port (defaults to `127.0.0.1:8000`). If configured with port `0`, the server dynamically binds to a random available port.
3. **Core Integration**: The request handler utilizes `self.server.api_module.engine.modules` to securely query companion modules (`StorageModule` and `SchedulerModule`) on-demand.
4. **CORS Preflight**: Full support for Cross-Origin Resource Sharing (CORS) with `OPTIONS` response handling is included, allowing browsers, PWAs, and local clients to interact with the API seamlessly.
5. **Centralized Logging**: Standard server request logs are intercepted and routed through the unified YasinFeed logging handler, conforming to the pattern `[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s`.

---

## REST Endpoints Reference

### 1. Health Status
Returns the server status, UTC timestamp, and service info.

- **Path**: `/health` or `/api/health`
- **Method**: `GET`
- **Response**: `200 OK`
- **Payload Example**:
  ```json
  {
    "status": "ok",
    "timestamp": "2026-08-05T20:58:34.214256+00:00",
    "service": "YasinFeed API Layer"
  }
  ```

---

### 2. List Curated Articles
Retrieves all processed and saved articles from the active storage backend.

- **Path**: `/api/articles`
- **Method**: `GET`
- **Response**: `200 OK` (or `503 Service Unavailable` if storage is disconnected)
- **Payload Example**:
  ```json
  [
    {
      "id": "art123",
      "source_id": "src_tech",
      "title": "Python is amazing",
      "content": "Python is widely used in AI, web development, and backend services.",
      "original_url": "https://python.org",
      "published_at": "2026-08-05T20:55:00+00:00",
      "rewritten_content": "Python is great for backend development and artificial intelligence.",
      "rewrite_status": "completed",
      "published_outputs": ["eitaa", "rss"]
    }
  ]
  ```

---

### 3. Get Specific Article
Retrieves detailed information for a single article. Supports both path variables and query parameters.

- **Path Options**:
  - `/api/articles?id={id}`
  - `/api/articles/{id}`
- **Method**: `GET`
- **Response**: `200 OK` (or `404 Not Found` if the article ID does not exist)
- **Payload Example**:
  ```json
  {
    "id": "art123",
    "source_id": "src_tech",
    "title": "Python is amazing",
    "content": "Python is widely used in AI, web development, and backend services.",
    "original_url": "https://python.org",
    "published_at": "2026-08-05T20:55:00+00:00",
    "rewritten_content": "Python is great for backend development and artificial intelligence.",
    "rewrite_status": "completed",
    "published_outputs": ["eitaa", "rss"]
  }
  ```

---

### 4. List Feed Sources
Lists all feed channels configured in the system.

- **Path**: `/api/sources`
- **Method**: `GET`
- **Response**: `200 OK`
- **Payload Example**:
  ```json
  [
    {
      "id": "src_ai",
      "url": "https://openai.com/feed.xml",
      "name": "OpenAI Blog",
      "enabled": true,
      "last_fetched_at": "2026-08-05T20:50:00+00:00"
    }
  ]
  ```

---

### 5. Background Scheduler Status
Queries status and execution tracking data for registered periodic jobs (e.g. `fetch_and_process`).

- **Path**: `/api/scheduler`
- **Method**: `GET`
- **Response**: `200 OK`
- **Payload Example**:
  ```json
  {
    "enabled": true,
    "jobs": [
      {
        "name": "fetch_and_process",
        "interval": 300.0,
        "enabled": true,
        "last_run_start": "2026-08-05T20:45:00+00:00",
        "last_run_end": "2026-08-05T20:45:02+00:00",
        "next_run": "2026-08-05T20:50:00+00:00",
        "run_count": 5,
        "success_count": 5,
        "failure_count": 0,
        "last_status": "success",
        "last_error": null,
        "last_duration": 2.134
      }
    ]
  }
  ```

---

## Error Handling

Standardized JSON payloads are returned on all operational or routing errors:

- **404 Not Found** (Routing or Missing ID):
  ```json
  {
    "error": "Endpoint '/api/invalid' not found"
  }
  ```
- **503 Service Unavailable** (Dependency module disabled):
  ```json
  {
    "error": "Storage module is unavailable"
  }
  ```
- **500 Internal Server Error**:
  ```json
  {
    "error": "Internal Server Error: [Specific traceback message]"
  }
  ```
