import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def _scrape_with_newspaper(url: str) -> dict:
    article = Article(url)
    article.config.browser_user_agent = HEADERS["User-Agent"]
    article.config.request_timeout = 15
    article.download()
    article.parse()
    text = _clean_text(article.text)
    title = article.title or ""
    authors = article.authors or []
    publish_date = str(article.publish_date) if article.publish_date else ""
    return {
        "title": title,
        "text": text,
        "authors": authors,
        "publish_date": publish_date
    }

def _scrape_with_beautifulsoup(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    paragraphs = soup.find_all("p")
    text = " ".join([p.get_text() for p in paragraphs])
    text = _clean_text(text)
    title = soup.title.string if soup.title else ""
    title = _clean_text(title)
    return {
        "title": title,
        "text": text,
        "authors": [],
        "publish_date": ""
    }

def scrape_article(url: str) -> dict:
    if not url or not url.startswith("http"):
        return {
            "title": None,
            "text": None,
            "authors": None,
            "publish_date": None,
            "url": url,
            "word_count": 0,
            "error": "Invalid URL. Please make sure the URL starts with http or https."
        }

    result = None

    if NEWSPAPER_AVAILABLE:
        try:
            result = _scrape_with_newspaper(url)
        except Exception as e:
            result = None

    if not result or not result["text"] or len(result["text"]) < 100:
        try:
            result = _scrape_with_beautifulsoup(url)
        except requests.exceptions.Timeout:
            return {
                "title": None,
                "text": None,
                "authors": None,
                "publish_date": None,
                "url": url,
                "word_count": 0,
                "error": "Request timed out after 15 seconds. The site may be slow or blocking scrapers."
            }
        except requests.exceptions.HTTPError as e:
            return {
                "title": None,
                "text": None,
                "authors": None,
                "publish_date": None,
                "url": url,
                "word_count": 0,
                "error": f"HTTP error: {str(e)}. This site may be paywalled or blocked."
            }
        except Exception as e:
            return {
                "title": None,
                "text": None,
                "authors": None,
                "publish_date": None,
                "url": url,
                "word_count": 0,
                "error": f"Scraping failed: {str(e)}"
            }

    if not result["text"] or len(result["text"]) < 100:
        return {
            "title": None,
            "text": None,
            "authors": None,
            "publish_date": None,
            "url": url,
            "word_count": 0,
            "error": "Could not extract article text. This site may be paywalled or JavaScript-rendered."
        }

    word_count = len(result["text"].split())

    return {
        "title": result["title"],
        "text": result["text"],
        "authors": result["authors"],
        "publish_date": result["publish_date"],
        "url": url,
        "word_count": word_count,
        "error": None
    }


if __name__ == "__main__":
    test_url = "https://www.bbc.com/news/world"
    print(f"Testing scraper with URL: {test_url}")
    print("-" * 50)

    result = scrape_article(test_url)

    if result["error"]:
        print(f"ERROR: {result['error']}")
    else:
        print(f"Title: {result['title']}")
        print(f"Text (first 200 chars): {result['text'][:200]}")
        print(f"Word Count: {result['word_count']}")
        print(f"Authors: {result['authors']}")
        print(f"Publish Date: {result['publish_date']}")
        print("-" * 50)
        print("SCRAPER WORKING CORRECTLY")