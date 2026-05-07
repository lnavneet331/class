"""
Portfolio Tracker – main Streamlit entry point.

Run with:
    streamlit run portfolio_tracker/app.py        (from repo root)
    streamlit run app.py                          (from portfolio_tracker/)
    streamlit run streamlit_app.py                (from repo root via root entry-point)
"""

from __future__ import annotations

import logging
import os
import sys

# Ensure portfolio_tracker's own directory is on the path so peer modules
# (auth, config, portfolio, sheets_manager) are importable regardless of the
# working directory Streamlit is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import auth
import sheets_manager as sm
from config import CURRENCY, TRANSACTION_TYPES, BENCHMARK_NAME
from portfolio import build_portfolio

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Portfolio Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Auth gate
# ──────────────────────────────────────────────────────────────────────────────

if not auth.is_authenticated():
    auth.render_login_page()
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"### 👤 {auth.get_display_name()}")
    st.markdown(f"Role: **{auth.get_role().title()}**")
    st.markdown("---")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        try:
            rows = sm.load_transactions()
            if rows:
                logger.info("Reload successful: loaded %d row(s).", len(rows))
            else:
                logger.warning("Reload failed: load_transactions returned no rows.")
        except Exception as exc:
            logger.exception("Reload failed with exception: %s", exc)
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        auth.logout()
        st.rerun()

    st.markdown("---")
    connected = sm.is_sheets_connected()
    if connected:
        st.success("🟢 Google Sheets connected")
    else:
        st.warning("🟡 Read-only – Google Sheets write access not configured")

    st.markdown("---")
    st.caption("Portfolio Tracker v1.0")


# ──────────────────────────────────────────────────────────────────────────────
# Data loading (cached)
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner="Loading portfolio data…")
def _load_portfolio():
    rows = sm.load_transactions()
    return build_portfolio(rows)


data = _load_portfolio()
holdings   = data["holdings"]
txns       = data["transactions"]
has_holdings = isinstance(holdings, pd.DataFrame) and not holdings.empty


# ──────────────────────────────────────────────────────────────────────────────
# Helper formatters
# ──────────────────────────────────────────────────────────────────────────────

def _fmt(val: float | None, decimals: int = 2, prefix: str = "") -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return f"{prefix}{val:,.{decimals}f}"


def _inr(val: float | None) -> str:
    return _fmt(val, 0, CURRENCY)


def _pct(val: float | None) -> str:
    return _fmt(val, 2) + "%" if val is not None else "N/A"


def _delta_color(val: float | None) -> str:
    if val is None:
        return "off"
    return "normal" if val >= 0 else "inverse"


# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 1: Summary KPI cards ─────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

st.title("📈 Portfolio Dashboard")
if not sm.is_sheets_connected():
    st.info("ℹ️ Read-only mode — Google Sheets write access not configured. Transactions are loaded from the sheet but cannot be added here.")

st.markdown("---")

c1, c2, c3, c4, c5, c6 = st.columns(6)

total_value      = data.get("total_value", 0)
total_invested   = data.get("total_invested", 0)
unrealized_pnl   = data.get("unrealized_pnl", 0)
realized_pnl     = data.get("realized_pnl", 0)
portfolio_return = data.get("portfolio_return", 0)
benchmark_return = data.get("benchmark_return", 0)
alpha            = data.get("alpha", 0)
portfolio_beta   = data.get("portfolio_beta")
portfolio_pe     = data.get("portfolio_pe")
cash_balance     = data.get("cash_balance", 0)

with c1:
    st.metric("💼 Portfolio Value",
              _inr(total_value),
              delta=_inr(unrealized_pnl + realized_pnl) + " total P&L")
with c2:
    st.metric("💰 Total Invested",
              _inr(total_invested))
with c3:
    st.metric("📊 Portfolio Return",
              _pct(portfolio_return),
              delta=_pct(alpha) + f" vs {BENCHMARK_NAME}")
with c4:
    st.metric(f"📉 {BENCHMARK_NAME} Return",
              _pct(benchmark_return))
with c5:
    beta_str = _fmt(portfolio_beta, 2) if portfolio_beta is not None else "N/A"
    st.metric("⚡ Portfolio Beta", beta_str)
with c6:
    pe_str = _fmt(portfolio_pe, 1) if portfolio_pe is not None else "N/A"
    st.metric("📐 Wtd. Avg P/E", pe_str)

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 2: Admin – Add Transaction ───────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

