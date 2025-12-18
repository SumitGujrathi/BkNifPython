import cloudscraper
import time
import random
import logging
from flask import Flask, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_with_retry(url, max_retries=3):
    # Create a scraper that mimics a Desktop Chrome browser
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}: Connecting to NSE...")
            
            # Step A: Visit homepage to clear the 'handshake'
            scraper.get("https://www.nseindia.com", timeout=10)
            
            # Small random pause (mimicking human behavior)
            time.sleep(random.uniform(1, 3)) 
            
            # Step B: Get the Option Chain data
            response = scraper.get(url, timeout=15)
            
            if response.status_code == 200:
                logger.info("Success! Data received.")
                return response.json()
            
            logger.warning(f"Attempt {attempt + 1} failed with status: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} error: {str(e)}")
        
        # Wait longer before retrying (Exponential Backoff)
        time.sleep(2 * (attempt + 1))
        
    return None

@app.route('/')
def index():
    api_url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    raw_data = fetch_with_retry(api_url)
    
    if raw_data:
        try:
            # Process data for the table
            processed = {
                "time": raw_data['records']['timestamp'],
                "price": raw_data['records']['underlyingValue'],
                "data": raw_data['filtered']['data'][:12], # Show top 12 strikes
                "status": "Success"
            }
            return render_template('index.html', data=processed)
        except KeyError:
            return render_template('index.html', data={"status": "Error", "error": "Data format mismatch from NSE."})
    
    return render_template('index.html', data={"status": "Error", "error": "NSE is currently blocking Render's IP. Try again in 5 minutes."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
