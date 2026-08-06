from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # API Routes Discovery
            elif path == "/api/routes":
'''

new = '''            # Version Endpoint
            elif path == "/api/version":
                self.send_json(
                    {
                        "name": "YasinFeed",
                        "version": "1.0.0",
                        "api": "v1"
                    },
                    200
                )
                return

            # API Routes Discovery
            elif path == "/api/routes":
'''

if 'path == "/api/version"' not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Version endpoint added.")
else:
    print("Version already exists.")
