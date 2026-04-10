"""Google Sheets read / write helpers."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

from config import (
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


# ---------------------------------------------------------------------------
# Sample data (used when Google Sheets is not configured)
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
    """Returns all rows from the Transactions sheet (including header)."""
    ws = _get_worksheet()
    if ws is None:
        return SAMPLE_TRANSACTIONS

    rows = ws.get_all_values()
    if not rows:
        # Sheet exists but is empty – write header
        ws.append_row(
            ["Date", "Type", "Symbol", "Quantity", "Price", "Amount", "Notes"],
            value_input_option="USER_ENTERED",
        )
        return [["Date", "Type", "Symbol", "Quantity", "Price", "Amount", "Notes"]]
    return rows


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
