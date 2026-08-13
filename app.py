from flask import Flask, jsonify, render_template
from dhanhq import DhanContext, dhanhq
import os

app = Flask(__name__)

# Replace with your actual Dhan Credentials
CLIENT_ID = "YOUR_DHAN_CLIENT_ID"
ACCESS_TOKEN = "YOUR_DHAN_ACCESS_TOKEN"

# Initialize Dhan API Client
context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(context)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        # Fetch live Nifty 50 Option Chain (under_security_id=13 is NIFTY 50)
        # Note: Set expiry to the current active expiry date in YYYY-MM-DD format
        response = dhan.option_chain(
            under_security_id=13,
            under_exchange_segment="IDX_I",
            expiry="2026-08-27"  # Update this to the upcoming weekly/monthly expiry
        )
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
