import os
import sqlite3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_fetcher import StockDataFetcher, get_stock_info
from trading_signals import AdvancedTradingSignals
from database import (
    init_database,
    add_transaction,
    add_to_watchlist,
    add_price_alert,
    get_watchlist,
    get_transactions,
    get_signals_history,
    record_signal,
)
from ml_predictor import MLStockPredictor


st.set_page_config(page_title="Advanced Stock Dashboard", page_icon="📈", layout="wide")

init_database()

fetcher = StockDataFetcher()
signal_engine = AdvancedTradingSignals()
predictor = MLStockPredictor()


def format_currency(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"


st.title("Advanced Stock Market Dashboard")
st.caption("Advanced technical analysis, AI signal scoring, portfolio tracking, and market alerts.")
st.caption("Educational use only — not financial advice.")

with st.sidebar:
    st.header("Controls")
    ticker = st.text_input("Ticker", value="AAPL").upper()
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    interval = st.selectbox("Interval", ["1d", "1wk"], index=0)
    st.markdown("---")

    st.subheader("Add Transaction")
    tx_action = st.selectbox("Action", ["BUY", "SELL"])
    tx_quantity = st.number_input("Quantity", min_value=0.0, step=1.0, value=1.0)
    tx_price = st.number_input("Price", min_value=0.0, step=0.01, value=0.0)
    tx_commission = st.number_input("Commission", min_value=0.0, step=0.01, value=0.0)
    notes = st.text_input("Notes", value="")

    if st.button("Record Transaction"):
        if tx_price <= 0:
            st.warning("Price must be greater than zero.")
        else:
            add_transaction(ticker, tx_action, tx_quantity, tx_price, tx_commission, notes)
            st.success(f"{tx_action} order recorded for {ticker}.")

    st.markdown("---")
    st.subheader("Watchlist")
    watch_ticker = st.text_input("Add to watchlist", value="MSFT")
    if st.button("Add Watchlist Item"):
        add_to_watchlist(watch_ticker)
        st.success(f"{watch_ticker.upper()} added to watchlist")

    st.subheader("Price Alert")
    alert_ticker = st.text_input("Alert Ticker", value="NVDA")
    alert_type = st.selectbox("Alert Type", ["ABOVE", "BELOW"])
    alert_threshold = st.number_input("Threshold", min_value=0.0, step=0.01, value=0.0)
    if st.button("Create Alert"):
        if alert_threshold <= 0:
            st.warning("Threshold must be > 0.")
        else:
            add_price_alert(alert_ticker, alert_type, alert_threshold)
            st.success(f"Alert created for {alert_ticker.upper()}.")

    st.markdown("---")
    st.subheader("Overview")
    st.write("Signals are based on multiple indicators: SMA, EMA, MACD, RSI, Bollinger Bands, Stoch., volume, ROC, and ADX.")


if ticker:
    with st.spinner(f"Loading {ticker} data..."):
        history = fetcher.get_stock_data(ticker, period=period, interval=interval)
        current_price = fetcher.get_current_price(ticker)
        info = get_stock_info(ticker)

    if history is None:
        st.warning(f"No valid data available for {ticker}. Check the ticker and try again.")
        st.stop()

    signal = signal_engine.analyze_stock(history, ticker)
    if signal is None:
        st.warning("Not enough data for reliable analysis.")
        st.stop()

    levels = signal_engine.get_buy_sell_levels(history, current_price)

    if ticker not in predictor.models:
        ml_result = predictor.train_model(history, ticker)
    else:
        ml_result = None

    prediction = predictor.predict(history, ticker)

    if prediction is not None:
        probability_up = prediction["probability_up"] * 100
        confidence = prediction["confidence"]
    else:
        probability_up = 0
        confidence = 0

    st.subheader(f"{ticker} — {info['name'] if info else ticker}")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Current Price", format_currency(current_price))
    kpi2.metric("Signal", signal["signal"], f"{signal['strength']:.2f} strength")
    kpi3.metric("Signal Confidence", f"{signal['confidence']:.1f}%")
    kpi4.metric("ML Up Probability", f"{probability_up:.1f}%")

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Buy Level", format_currency(levels["buy_level_conservative"]))
    colB.metric("Sell Level", format_currency(levels["sell_level_conservative"]))
    colC.metric("Support", format_currency(levels["support"]))
    colD.metric("Resistance", format_currency(levels["resistance"]))

    st.markdown("---")

    chart_col, summary_col = st.columns([2.5, 1.3])

    with chart_col:
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=history.index,
                    open=history["Open"],
                    high=history["High"],
                    low=history["Low"],
                    close=history["Close"],
                    name="Price",
                )
            ]
        )
        fig.add_trace(go.Scatter(x=history.index, y=history["SMA_20"], mode="lines", name="SMA 20"))
        fig.add_trace(go.Scatter(x=history.index, y=history["SMA_50"], mode="lines", name="SMA 50"))
        fig.add_trace(go.Scatter(x=history.index, y=history["SMA_200"], mode="lines", name="SMA 200"))
        fig.update_layout(legend=dict(orientation="h"), template="plotly_dark", height=600)
        st.plotly_chart(fig, use_container_width=True)

    with summary_col:
        st.subheader("Buy / Sell Recommendation")
        if signal["signal"] == "BUY":
            st.success(f"Recommended Action: BUY")
        elif signal["signal"] == "SELL":
            st.error(f"Recommended Action: SELL")
        else:
            st.warning(f"Recommended Action: HOLD")

        st.write(f"Signal strength: {signal['strength']:.2f}")
        st.write(f"Signal confidence: {signal['confidence']:.1f}%")
        st.write(f"ML probability for upside: {probability_up:.1f}%")
        st.write(f"Current price: {format_currency(current_price)}")

        st.markdown("---")
        st.subheader("Key technical checks")
        for name, value in signal["components"].items():
            if "score" in value:
                st.write(f"{name.replace('_', ' ').title()}: {value['score']:.1f}")

    st.markdown("---")

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.subheader("Company Overview")
        if info:
            st.write(f"Name: {info.get('name', 'N/A')}")
            st.write(f"Sector: {info.get('sector', 'N/A')}")
            st.write(f"Industry: {info.get('industry', 'N/A')}")
            st.write(f"Market Cap: {info.get('market_cap', 'N/A')}")
            st.write(f"P/E Ratio: {info.get('pe_ratio', 'N/A')}")
            st.write(f"Dividend Yield: {info.get('dividend_yield', 'N/A')}")
            st.write(f"52 Week High: {format_currency(info.get('52_week_high'))}")
            st.write(f"52 Week Low: {format_currency(info.get('52_week_low'))}")
            st.write(f"Average Volume: {info.get('average_volume', 'N/A')}")
            st.write(f"Beta: {info.get('beta', 'N/A')}")

    with info_col2:
        st.subheader("Signal Logic")
        st.write("- Moving averages: trend direction")
        st.write("- MACD: momentum and crossover")
        st.write("- RSI: overbought/oversold conditions")
        st.write("- Bollinger Bands: volatility expansion and compression")
        st.write("- Stochastic Oscillator: momentum trend confirmation")
        st.write("- Volume ratio: institutional participation")
        st.write("- ROC: trend acceleration")
        st.write("- ADX: trend strength")

    st.markdown("---")
    st.subheader("Portfolio")
    transactions = get_transactions()
    if transactions:
        tx_df = pd.DataFrame(
            transactions,
            columns=["id", "ticker", "action", "quantity", "price", "date", "commission", "notes"],
        )
        st.dataframe(tx_df, use_container_width=True)
    else:
        st.info("No transactions yet. Add one from the sidebar.")

    st.subheader("Watchlist")
    watchlist = get_watchlist()
    if watchlist:
        watch_df = pd.DataFrame(watchlist, columns=["id", "ticker", "added_date", "target_buy_price", "target_sell_price", "alerts_enabled"])
        st.dataframe(watch_df, use_container_width=True)
    else:
        st.info("No watchlist items yet.")

    st.subheader("Recent Signals")
    signal_history = get_signals_history(ticker, limit=20)
    if signal_history:
        hist_df = pd.DataFrame(
            signal_history,
            columns=["id", "ticker", "signal_type", "signal_strength", "components", "date", "price", "confidence"],
        )
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("No recent recorded signals yet.")

    record_signal(ticker, signal["signal"], signal["strength"], signal["components"], current_price, signal["confidence"])

st.markdown("---")
st.caption("This dashboard is a stock-analysis tool for research and educational purposes only. It does not guarantee profits or provide financial advice.")
