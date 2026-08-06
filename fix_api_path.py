from pathlib import Path

p = Path("yasinfeed/api/__init__.py")
text = p.read_text()

old = 'article_id = path[len("/api/api/articles/"):] if path.startswith("/api/api/") else path[len("/api/articles/"): ]'
old2 = 'article_id = path[len("/api/api/articles/"):] if path.startswith("/api/api/") else path[len("/api/articles/"):]'

if old in text:
    text = text.replace(old, 'article_id = path[len("/api/articles/"):]')
elif old2 in text:
    text = text.replace(old2, 'article_id = path[len("/api/articles/"):]')

p.write_text(text)

print("API article path fixed.")
