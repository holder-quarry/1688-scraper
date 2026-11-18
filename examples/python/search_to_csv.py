"""Search 1688.com by keyword and write the offers to a CSV file: prices by quantity, MOQ, supplier.

    python search_to_csv.py KEYWORD [KEYWORD ...] [--pages 1] [--english] [--out offers.csv]

1688 is a Chinese site: Chinese keywords such as 手机壳 (phone case) find the most. One page is 60 offers;
1688 shows at most 3 pages (180) to a visitor. --english adds an English machine translation of each title.
Prices come in CNY and USD. The MOQ is taken from the first price tier, when 1688 shows tiers for the offer.
Set APIFY_TOKEN first (Apify Console > Settings > API & Integrations).
"""
import argparse
import csv
import os
import re
import sys
from decimal import Decimal

from apify_client import ApifyClient

ACTOR = "maksim_lazouski/1688-product-scraper"
COLUMNS = ["keyword", "position", "offer_id", "title", "title_en", "price", "price_usd", "price_by_quantity",
           "min_order", "sold", "repeat_buyers", "company", "supplier_years", "province", "city", "is_ad", "url"]


def tiers(row):
    """Price by quantity as one cell, e.g. "10~499个: 28 ($4.20); ≥2000个: 26.5 ($3.98)"."""
    parts = []
    for t in row.get("price_tiers") or []:
        qty = t.get("quantity") or f"≥{t.get('from_quantity')}"
        usd = f" (${t['price_usd']:.2f})" if t.get("price_usd") is not None else ""
        parts.append(f"{qty}: {t.get('price')}{usd}")
    return "; ".join(parts)


def min_order(row):
    """The smallest order: 1688's own MOQ text if the row has it, else the start of the first price tier."""
    if row.get("min_order_text") or row.get("min_order"):
        return row.get("min_order_text") or row.get("min_order")
    first = (row.get("price_tiers") or [{}])[0]
    match = re.match(r"\s*≥?\s*(\d+)", str(first.get("quantity") or first.get("from_quantity") or ""))
    return int(match.group(1)) if match else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Chinese text prints on any Windows console, pipe or log file
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Search 1688 by keyword to CSV.")
    parser.add_argument("keywords", nargs="+", help="search keywords")
    parser.add_argument("--pages", type=int, default=1, choices=[1, 2, 3], help="pages of 60 per keyword (default 1)")
    parser.add_argument("--english", action="store_true", help="add English titles ($0.10 per 1,000 rows)")
    parser.add_argument("--out", default="offers.csv", help="CSV file to write (default offers.csv)")
    parser.add_argument("--max-usd", type=Decimal, default=Decimal("1"),
                        help="the run stops when it has cost this much (default 1)")
    args = parser.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN first: Apify Console > Settings > API & Integrations.")

    client = ApifyClient(token)
    run = client.actor(ACTOR).call(
        run_input={"keywords": args.keywords, "maxPagesPerKeyword": args.pages, "translateTitles": args.english},
        max_total_charge_usd=args.max_usd,
    )
    if run is None:
        sys.exit("The run did not start.")
    if run.status != "SUCCEEDED":
        print(f"Warning: the run ended as {run.status}: {run.status_message or ''}", file=sys.stderr)

    count = 0
    # utf-8-sig so that Excel shows the Chinese titles right
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in client.dataset(run.default_dataset_id).iterate_items():
            if row.get("type") != "search_result":
                continue
            writer.writerow({
                "keyword": row.get("keyword"), "position": row.get("position"), "offer_id": row.get("offer_id"),
                "title": row.get("title"), "title_en": row.get("title_en"),
                "price": row.get("price"), "price_usd": row.get("price_usd"), "price_by_quantity": tiers(row),
                "min_order": min_order(row), "sold": row.get("sold_text"),
                "repeat_buyers": row.get("repeat_buyer_rate") or row.get("repurchase_rate"),
                "company": row.get("company"), "supplier_years": row.get("supplier_years"),
                "province": row.get("province"), "city": row.get("city"), "is_ad": row.get("is_ad"),
                "url": row.get("url"),
            })
            count += 1
    print(f"{count} offers written to {args.out}")


if __name__ == "__main__":
    main()
