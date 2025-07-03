#!/usr/bin/env python3
"""
Myntra Price Prediction System - Hybrid ARIMA + LSTM Model
Predicts future price trends and sends WhatsApp alerts for price drops
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Time Series & ML Libraries
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Deep Learning
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# WhatsApp Integration
import os
from dotenv import load_dotenv
from twilio.rest import Client

# Web Scraping for Real-time Data
import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from fake_useragent import UserAgent

from whatsapp import send_whatsapp_alert

class MyntraPricePredictor:
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.arima_model = None
        self.lstm_model = None
        self.hybrid_predictions = None
        self.product_data = None
        self.time_series_data = None
        
    def load_and_prepare_data(self, csv_file="data/myntra_products.csv"):
        """Load and prepare data for time series analysis"""
        try:
            print("📊 Loading Myntra product data...")
            df = pd.read_csv(csv_file)
            
            # Create synthetic time series data for demonstration
            # In real scenario, you'd have historical price data
            self.product_data = df
            print(f"✅ Loaded {len(df)} products")
            
            return df
        except FileNotFoundError:
            print(f"❌ CSV file '{csv_file}' not found!")
            return None
    
    def create_synthetic_time_series(self, product_id, days=365):
        """Create synthetic historical price data for a product"""
        print(f"🔨 Creating synthetic time series for product {product_id}...")
        
        # Get product info
        product = self.product_data[self.product_data['id'] == product_id].iloc[0]
        current_price = float(product['price'])
        mrp = float(product['mrp'])
        
        # Create date range
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
            freq='D'
        )
        
        # Generate realistic price variations
        np.random.seed(42)  # For reproducibility
        
        # Base trend (seasonal patterns)
        trend = np.sin(np.arange(len(dates)) * 2 * np.pi / 30) * 0.1  # Monthly cycles
        seasonal = np.sin(np.arange(len(dates)) * 2 * np.pi / 7) * 0.05  # Weekly cycles
        
        # Random walk component
        random_walk = np.cumsum(np.random.normal(0, 0.02, len(dates)))
        
        # Price variations around current price
        price_variations = current_price * (1 + trend + seasonal + random_walk * 0.1)
        
        # Add some realistic constraints
        price_variations = np.clip(price_variations, current_price * 0.7, mrp * 1.1)
        
        # Add some discount events (random price drops)
        discount_events = np.random.choice(len(dates), size=int(len(dates) * 0.1), replace=False)
        for event in discount_events:
            discount_factor = np.random.uniform(0.6, 0.9)
            price_variations[event:event+3] *= discount_factor
        
        # Create time series DataFrame
        ts_data = pd.DataFrame({
            'date': dates,
            'price': price_variations,
            'product_id': product_id,
            'product_name': product['product_name']
        })
        
        return ts_data
    
    def check_stationarity(self, ts_data):
        """Check if time series is stationary"""
        print("📈 Checking time series stationarity...")
        
        result = adfuller(ts_data['price'])
        
        print(f"ADF Statistic: {result[0]:.6f}")
        print(f"p-value: {result[1]:.6f}")
        
        if result[1] <= 0.05:
            print("✅ Time series is stationary")
            return True
        else:
            print("⚠️ Time series is not stationary - will apply differencing")
            return False
    
    def make_stationary(self, ts_data):
        """Make time series stationary through differencing"""
        ts_data = ts_data.copy()
        ts_data['price_diff'] = ts_data['price'].diff()
        ts_data = ts_data.dropna()
        
        # Check stationarity again
        result = adfuller(ts_data['price_diff'])
        if result[1] <= 0.05:
            print("✅ Time series is now stationary after differencing")
            return ts_data, True
        else:
            print("⚠️ May need second-order differencing")
            return ts_data, False
    
    def fit_arima_model(self, ts_data, order=(1,1,1)):
        """Fit ARIMA model to the data"""
        print(f"🔧 Fitting ARIMA{order} model...")
        
        try:
            self.arima_model = ARIMA(ts_data['price'], order=order)
            arima_fitted = self.arima_model.fit()
            
            print("✅ ARIMA model fitted successfully")
            print(arima_fitted.summary())
            
            return arima_fitted
        except Exception as e:
            print(f"❌ ARIMA model fitting failed: {str(e)}")
            return None
    
    def prepare_lstm_data(self, ts_data, lookback=30):
        """Prepare data for LSTM model"""
        print(f"🔧 Preparing LSTM data with lookback={lookback}...")
        
        # Scale the data
        prices = ts_data['price'].values.reshape(-1, 1)
        scaled_prices = self.scaler.fit_transform(prices)
        
        # Create sequences
        X, y = [], []
        for i in range(lookback, len(scaled_prices)):
            X.append(scaled_prices[i-lookback:i, 0])
            y.append(scaled_prices[i, 0])
        
        X, y = np.array(X), np.array(y)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def build_lstm_model(self, input_shape):
        """Build LSTM neural network"""
        print("🏗️ Building LSTM model...")
        
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        
        print("✅ LSTM model built successfully")
        return model
    
    def train_lstm_model(self, X_train, y_train, X_test, y_test, epochs=50):
        """Train LSTM model"""
        print(f"🚀 Training LSTM model for {epochs} epochs...")
        
        self.lstm_model = self.build_lstm_model((X_train.shape[1], 1))
        
        history = self.lstm_model.fit(
            X_train, y_train,
            batch_size=32,
            epochs=epochs,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        print("✅ LSTM model trained successfully")
        return history
    
    def create_hybrid_predictions(self, ts_data, forecast_days=30):
        """Create hybrid ARIMA + LSTM predictions"""
        print(f"🔮 Creating hybrid predictions for {forecast_days} days...")
        
        # ARIMA predictions
        arima_fitted = self.fit_arima_model(ts_data)
        if arima_fitted:
            arima_forecast = arima_fitted.forecast(steps=forecast_days)
            arima_conf_int = arima_fitted.get_forecast(steps=forecast_days).conf_int()
        else:
            arima_forecast = np.array([ts_data['price'].iloc[-1]] * forecast_days)
            arima_conf_int = None
        
        # Prepare LSTM data and train
        X_train, X_test, y_train, y_test = self.prepare_lstm_data(ts_data)
        
        if len(X_train) > 0:
            history = self.train_lstm_model(X_train, y_train, X_test, y_test, epochs=30)
            
            # LSTM predictions
            last_sequence = X_test[-1].reshape(1, X_test.shape[1], 1)
            lstm_predictions = []
            
            for _ in range(forecast_days):
                pred = self.lstm_model.predict(last_sequence, verbose=0)
                lstm_predictions.append(pred[0, 0])
                
                # Update sequence for next prediction
                last_sequence = np.roll(last_sequence, -1, axis=1)
                last_sequence[0, -1, 0] = pred[0, 0]
            
            # Inverse transform LSTM predictions
            lstm_predictions = np.array(lstm_predictions).reshape(-1, 1)
            lstm_forecast = self.scaler.inverse_transform(lstm_predictions).flatten()
        else:
            lstm_forecast = np.array([ts_data['price'].iloc[-1]] * forecast_days)
        
        # Combine ARIMA and LSTM predictions (weighted average)
        arima_weight = 0.4
        lstm_weight = 0.6
        
        hybrid_forecast = arima_weight * arima_forecast + lstm_weight * lstm_forecast
        
        # Create forecast dates
        last_date = pd.to_datetime(ts_data['date'].iloc[-1])
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=forecast_days,
            freq='D'
        )
        
        # Create predictions DataFrame
        predictions_df = pd.DataFrame({
            'date': forecast_dates,
            'arima_forecast': arima_forecast,
            'lstm_forecast': lstm_forecast,
            'hybrid_forecast': hybrid_forecast,
            'current_price': ts_data['price'].iloc[-1]
        })
        
        self.hybrid_predictions = predictions_df
        
        print("Predictions DataFrame:")
        print(predictions_df)
        print("Hybrid Forecast:")
        print(hybrid_forecast)
        
        return predictions_df
    
    def analyze_price_trends(self, predictions_df):
        """Analyze predicted price trends"""
        print("📊 Analyzing price trends...")
        
        current_price = predictions_df['current_price'].iloc[0]
        future_prices = predictions_df['hybrid_forecast']
        
        if len(future_prices) == 0:
            print("❌ No future price predictions available.")
            return None
        
        # Calculate trend metrics
        min_future_price = future_prices.min()
        max_future_price = future_prices.max()
        avg_future_price = future_prices.mean()
        
        # Price change analysis
        price_change = future_prices.iloc[-1] - current_price
        price_change_pct = (price_change / current_price) * 100
        
        # Find best buying opportunity (lowest predicted price)
        best_price_idx = future_prices.idxmin()
        best_price_date = predictions_df.loc[best_price_idx, 'date']
        best_price = future_prices.iloc[best_price_idx]
        savings_potential = current_price - best_price
        savings_pct = (savings_potential / current_price) * 100
        
        trends = {
            'current_price': current_price,
            'predicted_price_end': future_prices.iloc[-1],
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'min_future_price': min_future_price,
            'max_future_price': max_future_price,
            'avg_future_price': avg_future_price,
            'best_buy_date': best_price_date,
            'best_buy_price': best_price,
            'savings_potential': savings_potential,
            'savings_pct': savings_pct,
            'trend_direction': 'UP' if price_change > 0 else 'DOWN'
        }
        
        return trends
    
    def visualize_predictions(self, ts_data, predictions_df, product_name):
        """Visualize historical data and predictions"""
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Historical prices and predictions
        plt.subplot(2, 2, 1)
        plt.plot(pd.to_datetime(ts_data['date']), ts_data['price'], 
                label='Historical Prices', color='blue', linewidth=2)
        plt.plot(pd.to_datetime(predictions_df['date']), predictions_df['hybrid_forecast'], 
                label='Hybrid Forecast', color='red', linewidth=2, linestyle='--')
        plt.plot(pd.to_datetime(predictions_df['date']), predictions_df['arima_forecast'], 
                label='ARIMA Only', color='green', alpha=0.7)
        plt.plot(pd.to_datetime(predictions_df['date']), predictions_df['lstm_forecast'], 
                label='LSTM Only', color='orange', alpha=0.7)
        
        plt.title(f'Price Prediction: {product_name}')
        plt.xlabel('Date')
        plt.ylabel('Price (₹)')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Price trend analysis
        plt.subplot(2, 2, 2)
        trends = self.analyze_price_trends(predictions_df)
        
        trend_data = {
            'Current': trends['current_price'],
            'Predicted (30d)': trends['predicted_price_end'],
            'Min Future': trends['min_future_price'],
            'Max Future': trends['max_future_price']
        }
        
        bars = plt.bar(trend_data.keys(), trend_data.values(), 
                      color=['blue', 'red', 'green', 'orange'], alpha=0.7)
        plt.title('Price Trend Analysis')
        plt.ylabel('Price (₹)')
        plt.xticks(rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'₹{height:.0f}', ha='center', va='bottom')
        
        # Plot 3: Savings opportunity
        plt.subplot(2, 2, 3)
        savings_data = pd.DataFrame({
            'date': pd.to_datetime(predictions_df['date']),
            'savings': predictions_df['current_price'].iloc[0] - predictions_df['hybrid_forecast']
        })
        
        plt.plot(savings_data['date'], savings_data['savings'], 
                color='purple', linewidth=2)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.fill_between(savings_data['date'], savings_data['savings'], 0, 
                        where=(savings_data['savings'] > 0), 
                        color='green', alpha=0.3, label='Savings')
        plt.fill_between(savings_data['date'], savings_data['savings'], 0, 
                        where=(savings_data['savings'] < 0), 
                        color='red', alpha=0.3, label='Premium')
        
        plt.title('Potential Savings Over Time')
        plt.xlabel('Date')
        plt.ylabel('Savings (₹)')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Model comparison
        plt.subplot(2, 2, 4)
        model_comparison = {
            'ARIMA': np.mean(predictions_df['arima_forecast']),
            'LSTM': np.mean(predictions_df['lstm_forecast']),
            'Hybrid': np.mean(predictions_df['hybrid_forecast'])
        }
        
        colors = ['lightblue', 'lightcoral', 'lightgreen']
        wedges, texts, autotexts = plt.pie(model_comparison.values(), 
                                          labels=model_comparison.keys(),
                                          colors=colors, autopct='%1.1f%%')
        plt.title('Model Contribution to Predictions')
        
        plt.tight_layout()
        plt.savefig(f'price_prediction_{product_name.replace(" ", "_")}.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        return trends
    
    def send_price_alert(self, product_info, trends, predictions_df):
        """Send WhatsApp alert for price predictions"""
        product_name = product_info['product_name']
        current_price = trends['current_price']
        best_price = trends['best_buy_price']
        best_date = trends['best_buy_date'].strftime('%Y-%m-%d')
        savings_pct = trends['savings_pct']
        trend_direction = trends['trend_direction']
        
        # Determine alert type
        if savings_pct > 10:
            alert_type = "🚨 MAJOR PRICE DROP PREDICTED!"
        elif savings_pct > 5:
            alert_type = "⚠️ PRICE DROP EXPECTED"
        elif trend_direction == 'UP':
            alert_type = "📈 PRICE INCREASE PREDICTED"
        else:
            alert_type = "📊 PRICE ANALYSIS COMPLETE"
        
        message = f"""{alert_type}

