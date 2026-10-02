import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

class MLStockPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = [
            'RSI', 'MACD_Hist', 'Stoch_K', 'Stoch_D',
            'BB_Upper', 'BB_Lower', 'ATR', 'ROC',
            'Volume_Ratio', 'SMA_20', 'SMA_50', 'SMA_200',
            'EMA_12', 'EMA_26', 'ADX'
        ]
    
    def prepare_features(self, df):
        """Prepare features for ML model"""
        features = pd.DataFrame()
        
        features['RSI'] = df['RSI']
        features['MACD_Hist'] = df['MACD_Hist']
        features['Stoch_K'] = df['Stoch_K']
        features['Stoch_D'] = df['Stoch_D']
        features['BB_Upper'] = df['BB_Upper']
        features['BB_Lower'] = df['BB_Lower']
        features['ATR'] = df['ATR']
        features['ROC'] = df['ROC']
        features['Volume_Ratio'] = df['Volume_Ratio']
        features['SMA_20'] = df['SMA_20']
        features['SMA_50'] = df['SMA_50']
        features['SMA_200'] = df['SMA_200']
        features['EMA_12'] = df['EMA_12']
        features['EMA_26'] = df['EMA_26']
        features['ADX'] = df['ADX']
        
        return features.dropna()
    
    def create_labels(self, df, lookahead=5):
        """
        Create labels for ML training
        1 = Price goes up in next 'lookahead' days
        0 = Price goes down
        """
        labels = []
        for i in range(len(df) - lookahead):
            future_price = df['Close'].iloc[i + lookahead]
            current_price = df['Close'].iloc[i]
            
            if future_price > current_price:
                labels.append(1)  # BUY signal
            else:
                labels.append(0)  # SELL signal
        
        return np.array(labels)
    
    def train_model(self, df, ticker, lookahead=5):
        """Train ML model for ticker"""
        features = self.prepare_features(df)
        
        if len(features) < lookahead + 50:
            return False
        
        labels = self.create_labels(df.iloc[features.index], lookahead)
        
        # Trim features to match labels length
        features = features.iloc[:len(labels)]
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, labels, test_size=0.2, random_state=42
        )
        
        # Train ensemble models
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        rf_model.fit(X_train, y_train)
        gb_model.fit(X_train, y_train)
        
        # Store models and scaler
        self.models[ticker] = {
            'random_forest': rf_model,
            'gradient_boosting': gb_model,
            'feature_importance': rf_model.feature_importances_
        }
        self.scalers[ticker] = scaler
        
        # Calculate accuracy
        rf_score = rf_model.score(X_test, y_test)
        gb_score = gb_model.score(X_test, y_test)
        
        return {
            'ticker': ticker,
            'rf_accuracy': rf_score,
            'gb_accuracy': gb_score,
            'ensemble_accuracy': (rf_score + gb_score) / 2
        }
    
    def predict(self, df, ticker):
        """
        Make prediction for next move
        Returns: probability of up move, confidence
        """
        if ticker not in self.models:
            return None
        
        features = self.prepare_features(df)
        
        if features.empty:
            return None
        
        latest_features = features.iloc[-1].values.reshape(1, -1)
        
        # Scale using saved scaler
        scaler = self.scalers[ticker]
        latest_scaled = scaler.transform(latest_features)
        
        # Get predictions from both models
        rf_model = self.models[ticker]['random_forest']
        gb_model = self.models[ticker]['gradient_boosting']
        
        rf_pred = rf_model.predict_proba(latest_scaled)[0]
        gb_pred = gb_model.predict_proba(latest_scaled)[0]
        
        # Ensemble prediction (average)
        ensemble_pred = (rf_pred + gb_pred) / 2
        
        probability_up = ensemble_pred[1]
        confidence = max(ensemble_pred) * 100
        
        return {
            'probability_up': float(probability_up),
            'probability_down': float(ensemble_pred[0]),
            'confidence': float(confidence),
            'rf_probability_up': float(rf_pred[1]),
            'gb_probability_up': float(gb_pred[1])
        }
    
    def get_feature_importance(self, ticker):
        """Get feature importance for trained model"""
        if ticker not in self.models:
            return None
        
        importance = self.models[ticker]['feature_importance']
        
        feature_dict = {}
        for name, imp in zip(self.feature_names, importance):
            feature_dict[name] = float(imp)
        
        # Sort by importance
        sorted_features = sorted(feature_dict.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_features)
    
    def save_model(self, ticker, path="models/"):
        """Save trained model"""
        if ticker not in self.models:
            return False
        
        os.makedirs(path, exist_ok=True)
        
        try:
            with open(f"{path}{ticker}_model.pkl", 'wb') as f:
                pickle.dump({
                    'models': self.models[ticker],
                    'scaler': self.scalers[ticker]
                }, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, ticker, path="models/"):
        """Load trained model"""
        try:
            with open(f"{path}{ticker}_model.pkl", 'rb') as f:
                data = pickle.load(f)
                self.models[ticker] = data['models']
                self.scalers[ticker] = data['scaler']
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
