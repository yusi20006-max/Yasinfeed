from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''            # 5. Authenticated Feed Endpoint
            elif path == "/api/feed":
                response, status = api_mod.handle_get_articles(dict(self.headers))
                self.send_json(response, status)
                return

            # 6. Not Found
            else:
'''

new = '''            # 5. Authenticated Feed Endpoint
            elif path == "/api/feed":
                response, status = api_mod.handle_get_articles(dict(self.headers))
                self.send_json(response, status)
                return

            # 6. Dashboard Statistics
            elif path == "/api/stats":
                storage = engine.modules.get("storage")

                if not storage:
                    self.send_json(
                        {"error": "Storage module unavailable"},
                        503
                    )
                    return

                try:
                    articles = storage.list_articles()
                    sources = storage.list_feed_sources()

                    total_articles = len(articles)

                    rewritten = len([
                        a for a in articles
                        if a.rewrite_status == "completed"
                    ])

                    stats = {
                        "status": "success",
                        "data": {
                            "articles_total": total_articles,
                            "rewrites_completed": rewritten,
                            "sources_total": len(sources),
                            "service": "YasinFeed API"
                        }
                    }

                    self.send_json(stats, 200)

                except Exception as e:
                    self.send_json(
                        {
                            "status": "error",
                            "message": str(e)
                        },
                        500
                    )

                return

            # 7. Not Found
            else:
'''

if 'path == "/api/stats"' not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Stats route added.")
else:
    print("Stats route already exists.")
