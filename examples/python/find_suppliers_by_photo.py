"""Find 1688 suppliers by product photo: for each photo, the 1688 offers that look like it, best match first.

    python find_suppliers_by_photo.py PHOTO_URL [PHOTO_URL ...] [--file photos.txt] [--english] [--out matches.csv]

A photo is a link to an image: from Amazon, AliExpress, Shopify, TikTok Shop, 1688 or your own site.
--file reads more links, one per line. Each photo returns 60 matches (a page); --pages up to 10.
A photo of one product on a plain background works best. A 1688 photo usually finds the same product;
a photo from another shop mostly finds similar ones.
Set APIFY_TOKEN first (Apify Console > Settings > API & Integrations).
"""
import argparse
import csv
import os
import sys
from decimal import Decimal

from apify_client import ApifyClient

ACTOR = "maksim_lazouski/1688-image-search"
COLUMNS = ["photo", "rank", "offer_id", "title", "title_en", "price", "price_usd", "min_order", "sold",
           "repeat_buyers", "company", "supplier_years", "province", "city", "is_ad", "url", "image"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Chinese text prints on any Windows console, pipe or log file
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Find 1688 suppliers by product photo.")
    parser.add_argument("photos", nargs="*", help="photo links")
    parser.add_argument("--file", help="a text file with one photo link per line")
    parser.add_argument("--pages", type=int, default=1, help="pages of 60 matches per photo, 1 to 10 (default 1)")
    parser.add_argument("--english", action="store_true", help="add English titles ($0.10 per 1,000 rows)")
    parser.add_argument("--out", default="matches.csv", help="CSV file to write (default matches.csv)")
    parser.add_argument("--max-usd", type=Decimal, default=Decimal("1"),
                        help="the run stops when it has cost this much (default 1)")
    args = parser.parse_args()
    if not 1 <= args.pages <= 10:
        parser.error("--pages must be between 1 and 10")

    photos = list(args.photos)
    if args.file:
        with open(args.file, encoding="utf-8-sig") as f:  # -sig: a file saved with a BOM works too
            photos += [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not photos:
        sys.exit("Give photo links, or --file with one link per line.")
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN first: Apify Console > Settings > API & Integrations.")

    client = ApifyClient(token)
    run = client.actor(ACTOR).call(
        run_input={"images": photos, "maxPagesPerImage": args.pages, "translateTitles": args.english},
        max_total_charge_usd=args.max_usd,
    )
    if run is None:
        sys.exit("The run did not start.")
    if run.status != "SUCCEEDED":
        print(f"Warning: the run ended as {run.status}: {run.status_message or ''}", file=sys.stderr)

    best = {}
    count = 0
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in client.dataset(run.default_dataset_id).iterate_items():
            if row.get("type") != "image_match":
                continue
            writer.writerow({
                "photo": row.get("image_url"), "rank": row.get("rank"), "offer_id": row.get("offer_id"),
                "title": row.get("title"), "title_en": row.get("title_en"),
                "price": row.get("price"), "price_usd": row.get("price_usd"),
                "min_order": row.get("min_order_text") or row.get("min_order"), "sold": row.get("sold_text"),
                "repeat_buyers": row.get("repurchase_rate") or row.get("repeat_buyer_rate"),
                "company": row.get("company"), "supplier_years": row.get("supplier_years"),
                "province": row.get("province"), "city": row.get("city"), "is_ad": row.get("is_ad"),
                "url": row.get("url"), "image": row.get("image"),
            })
            count += 1
            if not row.get("is_ad"):
                best.setdefault(row.get("image_url"), []).append(row)

    for photo, rows in best.items():
        print(f"\n{photo}")
        for row in rows[:3]:
            print(f"  {row.get('price')} CNY (${row.get('price_usd')}) | {row.get('min_order_text') or ''} | "
                  f"{row.get('sold_text') or ''} | {row.get('company')} | {row.get('url')}")
    print(f"\n{count} matches for {len(photos)} photo(s) written to {args.out} (ads are marked in is_ad)")


if __name__ == "__main__":
    main()
