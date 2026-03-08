# Meat Scout — Project Context

## Purpose
CLI tool to compare weekly meat sale prices across grocery stores near JBLM/Lakewood WA.
Generates categorized deal reports, HTML flyer emails, and price history.

## Stores
Safeway, Fred Meyer, WinCo, Costco, Trader Joe's, Stadium Thriftway

## Tech Stack
- Python 3.11+ (venv in .venv/)
- httpx for HTTP requests
- beautifulsoup4 for HTML parsing
- rich for terminal table output
- anthropic SDK + Claude Vision (Sonnet) for image price extraction
- playwright (Chromium) for Stadium Thriftway only (Red Pepper Digital flyer)
- python-dotenv for env var management
- smtplib for Gmail SMTP email delivery
- System crontab for weekly scheduling

## API Keys & Credentials
- `.env` contains ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD (gitignored)
- `.env.example` is the template for new users
- SHARE REMINDER: Before sharing this repo, verify `.env` is NOT committed

## Project Structure
meat-scout/
├── main.py              — CLI entry point (--store, --flyer, --email, --scan, --log, --history)
├── compare.py           — Categorized price comparison + terminal output
├── flyer.py             — HTML email flyer generator (product cards, Flipp/Unsplash images)
├── emailer.py           — Gmail SMTP sender (app password auth)
├── logger.py            — CSV logging + 30-day history viewer
├── weekly_flyer.sh      — Cron wrapper (Friday 0700 PT)
├── scrapers/
│   ├── __init__.py      — Scraper registry
│   ├── flipp.py         — Flipp API client (Safeway, Fred Meyer, Costco)
│   ├── search.py        — DuckDuckGo HTML search fallback
│   ├── vision.py        — Claude Vision API wrapper
│   ├── browser.py       — Playwright browser automation
│   ├── safeway.py       — Flipp API → search fallback
│   ├── fredmeyer.py     — Flipp API → search fallback
│   ├── costco.py        — Flipp API → search fallback (bulk price normalization)
│   ├── winco.py         — Claude Vision (local photos) → search fallback
│   ├── traderjoes.py    — traderjoesprices.com → search → known prices fallback
│   └── thriftway.py     — Playwright + Vision → local photos → search
├── scans/               — User photos for Vision (per-store subdirs, gitignored)
├── .env / .env.example
└── prices.csv           — Price log (gitignored)

## Data Sources
- Safeway, Fred Meyer, Costco: Flipp API (backflipp.wishabi.com) — weekly ad data + product images
- Trader Joe's: Known everyday prices (TJ's blocks headless browsers). No Playwright.
- WinCo: In-store green tags only — use --scan with photos
- Stadium Thriftway: Playwright renders Red Pepper Digital flyer → Claude Vision extracts prices

## CLI Flags
- python main.py                              — full comparison all stores
- python main.py --store safeway              — single store
- python main.py --flyer                      — generate HTML flyer (saves flyer.html)
- python main.py --email                      — scrape + email flyer to yourself
- python main.py --email user@example.com     — email to specific address
- python main.py --scan photo.jpg --store winco — analyze photo with Claude Vision
- python main.py --log                        — append results to prices.csv
- python main.py --history                    — show 30-day trend from CSV

## Output Categories (no ground meat)
- BEST CHICKEN DEALS — breast, thigh, drumstick, whole, wings
- BEST BEEF DEALS — steaks, roasts, brisket (whole cuts only)
- BEST PORK DEALS — chops, loin, tenderloin, ribs, shoulder
- PREMIUM / SPECIAL OCCASION — ribeye, filet, salmon, lobster, crab, shrimp, lamb
- TOP PICKS — single best deal from each category

## Constraints
- All prices normalized to $/lb
- Playwright used ONLY for Stadium Thriftway
- Price sanity check: $0.50 < price/lb < $50.00
