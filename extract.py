import json
import logging
import hashlib
import urllib.parse
from datetime import datetime
import sys
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from readability import Document

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

def process_images(article_html, article_url):
    """Ensures all image URLs are absolute, but does not download them."""
    try:
        soup = BeautifulSoup(article_html, 'html.parser')
        for img in soup.find_all('img'):
            img_url = img.get('src')
            if img_url:
                img['src'] = urllib.parse.urljoin(article_url, img_url)
        return str(soup)
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        return article_html

def check_duplicate(url):
    metadata = load_metadata()
    url_hash = get_url_hash(url)
    for entry_id, entry_data in metadata.items():
        if entry_data.get('url') == url or entry_data.get('url_hash') == url_hash:
            logger.info(f"Duplicate found: {entry_id}")
            return entry_id
    return None

def save_article_content(article, url):
    try:
        duplicate = check_duplicate(url)
        if duplicate:
            logger.info(f"Article already exists: {duplicate}")
            return duplicate

        article_content = process_images(article["content_html"], url)
        publish_date = article["publish_date"] or datetime.now().isoformat()
        metadata = load_metadata()
        entry_id = f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-{re.sub(r'[^a-zA-Z0-9-]', '', article['title'].lower())[:50]}"
        metadata[entry_id] = {
            'title': article["title"],
            'url': url,
            'url_hash': get_url_hash(url),
            'date': publish_date,
            'authors': article["authors"],
            'content_html': article_content,
            'summary': article["title"]
        }
        save_metadata(metadata)
        logger.info(f"Saved new article: {entry_id}")
        return entry_id

    except Exception as e:
        logger.error(f"Error saving article: {e}")
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
                    save_article_content(article, url)
                    logger.info("Article saved successfully")
                else:
                    logger.error("Failed to extract article or article has no title")
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
        else:
            logger.info("No URL to process")
        logger.info("Process completed")
    except Exception as e:
        logger.error(f"Fatal error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
