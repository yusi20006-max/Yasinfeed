from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # 5. Authenticated Feed Endpoint
            elif path == "/api/feed":
'''

new = '''            # Health Check
            elif path == "/api/health":
                self.send_json(
                    {
                        "status": "success",
                        "service": "YasinFeed API",
                        "engine": "running"
                    },
                    200
                )
                return

            # Authenticated Feed Endpoint
            elif path == "/api/feed":
'''

if '"/api/health"' not in text:
    text = text.replace(old,new)
    p.write_text(text)
    print("Health endpoint added.")
else:
    print("Already exists.")
