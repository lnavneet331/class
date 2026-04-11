# 📈 Portfolio Tracker

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=lnavneet331/class&branch=copilot/add-portfolio-tracker-feature&mainModule=streamlit_app.py)

A **Streamlit** web app for tracking a stock & ETF portfolio with two user roles (Admin / Viewer), live Yahoo Finance prices, and Google Sheets as the transaction database.

---

## 🚀 Try it instantly — no setup required

The app ships with **demo mode**: if no `secrets.toml` is configured, it uses built-in sample data and shows you the login credentials right on the login page.

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Full access – add transactions, view all KPIs |
| `father` | `father123` | Read-only portfolio dashboard |

---

## Deploy to Streamlit Community Cloud (one-click)

1. Click the **Deploy to Streamlit** badge above, or go to <https://share.streamlit.io>.
2. Connect your GitHub account and select this repo (`lnavneet331/class`).
3. Set **Main file path** to `streamlit_app.py` (repo root).
4. Click **Deploy** — the app runs in demo mode immediately.

### (Optional) Connect your real Google Sheet

In the Streamlit Cloud app → **Settings → Secrets**, paste:

```toml
[users.admin]
password     = "your_strong_admin_password"
role         = "admin"
display_name = "Portfolio Manager"

[users.father]
password     = "your_strong_father_password"
role         = "viewer"
display_name = "Dad's Portfolio"

[gcp_service_account]
type                        = "service_account"
project_id                  = "your-project-id"
private_key_id              = "key-id"
private_key                 = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email                = "your-sa@your-project.iam.gserviceaccount.com"
client_id                   = "1234567890"
auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
token_uri                   = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"
```

Then create a Google Spreadsheet named **`Portfolio Tracker`** and share it with the service-account email (Editor role). The app auto-creates the `Transactions` tab.

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
streamlit_app.py              ← Root entry point (Streamlit Cloud / local)
requirements.txt              ← Root-level deps (Streamlit Cloud auto-detects)
portfolio_tracker/
├── app.py                    ← Core Streamlit app
├── auth.py                   ← Login / session management
├── portfolio.py              ← Business logic & FIFO cost basis
├── sheets_manager.py         ← Google Sheets read/write
├── config.py                 ← Constants
├── requirements.txt          ← Deps for local portfolio_tracker/ runs
└── .streamlit/
    ├── config.toml           ← UI theme
    └── secrets.toml.example  ← Credentials template
```

---

## Local Quick Start

```bash
# From repo root
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Or run directly from the sub-directory:

```bash
cd portfolio_tracker
pip install -r requirements.txt
streamlit run app.py
```

---

## Transaction Format

| Type | Symbol | Qty | Price | Amount | Example |
|---|---|---|---|---|---|
| `BUY` | `RELIANCE.NS` | 10 | 2400 | 24000 | Buy 10 shares @ ₹2400 |
| `SELL` | `TCS.NS` | 5 | 3600 | 18000 | Sell 5 shares @ ₹3600 |
| `DEPOSIT` | *(blank)* | 0 | 0 | 500000 | Add ₹5L to portfolio |
| `WITHDRAW` | *(blank)* | 0 | 0 | -50000 | Withdraw ₹50k (negative) |

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
- **Add users**: Add new `[users.username]` blocks in Streamlit Cloud secrets or `secrets.toml`.

