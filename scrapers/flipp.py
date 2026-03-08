"""Flipp API client for fetching weekly ad prices near JBLM."""

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

POSTAL_CODE = "98499"  # Lakewood WA

MEAT_SEARCHES = [
    # Chicken
    "chicken breast", "chicken thigh", "whole chicken", "chicken drumstick",
    "chicken wing",
    # Beef (whole cuts, no ground)
    "steak", "ribeye", "sirloin", "filet mignon", "new york strip",
    "brisket", "tri-tip", "chuck roast", "beef roast",
    # Pork
    "pork chops", "pork loin", "pork tenderloin", "pork shoulder",
    "baby back ribs", "pork ribs",
    # Premium / Special Occasion
    "salmon", "lobster", "crab", "shrimp", "scallops",
    "lamb chops", "lamb rack", "prime rib",
]


def fetch_flipp_prices(merchant_name: str) -> list[dict]:
    """Fetch meat prices for a specific merchant from Flipp's API."""
    results = []
    seen = set()

    for term in MEAT_SEARCHES:
        try:
            resp = httpx.get(
                "https://backflipp.wishabi.com/flipp/items/search",
                params={
                    "locale": "en-us",
                    "postal_code": POSTAL_CODE,
                    "q": term,
                },
                headers=HEADERS,
                timeout=10,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()

            for item in data.get("items", []):
                name = (item.get("merchant_name") or "").strip()
                if name.lower() != merchant_name.strip().lower():
                    continue

                product_name = item.get("name", "").strip()
                price = item.get("current_price")
                post_price = (item.get("post_price_text") or "").lower()
                pre_price = (item.get("pre_price_text") or "").lower()
                sale_end = item.get("valid_to", "")

                if not product_name or not price:
                    continue

                # Deduplicate by product name
                key = product_name.lower()
                if key in seen:
                    continue
                seen.add(key)

                # Determine if price is per-lb or per-unit
                price_per_lb = _normalize_price(
                    price, post_price, pre_price, product_name.lower()
                )

                if price_per_lb and 0.50 < price_per_lb < 50.0:
                    # Format sale end date
                    sale_date = None
                    if sale_end:
                        sale_date = sale_end[:10]  # YYYY-MM-DD

                    results.append({
                        "store": name,
                        "cut": product_name,
                        "price_per_lb": round(price_per_lb, 2),
                        "sale_end_date": sale_date,
                        "image_url": item.get("clean_image_url") or item.get("clipping_image_url"),
                    })

        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            continue

    return results


def _normalize_price(
    price: float, post_text: str, pre_text: str, name: str
) -> float | None:
    """Normalize price to per-lb. Returns None if can't determine."""
    import re

    combined = f"{pre_text} {post_text} {name}"

    # If explicitly per-lb
    if any(x in combined for x in ["/lb", "per lb", "per pound"]):
        return price

    # Try to extract weight from product name (e.g. "7.5 Lbs", "16 oz")
    lb_match = re.search(r'([\d.]+)\s*lbs?\.?\s*(?:total)?', combined, re.IGNORECASE)
    if lb_match:
        lbs = float(lb_match.group(1))
        if lbs > 0:
            return price / lbs

    oz_match = re.search(r'([\d.]+)\s*oz\.?\s*(?:total)?', combined, re.IGNORECASE)
    if oz_match:
        oz = float(oz_match.group(1))
        # Check if there's a count (e.g. "20/6 Oz Per Steak" = 20 * 6 oz)
        count_match = re.search(r'(\d+)\s*/\s*' + re.escape(oz_match.group(0)), combined)
        if count_match:
            count = int(count_match.group(1))
            total_oz = count * oz
        else:
            total_oz = oz
        if total_oz > 0:
            return price / (total_oz / 16.0)

    # If explicitly per-ea and no weight indication, skip
    if "ea" in post_text and "lb" not in combined:
        return None

    # If "with card" pricing (Kroger/Fred Meyer), assume per-lb if text suggests
    if "with card" in combined and "/lb" not in combined:
        if any(x in name for x in ["ground", "breast", "thigh", "steak", "chop", "roast"]):
            return price

    return price
