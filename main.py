from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

# Mimic a standard web browser to avoid getting blocked by NSE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br'
}

# Create a session to hold cookies
session = requests.Session()
session.headers.update(headers)

def fetch_nse_data():
    try:
        # Step 1: Hit the homepage to establish a session and get cookies
        session.get("https://www.nseindia.com", timeout=10)
        
        # Step 2: Fetch the Nifty Option Chain API
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed with status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    # This serves your website UI
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    # This provides the raw JSON data to your website
    data = fetch_nse_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
