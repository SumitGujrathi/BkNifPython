import requests
from flask import Flask, render_template

app = Flask(__name__)

# Headers to mimic a real Chrome browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/'
}

def get_nifty_data():
    session = requests.Session()
    try:
        # Step 1: Visit the homepage to get Cookies (Crucial for NSE)
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        
        # Step 2: Now fetch the Option Chain API
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        response = session.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            payload = response.json()
            timestamp = payload['records']['timestamp']
            underlying_value = payload['records']['underlyingValue']
            # Filter top 10 rows (closest to ATM)
            raw_data = payload['filtered']['data'][:10]
            
            return {
                "time": timestamp,
                "price": underlying_value,
                "data": raw_data
            }
        else:
            return {"error": f"NSE returned status code: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

@app.route('/')
def index():
    data = get_nifty_data()
    return render_template('index.html', data=data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
