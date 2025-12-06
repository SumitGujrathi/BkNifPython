from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

app = Flask(__name__)

symbols = [
    "^NSEI", "^NSEBANK", "ACC.NS", "ADANIPORTS.NS", "SBIN.NS", "AMBUJACEM.NS",
    "WIPRO.NS", "APOLLOTYRE.NS", "ASIANPAINT.NS", "AUROPHARMA.NS",
    "AXISBANK.NS", "BAJFINANCE.NS", "IOC.NS", "BANKBARODA.NS",
    "BATAINDIA.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "COALINDIA.NS",
    "INDUSINDBK.NS", "DRREDDY.NS", "INFY.NS", "JSWSTEEL.NS",
    "POWERGRID.NS", "LICHSGFIN.NS", "CANBK.NS", "MGL.NS",
    "M&MFIN.NS", "HDFCBANK.NS", "MANAPPURAM.NS", "MARICO.NS",
    "SUNTV.NS", "HINDZINC.NS", "ICICIBANK.NS", "ZEEL.NS"
]

def fetch_data():
    data = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                latest = hist.iloc[-1]
                data.append({
                    'symbol': symbol.replace('.NS', '').replace('^NSEI', 'NIFTY_50').replace('^NSEBANK', 'NIFTY_BANK'),
                    'ltp': round(info.get('currentPrice', latest.get('Close', 0)), 2),
                    'open': round(latest.get('Open', 0), 2),
                    'high': round(latest.get('High', 0), 2),
                    'low': round(latest.get('Low', 0), 2),
                    'prev_close': round(info.get('previousClose', 0), 2),
                    'volume': int(latest.get('Volume', 0)),
                    'change': round(latest.get('Close', 0) - info.get('previousClose', 0), 2)
                })
        except:
            continue
    return pd.DataFrame(data).to_dict('records')

@app.route('/')
def index():
    data = fetch_data()
    last_update = datetime.now().strftime("%H:%M:%S IST")
    return render_template('index.html', data=data, last_update=last_update)

if __name__ == '__main__':
    app.run(debug=True)
