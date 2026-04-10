# ── Portfolio Tracker – Configuration ──────────────────────────────────────────

# Google Sheets
PORTFOLIO_SHEET_NAME = "Portfolio Tracker"      # Name of the Google Spreadsheet
TRANSACTIONS_WORKSHEET = "Transactions"          # Tab that holds all transactions

# Benchmark
BENCHMARK_SYMBOL = "^NSEI"      # Nifty 50 index
BENCHMARK_NAME   = "Nifty 50"

# Currency / locale
CURRENCY        = "₹"
CURRENCY_CODE   = "INR"

# yfinance download period for charts
CHART_PERIOD    = "1y"          # 1 year of history

# Column positions in the Transactions worksheet (0-indexed after header)
COL_DATE     = 0
COL_TYPE     = 1   # BUY | SELL | DEPOSIT | WITHDRAW
COL_SYMBOL   = 2   # e.g. RELIANCE.NS  (blank for cash transactions)
COL_QTY      = 3
COL_PRICE    = 4   # per-share price
COL_AMOUNT   = 5   # total ₹ amount  (+ve = money in, -ve = money out)
COL_NOTES    = 6

TRANSACTION_TYPES = ["BUY", "SELL", "DEPOSIT", "WITHDRAW"]
