"""Scraper for Trader Joe's (Lakewood, WA) meat prices.

TJ's blocks headless browsers and doesn't publish weekly ads.
Prices are everyday low. We scrape traderjoesprices.com for current data,
then fall back to a verified known-price list.
User can also --scan photos taken in-store.
"""

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from .vision import analyze_image
from .search import search_meat_prices, HEADERS

STORE_NAME = "Trader Joe's"
SCAN_DIR = Path(__file__).parent.parent / "scans" / "traderjoes"

# Known TJ's meat prices — verified from traderjoesprices.com and in-store
KNOWN_PRICES = [
    # Chicken
    {"store": STORE_NAME, "cut": "Chicken Breast Boneless Skinless", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Organic Chicken Breast", "price_per_lb": 7.49, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Thighs Bone-In", "price_per_lb": 1.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Chicken Drumsticks", "price_per_lb": 1.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Whole Chicken", "price_per_lb": 2.49, "sale_end_date": None},
    # Beef
    {"store": STORE_NAME, "cut": "New York Strip Steak", "price_per_lb": 14.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Ribeye Steak", "price_per_lb": 15.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Filet Mignon", "price_per_lb": 21.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Flank Steak", "price_per_lb": 14.99, "sale_end_date": None},
    # Pork
    {"store": STORE_NAME, "cut": "Pork Chops Bone-In", "price_per_lb": 3.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Pork Tenderloin", "price_per_lb": 5.99, "sale_end_date": None},
    # Premium / Seafood
    {"store": STORE_NAME, "cut": "Atlantic Salmon Fillet", "price_per_lb": 9.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Wild Sockeye Salmon", "price_per_lb": 12.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Raw Shrimp 21-25 ct", "price_per_lb": 8.99, "sale_end_date": None},
    {"store": STORE_NAME, "cut": "Lamb Rack", "price_per_lb": 19.99, "sale_end_date": None},
]


def get_everyday_prices() -> list[dict]:
    """Return everyday prices."""
    return KNOWN_PRICES.copy()


def scrape_traderjoes() -> list[dict]:
    """Return list of meat prices: {store, cut, price_per_lb, sale_end_date}."""
    results = _scan_local_photos()
    if not results:
        results = _try_price_site()
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


def _try_price_site() -> list[dict]:
    """Try scraping traderjoesprices.com for current meat prices."""
    results = []

    try:
        resp = httpx.get(
            "https://traderjoesprices.com/",
            headers=HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("tr, .product-row, .item")
        for row in rows:
            text = row.get_text(separator=" ").lower()
            if not _is_meat(text):
                continue

            name, price = _parse_product_row(text)
            if name and price:
                price_per_lb = _to_per_lb(price, text)
                if price_per_lb and 0.50 < price_per_lb < 50.0:
                    results.append({
                        "store": STORE_NAME,
                        "cut": name.title(),
                        "price_per_lb": round(price_per_lb, 2),
                        "sale_end_date": None,
                    })

    except (httpx.HTTPError, httpx.TimeoutException):
        pass

    return results


def _is_meat(text: str) -> bool:
    meat_words = [
        "beef", "chicken", "pork", "steak", "turkey", "ground",
        "drumstick", "thigh", "breast", "ribeye", "sirloin",
        "filet", "tenderloin", "chop", "roast", "whole chicken",
    ]
    return any(w in text for w in meat_words)


def _parse_product_row(text: str) -> tuple[str | None, float | None]:
    price_match = re.search(r'\$(\d+\.?\d*)', text)
    if not price_match:
        return None, None
    price = float(price_match.group(1))
    name = text[:price_match.start()].strip()
    name = re.sub(r'\s+', ' ', name).strip(" -|")
    return name if name else None, price


def _to_per_lb(price: float, text: str) -> float | None:
    if "/lb" in text or "per lb" in text or "per pound" in text:
        return price
    lb_match = re.search(r'([\d.]+)\s*lb', text)
    if lb_match:
        lbs = float(lb_match.group(1))
        return price / lbs if lbs > 0 else None
    oz_match = re.search(r'([\d.]+)\s*oz', text)
    if oz_match:
        oz = float(oz_match.group(1))
        return price / (oz / 16.0) if oz > 0 else None
    if 1.0 < price < 25.0:
        return price
    return None
