import os
import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS 

app = Flask(__name__)
CORS(app) 

# --- Dhan API Setup ---
# *** CRITICAL: Set these as environment variables in Render's dashboard ***
DHAN_API_URL = "https://api.dhan.co/v2/optionchain"
DHAN_ACCESS_TOKEN = os.environ.get('DHAN_ACCESS_TOKEN')
DHAN_CLIENT_ID = os.environ.get('DHAN_CLIENT_ID')

# NIFTY 50 Scrip ID for Dhan (This ID is specific to their platform)
NIFTY_SCRIP_ID = 13 # This is an example, you must verify the NIFTY ID in Dhan's docs

def fetch_dhan_option_chain():
    """Fetches Option Chain data using the DhanHQ API."""
    
    if not DHAN_ACCESS_TOKEN or not DHAN_CLIENT_ID:
        print("Error: Dhan API credentials not found in environment variables.")
        return None

    # Step 1: Get the list of expiries first
    # This ensures you always query for a valid, current expiry.
    # (Simplified for this example; often brokers require a separate call)
    
    # Step 2: Request the Option Chain for the nearest expiry
    headers = {
        'access-token': f'Bearer {DHAN_ACCESS_TOKEN}', # Check Dhan's exact format
        'client-id': DHAN_CLIENT_ID,
        'Content-Type': 'application/json'
    }
    
    payload = {
        # Assuming we want the nearest expiry. You'd need a separate call to get the exact date.
        "UnderlyingScrip": NIFTY_SCRIP_ID, 
        "UnderlyingSeg": "IDX_I" # Index segment
        # "Expiry": "2025-12-18" # You'd dynamically get this
    }
    
    try:
        response = requests.post(DHAN_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Dhan data: {e}")
        return None


# --- Option Chain Route (Needs significant modification for Dhan's JSON structure) ---

@app.route('/api/optionchain', methods=['GET'])
def get_option_chain():
    # 1. Fetch data from the new, reliable API
    data = fetch_dhan_option_chain()
    
    # 2. Process Dhan's data structure and calculate PCR
    # Note: This is the biggest change. Dhan's JSON structure is different from NSE's.
    if data and data.get('data') and data['data'].get('oc'):
        dhan_oc_data = data['data']['oc']
        
        # You would write a function here to convert Dhan's structure
        # (which is an array of strikes, each with CE/PE details)
        # into the format your frontend expects, and calculate PCR.
        
        # Example PCR calculation (simplified):
        total_call_oi = sum(item.get('ce', {}).get('oi', 0) for strike, item in dhan_oc_data.items())
        total_put_oi = sum(item.get('pe', {}).get('oi', 0) for strike, item in dhan_oc_data.items())
        pcr_value = round(total_put_oi / total_call_oi, 4) if total_call_oi > 0 else 0.0

        # ... (rest of the JSON structure conversion and return) ...
        
        # For now, just return the raw Dhan data to see if the connection is successful:
        return jsonify(data) 
    
    return jsonify({"error": "Failed to fetch or process data from the Dhan API."}), 500

# ... (rest of your Flask routes and __main__ block) ...
