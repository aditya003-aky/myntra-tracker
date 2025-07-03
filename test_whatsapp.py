from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

def comprehensive_debug():
    print("🔍 COMPREHENSIVE TWILIO DEBUG")
    print("=" * 50)
    
    # Step 1: Check credentials
    sid = os.getenv('TWILIO_SID')
    token = os.getenv('TWILIO_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE')
    to_phone = os.getenv('YOUR_PHONE')
    
    print("1️⃣ CREDENTIALS CHECK:")
    print(f"   SID: {sid[:15]}...{sid[-4:] if sid else 'None'}")
    print(f"   Token: {'✅ Present' if token else '❌ Missing'}")
    print(f"   From: {from_phone}")
    print(f"   To: {to_phone}")
    
    if not all([sid, token, from_phone, to_phone]):
        print("❌ Missing credentials in .env file!")
        return False
    
    try:
        # Step 2: Test basic authentication
        print("\n2️⃣ AUTHENTICATION TEST:")
        client = Client(sid, token)
        
        account = client.api.accounts(sid).fetch()
        print(f"   ✅ Account: {account.friendly_name}")
        print(f"   ✅ Status: {account.status}")
        print(f"   ✅ Type: {account.type}")
        
        # Step 3: Check account balance (for trial accounts)
        try:
            balance = client.balance.fetch()
            print(f"   💰 Balance: {balance.balance} {balance.currency}")
        except:
            print("   💰 Balance: Trial account")
        
        # Step 4: List phone numbers
        print("\n3️⃣ PHONE NUMBERS:")
        try:
            phone_numbers = client.incoming_phone_numbers.list(limit=5)
            if phone_numbers:
                for number in phone_numbers:
                    print(f"   📱 {number.phone_number} ({number.friendly_name})")
            else:
                print("   📱 No phone numbers (using trial)")
        except Exception as e:
            print(f"   📱 Error fetching numbers: {e}")
        
        # Step 5: Test WhatsApp sandbox
        print("\n4️⃣ WHATSAPP SANDBOX TEST:")
        
        # First, try to get WhatsApp sandbox info
        try:
            # This will fail if sandbox isn't set up
            message = client.messages.create(
                body="🧪 DEBUG: Testing WhatsApp connection from Myntra Tracker",
                from_=from_phone,
                to=to_phone
            )
            print(f"   ✅ Message sent! SID: {message.sid}")
            print(f"   ✅ Status: {message.status}")
            print(f"   ✅ Direction: {message.direction}")
            return True
            
        except Exception as whatsapp_error:
            print(f"   ❌ WhatsApp Error: {whatsapp_error}")
            
            # Check if it's a sandbox issue
            if "21608" in str(whatsapp_error):
                print("\n   🎯 SOLUTION: WhatsApp Sandbox not joined!")
                print("   📱 Send this message to +1 415 523 8886:")
                print("   💬 'join <sandbox-code>'")
                print("   🔍 Find your sandbox code at: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
                
            elif "21614" in str(whatsapp_error):
                print("\n   🎯 SOLUTION: Phone number not verified!")
                print("   📱 Add +918814804298 to verified numbers")
                print("   🔍 Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
                
            return False
        
    except Exception as e:
        print(f"\n❌ AUTHENTICATION FAILED: {e}")
        
        if "20003" in str(e):
            print("\n🎯 POSSIBLE SOLUTIONS:")
            print("1. Double-check SID and Token from console")
            print("2. Regenerate Auth Token if needed")
            print("3. Check if account is suspended")
        
        return False

def quick_whatsapp_fix():
    """Try alternative WhatsApp setup"""
    print("\n" + "="*50)
    print("🚀 QUICK WHATSAPP FIX ATTEMPT")
    print("="*50)
    
    sid = os.getenv('TWILIO_SID')
    token = os.getenv('TWILIO_TOKEN')
    
    try:
        client = Client(sid, token)
        
        # Try different phone number formats
        phone_formats = [
            "whatsapp:+918814804298",  # Current format
            "+918814804298",           # Without whatsapp prefix
            "918814804298"             # Without + symbol
        ]
        
        for i, phone in enumerate(phone_formats, 1):
            print(f"\n🧪 Test {i}: Trying phone format: {phone}")
            try:
                message = client.messages.create(
                    body=f"Test {i}: WhatsApp format test",
                    from_="whatsapp:+14155238886",
                    to=phone
                )
                print(f"   ✅ SUCCESS with format: {phone}")
                print(f"   📨 Message SID: {message.sid}")
                return True
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:100]}...")
                continue
        
        print("\n❌ All phone formats failed")
        return False
        
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TWILIO WHATSAPP DEBUGGER")
    print("This will help identify exactly what's wrong\n")
    
    # Run comprehensive debug
    success = comprehensive_debug()
    
    if not success:
        print("\n" + "="*50)
        input("Press Enter to try alternative solutions...")
        quick_whatsapp_fix()
    
    print("\n📋 NEXT STEPS:")
    print("1. Join WhatsApp Sandbox if not already done")
    print("2. Verify your phone number in Twilio Console")
    print("3. Check Twilio Debugger for detailed logs")
    print("4. URL: https://console.twilio.com/us1/monitor/debugger")
#**********************************************************************************
def test_whatsapp():
    """Simple test function for WhatsApp connectivity"""
    import os
    from dotenv import load_dotenv
    from twilio.rest import Client
    
    load_dotenv()
    
    # Using your actual environment variable names
    account_sid = os.getenv('TWILIO_SID')
    auth_token = os.getenv('TWILIO_TOKEN')
    from_number = os.getenv('TWILIO_PHONE')  # whatsapp:+14155238886
    to_number = os.getenv('YOUR_PHONE')      # whatsapp:+918814804298
    
    try:
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body="🧪 WhatsApp test from Myntra Tracker - Connection successful!",
            from_=from_number,
            to=to_number
        )
        
        print(f"✅ WhatsApp test message sent! SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp test failed: {str(e)}")
        return False