import numpy as np
import pandas as pd
from datetime import datetime


class AdvancedTradingSignals:
    def __init__(self):
        self.signal_weights = {
            "moving_average": 0.15,
            "macd": 0.15,
            "rsi": 0.15,
            "bollinger_bands": 0.10,
            "stochastic": 0.10,
            "volume": 0.15,
            "momentum": 0.10,
            "adx": 0.10,
        }

    def analyze_stock(self, df, ticker):
        if df is None or df.empty or len(df) < 200:
            return None

        components = {
            "moving_average": self._analyze_moving_averages(df),
            "macd": self._analyze_macd(df),
            "rsi": self._analyze_rsi(df),
            "bollinger_bands": self._analyze_bollinger_bands(df),
            "stochastic": self._analyze_stochastic(df),
            "volume": self._analyze_volume(df),
            "momentum": self._analyze_momentum(df),
            "adx": self._analyze_adx(df),
        }

        composite = self._calculate_composite_signal(components)
        latest = df.iloc[-1]

        return {
            "ticker": ticker,
            "signal": composite["signal"],
            "strength": composite["strength"],
            "confidence": composite["confidence"],
            "components": components,
            "current_price": float(latest["Close"]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _analyze_moving_averages(self, df):
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        score = 0

        if latest["SMA_20"] > latest["SMA_50"] > latest["SMA_200"]:
            score += 35
        if latest["SMA_20"] < latest["SMA_50"] < latest["SMA_200"]:
            score -= 35
        if latest["Close"] > latest["SMA_20"]:
            score += 12
        if latest["Close"] > latest["SMA_50"]:
            score += 12
        if latest["Close"] > latest["SMA_200"]:
            score += 15

        if prev["SMA_20"] <= prev["SMA_50"] and latest["SMA_20"] > latest["SMA_50"]:
            score += 20
        elif prev["SMA_20"] >= prev["SMA_50"] and latest["SMA_20"] < latest["SMA_50"]:
            score -= 20

        return {"score": np.clip(score, -100, 100)}

    def _analyze_macd(self, df):
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        score = 0

        if latest["MACD"] > latest["Signal"]:
            score += 30
        else:
            score -= 30

        if prev["MACD"] <= prev["Signal"] and latest["MACD"] > latest["Signal"]:
            score += 25
        elif prev["MACD"] >= prev["Signal"] and latest["MACD"] < latest["Signal"]:
            score -= 25

        if latest["MACD_Hist"] > 0:
            score += 10
        else:
            score -= 10

        return {"score": np.clip(score, -100, 100)}

    def _analyze_rsi(self, df):
        rsi = float(df.iloc[-1]["RSI"])
        if rsi < 30:
            return {"score": 45, "rsi_value": rsi, "signal": "OVERSOLD"}
        if rsi > 70:
            return {"score": -45, "rsi_value": rsi, "signal": "OVERBOUGHT"}
        if rsi < 50:
            return {"score": 15, "rsi_value": rsi, "signal": "BULLISH"}
        return {"score": -15, "rsi_value": rsi, "signal": "BEARISH"}

    def _analyze_bollinger_bands(self, df):
        latest = df.iloc[-1]
        if latest["Close"] <= latest["BB_Lower"]:
            return {"score": 30, "signal": "AT_LOWER_BAND"}
        if latest["Close"] >= latest["BB_Upper"]:
            return {"score": -30, "signal": "AT_UPPER_BAND"}
        if latest["Close"] > latest["BB_Middle"]:
            return {"score": 12, "signal": "ABOVE_MIDDLE"}
        return {"score": -12, "signal": "BELOW_MIDDLE"}

    def _analyze_stochastic(self, df):
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        k = latest["Stoch_K"]
        d = latest["Stoch_D"]

        if k < 20 and d < 20:
            return {"score": 40, "signal": "OVERSOLD"}
        if k > 80 and d > 80:
            return {"score": -40, "signal": "OVERBOUGHT"}
        if prev["Stoch_K"] <= prev["Stoch_D"] and k > d:
            return {"score": 25, "signal": "BULLISH_CROSSOVER"}
        if prev["Stoch_K"] >= prev["Stoch_D"] and k < d:
            return {"score": -25, "signal": "BEARISH_CROSSOVER"}
        return {"score": 0, "signal": "NEUTRAL"}

    def _analyze_volume(self, df):
        latest = df.iloc[-1]
        if pd.isna(latest["Volume_Ratio"]):
            return {"score": 0, "signal": "NO_DATA"}
        if latest["Volume_Ratio"] > 1.5:
            return {"score": 25, "signal": "STRONG_VOLUME"}
        if latest["Volume_Ratio"] < 0.5:
            return {"score": -20, "signal": "LOW_VOLUME"}
        return {"score": 5, "signal": "NORMAL_VOLUME"}

    def _analyze_momentum(self, df):
        roc = df.iloc[-1]["ROC"]
        if roc > 5:
            return {"score": 35, "roc": roc}
        if roc < -5:
            return {"score": -35, "roc": roc}
        if roc > 0:
            return {"score": 10, "roc": roc}
        return {"score": -10, "roc": roc}

    def _analyze_adx(self, df):
        adx = df.iloc[-1]["ADX"]
        if pd.isna(adx):
            return {"score": 0, "adx_value": 0, "trend_strength": "N/A"}
        if adx > 35:
            return {"score": 20, "adx_value": adx, "trend_strength": "STRONG"}
        if adx > 20:
            return {"score": 10, "adx_value": adx, "trend_strength": "MODERATE"}
        return {"score": 0, "adx_value": adx, "trend_strength": "WEAK"}

    def _calculate_composite_signal(self, components):
        total_score = 0
        total_weight = 0
        for indicator, weight in self.signal_weights.items():
            total_score += components.get(indicator, {}).get("score", 0) * weight
            total_weight += weight

        final_score = total_score / total_weight if total_weight > 0 else 0

        if final_score > 20:
            signal_type = "BUY"
        elif final_score < -20:
            signal_type = "SELL"
        else:
            signal_type = "HOLD"

        confidence = min(abs(final_score) * 2.5, 100)
        return {"signal": signal_type, "strength": float(final_score), "confidence": float(confidence)}

    def get_buy_sell_levels(self, df, current_price):
        latest = df.iloc[-1]
        atr = latest["ATR"]
        recent_high = df["High"].tail(20).max()
        recent_low = df["Low"].tail(20).min()
        pivot = (recent_high + recent_low) / 2

        return {
            "current_price": float(current_price),
            "pivot_point": float(pivot),
            "buy_level_aggressive": float(pivot - (2 * atr)),
            "buy_level_conservative": float(pivot - atr),
            "sell_level_conservative": float(pivot + atr),
            "sell_level_aggressive": float(pivot + (2 * atr)),
            "resistance": float(recent_high),
            "support": float(recent_low),
            "atr": float(atr),
        }
