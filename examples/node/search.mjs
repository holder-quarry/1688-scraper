// Search 1688.com by keyword and write the offers to offers.csv: price in CNY and USD, MOQ, supplier.
//
//   node examples/node/search.mjs KEYWORD [KEYWORD ...]
//
// Set APIFY_TOKEN first (Apify Console > Settings > API & Integrations).
import { writeFileSync } from 'node:fs';
import { ApifyClient } from 'apify-client';

const ACTOR = 'maksim_lazouski/1688-product-scraper';

// The smallest order: 1688's own MOQ text if the row has it, else the start of the first price tier.
const minOrder = (row) => {
    if (row.min_order_text || row.min_order) return row.min_order_text ?? row.min_order;
    const first = (row.price_tiers ?? [])[0] ?? {};
    const match = String(first.quantity ?? first.from_quantity ?? '').match(/^\s*≥?\s*(\d+)/);
    return match ? Number(match[1]) : null;
};
// CSV column -> how to get it from a search result row
const COLUMNS = {
    keyword: (r) => r.keyword, position: (r) => r.position, offer_id: (r) => r.offer_id, title: (r) => r.title,
    title_en: (r) => r.title_en, price: (r) => r.price, price_usd: (r) => r.price_usd, min_order: minOrder,
    sold: (r) => r.sold_text, repeat_buyers: (r) => r.repeat_buyer_rate ?? r.repurchase_rate, company: (r) => r.company,
    supplier_years: (r) => r.supplier_years, province: (r) => r.province, city: (r) => r.city,
    is_ad: (r) => r.is_ad, url: (r) => r.url,
};

const keywords = process.argv.slice(2);
if (keywords.length === 0) {
    console.error('Give one or more keywords, for example: node examples/node/search.mjs 手机壳');
    process.exit(1);
}
if (!process.env.APIFY_TOKEN) {
    console.error('Set APIFY_TOKEN first: Apify Console > Settings > API & Integrations.');
    process.exit(1);
}

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const run = await client.actor(ACTOR).call(
    { keywords, maxPagesPerKeyword: 1, translateTitles: true }, // English titles: $0.10 per 1,000 rows
    { maxTotalChargeUsd: 1 }, // the run stops when it has cost $1
);
if (run.status !== 'SUCCEEDED') console.error(`Warning: the run ended as ${run.status}: ${run.statusMessage ?? ''}`);
const { items } = await client.dataset(run.defaultDatasetId).listItems();
const offers = items.filter((row) => row.type === 'search_result');

const cell = (value) => {
    const text = value === undefined || value === null ? '' : String(value);
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};
const lines = [
    Object.keys(COLUMNS).join(','),
    ...offers.map((row) => Object.values(COLUMNS).map((get) => cell(get(row))).join(',')),
];
// The BOM makes Excel show the Chinese titles right.
writeFileSync('offers.csv', `﻿${lines.join('\n')}\n`);
console.log(`${offers.length} offers written to offers.csv`);
