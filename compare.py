"""Compare meat prices across stores and render output."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Keywords for categorizing items — order matters (first match wins)
CHICKEN_KW = [
    "chicken breast", "chicken thigh", "chicken drumstick", "chicken leg",
    "chicken wing", "whole chicken", "chicken",
]
BEEF_KW = [
    "ribeye", "rib eye", "new york strip", "ny strip", "sirloin",
    "t-bone", "filet mignon", "tenderloin", "flank", "chuck roast",
    "brisket", "tri-tip", "round steak", "beef roast", "prime rib",
    "cross rib", "beef steak", "beef",
]
PORK_KW = [
    "pork chop", "pork loin", "pork tenderloin", "pork shoulder",
    "baby back rib", "pork rib", "spare rib", "ham",
    "bacon", "pork",
]
PREMIUM_KW = [
    "salmon", "lobster", "crab", "shrimp", "scallop",
    "lamb chop", "lamb rack", "lamb leg", "lamb",
    "filet mignon", "prime rib", "ribeye", "rib eye",
    "new york strip", "ny strip",
    "steelhead", "halibut", "tuna", "swordfish", "cod",
    "rockfish", "mahi", "sea bass",
]

# Skip these — user wants whole cuts, not ground
SKIP_KW = ["ground beef", "ground turkey", "ground pork", "ground chuck",
            "meat frank", "hot dog", "sausage", "deli", "lunch meat",
            "ham,", "gouda", "cheese"]


def compare_prices(all_results: list[dict]) -> None:
    """Print categorized best deals."""
    console = Console()

    if not all_results:
        console.print("[bold red]No results found from any store.[/bold red]")
        return

    # Categorize and filter
    chicken, beef, pork, premium, other = [], [], [], [], []

    for item in all_results:
        name = item.get("cut", "").lower()

        # Skip ground meat and non-meat items
        if any(s in name for s in SKIP_KW):
            continue

        # Categorize (premium first since it overlaps with beef)
        if any(k in name for k in PREMIUM_KW):
            premium.append(item)
        if any(k in name for k in CHICKEN_KW):
            chicken.append(item)
        elif any(k in name for k in BEEF_KW):
            beef.append(item)
        elif any(k in name for k in PORK_KW):
            pork.append(item)

    # Sort each by price
    chicken.sort(key=lambda x: x["price_per_lb"])
    beef.sort(key=lambda x: x["price_per_lb"])
    pork.sort(key=lambda x: x["price_per_lb"])
    premium.sort(key=lambda x: x["price_per_lb"])

    console.print()
    console.rule("[bold]MEAT SCOUT — Best Deals Near JBLM[/bold]")
    console.print()

    _print_category(console, "BEST CHICKEN DEALS", chicken, top_n=5)
    _print_category(console, "BEST BEEF DEALS", beef, top_n=5)
    _print_category(console, "BEST PORK DEALS", pork, top_n=5)
    _print_category(console, "PREMIUM / SPECIAL OCCASION", premium, top_n=8)

    # Summary: best of each
    console.print()
    console.rule("[bold]TOP PICKS[/bold]")
    console.print()

    picks = []
    if chicken:
        picks.append(("Chicken", chicken[0]))
    if beef:
        picks.append(("Beef", beef[0]))
    if pork:
        picks.append(("Pork", pork[0]))
    if premium:
        picks.append(("Premium", premium[0]))

    for label, item in picks:
        store = item["store"]
        cut = item["cut"]
        price = item["price_per_lb"]
        sale = item.get("sale_end_date") or ""
        sale_str = f"  (sale ends {sale})" if sale else ""
        console.print(
            f"  [bold green]{label}:[/bold green] "
            f"[bold]{cut}[/bold] at [bold green]${price:.2f}/lb[/bold green] "
            f"— {store}{sale_str}"
        )

    console.print()


def _print_category(
    console: Console, title: str, items: list[dict], top_n: int = 5
) -> None:
    """Print a category table with the top N deals."""
    if not items:
        return

    table = Table(
        title=f"[bold]{title}[/bold]",
        show_lines=False,
        pad_edge=False,
        box=None,
    )
    table.add_column("Store", style="bold", min_width=18)
    table.add_column("Cut", min_width=30)
    table.add_column("$/lb", justify="right", min_width=8)
    table.add_column("Sale Ends", min_width=12)

    best_price = items[0]["price_per_lb"] if items else 999

    for item in items[:top_n]:
        price = item["price_per_lb"]
        is_best = price == best_price

        price_str = f"${price:.2f}"
        if is_best:
            store = f"[green]{item['store']}[/green]"
            cut = f"[green]{item['cut']}[/green]"
            price_str = f"[bold green]{price_str}[/bold green]"
            sale = f"[green]{item.get('sale_end_date') or '—'}[/green]"
        else:
            store = item["store"]
            cut = item["cut"]
            sale = item.get("sale_end_date") or "—"

        table.add_row(store, cut, price_str, sale)

    console.print(table)
    console.print()
