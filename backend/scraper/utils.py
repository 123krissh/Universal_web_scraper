import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


def make_absolute_url(base: str, href: str) -> str:
    if not href:
        return ""
    try:
        return urljoin(base, href)
    except Exception:
        return href or ""


def safe_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def truncate_html(html: str, limit: int = 2000):
    truncated = len(html) > limit
    return html[:limit], truncated


def generate_label_from_text(text: str, words: int = 6):
    tokens = re.split(r"\s+", (text or "").strip())
    if not tokens:
        return "Section"
    return " ".join(tokens[:words])
