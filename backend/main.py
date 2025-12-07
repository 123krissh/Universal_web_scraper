import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup

# Import from modular scraper package
from backend.scraper.static_fetch import static_scrape
from backend.scraper.playwright_scraper import (
    js_scrape_with_playwright,
    js_scrape_hard,
    js_scrape_full,
)
from backend.scraper.parsers.sections import parse_sections_from_soup
from backend.scraper.utils import make_absolute_url

LOG = logging.getLogger("uvicorn.error")

app = FastAPI(title="Lyftr Scraper (backend)")


# -----------------------
# Helpers
# -----------------------
def error_obj(message: str, phase: str):
    return {"message": message, "phase": phase}


# -----------------------
# Health
# -----------------------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# -----------------------
# Scrape endpoint
# -----------------------
@app.post("/scrape")
def scrape_endpoint(body: Dict[str, Any]):
    """
    POST /scrape
    body: { "url": "https://example.com" }
    """
    url = body.get("url") if isinstance(body, dict) else None
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' field")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Only HTTP/HTTPS URLs are supported",
                "errors": [error_obj("Unsupported URL scheme", "validation")],
            },
        )

    result = {
        "url": url,
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "meta": {"title": "", "description": "", "language": "", "canonical": None},
        "sections": [],
        "interactions": {"clicks": [], "scrolls": 0, "pages": [url]},
        "errors": [],
    }

    # -----------------------
    # 1) STATIC SCRAPE
    # -----------------------
    text = ""
    try:
        text, status_code, headers = static_scrape(url)
    except Exception as e:
        LOG.exception("static_scrape failed")
        result["errors"].append(error_obj(f"Static fetch failed: {str(e)}", "fetch"))
        text = ""

    if not text:
        result["errors"].append(error_obj("Static fetch returned empty body", "fetch"))

    # -----------------------
    # 2) PARSE STATIC HTML
    # -----------------------
    try:
        soup = BeautifulSoup(text or "<html></html>", "lxml")

        title_tag = soup.find("title")
        og_title = soup.find("meta", property="og:title")
        meta_title = (og_title and og_title.get("content")) or (title_tag.text if title_tag else "")

        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        description = desc_tag.get("content", "") if desc_tag else ""

        lang = ""
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = html_tag.get("lang")

        canonical = None
        can_tag = soup.find("link", rel="canonical")
        if can_tag and can_tag.get("href"):
            canonical = make_absolute_url(url, can_tag.get("href"))

        result["meta"].update({
            "title": meta_title,
            "description": description,
            "language": lang or "",
            "canonical": canonical
        })

        # Extract sections
        try:
            sections = parse_sections_from_soup(soup, source_url=url)
            result["sections"].extend(sections)
        except Exception as e:
            LOG.exception("parse_sections_from_soup failed")
            result["errors"].append(error_obj(f"Section parsing failed: {str(e)}", "parse"))

    except Exception as e:
        LOG.exception("HTML parse error")
        result["errors"].append(error_obj(f"HTML parse error: {str(e)}", "parse"))

    # -----------------------
    # 3) JS SCRAPE FALLBACK (normal -> full -> hard)
    # -----------------------
    total_text_len = sum(len(s.get("content", {}).get("text", "")) for s in result["sections"])

    if total_text_len < 300 or len(result["sections"]) == 0:
        js_result = None
        try:
            # Try lightweight JS render first
            js_result = js_scrape_with_playwright(url, max_scrolls=3)

            # If this returned no useful content, or errors indicate blocking,
            # escalate to the full JS engine which performs clicks/scrolls/pagination
            blocked_or_insufficient = False

            # check for blocking keywords
            if js_result.get("errors"):
                for e in js_result.get("errors", []):
                    msg = e.get("message", "").lower()
                    if "403" in msg or "blocked" in msg or "access denied" in msg:
                        blocked_or_insufficient = True
                        break

            # check content length
            js_text_len = sum(len(s.get("content", {}).get("text", "")) for s in js_result.get("sections", []))
            if js_text_len < 300 or len(js_result.get("sections", [])) == 0:
                blocked_or_insufficient = True

            if blocked_or_insufficient:
                LOG.info("Escalating to full JS scrape (clicks+scroll+pagination, depth=3)")
                # full mode: scrolls=5, clicks=5, pagination_depth=3, headless=False to mimic real user
                js_result = js_scrape_full(url, scrolls=5, clicks=5, pagination_depth=3, headless=False)

                # If still blocked or empty, try hard mode as last resort
                js_text_len = sum(len(s.get("content", {}).get("text", "")) for s in js_result.get("sections", []))
                if js_text_len < 300 or js_result.get("errors"):
                    LOG.info("Full JS scrape not sufficient or reported errors; attempting hard-scrape fallback")
                    js_result = js_scrape_hard(url, max_scrolls=8, headless=False)

        except Exception as e:
            LOG.exception("Playwright run failed")
            js_result = {
                "sections": [],
                "meta": {},
                "interactions": {"clicks": [], "scrolls": 0, "pages": []},
                "errors": [{"phase": "render", "message": str(e)}],
            }

        # Merge JS results
        try:
            if js_result:
                # Merge meta: prefer existing static meta, fill missing fields from JS
                for k, v in js_result.get("meta", {}).items():
                    if v and not result["meta"].get(k):
                        result["meta"][k] = v

                # Merge sections: avoid duplicates by short rawHtml snippet
                existing_raw = { (s.get("rawHtml") or "")[:200] for s in result["sections"] }
                for sec in js_result.get("sections", []):
                    raw_snip = (sec.get("rawHtml") or "")[:200]
                    if raw_snip not in existing_raw:
                        result["sections"].append(sec)
                        existing_raw.add(raw_snip)

                # Merge interactions
                result["interactions"]["clicks"].extend(js_result.get("interactions", {}).get("clicks", []))
                result["interactions"]["scrolls"] += js_result.get("interactions", {}).get("scrolls", 0)

                for p in js_result.get("interactions", {}).get("pages", []):
                    if p not in result["interactions"]["pages"]:
                        result["interactions"]["pages"].append(p)

                # Merge errors
                for e in js_result.get("errors", []):
                    result["errors"].append(e)

        except Exception as e:
            LOG.exception("Merging js_result failed")
            result["errors"].append(error_obj(f"Merging JS result failed: {str(e)}", "render"))

    # -----------------------
    # 4) ENSURE MINIMUM OUTPUT
    # -----------------------
    if not result["sections"]:
        result["sections"].append({
            "id": "page-0",
            "type": "unknown",
            "label": "Page content",
            "sourceUrl": url,
            "content": {"headings": [], "text": "", "links": [], "images": [], "lists": [], "tables": []},
            "rawHtml": "",
            "truncated": True,
        })
        result["errors"].append(error_obj("No readable content found in static or JS mode", "fallback"))

    return JSONResponse(status_code=200, content={"result": result})


