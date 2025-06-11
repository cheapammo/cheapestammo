#!/usr/bin/env python3
"""
Combine ammunition pricing CSVs into a single master feed.

Scans the current directory for any files that match the pattern `*_prices*.csv` as well as
`direct_retailer_prices.csv`, normalises their columns, removes obvious duplicates,
and writes the consolidated data to `all_prices.csv` (overwriting if it exists).

The output schema matches the admin dashboard:
    name,caliber,price,quantity,price_per_round,retailer,source,in_stock,url,scraped_at

Run simply with:
    python combine_prices.py
"""
import csv
import glob
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Canonical column order expected by the dashboard
COLUMNS = [
    "name",
    "caliber",
    "price",
    "quantity",
    "price_per_round",
    "retailer",
    "source",
    "in_stock",
    "url",
    "scraped_at",
]

def discover_input_files() -> List[Path]:
    patterns = ["*_prices*.csv", "direct_retailer_prices.csv"]
    files: List[Path] = []
    for pat in patterns:
        for path in Path(".").glob(pat):
            if path.is_file():
                files.append(path)
    return sorted(files)

def normalise_row(row: Dict[str, str]) -> Dict[str, str]:
    """Ensure every column is present and trimmed; provide sane defaults."""
    norm: Dict[str, str] = {}
    for col in COLUMNS:
        value = row.get(col, "")
        if isinstance(value, str):
            value = value.strip()
        norm[col] = value
    # Guarantee boolean strings are just True/False
    in_stock_val = norm["in_stock"].lower()
    if in_stock_val in {"true", "1", "yes", "y"}:
        norm["in_stock"] = "True"
    elif in_stock_val in {"false", "0", "no", "n"}:
        norm["in_stock"] = "False"
    # Fill scraped_at if missing
    if not norm["scraped_at"]:
        norm["scraped_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return norm

def unique_key(row: Dict[str, str]) -> Tuple[str, str, str]:
    """Return a tuple used to de-duplicate rows (url, retailer, price)."""
    return (row.get("url", ""), row.get("retailer", ""), row.get("price", ""))

def combine_files(files: List[Path]) -> List[Dict[str, str]]:
    all_rows: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    for path in files:
        try:
            with path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for raw_row in reader:
                    if not raw_row:
                        continue
                    row = normalise_row(raw_row)
                    key = unique_key(row)
                    if key in seen:
                        continue
                    seen.add(key)
                    all_rows.append(row)
        except Exception as e:
            print(f"[!] Skipping {path.name}: {e}")
    return all_rows

def save_output(rows: List[Dict[str, str]]):
    out_path = Path("all_prices.csv")
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[✓] Wrote {len(rows)} rows → {out_path}")

def main():
    files = discover_input_files()
    if not files:
        print("[!] No input CSVs found. Run scrapers first.")
        return
    print("[+] Combining the following files:")
    for f in files:
        print("   •", f.name)
    rows = combine_files(files)
    if not rows:
        print("[!] No rows combined – empty inputs?")
        return
    save_output(rows)

if __name__ == "__main__":
    main() 