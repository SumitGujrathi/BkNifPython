import os
import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import json # Import json for potential debugging/manual parsing

app = Flask(__name__)
# Enable CORS for frontend communication
CORS(app) 

# --- NSE API Setup (Unofficial Endpoint) ---
BASE_URL = "https://www.nseindia.com/"
OPTION_CHAIN_URL = f"{BASE_URL}api/option-chain-indices?symbol=NIFTY"

# Important: Headers to mimic a browser request for NSE's unofficial API
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'accept-language': 'en,gu;q=0.9,hi;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
}

def fetch_nse_data(url):
    """Fetches data from NSE with required headers using a session."""
    try:
        session = requests.Session()
        # Hit the base URL first to establish a session and get cookies
        session.get(BASE_URL, headers=HEADERS, timeout=5) 
        
        # Now fetch the option chain data using the established session
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_pcr(chain_data, expiry_date):
    """Calculates the Put-Call Ratio (PCR) for the specified expiry."""
    total_call_oi = 0
    total_put_oi = 0
    
    # Filter the data for the specific expiry and sum up Open Interest (OI)
    for item in chain_data:
        if item.get('expiryDate') == expiry_date:
            # Check if 'CE' (Call) data exists and has Open Interest
            if item.get('CE') and item['CE'].get('openInterest') is not None:
                total_call_oi += item['CE']['openInterest']
                
            # Check if 'PE' (Put) data exists and has Open Interest
            if item.get('PE') and item['PE'].get('openInterest') is not None:
                total_put_oi += item['PE']['openInterest']

    # PCR = Total Put OI / Total Call OI
    if total_call_oi > 0:
        pcr = total_put_oi / total_call_oi
    else:
        pcr = 0.0 # Avoid division by zero
        
    return round(pcr, 4)

# --- API Endpoint for Option Chain ---

@app.route('/api/optionchain', methods=['GET'])
def get_option_chain():
    data = fetch_nse_data(OPTION_CHAIN_URL)
    
    if data and data.get('records'):
        records = data['records']
        expiry_dates = records.get('expiryDates')
        
        # Check if we have valid data and at least one expiry date
        if not expiry_dates or not records.get('data'):
            return jsonify({"error": "No valid option chain data found."}), 500

        # Use the nearest expiry date
        nearest_expiry = expiry_dates[0]
        
        # Calculate PCR and add it to the JSON response
        pcr_value = calculate_pcr(records['data'], nearest_expiry)
        
        # Prepare a structured response for the frontend
        response_data = {
            "pcr": pcr_value,
            "underlyingValue": records.get('underlyingValue'),
            "expiryDate": nearest_expiry,
            "chainData": records['data']
        }
        
        return jsonify(response_data)
    
    return jsonify({"error": "Could not fetch or parse NIFTY Option Chain data."}), 500

# --- Frontend Route ---

@app.route('/')
def index():
    # Renders the HTML file where the Option Chain will be displayed
    return render_template('index.html')

# --- Render/Production Deployment Configuration ---

if __name__ == '__main__':
    # Get the PORT from the environment (provided by Render/Gunicorn), default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    
    # Bind the app to host '0.0.0.0' (all public interfaces) and the specified port
    # Note: When deploying with Gunicorn, this block might be ignored, 
    # but it is essential for local development.
    app.run(host='0.0.0.0', port=port, debug=False)
