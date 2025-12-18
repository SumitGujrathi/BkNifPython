from flask import Flask, render_template
from yahooquery import Ticker
import pandas as pd
import os
import datetime

app = Flask(__name__)

# Fake browser headers to prevent Yahoo from blocking Render
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_live_data():
    try:
        # Use a real User-Agent to avoid the "str has no attribute empty" error
        nifty = Ticker('^NSEI', headers=HEADERS)
        
        # Get the Option Chain
        df = nifty.option_chain
        
        # FIX: Check if df is a string (error message) instead of a DataFrame
        if isinstance(df, str) or df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return {"status": "Error", "error": "Yahoo Finance blocked the request. Try again in 30s."}

        # Get Spot Price
        price_dict = nifty.price
        if '^NSEI' not in price_dict:
             return {"status": "Error", "error": "Could not fetch spot price."}
             
        spot_price = price_dict['^NSEI'].get('regularMarketPrice', 0)
        
        # Get nearest expiry
        all_expiries = df.index.get_level_values('expiration').unique()
        nearest_expiry = all_expiries[0]
        
        # Filter for current expiry
        current_chain = df.xs(nearest_expiry, level='expiration')
        
        # Process Calls and Puts
        calls = current_chain[current_chain['optionType'] == 'calls']
        puts = current_chain[current_chain['optionType'] == 'puts']
        
        merged = pd.merge(
            calls[['strike', 'lastPrice', 'openInterest']],
            puts[['strike', 'lastPrice', 'openInterest']],
            on='strike', how='inner', suffixes=('_CE', '_PE')
        )

        # Filter strikes around the Spot price
        atm_strike = round(spot_price / 50) * 50
        final_df = merged[(merged['strike'] >= atm_strike - 250) & (merged['strike'] <= atm_strike + 250)]

        records = []
        for _, row in final_df.iterrows():
            records.append({
                "CE": {"openInterest": int(row.get('openInterest_CE', 0)), "lastPrice": row.get('lastPrice_CE', 0)},
                "strikePrice": row['strike'],
                "PE": {"lastPrice": row.get('lastPrice_PE', 0), "openInterest": int(row.get('openInterest_PE', 0))}
            })

        return {
            "status": "Success",
            "price": spot_price,
            "expiry": str(nearest_expiry),
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "data": records
        }
    except Exception as e:
        return {"status": "Error", "error": f"Internal Error: {str(e)}"}

@app.route('/')
def index():
    result = get_live_data()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
