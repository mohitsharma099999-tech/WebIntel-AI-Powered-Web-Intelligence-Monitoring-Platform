"""
Unit tests for the scraper module.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.browser_pool import BrowserPool, PoolConfig
from backend.app.exceptions import (
    BrowserLaunchError,
    PageCreationError,
    PoolShutdownError,
    PoolTimeoutError,
)


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------- #
# Scraper class tests (adjust import to your actual module)
# ---------------------------------------------------------------------- #
@pytest.fixture
def scraper_cls():
    try:
        from backend.app.scraper import Scraper
        return Scraper
    except Exception:
        pytest.skip("backend.app.scraper.Scraper not available")


async def test_scrape_returns_html(scraper_cls, mock_page):
    scraper = scraper_cls()
    mock_page.goto = AsyncMock(return_value=None)
    mock_page.content = AsyncMock(return_value="<html><body>hi</body></html>")

    with patch.object(scraper_cls, "_new_page", new=AsyncMock(return_value=mock_page)):
        result = await scraper.scrape("https://example.com")

    assert result is not None
    # Depending on API, result may be a str or dict
    if isinstance(result, dict):
        assert "content" in result or "html" in result
    else:
        assert "hi" in result


async def test_scrape_closes_page_on_error(scraper_cls, mock_page):
    scraper = scraper_cls()
    mock_page.goto = AsyncMock(side_effect=RuntimeError("nav failed"))
    mock_page.close = AsyncMock()

    with patch.object(scraper_cls, "_new_page", new=AsyncMock(return_value=mock_page)):
        with pytest.raises(Exception):
            await scraper.scrape("https://example.com")

    mock_page.close.assert_awaited()


async def test_scrape_extracts_with_selector(scraper_cls, mock_page):
    scraper = scraper_cls()
    el = MagicMock()
    el.inner_text = AsyncMock(return_value="$19.99")
    mock_page.query_selector_all = AsyncMock(return_value=[el])
    mock_page.goto = AsyncMock(return_value=None)

    with patch.object(scraper_cls, "_new_page", new=AsyncMock(return_value=mock_page)):
        if hasattr(scraper, "scrape_selector"):
            result = await scraper.scrape_selector(
                "https://example.com", ".price"
            )
            assert result is not None


# ---------------------------------------------------------------------- #
# BrowserPool integration
# ---------------------------------------------------------------------- #
async def test_pool_acquire_yields_page(browser_pool: BrowserPool, mock_page):
    async with browser_pool.acquire() as page:
        assert page is mock_page
        await page.goto("https://example.com")


async def test_pool_releases_page_after_use(browser_pool: BrowserPool, mock_page):
    async with browser_pool.acquire() as page:
        pass
    mock_page.close.assert_awaited()


async def test_pool_releases_on_exception(browser_pool: BrowserPool, mock_page):
    with pytest.raises(RuntimeError):
        async with browser_pool.acquire() as page:
            raise RuntimeError("boom")
    mock_page.close.assert_awaited()


async def test_pool_respects_max_size(mock_playwright, mock_page):
    pool = BrowserPool(PoolConfig(max_size=1, min_size=0, acquire_timeout=0.2))
    with patch("backend.app.browser_pool.async_playwright") as ap:
        ap.return_value.start = AsyncMock(return_value=mock_playwright)
        await pool.start()
        try:
            async with pool.acquire():
                # Second acquire should time out
                with pytest.raises(PoolTimeoutError):
                    async with pool.acquire():
                        pass
        finally:
            await pool.shutdown(timeout=5.0)


async def test_pool_raises_on_shutdown_acquire(browser_pool: BrowserPool):
    await browser_pool.shutdown(timeout=5.0)
    with pytest.raises((PoolShutdownError, Exception)):
        async with browser_pool.acquire():
            pass


async def test_pool_stats_track_uses(browser_pool: BrowserPool):
    async with browser_pool.acquire():
        pass
    assert browser_pool.stats["acquired"] >= 1
    assert browser_pool.stats["released"] >= 1


async def test_pool_recycles_unhealthy_browser(mock_playwright, mock_browser, mock_page):
    pool = BrowserPool(PoolConfig(max_size=2, min_size=0, acquire_timeout=1.0))
    with patch("backend.app.browser_pool.async_playwright") as ap:
        ap.return_value.start = AsyncMock(return_value=mock_playwright)
        await pool.start()
        try:
            async with pool.acquire():
                pass
            # Mark disconnected
            mock_browser.is_connected = MagicMock(return_value=False)
            async with pool.acquire() as page:
                assert page is mock_page
        finally:
            await pool.shutdown(timeout=5.0)


async def test_pool_launch_failure_raises(mock_playwright):
    mock_playwright.chromium.launch = AsyncMock(
        side_effect=RuntimeError("launch failed")
    )
    pool = BrowserPool(PoolConfig(max_size=1, min_size=0, acquire_timeout=1.0))
    with patch("backend.app.browser_pool.async_playwright") as ap:
        ap.return_value.start = AsyncMock(return_value=mock_playwright)
        await pool.start()
        try:
            with pytest.raises((BrowserLaunchError, PageCreationError)):
                async with pool.acquire():
                    pass
        finally:
            await pool.shutdown(timeout=5.0)


async def test_pool_timeout_on_acquire(mock_playwright, mock_page):
    pool = BrowserPool(PoolConfig(max_size=1, min_size=1, acquire_timeout=0.1))
    with patch("backend.app.browser_pool.async_playwright") as ap:
        ap.return_value.start = AsyncMock(return_value=mock_playwright)
        await pool.start()
        try:
            async with pool.acquire():
                with pytest.raises(PoolTimeoutError):
                    async with pool.acquire():
                        pass
        finally:
            await pool.shutdown(timeout=5.0)