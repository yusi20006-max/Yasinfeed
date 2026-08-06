from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # 5. Not Found
            else:
'''

new = '''            # 5. Authenticated Feed Endpoint
            elif path == "/api/feed":
                response, status = api_mod.handle_get_articles(dict(self.headers))
                self.send_json(response, status)
                return

            # 6. Not Found
            else:
'''

if 'path == "/api/feed"' not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Feed route added.")
else:
    print("Feed route already exists.")
