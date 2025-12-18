import requests
import logging
from flask import Flask, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Replace with your actual ScraperAPI key
SCRAPER_API_KEY = 'YOUR_SCRAPER_API_KEY_HERE' 

def fetch_nse_data():
    target_url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    
    # We send the request to ScraperAPI instead of directly to NSE
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
    
    try:
        logger.info("Fetching data via Proxy...")
        response = requests.get(proxy_url, timeout=30)
        
        logger.info(f"Proxy Response Status: {response.status_code}")

        if response.status_code == 200:
            json_data = response.json()
            # Filter top 10 strikes around the spot price
            all_data = json_data['filtered']['data']
            
            return {
                "time": json_data['records']['timestamp'],
                "price": json_data['records']['underlyingValue'],
                "data": all_data[:10],
                "status": "Success"
            }
        else:
            return {"status": "Error", "error": f"Proxy returned code: {response.status_code}. Check API key/balance."}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"status": "Error", "error": str(e)}

@app.route('/')
def index():
    result = fetch_nse_data()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
