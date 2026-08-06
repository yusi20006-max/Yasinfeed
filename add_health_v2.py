from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # 5. Not Found
            else:
'''

new = '''            # Health Check
            elif path == "/api/health":
                self.send_json(
                    {
                        "status": "ok",
                        "service": "YasinFeed",
                        "version": "1.0.0"
                    },
                    200
                )
                return

            # 5. Not Found
            else:
'''

if 'path == "/api/health"' not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Health endpoint added.")
else:
    print("Health already exists.")
