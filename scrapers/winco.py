"""Scraper for WinCo Foods (Lakewood, WA) meat prices.

WinCo doesn't publish digital weekly ads — they use in-store green tags.
Primary method: Claude Vision analysis of user-provided photos.
Fallback: known everyday prices.
"""

from pathlib import Path
from .vision import analyze_image
from .search import search_meat_prices, search_and_follow

STORE_NAME = "WinCo"
SCAN_DIR = Path(__file__).parent.parent / "scans" / "winco"

# Everyday prices — WinCo is known for low everyday prices
KNOWN_PRICES = [
    {"store": STORE_NAME, "cut": "Chicken Breast Boneless Skinless", "price_per_lb": 2.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Thighs Boneless Skinless", "price_per_lb": 2.48, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Whole Chicken", "price_per_lb": 1.68, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Tenderloin", "price_per_lb": 4.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Loin Roast", "price_per_lb": 2.48, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Chops Bone-In", "price_per_lb": 2.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Ground Beef 80/20", "price_per_lb": 4.48, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chuck Roast", "price_per_lb": 5.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Top Sirloin Steak", "price_per_lb": 7.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Atlantic Salmon Fillet", "price_per_lb": 8.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Raw Shrimp 21-25 ct", "price_per_lb": 7.48, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Sole Fillet", "price_per_lb": 6.98, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Flounder Fillet", "price_per_lb": 6.98, "sale_end_date": None},
]


def scrape_winco() -> list[dict]:
    """Return prices from scans or search (for sale/ad use)."""
    results = _scan_local_photos()
    if not results:
        results = search_meat_prices(STORE_NAME, "Lakewood WA")
    if not results:
        results = search_and_follow(STORE_NAME, "Lakewood WA")
    return results


def get_everyday_prices() -> list[dict]:
    """Return everyday prices. Uses scans if available, else known prices."""
    results = _scan_local_photos()
    if not results:
        results = KNOWN_PRICES.copy()
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
