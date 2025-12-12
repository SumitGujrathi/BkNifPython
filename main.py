import os
import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS 

app = Flask(__name__)
# Enable CORS for frontend communication
CORS(app) 

# --- NSE API Setup (Unofficial Endpoint) ---
BASE_URL = "https://www.nseindia.com/"
OPTION_CHAIN_URL = f"{BASE_URL}api/option-chain-indices?symbol=NIFTY"

# Important: Headers to mimic a browser request.
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'accept-language': 'en,gu;q=0.9,hi;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
}

# Global storage for critical cookies, managed manually to persist across requests
NSE_COOKIES = {} 

def fetch_nse_data(url):
    """Fetches data from NSE with required headers and manages cookies."""
    global NSE_COOKIES
    
    # --- Step 1: Initialize/Refresh Session Cookies ---
    # We must hit the base URL first to get the essential 'bm_sv' cookie.
    if not NSE_COOKIES:
        try:
            session = requests.Session()
            # Send the initial request to the base URL
            cookie_response = session.get(BASE_URL, headers=HEADERS, timeout=10)
            cookie_response.raise_for_status() 
            
            # Store cookies from the response
            NSE_COOKIES.update(session.cookies.get_dict())
            print(f"Successfully retrieved {len(NSE_COOKIES)} initial NSE cookies.")

        except requests.exceptions.RequestException as e:
            print(f"Error during initial cookie fetch: {e}")
            return None

    # --- Step 2: Fetch Option Chain Data ---
    try:
        # Use the stored cookies for the main API call
        response = requests.get(url, headers=HEADERS, cookies=NSE_COOKIES, timeout=15)
        response.raise_for_status()
        
        # Update cookies just in case the API call refreshed them
        NSE_COOKIES.update(response.cookies.get_dict())
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching data (Status: {e.response.status_code}): {e}")
        # If the request fails due to a security block (e.g., 403 Forbidden), 
        # clear cookies to force re-fetch on the next attempt.
        if e.response.status_code in [401, 403, 503]:
             print("Security block detected. Clearing cookies for next attempt.")
             NSE_COOKIES = {}
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"General Error fetching data: {e}")
        return None

def calculate_pcr(chain_data, expiry_date):
    """Calculates the Put-Call Ratio (PCR) for the specified expiry."""
    total_call_oi = 0
    total_put_oi = 0
    
    # Filter the data for the specific expiry and sum up Open Interest (OI)
    for item in chain_data:
        if item.get('expiryDate') == expiry_date:
            # Sum Call OI
            if item.get('CE') and item['CE'].get('openInterest') is not None:
                total_call_oi += item['CE']['openInterest']
                
            # Sum Put OI
            if item.get('PE') and item['PE'].get('openInterest') is not None:
                total_put_oi += item['PE']['openInterest']

    # PCR = Total Put OI / Total Call OI
    if total_call_oi > 0:
        pcr = total_put_oi / total_call_oi
    else:
        pcr = 0.0 
        
    return round(pcr, 4)

# --- API Endpoint for Option Chain ---

@app.route('/api/optionchain', methods=['GET'])
def get_option_chain():
    data = fetch_nse_data(OPTION_CHAIN_URL)
    
    if data and data.get('records'):
        records = data['records']
        expiry_dates = records.get('expiryDates')
        
        if not expiry_dates or not records.get('data'):
            print("Received data structure is invalid or empty.")
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
    
    # This is the error seen on Render if the fetch fails
    return jsonify({"error": "Could not fetch or parse NIFTY Option Chain data."}), 500

# --- Frontend Route ---

@app.route('/')
def index():
    # Renders the HTML file (must be in the 'templates' folder)
    return render_template('index.html')

# --- Render/Production Deployment Configuration ---

if __name__ == '__main__':
    # Get the PORT from the environment (provided by Render/Gunicorn), default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    
    # Bind the app to host '0.0.0.0' (all public interfaces) and the specified port
    app.run(host='0.0.0.0', port=port, debug=False)
