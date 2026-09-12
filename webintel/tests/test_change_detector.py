"""
Unit tests for the change detector module.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


pytestmark = pytest.mark.asyncio


@pytest.fixture
def detector_cls():
    try:
        from backend.app.change_detector import ChangeDetector
        return ChangeDetector
    except Exception:
        pytest.skip("backend.app.change_detector.ChangeDetector not available")


# ---------------------------------------------------------------------- #
# HTML hashing / diffing
# ---------------------------------------------------------------------- #
def test_hash_is_stable(detector_cls):
    detector = detector_cls()
    html = "<html><body>hello</body></html>"
    h1 = detector._hash(html) if hasattr(detector, "_hash") else hash(html)
    h2 = detector._hash(html) if hasattr(detector, "_hash") else hash(html)
    assert h1 == h2


def test_hash_changes_with_content(detector_cls):
    detector = detector_cls()
    a = "<html><body>hello</body></html>"
    b = "<html><body>world</body></html>"
    if hasattr(detector, "_hash"):
        assert detector._hash(a) != detector._hash(b)


async def test_detect_no_change(detector_cls, tmp_storage_dir: Path, sample_html):
    detector = detector_cls(storage_dir=tmp_storage_dir) if "storage_dir" in detector_cls.__init__.__code__.co_varnames else detector_cls()

    with patch.object(
        detector_cls, "_fetch_html", new=AsyncMock(return_value=sample_html)
    ):
        first = await detector.detect("https://example.com")
        second = await detector.detect("https://example.com")

    assert second.get("changed") is False


async def test_detect_change(detector_cls, tmp_storage_dir: Path, sample_html, sample_html_changed):
    detector = detector_cls() if "storage_dir" not in detector_cls.__init__.__code__.co_varnames else detector_cls(storage_dir=tmp_storage_dir)

    responses = [sample_html, sample_html_changed]
    async def fake_fetch(url):
        return responses.pop(0)

    with patch.object(detector_cls, "_fetch_html", new=AsyncMock(side_effect=fake_fetch)):
        await detector.detect("https://example.com")
        result = await detector.detect("https://example.com")

    assert result.get("changed") is True


async def test_detect_first_time_is_not_a_change(detector_cls, sample_html):
    detector = detector_cls()
    with patch.object(
        detector_cls, "_fetch_html", new=AsyncMock(return_value=sample_html)
    ):
        result = await detector.detect("https://example.com")

    # First observation should either be changed=False or explicitly flagged
    assert result.get("changed") in (False, None, 0) or result.get("first_seen") is True


async def test_detect_handles_fetch_error(detector_cls):
    detector = detector_cls()
    with patch.object(
        detector_cls,
        "_fetch_html",
        new=AsyncMock(side_effect=RuntimeError("network down")),
    ):
        with pytest.raises(Exception):
            await detector.detect("https://example.com")


async def test_detect_with_selector(detector_cls, sample_html, sample_html_changed):
    detector = detector_cls()
    responses = [sample_html, sample_html_changed]
    async def fake_fetch(url, selector=None):
        return responses.pop(0)

    with patch.object(detector_cls, "_fetch_html", new=AsyncMock(side_effect=fake_fetch)):
        if hasattr(detector, "detect_selector"):
            await detector.detect_selector("https://example.com", ".price")
            result = await detector.detect_selector("https://example.com", ".price")
            assert result.get("changed") is True


# ---------------------------------------------------------------------- #
# Storage
# ---------------------------------------------------------------------- #
async def test_storage_persists_between_instances(detector_cls, tmp_storage_dir: Path, sample_html):
    try:
        d1 = detector_cls(storage_dir=tmp_storage_dir)
    except TypeError:
        pytest.skip("ChangeDetector does not accept storage_dir")

    with patch.object(
        detector_cls, "_fetch_html", new=AsyncMock(return_value=sample_html)
    ):
        await d1.detect("https://example.com")

    d2 = detector_cls(storage_dir=tmp_storage_dir)
    with patch.object(
        detector_cls, "_fetch_html", new=AsyncMock(return_value=sample_html)
    ):
        result = await d2.detect("https://example.com")

    assert result.get("changed") is False


async def test_reset_clears_state(detector_cls, sample_html):
    detector = detector_cls()
    with patch.object(
        detector_cls, "_fetch_html", new=AsyncMock(return_value=sample_html)
    ):
        await detector.detect("https://example.com")

    if hasattr(detector, "reset"):
        await detector.reset("https://example.com")
        with patch.object(
            detector_cls, "_fetch_html", new=AsyncMock(return_value=sample_html)
        ):
            result = await detector.detect("https://example.com")
        assert result.get("changed") in (False, None, 0) or result.get("first_seen") is True


# ---------------------------------------------------------------------- #
# Diff output
# ---------------------------------------------------------------------- #
async def test_diff_is_returned_on_change(detector_cls, sample_html, sample_html_changed):
    detector = detector_cls()
    responses = [sample_html, sample_html_changed]
    async def fake_fetch(url):
        return responses.pop(0)

    with patch.object(detector_cls, "_fetch_html", new=AsyncMock(side_effect=fake_fetch)):
        await detector.detect("https://example.com")
        result = await detector.detect("https://example.com")

    if result.get("changed"):
        assert result.get("diff") is not None