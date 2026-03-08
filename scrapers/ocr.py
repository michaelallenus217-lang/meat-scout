"""OCR-based price extraction from weekly ad flyer images."""

import re
import subprocess
import tempfile
from pathlib import Path

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

MEAT_KEYWORDS = [
    "ground beef", "chicken breast", "chicken thigh", "chicken drumstick",
    "whole chicken", "pork chop", "pork loin", "pork shoulder",
    "ribeye", "rib eye", "new york strip", "ny strip", "sirloin",
    "t-bone", "filet mignon", "tenderloin", "flank steak", "chuck roast",
    "stew meat", "brisket", "tri-tip", "round steak",
    "beef", "chicken", "pork", "steak", "roast", "chop",
]


def ocr_image_url(image_url: str) -> str | None:
    """Download an image and run Tesseract OCR on it. Returns extracted text."""
    try:
        resp = httpx.get(image_url, headers=HEADERS, timeout=20, follow_redirects=True)
        resp.raise_for_status()

        # Determine file extension from content type
        content_type = resp.headers.get("content-type", "")
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "webp" in content_type:
            ext = ".webp"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(resp.content)
            tmp_path = f.name

        return ocr_file(tmp_path)

    except (httpx.HTTPError, httpx.TimeoutException):
        return None
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except (NameError, OSError):
            pass


def ocr_file(file_path: str) -> str | None:
    """Run Tesseract OCR on a local image file."""
    try:
        result = subprocess.run(
            ["tesseract", file_path, "stdout", "--psm", "6"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def extract_meat_prices(ocr_text: str, store_name: str) -> list[dict]:
    """Parse OCR text to find meat items and their prices."""
    if not ocr_text:
        return []

    results = []
    seen = set()

    # Strategy 1: Find lines with both a meat keyword AND a price on the same line
    # This is the most reliable approach for OCR'd flyers
    line_price = re.compile(r'\$\s*(\d{1,2}\.\d{2})\s*(?:/?\s*lb)?')

    for line in ocr_text.split("\n"):
        line_lower = line.lower().strip()
        if not line_lower:
            continue

        # Find price on this line
        price_match = line_price.search(line)
        if not price_match:
            continue

        price = float(price_match.group(1))
        if not (0.50 < price < 50.0):
            continue

        # Check if this line has a meat keyword
        for keyword in MEAT_KEYWORDS:
            if keyword in line_lower:
                cut_name = _clean_cut_name(keyword, line_lower)
                key = cut_name.lower()
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "store": store_name,
                        "cut": cut_name,
                        "price_per_lb": price,
                        "sale_end_date": None,
                    })
                break

    # Strategy 2: Meat keyword on one line, price on the next
    lines = ocr_text.split("\n")
    for i, line in enumerate(lines[:-1]):
        line_lower = line.lower().strip()
        next_line = lines[i + 1].strip()

        # This line has meat keyword but no price
        if line_price.search(line):
            continue  # already handled above

        for keyword in MEAT_KEYWORDS:
            if keyword not in line_lower:
                continue

            # Check next line for a price
            price_match = line_price.search(next_line)
            if not price_match:
                continue

            price = float(price_match.group(1))
            if 0.50 < price < 50.0:
                cut_name = _clean_cut_name(keyword, line_lower)
                key = cut_name.lower()
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "store": store_name,
                        "cut": cut_name,
                        "price_per_lb": price,
                        "sale_end_date": None,
                    })
            break

    # Strategy 3: Find "price /lb" patterns with preceding product names
    lb_pattern = re.compile(
        r'([^\n$]{3,40}?)\s*\$\s*(\d{1,2}\.\d{2})\s*/?\s*lb',
        re.IGNORECASE,
    )
    for match in lb_pattern.finditer(ocr_text):
        name = match.group(1).strip()
        price = float(match.group(2))
        if 0.50 < price < 50.0 and any(k in name.lower() for k in MEAT_KEYWORDS):
            cut_name = name.title().strip()
            key = cut_name.lower()
            if key not in seen:
                seen.add(key)
                results.append({
                    "store": store_name,
                    "cut": cut_name,
                    "price_per_lb": price,
                    "sale_end_date": None,
                })

    return results


def _clean_cut_name(keyword: str, line: str) -> str:
    """Extract a clean cut name from the OCR line."""
    # Try to get a reasonable product name from the line
    line = line.strip()
    # Remove price patterns
    cleaned = re.sub(r'\$?\d+\.\d{2}\s*/?\s*(?:lb|ea)?', '', line).strip()
    # Remove common junk
    cleaned = re.sub(r'[|•*©™®]', '', cleaned).strip()
    # If cleaned is too short or too long, fall back to keyword
    if len(cleaned) < 3 or len(cleaned) > 60:
        return keyword.title()
    return cleaned.title()
