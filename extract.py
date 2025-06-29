import json
import logging
import hashlib
import urllib.parse
from datetime import datetime
import sys
import re
import os
from pathlib import Path
import requests
from PIL import Image
from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
from readability import Document

ENTRIES_DIR = Path("entries")
IMAGES_DIR = Path("images")
TEMPLATES_DIR = Path("templates")
INDEX_FILE = Path("index.html")
RSS_FILE = Path("rss.xml")
METADATA_FILE = Path("metadata.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_template(template_name):
    try:
        template_path = TEMPLATES_DIR / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading template {template_name}: {e}")
        raise

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

def extract_article(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        doc = Document(resp.text)
        title = doc.short_title()
        summary_html = doc.summary(html_partial=False)
        soup = BeautifulSoup(summary_html, "html.parser")

        # Try to extract author from meta tags
        author = ""
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            author = meta_author["content"]
        else:
            # Try Open Graph
            og_author = soup.find("meta", attrs={"property": "article:author"})
            if og_author and og_author.get("content"):
                author = og_author["content"]

        # Try to extract publish date from meta tags
        date = ""
        meta_date = soup.find("meta", attrs={"property": "article:published_time"})
        if meta_date and meta_date.get("content"):
            date = meta_date["content"]
        else:
            meta_date = soup.find("meta", attrs={"name": "date"})
            if meta_date and meta_date.get("content"):
                date = meta_date["content"]

        logger.info(f"Successfully extracted article: {title}")
        return {
            "title": title,
            "content_html": str(soup),
            "authors": [author] if author else [],
            "publish_date": date,
            "url": url,
        }
    except Exception as e:
        logger.error(f"Error extracting article from {url}: {e}")
        raise

def process_images(article_html, article_url, slug):
    try:
        soup = BeautifulSoup(article_html, 'html.parser')
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
        return article_html

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

        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', article["title"].lower())[:50]
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{timestamp}-{slug}.html"
        filepath = ENTRIES_DIR / filename

        os.makedirs(ENTRIES_DIR, exist_ok=True)

        article_content = process_images(article["content_html"], url, slug)

        publish_date = article["publish_date"] or datetime.now().isoformat()

        template = load_template('article.html')

        author_section = f'<div class="metadata-item">✍️ {", ".join(article["authors"])}</div>' if article["authors"] else ''

        html_content = template.format(
            title=article["title"],
            authors=', '.join(article["authors"]),
            date=publish_date[:10],
            url=url,
            author_section=author_section,
            content=article_content
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        metadata = load_metadata()
        entry_id = timestamp + "-" + slug
        metadata[entry_id] = {
            'title': article["title"],
            'url': url,
            'url_hash': get_url_hash(url),
            'filename': filename,
            'date': publish_date,
            'authors': article["authors"],
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
            })

        articles_html = ""
        for article in article_data:
            author_meta = f'<div class="meta-item">✍️ {article["authors"]}</div>' if article['authors'] else ''
            
            articles_html += f'''
            <div class="article-card" data-title="{article['title'].lower()}" data-author="{article['authors'].lower()}">
                <div class="article-content">
                    <a href="./entries/{article['filename']}" class="article-title">{article['title']}</a>
                    <div class="article-meta">
                        <div class="meta-item">📅 {article['date']}</div>
                        {author_meta}
                    </div>
                </div>
            </div>
            '''

        template = load_template('index.html')
        
        html_content = template.format(
            total_count=len(article_data),
            articles_html=articles_html
        )
        
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info("Index generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating index: {e}")
        raise

def main():
    try:
        logger.info("Starting extraction process...")
        
        url = load_payload()
        if url:
            logger.info(f"Processing URL: {url}")
            try:
                article = extract_article(url)
                if article and article["title"]:
                    save_article_html(article, url)
                    logger.info("Article saved successfully")
                else:
                    logger.error("Failed to extract article or article has no title")
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
        else:
            logger.info("No URL to process, regenerating index and RSS")
        
        try:
            generate_index()
            logger.info("Index generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate index: {e}")
        
        try:
            generate_rss()
            logger.info("RSS generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate RSS: {e}")
        
        logger.info("Process completed")
        
    except Exception as e:
        logger.error(f"Fatal error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
