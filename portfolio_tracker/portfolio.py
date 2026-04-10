"""
Portfolio calculation engine.

Reads raw transactions, computes holdings with FIFO cost basis,
fetches live prices & fundamentals from Yahoo Finance, and builds
all the KPI metrics shown in the dashboard.
"""

from __future__ import annotations

import warnings
from collections import defaultdict, deque
from datetime import datetime, date, timedelta
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from config import BENCHMARK_SYMBOL, BENCHMARK_NAME, CHART_PERIOD

warnings.filterwarnings("ignore")


# ──────────────────────────────────────────────────────────────────────────────
# Transaction parsing
# ──────────────────────────────────────────────────────────────────────────────

def parse_transactions(raw_rows: list[list[Any]]) -> pd.DataFrame:
    """Convert the raw sheet rows (with header) into a clean DataFrame."""
    if len(raw_rows) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw_rows[1:], columns=["Date", "Type", "Symbol",
                                               "Quantity", "Price", "Amount", "Notes"])
    df["Date"]     = pd.to_datetime(df["Date"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Price"]    = pd.to_numeric(df["Price"],    errors="coerce").fillna(0)
    df["Amount"]   = pd.to_numeric(df["Amount"],   errors="coerce").fillna(0)
    df["Type"]     = df["Type"].str.upper().str.strip()
    df["Symbol"]   = df["Symbol"].str.upper().str.strip()
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Holdings & FIFO cost basis
# ──────────────────────────────────────────────────────────────────────────────

def _compute_holdings_and_pnl(df: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    """
    Returns:
        holdings_df    – one row per currently-held symbol
        realized_pnl   – total realised profit / loss (₹)
        cash_balance   – current cash in the portfolio
    """
    # FIFO lots per symbol: deque of (qty, cost_per_unit)
    lots: dict[str, deque] = defaultdict(deque)
    realized_pnl = 0.0
    cash_balance = 0.0

    for _, row in df.iterrows():
        t = row["Type"]
        sym = row["Symbol"]
        qty = float(row["Quantity"])
        price = float(row["Price"])
        amount = float(row["Amount"])

        if t == "DEPOSIT":
            cash_balance += amount
        elif t == "WITHDRAW":
            cash_balance += amount   # amount is negative
        elif t == "BUY":
            lots[sym].append((qty, price))
            cash_balance -= amount
        elif t == "SELL":
            remaining = qty
            sell_price = price
            while remaining > 0 and lots[sym]:
                lot_qty, lot_price = lots[sym][0]
                consumed = min(remaining, lot_qty)
                realized_pnl += consumed * (sell_price - lot_price)
                if consumed == lot_qty:
                    lots[sym].popleft()
                else:
                    lots[sym][0] = (lot_qty - consumed, lot_price)
                remaining -= consumed
                cash_balance += consumed * sell_price

    # Build holdings summary
    records = []
    for sym, lot_queue in lots.items():
        if not lot_queue:
            continue
        total_qty = sum(q for q, _ in lot_queue)
        if total_qty <= 0:
            continue
        total_cost = sum(q * p for q, p in lot_queue)
        avg_cost = total_cost / total_qty
        records.append({"Symbol": sym, "Quantity": total_qty,
                         "Avg_Cost": avg_cost, "Total_Cost": total_cost})

    holdings_df = pd.DataFrame(records)
    return holdings_df, realized_pnl, cash_balance


# ──────────────────────────────────────────────────────────────────────────────
# Yahoo Finance helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_ticker_info(symbol: str) -> dict:
    try:
        t = yf.Ticker(symbol)
        info = t.info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def _batch_current_prices(symbols: list[str]) -> dict[str, float]:
    """Fetch latest closing price for a list of symbols."""
    prices = {}
    if not symbols:
        return prices
    try:
        data = yf.download(symbols, period="5d", progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            close = data["Close"]
        else:
            close = data[["Close"]]
            close.columns = symbols
        last = close.dropna(how="all").iloc[-1]
        for sym in symbols:
            if sym in last.index and not np.isnan(last[sym]):
                prices[sym] = float(last[sym])
    except Exception:
        pass
    # Fill any missing with individual calls
    for sym in symbols:
        if sym not in prices:
            try:
                info = _fetch_ticker_info(sym)
                p = info.get("currentPrice") or info.get("regularMarketPrice")
                if p:
                    prices[sym] = float(p)
            except Exception:
                pass
    return prices


def _fetch_fundamentals(symbol: str) -> dict:
    info = _fetch_ticker_info(symbol)
    return {
        "pe_ratio":        info.get("trailingPE"),
        "forward_pe":      info.get("forwardPE"),
        "beta":            info.get("beta"),
        "dividend_yield":  info.get("dividendYield"),
        "market_cap":      info.get("marketCap"),
        "52w_high":        info.get("fiftyTwoWeekHigh"),
        "52w_low":         info.get("fiftyTwoWeekLow"),
        "sector":          info.get("sector", ""),
        "name":            info.get("longName") or info.get("shortName") or symbol,
        "eps":             info.get("trailingEps"),
        "pb_ratio":        info.get("priceToBook"),
        "roe":             info.get("returnOnEquity"),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Benchmark comparison
# ──────────────────────────────────────────────────────────────────────────────

def _portfolio_daily_value(df: pd.DataFrame, end_date: date | None = None) -> pd.Series:
    """
    Estimate portfolio value on each trading day over the past CHART_PERIOD.
    Uses end-of-day prices for all held symbols.
    """
    end_date = end_date or date.today()

    symbols = df[df["Type"] == "BUY"]["Symbol"].unique().tolist()
    if not symbols:
        return pd.Series(dtype=float)

    try:
        hist = yf.download(
            symbols + [BENCHMARK_SYMBOL],
            period=CHART_PERIOD,
            progress=False, auto_adjust=True,
        )
        if isinstance(hist.columns, pd.MultiIndex):
            prices_hist = hist["Close"]
        else:
            prices_hist = hist[["Close"]]
            prices_hist.columns = symbols
    except Exception:
        return pd.Series(dtype=float)

    # For each day reconstruct holdings using txns up to that day
    dates = prices_hist.index
    portfolio_vals = []

    for d in dates:
        sub = df[df["Date"] <= d]
        h, _, cash = _compute_holdings_and_pnl(sub)
        val = cash
        if not h.empty:
            for _, row in h.iterrows():
                sym = row["Symbol"]
                if sym in prices_hist.columns:
                    p_row = prices_hist.loc[:d, sym].dropna()
                    if not p_row.empty:
                        val += row["Quantity"] * p_row.iloc[-1]
        portfolio_vals.append(val)

    series = pd.Series(portfolio_vals, index=dates, name="Portfolio")
    return series


def get_benchmark_history(period: str = CHART_PERIOD) -> pd.Series:
    try:
        data = yf.download(BENCHMARK_SYMBOL, period=period, progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            return data["Close"][BENCHMARK_SYMBOL]
        return data["Close"]
    except Exception:
        return pd.Series(dtype=float)


# ──────────────────────────────────────────────────────────────────────────────
# Main public function
# ──────────────────────────────────────────────────────────────────────────────

def build_portfolio(raw_rows: list[list[Any]]) -> dict:
    """
    Full portfolio computation. Returns a dict with all data needed by the UI.
    """
    result = {
        "transactions":    pd.DataFrame(),
        "holdings":        pd.DataFrame(),
        "realized_pnl":    0.0,
        "cash_balance":    0.0,
        "total_invested":  0.0,
        "total_value":     0.0,
        "unrealized_pnl":  0.0,
        "portfolio_return": 0.0,
        "portfolio_beta":  None,
        "portfolio_pe":    None,
        "fundamentals":    {},
        "benchmark_return": 0.0,
        "alpha":           0.0,
        "chart_data":      pd.DataFrame(),
    }

    df = parse_transactions(raw_rows)
    if df.empty:
        return result

    result["transactions"] = df

    holdings, realized_pnl, cash_balance = _compute_holdings_and_pnl(df)
    result["realized_pnl"] = realized_pnl
    result["cash_balance"]  = cash_balance

    if holdings.empty:
        total_deposits    = df[df["Type"] == "DEPOSIT"]["Amount"].sum()
        total_withdrawals = df[df["Type"] == "WITHDRAW"]["Amount"].sum()
        result["total_invested"] = total_deposits + total_withdrawals
        return result

    # ── Fetch current prices ──────────────────────────────────────────────────
    symbols = holdings["Symbol"].tolist()
    prices  = _batch_current_prices(symbols)
    holdings["Current_Price"]  = holdings["Symbol"].map(prices).fillna(0)
    holdings["Current_Value"]  = holdings["Quantity"] * holdings["Current_Price"]
    holdings["Unrealized_PnL"] = holdings["Current_Value"] - holdings["Total_Cost"]
    holdings["PnL_Pct"]        = (
        (holdings["Unrealized_PnL"] / holdings["Total_Cost"]) * 100
    ).round(2)

    total_value       = holdings["Current_Value"].sum() + cash_balance
    total_cost        = holdings["Total_Cost"].sum()
    total_deposits    = df[df["Type"] == "DEPOSIT"]["Amount"].sum()
    total_withdrawals = abs(df[df["Type"] == "WITHDRAW"]["Amount"].sum())
    total_invested    = total_deposits - total_withdrawals

    unrealized_pnl = holdings["Unrealized_PnL"].sum()
    total_pnl      = unrealized_pnl + realized_pnl
    portfolio_return = (total_pnl / total_invested * 100) if total_invested else 0.0

    # ── Fundamentals per symbol ───────────────────────────────────────────────
    fund_data = {}
    for sym in symbols:
        fund_data[sym] = _fetch_fundamentals(sym)

    # Weighted portfolio beta & PE (weighted by current value)
    weights = holdings.set_index("Symbol")["Current_Value"]
    total_w = weights.sum()

    betas = {}
    pes   = {}
    for sym in symbols:
        b = fund_data[sym].get("beta")
        p = fund_data[sym].get("pe_ratio")
        if b is not None:
            betas[sym] = float(b)
        if p is not None and float(p) > 0:
            pes[sym] = float(p)

    portfolio_beta = None
    if betas and total_w > 0:
        portfolio_beta = sum(
            betas[s] * weights.get(s, 0) for s in betas
        ) / total_w

    portfolio_pe = None
    if pes and total_w > 0:
        portfolio_pe = sum(
            pes[s] * weights.get(s, 0) for s in pes
        ) / total_w

    # ── Benchmark return (1-year) ─────────────────────────────────────────────
    bench = get_benchmark_history(CHART_PERIOD)
    benchmark_return = 0.0
    if not bench.empty and len(bench) >= 2:
        benchmark_return = ((bench.iloc[-1] / bench.iloc[0]) - 1) * 100

    alpha = portfolio_return - benchmark_return

    # ── Add sector / name columns to holdings ─────────────────────────────────
    holdings["Name"]   = holdings["Symbol"].map(
        {s: fund_data[s].get("name", s) for s in symbols}
    )
    holdings["Sector"] = holdings["Symbol"].map(
        {s: fund_data[s].get("sector", "") for s in symbols}
    )
    holdings["Beta"]   = holdings["Symbol"].map(betas)
    holdings["PE"]     = holdings["Symbol"].map(pes)
    holdings["52W_High"] = holdings["Symbol"].map(
        {s: fund_data[s].get("52w_high") for s in symbols}
    )
    holdings["52W_Low"] = holdings["Symbol"].map(
        {s: fund_data[s].get("52w_low") for s in symbols}
    )
    holdings["Div_Yield"] = holdings["Symbol"].map(
        {s: fund_data[s].get("dividend_yield") for s in symbols}
    )

    # ── Chart data: benchmark normalised ─────────────────────────────────────
    chart_df = pd.DataFrame()
    if not bench.empty:
        bench_norm = (bench / bench.iloc[0] - 1) * 100
        chart_df[BENCHMARK_NAME] = bench_norm

    result.update(
        holdings       = holdings,
        realized_pnl   = realized_pnl,
        cash_balance   = cash_balance,
        total_invested = total_invested,
        total_value    = total_value,
        unrealized_pnl = unrealized_pnl,
        portfolio_return = portfolio_return,
        portfolio_beta = portfolio_beta,
        portfolio_pe   = portfolio_pe,
        fundamentals   = fund_data,
        benchmark_return = benchmark_return,
        alpha          = alpha,
        chart_data     = chart_df,
    )
    return result
