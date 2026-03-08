"""Generate a weekly flyer HTML email from meat-scout results."""

import os
from datetime import date

# Fallback images by category (Unsplash direct links — no API key needed)
FALLBACK_IMAGES = {
    "chicken": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400&h=300&fit=crop",
    "beef": "https://images.unsplash.com/photo-1588168333986-5078d3ae3976?w=400&h=300&fit=crop",
    "pork": "https://images.unsplash.com/photo-1432139509613-5c4255a1d197?w=400&h=300&fit=crop",
    "salmon": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=400&h=300&fit=crop",
    "shrimp": "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=400&h=300&fit=crop",
    "lobster": "https://images.unsplash.com/photo-1553247407-23251ce81f59?w=400&h=300&fit=crop",
    "steak": "https://images.unsplash.com/photo-1600891964092-4316c288032e?w=400&h=300&fit=crop",
    "lamb": "https://images.unsplash.com/photo-1608039829572-97381f5bc57e?w=400&h=300&fit=crop",
    "ribs": "https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop",
    "crab": "https://images.unsplash.com/photo-1510130113-7437ce4da639?w=400&h=300&fit=crop",
    "scallop": "https://images.unsplash.com/photo-1599084993091-1cb5c0721cc6?w=400&h=300&fit=crop",
    "default": "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=400&h=300&fit=crop",
}

# Category keywords (same as compare.py)
CHICKEN_KW = ["chicken", "whole chicken"]
BEEF_KW = ["ribeye", "rib eye", "new york strip", "ny strip", "sirloin", "t-bone",
           "filet mignon", "tenderloin", "flank", "chuck roast", "brisket", "tri-tip",
           "cross rib", "beef steak", "beef roast", "prime rib", "beef"]
PORK_KW = ["pork chop", "pork loin", "pork tenderloin", "pork shoulder",
           "baby back rib", "pork rib", "spare rib", "bacon", "ham", "pork"]
PREMIUM_KW = ["salmon", "lobster", "crab", "shrimp", "scallop", "lamb",
              "filet mignon", "prime rib", "ribeye", "rib eye", "new york strip",
              "steelhead", "halibut", "tuna", "swordfish", "cod", "rockfish",
              "mahi", "sea bass"]
SKIP_KW = ["ground beef", "ground turkey", "ground pork", "ground chuck",
           "meat frank", "hot dog", "sausage", "deli", "lunch meat",
           "gouda", "cheese"]


def generate_flyer(all_results: list[dict]) -> str:
    """Generate HTML flyer email from results."""
    today = date.today()
    week_str = today.strftime("%B %d, %Y")

    # Filter and categorize
    chicken, beef, pork, premium = [], [], [], []
    for item in all_results:
        name = item.get("cut", "").lower()
        if any(s in name for s in SKIP_KW):
            continue
        if any(k in name for k in PREMIUM_KW):
            premium.append(item)
        if any(k in name for k in CHICKEN_KW):
            chicken.append(item)
        elif any(k in name for k in BEEF_KW):
            beef.append(item)
        elif any(k in name for k in PORK_KW):
            pork.append(item)

    chicken.sort(key=lambda x: x["price_per_lb"])
    beef.sort(key=lambda x: x["price_per_lb"])
    pork.sort(key=lambda x: x["price_per_lb"])
    premium.sort(key=lambda x: x["price_per_lb"])

    # Build top picks
    picks = []
    if chicken:
        picks.append(("CHICKEN", chicken[0]))
    if beef:
        picks.append(("BEEF", beef[0]))
    if pork:
        picks.append(("PORK", pork[0]))
    if premium:
        picks.append(("PREMIUM", premium[0]))

    html = f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meat Scout Weekly Deals — {week_str}</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f4f4; font-family: 'Helvetica Neue', Arial, sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;">
<tr><td align="center" style="padding: 20px 0;">
<table width="640" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

  <!-- HEADER -->
  <tr>
    <td style="background: linear-gradient(135deg, #1a472a, #2d8a4e); padding: 30px 40px; text-align:center;">
      <h1 style="color:#ffffff; margin:0; font-size:32px; letter-spacing:1px;">MEAT SCOUT</h1>
      <p style="color:#a8d5ba; margin:8px 0 0; font-size:14px; letter-spacing:2px;">WEEKLY DEALS NEAR JBLM &bull; {week_str.upper()}</p>
    </td>
  </tr>

  <!-- TOP PICKS BANNER -->
  <tr>
    <td style="background-color:#fff3cd; padding:20px 40px; border-bottom: 2px solid #ffc107;">
      <h2 style="margin:0 0 12px; color:#856404; font-size:18px;">THIS WEEK'S TOP PICKS</h2>
      {_render_top_picks(picks)}
    </td>
  </tr>

  <!-- CHICKEN -->
  {_render_section("Best Chicken Deals", "#e8f5e9", "#2e7d32", chicken[:4])}

  <!-- BEEF -->
  {_render_section("Best Beef Deals", "#fce4ec", "#c62828", beef[:4])}

  <!-- PORK -->
  {_render_section("Best Pork Deals", "#fff3e0", "#e65100", pork[:4])}

  <!-- PREMIUM -->
  {_render_section("Premium / Special Occasion", "#e3f2fd", "#1565c0", premium[:6])}

  <!-- FOOTER -->
  <tr>
    <td style="background-color:#333; padding:20px 40px; text-align:center;">
      <p style="color:#999; font-size:12px; margin:0;">
        Prices sourced from Flipp, store websites, and in-store flyers.<br>
        Prices may vary by location. Generated by Meat Scout.
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return html


