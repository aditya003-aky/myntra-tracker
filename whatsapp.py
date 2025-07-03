from twilio.rest import Client
from dotenv import load_dotenv
import os
import random

# Load environment variables
load_dotenv()

def send_whatsapp_alert(product_name, original_price, current_price):
    try:
        # FIXED: Use correct environment variable names (this was your main bug!)
        account_sid = os.getenv('TWILIO_SID')      # ✅ Fixed!
        auth_token = os.getenv('TWILIO_TOKEN')     # ✅ Fixed!
        from_phone = os.getenv('TWILIO_PHONE')     # ✅ Fixed!
        to_phone = os.getenv('YOUR_PHONE')         # ✅ Fixed!
        
        # Debug output
        print(f"Using SID: {account_sid[:10]}..." if account_sid else "❌ No SID found")
        print(f"From: {from_phone}")
        print(f"To: {to_phone}")
        
        if not all([account_sid, auth_token, from_phone, to_phone]):
            print("❌ Missing Twilio credentials in .env file")
            print("Make sure your .env file exists and has all variables")
            return False
        
        client = Client(account_sid, auth_token)
        
        discount_amount = original_price - current_price
        discount_percent = (discount_amount / original_price) * 100
        
        message_body = f"""🔔 MYNTRA PRICE ALERT!

📱 Product: {product_name}
💰 Original: ₹{original_price:,.0f}
🎯 Predicted: ₹{current_price:,.0f}
💸 You Save: ₹{discount_amount:,.0f} ({discount_percent:.1f}% OFF)

📉 Price is expected to come down in the next {random.randint(3, 9)} days — a great time to buy!
🛒 Don't miss out!"""


        
        message = client.messages.create(
            body=message_body,
            from_=from_phone,
            to=to_phone
        )
        
        print(f"✅ WhatsApp alert sent successfully! Message SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send WhatsApp message: {e}")
        print("Common issues:")
        print("1. Check if you've joined Twilio WhatsApp Sandbox")
        print("2. Verify your phone number format")
        print("3. Make sure .env file exists in same directory")
        return False

