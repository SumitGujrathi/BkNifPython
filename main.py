from flask import Flask, render_template
from yahooquery import Ticker
import pandas as pd
import os
import datetime

app = Flask(__name__)

def get_live_data():
    try:
        # 1. Fetch Nifty data using yahooquery
        # Yahoo Symbol for Nifty 50 is ^NSEI
        nifty = Ticker('^NSEI')
        
        # 2. Get the Option Chain (all expiries)
        # yahooquery returns a dataframe directly
        df = nifty.option_chain
        
        if df is None or df.empty:
            return {"status": "Error", "error": "Yahoo data is temporarily offline. Try again in 1 min."}

        # 3. Get the current Spot Price for centering the table
        price_data = nifty.price['^NSEI']
        spot_price = price_data.get('regularMarketPrice', 0)
        
        # 4. Filter for the nearest Expiry (it's the first level of the index)
        all_expiries = df.index.get_level_values('expiration').unique()
        nearest_expiry = all_expiries[0]
        
        # Filter dataframe for just this expiry
        current_chain = df.xs(nearest_expiry, level='expiration')
        
        # 5. Split into Calls and Puts and Merge
        calls = current_chain[current_chain['optionType'] == 'calls']
        puts = current_chain[current_chain['optionType'] == 'puts']
        
        merged = pd.merge(
            calls[['strike', 'lastPrice', 'openInterest']],
            puts[['strike', 'lastPrice', 'openInterest']],
            on='strike', how='inner', suffixes=('_CE', '_PE')
        )

        # 6. Center the table around the ATM (At-The-Money) strike
        atm_strike = round(spot_price / 50) * 50
        final_df = merged[(merged['strike'] >= atm_strike - 300) & (merged['strike'] <= atm_strike + 300)]

        # 7. Format for HTML
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
        return {"status": "Error", "error": f"Bridge Error: {str(e)}"}

@app.route('/')
def index():
    result = get_live_data()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
