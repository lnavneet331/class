# 📈 Portfolio Tracker

A **Streamlit** web app for tracking a stock & ETF portfolio with two user roles (Admin / Viewer), live Yahoo Finance prices, and Google Sheets as the transaction database.

---

## Features

| Feature | Details |
|---|---|
| **Two-role login** | `admin` – full access + add transactions · `father` – read-only dashboard |
| **Live prices** | Yahoo Finance via `yfinance` (NSE `.NS`, BSE `.BO`, ETFs) |
| **KPIs** | Unrealized P&L · Realized P&L · Portfolio Return · Portfolio Beta · Weighted Avg P/E · Alpha vs Nifty 50 |
| **Per-stock fundamentals** | Beta · P/E · Forward P/E · P/B · EPS · ROE · Div Yield · 52-week range |
| **Benchmark comparison** | Nifty 50 (`^NSEI`) – chart + alpha |
| **Charts** | Asset allocation pie · Sector breakdown bar · Benchmark % return line |
| **Google Sheets backend** | Transactions sheet read/write via `gspread` |
| **Demo mode** | Works with built-in sample data when Sheets isn't configured |

---

## Directory Structure

```
portfolio_tracker/
├── app.py                    ← Streamlit entry point
├── auth.py                   ← Login / session management
├── portfolio.py              ← Business logic & FIFO cost basis
├── sheets_manager.py         ← Google Sheets read/write
├── config.py                 ← Constants
├── requirements.txt          ← Python dependencies
├── .streamlit/
│   └── secrets.toml.example  ← Credentials template
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
cd portfolio_tracker
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:
- Set strong passwords for `admin` and `father` users.
- Paste your **Google Service Account** JSON fields under `[gcp_service_account]`.

### 3. Set up Google Sheets

1. Create a Google Spreadsheet named **`Portfolio Tracker`** (or change `PORTFOLIO_SHEET_NAME` in `config.py`).
2. Share the spreadsheet with your service-account email (Editor role).
3. The app will auto-create a **`Transactions`** tab with the correct headers on first run.

> **Transaction columns:** `Date | Type | Symbol | Quantity | Price | Amount | Notes`

| Type | Symbol | Qty | Price | Amount | Example |
|---|---|---|---|---|---|
| `BUY` | `RELIANCE.NS` | 10 | 2400 | 24000 | Buy 10 shares of Reliance @ ₹2400 |
| `SELL` | `TCS.NS` | 5 | 3600 | 18000 | Sell 5 shares of TCS @ ₹3600 |
| `DEPOSIT` | *(blank)* | 0 | 0 | 500000 | Add ₹5L to portfolio |
| `WITHDRAW` | *(blank)* | 0 | 0 | -50000 | Withdraw ₹50k from portfolio |

### 4. Run the app

```bash
streamlit run app.py
```

Open <http://localhost:8501> in your browser.

---

## User Roles

| Username | Default password | Role | Permissions |
|---|---|---|---|
| `admin` | `admin123` *(change this!)* | Admin | Add transactions + full dashboard |
| `father` | `father123` *(change this!)* | Viewer | Read-only portfolio dashboard |

> Passwords are set in `.streamlit/secrets.toml`.  The defaults are only for demo/testing.

---

## Common Indian Symbols

| Stock/ETF | Yahoo Finance symbol |
|---|---|
| Reliance Industries | `RELIANCE.NS` |
| TCS | `TCS.NS` |
| HDFC Bank | `HDFCBANK.NS` |
| Infosys | `INFY.NS` |
| Nifty 50 ETF (NipponAMC) | `NIFTYBEES.NS` |
| Nifty 50 Index | `^NSEI` (benchmark only) |
| Sensex | `^BSESN` |

---

## Customising

- **Benchmark**: Change `BENCHMARK_SYMBOL` in `config.py` (e.g. `^BSESN` for Sensex).
- **Sheet name**: Change `PORTFOLIO_SHEET_NAME` in `config.py`.
- **Chart period**: Change `CHART_PERIOD` in `config.py` (e.g. `"6mo"`, `"2y"`).
- **Add more users**: Add new `[users.username]` blocks in `secrets.toml`.

---

## Deploy to Streamlit Community Cloud

1. Push your repo (without `secrets.toml`) to GitHub.
2. Go to <https://share.streamlit.io> → New app → select `portfolio_tracker/app.py`.
3. In **Advanced settings → Secrets**, paste the contents of your `secrets.toml`.
