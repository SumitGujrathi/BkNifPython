import cloudscraper
import time
import random
import logging
from flask import Flask, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_nse_option_chain():
    # Use cloudscraper to bypass NSE's bot protection
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    
    try:
        # Step 1: Visit home page to set cookies
        scraper.get("https://www.nseindia.com", timeout=10)
        time.sleep(random.uniform(1, 2))
        
        # Step 2: Fetch actual data
        response = scraper.get(url, timeout=15)
        
        if response.status_code == 200:
            raw_data = response.json()
            
            # Extract basic info
            spot_price = raw_data['records']['underlyingValue']
            timestamp = raw_data['records']['timestamp']
            
            # Logic: Filter for the nearest 10 strikes around the Spot Price
            all_data = raw_data['filtered']['data']
            # Sort by proximity to spot price
            closest = sorted(all_data, key=lambda x: abs(x['strikePrice'] - spot_price))[:12]
            # Re-sort numerically for the table
            final_list = sorted(closest, key=lambda x: x['strikePrice'])
            
            return {
                "status": "Success",
                "price": spot_price,
                "time": timestamp,
                "data": final_list
            }
        else:
            return {"status": "Error", "error": f"NSE Error: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Fetch failed: {str(e)}")
        return {"status": "Error", "error": "Connection Failed"}

@app.route('/')
def index():
    result = fetch_nse_option_chain()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
