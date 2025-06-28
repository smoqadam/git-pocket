import json
import logging
import hashlib
import urllib.parse
from newspaper import Article
from datetime import datetime
import sys
import re
import os
from pathlib import Path
import requests
from PIL import Image
from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup

ENTRIES_DIR = Path("entries")
IMAGES_DIR = Path("images")
INDEX_FILE = Path("index.html")
RSS_FILE = Path("rss.xml")
METADATA_FILE = Path("metadata.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_payload():
    try:
        with open("payload.json") as f:
            payload = json.load(f)
        
        url = payload.get("client_payload", {}).get("url")
        if url:
            logger.info(f"Loaded URL from payload: {url}")
            return url
        else:
            logger.info("No URL found in payload - likely triggered by push event")
            return None
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error loading payload: {e}")
        return None

def extract_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        logger.info(f"Successfully extracted article: {article.title}")
        return article
    except Exception as e:
        logger.error(f"Error extracting article from {url}: {e}")
        raise

def get_url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:8]

def load_metadata():
    try:
        if METADATA_FILE.exists():
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
    return {}

def save_metadata(metadata):
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info("Metadata saved successfully")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")

def download_image(img_url, filename):
    try:
        response = requests.get(img_url, stream=True, timeout=10)
        response.raise_for_status()
        
        os.makedirs(IMAGES_DIR, exist_ok=True)
        img_path = IMAGES_DIR / filename
        
        with open(img_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        with Image.open(img_path) as img:
            if img.width > 800:
                ratio = 800 / img.width
                new_size = (800, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                img.save(img_path, optimize=True, quality=85)
        
        logger.info(f"Downloaded and processed image: {filename}")
        return str(img_path)
    except Exception as e:
        logger.error(f"Error downloading image {img_url}: {e}")
        return None

def process_images(article_text, article_url, slug):
    try:
        soup = BeautifulSoup(article_text, 'html.parser')
        images = soup.find_all('img')
        
        for i, img in enumerate(images):
            img_url = img.get('src')
            if not img_url:
                continue
                
            if not img_url.startswith('http'):
                img_url = urllib.parse.urljoin(article_url, img_url)
            
            img_filename = f"{slug}_{i}.jpg"
            local_path = download_image(img_url, img_filename)
            
            if local_path:
                img['src'] = f"../images/{img_filename}"
        
        return str(soup)
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        return article_text

def check_duplicate(url):
    metadata = load_metadata()
    url_hash = get_url_hash(url)
    
    for entry_id, entry_data in metadata.items():
        if entry_data.get('url') == url or entry_data.get('url_hash') == url_hash:
            logger.info(f"Duplicate found: {entry_data.get('filename')}")
            return entry_data.get('filename')
    
    return None

def save_article_html(article, url):
    try:
        duplicate = check_duplicate(url)
        if duplicate:
            return duplicate
        
        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', article.title.lower())[:50]
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{timestamp}-{slug}.html"
        filepath = ENTRIES_DIR / filename
        
        os.makedirs(ENTRIES_DIR, exist_ok=True)
        
        article_content = process_images(article.text, url, slug)
        
        publish_date = article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat()
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article.title}</title>
    <meta name="author" content="{', '.join(article.authors)}">
    <meta name="description" content="{article.summary[:160]}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.7;
            color: #333;
            background-color: #fafafa;
        }}
        .nav {{
            margin-bottom: 30px;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .nav a {{
            color: white;
            text-decoration: none;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
        .article-header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 2.2em;
            margin-bottom: 20px;
            color: #2c3e50;
            line-height: 1.3;
        }}
        .metadata {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .source {{
            color: #007acc;
            text-decoration: none;
            border: 1px solid #007acc;
            padding: 8px 16px;
            border-radius: 25px;
            font-size: 0.85em;
            transition: all 0.3s ease;
        }}
        .source:hover {{
            background-color: #007acc;
            color: white;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: justify;
        }}
        .content p {{
            margin-bottom: 20px;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #007acc;
            margin-bottom: 30px;
            border-radius: 0 10px 10px 0;
            font-style: italic;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .article-header, .content {{ padding: 20px; }}
            h1 {{ font-size: 1.8em; }}
            .metadata {{ justify-content: center; }}
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../index.html">← Back to Index</a>
    </div>
    <div class="article-header">
        <h1>{article.title}</h1>
        <div class="metadata">
            <div class="metadata-item">📅 {publish_date[:10]}</div>
            {f'<div class="metadata-item">✍️ {", ".join(article.authors)}</div>' if article.authors else ''}
            <div class="metadata-item">🔗 <a href="{url}" class="source" target="_blank">Original Source</a></div>
        </div>
        {f'<div class="summary"><strong>Summary:</strong> {article.summary}</div>' if article.summary else ''}
    </div>
    <div class="content">
        {article_content.replace(chr(10), '</p><p>')}
    </div>
</body>
</html>"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        metadata = load_metadata()
        entry_id = timestamp + "-" + slug
        metadata[entry_id] = {
            'title': article.title,
            'url': url,
            'url_hash': get_url_hash(url),
            'filename': filename,
            'date': publish_date,
            'authors': article.authors,
            'summary': article.summary,
            'keywords': article.keywords[:10] if article.keywords else []
        }
        save_metadata(metadata)
        
        logger.info(f"Saved new article: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error saving article: {e}")
        raise

def generate_rss():
    try:
        metadata = load_metadata()
        
        fg = FeedGenerator()
        fg.title('Read It Later')
        fg.description('Personal article archive')
        fg.link(href='https://example.com', rel='alternate')
        fg.language('en')
        
        sorted_entries = sorted(metadata.items(), key=lambda x: x[1].get('date', ''), reverse=True)
        
        for entry_id, entry_data in sorted_entries[:20]:
            fe = fg.add_entry()
            fe.title(entry_data['title'])
            fe.description(entry_data.get('summary', ''))
            fe.link(href=entry_data['url'])
            fe.guid(entry_data['url'])
            fe.pubDate(entry_data['date'])
            fe.author({'name': ', '.join(entry_data.get('authors', []))})
        
        fg.rss_file(str(RSS_FILE))
        logger.info("RSS feed generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating RSS feed: {e}")

def generate_index():
    try:
        os.makedirs(ENTRIES_DIR, exist_ok=True)
        metadata = load_metadata()
        
        sorted_entries = sorted(metadata.items(), key=lambda x: x[1].get('date', ''), reverse=True)
        
        logger.info(f"Found {len(sorted_entries)} total entries")
        
        article_data = []
        for entry_id, entry_data in sorted_entries:
            article_data.append({
                'title': entry_data['title'],
                'filename': entry_data['filename'],
                'date': entry_data.get('date', '').split('T')[0],
                'authors': ', '.join(entry_data.get('authors', [])),
                'summary': entry_data.get('summary', '')[:150] + '...' if entry_data.get('summary', '') else '',
                'keywords': entry_data.get('keywords', [])
            })

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Read It Later - Personal Archive</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }}
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .search-container {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}
        .search-box {{
            width: 100%;
            padding: 15px 20px;
            font-size: 1.1em;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            outline: none;
            transition: border-color 0.3s ease;
        }}
        .search-box:focus {{
            border-color: #667eea;
        }}
        .stats {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            color: #666;
            font-size: 0.9em;
        }}
        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }}
        .article-card {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .article-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        .article-content {{
            padding: 25px;
        }}
        .article-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            line-height: 1.4;
            text-decoration: none;
        }}
        .article-title:hover {{
            color: #667eea;
        }}
        .article-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 15px;
            color: #666;
            font-size: 0.85em;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .article-summary {{
            color: #555;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        .article-keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .keyword {{
            background: #f0f2f5;
            color: #555;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75em;
        }}
        .no-results {{
            text-align: center;
            color: white;
            font-size: 1.2em;
            margin-top: 50px;
        }}
        .rss-link {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #ff6b35;
            color: white;
            padding: 12px 16px;
            border-radius: 25px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        .rss-link:hover {{
            transform: scale(1.05);
        }}
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2em; }}
            .articles-grid {{ grid-template-columns: 1fr; }}
            .stats {{ flex-direction: column; gap: 10px; text-align: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Read It Later</h1>
            <p>Your Personal Article Archive</p>
        </div>
        
        <div class="search-container">
            <input type="text" id="searchBox" class="search-box
