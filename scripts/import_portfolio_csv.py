#!/usr/bin/env python3
"""Convert a broker portfolio CSV into dashboard holdings data."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROFILE = {
    "SANSERA": ("Sansera Engineering", "SANSERA.NS", "Auto Components"),
    "KPL": ("Kwality Pharmaceuticals", "KPL.NS", "Pharma"),
    "PARAS": ("Paras Defence and Space Technologies", "PARAS.NS", "Defence"),
    "ARVIND": ("Arvind", "ARVIND.NS", "Textiles / Apparel"),
    "INDSWFTLAB": ("Ind-Swift Laboratories", "INDSWFTLAB.NS", "Pharma"),
    "TITANBIO-BE": ("Titan Biotech", "TITANBIO.NS", "Biotechnology"),
    "SHILPAMED": ("Shilpa Medicare", "SHILPAMED.NS", "Pharma"),
    "SHYAMMETL": ("Shyam Metalics and Energy", "SHYAMMETL.NS", "Metals"),
    "AZAD": ("Azad Engineering", "AZAD.NS", "Industrials / Aerospace"),
    "UJJIVANSFB": ("Ujjivan Small Finance Bank", "UJJIVANSFB.NS", "Banking"),
    "MONARCH": ("Monarch Networth Capital", "MONARCH.NS", "Capital Markets"),
    "THANGAMAYL": ("Thangamayil Jewellery", "THANGAMAYL.NS", "Jewellery"),
    "AJANTPHARM": ("Ajanta Pharma", "AJANTPHARM.NS", "Pharma"),
    "ZYDUSWELL": ("Zydus Wellness", "ZYDUSWELL.NS", "Consumer Staples"),
    "MOTHERSON": ("Samvardhana Motherson International", "MOTHERSON.NS", "Auto Components"),
    "HSCL": ("Himadri Speciality Chemical", "HSCL.NS", "Specialty Chemicals"),
    "AVALON": ("Avalon Technologies", "AVALON.NS", "Electronics Manufacturing"),
    "ICICIBANK": ("ICICI Bank", "ICICIBANK.NS", "Banking"),
    "INDNIPPON": ("India Nippon Electricals", "INDNIPPON.NS", "Auto Components"),
    "TANFACIND-EQ": ("Tanfac Industries", "TANFACIND.NS", "Specialty Chemicals"),
    "VADILALIND": ("Vadilal Industries", "VADILALIND.NS", "Consumer Staples"),
    "MARICO": ("Marico", "MARICO.NS", "Consumer Staples"),
    "BLSE": ("BLS E-Services", "BLSE.NS", "Digital Services"),
    "MARUTI": ("Maruti Suzuki India", "MARUTI.NS", "Auto"),
    "NYKAA": ("FSN E-Commerce Ventures (Nykaa)", "NYKAA.NS", "Consumer Internet"),
    "TATATECH": ("Tata Technologies", "TATATECH.NS", "Engineering Services"),
    "J&KBANK": ("Jammu & Kashmir Bank", "J&KBANK.NS", "Banking"),
    "EQUITASBNK": ("Equitas Small Finance Bank", "EQUITASBNK.NS", "Banking"),
    "KTKBANK": ("Karnataka Bank", "KTKBANK.NS", "Banking"),
    "ANANDRATHI": ("Anand Rathi Wealth", "ANANDRATHI.NS", "Wealth Management"),
    "SOLARINDS": ("Solar Industries India", "SOLARINDS.NS", "Defence / Explosives"),
    "PRUDENT": ("Prudent Corporate Advisory Services", "PRUDENT.NS", "Wealth Distribution"),
    "FERMENTA": ("Fermenta Biotech", "FERMENTA.NS", "Biotechnology"),
    "RRKABEL": ("R R Kabel", "RRKABEL.NS", "Electricals"),
    "RAIN": ("Rain Industries", "RAIN.NS", "Materials"),
    "JAYBARMARU": ("JBM Auto", "JAYBARMARU.NS", "Auto Components"),
    "LALPATHLAB": ("Dr. Lal PathLabs", "LALPATHLAB.NS", "Diagnostics"),
    "RPTECH": ("Rashi Peripherals", "RPTECH.NS", "Technology Distribution"),
}


def number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.replace("+", "", regex=False).str.replace("%", "", regex=False), errors="coerce")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = pd.read_csv(args.input)
    raw["Name"] = raw["Name"].astype(str).str.strip()
    raw = raw[raw["Name"].str.casefold().ne("total")].copy()
    missing = sorted(set(raw["Name"]) - set(PROFILE))
    if missing:
        raise SystemExit(f"Ticker profiles are missing for: {', '.join(missing)}")
    quantity, ltp = number(raw["Quantity"]), number(raw["LTP"])
    current, invested = number(raw["Current Value"]), number(raw["Invested Value"])
    overall_pnl, overall_pct = number(raw["Profit/Loss"]), number(raw["Profit/Loss %"])
    day_pnl, day_pct = number(raw["Todays Profit/Loss"]), number(raw["Todays Profit/Loss %"])
    day_change = day_pnl / quantity
    out = pd.DataFrame({
        "Name": raw["Name"], "Free Qty": quantity, "Pledged Qty": 0.0,
        "Day Change %": day_pct, "LTP": ltp, "Quantity": quantity,
        "Day Change": day_change, "Current Value": current, "Source Name": raw["Name"],
        "Display Name": raw["Name"].map(lambda x: PROFILE[x][0]), "Symbol": raw["Name"],
        "Yahoo Ticker": raw["Name"].map(lambda x: PROFILE[x][1]),
        "Theme": raw["Name"].map(lambda x: PROFILE[x][2]),
        "Portfolio Bucket": "Monitor",
        "Ticker Confidence": "Mapped", "Ticker Note": "Ticker mapped for Yahoo/NSE technical refresh.",
        "Day P&L": day_pnl, "Previous Close": ltp - day_change,
        "P&L Matched": True, "P&L Lots": 1, "P&L Quantity": quantity,
        "Costed Quantity": quantity, "Uncosted Quantity": 0.0,
        "Known Cost Value": invested, "Average Recorded Cost": number(raw["Avg. Price"]),
        "Broker Unrealized P&L": overall_pnl, "Return on Recorded Cost %": overall_pct,
        "Cost Basis Coverage %": 100.0, "Quantity Reconciliation %": 100.0,
        "Cost Basis Status": "Cost basis available",
        "Cost Basis Note": "Quantity, average price, invested value, and unrealized P&L were supplied in the portfolio export.",
        "Price Source": "Portfolio export", "Quote Status": "Supplied snapshot",
        "Quote Note": "Price and day movement came from the supplied portfolio CSV.",
    })
    out["Weight %"] = out["Current Value"] / out["Current Value"].sum() * 100
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Imported {len(out)} holdings; current value Rs {out['Current Value'].sum():,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