if auth.get_role() == auth.ROLE_ADMIN:
    with st.expander("➕ Add New Transaction", expanded=False):
        with st.form("add_txn_form", clear_on_submit=True):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                txn_date = st.date_input("Date", value=date.today())
                txn_type = st.selectbox("Type", TRANSACTION_TYPES)
            with col_b:
                symbol   = st.text_input("Symbol (e.g. RELIANCE.NS)",
                                          help="Leave blank for DEPOSIT / WITHDRAW")
                quantity = st.number_input("Quantity (shares)", min_value=0.0, step=1.0)
            with col_c:
                price  = st.number_input(f"Price per share ({CURRENCY})", min_value=0.0, step=0.01)
                amount = st.number_input(
                    f"Amount ({CURRENCY})  [–ve for WITHDRAW]",
                    value=round(quantity * price, 2),
                    step=0.01,
                )
            notes   = st.text_input("Notes (optional)")
            submit  = st.form_submit_button("Submit Transaction", use_container_width=True)

            if submit:
                if txn_type in ("BUY", "SELL") and not symbol.strip():
                    st.error("Symbol is required for BUY / SELL transactions.")
                elif txn_type == "WITHDRAW" and amount > 0:
                    st.error(
                        "Amount must be **negative** for WITHDRAW transactions "
                        f"(e.g. enter −{abs(amount):,.0f} to withdraw {CURRENCY}{abs(amount):,.0f})."
                    )
                else:
                    ok = sm.append_transaction(
                        txn_date, txn_type, symbol, quantity, price, amount, notes
                    )
                    if ok:
                        st.success("✅ Transaction added to Google Sheets!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Failed to write to Google Sheets. Check credentials.")

    st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 3: Holdings table ────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📋 Current Holdings")
    if has_holdings:
        display_cols = {
            "Name":          "Name",
            "Symbol":        "Symbol",
            "Quantity":      "Qty",
            "Avg_Cost":      "Avg Cost",
            "Current_Price": "LTP",
            "Current_Value": "Value",
            "Unrealized_PnL":"Unreal. P&L",
            "PnL_Pct":       "P&L %",
            "Beta":          "Beta",
            "PE":            "P/E",
            "Div_Yield":     "Div Yield",
        }
        disp = holdings[[c for c in display_cols if c in holdings.columns]].copy()
        disp.columns = [display_cols[c] for c in display_cols if c in holdings.columns]

        # Format numeric columns
        for col_name in ["Avg Cost", "LTP", "Value", "Unreal. P&L"]:
            if col_name in disp.columns:
                disp[col_name] = disp[col_name].apply(
                    lambda x: f"{CURRENCY}{x:,.0f}" if pd.notna(x) and x != 0 else "—"
                )
        for col_name in ["P&L %"]:
            if col_name in disp.columns:
                disp[col_name] = disp[col_name].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
                )
        for col_name in ["Div Yield"]:
            if col_name in disp.columns:
                disp[col_name] = disp[col_name].apply(
                    lambda x: f"{x*100:.2f}%" if pd.notna(x) and x else "—"
                )

        st.dataframe(disp, use_container_width=True, hide_index=True)

        # Realized & unrealized summary
        r1, r2, r3 = st.columns(3)
        r1.metric("Unrealized P&L", _inr(unrealized_pnl),
                  delta=_pct(unrealized_pnl / (holdings["Total_Cost"].sum()) * 100
                             if holdings["Total_Cost"].sum() else None))
        r2.metric("Realized P&L",   _inr(realized_pnl))
        r3.metric("Cash Balance",   _inr(cash_balance))
    else:
        st.info("No holdings yet. Add BUY transactions to see your portfolio.")


# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 4: Asset allocation pie ─────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

with col_right:
    st.subheader("🥧 Asset Allocation")
    if has_holdings:
        alloc = holdings[["Symbol", "Current_Value"]].copy()
        if cash_balance > 0:
            alloc = pd.concat([
                alloc,
                pd.DataFrame([{"Symbol": "CASH", "Current_Value": cash_balance}])
            ], ignore_index=True)
        fig_pie = px.pie(
            alloc, values="Current_Value", names="Symbol",
            hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=True,
                               legend=dict(orientation="h"))
        st.plotly_chart(fig_pie, use_container_width=True)

        # Sector allocation
        if "Sector" in holdings.columns and holdings["Sector"].notna().any():
            st.subheader("🏭 Sector Breakdown")
            sector_alloc = (
                holdings[holdings["Sector"].notna() & (holdings["Sector"] != "")]
                .groupby("Sector")["Current_Value"].sum()
                .reset_index()
            )
            fig_sec = px.bar(
                sector_alloc, x="Sector", y="Current_Value",
                color="Sector", text_auto=True,
                labels={"Current_Value": f"Value ({CURRENCY})"},
            )
            fig_sec.update_layout(showlegend=False, margin=dict(t=10, b=40))
            st.plotly_chart(fig_sec, use_container_width=True)
    else:
        st.info("No data to display.")

