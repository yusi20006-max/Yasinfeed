from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # Health Check
            elif path == "/api/health":
'''

new = '''            # API Routes Discovery
            elif path == "/api/routes":
                self.send_json(
                    {
                        "service": "YasinFeed",
                        "routes": [
                            "POST /api/auth/login",
                            "GET /api/feed",
                            "GET /api/articles",
                            "GET /api/articles/{id}",
                            "GET /api/stats",
                            "GET /api/health",
                            "GET /api/routes"
                        ]
                    },
                    200
                )
                return

            # Health Check
            elif path == "/api/health":
'''

if 'path == "/api/routes"' not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Routes endpoint added.")
else:
    print("Routes already exists.")
