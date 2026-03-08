"""Shared web search fallback for stores that block direct scraping."""

import re
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MEAT_CUTS = [
    # Chicken
    "chicken breast", "chicken thigh", "chicken drumstick", "chicken wing",
    "whole chicken", "chicken leg",
    # Beef (whole cuts)
    "ribeye", "rib eye", "new york strip", "ny strip", "sirloin",
    "t-bone", "filet mignon", "tenderloin", "flank steak", "chuck roast",
    "brisket", "tri-tip", "round steak", "beef roast", "prime rib",
    # Pork
    "pork chop", "pork loin", "pork shoulder", "pork tenderloin",
    "baby back rib", "pork rib", "spare rib",
    # Premium / Seafood
    "salmon", "lobster", "crab", "shrimp", "scallop",
    "lamb chop", "lamb rack", "lamb leg",
]


def search_meat_prices(store_name: str, location: str = "Lakewood WA") -> list[dict]:
    """Search DuckDuckGo for current meat prices at a store."""
    results = []
    query = f"{store_name} {location} weekly ad meat prices per pound"

    try:
        resp = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract text from search result snippets
        snippets = soup.select(".result__snippet")
        for snippet in snippets:
            text = snippet.get_text(separator=" ").lower()
            results.extend(_extract_prices(text, store_name))

        # Also check result titles
        titles = soup.select(".result__title")
        for title in titles:
            text = title.get_text(separator=" ").lower()
            results.extend(_extract_prices(text, store_name))

    except (httpx.HTTPError, httpx.TimeoutException):
        pass

    # Deduplicate by cut name
    seen = set()
    deduped = []
    for r in results:
        key = r["cut"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped


def search_and_follow(store_name: str, location: str = "Lakewood WA") -> list[dict]:
    """Search DuckDuckGo, then follow top result links for detailed prices."""
    results = []
    query = f"{store_name} {location} weekly ad meat prices"

    try:
        resp = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Get top result URLs
        links = soup.select(".result__a")
        urls = []
        for link in links[:5]:
            href = link.get("href", "")
            # DuckDuckGo wraps URLs — extract the real one
            url_match = re.search(r'uddg=([^&]+)', href)
            if url_match:
                from urllib.parse import unquote
                urls.append(unquote(url_match.group(1)))
            elif href.startswith("http"):
                urls.append(href)

        # Follow each URL and try to extract prices
        for url in urls:
            try:
                page = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
                if page.status_code != 200:
                    continue
                page_soup = BeautifulSoup(page.text, "html.parser")
                page_text = page_soup.get_text(separator=" ").lower()
                results.extend(_extract_prices(page_text, store_name))
                if results:
                    break
            except (httpx.HTTPError, httpx.TimeoutException):
                continue

    except (httpx.HTTPError, httpx.TimeoutException):
        pass

    # Deduplicate
    seen = set()
    deduped = []
    for r in results:
        key = r["cut"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped


def _extract_prices(text: str, store_name: str) -> list[dict]:
    """Extract meat prices from a text block."""
    results = []

    # Multiple price patterns to catch different formats:
    # "$X.XX/lb", "$X.XX per lb", "$X.XX lb", "X.XX/lb", "price X.XX"
    price_patterns = [
        re.compile(r'\$(\d+\.?\d{0,2})\s*(?:/\s*lb|per\s+(?:lb|pound))', re.IGNORECASE),
        re.compile(r'(\d+\.\d{2})\s*(?:/\s*lb|per\s+(?:lb|pound))', re.IGNORECASE),
        re.compile(r'(?:price|sale|now|only)\s*\$?(\d+\.\d{2})', re.IGNORECASE),
        re.compile(r'\$(\d+\.\d{2})\s*(?:lb|ea)', re.IGNORECASE),
    ]

    for cut in MEAT_CUTS:
        if cut not in text:
            continue

        # Find all occurrences of this cut
        for match in re.finditer(re.escape(cut), text):
            cut_idx = match.start()
            window = text[max(0, cut_idx - 120):cut_idx + 120]

            for pattern in price_patterns:
                prices = pattern.findall(window)
                if prices:
                    try:
                        price = float(prices[0])
                        if 0.50 < price < 50.0:
                            sale_date = extract_sale_date(window)
                            results.append({
                                "store": store_name,
                                "cut": cut.title(),
                                "price_per_lb": price,
                                "sale_end_date": sale_date,
                            })
                            break  # found price for this occurrence
                    except ValueError:
                        continue

    return results


def extract_sale_date(text: str) -> str | None:
    """Try to extract a sale end date from text."""
    # Pattern: "through 3/10" or "ends 3/10" or "valid thru 3/10/26"
    date_pattern = re.compile(
        r'(?:through|thru|ends?|valid\s+(?:through|thru))\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
        re.IGNORECASE,
    )
    match = date_pattern.search(text)
    return match.group(1) if match else None
