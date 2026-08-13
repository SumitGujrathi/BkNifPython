from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

def fetch_nse_data():
    session = requests.Session()
    
    # Modern browser headers required by NSE WAF
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nseindia.com/option-chain',
        'Authority': 'www.nseindia.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    }
    
    session.headers.update(headers)
    
    try:
        # Step 1: Pre-warm cookies on main domain
        init_res = session.get("https://www.nseindia.com", timeout=10)
        
        # Step 2: Fetch option chain
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404 or response.status_code == 403:
            return {
                "error": f"NSE blocked Render's IP address (HTTP {response.status_code}). See permanent broker API solution."
            }
        else:
            return {"error": f"HTTP Error {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    return jsonify(fetch_nse_data())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
