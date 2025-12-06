import time
import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from backend.scraper.utils import make_absolute_url, safe_soup
from backend.scraper.parsers.sections import parse_sections_from_soup

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


# ---------------------------------------------------
# Apply Stealth
# ---------------------------------------------------
def _apply_stealth(page):
    try:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = window.chrome || { runtime: {} };
        """)
    except Exception:
        pass


# ---------------------------------------------------
# JS Scraper (Normal)
# ---------------------------------------------------
def js_scrape_with_playwright(url: str, max_scrolls: int = 3) -> Dict[str, Any]:
    result = {
        "sections": [],
        "meta": {},
        "interactions": {"clicks": [], "scrolls": 0, "pages": []},
        "errors": []
    }

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
                viewport={"width": 1366, "height": 800},
                locale="en-US"
            )

            page = context.new_page()
            page.set_default_navigation_timeout(30000)

            _apply_stealth(page)

            try:
                page.goto(url, wait_until="networkidle")
            except Exception:
                try:
                    page.goto(url, wait_until="load")
                except Exception as e:
                    result["errors"].append({"message": f"Navigation failed: {str(e)}", "phase": "render"})

            # Scroll
            for i in range(max_scrolls):
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    result["interactions"]["scrolls"] += 1
                except Exception:
                    break

            # Extract content
            try:
                html = page.content()
                soup = safe_soup(html)

                title_tag = soup.find("title")
                meta_title = title_tag.text if title_tag else ""

                desc_tag = soup.find("meta", attrs={"name": "description"})
                description = desc_tag.get("content", "") if desc_tag else ""

                can_tag = soup.find("link", rel="canonical")
                canonical = make_absolute_url(url, can_tag.get("href")) if can_tag else None

                result["meta"] = {
                    "title": meta_title,
                    "description": description,
                    "language": soup.html.get("lang") if soup.html else "",
                    "canonical": canonical,
                }

                result["sections"] = parse_sections_from_soup(soup, source_url=url)
                result["interactions"]["pages"] = [url]
            finally:
                context.close()
                browser.close()

    except PlaywrightTimeoutError as te:
        result["errors"].append({"message": f"Playwright timeout: {str(te)}", "phase": "render"})

    except Exception as e:
        result["errors"].append({"message": f"Playwright error: {str(e)}", "phase": "render"})

    return result


# ---------------------------------------------------
# JS Scraper (Hard Mode)
# Anti-bot bypass: slower scrolling, human-like behavior
# ---------------------------------------------------
def js_scrape_hard(url: str, max_scrolls: int = 10, headless: bool = True) -> Dict[str, Any]:
    result = {
        "sections": [],
        "meta": {},
        "interactions": {"clicks": [], "scrolls": 0, "pages": []},
        "errors": []
    }

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-infobars"
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="en-US"
            )

            page = context.new_page()
            page.set_default_navigation_timeout(45000)

            _apply_stealth(page)

            try:
                page.goto(url, wait_until="networkidle")
            except Exception:
                try:
                    page.goto(url, wait_until="load")
                except Exception as e:
                    result["errors"].append({"message": f"Navigation failed: {str(e)}", "phase": "render"})

            # Human-like slow scrolling
            for i in range(max_scrolls):
                try:
                    page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 0.8))")
                    time.sleep(0.5 + (i % 3) * 0.3)  # variable delay
                    result["interactions"]["scrolls"] += 1
                except Exception:
                    break

            # Extract content
            try:
                html = page.content()
                soup = safe_soup(html)

                title_tag = soup.find("title")
                meta_title = title_tag.text if title_tag else ""

                desc_tag = soup.find("meta", attrs={"name": "description"})
                description = desc_tag.get("content", "") if desc_tag else ""

                can_tag = soup.find("link", rel="canonical")
                canonical = make_absolute_url(url, can_tag.get("href")) if can_tag else None

                result["meta"] = {
                    "title": meta_title,
                    "description": description,
                    "language": soup.html.get("lang") if soup.html else "",
                    "canonical": canonical,
                }

                result["sections"] = parse_sections_from_soup(soup, source_url=url)
                result["interactions"]["pages"] = [url]
            finally:
                context.close()
                browser.close()

    except Exception as e:
        result["errors"].append({"message": f"Playwright hard-scrape error: {str(e)}", "phase": "render"})

    return result