# -----------------------
# Serve frontend build
# -----------------------
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/", response_class=JSONResponse)
    def root_info():
        return {"message": "Frontend not built. Run: npm run build", "api": "/scrape"}



# import json
# import logging
# import os
# from datetime import datetime, timezone
# from typing import Any, Dict
# from urllib.parse import urlparse

# from fastapi import FastAPI, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.staticfiles import StaticFiles
# from bs4 import BeautifulSoup

# # Import from modular scraper package
# from backend.scraper.static_fetch import static_scrape
# from backend.scraper.playwright_scraper import js_scrape_with_playwright, js_scrape_hard
# from backend.scraper.parsers.sections import parse_sections_from_soup
# from backend.scraper.utils import make_absolute_url

# LOG = logging.getLogger("uvicorn.error")

# app = FastAPI(title="Lyftr Scraper (backend)")


# # -----------------------
# # Helpers
# # -----------------------
# def error_obj(message: str, phase: str):
#     return {"message": message, "phase": phase}


# # -----------------------
# # Health
# # -----------------------
# @app.get("/healthz")
# def healthz():
#     return {"status": "ok"}


# # -----------------------
# # Scrape endpoint
# # -----------------------
# @app.post("/scrape")
# def scrape_endpoint(body: Dict[str, Any]):
#     """
#     POST /scrape
#     body: { "url": "https://example.com" }
#     """
#     url = body.get("url") if isinstance(body, dict) else None
#     if not url:
#         raise HTTPException(status_code=400, detail="Missing 'url' field")

#     parsed = urlparse(url)
#     if parsed.scheme not in ("http", "https"):
#         return JSONResponse(
#             status_code=400,
#             content={
#                 "success": False,
#                 "error": "Only HTTP/HTTPS URLs are supported",
#                 "errors": [error_obj("Unsupported URL scheme", "validation")],
#             },
#         )

#     result = {
#         "url": url,
#         "scrapedAt": datetime.now(timezone.utc).isoformat(),
#         "meta": {"title": "", "description": "", "language": "", "canonical": None},
#         "sections": [],
#         "interactions": {"clicks": [], "scrolls": 0, "pages": [url]},
#         "errors": [],
#     }

#     # -----------------------
#     # 1) STATIC SCRAPE
#     # -----------------------
#     text = ""
#     try:
#         text, status_code, headers = static_scrape(url)
#     except Exception as e:
#         LOG.exception("static_scrape failed")
#         result["errors"].append(error_obj(f"Static fetch failed: {str(e)}", "fetch"))
#         text = ""

