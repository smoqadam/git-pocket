import json
from newspaper import Article
from datetime import datetime
import sys
import re
import os
from pathlib import Path

ENTRIES_DIR = Path("entries")
INDEX_FILE = Path("index.html")

def load_payload():
    with open("payload.json") as f:
        payload = json.load(f)
    
    try:
        url = payload["client_payload"]["url"]
        return url
    except KeyError:
        print("No URL found in payload — likely triggered by push event. Exiting.")
        sys.exit(0)

def extract_article(url):
    article = Article(url)
    article.download()
    article.parse()
    return article

def save_article_html(article, url):
    slug = re.sub(r'[^a-zA-Z0-9\-]', '-', article.title.lower())[:50]
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    filename = f"entries/{timestamp}-{slug}.html"
    
    os.makedirs("entries", exist_ok=True)
    
    existing_files = list(ENTRIES_DIR.glob("*.html"))
    for existing_file in existing_files:
        with open(existing_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if url in content:
                print(f"Article from {url} already exists: {existing_file}")
                return existing_file.name
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        .nav {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        .nav a {{
            color: #007acc;
            text-decoration: none;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
        .source {{
            font-style: italic;
            color: #666;
            margin-bottom: 20px;
        }}
        .content {{
            text-align: justify;
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../index.html">← Back to Index</a>
    </div>
    <h1>{article.title}</h1>
    <div class="source">Source: <a href="{url}">{url}</a></div>
    <div class="content">
        {article.text.replace(chr(10), '</p><p>')}
    </div>
</body>
</html>"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return filename

def generate_index():
    os.makedirs("entries", exist_ok=True)
    entries = sorted(ENTRIES_DIR.glob("*.html"), reverse=True)
    
    links = []
    for entry in entries:
        try:
            with open(entry, 'r', encoding='utf-8') as f:
                content = f.read()
                title_match = re.search(r'<h1>(.*?)</h1>', content)
                if title_match:
                    title = title_match.group(1)
                else:
                    title = entry.name.replace('.html', '').replace('-', ' ').title()
        except Exception:
            title = entry.name.replace('.html', '').replace('-', ' ').title()
        
        url = f"./entries/{entry.name}"
        links.append(f'<li><a href="{url}">{title}</a></li>')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Read It Later - Index</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        ul {{
            list-style-type: none;
            padding: 0;
        }}
        li {{
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        a {{
            color: #007acc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Saved Articles</h1>
    <ul>
        {''.join(links)}
    </ul>
</body>
</html>"""
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    url = load_payload()
    if url:
        article = extract_article(url)
        save_article_html(article, url)
    generate_index()

if __name__ == "__main__":
    main()
