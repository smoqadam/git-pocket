import json
from newspaper import Article
from datetime import datetime
import os
import re

# Load webhook payload
with open("payload.json") as f:
    payload = json.load(f)

url = payload["url"]
article = Article(url)
article.download()
article.parse()

# Sanitize filename
slug = re.sub(r'[^a-zA-Z0-9\-]', '-', article.title.lower())[:50]
timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
filename = f"entries/{timestamp}-{slug}.md"

# Ensure directory exists
os.makedirs("entries", exist_ok=True)

# Save as Markdown
with open(filename, "w") as f:
    f.write(f"# {article.title}\n\n")
    f.write(f"*Source: [{url}]({url})*\n\n")
    f.write(article.text)
