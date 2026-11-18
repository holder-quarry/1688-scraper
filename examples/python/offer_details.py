"""Get full 1688 offers: prices by quantity, every variant with stock, supplier, ratings, dropshipping terms.

    python offer_details.py OFFER [OFFER ...] [--english] [--out offers.jsonl]

OFFER is an offer link such as https://detail.1688.com/offer/762640272016.html, or just the id.
Each offer row has about 100 fields; see sample/offer.json.
Set APIFY_TOKEN first (Apify Console > Settings > API & Integrations).
"""
import argparse
import json
import os
import sys
from decimal import Decimal

from apify_client import ApifyClient

ACTOR = "maksim_lazouski/1688-product-scraper"


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Chinese text prints on any Windows console, pipe or log file
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Get full 1688 offers.")
    parser.add_argument("offers", nargs="+", help="offer links or ids")
    parser.add_argument("--english", action="store_true", help="add English titles ($0.10 per 1,000 rows)")
    parser.add_argument("--out", default="offers.jsonl", help="JSON lines file to write (default offers.jsonl)")
    parser.add_argument("--max-usd", type=Decimal, default=Decimal("1"),
                        help="the run stops when it has cost this much (default 1)")
    args = parser.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN first: Apify Console > Settings > API & Integrations.")

    client = ApifyClient(token)
    run = client.actor(ACTOR).call(
        run_input={"offers": args.offers, "translateTitles": args.english},
        max_total_charge_usd=args.max_usd,
    )
    if run is None:
        sys.exit("The run did not start.")
    if run.status != "SUCCEEDED":
        print(f"Warning: the run ended as {run.status}: {run.status_message or ''}", file=sys.stderr)

    offers = [r for r in client.dataset(run.default_dataset_id).iterate_items() if r.get("type") == "offer"]
    with open(args.out, "w", encoding="utf-8") as f:
        for row in offers:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    for row in offers:
        tiers = row.get("price_tiers") or []
        by_quantity = ""
        if len({t.get("from_quantity") for t in tiers}) > 1:  # otherwise the prices differ by variant, not quantity
            by_quantity = " | by quantity: " + ", ".join(f"from {t.get('from_quantity')}: {t.get('price')}" for t in tiers)
        print(f"{row.get('offer_id')}: {row.get('title_en') or row.get('title')}")
        print(f"  {row.get('price_min')}-{row.get('price_max')} CNY (${row.get('price_min_usd')}-"
              f"{row.get('price_max_usd')}) | MOQ {row.get('min_order')} {row.get('unit') or ''}{by_quantity}")
        print(f"  {row.get('sku_count')} variants, stock {row.get('stock_total')} | {row.get('sold_text')} sold | "
              f"{row.get('review_count')} reviews, {row.get('good_rate_percent')}% good | "
              f"repeat buyers {row.get('repeat_rate_3m')}")
        print(f"  {row.get('company')} | {row.get('supplier_years')} years on 1688 | ships from "
              f"{row.get('ships_from')} | dropshipping: {'yes' if row.get('is_dropship') else 'no'}")
    print(f"{len(offers)} offers written to {args.out}")


if __name__ == "__main__":
    main()
