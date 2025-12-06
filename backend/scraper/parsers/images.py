import re
from typing import List, Dict
from bs4 import BeautifulSoup
from backend.scraper.utils import make_absolute_url


def extract_images(node: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    imgs = []

    for img in node.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""

        # CSS background-image fallback
        if not src:
            m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', img.get("style", ""))
            if m:
                src = m.group(1)

        if not src:
            continue

        imgs.append({
            "src": make_absolute_url(base_url, src),
            "alt": img.get("alt") or ""
        })

    return imgs