def _render_top_picks(picks: list[tuple[str, dict]]) -> str:
    """Render the top picks summary."""
    rows = []
    for label, item in picks:
        rows.append(
            f'<p style="margin:4px 0; font-size:15px;">'
            f'<strong style="color:#856404;">{label}:</strong> '
            f'{item["cut"]} — <strong style="color:#2e7d32;">${item["price_per_lb"]:.2f}/lb</strong> '
            f'at {item["store"]}'
            f'</p>'
        )
    return "\n".join(rows)


def _render_section(title: str, bg_color: str, accent: str, items: list[dict]) -> str:
    """Render a category section with product cards."""
    if not items:
        return ""

    cards = []
    for i, item in enumerate(items):
        img_url = _get_image(item)
        is_best = i == 0
        badge = f'<span style="background:{accent}; color:#fff; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:bold;">BEST DEAL</span>' if is_best else ""
        sale = item.get("sale_end_date")
        sale_str = f'<span style="color:#999; font-size:11px;">Sale ends {sale}</span>' if sale else ""

        cards.append(f"""\
      <td width="50%" style="padding:8px; vertical-align:top;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff; border-radius:6px; overflow:hidden; border:1px solid #e0e0e0;">
          <tr>
            <td style="height:140px; background:url('{img_url}') center/cover no-repeat; position:relative;">
              &nbsp;
            </td>
          </tr>
          <tr>
            <td style="padding:10px 12px;">
              {badge}
              <p style="margin:4px 0 2px; font-size:13px; font-weight:bold; color:#333;">{item["cut"]}</p>
              <p style="margin:0; font-size:11px; color:#666;">{item["store"]}</p>
              <p style="margin:6px 0 2px; font-size:22px; font-weight:bold; color:{accent};">${item["price_per_lb"]:.2f}<span style="font-size:12px; color:#999;">/lb</span></p>
              {sale_str}
            </td>
          </tr>
        </table>
      </td>""")

    # Arrange in 2-column grid
    rows_html = []
    for i in range(0, len(cards), 2):
        pair = cards[i:i + 2]
        if len(pair) == 1:
            pair.append('<td width="50%">&nbsp;</td>')
        rows_html.append(f"<tr>{''.join(pair)}</tr>")

    return f"""\
  <tr>
    <td style="background-color:{bg_color}; padding:20px 30px;">
      <h2 style="margin:0 0 12px; color:{accent}; font-size:18px; border-bottom:2px solid {accent}; padding-bottom:6px;">{title}</h2>
      <table width="100%" cellpadding="0" cellspacing="0">
        {''.join(rows_html)}
      </table>
    </td>
  </tr>"""


def _get_image(item: dict) -> str:
    """Get the best image URL for an item."""
    # Flipp image first
    img = item.get("image_url")
    if img:
        return img

    # Fallback to category-matched Unsplash photo
    name = item.get("cut", "").lower()
    for keyword, url in FALLBACK_IMAGES.items():
        if keyword in name:
            return url

    # Category-level fallback
    if any(k in name for k in CHICKEN_KW):
        return FALLBACK_IMAGES["chicken"]
    if any(k in name for k in ["salmon", "steelhead"]):
        return FALLBACK_IMAGES["salmon"]
    if any(k in name for k in ["shrimp"]):
        return FALLBACK_IMAGES["shrimp"]
    if any(k in name for k in ["lobster"]):
        return FALLBACK_IMAGES["lobster"]
    if any(k in name for k in ["crab"]):
        return FALLBACK_IMAGES["crab"]
    if any(k in name for k in ["lamb"]):
        return FALLBACK_IMAGES["lamb"]
    if any(k in name for k in ["rib"]):
        return FALLBACK_IMAGES["ribs"]
    if any(k in name for k in PORK_KW):
        return FALLBACK_IMAGES["pork"]
    if any(k in name for k in BEEF_KW):
        return FALLBACK_IMAGES["steak"]

    return FALLBACK_IMAGES["default"]
