"""Meat Scout — Flask web dashboard."""

import threading
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from flask import Flask, render_template, jsonify

from scrapers import SCRAPERS, EVERYDAY
from firebase_db import (
    save_prices,
    get_latest_prices,
    get_all_history,
    match_cut,
    STANDARD_CUTS,
)
from flyer import generate_flyer
from emailer import send_flyer_email

app = Flask(__name__)

_scrape_status = {"running": False, "last_run": None, "message": ""}

STORES = ["Safeway", "Fred Meyer", "WinCo", "Costco", "Trader Joe's", "Stadium Thriftway", "Commissary (JBLM)"]


@app.route("/")
def dashboard():
    return render_template("dashboard.html", cuts=STANDARD_CUTS, stores=STORES)


@app.route("/api/prices")
def api_prices():
    """Get latest everyday prices for the dashboard grid."""
    try:
        prices = get_latest_prices()
        return jsonify({"ok": True, "prices": prices})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/history")
def api_history():
    """Get price history for charts."""
    try:
        history = get_all_history()
        return jsonify({"ok": True, "history": history})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Refresh everyday prices from all stores and save to Firebase."""
    if _scrape_status["running"]:
        return jsonify({"ok": False, "error": "Already running"}), 409

    thread = threading.Thread(target=_run_everyday_refresh)
    thread.start()
    return jsonify({"ok": True, "message": "Refreshing everyday prices..."})


@app.route("/api/send-deals", methods=["POST"])
def api_send_deals():
    """Scrape sale/ad deals from all stores and email the flyer."""
    if _scrape_status["running"]:
        return jsonify({"ok": False, "error": "Already running"}), 409

    thread = threading.Thread(target=_run_send_deals)
    thread.start()
    return jsonify({"ok": True, "message": "Scraping deals and sending email..."})


@app.route("/api/status")
def api_status():
    return jsonify(_scrape_status)


def _run_everyday_refresh():
    """Load everyday prices from all stores and save to Firebase."""
    global _scrape_status
    _scrape_status = {"running": True, "last_run": None, "message": "Loading everyday prices..."}

    all_results = []
    for name, price_fn in EVERYDAY.items():
        _scrape_status["message"] = f"Loading {name} everyday prices..."
        try:
            results = price_fn()
            all_results.extend(results)
        except Exception as e:
            print(f"Error loading {name}: {e}")

    _scrape_status["message"] = "Saving to Firebase..."
    try:
        count = save_prices(all_results)
        _scrape_status = {
            "running": False,
            "last_run": date.today().isoformat(),
            "message": f"Done — {count} everyday prices saved.",
        }
    except Exception as e:
        _scrape_status = {
            "running": False,
            "last_run": None,
            "message": f"Error saving: {e}",
        }


def _run_send_deals():
    """Scrape sale deals and email the flyer."""
    global _scrape_status
    _scrape_status = {"running": True, "last_run": None, "message": "Scraping sale deals..."}

    all_results = []
    for name, scraper_fn in SCRAPERS.items():
        _scrape_status["message"] = f"Scanning {name} for deals..."
        try:
            results = scraper_fn()
            all_results.extend(results)
        except Exception as e:
            print(f"Error scraping {name}: {e}")

    _scrape_status["message"] = "Generating flyer..."
    try:
        html = generate_flyer(all_results)
        _scrape_status["message"] = "Sending email..."
        success = send_flyer_email(html)
        if success:
            _scrape_status = {
                "running": False,
                "last_run": date.today().isoformat(),
                "message": f"Deals email sent! ({len(all_results)} items found)",
            }
        else:
            _scrape_status = {
                "running": False,
                "last_run": None,
                "message": "Email failed — check Gmail credentials in .env",
            }
    except Exception as e:
        _scrape_status = {
            "running": False,
            "last_run": None,
            "message": f"Error: {e}",
        }


if __name__ == "__main__":
    app.run(debug=True, port=5050)
