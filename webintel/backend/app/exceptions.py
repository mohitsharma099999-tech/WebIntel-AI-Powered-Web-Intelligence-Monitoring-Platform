"""
Custom exceptions for the browser pool application.
"""

from typing import Any, Optional


class BrowserPoolError(Exception):
    """Base exception for all browser pool related errors."""

    def __init__(self, message: str = "Browser pool error occurred", details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details: {self.details}"
        return self.message


class BrowserNotFoundError(BrowserPoolError):
    """Raised when a requested browser instance cannot be found."""

    def __init__(self, browser_id: str, details: Optional[Any] = None):
        self.browser_id = browser_id
        super().__init__(
            message=f"Browser with id '{browser_id}' not found",
            details=details,
        )


class BrowserLaunchError(BrowserPoolError):
    """Raised when a browser fails to launch."""

    def __init__(self, message: str = "Failed to launch browser", details: Optional[Any] = None):
        super().__init__(message=message, details=details)


class BrowserClosedError(BrowserPoolError):
    """Raised when an operation is attempted on a closed browser."""

    def __init__(self, browser_id: Optional[str] = None, details: Optional[Any] = None):
        message = (
            f"Browser '{browser_id}' is already closed"
            if browser_id
            else "Browser is already closed"
        )
        super().__init__(message=message, details=details)


class PoolExhaustedError(BrowserPoolError):
    """Raised when the pool has no available browsers and is at max capacity."""

    def __init__(self, max_size: int, details: Optional[Any] = None):
        self.max_size = max_size
        super().__init__(
            message=f"Browser pool exhausted (max size: {max_size})",
            details=details,
        )


class PoolShutdownError(BrowserPoolError):
    """Raised when an operation is attempted on a pool that is shutting down or shut down."""

    def __init__(self, message: str = "Browser pool is shut down", details: Optional[Any] = None):
        super().__init__(message=message, details=details)


class PoolTimeoutError(BrowserPoolError):
    """Raised when waiting for an available browser times out."""

    def __init__(self, timeout: float, details: Optional[Any] = None):
        self.timeout = timeout
        super().__init__(
            message=f"Timed out after {timeout}s waiting for an available browser",
            details=details,
        )


class PageCreationError(BrowserPoolError):
    """Raised when creating a new page/context fails."""

    def __init__(self, message: str = "Failed to create page", details: Optional[Any] = None):
        super().__init__(message=message, details=details)


class InvalidConfigurationError(BrowserPoolError):
    """Raised when the pool is configured with invalid parameters."""

    def __init__(self, message: str = "Invalid browser pool configuration", details: Optional[Any] = None):
        super().__init__(message=message, details=details)


class BrowserCrashedError(BrowserPoolError):
    """Raised when a browser process crashes unexpectedly."""

    def __init__(self, browser_id: Optional[str] = None, details: Optional[Any] = None):
        message = (
            f"Browser '{browser_id}' crashed"
            if browser_id
            else "Browser crashed"
        )
        super().__init__(message=message, details=details)


__all__ = [
    "BrowserPoolError",
    "BrowserNotFoundError",
    "BrowserLaunchError",
    "BrowserClosedError",
    "PoolExhaustedError",
    "PoolShutdownError",
    "PoolTimeoutError",
    "PageCreationError",
    "InvalidConfigurationError",
    "BrowserCrashedError",
]
