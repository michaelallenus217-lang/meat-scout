"""Scraper for Costco (Lakewood, WA) meat prices."""

from .flipp import fetch_flipp_prices
from .search import search_meat_prices, search_and_follow

STORE_NAME = "Costco"

# Everyday (non-sale) prices — verified from in-store visits
KNOWN_PRICES = [
    {"store": STORE_NAME, "cut": "Chicken Breast Boneless Skinless", "price_per_lb": 3.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Thighs Boneless Skinless", "price_per_lb": 2.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Whole Chicken (Rotisserie)", "price_per_lb": 2.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Tenderloin", "price_per_lb": 4.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Loin Roast", "price_per_lb": 2.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Chops Boneless", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Ground Beef 88/12", "price_per_lb": 5.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chuck Roast", "price_per_lb": 6.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Top Sirloin Steak", "price_per_lb": 8.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Atlantic Salmon Fillet", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Raw Shrimp 21-25 ct", "price_per_lb": 7.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Sole Fillet", "price_per_lb": 7.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Flounder Fillet", "price_per_lb": 7.99, "sale_end_date": None},
]


def scrape_costco() -> list[dict]:
    """Return sale/ad deals from Flipp."""
    results = fetch_flipp_prices(STORE_NAME)
    if not results:
        results = search_meat_prices(STORE_NAME, "Lakewood WA")
    if not results:
        results = search_and_follow(STORE_NAME, "Lakewood WA")
    return results


def get_everyday_prices() -> list[dict]:
    """Return everyday (non-sale) prices."""
    return KNOWN_PRICES.copy()
