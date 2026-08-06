import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from yasinfeed.engine import BaseModule


class YasinFeedAPIRequestHandler(BaseHTTPRequestHandler):
    """
    REST request handler for YasinFeed API endpoints.
    Provides standard JSON endpoints for articles, feed sources, and scheduler state.
    """

    def send_json(self, data: Any, status_code: int = 200) -> None:
        """Helper to send a structured JSON response with correct headers."""
        try:
            response_bytes = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(response_bytes)
        except Exception as e:
            self.log_error("Error sending JSON response: %s", e)

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle REST GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # Retrieve sibling modules from the engine
        api_mod = self.server.api_module
        engine = api_mod.engine
        storage = engine.modules.get("storage")
        scheduler_mod = engine.modules.get("scheduler")

        # Route matching
        try:
            # 1. Health endpoint
            if path == "/health" or path == "/api/health":
                health_data = {
                    "status": "ok",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "YasinFeed API Layer"
                }
                self.send_json(health_data, 200)
                return

            # 2. Articles endpoints
            elif path == "/api/articles":
                if not storage:
                    self.send_json({"error": "Storage module is unavailable"}, 503)
                    return

                # Check if a specific ID was requested via query param
                article_ids = query.get("id")
                if article_ids:
                    article_id = article_ids[0]
                    self._handle_single_article(storage, article_id)
                else:
                    self._handle_list_articles(storage)
                return

            elif path.startswith("/api/articles/"):
                if not storage:
                    self.send_json({"error": "Storage module is unavailable"}, 503)
                    return

                article_id = path[len("/api/api/articles/"):] if path.startswith("/api/api/") else path[len("/api/articles/"):]
                self._handle_single_article(storage, article_id)
                return

            # 3. Sources endpoint
            elif path == "/api/sources":
                if not storage:
                    self.send_json({"error": "Storage module is unavailable"}, 503)
                    return

                try:
                    sources = storage.list_feed_sources()
                    serialized_sources = [
                        {
                            "id": s.id,
                            "url": s.url,
                            "name": s.name,
                            "enabled": s.enabled,
                            "last_fetched_at": s.last_fetched_at.isoformat() if s.last_fetched_at and hasattr(s.last_fetched_at, "isoformat") else None
                        }
                        for s in sources
                    ]
                    self.send_json(serialized_sources, 200)
                except Exception as e:
                    api_mod.logger.error("Failed to retrieve feed sources: %s", e, exc_info=True)
                    self.send_json({"error": f"Failed to retrieve feed sources: {str(e)}"}, 500)
                return

            # 4. Scheduler endpoint
            elif path == "/api/scheduler":
                if not scheduler_mod:
                    self.send_json({"error": "Scheduler module is unavailable"}, 503)
                    return

                try:
                    jobs = scheduler_mod.scheduler.list_jobs()
                    serialized_jobs = [job.to_dict() for job in jobs]
                    scheduler_status = {
                        "enabled": scheduler_mod.enabled,
                        "jobs": serialized_jobs
                    }
                    self.send_json(scheduler_status, 200)
                except Exception as e:
                    api_mod.logger.error("Failed to retrieve scheduler status: %s", e, exc_info=True)
                    self.send_json({"error": f"Failed to retrieve scheduler status: {str(e)}"}, 500)
                return

            # 5. Not Found
            else:
                self.send_json({"error": f"Endpoint '{path}' not found"}, 404)
                return

        except Exception as e:
            api_mod.logger.error("Unexpected error in API request handler: %s", e, exc_info=True)
            self.send_json({"error": f"Internal Server Error: {str(e)}"}, 500)

    def _handle_single_article(self, storage: Any, article_id: str) -> None:
        """Helper to fetch and serialize a single article."""
        try:
            article = storage.get_article(article_id)
            if not article:
                self.send_json({"error": f"Article with ID '{article_id}' not found"}, 404)
                return

            serialized = {
                "id": article.id,
                "source_id": article.source_id,
                "title": article.title,
                "content": article.content,
                "original_url": article.original_url,
                "published_at": article.published_at.isoformat() if hasattr(article.published_at, "isoformat") else str(article.published_at),
                "rewritten_content": article.rewritten_content,
                "rewrite_status": article.rewrite_status,
                "published_outputs": article.published_outputs
            }
            self.send_json(serialized, 200)
        except Exception as e:
            self.server.api_module.logger.error("Failed to retrieve article '%s': %s", article_id, e, exc_info=True)
            self.send_json({"error": f"Failed to retrieve article: {str(e)}"}, 500)

    def _handle_list_articles(self, storage: Any) -> None:
        """Helper to list and serialize all articles."""
        try:
            articles = storage.list_articles()
            serialized_list = [
                {
                    "id": a.id,
                    "source_id": a.source_id,
                    "title": a.title,
                    "content": a.content,
                    "original_url": a.original_url,
                    "published_at": a.published_at.isoformat() if hasattr(a.published_at, "isoformat") else str(a.published_at),
                    "rewritten_content": a.rewritten_content,
                    "rewrite_status": a.rewrite_status,
                    "published_outputs": a.published_outputs
                }
                for a in articles
            ]
            self.send_json(serialized_list, 200)
        except Exception as e:
            self.server.api_module.logger.error("Failed to retrieve articles: %s", e, exc_info=True)
            self.send_json({"error": f"Failed to retrieve articles: {str(e)}"}, 500)

    def do_POST(self):
        import json

        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            data = json.loads(body.decode("utf-8"))

            api = self.server.api_module

            if path == "/api/auth/register":
                response, status = api.handle_register(data)

            elif path == "/api/auth/login":
                response, status = api.handle_login(data)

            else:
                response = {
                    "status": "error",
                    "message": "Endpoint not found"
                }
                status = 404

            self.send_json(response, status)

        except Exception as e:
            self.send_json(
                {
                    "status": "error",
                    "message": str(e)
                },
                500
            )


    def log_message(self, format: str, *args: Any) -> None:
        """Intercept standard logs and route them through the core engine's logger."""
        self.server.api_module.logger.info(format, *args)


