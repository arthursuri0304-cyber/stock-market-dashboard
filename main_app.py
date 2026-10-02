import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
from wealth_database import (
    init_database, add_holding, add_contribution, add_goal,
    get_portfolio, get_contributions, get_goals, add_trade, get_trades, add_alert
)
from data_fetcher import StockDataFetcher
from trading_signals import AdvancedTradingSignals
import config

st.set_page_config(
    page_title="Wealth & Trading Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_database()
fetcher = StockDataFetcher()
signals = AdvancedTradingSignals()

st.markdown("""
<style>
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; }
    .positive { color: #00ff41; font-weight: bold; }
    .negative { color: #ff0033; font-weight: bold; }
    .neutral { color: #ffaa00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

page = st.sidebar.radio("📱 Navigation", ["💰 Wealth Dashboard", "📈 Trading Hub", "⚙️ Settings"], label_visibility="collapsed")

if page == "💰 Wealth Dashboard":
    st.title("💰 Wealth Builder")
    
    # Get portfolio data
    portfolio = get_portfolio()
    contributions = get_contributions()
    goals = get_goals()
    
    # Calculate totals
    total_invested = sum([c[2] for c in contributions]) if contributions else 0
    total_value = 0
    holdings_list = []
    
    if portfolio:
        for p in portfolio:
            symbol = p[1]
            shares = p[2]
            try:
                price = fetcher.get_current_price(symbol)
                if price:
                    value = shares * price
                    total_value += value
                    holdings_list.append({"symbol": symbol, "shares": shares, "price": price, "value": value})
            except:
                pass
    
    gain = total_value - total_invested
    gain_pct = (gain / total_invested * 100) if total_invested > 0 else 0
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💵 Portfolio Value", f"${total_value:,.2f}", delta=f"+{gain:,.2f}" if gain >= 0 else f"{gain:,.2f}")
    
    with col2:
        st.metric("📊 Total Invested", f"${total_invested:,.2f}")
    
    with col3:
        st.metric("📈 Unrealized Gain", f"${gain:,.2f}", delta=f"{gain_pct:.1f}%")
    
    with col4:
        months = len(set([c[1][:7] for c in contributions])) if contributions else 0
        st.metric("⏰ Months Invested", months)
    
    st.markdown("---")
    
    # Holdings and contributions side by side
    col_holdings, col_contrib = st.columns(2)
    
    with col_holdings:
        st.subheader("Your Holdings")
        if holdings_list:
            holdings_df = pd.DataFrame(holdings_list)
            st.dataframe(holdings_df, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No holdings yet")
    
    with col_contrib:
        st.subheader("Recent Contributions")
        if contributions:
            contrib_df = pd.DataFrame(contributions[-5:], columns=["ID", "Date", "Amount", "Symbol", "Shares"])
            st.dataframe(contrib_df[["Date", "Amount", "Symbol"]], use_container_width=True, hide_index=True)
        else:
            st.info("📭 No contributions yet")
    
    st.markdown("---")
    
    # Add contribution section
    st.subheader("➕ Add Monthly Contribution")
    col_add1, col_add2, col_add3 = st.columns(3)
    
    with col_add1:
        add_amount = st.number_input("Amount ($)", min_value=1.0, step=1.0, value=50.0)
    
    with col_add2:
        add_symbol = st.selectbox("Symbol", ["VOO", "VTI", "VXUS", "BND", "AAPL", "MSFT", "Other"])
    
    with col_add3:
        if st.button("💾 Record Contribution"):
            add_contribution(add_amount, add_symbol)
            st.success(f"✅ Added ${add_amount} to {add_symbol}")
            st.rerun()
    
    st.markdown("---")
    
    # Goals section
    st.subheader("🎯 Wealth Goals")
    
    col_goal_view, col_goal_add = st.columns(2)
    
    with col_goal_view:
        if goals:
            for goal in goals:
                goal_id, name, target, current, target_date = goal
                progress = (current / target * 100) if target > 0 else 0
                st.write(f"**{name}** ({target_date})")
                st.progress(min(progress / 100, 1.0))
                st.caption(f"${current:,.0f} / ${target:,.0f}")
        else:
            st.info("🎯 No goals yet")
    
    with col_goal_add:
        st.write("**Add New Goal**")
        goal_name = st.text_input("Goal Name", value="Emergency Fund")
        goal_target = st.number_input("Target Amount ($)", min_value=100.0, step=100.0, value=5000.0)
        goal_date = st.date_input("Target Date")
        
        if st.button("🎯 Set Goal"):
            add_goal(goal_name, goal_target, goal_date.strftime("%Y-%m-%d"))
            st.success(f"Goal '{goal_name}' created!")
            st.rerun()
    
    st.markdown("---")
    
    # Projections
    st.subheader("📊 Wealth Projection")
    
    col_proj1, col_proj2, col_proj3 = st.columns(3)
    
    with col_proj1:
        proj_monthly = st.number_input("Monthly Investment ($)", min_value=1.0, step=10.0, value=config.DEFAULT_MONTHLY_INVESTMENT)
    
    with col_proj2:
        proj_return = st.slider("Annual Return (%)", 0.0, 20.0, config.DEFAULT_ANNUAL_RETURN)
    
    with col_proj3:
        proj_years = st.slider("Years", 1, 40, 10)
    
    if st.button("📈 Calculate"):
        # Calculate projection
        months = proj_years * 12
        monthly_return = (proj_return / 100) / 12
        
        fv_current = total_value * ((1 + monthly_return) ** months)
        fv_contrib = proj_monthly * (((1 + monthly_return) ** months - 1) / monthly_return) if monthly_return > 0 else proj_monthly * months
        future_value = fv_current + fv_contrib
        total_contrib = total_invested + (proj_monthly * 12 * proj_years)
        projected_gain = future_value - total_contrib
        
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Projected Value", f"${future_value:,.0f}")
        col_r2.metric("Total Contributions", f"${total_contrib:,.0f}")
        col_r3.metric("Investment Gains", f"${projected_gain:,.0f}")

elif page == "📈 Trading Hub":
    st.title("📈 Trading & Signals")
    
    col_ticker, col_period = st.columns(2)
    
    with col_ticker:
        ticker = st.text_input("Stock Ticker", value="AAPL").upper()
    
    with col_period:
        period = st.selectbox("Chart Period", ["1mo", "3mo", "6mo", "1y", "2y"])
    
    if ticker:
        try:
            # Get data
            df = fetcher.get_stock_data(ticker, period=period)
            current_price = fetcher.get_current_price(ticker)
            
            if df is not None and current_price:
                # Get signals
                signal_result = signals.analyze_stock(df, ticker)
                levels = signals.get_buy_sell_levels(df, current_price)
                
                # Display signal
                col_signal1, col_signal2, col_signal3 = st.columns(3)
                
                with col_signal1:
                    signal_type = signal_result["signal"]
                    signal_color = "🟢" if signal_type == "BUY" else "🔴" if signal_type == "SELL" else "🟡"
                    st.metric("Signal", f"{signal_color} {signal_type}")
                
                with col_signal2:
                    st.metric("Current Price", f"${current_price:.2f}")
                
                with col_signal3:
                    st.metric("Confidence", f"{signal_result['confidence']:.1f}%")
                
                st.markdown("---")
                
                # Price levels
                col_levels1, col_levels2, col_levels3, col_levels4 = st.columns(4)
                
                with col_levels1:
                    st.metric("Buy Level (Aggressive)", f"${levels['buy_level_aggressive']:.2f}")
                
                with col_levels2:
                    st.metric("Buy Level (Conservative)", f"${levels['buy_level_conservative']:.2f}")
                
                with col_levels3:
                    st.metric("Sell Level (Conservative)", f"${levels['sell_level_conservative']:.2f}")
                
                with col_levels4:
                    st.metric("Sell Level (Aggressive)", f"${levels['sell_level_aggressive']:.2f}")
                
                st.markdown("---")
                
                # Chart
                fig = go.Figure(data=[
                    go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='Price'
                    )
                ])
                
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], mode='lines', name='SMA 200'))
                
                fig.update_layout(height=500, template="plotly_dark", hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # Signal components
                st.subheader("📊 Signal Breakdown")
                components = signal_result["components"]
                
                comp_cols = st.columns(2)
                for i, (comp_name, comp_data) in enumerate(components.items()):
                    with comp_cols[i % 2]:
                        score = comp_data.get('score', 0)
                        st.write(f"**{comp_name}**")
                        st.progress((score + 100) / 200)  # Normalize to 0-1
                        st.caption(f"Score: {score:.1f}")
                
                st.markdown("---")
                
                # Trade execution
                st.subheader("🔄 Execute Trade")
                
                col_trade1, col_trade2, col_trade3 = st.columns(3)
                
                with col_trade1:
                    trade_action = st.selectbox("Action", ["BUY", "SELL"])
                
                with col_trade2:
                    trade_shares = st.number_input("Shares", min_value=0.001, step=0.001, value=1.0)
                
                with col_trade3:
                    trade_price = st.number_input("Price", min_value=0.01, step=0.01, value=current_price)
                
                if st.button("✅ Record Trade"):
                    add_trade(ticker, trade_action, trade_shares, trade_price, signal_result["signal"])
                    st.success(f"✅ {trade_action} order recorded: {trade_shares} shares @ ${trade_price:.2f}")
                    st.rerun()
                
                st.markdown("---")
                
                # Trade history
                st.subheader("📜 Trade History")
                trades = get_trades()
                if trades:
                    trades_df = pd.DataFrame(trades, columns=["ID", "Date", "Symbol", "Action", "Shares", "Price", "Total", "Signal"])
                    st.dataframe(trades_df[["Date", "Symbol", "Action", "Shares", "Price", "Total"]], use_container_width=True, hide_index=True)
                else:
                    st.info("📭 No trades yet")
                
                st.markdown("---")
                
                # Price alerts
                st.subheader("🔔 Price Alerts")
                col_alert1, col_alert2, col_alert3 = st.columns(3)
                
                with col_alert1:
                    alert_type = st.selectbox("Alert Type", ["Above", "Below"])
                
                with col_alert2:
                    alert_price = st.number_input("Price Level", min_value=0.01, step=0.01, value=current_price)
                
                with col_alert3:
                    if st.button("🔔 Set Alert"):
                        add_alert(ticker, alert_type, alert_price)
                        st.success(f"Alert set: {ticker} {alert_type} ${alert_price:.2f}")
            else:
                st.error("❌ Could not fetch data for ticker")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.info("Enter a ticker to get started")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    st.subheader("Portfolio Settings")
    st.write("Default allocation:")
    for asset, percent in config.DEFAULT_ALLOCATION.items():
        st.write(f"- {asset}: {percent*100}%")
    
    st.subheader("Recommended Strategy")
    st.write("""
    For long-term wealth building with $50/month:
    
    1. **Diversify**: 60% US (VOO/VTI), 25% International (VXUS), 15% Bonds (BND)
    2. **Be consistent**: Invest every month, no matter what
    3. **Ignore noise**: Don't panic sell on dips
    4. **Reinvest**: Let dividends compound
    5. **Rebalance**: Adjust allocation annually
    
    Example: $50/month at 7% annual return
    - 5 years: ~$3,500
    - 10 years: ~$8,000
    - 20 years: ~$24,000
    """)
    
    st.subheader("Trading Tips")
    st.write("""
    ⚠️ Trading is risky. Use caution:
    
    - Only trade with money you can afford to lose
    - Use stop-losses to limit downside
    - Don't chase losses
    - Keep emotions out of it
    - Log every trade (learn from winners/losers)
    """)

st.markdown("---")
st.caption("📱 Mobile-friendly Wealth & Trading Dashboard | Not financial advice | For educational purposes only")
