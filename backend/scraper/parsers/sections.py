from typing import List, Dict, Any
from bs4 import BeautifulSoup

from backend.scraper.parsers.links import extract_links
from backend.scraper.parsers.images import extract_images
from backend.scraper.parsers.lists import extract_lists
from backend.scraper.utils import truncate_html, generate_label_from_text


def parse_sections_from_soup(soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
    sections = []
    used_html = set()
    idx = 0

    landmark_tags = ["header", "nav", "main", "section", "article", "footer"]

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

            links = extract_links(el, source_url)
            images = extract_images(el, source_url)
            lists = extract_lists(el)

            raw_snip, truncated = truncate_html(raw_html)
            label = headings[0] if headings else generate_label_from_text(text)

            sec_type = "unknown"
            if tag == "nav": sec_type = "nav"
            if tag == "header" and idx == 0: sec_type = "hero"
            if tag == "footer": sec_type = "footer"
            if tag == "main": sec_type = "section"

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
                    "tables": []
                },
                "rawHtml": raw_snip,
                "truncated": truncated,
            })
            idx += 1

    # Fallbacks
    if not sections:
        body = soup.body or soup
        text = body.get_text(" ", strip=True) or ""
        raw_snip, truncated = truncate_html(str(body))
        if text:
            sections.append({
                "id": "body-0",
                "type": "unknown",
                "label": generate_label_from_text(text),
                "sourceUrl": source_url,
                "content": {"headings": [], "text": text, "links": [], "images": [], "lists": [], "tables": []},
                "rawHtml": raw_snip,
                "truncated": truncated,
            })

    return sections
