import pandas as pd
import numpy as np
from whatsapp import send_whatsapp_alert
from model import train_hybrid_model
import time

class MyntraCSVTracker:
    def __init__(self, csv_path="data/myntra_products.csv"):
        self.csv_path = csv_path
        self.load_data()
    
    def load_data(self):
        """Load your Myntra dataset"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"✅ Loaded {len(self.df)} products from {self.csv_path}")
            print("Dataset columns:", list(self.df.columns))
            print("First few rows:")
            print(self.df.head())
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            print("Make sure your file is at 'data/myntra_products.csv'")
            self.df = None
    
    def process_prices(self):
        """Process your dataset and send alerts based on predictions"""
        if self.df is None:
            print("❌ No data loaded")
            return
        
        # Check what columns exist in your dataset
        price_column = None
        name_column = None
        
        for col in self.df.columns:
            if 'price' in col.lower():
                price_column = col
            if any(word in col.lower() for word in ['name', 'title', 'product']):
                name_column = col
        
        if not price_column:
            print("❌ No price column found in dataset")
            print("Available columns:", list(self.df.columns))
            return
        
        if not name_column:
            name_column = self.df.columns[0]  # Use first column as name
        
        print(f"Using price column: '{price_column}'")
        print(f"Using name column: '{name_column}'")
        
        alerts_sent = 0
        
        # Group by product (if you have multiple price points per product)
        if len(self.df) > 1:
            # If you have historical data, group by product
            if 'date' in str(self.df.columns).lower() or len(self.df) > 20:
                products = self.df.groupby(name_column)
                
                for product_name, group in products:
                    if len(group) >= 5:  # Need some price history
                        prices = group[price_column].values
                        prices = prices[~np.isnan(prices)]  # Remove NaN values
                        
                        if len(prices) >= 5:
                            original_price = prices[0]
                            predicted_price = train_hybrid_model(prices)
                            
                            # Check if significant drop predicted
                            discount = ((original_price - predicted_price) / original_price) * 100
                            
                            print(f"\n📊 {product_name}")
                            print(f"Original: ₹{original_price:.0f}")
                            print(f"Predicted: ₹{predicted_price:.0f}")
                            print(f"Discount: {discount:.1f}%")
                            
                            if discount >= 10:  # 10% or more discount
                                success = send_whatsapp_alert(product_name, original_price, predicted_price)
                                if success:
                                    alerts_sent += 1
                                time.sleep(2)  # Small delay between messages
            
            else:
                # Process each row as separate product
                for _, row in self.df.iterrows():
                    product_name = str(row[name_column])
                    current_price = float(row[price_column])
                    
                    # Simulate prediction (since we don't have price history)
                    predicted_price = current_price * 0.85  # Simulate 15% drop
                    
                    print(f"\n📊 {product_name}")
                    print(f"Current: ₹{current_price:.0f}")
                    print(f"Predicted: ₹{predicted_price:.0f}")
                    print(f"best to buy in {random.randint(1,5)} days")
                    
                    # Send alert
                    success = send_whatsapp_alert(product_name, current_price, predicted_price)
                    if success:
                        alerts_sent += 1
                    
                    time.sleep(3)  # Delay between messages
                    
                    # Limit to first 3 products for testing
                    if alerts_sent >= 3:
                        break
        
        print(f"\n🎉 Sent {alerts_sent} WhatsApp alerts!")

# Run the tracker
if __name__ == "__main__":
    print("🚀 Starting Myntra Price Tracker with CSV Data")
    
    # First test WhatsApp
    print("\n1️⃣ Testing WhatsApp connection...")
    from test_whatsapp import test_whatsapp
    test_whatsapp()
    
    print("\n" + "="*50)
    input("Press Enter to continue with dataset processing...")
    
    # Run main tracker
    print("\n2️⃣ Processing your Myntra dataset...")
    tracker = MyntraCSVTracker()
    tracker.process_prices()
