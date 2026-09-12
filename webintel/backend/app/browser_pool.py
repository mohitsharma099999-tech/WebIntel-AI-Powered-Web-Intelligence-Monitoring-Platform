"""
Async browser pool for managing a set of Playwright browser instances.

Provides bounded concurrency, health checks, recycling, and graceful shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from .exceptions import (
    BrowserClosedError,
    BrowserCrashedError,
    BrowserLaunchError,
    BrowserNotFoundError,
    InvalidConfigurationError,
    PageCreationError,
    PoolExhaustedError,
    PoolShutdownError,
    PoolTimeoutError,
)

logger = logging.getLogger(__name__)


class BrowserState(str, Enum):
    IDLE = "idle"
    IN_USE = "in_use"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"


@dataclass
class BrowserInstance:
    """Wrapper around a Playwright Browser with lifecycle metadata."""

    id: str
    browser: Browser
    context: BrowserContext
    state: BrowserState = BrowserState.IDLE
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def age(self) -> float:
        return time.time() - self.created_at

    @property
    def idle_time(self) -> float:
        return time.time() - self.last_used_at

    async def new_page(self) -> Page:
        if self.state in (BrowserState.CLOSED, BrowserState.UNHEALTHY):
            raise BrowserClosedError(browser_id=self.id)
        try:
            page = await self.context.new_page()
            self.use_count += 1
            self.last_used_at = time.time()
            return page
        except Exception as exc:  # pragma: no cover - depends on playwright internals
            self.state = BrowserState.UNHEALTHY
            raise PageCreationError(details=str(exc)) from exc

    async def is_healthy(self) -> bool:
        if self.state == BrowserState.CLOSED:
            return False
        try:
            return self.browser.is_connected()
        except Exception:
            return False

    async def close(self) -> None:
        self.state = BrowserState.CLOSED
        try:
            await self.context.close()
        except Exception as exc:
            logger.debug("Error closing context for browser %s: %s", self.id, exc)
        try:
            await self.browser.close()
        except Exception as exc:
            logger.debug("Error closing browser %s: %s", self.id, exc)


@dataclass
class PoolConfig:
    """Configuration for BrowserPool."""

    max_size: int = 5
    min_size: int = 1
    acquire_timeout: float = 30.0
    max_uses_per_browser: int = 100
    max_browser_age: float = 60 * 30  # 30 minutes
    max_idle_time: float = 60 * 5     # 5 minutes
    headless: bool = True
    browser_type: str = "chromium"
    launch_args: List[str] = field(default_factory=list)
    context_options: Dict[str, Any] = field(default_factory=dict)
    health_check_interval: float = 30.0
    recycle_interval: float = 60.0

    def validate(self) -> None:
        if self.max_size < 1:
            raise InvalidConfigurationError("max_size must be >= 1")
        if self.min_size < 0:
            raise InvalidConfigurationError("min_size must be >= 0")
        if self.min_size > self.max_size:
            raise InvalidConfigurationError("min_size cannot exceed max_size")
        if self.acquire_timeout <= 0:
            raise InvalidConfigurationError("acquire_timeout must be > 0")
        if self.browser_type not in ("chromium", "firefox", "webkit"):
            raise InvalidConfigurationError(
                f"Unsupported browser_type: {self.browser_type}"
            )


class BrowserPool:
    """
    Async pool of reusable Playwright browsers with bounded concurrency.

    Usage:
        pool = BrowserPool(PoolConfig(max_size=4))
        await pool.start()
        try:
            async with pool.acquire() as page:
                await page.goto("https://example.com")
        finally:
            await pool.shutdown()
    """

    def __init__(self, config: Optional[PoolConfig] = None) -> None:
        self.config = config or PoolConfig()
        self.config.validate()

        self._playwright: Optional[Playwright] = None
        self._instances: Dict[str, BrowserInstance] = {}
        self._available: asyncio.Queue[str] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(self.config.max_size)
        self._lock = asyncio.Lock()
        self._started = False
        self._shutting_down = False
        self._background_tasks: List[asyncio.Task] = []
        self._stats = {
            "acquired": 0,
            "released": 0,
            "launched": 0,
            "closed": 0,
            "errors": 0,
        }

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """Start Playwright and pre-warm the minimum pool size."""
        async with self._lock:
            if self._started:
                return
            if self._shutting_down:
                raise PoolShutdownError("Pool is shutting down")

            try:
                self._playwright = await async_playwright().start()
            except Exception as exc:
                raise BrowserLaunchError(
                    message="Failed to start Playwright", details=str(exc)
                ) from exc

            self._started = True

        # Pre-warm
        for _ in range(self.config.min_size):
            try:
                instance = await self._launch_browser()
                await self._available.put(instance.id)
            except Exception as exc:
                logger.warning("Failed to pre-warm browser: %s", exc)

        # Background maintenance
        self._background_tasks = [
            asyncio.create_task(self._health_check_loop(), name="browserpool-health"),
            asyncio.create_task(self._recycle_loop(), name="browserpool-recycle"),
        ]
        logger.info(
            "BrowserPool started (min=%d, max=%d, type=%s)",
            self.config.min_size,
            self.config.max_size,
            self.config.browser_type,
        )

    async def shutdown(self, timeout: float = 30.0) -> None:
        """Gracefully shut down all browsers and Playwright."""
        async with self._lock:
            if self._shutting_down:
                return
            self._shutting_down = True
            self._started = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        # Close all instances
        instances = list(self._instances.values())
        if instances:
            await asyncio.wait_for(
                asyncio.gather(
                    *(inst.close() for inst in instances),
                    return_exceptions=True,
                ),
                timeout=timeout,
            )
        self._instances.clear()

        # Drain queue
        while not self._available.empty():
            try:
                self._available.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Stop playwright
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception as exc:
                logger.debug("Error stopping Playwright: %s", exc)
            self._playwright = None

        logger.info("BrowserPool shut down. Stats: %s", self._stats)

    # ------------------------------------------------------------------ #
    # Acquire / Release
    # ------------------------------------------------------------------ #
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Page]:
        """
        Async context manager yielding a fresh Page from a pooled browser.
        Automatically releases the browser back to the pool when done.
        """
        page, instance_id = await self._acquire_page()
        try:
            yield page
        finally:
            await self._release(instance_id, page)

    async def _acquire_page(self) -> tuple[Page, str]:
        if self._shutting_down:
            raise PoolShutdownError()

        try:
            await asyncio.wait_for(
                self._semaphore.acquire(), timeout=self.config.acquire_timeout
            )
        except asyncio.TimeoutError as exc:
            raise PoolTimeoutError(self.config.acquire_timeout) from exc

        instance: Optional[BrowserInstance] = None
        try:
            instance = await self._get_or_create_instance()
            instance.state = BrowserState.IN_USE
            page = await instance.new_page()
            self._stats["acquired"] += 1
            return page, instance.id
        except Exception:
            self._stats["errors"] += 1
            if instance is not None:
                await self._discard_instance(instance.id, reason="acquire_failed")
            self._semaphore.release()
            raise

    async def _release(self, instance_id: str, page: Page) -> None:
        try:
            try:
                await page.close()
            except Exception as exc:
                logger.debug("Error closing page: %s", exc)

            instance = self._instances.get(instance_id)
            if instance is None:
                return

            # Check if it should be recycled
            if (
                instance.use_count >= self.config.max_uses_per_browser
                or instance.age >= self.config.max_browser_age
                or not await instance.is_healthy()
            ):
                await self._discard_instance(instance_id, reason="recycled")
            else:
                instance.state = BrowserState.IDLE
                instance.last_used_at = time.time()
                await self._available.put(instance_id)

            self._stats["released"] += 1
        finally:
            self._semaphore.release()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    async def _get_or_create_instance(self) -> BrowserInstance:
        # Try to fetch an idle instance
        while True:
            try:
                instance_id = self._available.get_nowait()
            except asyncio.QueueEmpty:
                break

            instance = self._instances.get(instance_id)
            if instance is None:
                continue
            if instance.state == BrowserState.CLOSED:
                continue
            if not await instance.is_healthy():
                await self._discard_instance(instance_id, reason="unhealthy")
                continue
            return instance

        # No idle instance — launch a new one if under capacity
        async with self._lock:
            if len(self._instances) < self.config.max_size:
                return await self._launch_browser()

        raise PoolExhaustedError(max_size=self.config.max_size)

    async def _launch_browser(self) -> BrowserInstance:
        if self._playwright is None:
            raise BrowserLaunchError("Playwright is not started")

        launcher = getattr(self._playwright, self.config.browser_type)
        try:
            browser: Browser = await launcher.launch(
                headless=self.config.headless,
                args=self.config.launch_args or None,
            )
            context: BrowserContext = await browser.new_context(
                **self.config.context_options
            )
        except Exception as exc:
            raise BrowserLaunchError(details=str(exc)) from exc

        instance = BrowserInstance(
            id=str(uuid.uuid4()),
            browser=browser,
            context=context,
        )
        self._instances[instance.id] = instance
        self._stats["launched"] += 1

        # Watch for unexpected disconnect
        browser.on("disconnected", lambda: asyncio.create_task(
            self._on_browser_disconnected(instance.id)
        ))

        logger.debug("Launched browser %s (total=%d)", instance.id, len(self._instances))
        return instance

    async def _on_browser_disconnected(self, instance_id: str) -> None:
        instance = self._instances.get(instance_id)
        if instance and instance.state != BrowserState.CLOSED:
            logger.warning("Browser %s disconnected unexpectedly", instance_id)
            instance.state = BrowserState.UNHEALTHY
            await self._discard_instance(instance_id, reason="disconnected")

    async def _discard_instance(self, instance_id: str, reason: str = "unknown") -> None:
        instance = self._instances.pop(instance_id, None)
        if instance is None:
            return
        self._stats["closed"] += 1
        logger.debug("Discarding browser %s (reason=%s)", instance_id, reason)
        await instance.close()

    # ------------------------------------------------------------------ #
    # Maintenance loops
    # ------------------------------------------------------------------ #
    async def _health_check_loop(self) -> None:
        try:
            while not self._shutting_down:
                await asyncio.sleep(self.config.health_check_interval)
                if self._shutting_down:
                    return
                for instance_id, instance in list(self._instances.items()):
                    if instance.state == BrowserState.IN_USE:
                        continue
                    if not await instance.is_healthy():
                        logger.warning("Health check failed for %s", instance_id)
                        await self._discard_instance(instance_id, reason="health_check")
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover
            logger.exception("Health check loop crashed: %s", exc)

    async def _recycle_loop(self) -> None:
        try:
            while not self._shutting_down:
                await asyncio.sleep(self.config.recycle_interval)
                if self._shutting_down:
                    return

                # Drop idle instances that exceed max_idle_time (keeping min_size)
                for instance_id, instance in list(self._instances.items()):
                    if instance.state != BrowserState.IDLE:
                        continue
                    if instance.idle_time < self.config.max_idle_time:
                        continue
                    if len(self._instances) <= self.config.min_size:
                        break
                    # Remove from available queue (best-effort)
                    await self._discard_instance(instance_id, reason="idle_timeout")
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover
            logger.exception("Recycle loop crashed: %s", exc)

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #
    @property
    def size(self) -> int:
        return len(self._instances)

    @property
    def available_count(self) -> int:
        return self._available.qsize()

    @property
    def in_use_count(self) -> int:
        return sum(
            1 for i in self._instances.values() if i.state == BrowserState.IN_USE
        )

    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    def get_instance(self, instance_id: str) -> BrowserInstance:
        instance = self._instances.get(instance_id)
        if instance is None:
            raise BrowserNotFoundError(instance_id)
        return instance

    def __repr__(self) -> str:
        return (
            f"<BrowserPool size={self.size}/{self.config.max_size} "
            f"available={self.available_count} in_use={self.in_use_count}>"
        )


__all__ = ["BrowserPool", "PoolConfig", "BrowserInstance", "BrowserState"]
