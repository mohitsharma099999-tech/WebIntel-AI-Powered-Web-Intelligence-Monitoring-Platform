import hashlib
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

USER_AGENT = "WebIntelBot/1.0 (respectful research crawler)"

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def scrape_requests(url: str):
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    content = soup.get_text(separator=" ", strip=True)
    return {"url": url, "title": title, "content": content, "hash": hash_content(content)}

async def scrape_browser(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        title = await page.title()
        content = await page.locator("body").inner_text()
        await browser.close()
        return {"url": url, "title": title, "content": content, "hash": hash_content(content)}
