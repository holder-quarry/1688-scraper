# 1688 scraper: wholesale offers by keyword, link or product photo

Get offers from [1688.com](https://www.1688.com), the Chinese wholesale marketplace, as CSV or JSON: prices by
quantity, MOQ, every variant with stock, units sold, repeat-buyer rate, the supplier, ratings and dropshipping
terms, with prices also in US dollars and, as a paid add-on, titles in English. Search by keyword, read offers by link, or find
suppliers by a product photo. No 1688 account, no cookies, no proxies of your own.

The scraping runs as two hosted actors on Apify:

- **[1688 Product Scraper](https://apify.com/maksim_lazouski/1688-product-scraper)**: search by keyword, or
  full offers by link.
- **[1688 Image Search](https://apify.com/maksim_lazouski/1688-image-search)**: the 1688 offers that look like
  your product photo, best match first.

This repo holds ready-to-run examples and real sample output. You need a free Apify account and its API token.

## Quick start (Python)

Linux or macOS:

```bash
git clone https://github.com/holder-quarry/1688-scraper
cd 1688-scraper
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export APIFY_TOKEN=your_token
.venv/bin/python examples/python/search_to_csv.py 手机壳 --english --out phone-cases.csv
```

Windows PowerShell:

```powershell
git clone https://github.com/holder-quarry/1688-scraper
cd 1688-scraper
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:APIFY_TOKEN = "your_token"
.venv\Scripts\python examples\python\search_to_csv.py 手机壳 --english --out phone-cases.csv
```

Your token is in Apify Console under **Settings > API & Integrations**. The CSV files are written with a BOM,
so Excel shows the Chinese titles right.

## Examples

| Script | What it does |
|---|---|
| [`search_to_csv.py`](examples/python/search_to_csv.py) | Keywords to a CSV of offers: price in CNY and USD, price by quantity, MOQ (from the first price tier), units sold, repeat buyers, supplier, years on 1688, province and city. Sample: [`sample/search-phone-case.csv`](sample/search-phone-case.csv) |
| [`find_suppliers_by_photo.py`](examples/python/find_suppliers_by_photo.py) | Photo links (or a text file of them) to a CSV of the matching offers per photo, and the top 3 per photo on screen. Sample: [`sample/photo-matches.csv`](sample/photo-matches.csv) |
| [`offer_details.py`](examples/python/offer_details.py) | Offer links to full offers, about 100 fields each (JSON lines). Sample: [`sample/offer.json`](sample/offer.json) |
| [`search.mjs`](examples/node/search.mjs) | The keyword search in Node.js (`npm install`, then `node examples/node/search.mjs 手机壳`) |

Every script stops the run when it has cost $1 (in Python `--max-usd` changes that), so a typo cannot run up
a bill.

### Find suppliers for a list of your products

Put the photo links of your products in a file, one per line, and run:

```bash
python examples/python/find_suppliers_by_photo.py --file photos.txt --english --out matches.csv
```

The photos can come from Amazon, AliExpress, Shopify, TikTok Shop, 1688 or your own site. A photo of one
product on a plain background works best. A 1688 photo usually finds the same product; a photo from another
shop mostly finds similar ones. Ads are in the results where 1688 puts
them, marked `is_ad`.

### One HTTP call

```bash
curl -X POST "https://api.apify.com/v2/acts/maksim_lazouski~1688-product-scraper/run-sync-get-dataset-items" \
  -H "Authorization: Bearer YOUR_APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["手机壳"], "maxItems": 40}'
```

Windows PowerShell (`curl.exe`, not PowerShell's own `curl`):

```powershell
'{"keywords": ["\u624b\u673a\u58f3"], "maxItems": 40}' | Set-Content -Encoding ascii body.json
curl.exe -X POST "https://api.apify.com/v2/acts/maksim_lazouski~1688-product-scraper/run-sync-get-dataset-items" -H "Authorization: Bearer YOUR_APIFY_TOKEN" -H "Content-Type: application/json" -d "@body.json"
```

(`\u624b\u673a\u58f3` is 手机壳 written so that the file stays plain ASCII.)

It waits for the run and returns the rows; use it for runs that end within 5 minutes.

## Input

1688 Product Scraper:

| Field | What it is |
|---|---|
| `keywords` | Search keywords. Chinese keywords find the most |
| `maxPagesPerKeyword` | Pages of 60 results per keyword, 1 to 3 (default 1) |
| `offers` | Offer links (`https://detail.1688.com/offer/....html`) or ids |
| `scrapeDetails` | Open every search result for its full offer row |
| `translateTitles` | Add `title_en`, an English machine translation of each title |
| `watchName` | For runs on a schedule: return only offers that are new or whose price, title or state changed |

1688 Image Search:

| Field | What it is |
|---|---|
| `images` | Photo links: JPEG, PNG, WebP or GIF |
| `maxPagesPerImage` | Pages of 60 matches per photo, 1 to 10 (default 1) |
| `scrapeDetails` | Open every match for its full offer row |
| `translateTitles` | Add `title_en` |

The actor pages list every field of the input and the output.

## Cost

You pay for what the actors return: rows, or for Image Search photos and pages of matches. Prices on
Apify's Free plan (paid plans pay less):

- 1688 Product Scraper: a full offer row $3.00 per 1,000, a search result row $0.50 per 1,000. One keyword
  read to the end (180 results) costs $0.09.
- 1688 Image Search: a photo with its first 60 matches $0.004, each further page of 60 $0.002, plus $0.005
  per run. 100 photos with 60 matches each cost $0.40.
- English titles: $0.10 per 1,000 rows.

Rows and photos that could not be read are not charged. Apify's free plan comes with $5 of usage a month. Current prices
are on the actor pages.

## Limits

- Search gives up to 180 offers per keyword: 1688 shows a visitor who is not logged in three pages of 60.
  To get more offers, use more specific keywords.
- Up to 600 matches per photo (10 pages of 60).
- Text comes as 1688 gives it: in Chinese, prices in CNY (and in US dollars beside them).
- Descriptions on 1688 are mostly pictures, so `description_text` is often short.
- 1688 sometimes refuses search for a while; the actor waits and tries again. If it lasts, start the run
  again later.

## Data and law

The actors read only what 1688.com shows publicly, without logging in. Offer pages name companies and their
shops, and a seller can be a private person, so handle names as the data protection rules that apply to you
require. You are responsible for how you use the data; if you are not sure, ask a lawyer.

## 中文说明

本仓库是 **1688 商品采集** 和 **1688 以图搜货** 的 Python / Node.js 示例代码。采集在 Apify 上运行
（[1688 Product Scraper](https://apify.com/maksim_lazouski/1688-product-scraper)、
[1688 Image Search](https://apify.com/maksim_lazouski/1688-image-search)），无需 1688 账号、无需 Cookie、
无需自备代理，需要一个免费的 Apify 账号和 API Token。

- 关键词搜索：默认每个关键词取第一页 60 个商品，最多 3 页 180 个；结果含人民币和美元价格、阶梯价、
  起批量（取自第一档阶梯价）、销量、回头率、供应商、入驻年限、所在省市。
- 商品详情：每条约 100 个字段，包括规格及库存、评价、发货地与运费、供应商信息、一件代发条款。
- 以图搜货：每张图片最多 600 个匹配商品；1688 上的图片最容易找到同款，其他网站的图片多为相似款。
- 英文标题为可选付费附加项。
- 按条计费（按 Apify Free 套餐计价，付费套餐更低）：商品详情每千条 $3.00，搜索结果每千条 $0.50；
  以图搜货每张图片（含前 60 个结果）$0.004，之后每页 $0.002，每次运行另收 $0.005；英文标题每千条 $0.10。

## More scrapers by the same author

- [Xianyu Item & Seller Scraper](https://apify.com/maksim_lazouski/xianyu-goofish-item-seller-scraper): items
  and seller shops from Xianyu (闲鱼), China's largest second-hand marketplace. Examples:
  [holder-quarry/xianyu-goofish-scraper](https://github.com/holder-quarry/xianyu-goofish-scraper).
- [Mercari Japan Scraper](https://apify.com/maksim_lazouski/mercari-japan-scraper): Mercari (メルカリ) sold prices
  and listings in English.

Questions, a missing field, something wrong: open an issue here or on the actor's Issues tab
([1688 Product Scraper](https://apify.com/maksim_lazouski/1688-product-scraper/issues),
[1688 Image Search](https://apify.com/maksim_lazouski/1688-image-search/issues)).

The example code is under the MIT License. This project is not affiliated with 1688.com or Alibaba.
