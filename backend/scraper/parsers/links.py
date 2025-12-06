from typing import List, Dict
from bs4 import BeautifulSoup
from backend.scraper.utils import make_absolute_url


def extract_links(node: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    links = []
    for a in node.find_all("a", href=True):
        text = (a.get_text(" ", strip=True) or "").strip()
        href_abs = make_absolute_url(base_url, a.get("href"))
        links.append({"text": text, "href": href_abs})
    return links
