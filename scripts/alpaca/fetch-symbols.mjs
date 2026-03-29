#!/usr/bin/env node
/**
 * Fetch all active US equity symbols from Alpaca Trading API.
 *
 * Usage:
 *   node scripts/alpaca/fetch-symbols.mjs
 *   # or via npm: npm run fetch:symbols
 *
 * Environment:
 *   ALPACA_API_KEY    — Alpaca API key (paper or live)
 *   ALPACA_API_SECRET — Alpaca API secret
 *   ALPACA_BASE_URL   — (optional) defaults to https://paper-api.alpaca.markets
 *
 * Output:
 *   data/symbols/symbols.csv
 */

import { writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, "..", "..");

// --- Config ---
const API_KEY = process.env.ALPACA_API_KEY;
const API_SECRET = process.env.ALPACA_API_SECRET;
const BASE_URL =
  process.env.ALPACA_BASE_URL || "https://paper-api.alpaca.markets";
const OUTPUT_DIR = join(PROJECT_ROOT, "data", "symbols");
const OUTPUT_FILE = join(OUTPUT_DIR, "symbols.csv");
const VALID_EXCHANGES = new Set(["NYSE", "NASDAQ", "AMEX"]);
const PREVIEW_COUNT = 10;

// --- Validation ---
if (!API_KEY || !API_SECRET) {
  console.error(
    "Error: ALPACA_API_KEY and ALPACA_API_SECRET must be set in environment.\n" +
      "  export ALPACA_API_KEY=your_key\n" +
      "  export ALPACA_API_SECRET=your_secret"
  );
  process.exit(1);
}

// --- Fetch ---
async function fetchAllAssets() {
  const url = new URL("/v2/assets", BASE_URL);
  url.searchParams.set("asset_class", "us_equity");
  url.searchParams.set("status", "active");

  console.log(`Fetching assets from ${url.origin}...`);

  const res = await fetch(url.toString(), {
    headers: {
      "APCA-API-KEY-ID": API_KEY,
      "APCA-API-SECRET-KEY": API_SECRET,
      Accept: "application/json",
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Alpaca API error ${res.status}: ${body}`);
  }

  return res.json();
}

// --- Filter ---
function filterAssets(assets) {
  return assets.filter(
    (a) =>
      a.asset_class === "us_equity" &&
      a.status === "active" &&
      VALID_EXCHANGES.has(a.exchange) &&
      !a.fractionable // optional: exclude fractionable
  );
}

// --- CSV ---
function toCsv(assets) {
  const header = "symbol,exchange,name,tradable,shortable";
  const rows = assets
    .sort((a, b) => a.symbol.localeCompare(b.symbol))
    .map((a) => {
      // Escape name field (may contain commas)
      const name = `"${(a.name || "").replace(/"/g, '""')}"`;
      return `${a.symbol},${a.exchange},${name},${a.tradable},${a.shortable}`;
    });
  return [header, ...rows].join("\n") + "\n";
}

// --- Main ---
async function main() {
  try {
    const allAssets = await fetchAllAssets();
    console.log(`Total assets returned by API: ${allAssets.length}`);

    const filtered = filterAssets(allAssets);
    console.log(
      `After filter (active, US_EQUITY, NYSE/NASDAQ/AMEX, non-fractionable): ${filtered.length}`
    );

    // Ensure output directory exists
    if (!existsSync(OUTPUT_DIR)) {
      mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    // Write CSV
    const csv = toCsv(filtered);
    writeFileSync(OUTPUT_FILE, csv, "utf-8");
    console.log(`\nSaved ${filtered.length} symbols to ${OUTPUT_FILE}`);

    // Preview
    console.log(`\nFirst ${PREVIEW_COUNT} symbols:`);
    filtered
      .sort((a, b) => a.symbol.localeCompare(b.symbol))
      .slice(0, PREVIEW_COUNT)
      .forEach((a) =>
        console.log(`  ${a.symbol.padEnd(8)} ${a.exchange.padEnd(8)} ${a.name}`)
      );

    // Exchange breakdown
    const byExchange = {};
    filtered.forEach((a) => {
      byExchange[a.exchange] = (byExchange[a.exchange] || 0) + 1;
    });
    console.log("\nBreakdown by exchange:");
    Object.entries(byExchange)
      .sort(([, a], [, b]) => b - a)
      .forEach(([ex, count]) => console.log(`  ${ex}: ${count}`));
  } catch (err) {
    console.error(`Failed: ${err.message}`);
    process.exit(1);
  }
}

main();
