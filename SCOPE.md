# Meat Scout — Project Scope

## Mission
Automated weekly meat price comparison across grocery stores near JBLM/Lakewood WA.
Delivers a categorized deal report via terminal, HTML flyer, and email.

## Features

### 1. Price Scraping (6 Stores)
| Store | Primary Source | Fallback | Notes |
|-------|---------------|----------|-------|
| Safeway | Flipp API | DuckDuckGo search | Weekly ad data with images |
| Fred Meyer | Flipp API | DuckDuckGo search | Weekly ad data with images |
| Costco | Flipp API | DuckDuckGo search | Bulk prices normalized to /lb |
| WinCo | Claude Vision (--scan photos) | DuckDuckGo search | No digital weekly ad |
| Trader Joe's | traderjoesprices.com | Known prices list | Blocks headless browsers |
| Stadium Thriftway | Playwright + Claude Vision | Local photos (--scan) | Red Pepper Digital flyer |

### 2. Price Comparison (Terminal)
- Categorized output: Chicken, Beef, Pork, Premium/Special Occasion
- Filters out ground meat, hot dogs, sausage, deli, cheese
- Best deal per category highlighted green
- Top Picks summary

### 3. HTML Flyer Generation (--flyer)
- Grocery circular-style layout with product image cards
- 2-column grid per category with "BEST DEAL" badges
- Images: Flipp product photos (primary), Unsplash (fallback)
- Saves to flyer.html for browser preview

### 4. Email Delivery (--email)
- Gmail SMTP with app password authentication
- HTML flyer as email body with plain-text fallback
- Send to self (default) or any address

### 5. Automated Weekly Schedule
- Cron job: every Friday at 0700 PT
- Runs full scrape → generates flyer → emails → logs to CSV
- Output logged to cron.log

### 6. Photo Scanning (--scan)
- Claude Vision (Sonnet) analyzes in-store photos
- Supports: WinCo green tags, any store's shelf labels
- Photos stored in scans/{store}/ directories

### 7. Price History (--history, --log)
- CSV logging: date, store, cut, price_per_lb, sale_end_date
- 30-day trend view from accumulated data

## CLI Interface
```
python main.py                              # Full comparison, all stores
python main.py --store safeway              # Single store
python main.py --flyer                      # Generate HTML flyer
python main.py --email                      # Scrape + email flyer to yourself
python main.py --email user@gmail.com       # Email to specific address
python main.py --scan photo.jpg --store winco  # Analyze store photo
python main.py --log                        # Append results to CSV
python main.py --history                    # Show 30-day price trends
```

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| HTTP | httpx |
| HTML parsing | beautifulsoup4 |
| Terminal UI | rich |
| Image analysis | Anthropic Claude Vision (Sonnet) |
| Browser automation | Playwright (Thriftway only) |
| Email | smtplib (Gmail SMTP_SSL) |
| Config | python-dotenv |
| Scheduling | System crontab |

## File Structure
```
meat-scout/
├── main.py              # CLI entry point
├── compare.py           # Categorized price comparison + terminal output
├── flyer.py             # HTML email flyer generator
├── emailer.py           # Gmail SMTP sender
├── logger.py            # CSV logging + history viewer
├── weekly_flyer.sh      # Cron wrapper script
├── scrapers/
│   ├── __init__.py      # Scraper registry
│   ├── flipp.py         # Flipp API client (Safeway, Fred Meyer, Costco)
│   ├── search.py        # DuckDuckGo fallback + price regex
│   ├── vision.py        # Claude Vision API wrapper
│   ├── browser.py       # Playwright automation
│   ├── safeway.py       # Safeway scraper
│   ├── fredmeyer.py     # Fred Meyer scraper
│   ├── costco.py        # Costco scraper
│   ├── winco.py         # WinCo scraper
│   ├── traderjoes.py    # Trader Joe's scraper
│   └── thriftway.py     # Stadium Thriftway scraper
├── scans/               # User photos for Vision (gitignored)
├── .env                 # API keys (gitignored)
├── .env.example         # Template for new users
├── .gitignore
├── CLAUDE.md            # Project context for AI
├── SCOPE.md             # This file
└── prices.csv           # Price log (gitignored)
```

## Data Flow
```
Flipp API ──────────┐
DuckDuckGo search ──┤
Claude Vision ──────┤──→ normalize to $/lb ──→ categorize ──→ terminal output
Playwright+Vision ──┤                                    ├──→ HTML flyer
Known prices ───────┘                                    ├──→ email
                                                         └──→ CSV log
```

## Constraints
- All prices normalized to $/lb
- No ground meat, hot dogs, sausage, deli in output
- Playwright used ONLY for Stadium Thriftway
- .env never committed (contains API keys)
- Price sanity check: $0.50 < price < $50.00/lb
