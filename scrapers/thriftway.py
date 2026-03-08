"""Scraper for Stadium Thriftway (Tacoma, WA) weekly meat deals.

Stadium Thriftway uses Red Pepper Digital for their weekly ad.
We use Playwright to open the flyer, grab the CloudFront page images,
then send them to Claude Vision for price extraction.
"""

import re
from pathlib import Path

from .vision import analyze_image, analyze_screenshot
from .search import search_meat_prices, search_and_follow

STORE_NAME = "Stadium Thriftway"
FLYER_HOME = "https://app.redpepper.digital/a10/publications/home/4824?toolbar=no&portrait=true&cw=1280"
SCAN_DIR = Path(__file__).parent.parent / "scans" / "thriftway"

# Everyday (non-sale) prices — verified from in-store
KNOWN_PRICES = [
    {"store": STORE_NAME, "cut": "Chicken Breast Boneless Skinless", "price_per_lb": 4.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Thighs Boneless Skinless", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Whole Chicken", "price_per_lb": 2.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Tenderloin", "price_per_lb": 5.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Loin Roast", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Chops Bone-In", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Ground Beef 80/20", "price_per_lb": 5.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chuck Roast", "price_per_lb": 7.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Top Sirloin Steak", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Atlantic Salmon Fillet", "price_per_lb": 10.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Raw Shrimp 21-25 ct", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Sole Fillet", "price_per_lb": 8.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Flounder Fillet", "price_per_lb": 8.99, "sale_end_date": None},
]


def get_everyday_prices() -> list[dict]:
    """Return everyday (non-sale) prices."""
    return KNOWN_PRICES.copy()


def scrape_thriftway() -> list[dict]:
    """Return list of meat deals: {store, cut, price_per_lb, sale_end_date}."""
    results = _scan_local_photos()
    if not results:
        results = _try_redpepper_flyer()
    if not results:
        results = search_meat_prices(STORE_NAME, "Tacoma WA")
    if not results:
        results = search_and_follow(STORE_NAME, "Tacoma WA")
    return results


def _scan_local_photos() -> list[dict]:
    """Analyze user photos with Claude Vision."""
    if not SCAN_DIR.exists():
        return []

    results = []
    for img_path in sorted(SCAN_DIR.iterdir()):
        if img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            items = analyze_image(str(img_path), STORE_NAME)
            results.extend(items)

    return results


def _try_redpepper_flyer() -> list[dict]:
    """Open the Red Pepper Digital flyer, get page images, analyze with Vision."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    import httpx
    import tempfile

    page_urls = _get_flyer_page_urls()
    if not page_urls:
        return []

    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    for url in page_urls:
        try:
            resp = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
            if resp.status_code != 200:
                continue

            # Save to temp file and analyze
            suffix = ".webp" if "webp" in url else ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(resp.content)
                tmp_path = f.name

            items = analyze_image(tmp_path, STORE_NAME)
            results.extend(items)

            Path(tmp_path).unlink(missing_ok=True)

        except (httpx.HTTPError, httpx.TimeoutException):
            continue

    return results


def _get_flyer_page_urls() -> list[str]:
    """Use Playwright to open the Red Pepper flyer and extract page image URLs."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return []

    urls = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_context(
                viewport={"width": 1280, "height": 2000},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ).new_page()

            page.goto(FLYER_HOME, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Click on "Stadium Thriftway Weekly Ad" to open the flyer
            try:
                page.click("text=Stadium Thriftway Weekly Ad", timeout=5000)
                page.wait_for_timeout(5000)
            except PWTimeout:
                browser.close()
                return []

            # Collect CloudFront image URLs (full-size flyer pages)
            imgs = page.query_selector_all("img")
            for img in imgs:
                src = img.get_attribute("src") or ""
                if "cloudfront.net/prod/" in src and src.endswith(".webp"):
                    urls.append(src)

            browser.close()

    except Exception:
        pass

    return urls
