import re
from typing import Dict, Any
import httpx
from bs4 import BeautifulSoup
from app.utils.logger import logger


def scrape_website_content(url: str, timeout_seconds: float = 12.0) -> Dict[str, Any]:
    """
    Scrapes public website content, strips noisy boilerplate (nav, scripts, styles),
    and returns clean, structured text for RAG indexing.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=timeout_seconds) as client:
            resp = client.get(clean_url, headers=headers)
            resp.raise_for_status()
            html_content = resp.text

    except httpx.HTTPStatusError as e:
        logger.warning(f"⚠️ Web scraper HTTP status error for {clean_url}: {e}")
        raise ValueError(f"Website returned HTTP status {e.response.status_code}. Scraping blocked or page not found.")
    except Exception as e:
        logger.warning(f"⚠️ Web scraper connection failed for {clean_url}: {e}")
        raise ValueError(f"Unable to connect to website: {str(e)}")

    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title = soup.title.string.strip() if (soup.title and soup.title.string) else clean_url

    # Strip clutter tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe", "button"]):
        tag.decompose()

    # Extract clean text from main or body
    main_section = soup.find("main") or soup.find("article") or soup.body
    if main_section:
        raw_text = main_section.get_text(separator="\n")
    else:
        raw_text = soup.get_text(separator="\n")

    # Clean redundant whitespaces
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    # Collapse multiple consecutive blank lines
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

    if len(clean_text) < 50:
        raise ValueError("The website content is too short or protected by JavaScript/anti-bot security.")

    logger.info(f"🌐 Successfully scraped '{title}' ({clean_url}) - {len(clean_text)} characters extracted.")
    return {
        "title": title,
        "content": clean_text,
        "url": clean_url,
        "char_count": len(clean_text)
    }
