import cloudscraper
import time
import random
import logging
from flask import Flask, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_nse_option_chain():
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    
    try:
        # Step 1: Establish session
        scraper.get("https://www.nseindia.com", timeout=10)
        time.sleep(random.uniform(1, 2))
        
        # Step 2: Fetch data
        response = scraper.get(url, timeout=15)
        
        if response.status_code == 200:
            raw_data = response.json()
            
            # --- SAFETY CHECK: Verify if 'records' exists ---
            if 'records' not in raw_data:
                logger.error("NSE sent a success code but NO DATA (empty records).")
                return {"status": "Error", "error": "NSE is sending empty data. The API might be down or throttling Render."}
            
            spot_price = raw_data['records']['underlyingValue']
            timestamp = raw_data['records']['timestamp']
            all_data = raw_data['filtered']['data']
            
            # Filter closest 12 strikes
            closest = sorted(all_data, key=lambda x: abs(x['strikePrice'] - spot_price))[:12]
            final_list = sorted(closest, key=lambda x: x['strikePrice'])
            
            return {
                "status": "Success",
                "price": spot_price,
                "time": timestamp,
                "data": final_list
            }
        else:
            return {"status": "Error", "error": f"NSE Blocked Request (Status {response.status_code})"}
            
    except Exception as e:
        logger.error(f"Critical Failure: {str(e)}")
        return {"status": "Error", "error": "Connection error or invalid data format."}

@app.route('/')
def index():
    result = fetch_nse_option_chain()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
