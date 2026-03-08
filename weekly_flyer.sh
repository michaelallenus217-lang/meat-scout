#!/bin/bash
# Meat Scout — weekly flyer email (Friday 0700 PT)
cd "$(dirname "$0")"
.venv/bin/python main.py --email --log
