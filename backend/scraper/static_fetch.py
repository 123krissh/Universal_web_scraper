import httpx
import logging

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


def static_scrape(url: str, timeout: int = 12):
    default_headers = {"User-Agent": "Lyftr-Assignment-Bot/1.0"}
    browser_headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36")
    }

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        try:
            r = client.get(url, headers=default_headers)
            if r.status_code == 403:
                LOG.debug("Retrying with browser headers")
                r2 = client.get(url, headers=browser_headers)
                r2.raise_for_status()
                return r2.text, r2.status_code, dict(r2.headers)

            r.raise_for_status()
            return r.text, r.status_code, dict(r.headers)

        except Exception:
            LOG.exception("static_scrape failed")
            raise
