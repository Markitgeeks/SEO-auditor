import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import REQUEST_TIMEOUT, USER_AGENT


class FetchResult:
    def __init__(self, url: str, response: requests.Response, soup: BeautifulSoup):
        self.url = url
        self.response = response
        self.soup = soup
        self.elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        self.page_size_kb = len(response.content) / 1024
        parsed = urlparse(url)
        self.scheme = parsed.scheme
        self.domain = parsed.netloc
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"


def fetch_page(url: str) -> FetchResult:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    return FetchResult(url=url, response=resp, soup=soup)
