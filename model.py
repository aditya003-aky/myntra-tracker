import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

def prepare_lstm_data(data, lookback=10):
    """Prepare price data for LSTM"""
    if len(data) < lookback + 5:
        return None, None, None
        
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data.reshape(-1, 1))
    
    X, y = [], []
    for i in range(lookback, len(scaled_data)):
        X.append(scaled_data[i-lookback:i, 0])
        y.append(scaled_data[i, 0])
    
    return np.array(X), np.array(y), scaler

def train_hybrid_model(prices):
    """Train hybrid ARIMA + LSTM model on price data"""
    try:
        if len(prices) < 10:
            # Not enough data, return simple prediction
            return np.mean(prices[-3:]) * 0.95  # Predict 5% drop
        
        # ARIMA component
        try:
            arima_model = ARIMA(prices, order=(2,1,1)).fit()
            arima_pred = arima_model.forecast(steps=1)[0]
        except:
            arima_pred = prices[-1] * 0.95
        
        # LSTM component
        lstm_pred = arima_pred  # Default fallback
        
        if len(prices) >= 20:
            X, y, scaler = prepare_lstm_data(prices)
            
            if X is not None and len(X) > 5:
                model = Sequential([
                    LSTM(32, return_sequences=True, input_shape=(X.shape[1], 1)),
                    LSTM(16),
                    Dense(8),
                    Dense(1)
                ])
                model.compile(optimizer='adam', loss='mse')
                
                X = X.reshape((X.shape[0], X.shape[1], 1))
                model.fit(X, y, epochs=30, batch_size=16, verbose=0)
                
                # Predict
                last_sequence = X[-1:] if len(X) > 0 else X[:1]
                lstm_pred_scaled = model.predict(last_sequence, verbose=0)
                lstm_pred = scaler.inverse_transform(lstm_pred_scaled)[0][0]
        
        # Hybrid prediction (combine both models)
        hybrid_pred = 0.7 * arima_pred + 0.3 * lstm_pred
        
        # Ensure prediction makes sense (not too extreme)
        price_mean = np.mean(prices[-5:])
        if abs(hybrid_pred - price_mean) > price_mean * 0.3:
            hybrid_pred = price_mean * 0.9  # Conservative 10% drop prediction
        
        return max(hybrid_pred, prices[-1] * 0.5)  # Don't predict less than 50% of current price
        
    except Exception as e:
        print(f"Model error: {e}")
        return prices[-1] * 0.9  # Predict 10% drop as fallback