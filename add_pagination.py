from pathlib import Path

p = Path("yasinfeed/api/__init__.py")

text = p.read_text()

old = '''                else:
                    self._handle_list_articles(storage)
                return
'''

new = '''                else:
                    page = int(query.get("page", ["1"])[0])
                    limit = int(query.get("limit", ["10"])[0])

                    articles = storage.list_articles()

                    total = len(articles)

                    start = (page - 1) * limit
                    end = start + limit

                    paginated = articles[start:end]

                    serialized = [
                        {
                            "id": a.id,
                            "title": a.title,
                            "content": a.content,
                            "published_at": a.published_at.isoformat()
                            if hasattr(a.published_at, "isoformat")
                            else str(a.published_at),
                            "rewrite_status": a.rewrite_status
                        }
                        for a in paginated
                    ]

                    self.send_json(
                        {
                            "status": "success",
                            "page": page,
                            "limit": limit,
                            "total": total,
                            "data": serialized
                        },
                        200
                    )

                return
'''

if "paginated =" not in text:
    text = text.replace(old, new)
    p.write_text(text)
    print("Pagination added.")
else:
    print("Pagination already exists.")