#     if not text:
#         result["errors"].append(error_obj("Static fetch returned empty body", "fetch"))

#     # -----------------------
#     # 2) PARSE STATIC HTML
#     # -----------------------
#     try:
#         soup = BeautifulSoup(text or "<html></html>", "lxml")

#         title_tag = soup.find("title")
#         og_title = soup.find("meta", property="og:title")
#         meta_title = (og_title and og_title.get("content")) or (title_tag.text if title_tag else "")

#         desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
#         description = desc_tag.get("content", "") if desc_tag else ""

#         lang = ""
#         html_tag = soup.find("html")
#         if html_tag and html_tag.get("lang"):
#             lang = html_tag.get("lang")

#         canonical = None
#         can_tag = soup.find("link", rel="canonical")
#         if can_tag and can_tag.get("href"):
#             canonical = make_absolute_url(url, can_tag.get("href"))

#         result["meta"].update({
#             "title": meta_title,
#             "description": description,
#             "language": lang or "",
#             "canonical": canonical
#         })

#         # Extract sections
#         try:
#             sections = parse_sections_from_soup(soup, source_url=url)
#             result["sections"].extend(sections)
#         except Exception as e:
#             LOG.exception("parse_sections_from_soup failed")
#             result["errors"].append(error_obj(f"Section parsing failed: {str(e)}", "parse"))

#     except Exception as e:
#         LOG.exception("HTML parse error")
#         result["errors"].append(error_obj(f"HTML parse error: {str(e)}", "parse"))

#     # -----------------------
#     # 3) JS SCRAPE FALLBACK
#     # -----------------------
#     total_text_len = sum(len(s.get("content", {}).get("text", "")) for s in result["sections"])

#     if total_text_len < 300 or len(result["sections"]) == 0:
#         try:
#             js_result = js_scrape_with_playwright(url, max_scrolls=3)

#             # If blocked → use HARD MODE
#             if js_result.get("errors") and any(
#                 "403" in e.get("message", "") or "blocked" in e.get("message", "").lower()
#                 for e in js_result.get("errors", [])
#             ):
#                 LOG.info("Site blocking detected. Using hard-scrape mode")
#                 js_result = js_scrape_hard(url, max_scrolls=8, headless=False)

#         except Exception as e:
#             LOG.exception("Playwright normal flow failed")
#             js_result = {
#                 "sections": [],
#                 "meta": {},
#                 "interactions": {"clicks": [], "scrolls": 0, "pages": []},
#                 "errors": [{"phase": "render", "message": str(e)}],
#             }

#         # Merge JS results
#         try:
#             # Merge meta
#             for k, v in js_result.get("meta", {}).items():
#                 if v and not result["meta"].get(k):
#                     result["meta"][k] = v

#             # Merge sections (avoid duplicates)
#             existing_raw = {s.get("rawHtml")[:200] for s in result["sections"]}
#             for sec in js_result.get("sections", []):
#                 if sec.get("rawHtml", "")[:200] not in existing_raw:
#                     result["sections"].append(sec)

#             # Merge interactions
#             result["interactions"]["clicks"].extend(js_result["interactions"].get("clicks", []))
#             result["interactions"]["scrolls"] += js_result["interactions"].get("scrolls", 0)

#             for p in js_result["interactions"].get("pages", []):
#                 if p not in result["interactions"]["pages"]:
#                     result["interactions"]["pages"].append(p)

#             result["errors"].extend(js_result.get("errors", []))

#         except Exception as e:
#             LOG.exception("Merging js_result failed")
#             result["errors"].append(error_obj(f"Merging JS result failed: {str(e)}", "render"))

#     # -----------------------
#     # 4) ENSURE MINIMUM OUTPUT
#     # -----------------------
#     if not result["sections"]:
#         result["sections"].append({
#             "id": "page-0",
#             "type": "unknown",
#             "label": "Page content",
#             "sourceUrl": url,
#             "content": {"headings": [], "text": "", "links": [], "images": [], "lists": [], "tables": []},
#             "rawHtml": "",
#             "truncated": True,
#         })
#         result["errors"].append(error_obj("No readable content found in static or JS mode", "fallback"))

#     return JSONResponse(status_code=200, content={"result": result})


# # -----------------------
# # Serve frontend build
# # -----------------------
# frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

# if os.path.isdir(frontend_dist):
#     app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
# else:
#     @app.get("/", response_class=JSONResponse)
#     def root_info():
#         return {"message": "Frontend not built. Run: npm run build", "api": "/scrape"}

