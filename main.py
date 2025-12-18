import yfinance as yf
import pandas as pd
from flask import Flask, render_template
import datetime

app = Flask(__name__)

def get_nifty_options():
    try:
        # 1. Connect to Nifty 50 Ticker
        nifty = yf.Ticker("^NSEI")
        
        # 2. Get the current price (LTP)
        spot_price = nifty.history(period="1d")['Close'].iloc[-1]
        
        # 3. Get all available expiry dates
        expiries = nifty.options
        if not expiries:
            return {"status": "Error", "error": "No expiry dates found"}
            
        # 4. Fetch the nearest expiry (the first one in the list)
        chain = nifty.option_chain(expiries[0])
        calls = chain.calls
        puts = chain.puts
        
        # 5. Merge Calls and Puts on Strike Price
        df = pd.merge(calls[['strike', 'lastPrice', 'openInterest']], 
                     puts[['strike', 'lastPrice', 'openInterest']], 
                     on='strike', how='inner', suffixes=('_CE', '_PE'))
        
        # 6. Filter for strikes near the Spot Price (ATM +/- 5 strikes)
        atm_strike = round(spot_price / 50) * 50
        df = df[(df['strike'] >= atm_strike - 250) & (df['strike'] <= atm_strike + 250)]
        
        # 7. Format for HTML
        records = []
        for _, row in df.iterrows():
            records.append({
                "CE": {"openInterest": int(row['openInterest_CE']), "lastPrice": row['lastPrice_CE']},
                "strikePrice": row['strike'],
                "PE": {"lastPrice": row['lastPrice_PE'], "openInterest": int(row['openInterest_PE'])}
            })
            
        return {
            "status": "Success",
            "price": round(spot_price, 2),
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": records
        }
    except Exception as e:
        return {"status": "Error", "error": f"Yahoo API Error: {str(e)}"}

@app.route('/')
def index():
    result = get_nifty_options()
    return render_template('index.html', data=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
