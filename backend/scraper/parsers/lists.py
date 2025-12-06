from typing import List
from bs4 import BeautifulSoup


def extract_lists(node: BeautifulSoup) -> List[List[str]]:
    lists = []
    for ul in node.find_all(["ul", "ol"]):
        items = [li.get_text(" ", strip=True) for li in ul.find_all("li")]
        if items:
            lists.append(items)
    return lists
