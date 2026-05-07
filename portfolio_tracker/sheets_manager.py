"""Google Sheets read / write helpers."""

from __future__ import annotations

import csv
import io
import logging
import re
import time
import urllib.parse
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
logger = logging.getLogger(__name__)

_SHEET_URL_SECRET_KEYS = (
    "portfolio_sheet_url",
    "PORTFOLIO_SHEET_URL",
    "portfolio_sheet_key",
    "PORTFOLIO_SHEET_KEY",
)
_MIN_SHEET_KEY_LENGTH = 20

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


def _extract_sheet_key(value: str) -> str | None:
    """Extract Google Sheet key from a full URL or return key as-is."""
    raw = (value or "").strip()
    if not raw:
        return None

    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", raw)
    if m:
        return m.group(1)

    if re.fullmatch(rf"[a-zA-Z0-9-_]{{{_MIN_SHEET_KEY_LENGTH},}}", raw):
        return raw

    return None


def _extract_sheet_gid(value: str) -> str | None:
    """Extract Google Sheet gid (tab id) from a full URL, if present."""
    raw = (value or "").strip()
    if not raw:
        return None

    m = re.search(r"[?&]gid=(\d+)", raw)
    if m:
        return m.group(1)
    return None


def _get_sheet_secret_value() -> str | None:
    """Get the first available sheet secret value."""
    for secret_key in _SHEET_URL_SECRET_KEYS:
        try:
            if secret_key in st.secrets:
                return str(st.secrets[secret_key])
        except Exception:
            continue
    return None


def _get_sheet_key() -> str:
    """Get sheet key from secrets first, then fall back to config constant."""
    secret_value = _get_sheet_secret_value()
    if secret_value is not None:
        extracted = _extract_sheet_key(secret_value)
        if extracted:
            return extracted
        logger.warning("Invalid Google Sheet URL/key in secrets; falling back to config key.")
    return PORTFOLIO_SHEET_KEY


def _get_sheet_gid() -> str | None:
    """Get sheet gid from secrets URL (if provided)."""
    secret_value = _get_sheet_secret_value()
    if not secret_value:
        return None
    return _extract_sheet_gid(secret_value)


def _get_worksheet() -> gspread.Worksheet | None:
    client = _get_client()
    if client is None:
        return None
    sheet_key = _get_sheet_key()
    if not sheet_key:
        return None
    try:
        try:
            sh = client.open_by_key(sheet_key)
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
        sheet_key = _get_sheet_key()
        if not sheet_key:
            return None
        base = f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv"
        if TRANSACTIONS_WORKSHEET:
            sheet_name = urllib.parse.quote_plus(TRANSACTIONS_WORKSHEET)
            url = f"{base}&sheet={sheet_name}"
        elif (gid := _get_sheet_gid()):
            url = f"{base}&gid={gid}"
        else:
            url = base
        cache_bust = int(time.time() * 1000)
        url = f"{url}&_cb={cache_bust}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
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
