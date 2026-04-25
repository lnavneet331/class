"""Google Sheets read / write helpers."""

from __future__ import annotations

import csv
import io
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
        try:
            sh = client.open_by_key(PORTFOLIO_SHEET_KEY)
        except Exception:
            sh = client.open(PORTFOLIO_SHEET_NAME)
        if TRANSACTIONS_WORKSHEET:
            try:
                ws = sh.worksheet(TRANSACTIONS_WORKSHEET)
            except gspread.WorksheetNotFound:
                ws = sh.get_worksheet(0)
        else:
            ws = sh.get_worksheet(0)
        return ws
    except Exception:
        return None


def _read_public_sheet() -> list[list[Any]] | None:
    """
    Read from the Google Sheet via its public CSV export URL.
    Works for sheets shared as 'Anyone with the link can view'.
    Reads the first visible tab when no worksheet name is configured.
    Returns a list-of-lists (header row first), or None on failure.
    """
    try:
        base = f"https://docs.google.com/spreadsheets/d/{PORTFOLIO_SHEET_KEY}/gviz/tq?tqx=out:csv"
        if TRANSACTIONS_WORKSHEET:
            url = f"{base}&sheet={TRANSACTIONS_WORKSHEET}"
        else:
            url = base
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

# Google Finance export format: matches the actual sheet structure
SAMPLE_TRANSACTIONS: list[list[Any]] = [
    ["Symbol", "Current Price", "Date", "Time", "Change", "Open", "High", "Low",
     "Volume", "Trade Date", "Purchase Price", "Quantity", "Commission",
     "High Limit", "Low Limit", "Comment", "Transaction Type"],
    ["$$CASH_TX", "", "", "", "", "", "", "", "", "20260410", "", "5000", "", "", "", "", "DEPOSIT"],
    ["$$CASH_TX", "", "", "", "", "", "", "", "", "20260210", "", "83690", "", "", "", "", "DEPOSIT"],
    ["HDFCBANK.NS", "", "", "", "", "", "", "", "", "20260330", "744.85", "10", "9", "", "", "", "BUY"],
    ["NIFTYBEES.NS", "", "", "", "", "", "", "", "", "20260313", "263.25", "25", "2", "", "", "", "BUY"],
    ["NIFTYBEES.NS", "", "", "", "", "", "", "", "", "20260309", "269.33", "25", "2", "", "", "", "BUY"],
    ["INFY.NS", "", "", "", "", "", "", "", "", "20260216", "1340.9", "4", "15", "", "", "", "BUY"],
    ["ADANIENT.NS", "", "", "", "", "", "", "", "", "20260123", "1905", "5", "", "", "", "", "BUY"],
    ["KALYANKJIL.NS", "", "", "", "", "", "", "", "", "20260123", "370", "40", "", "", "", "", "BUY"],
    ["KALYANKJIL.NS", "", "", "", "", "", "", "", "", "20260209", "437.35", "40", "40", "", "", "", "SELL"],
    ["TATACAP.NS", "", "", "", "", "", "", "", "", "20260129", "331.5", "20", "", "", "", "", "BUY"],
    ["WIPRO.NS", "", "", "", "", "", "", "", "", "20260212", "220", "23", "", "", "", "", "BUY"],
    ["WIPRO.NS", "", "", "", "", "", "", "", "", "20260210", "233.47", "21", "", "", "", "", "BUY"],
    ["GOLDBEES.NS", "", "", "", "", "", "", "", "", "20260130", "138.68", "72", "", "", "", "", "BUY"],
    ["GOLDBEES.NS", "", "", "", "", "", "", "", "", "20260410", "123.68", "72", "8", "", "", "", "BUY"],
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_sheets_connected() -> bool:
    return _get_client() is not None


def load_transactions() -> list[list[Any]]:
    """
    Returns all rows from the sheet (including header).

    Priority:
      1. Authenticated gspread (read + write)
      2. Public HTTP read from the hardcoded sheet key (read-only)
      3. Built-in sample data
    """
    ws = _get_worksheet()
    if ws is not None:
        rows = ws.get_all_values()
        if rows:
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
                "",                         # Symbol
                "",                         # Current Price
                "",                         # Date
                "",                         # Time
                "",                         # Change
                "",                         # Open
                "",                         # High
                "",                         # Low
                "",                         # Volume
                txn_date.strftime("%Y%m%d"),  # Trade Date (YYYYMMDD)
                price if txn_type.upper() in ("BUY", "SELL") else "",  # Purchase Price
                quantity if txn_type.upper() in ("BUY", "SELL") else amount,  # Quantity / Amount
                "",                         # Commission
                "",                         # High Limit
                "",                         # Low Limit
                notes,                      # Comment
                txn_type.upper(),           # Transaction Type
            ],
            value_input_option="USER_ENTERED",
        )
        st.cache_data.clear()
        return True
    except Exception:
        return False
