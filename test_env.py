from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()  # or load_dotenv(r'C:\Users\adity\myntra-tracker\.env')

# Test the values
print("TWILIO_SID:", os.getenv('TWILIO_SID'))
print("TWILIO_PHONE:", os.getenv('TWILIO_PHONE'))