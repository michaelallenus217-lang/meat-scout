"""CSV logger for price history tracking."""

import csv
from datetime import date
from pathlib import Path

CSV_PATH = Path(__file__).parent / "prices.csv"
FIELDNAMES = ["date", "store", "cut", "price_per_lb", "sale_end_date"]


def log_results(results: list[dict]) -> None:
    """Append results to prices.csv."""
    file_exists = CSV_PATH.exists()

    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        today = date.today().isoformat()
        for item in results:
            writer.writerow({
                "date": today,
                "store": item.get("store", ""),
                "cut": item.get("cut", ""),
                "price_per_lb": item.get("price_per_lb", ""),
                "sale_end_date": item.get("sale_end_date", ""),
            })


def show_history(days: int = 30) -> None:
    """Print 30-day price trend from CSV."""
    from rich.console import Console
    from rich.table import Table
    from datetime import timedelta

    console = Console()

    if not CSV_PATH.exists():
        console.print("[bold red]No price history found. Run with --log first.[/bold red]")
        return

    cutoff = (date.today() - timedelta(days=days)).isoformat()

    rows = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] >= cutoff:
                rows.append(row)

    if not rows:
        console.print(f"[yellow]No data in the last {days} days.[/yellow]")
        return

    table = Table(title=f"Price History (last {days} days)", show_lines=True)
    table.add_column("Date")
    table.add_column("Store", style="bold")
    table.add_column("Cut")
    table.add_column("Price/lb", justify="right")

    for row in rows:
        table.add_row(row["date"], row["store"], row["cut"], f"${float(row['price_per_lb']):.2f}")

    console.print(table)
