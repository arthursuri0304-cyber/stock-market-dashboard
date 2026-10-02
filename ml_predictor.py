import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle


class MLStockPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = [
            "RSI",
            "MACD_Hist",
            "Stoch_K",
            "Stoch_D",
            "BB_Upper",
            "BB_Lower",
            "ATR",
            "ROC",
            "Volume_Ratio",
            "SMA_20",
            "SMA_50",
            "SMA_200",
            "EMA_12",
            "EMA_26",
            "ADX",
        ]

    def prepare_features(self, df):
        features = pd.DataFrame()
        for name in self.feature_names:
            if name in df.columns:
                features[name] = df[name]
        return features.dropna()

    def create_labels(self, df, lookahead=5):
        labels = []
        for i in range(len(df) - lookahead):
            current = df["Close"].iloc[i]
            future = df["Close"].iloc[i + lookahead]
            labels.append(1 if future > current else 0)
        return np.array(labels)

    def train_model(self, df, ticker, lookahead=5):
        features = self.prepare_features(df)
        if len(features) < lookahead + 50:
            return False

        labels = self.create_labels(df.iloc[features.index], lookahead)
        features = features.iloc[: len(labels)]

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, labels, test_size=0.2, random_state=42
        )

        rf_model = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42, n_jobs=-1)
        gb_model = GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, random_state=42)

        rf_model.fit(X_train, y_train)
        gb_model.fit(X_train, y_train)

        self.models[ticker] = {
            "random_forest": rf_model,
            "gradient_boosting": gb_model,
            "feature_importance": rf_model.feature_importances_,
        }
        self.scalers[ticker] = scaler

        rf_score = rf_model.score(X_test, y_test)
        gb_score = gb_model.score(X_test, y_test)

        return {
            "ticker": ticker,
            "rf_accuracy": rf_score,
            "gb_accuracy": gb_score,
            "ensemble_accuracy": (rf_score + gb_score) / 2,
        }

    def predict(self, df, ticker):
        if ticker not in self.models:
            return None

        features = self.prepare_features(df)
        if features.empty:
            return None

        latest = features.iloc[-1].values.reshape(1, -1)
        scaled = self.scalers[ticker].transform(latest)

        rf_model = self.models[ticker]["random_forest"]
        gb_model = self.models[ticker]["gradient_boosting"]

        rf_prob = rf_model.predict_proba(scaled)[0]
        gb_prob = gb_model.predict_proba(scaled)[0]
        ensemble = (rf_prob + gb_prob) / 2.0

        probability_up = float(ensemble[1])
        confidence = float(max(ensemble) * 100)

        return {
            "probability_up": probability_up,
            "probability_down": float(ensemble[0]),
            "confidence": confidence,
            "rf_probability_up": float(rf_prob[1]),
            "gb_probability_up": float(gb_prob[1]),
        }

    def save_model(self, ticker, path="models/"):
        if ticker not in self.models:
            return False
        os.makedirs(path, exist_ok=True)
        with open(f"{path}{ticker}_model.pkl", "wb") as file:
            pickle.dump({"models": self.models[ticker], "scaler": self.scalers[ticker]}, file)
        return True

    def load_model(self, ticker, path="models/"):
        try:
            with open(f"{path}{ticker}_model.pkl", "rb") as file:
                blob = pickle.load(file)
                self.models[ticker] = blob["models"]
                self.scalers[ticker] = blob["scaler"]
            return True
        except Exception:
            return False
