import hashlib
from typing import TypedDict

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import Browser, Playwright, async_playwright

from .config import settings

USER_AGENT = settings.USER_AGENT


class ScrapeResult(TypedDict):
    url: str
    title: str
    content: str
    hash: str


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _clean_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    for el in soup(["script", "style", "noscript", "template", "iframe"]):
        el.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    content = soup.get_text(separator=" ", strip=True)
    return title, content


async def scrape_http(url: str) -> ScrapeResult:
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=settings.HTTP_TIMEOUT,
        follow_redirects=True,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        title, content = _clean_html(resp.text)
        return {
            "url": str(resp.url),
            "title": title,
            "content": content,
            "hash": hash_content(content),
        }


# Reused across tasks (see browser_pool.py below for a better pattern)
async def scrape_browser(url: str) -> ScrapeResult:
    playwright: Playwright | None = None
    browser: Browser | None = None
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle",
                        timeout=settings.BROWSER_TIMEOUT_MS)
        title = await page.title()
        content = await page.locator("body").inner_text()
        return {
            "url": page.url,
            "title": title or "",
            "content": content,
            "hash": hash_content(content),
        }
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
