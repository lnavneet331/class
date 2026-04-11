"""Google Sheets read / write helpers."""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from datetime import date
from typing import Any

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

from config import (
    PORTFOLIO_SHEET_KEY,
    PORTFOLIO_SHEET_NAME,
    TRANSACTIONS_WORKSHEET,
    COL_DATE, COL_TYPE, COL_SYMBOL, COL_QTY, COL_PRICE, COL_AMOUNT, COL_NOTES,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _get_client() -> gspread.Client | None:
    """Returns an authenticated gspread client, or None if not configured."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            dict(creds_dict), scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception:
        return None


def _get_worksheet() -> gspread.Worksheet | None:
    client = _get_client()
    if client is None:
        return None
    try:
        # Open by key (sheet ID) for reliability
        try:
            sh = client.open_by_key(PORTFOLIO_SHEET_KEY)
        except Exception:
            sh = client.open(PORTFOLIO_SHEET_NAME)
        try:
            ws = sh.worksheet(TRANSACTIONS_WORKSHEET)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(
                title=TRANSACTIONS_WORKSHEET, rows="1000", cols="7"
            )
            ws.append_row(
                ["Date", "Type", "Symbol", "Quantity", "Price", "Amount", "Notes"],
                value_input_option="USER_ENTERED",
            )
        return ws
    except Exception:
        return None


def _read_public_sheet() -> list[list[Any]] | None:
    """
    Read the Transactions tab from the Google Sheet via its public CSV export URL.
    Works for sheets shared as 'Anyone with the link can view'.
    Returns a list-of-lists (header row first), or None on failure.
    """
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/{PORTFOLIO_SHEET_KEY}"
            f"/gviz/tq?tqx=out:csv&sheet={TRANSACTIONS_WORKSHEET}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        return rows if rows else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Sample data (fallback when neither gspread nor public read is available)
# ---------------------------------------------------------------------------

SAMPLE_TRANSACTIONS: list[list[Any]] = [
    ["Date",       "Type",     "Symbol",       "Quantity", "Price",  "Amount",   "Notes"],
    ["2023-01-05", "DEPOSIT",  "",             0,          0,        500000,     "Initial deposit"],
    ["2023-01-10", "BUY",      "RELIANCE.NS",  10,         2400,     24000,      ""],
    ["2023-01-10", "BUY",      "TCS.NS",       5,          3200,     16000,      ""],
    ["2023-02-01", "BUY",      "HDFCBANK.NS",  20,         1650,     33000,      ""],
    ["2023-03-15", "BUY",      "NIFTYBEES.NS", 100,        185,      18500,      "Nifty ETF"],
    ["2023-04-20", "BUY",      "INFY.NS",      15,         1400,     21000,      ""],
    ["2023-06-10", "SELL",     "TCS.NS",       2,          3500,     7000,       "Partial profit booking"],
    ["2023-07-01", "DEPOSIT",  "",             0,          0,        100000,     "Monthly addition"],
    ["2023-08-05", "BUY",      "ITC.NS",       50,         420,      21000,      ""],
    ["2023-09-20", "BUY",      "BAJFINANCE.NS",3,          7200,     21600,      ""],
    ["2024-01-15", "BUY",      "WIPRO.NS",     30,         480,      14400,      ""],
    ["2024-03-01", "SELL",     "RELIANCE.NS",  5,          2900,     14500,      "Profit booking"],
    ["2024-04-10", "WITHDRAW", "",             0,          0,        -50000,     "Partial withdrawal"],
    ["2024-06-01", "BUY",      "TATAMOTORS.NS",20,         950,      19000,      ""],
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_sheets_connected() -> bool:
    return _get_client() is not None


def load_transactions() -> list[list[Any]]:
    """
    Returns all rows from the Transactions sheet (including header).

    Priority:
      1. Authenticated gspread (read + write)
      2. Public HTTP read from the hardcoded sheet key (read-only)
      3. Built-in sample data
    """
    ws = _get_worksheet()
    if ws is not None:
        rows = ws.get_all_values()
        if not rows:
            ws.append_row(
                ["Date", "Type", "Symbol", "Quantity", "Price", "Amount", "Notes"],
                value_input_option="USER_ENTERED",
            )
            return [["Date", "Type", "Symbol", "Quantity", "Price", "Amount", "Notes"]]
        return rows

    # No auth — try reading the sheet publicly
    rows = _read_public_sheet()
    if rows:
        return rows

    return SAMPLE_TRANSACTIONS


def append_transaction(
    txn_date: date,
    txn_type: str,
    symbol: str,
    quantity: float,
    price: float,
    amount: float,
    notes: str = "",
) -> bool:
    """Appends one transaction row to the sheet. Returns True on success."""
    ws = _get_worksheet()
    if ws is None:
        return False
    try:
        ws.append_row(
            [
                txn_date.strftime("%Y-%m-%d"),
                txn_type.upper(),
                symbol.upper().strip(),
                quantity,
                price,
                amount,
                notes,
            ],
            value_input_option="USER_ENTERED",
        )
        # Clear the data cache so next load_transactions fetches fresh rows
        st.cache_data.clear()
        return True
    except Exception:
        return False
