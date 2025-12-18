import cloudscraper
import logging
from flask import Flask, render_template

# Setup logging to see what's happening in Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_nse_data():
    # Create a scraper instance that mimics a real browser
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        # Step 1: Hit the home page first to establish a real session
        logger.info("Accessing NSE Homepage for session...")
        scraper.get("https://www.nseindia.com", timeout=15)
        
        # Step 2: Fetch the actual Option Chain data
        api_url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        logger.info("Fetching Option Chain...")
        response = scraper.get(api_url, timeout=15)
        
        logger.info(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            json_data = response.json()
            return {
                "time": json_data['records']['timestamp'],
                "price": json_data['records']['underlyingValue'],
                "data": json_data['filtered']['data'][:10], # Nearest 10 strikes
                "status": "Success"
            }
        else:
            return {"status": "Error", "error": f"NSE Error Code: {response.status_code}"}

    except Exception as e:
        logger.error(f"Scraper Failed: {str(e)}")
        return {"status": "Error", "error": "Connection failed. NSE might be blocking the server."}

@app.route('/')
def index():
    result = fetch_nse_data()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
