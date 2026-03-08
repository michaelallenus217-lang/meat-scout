"""Firebase Firestore integration for price history."""

import os
from datetime import datetime, date
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

_db = None

# The 13 standard cuts we track
STANDARD_CUTS = [
    "Chicken Breast Boneless Skinless",
    "Chicken Thighs Boneless Skinless",
    "Whole Chicken",
    "Pork Tenderloin",
    "Pork Loin",
    "Pork Chops",
    "Ground Beef",
    "Chuck Roast",
    "Sirloin",
    "Salmon",
    "Shrimp",
    "Sole",
    "Flounder",
]

# Keywords to match scraped product names → standard cuts
# Order matters within each cut: first match wins
CUT_MATCHERS = {
    "Chicken Breast Boneless Skinless": {
        "require": ["chicken", "breast"],
        "bonus": ["boneless", "skinless"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
    "Chicken Thighs Boneless Skinless": {
        "require": ["chicken", "thigh"],
        "bonus": ["boneless", "skinless"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
    "Whole Chicken": {
        "require": ["whole", "chicken"],
        "bonus": [],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen", "breast", "thigh", "wing", "drum"],
    },
    "Pork Tenderloin": {
        "require": ["pork", "tenderloin"],
        "bonus": [],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
    "Pork Loin": {
        "require": ["pork", "loin"],
        "bonus": [],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen", "tenderloin"],
    },
    "Pork Chops": {
        "require": ["pork", "chop"],
        "bonus": [],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
    "Ground Beef": {
        "require": ["ground", "beef"],
        "bonus": [],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen", "turkey"],
    },
    "Chuck Roast": {
        "require": ["chuck", "roast"],
        "bonus": [],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
    "Sirloin": {
        "require": ["sirloin"],
        "bonus": ["steak"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen", "ground", "tip"],
    },
    "Salmon": {
        "require": ["salmon"],
        "bonus": ["fillet", "filet", "fresh", "atlantic", "sockeye", "wild"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen", "smoked", "jerky", "canned"],
    },
    "Shrimp": {
        "require": ["shrimp"],
        "bonus": ["raw", "peel", "fresh"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen", "cocktail", "popcorn", "breaded"],
    },
    "Sole": {
        "require": ["sole"],
        "bonus": ["fillet", "filet", "fresh"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
    "Flounder": {
        "require": ["flounder"],
        "bonus": ["fillet", "filet", "fresh"],
        "exclude": ["frozen", "freeze", "ice glazed", "previously frozen", "flash frozen", "iqf", "thaw", "keep frozen", "from frozen"],
    },
}


def get_db():
    """Get Firestore client, initializing Firebase if needed."""
    global _db
    if _db is not None:
        return _db

    cred_path = os.environ.get("FIREBASE_CREDENTIALS")
    if not cred_path:
        raise RuntimeError(
            "FIREBASE_CREDENTIALS not set in .env. "
            "Download your service account JSON from Firebase Console > "
            "Project Settings > Service Accounts > Generate New Private Key"
        )

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    _db = firestore.client()
    return _db


def match_cut(product_name: str) -> str | None:
    """Match a scraped product name to one of the 13 standard cuts.

    Returns the standard cut name or None if no match.
    """
    name = product_name.lower()

    for cut, matcher in CUT_MATCHERS.items():
        # Check excludes first
        if any(ex in name for ex in matcher["exclude"]):
            continue

        # All required keywords must be present
        if all(kw in name for kw in matcher["require"]):
            return cut

    return None


def save_prices(results: list[dict]) -> int:
    """Save scraped prices to Firestore. Returns count saved."""
    db = get_db()
    today = date.today().isoformat()
    batch = db.batch()
    count = 0

    for item in results:
        cut_name = match_cut(item.get("cut", ""))
        if not cut_name:
            continue

        doc_id = f"{today}_{item['store']}_{cut_name}".replace(" ", "_").replace("'", "")
        doc_ref = db.collection("prices").document(doc_id)

        batch.set(doc_ref, {
            "date": today,
            "store": item["store"],
            "standard_cut": cut_name,
            "original_name": item.get("cut", ""),
            "price_per_lb": item["price_per_lb"],
            "sale_end_date": item.get("sale_end_date"),
            "image_url": item.get("image_url"),
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
        count += 1

    if count > 0:
        batch.commit()

    return count


def _fetch_all_prices() -> list[dict]:
    """Fetch all price documents from Firestore (single query, no index needed)."""
    db = get_db()
    docs = db.collection("prices").stream()
    results = []
    for doc in docs:
        results.append(doc.to_dict())
    return results


def get_latest_prices() -> dict:
    """Get the most recent price for each cut at each store.

    Returns: {standard_cut: {store: {price_per_lb, date, original_name, ...}}}
    """
    all_docs = _fetch_all_prices()

    # Group by cut+store, keep most recent
    results = {cut: {} for cut in STANDARD_CUTS}

    for data in all_docs:
        cut = data.get("standard_cut")
        store = data.get("store")
        if cut not in results:
            continue

        existing = results[cut].get(store)
        if not existing or data.get("date", "") > existing.get("date", ""):
            results[cut][store] = {
                "price_per_lb": data["price_per_lb"],
                "date": data.get("date", ""),
                "original_name": data.get("original_name", ""),
                "sale_end_date": data.get("sale_end_date"),
                "image_url": data.get("image_url"),
            }

    return results


def get_all_history() -> dict:
    """Get price history for all cuts.

    Returns: {standard_cut: [{date, store, price_per_lb}, ...]}
    """
    all_docs = _fetch_all_prices()

    result = {cut: [] for cut in STANDARD_CUTS}

    for data in all_docs:
        cut = data.get("standard_cut")
        if cut not in result:
            continue
        result[cut].append({
            "date": data.get("date", ""),
            "store": data.get("store", ""),
            "price_per_lb": data.get("price_per_lb", 0),
        })

    for cut in result:
        result[cut].sort(key=lambda x: x["date"])

    return result
