"""
Shared pytest fixtures for the test suite.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Adjust import path depending on your package layout
from backend.app.browser_pool import BrowserPool, PoolConfig


# ---------------------------------------------------------------------- #
# Event loop
# ---------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Provide a session-scoped event loop for pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------- #
# Paths
# ---------------------------------------------------------------------- #
@pytest.fixture
def tmp_storage_dir(tmp_path: Path) -> Path:
    """Isolated temporary storage directory per test."""
    storage = tmp_path / "storage"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def sample_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
      <head><title>Sample</title></head>
      <body>
        <h1>Hello</h1>
        <p class="price">$19.99</p>
        <p class="price">$29.99</p>
      </body>
    </html>
    """


@pytest.fixture
def sample_html_changed() -> str:
    return """
    <!DOCTYPE html>
    <html>
      <head><title>Sample</title></head>
      <body>
        <h1>Hello</h1>
        <p class="price">$24.99</p>
        <p class="price">$29.99</p>
      </body>
    </html>
    """


# ---------------------------------------------------------------------- #
# Mocked Playwright primitives
# ---------------------------------------------------------------------- #
@pytest.fixture
def mock_page() -> AsyncMock:
    page = AsyncMock()
    page.goto = AsyncMock(return_value=None)
    page.content = AsyncMock(return_value="<html><body>mock</body></html>")
    page.close = AsyncMock(return_value=None)
    page.title = AsyncMock(return_value="Mock Title")
    page.query_selector_all = AsyncMock(return_value=[])
    page.wait_for_selector = AsyncMock(return_value=None)
    return page


@pytest.fixture
def mock_context(mock_page: AsyncMock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.new_page = AsyncMock(return_value=mock_page)
    ctx.close = AsyncMock(return_value=None)
    return ctx


@pytest.fixture
def mock_browser(mock_context: AsyncMock) -> MagicMock:
    browser = MagicMock()
    browser.new_context = AsyncMock(return_value=mock_context)
    browser.close = AsyncMock(return_value=None)
    browser.is_connected = MagicMock(return_value=True)
    browser.on = MagicMock()
    return browser


@pytest.fixture
def mock_playwright(mock_browser: MagicMock) -> MagicMock:
    pw = MagicMock()
    pw.chromium = MagicMock()
    pw.chromium.launch = AsyncMock(return_value=mock_browser)
    pw.firefox = MagicMock()
    pw.firefox.launch = AsyncMock(return_value=mock_browser)
    pw.webkit = MagicMock()
    pw.webkit.launch = AsyncMock(return_value=mock_browser)
    pw.stop = AsyncMock(return_value=None)
    return pw


# ---------------------------------------------------------------------- #
# Browser pool
# ---------------------------------------------------------------------- #
@pytest_asyncio.fixture
async def browser_pool(mock_playwright: MagicMock) -> AsyncIterator[BrowserPool]:
    """A started BrowserPool backed by a mocked Playwright."""
    pool = BrowserPool(
        PoolConfig(max_size=3, min_size=0, acquire_timeout=2.0)
    )
    with patch("backend.app.browser_pool.async_playwright") as ap:
        ap.return_value.start = AsyncMock(return_value=mock_playwright)
        await pool.start()
        try:
            yield pool
        finally:
            await pool.shutdown(timeout=5.0)


# ---------------------------------------------------------------------- #
# FastAPI app / clients
# ---------------------------------------------------------------------- #
@pytest.fixture
def app():
    """Override with your real FastAPI app.

    Example:
        from backend.app.main import app as fastapi_app
        return fastapi_app
    """
    try:
        from backend.app.main import app as fastapi_app  # type: ignore
        return fastapi_app
    except Exception:  # pragma: no cover
        pytest.skip("backend.app.main.app not available")


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client(app) -> AsyncIterator[AsyncClient]:
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------- #
# Misc
# ---------------------------------------------------------------------- #
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"