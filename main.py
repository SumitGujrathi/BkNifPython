import yfinance as yf
import pandas as pd
from flask import Flask, render_template
import datetime
import os

app = Flask(__name__)

def get_nifty_options():
    try:
        # 1. Connect to Nifty 50 Ticker
        nifty = yf.Ticker("^NSEI")
        
        # 2. Get the current price (LTP)
        history = nifty.history(period="1d")
        if history.empty:
            return {"status": "Error", "error": "Market Data Unavailable (Check if market is open)"}
        
        spot_price = history['Close'].iloc[-1]
        
        # 3. Get all available expiry dates
        expiries = nifty.options
        if not expiries:
            return {"status": "Error", "error": "No expiry dates found"}
            
        # 4. Fetch the nearest expiry
        chain = nifty.option_chain(expiries[0])
        calls = chain.calls
        puts = chain.puts
        
        # 5. Merge Calls and Puts
        df = pd.merge(calls[['strike', 'lastPrice', 'openInterest']], 
                     puts[['strike', 'lastPrice', 'openInterest']], 
                     on='strike', how='inner', suffixes='_CE', '_PE')
        
        # 6. Filter ATM Strikes (+/- 5 strikes)
        atm_strike = round(spot_price / 50) * 50
        df = df[(df['strike'] >= atm_strike - 250) & (df['strike'] <= atm_strike + 250)]
        
        records = []
        for _, row in df.iterrows():
            records.append({
                "CE": {"openInterest": int(row['openInterest_CE']) if not pd.isna(row['openInterest_CE']) else 0, 
                       "lastPrice": round(row['lastPrice_CE'], 2)},
                "strikePrice": row['strike'],
                "PE": {"lastPrice": round(row['lastPrice_PE'], 2), 
                       "openInterest": int(row['openInterest_PE']) if not pd.isna(row['openInterest_PE']) else 0}
            })
            
        return {
            "status": "Success",
            "price": round(spot_price, 2),
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "data": records
        }
    except Exception as e:
        return {"status": "Error", "error": str(e)}

@app.route('/')
def index():
    result = get_nifty_options()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    # Render binds to a specific PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
