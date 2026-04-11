# ── Portfolio Tracker – Configuration ──────────────────────────────────────────

# Google Sheets
PORTFOLIO_SHEET_KEY  = "1sZEIJS-k5ukXNQHVfpaAqbx0cB-Ie5O7n0YB59uSSLo"  # Sheet ID from URL
PORTFOLIO_SHEET_NAME = "Portfolio Tracker"      # Fallback: open by name
TRANSACTIONS_WORKSHEET = ""    # Tab name; empty = read first visible tab

# Benchmark
BENCHMARK_SYMBOL = "^NSEI"      # Nifty 50 index
BENCHMARK_NAME   = "Nifty 50"

# Currency / locale
CURRENCY        = "₹"
CURRENCY_CODE   = "INR"

# yfinance download period for charts
CHART_PERIOD    = "1y"          # 1 year of history

TRANSACTION_TYPES = ["BUY", "SELL", "DEPOSIT", "WITHDRAW"]
