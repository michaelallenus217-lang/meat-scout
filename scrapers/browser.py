"""Playwright browser automation for JS-rendered store pages.

Used ONLY for Trader Joe's and Stadium Thriftway where httpx can't
reach the content (React app and Red Pepper Digital flyer).
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def screenshot_page(url: str, wait_selector: str | None = None, scroll: bool = False) -> bytes | None:
    """Load a page in headless Chromium and return a full-page screenshot as PNG bytes."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 2000},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)

            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=10000)
                except PWTimeout:
                    pass  # continue with whatever loaded

            if scroll:
                _scroll_to_load(page)

            screenshot = page.screenshot(full_page=True)
            browser.close()
            return screenshot

    except Exception:
        return None


def get_page_text(url: str, wait_selector: str | None = None) -> str | None:
    """Load a page in headless Chromium and return rendered text content."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 2000},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)

            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=10000)
                except PWTimeout:
                    pass

            text = page.inner_text("body")
            browser.close()
            return text

    except Exception:
        return None


def screenshot_multiple_pages(urls: list[str], wait_selector: str | None = None) -> list[bytes]:
    """Screenshot multiple URLs using a single browser session."""
    screenshots = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 2000},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            for url in urls:
                try:
                    page = context.new_page()
                    page.goto(url, wait_until="networkidle", timeout=30000)

                    if wait_selector:
                        try:
                            page.wait_for_selector(wait_selector, timeout=10000)
                        except PWTimeout:
                            pass

                    screenshots.append(page.screenshot(full_page=True))
                    page.close()
                except Exception:
                    continue

            browser.close()

    except Exception:
        pass

    return screenshots


def _scroll_to_load(page, scrolls: int = 5) -> None:
    """Scroll down incrementally to trigger lazy-loaded content."""
    for _ in range(scrolls):
        page.evaluate("window.scrollBy(0, window.innerHeight)")
        page.wait_for_timeout(1000)
