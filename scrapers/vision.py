"""Claude Vision API for extracting meat prices from images."""

import base64
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

EXTRACTION_PROMPT = """You are analyzing a grocery store flyer/ad image or a photo of in-store price tags.

Extract ALL meat and seafood prices you can see. Include:
- Chicken (breast, thigh, drumstick, whole, wings)
- Beef (steaks, roasts, brisket, ribs — skip ground beef)
- Pork (chops, loin, tenderloin, ribs, shoulder)
- Premium/Seafood (salmon, lobster, crab, shrimp, scallops, lamb)

For each item, provide:
- name: the product name/cut (e.g. "Boneless Skinless Chicken Breast")
- price_per_lb: the price per pound as a number (e.g. 4.99). If the price is per package, estimate the per-lb price from the weight shown. If you can't determine per-lb, use the listed price.
- sale_end_date: the sale end date if visible (e.g. "2026-03-11"), or null

Return ONLY a JSON array, no other text. Example:
[
  {"name": "Atlantic Salmon Fillet", "price_per_lb": 8.99, "sale_end_date": "2026-03-11"},
  {"name": "Chicken Breast", "price_per_lb": 2.49, "sale_end_date": null}
]

If no meat/seafood prices are visible, return an empty array: []"""


def analyze_image(image_path: str, store_name: str) -> list[dict]:
    """Send an image to Claude Vision and extract meat prices."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Read and encode the image
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Determine media type
        suffix = img_path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        media_type = media_types.get(suffix, "image/jpeg")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        # Parse the JSON response
        response_text = message.content[0].text.strip()
        # Handle markdown code blocks
        if response_text.startswith("```"):
            response_text = re.sub(r"^```\w*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        items = json.loads(response_text)

        results = []
        for item in items:
            price = item.get("price_per_lb")
            if price and 0.50 < float(price) < 50.0:
                results.append({
                    "store": store_name,
                    "cut": item.get("name", "Unknown"),
                    "price_per_lb": round(float(price), 2),
                    "sale_end_date": item.get("sale_end_date"),
                })

        return results

    except Exception:
        return []


def analyze_screenshot(screenshot_bytes: bytes, store_name: str) -> list[dict]:
    """Analyze a Playwright screenshot (bytes) with Claude Vision."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        img_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r"^```\w*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        items = json.loads(response_text)

        results = []
        for item in items:
            price = item.get("price_per_lb")
            if price and 0.50 < float(price) < 50.0:
                results.append({
                    "store": store_name,
                    "cut": item.get("name", "Unknown"),
                    "price_per_lb": round(float(price), 2),
                    "sale_end_date": item.get("sale_end_date"),
                })

        return results

    except Exception:
        return []
