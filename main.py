import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS # Required for cross-origin requests

app = Flask(__name__)
# Enable CORS to allow your frontend (running on a different port/origin) to access the API
CORS(app) 

# --- NSE API Setup (Unofficial Endpoint) ---
BASE_URL = "https://www.nseindia.com/"
OPTION_CHAIN_URL = f"{BASE_URL}api/option-chain-indices?symbol=NIFTY"

# Important: NSE blocks requests without proper headers, so we mimic a browser.
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'accept-language': 'en,gu;q=0.9,hi;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
}

def fetch_nse_data(url):
    """Fetches data from NSE with required headers."""
    try:
        # We need to hit the base URL first to get the necessary cookies for the session
        session = requests.Session()
        session.get(BASE_URL, headers=HEADERS, timeout=5) 
        
        # Now fetch the option chain data using the session
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# --- API Endpoint for Option Chain ---

@app.route('/api/optionchain', methods=['GET'])
def get_option_chain():
    data = fetch_nse_data(OPTION_CHAIN_URL)
    
    if data:
        # Optional: You can filter and clean the JSON data here 
        # (e.g., calculate PCR, filter for nearest expiry, etc.)
        # For simplicity, we return the raw data structure from NSE.
        # The frontend will handle the presentation.
        return jsonify(data)
    
    return jsonify({"error": "Could not fetch NIFTY Option Chain data."}), 500

# --- Frontend Route ---

@app.route('/')
def index():
    # Renders the HTML file where the Option Chain will be displayed
    return render_template('index.html')

if __name__ == '__main__':
    # You will run this and access the page via http://127.0.0.1:5000/
    app.run(debug=True)
