from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

# Create a free account on scraperapi.com to get your key
SCRAPER_API_KEY = "YOUR_SCRAPER_API_KEY" 

def fetch_nse_data():
    target_url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    
    # ScraperAPI routes your request through a residential proxy, bypassing Render's IP block
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=false"
    
    try:
        response = requests.get(proxy_url, timeout=20)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Proxy returned status code {response.status_code}"}
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
