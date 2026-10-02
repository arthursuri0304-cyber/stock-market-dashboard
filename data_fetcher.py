import pandas as pd
import numpy as np
import yfinance as yf


class StockDataFetcher:
    def __init__(self):
        self.cache = {}

    def get_stock_data(self, ticker, period="1y", interval="1d"):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            if df.empty:
                return None
            df = self._add_technical_indicators(df)
            return df
        except Exception as exc:
            print(f"Error fetching {ticker}: {exc}")
            return None

    def get_current_price(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
            return None
        except Exception as exc:
            print(f"Error fetching current price for {ticker}: {exc}")
            return None

    def _add_technical_indicators(self, df):
        df = df.copy()

        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()

        df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = df["EMA_12"] - df["EMA_26"]
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["Signal"]

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs.fillna(0)))

        middle = df["Close"].rolling(window=20).mean()
        std = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = middle + (std * 2)
        df["BB_Middle"] = middle
        df["BB_Lower"] = middle - (std * 2)

        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        low_min = df["Low"].rolling(window=14).min()
        high_max = df["High"].rolling(window=14).max()
        df["Stoch_K"] = 100 * ((df["Close"] - low_min) / (high_max - low_min).replace(0, np.nan))
        df["Stoch_D"] = df["Stoch_K"].rolling(window=3).mean()

        df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()
        df["Volume_Ratio"] = df["Volume"] / df["Volume_SMA"].replace(0, np.nan)
        df["ROC"] = ((df["Close"] - df["Close"].shift(12)) / df["Close"].shift(12)) * 100

        plus_dm = df["High"].diff()
        minus_dm = df["Low"].diff() * -1
        plus_dm = plus_dm.where(plus_dm > 0, 0)
        minus_dm = minus_dm.where(minus_dm > 0, 0)
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        pos_di = 100 * (plus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
        neg_di = 100 * (minus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
        dx = 100 * (abs(pos_di - neg_di) / (pos_di + neg_di).replace(0, np.nan))
        df["ADX"] = dx.rolling(window=14).mean()

        return df


def get_stock_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "average_volume": info.get("averageVolume", "N/A"),
            "beta": info.get("beta", "N/A"),
        }
    except Exception:
        return None
