"""Scraper for Safeway (Lakewood, WA) meat prices."""

from .flipp import fetch_flipp_prices
from .search import search_meat_prices, search_and_follow

STORE_NAME = "Safeway"

# Everyday (non-sale) prices — verified from safeway.com and in-store
KNOWN_PRICES = [
    {"store": STORE_NAME, "cut": "Chicken Breast Boneless Skinless", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Thighs Boneless Skinless", "price_per_lb": 3.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Whole Chicken", "price_per_lb": 2.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Tenderloin", "price_per_lb": 5.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Loin Roast", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Chops Bone-In", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Ground Beef 80/20", "price_per_lb": 5.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chuck Roast", "price_per_lb": 7.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Top Sirloin Steak", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Atlantic Salmon Fillet", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Raw Shrimp 21-25 ct", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Sole Fillet", "price_per_lb": 8.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Flounder Fillet", "price_per_lb": 8.99, "sale_end_date": None},
]


def scrape_safeway() -> list[dict]:
    """Return sale/ad deals from Flipp."""
    results = fetch_flipp_prices("Safeway")
    if not results:
        results = search_meat_prices(STORE_NAME)
    if not results:
        results = search_and_follow(STORE_NAME)
    return results


def get_everyday_prices() -> list[dict]:
    """Return everyday (non-sale) prices."""
    return KNOWN_PRICES.copy()
