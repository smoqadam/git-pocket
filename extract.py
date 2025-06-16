import json
from newspaper import Article
from datetime import datetime
import sys
import re
import os
from pathlib import Path

ENTRIES_DIR = Path("entries")
INDEX_FILE = Path("index.html")

def generate_index():
    entries = sorted(ENTRIES_DIR.glob("*"), reverse=True)
    
    links = []
    for entry in entries:
        filename = entry.name
        url = f"./entries/{filename}"
        links.append(f'<li><a href="{url}">{filename}</a></li>')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Read It Later - Index</title>
</head>
<body>
  <h1>Saved Articles</h1>
  <ul>
    {''.join(links)}
  </ul>
</body>
</html>
"""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

with open("payload.json") as f:
    payload = json.load(f)

try:
    url = payload["client_payload"]["url"]
except KeyError:
    print("No URL found in payload — likely triggered by push event. Exiting.")
    sys.exit(0)

article = Article(url)
article.download()
article.parse()

slug = re.sub(r'[^a-zA-Z0-9\-]', '-', article.title.lower())[:50]
timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
filename = f"entries/{timestamp}-{slug}.html"

os.makedirs("entries", exist_ok=True)

with open(filename, "w") as f:
    f.write(f"# {article.title}\n\n")
    f.write(f"*Source: [{url}]({url})*\n\n")
    f.write(article.text)
    generate_index()