st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 5: Benchmark comparison chart ────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

st.subheader(f"📉 Benchmark Comparison  –  {BENCHMARK_NAME}")

chart_data = data.get("chart_data", pd.DataFrame())
if not chart_data.empty:
    fig_bench = px.line(
        chart_data,
        labels={"value": "Return (%)", "variable": ""},
        color_discrete_map={BENCHMARK_NAME: "#EF553B"},
    )
    fig_bench.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_bench.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05),
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_tickformat=".1f",
        yaxis_ticksuffix="%",
    )
    st.plotly_chart(fig_bench, use_container_width=True)

    col_bm1, col_bm2, col_bm3 = st.columns(3)
    col_bm1.metric(f"{BENCHMARK_NAME} 1Y Return", _pct(benchmark_return))
    col_bm2.metric("Portfolio Return",             _pct(portfolio_return))
    col_bm3.metric("Alpha (outperformance)",       _pct(alpha),
                   delta_color="normal" if alpha >= 0 else "inverse")
else:
    st.info("Benchmark data unavailable. Check internet connectivity.")

st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 6: Individual stock KPIs ─────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

if has_holdings:
    st.subheader("🔬 Stock-level Fundamentals")
    fundamentals = data.get("fundamentals", {})

    for sym in holdings["Symbol"].tolist():
        f = fundamentals.get(sym, {})
        curr_price = holdings.loc[holdings["Symbol"] == sym, "Current_Price"].values
        curr_price = curr_price[0] if len(curr_price) else None
        h52   = f.get("52w_high")
        l52   = f.get("52w_low")
        name  = f.get("name", sym)

        with st.expander(f"**{name}** ({sym})", expanded=False):
            kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)
            kc1.metric("Current Price",  _inr(curr_price))
            kc2.metric("Beta",           _fmt(f.get("beta"), 2))
            kc3.metric("Trailing P/E",   _fmt(f.get("pe_ratio"), 1))
            kc4.metric("Forward P/E",    _fmt(f.get("forward_pe"), 1))
            kc5.metric("P/B Ratio",      _fmt(f.get("pb_ratio"), 2))
            kc6.metric("Div. Yield",
                       f"{f['dividend_yield']*100:.2f}%"
                       if f.get("dividend_yield") else "N/A")

            kc7, kc8, kc9, kc10 = st.columns(4)
            kc7.metric("52W High",  _inr(h52))
            kc8.metric("52W Low",   _inr(l52))
            kc9.metric("EPS",       _fmt(f.get("eps"), 2))
            kc10.metric("ROE",
                        f"{f['roe']*100:.1f}%"
                        if f.get("roe") else "N/A")

            # 52-week range progress bar
            if h52 and l52 and curr_price and h52 > l52:
                pct_in_range = (curr_price - l52) / (h52 - l52)
                st.caption(f"52W Range position: {pct_in_range*100:.0f}% of range  "
                           f"({_inr(l52)} ← {_inr(curr_price)} → {_inr(h52)})")
                st.progress(min(max(pct_in_range, 0.0), 1.0))

    st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 7: Transaction history ───────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

st.subheader("📜 Transaction History")
if not txns.empty:
    show_txns = txns.copy()
    show_txns["Date"] = show_txns["Date"].dt.strftime("%Y-%m-%d")
    show_txns = show_txns.sort_values("Date", ascending=False)

    # Color by type
    def _type_icon(t):
        return {"BUY": "🟢 BUY", "SELL": "🔴 SELL",
                "DEPOSIT": "🔵 DEPOSIT", "WITHDRAW": "🟠 WITHDRAW"}.get(t, t)

    show_txns["Type"] = show_txns["Type"].apply(_type_icon)
    show_txns["Amount"] = show_txns["Amount"].apply(
        lambda x: f"{CURRENCY}{abs(x):,.0f}" if pd.notna(x) else "—"
    )
    show_txns["Price"] = show_txns["Price"].apply(
        lambda x: f"{CURRENCY}{x:,.2f}" if pd.notna(x) and x > 0 else "—"
    )
    st.dataframe(
        show_txns[["Date", "Type", "Symbol", "Quantity", "Price", "Amount", "Notes"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No transactions found.")