🛍️ Product: {product_name}

💰 Current Price: ₹{current_price:,.0f}
🎯 Best Predicted Price: ₹{best_price:,.0f}
📅 Best Buy Date: {best_date}
💸 Potential Savings: ₹{trends['savings_potential']:,.0f} ({savings_pct:.1f}%)

📈 30-Day Trend: {trend_direction}
📊 Predicted Price Range: ₹{trends['min_future_price']:,.0f} - ₹{trends['max_future_price']:,.0f}

🤖 AI-Powered Prediction using Hybrid ARIMA+LSTM Model

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        return send_whatsapp_alert(product_name, current_price, best_price)

def main():
    """Main function for price prediction system"""
    print("🚀 MYNTRA PRICE PREDICTION SYSTEM")
    print("=" * 50)
    print("🤖 Hybrid ARIMA + LSTM Model for Price Forecasting")
    print()
    
    predictor = MyntraPricePredictor()
    
    # Load data
    df = predictor.load_and_prepare_data()
    if df is None:
        return
    
    print("\n📋 Available products (showing first 10):")
    print(df[['id', 'product_name', 'price', 'mrp', 'discount']].head(10).to_string(index=False))
    
    while True:
        print("\n" + "=" * 50)
        
        # Get product selection
        try:
            product_id = input("\n🔍 Enter product ID for price prediction (or 'quit'): ").strip()
            
            if product_id.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            product_id = int(product_id)
            
            # Check if product exists
            if product_id not in df['id'].values:
                print("❌ Product ID not found!")
                continue
            
            product_info = df[df['id'] == product_id].iloc[0]
            print(f"\n📱 Selected: {product_info['product_name']}")
            print(f"💰 Current Price: ₹{product_info['price']:,}")
            print(f"🏷️ MRP: ₹{product_info['mrp']:,}")
            
            # Create synthetic time series
            ts_data = predictor.create_synthetic_time_series(product_id)
            
            # Create predictions
            print("\n🔮 Generating price predictions...")
            predictions_df = predictor.create_hybrid_predictions(ts_data, forecast_days=30)
            
            # Analyze trends
            trends = predictor.analyze_price_trends(predictions_df)
            
            # Display results
            print("\n📊 PRICE PREDICTION RESULTS:")
            print("-" * 40)
            print(f"📈 Trend Direction: {trends['trend_direction']}")
            print(f"💰 Current Price: ₹{trends['current_price']:,.0f}")
            print(f"🔮 Predicted Price (30d): ₹{trends['predicted_price_end']:,.0f}")
            print(f"📉 Min Future Price: ₹{trends['min_future_price']:,.0f}")
            print(f"📈 Max Future Price: ₹{trends['max_future_price']:,.0f}")
            print(f"🎯 Best Buy Date: {trends['best_buy_date'].strftime('%Y-%m-%d')}")
            print(f"💸 Max Savings: ₹{trends['savings_potential']:,.0f} ({trends['savings_pct']:.1f}%)")
            
            # Visualize results
            visualize = input("\n📊 Show visualization? (y/n): ").lower().strip()
            if visualize in ['y', 'yes']:
                trends_full = predictor.visualize_predictions(ts_data, predictions_df, product_info['product_name'])
            
            # Send WhatsApp alert
            send_alert = input("\n📱 Send WhatsApp price alert? (y/n): ").lower().strip()
            if send_alert in ['y', 'yes']:
                predictor.send_price_alert(product_info, trends, predictions_df)
            
            # Continue or exit
            continue_pred = input("\n🔄 Predict another product? (y/n): ").lower().strip()
            if continue_pred not in ['y', 'yes']:
                print("👋 Thank you for using Myntra Price Predictor!")
                break
                
        except ValueError:
            print("❌ Please enter a valid product ID (number)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()