class ApiModule(BaseModule):
    """
    Exposes REST endpoints for PWA clients and other components to consume feed outputs.
    Provides seamless zero-dependency integration across core modules.
    """

    def initialize(self) -> bool:
        self.logger.info("Initializing API module...")
        self.host = self.config.get("api", {}).get("host", "127.0.0.1")
        self.port = self.config.get("api", {}).get("port", 8000)
        self.logger.info("API server bound to %s:%d", self.host, self.port)
        return True

    def start(self) -> bool:
        self.logger.info("API module starting...")
        try:
            self.server = ThreadingHTTPServer((self.host, self.port), YasinFeedAPIRequestHandler)
            self.server.api_module = self

            # Update the port if dynamically assigned (e.g. port 0 for testing)
            self.port = self.server.server_address[1]

            import threading
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True,
                name="YasinFeedAPIHTTPServer"
            )
            self.server_thread.start()
            self.logger.info("API module started. Listening on http://%s:%d", self.host, self.port)
            return True
        except Exception as e:
            self.logger.error("Failed to start API server on %s:%d: %s", self.host, self.port, e, exc_info=True)
            return False

    def handle_register(self, request_data: dict) -> tuple:
        """
        Simulates POST /api/auth/register endpoint.
        Expects request_data to have 'username' and 'password'.
        Returns tuple of (JSON-like dictionary response, status_code).
        """
        username = request_data.get("username")
        password = request_data.get("password")
        auth_module = self.engine.modules.get("auth")
        if not auth_module:
            return {"status": "error", "message": "Auth system unavailable"}, 500

        try:
            user = auth_module.register_user(username, password)
            return {
                "status": "success",
                "message": "User registered successfully",
                "data": {"user_id": user.id, "username": user.username}
            }, 201
        except ValueError as e:
            return {"status": "error", "message": str(e)}, 400
        except Exception as e:
            return {"status": "error", "message": "Internal server error"}, 500

    def handle_login(self, request_data: dict) -> tuple:
        """
        Simulates POST /api/auth/login endpoint.
        Expects request_data to have 'username' and 'password'.
        Returns tuple of (JSON-like dictionary response, status_code).
        """
        username = request_data.get("username")
        password = request_data.get("password")
        auth_module = self.engine.modules.get("auth")
        if not auth_module:
            return {"status": "error", "message": "Auth system unavailable"}, 500

        session = auth_module.login(username, password)
        if not session:
            return {"status": "error", "message": "Invalid username or password"}, 401

        return {
            "status": "success",
            "message": "Login successful",
            "data": {
                "token": session.token,
                "expires_at": session.expires_at.isoformat()
            }
        }, 200

    def handle_get_articles(self, headers: dict) -> tuple:
        """
        Simulates GET /api/feed endpoint (protected).
        Requires Authorization header format: 'Bearer <token>'.
        Returns tuple of (JSON-like dictionary response, status_code).
        """
        auth_header = headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"status": "error", "message": "Authorization token required"}, 401

        token = auth_header[7:].strip()
        auth_module = self.engine.modules.get("auth")
        if not auth_module:
            return {"status": "error", "message": "Auth system unavailable"}, 500

        user = auth_module.authenticate_token(token)
        if not user:
            return {"status": "error", "message": "Invalid or expired authorization token"}, 401

        # Retrieve articles
        storage = self.engine.modules.get("storage")
        if not storage:
            return {"status": "error", "message": "Storage system unavailable"}, 500

        articles = storage.list_articles()
        articles_data = [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "original_url": a.original_url,
                "published_at": a.published_at.isoformat(),
                "rewritten_content": a.rewritten_content,
                "rewrite_status": a.rewrite_status
            }
            for a in articles
        ]

        return {
            "status": "success",
            "user": user.username,
            "data": articles_data
        }, 200

    def stop(self) -> bool:
        self.logger.info("API module stopping...")
        if hasattr(self, 'server') and self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception as e:
                self.logger.warning("Error during API server shutdown: %s", e)
        if hasattr(self, 'server_thread') and self.server_thread:
            self.server_thread.join(timeout=3.0)
        self.logger.info("API module stopped. Socket connection closed.")
        return True
