# 📱 Wealth & Trading Dashboard

A mobile-friendly app to build wealth long-term and make informed trading decisions.

## Two Screens

### 💰 Wealth Dashboard
- Track portfolio value
- Log monthly contributions
- View holdings and gains
- Set wealth goals
- Project future wealth

### 📈 Trading Hub
- Real-time stock signals (BUY/SELL/HOLD)
- Technical analysis with buy/sell price levels
- Trade execution and history
- Price alerts
- Signal component breakdown

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run

```bash
streamlit run main_app.py
```

Then open: `http://localhost:8501`

## Mobile

Streamlit is mobile-responsive. Access from your phone by:
1. Running the app on your computer
2. Finding your computer's IP address
3. Accessing `http://<YOUR_IP>:8501` from your phone

Or deploy to Streamlit Cloud for free hosting.

## Strategy

**Long-term wealth**: Invest $50/month in diversified ETFs, let it compound

**Trading**: Use signals to time entries/exits, but keep size small until you prove it works

## Disclaimer

Educational tool only. Not financial advice. Past performance ≠ future results. You can lose money.
