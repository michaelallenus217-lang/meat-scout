"""Scraper for JBLM Commissary (DeCA) meat prices.

The commissary doesn't publish weekly ads online.
Prices are cost + 5% surcharge, relatively stable.
Primary source: user --scan photos from in-store visits.
Fallback: known price list from verified in-store visits.
"""

from pathlib import Path

from .vision import analyze_image
from .search import search_meat_prices

STORE_NAME = "Commissary (JBLM)"
SCAN_DIR = Path(__file__).parent.parent / "scans" / "commissary"

# Known commissary prices — cost + 5% surcharge
# These are baseline estimates; update with --scan photos for accuracy
KNOWN_PRICES = [
    # Chicken
    {"store": STORE_NAME, "cut": "Chicken Breast Boneless Skinless", "price_per_lb": 2.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Thighs Bone-In", "price_per_lb": 1.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Drumsticks", "price_per_lb": 1.29, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Whole Chicken", "price_per_lb": 1.79, "sale_end_date": None},
    # Beef
    {"store": STORE_NAME, "cut": "Ground Beef 80/20", "price_per_lb": 4.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chuck Roast", "price_per_lb": 6.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Top Sirloin Steak", "price_per_lb": 7.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Ribeye Steak", "price_per_lb": 12.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "New York Strip Steak", "price_per_lb": 11.99, "sale_end_date": None},
    # Pork
    {"store": STORE_NAME, "cut": "Pork Chops Bone-In", "price_per_lb": 2.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Tenderloin", "price_per_lb": 4.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Loin Roast", "price_per_lb": 2.79, "sale_end_date": None},
    # Seafood
    {"store": STORE_NAME, "cut": "Atlantic Salmon Fillet", "price_per_lb": 8.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Raw Shrimp 21-25 ct", "price_per_lb": 7.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Sole Fillet", "price_per_lb": 6.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Flounder Fillet", "price_per_lb": 7.49, "sale_end_date": None},
]


def get_everyday_prices() -> list[dict]:
    """Return everyday prices. Uses scans if available, else known prices."""
    results = _scan_local_photos()
    if not results:
        results = KNOWN_PRICES.copy()
    return results


def scrape_commissary() -> list[dict]:
    """Return list of meat prices: {store, cut, price_per_lb, sale_end_date}."""
    results = _scan_local_photos()
    if not results:
        results = search_meat_prices(STORE_NAME)
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
