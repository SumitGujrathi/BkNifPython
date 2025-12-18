from flask import Flask, render_template
from nsepython import nse_optionchain_scrapper
import pandas as pd

app = Flask(__name__)

def get_nifty_data():
    try:
        # Fetching NIFTY Option Chain
        payload = nse_optionchain_scrapper("NIFTY")
        
        # Extracting relevant data (Simplified for display)
        # In a real scenario, you'd parse 'CE' and 'PE' keys
        timestamp = payload['records']['timestamp']
        underlying_value = payload['records']['underlyingValue']
        
        return {
            "time": timestamp,
            "price": underlying_value,
            "data": payload['filtered']['data'][:10] # Top 10 strikes
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    option_data = get_nifty_data()
    return render_template('index.html', data=option_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
