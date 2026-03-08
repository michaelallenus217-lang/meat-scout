#!/usr/bin/env python3
"""Meat Scout — compare weekly meat sale prices near JBLM."""

import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from scrapers import SCRAPERS
from compare import compare_prices
from logger import log_results, show_history
from flyer import generate_flyer
from emailer import send_flyer_email

SCAN_BASE = Path(__file__).parent / "scans"

STORE_SCAN_DIRS = {
    "winco": SCAN_BASE / "winco",
    "thriftway": SCAN_BASE / "thriftway",
    "safeway": SCAN_BASE / "safeway",
    "fredmeyer": SCAN_BASE / "fredmeyer",
    "traderjoes": SCAN_BASE / "traderjoes",
    "costco": SCAN_BASE / "costco",
    "commissary": SCAN_BASE / "commissary",
}


def main():
    parser = argparse.ArgumentParser(description="Compare meat prices near JBLM")
    parser.add_argument("--store", choices=list(SCRAPERS.keys()), help="Single store only")
    parser.add_argument("--log", action="store_true", help="Append results to prices.csv")
    parser.add_argument("--history", action="store_true", help="Show 30-day price trend")
    parser.add_argument(
        "--scan",
        nargs="+",
        metavar="IMAGE",
        help="Analyze photos of in-store ads with Claude Vision. Use with --store.",
    )
    parser.add_argument("--flyer", action="store_true", help="Generate HTML flyer and save to flyer.html")
    parser.add_argument("--email", metavar="ADDRESS", nargs="?", const="self",
                        help="Email the flyer (default: send to yourself)")
    args = parser.parse_args()

    if args.history:
        show_history()
        return

    # Warn if API key is missing and vision features are needed
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Note: ANTHROPIC_API_KEY not set in .env — Claude Vision disabled.")
        print("  Copy .env.example to .env and add your key for full functionality.\n")

    # Handle --scan: copy images into the store's scan directory
    if args.scan:
        store = args.store or _guess_store(args.scan)
        if not store:
            print("Use --store to specify which store these photos are from.")
            print("  Example: python main.py --scan photo.jpg --store winco")
            return

        scan_dir = STORE_SCAN_DIRS.get(store, SCAN_BASE / store)
        scan_dir.mkdir(parents=True, exist_ok=True)

        for img_path in args.scan:
            src = Path(img_path)
            if not src.exists():
                print(f"File not found: {img_path}")
                continue
            dest = scan_dir / src.name
            shutil.copy2(src, dest)
            print(f"Copied {src.name} -> scans/{store}/")

        print(f"Analyzing {store} photos with Claude Vision...")

    if args.store:
        scrapers_to_run = {args.store: SCRAPERS[args.store]}
    else:
        scrapers_to_run = SCRAPERS

    all_results = []
    for name, scraper_fn in scrapers_to_run.items():
        print(f"Scanning {name}...")
        results = scraper_fn()
        all_results.extend(results)

    compare_prices(all_results)

    if args.flyer or args.email:
        html = generate_flyer(all_results)
        if args.flyer:
            out = Path(__file__).parent / "flyer.html"
            out.write_text(html)
            print(f"Flyer saved to {out}")
        if args.email:
            to_addr = None if args.email == "self" else args.email
            send_flyer_email(html, to_addr)

    if args.log:
        log_results(all_results)
        print(f"Logged {len(all_results)} results to prices.csv")


def _guess_store(image_paths: list[str]) -> str | None:
    """Try to guess store from filename."""
    combined = " ".join(image_paths).lower()
    for store in STORE_SCAN_DIRS:
        if store in combined:
            return store
    return None


if __name__ == "__main__":
    main()
