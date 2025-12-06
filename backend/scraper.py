# backend/scraper.py
import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

# -------------------------
# Utilities
# -------------------------
def make_absolute_url(base: str, href: Optional[str]) -> str:
    if not href:
        return ""
    try:
        return urljoin(base, href)
    except Exception:
        return href or ""


def _safe_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


# -------------------------
# Static fetch
# -------------------------
def static_scrape(url: str, timeout: int = 12) -> Tuple[str, int, Dict[str, Any]]:
    default_headers = {"User-Agent": "Lyftr-Assignment-Bot/1.0 (+https://example.com)"}
    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://google.com/",
    }

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        try:
            r = client.get(url, headers=default_headers)
            if r.status_code == 403:
                LOG.debug("static_scrape: 403, retrying with browser headers")
                r2 = client.get(url, headers=browser_headers)
                r2.raise_for_status()
                return r2.text, r2.status_code, dict(r2.headers)
            r.raise_for_status()
            return r.text, r.status_code, dict(r.headers)
        except Exception:
            LOG.exception("static_scrape failed")
            raise


# -------------------------
# Parsing helpers
# -------------------------
def _extract_links(node: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    links = []
    for a in node.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        href_abs = make_absolute_url(base_url, href)
        text = (a.get_text(" ", strip=True) or "").strip()
        links.append({"text": text, "href": href_abs})
    return links


def _extract_images(node: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    imgs = []
    for img in node.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        if not src:
            # try CSS background in style attribute
            style = img.get("style") or ""
            m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
            if m:
                src = m.group(1)
        if not src:
            continue
        src_abs = make_absolute_url(base_url, src)
        alt = img.get("alt") or ""
        imgs.append({"src": src_abs, "alt": alt})
    return imgs


def _extract_lists(node: BeautifulSoup) -> List[List[str]]:
    lists = []
    for ul in node.find_all(["ul", "ol"]):
        items = [li.get_text(" ", strip=True) for li in ul.find_all("li")]
        if items:
            lists.append(items)
    return lists


def _truncate_html(html: str, limit: int = 2000):
    truncated = len(html) > limit
    return html[:limit], truncated


def _generate_label_from_text(text: str, words: int = 6):
    tokens = re.split(r"\s+", (text or "").strip())
    if not tokens:
        return "Section"
    return " ".join(tokens[:words])


# -------------------------
# Main parser
# -------------------------
def parse_sections_from_soup(soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    landmark_tags = ["header", "nav", "main", "section", "article", "footer"]
    used_html = set()
    idx = 0

    for tag in landmark_tags:
        for el in soup.find_all(tag):
            raw_html = str(el)
            if not raw_html or raw_html in used_html:
                continue
            used_html.add(raw_html)
            headings = [h.get_text(" ", strip=True) for h in el.find_all(["h1", "h2", "h3"])][:5]
            text = el.get_text(" ", strip=True) or ""
            if not text:
                continue
            links = _extract_links(el, source_url)
            images = _extract_images(el, source_url)
            lists = _extract_lists(el)
            raw_snip, truncated = _truncate_html(raw_html)
            label = headings[0] if headings else _generate_label_from_text(text)
            sec_type = "unknown"
            if tag == "nav":
                sec_type = "nav"
            elif tag == "header" and idx == 0:
                sec_type = "hero"
            elif tag == "footer":
                sec_type = "footer"
            elif tag == "main":
                sec_type = "section"

            sections.append({
                "id": f"{tag}-{idx}",
                "type": sec_type,
                "label": label,
                "sourceUrl": source_url,
                "content": {
                    "headings": headings,
                    "text": text,
                    "links": links,
                    "images": images,
                    "lists": lists,
                    "tables": [],  # placeholder
                },
                "rawHtml": raw_snip,
                "truncated": truncated,
            })
            idx += 1

    # Heading-based fallback
    if not sections:
        for h in soup.find_all(["h1", "h2", "h3"]):
            parent = h.find_parent()
            if not parent:
                continue
            raw_html = str(parent)
            if raw_html in used_html:
                continue
            used_html.add(raw_html)
            headings = [h.get_text(" ", strip=True)]
            text = parent.get_text(" ", strip=True) or ""
            if not text:
                continue
            links = _extract_links(parent, source_url)
            images = _extract_images(parent, source_url)
            lists = _extract_lists(parent)
            raw_snip, truncated = _truncate_html(raw_html)
            label = headings[0] if headings else _generate_label_from_text(text)
            sections.append({
                "id": f"heading-{len(sections)}",
                "type": "section",
                "label": label,
                "sourceUrl": source_url,
                "content": {
                    "headings": headings,
                    "text": text,
                    "links": links,
                    "images": images,
                    "lists": lists,
                    "tables": [],
                },
                "rawHtml": raw_snip,
                "truncated": truncated,
            })

    # Final fallback whole body
    if not sections:
        body = soup.body or soup
        text = body.get_text(" ", strip=True) or ""
        raw_snip, truncated = _truncate_html(str(body))
        if text:
            sections.append({
                "id": "body-0",
                "type": "unknown",
                "label": _generate_label_from_text(text),
                "sourceUrl": source_url,
                "content": {"headings": [], "text": text, "links": [], "images": [], "lists": [], "tables": []},
                "rawHtml": raw_snip,
                "truncated": truncated,
            })

    return sections


# -------------------------
# Playwright flows
# -------------------------
def _apply_stealth(page) -> None:
    try:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = window.chrome || { runtime: {} };
        """)
    except Exception:
        pass


def js_scrape_with_playwright(url: str, max_scrolls: int = 3, click_selectors: Optional[List[str]] = None,
                              headless: bool = True, navigation_timeout: int = 30000) -> Dict[str, Any]:
    result: Dict[str, Any] = {"sections": [], "meta": {}, "interactions": {"clicks": [], "scrolls": 0, "pages": []}, "errors": []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            context = browser.new_context(user_agent=user_agent, viewport={"width":1366,"height":800}, locale="en-US")
            page = context.new_page()
            page.set_default_navigation_timeout(navigation_timeout)
            _apply_stealth(page)
            try:
                page.goto(url, wait_until="networkidle")
            except Exception:
                try:
                    page.goto(url, wait_until="load")
                except Exception as e:
                    result["errors"].append({"message": f"Navigation failed: {str(e)}", "phase": "render"})
            # Try clicks
            selectors = click_selectors or ["[role='tab']", "button:has-text('Load more')", "button:has-text('Show more')"]
            for sel in selectors:
                try:
                    els = page.query_selector_all(sel)
                    for el in els[:3]:
                        try:
                            el.click(timeout=2000)
                            result["interactions"]["clicks"].append(sel)
                            time.sleep(0.3)
                        except Exception:
                            pass
                except Exception:
                    pass
            # Overlays
            overlay_selectors = ["button[aria-label*='close']", ".cookie-banner button", ".cookie-consent button", ".modal button.close", ".popup-close"]
            for sel in overlay_selectors:
                try:
                    els = page.query_selector_all(sel)
                    for el in els:
                        try:
                            el.click(timeout=1500)
                            result["interactions"]["clicks"].append(sel)
                        except Exception:
                            pass
                except Exception:
                    pass
            # Scrolling
            for i in range(max_scrolls):
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.0)
                    result["interactions"]["scrolls"] += 1
                except Exception:
                    break
            # Pagination follow
            pages_visited = [url]
            try:
                for _ in range(2):
                    next_link = page.query_selector("a[rel='next'], a:has-text('Next'), a:has-text('next')")
                    if next_link:
                        href = next_link.get_attribute("href")
                        if href:
                            next_url = make_absolute_url(url, href)
                            if next_url not in pages_visited:
                                try:
                                    page.goto(next_url, wait_until="networkidle")
                                    pages_visited.append(next_url)
                                    result["interactions"]["pages"].append(next_url)
                                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                    time.sleep(1.0)
                                except Exception:
                                    break
                    else:
                        break
            except Exception:
                pass
            # Extract html
            try:
                html = page.content()
                soup = _safe_soup(html)
                title_tag = soup.find("title")
                og_title = soup.find("meta", property="og:title")
                meta_title = (og_title and og_title.get("content")) or (title_tag and title_tag.text) or ""
                desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
                description = desc_tag.get("content", "") if desc_tag else ""
                can_tag = soup.find("link", rel="canonical")
                canonical = make_absolute_url(url, can_tag.get("href")) if can_tag and can_tag.get("href") else None
                lang = (soup.find("html") and soup.find("html").get("lang")) or ""
                result["meta"] = {"title": meta_title, "description": description, "language": lang or "", "canonical": canonical}
                result["sections"] = parse_sections_from_soup(soup, source_url=url)
                if not result["interactions"]["pages"]:
                    result["interactions"]["pages"] = pages_visited
                else:
                    if url not in result["interactions"]["pages"]:
                        result["interactions"]["pages"].insert(0, url)
            finally:
                try:
                    context.close()
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass
    except PlaywrightTimeoutError as te:
        LOG.exception("Playwright timeout")
        result["errors"].append({"message": f"Playwright timeout: {str(te)}", "phase": "render"})
    except Exception as e:
        LOG.exception("Playwright error")
        result["errors"].append({"message": f"Playwright error: {str(e)}", "phase": "render"})

    return result


def js_scrape_hard(url: str, max_scrolls: int = 10, headless: bool = True, navigation_timeout: int = 45000) -> Dict[str, Any]:
    result = {"sections": [], "meta": {}, "interactions": {"clicks": [], "scrolls": 0, "pages": []}, "errors": []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage", "--disable-infobars"])
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            context = browser.new_context(user_agent=user_agent, viewport={"width":1366,"height":768}, locale="en-US")
            page = context.new_page()
            page.set_default_navigation_timeout(navigation_timeout)
            _apply_stealth(page)
            try:
                page.goto(url, wait_until="networkidle")
            except Exception:
                try:
                    page.goto(url, wait_until="load")
                except Exception as e:
                    result["errors"].append({"message": f"Navigation failed: {str(e)}", "phase": "render"})
            # slow human-like scroll
            for i in range(max_scrolls):
                try:
                    page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 0.8))")
                    time.sleep(0.6 + (i % 3) * 0.2)
                    result["interactions"]["scrolls"] += 1
                except Exception:
                    break
            # collect html
            try:
                html = page.content()
                soup = _safe_soup(html)
                title_tag = soup.find("title")
                og_title = soup.find("meta", property="og:title")
                meta_title = (og_title and og_title.get("content")) or (title_tag and title_tag.text) or ""
                desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
                description = desc_tag.get("content", "") if desc_tag else ""
                can_tag = soup.find("link", rel="canonical")
                canonical = make_absolute_url(url, can_tag.get("href")) if can_tag and can_tag.get("href") else None
                lang = (soup.find("html") and soup.find("html").get("lang")) or ""
                result["meta"] = {"title": meta_title, "description": description, "language": lang or "", "canonical": canonical}
                result["sections"] = parse_sections_from_soup(soup, source_url=url)
                result["interactions"]["pages"] = [url]
            finally:
                try:
                    context.close()
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass
    except Exception as e:
        LOG.exception("js_scrape_hard failed")
        result["errors"].append({"message": f"Playwright hard-scrape error: {str(e)}", "phase": "render"})
    return result

