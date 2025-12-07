import time
import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

from backend.scraper.utils import make_absolute_url, safe_soup
from backend.scraper.parsers.sections import parse_sections_from_soup

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


# -------------------------------------------------
# Stealth Mode
# -------------------------------------------------
def _apply_stealth(page):
    try:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            window.chrome = window.chrome || { runtime: {} };
        """)
    except Exception:
        pass


# -------------------------------------------------
# Scroll Helper
# -------------------------------------------------
def smart_scroll(page, max_scrolls: int, result: Dict[str, Any]):
    last_height = 0
    for _ in range(max_scrolls):
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            result["interactions"]["scrolls"] += 1

            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        except Exception:
            break


# -------------------------------------------------
# Click Helper
# -------------------------------------------------
def auto_click_elements(page, result: Dict[str, Any], max_clicks=5):
    CLICK_SELECTORS = [
        "button", "a[href]", "[role='button']", "[onclick]",
        ".load-more", ".next", ".btn", ".show-more"
    ]

    clickable = []
    for sel in CLICK_SELECTORS:
        try:
            clickable.extend(page.query_selector_all(sel))
        except Exception:
            continue

    clicked = 0
    for el in clickable:
        if clicked >= max_clicks:
            break
        try:
            box = el.bounding_box()
            if not box:
                continue

            text = (el.inner_text() or "").strip()
            href = el.get_attribute("href") or ""

            el.click()
            time.sleep(1.2)

            result["interactions"]["clicks"].append(text or href)
            clicked += 1
        except Exception:
            continue


# -------------------------------------------------
# Pagination Helper
# -------------------------------------------------
def detect_and_click_pagination(page, visited_pages: set, result: Dict[str, Any]) -> Optional[str]:
    """
    Improved pagination detection:
    - Handles HN-style 'More' link (a.morelink)
    - Tries to click and wait for navigation; if click doesn't navigate, falls back to href + page.goto()
    - Returns the absolute next-page URL or None if none found / already visited
    """
    PAGINATION_SELECTORS = [
        "a.morelink",        
        "a[rel='next']",
        "a.next",
        "button.next",
        ".pagination-next",
        ".pager-next"
    ]

    for sel in PAGINATION_SELECTORS:
        try:
            btn = page.query_selector(sel)
            if not btn:
                continue

            # Prefer the href if available (HN uses relative hrefs)
            href = btn.get_attribute("href")
            absolute = make_absolute_url(page.url, href) if href else page.url

            # already visited?
            if absolute in visited_pages:
                return None

            # Try clicking and wait for navigation; if navigation doesn't happen, fallback to goto(href)
            try:
                # record current url to detect navigation
                before = page.url
                btn.click()
                # wait for either networkidle or url change
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    # load_state wait may timeout for very fast responses; ignore
                    pass

                after = page.url
                if after and after != before:
                    # click caused navigation; use the new url
                    result["interactions"]["pages"].append(after)
                    return after
                else:
                    # Click didn't change URL; try explicit goto if href exists
                    if href:
                        page.goto(absolute, wait_until="networkidle", timeout=10000)
                        result["interactions"]["pages"].append(absolute)
                        return absolute
                    else:
                        # no href, no navigation — skip this selector
                        continue

            except Exception:
                # fallback: try direct goto if href exists
                if href:
                    try:
                        page.goto(absolute, wait_until="networkidle", timeout=10000)
                        result["interactions"]["pages"].append(absolute)
                        return absolute
                    except Exception:
                        continue
                else:
                    continue

        except Exception:
            continue

    return None


# -------------------------------------------------
# Extract META
# -------------------------------------------------
def extract_meta(soup, url):
    title = soup.find("title")
    meta_title = title.text.strip() if title else ""

    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    can = soup.find("link", rel="canonical")
    canonical = make_absolute_url(url, can.get("href")) if can else None

    lang = soup.html.get("lang") if soup.html and soup.html.get("lang") else ""

    return {
        "title": meta_title,
        "description": description,
        "canonical": canonical,
        "language": lang
    }


# -------------------------------------------------
# SIMPLE JS SCRAPER
# -------------------------------------------------
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
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125 Safari/537.36",
                viewport={"width": 1366, "height": 800},
                locale="en-US"
            )
            page = context.new_page()
            _apply_stealth(page)

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                page.goto(url, wait_until="load", timeout=30000)

            smart_scroll(page, max_scrolls, result)

            html = page.content()
            soup = safe_soup(html)

            result["meta"] = extract_meta(soup, url)
            result["sections"] = parse_sections_from_soup(soup, source_url=url)
            result["interactions"]["pages"] = [url]

            context.close()
            browser.close()

    except Exception as e:
        result["errors"].append({"message": str(e), "phase": "render"})

    return result


# -------------------------------------------------
# HARD SCRAPER (Anti-Bot)
# -------------------------------------------------
def js_scrape_hard(url: str, max_scrolls: int = 8, headless: bool = False) -> Dict[str, Any]:
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
                    "--disable-dev-shm-usage"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="en-US"
            )
            page = context.new_page()
            _apply_stealth(page)

            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                page.goto(url, wait_until="load", timeout=45000)

            # Slow human-like scrolling
            for i in range(max_scrolls):
                page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                time.sleep(0.5 + (i % 3) * 0.3)
                result["interactions"]["scrolls"] += 1

            html = page.content()
            soup = safe_soup(html)

            result["meta"] = extract_meta(soup, url)
            result["sections"] = parse_sections_from_soup(soup, source_url=url)
            result["interactions"]["pages"] = [url]

            context.close()
            browser.close()

    except Exception as e:
        result["errors"].append({"message": str(e), "phase": "render"})

    return result


# -------------------------------------------------
# FULL SCRAPER — SCROLL + CLICK + PAGINATION (Depth 3)
# -------------------------------------------------
def js_scrape_full(
    url: str,
    scrolls: int = 3,
    clicks: int = 3,
    pagination_limit: int = 3,
    headless: bool = True
) -> Dict[str, Any]:

    result = {
        "sections": [],
        "meta": {},
        "interactions": {"clicks": [], "scrolls": 0, "pages": []},
        "errors": []
    }

    visited_pages = set()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="en-US"
            )
            page = context.new_page()
            _apply_stealth(page)

            current = url
            depth = 0

            while current and depth < pagination_limit:
                visited_pages.add(current)
                result["interactions"]["pages"].append(current)

                # Open page
                try:
                    page.goto(current, wait_until="networkidle")
                except Exception:
                    page.goto(current, wait_until="load")

                # Scroll + click
                smart_scroll(page, scrolls, result)
                auto_click_elements(page, result, max_clicks=clicks)

                # Extract
                html = page.content()
                soup = safe_soup(html)

                if depth == 0:
                    result["meta"] = extract_meta(soup, current)

                result["sections"].extend(
                    parse_sections_from_soup(soup, source_url=current)
                )

                # Pagination
                next_page = detect_and_click_pagination(page, visited_pages, result)
                if not next_page:
                    break
                current = next_page
                depth += 1

            context.close()
            browser.close()

    except Exception as e:
        result["errors"].append({"message": str(e), "phase": "render"})

    return result