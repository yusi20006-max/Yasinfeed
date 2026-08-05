from yasinfeed.engine import BaseModule

class ApiModule(BaseModule):
    """
    Exposes endpoints for PWA clients and other components to consume feed outputs.
    """
    def initialize(self) -> bool:
        self.logger.info("Initializing API module...")
        self.host = self.config.get("api", {}).get("host", "127.0.0.1")
        self.port = self.config.get("api", {}).get("port", 8000)
        self.logger.info("API server bound to %s:%d", self.host, self.port)
        return True

    def start(self) -> bool:
        self.logger.info("API module started. Listening on http://%s:%d", self.host, self.port)
        return True

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
        self.logger.info("API module stopped. Socket connection closed.")
        return True
