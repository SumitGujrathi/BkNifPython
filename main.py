import pandas as pd
from flask import Flask, render_template
from datetime import datetime
import pytz
import os
import sys

# Import the specific NSE function from the community library
try:
    from nsepython import nse_optionchain_scrapper
except ImportError:
    # If deploying on Render, this check will fail if requirements.txt is missing nsepython
    # For local testing, ensure it is installed.
    print("Error: The 'nsepython' library is not installed.")
    sys.exit(1)


# --- Configuration ---
SYMBOL = "NIFTY" 
# Use environment variable for port (required by Render) or default to 5000
PORT = int(os.environ.get('PORT', 5000))
IST = pytz.timezone('Asia/Kolkata')

app = Flask(__name__)


def is_market_open():
    """Checks if the time is within the NSE regular trading hours (9:15 AM to 3:30 PM IST)."""
    now_ist = datetime.now(IST)
    
    if now_ist.weekday() >= 5:
        return False, f"Weekend ({now_ist.strftime('%A')})"

    market_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)

    if market_open <= now_ist <= market_close:
        return True, "Market Open"
    
    if now_ist < market_open:
        return False, "Pre-Open"
    
    return False, "Market Closed"


def fetch_and_process_oc_data():
    """Fetches, processes, and returns the Option Chain DataFrame."""
    
    is_open, status = is_market_open()
    
    if not is_open:
        # Return empty data structure if market is closed
        return None, status, None

    try:
        # Fetch data using the reliable nsepython library
        data = nse_optionchain_scrapper(SYMBOL)
        
        if not (data and 'records' in data and 'data' in data['records']):
            return None, "Data Filtered/Empty", None

        # --- Data Processing (Same logic as before) ---
        option_data = data['records']['data']
        underlying_value = data['records']['underlyingValue']
        expiry_date = data['records']['expiryDates'][0]
        
        nearest_strike = round(underlying_value / 50) * 50
        STRIKE_RANGE = 5
        min_strike = nearest_strike - (STRIKE_RANGE * 50)
        max_strike = nearest_strike + (STRIKE_RANGE * 50)
        
        filtered_options = [
            item for item in option_data 
            if item.get('expiryDate') == expiry_date and min_strike <= item.get('strikePrice', 0) <= max_strike
        ]
        
        structured_data = []
        for item in filtered_options:
            strike = item.get('strikePrice')
            ce = item.get('CE', {})
            pe = item.get('PE', {})
            
            structured_data.append({
                'CE_OI': ce.get('openInterest', 0),
                'CE_Chg_OI': ce.get('changeinOpenInterest', 0),
                'CE_LTP': ce.get('lastPrice', 0),
                'Strike Price': strike,
                'PE_LTP': pe.get('lastPrice', 0),
                'PE_Chg_OI': pe.get('changeinOpenInterest', 0),
                'PE_OI': pe.get('openInterest', 0)
            })

        df = pd.DataFrame(structured_data)
        
        # Prepare header data for the template
        header_data = {
            'ltp': f"₹{underlying_value:,.2f}",
            'expiry': expiry_date,
            'refresh_time': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
        }
        
        # Convert DataFrame to HTML table, highlighting ATM strike
        def highlight_atm(row):
            is_atm = row['Strike Price'] == nearest_strike
            return ['style="background-color: #ffff99;"' if is_atm else '' for _ in row]

        # Use to_html for Flask compatibility
        html_table = df.to_html(
            index=False, 
            classes='table table-striped table-bordered text-center', 
            float_format='%.2f',
            justify='center',
            formatters={
                'Strike Price': lambda x: f'{x:,.0f}',
            }
        )
        
        return html_table, "Market Open", header_data

    except Exception as e:
        print(f"Error during data fetch/processing: {e}")
        return None, f"Error: {e}", None

@app.route('/')
def index():
    """Main route to fetch and display the Option Chain data."""
    table_html, status, header_data = fetch_and_process_oc_data()
    
    return render_template(
        'index.html', 
        table_html=table_html,
        status=status,
        header=header_data
    )

if __name__ == '__main__':
    # Use Gunicorn in a production environment (like Render), but Flask dev server for local testing
    print(f"Starting Flask server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
