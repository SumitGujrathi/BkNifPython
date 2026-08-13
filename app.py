from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

def fetch_nse_data():
    session = requests.Session()
    
    # Exact headers required by NSE to prevent 404 Cloud Firewall blocks
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.nseindia.com/option-chain'
    }
    
    session.headers.update(headers)
    
    try:
        # Step 1: Hit main option-chain page to establish valid session cookies
        session.get("https://www.nseindia.com/option-chain", timeout=10)
        
        # Step 2: Request the actual JSON API
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
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    data = fetch_nse_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
