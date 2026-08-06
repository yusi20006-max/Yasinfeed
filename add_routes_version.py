from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # 7. Not Found
            else:
'''

new = '''            # 7. API Routes Discovery
            elif path == "/api/routes":
                routes = {
                    "status": "success",
                    "service": "YasinFeed API",
                    "routes": [
                        "GET /api/health",
                        "POST /api/auth/login",
                        "GET /api/feed",
                        "GET /api/articles",
                        "GET /api/articles/{id}",
                        "GET /api/sources",
                        "GET /api/scheduler",
                        "GET /api/stats",
                        "GET /api/version"
                    ]
                }

                self.send_json(routes, 200)
                return

            # 8. API Version
            elif path == "/api/version":
                version = {
                    "status": "success",
                    "service": "YasinFeed API",
                    "version": "1.0.0",
                    "api_version": "v1"
                }

                self.send_json(version, 200)
                return

            # 9. Not Found
            else:
'''

if 'path == "/api/routes"' not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Routes and version endpoints added.")
else:
    print("Already exists.")
