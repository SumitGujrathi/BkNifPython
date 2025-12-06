from flask import Flask, render_template
import yfinance as yf
import time
from datetime import datetime

app = Flask(__name__)

symbols = [
    "^NSEI", "^NSEBANK", "ACC.NS", "ADANIPORTS.NS", "SBIN.NS", "AMBUJACEM.NS",
    "WIPRO.NS", "APOLLOTYRE.NS", "ASIANPAINT.NS", "AUROPHARMA.NS",
    "AXISBANK.NS", "BAJFINANCE.NS", "IOC.NS", "BANKBARODA.NS"
    # Add more during testing
]

def fetch_data():
    data = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d", interval="5m")
            if not hist.empty and len(hist) > 0:
                latest = hist.iloc[-1]
                data.append({
                    'symbol': symbol.replace('.NS', '').replace('^NSEI', 'NIFTY_50').replace('^NSEBANK', 'NIFTY_BANK'),
                    'ltp': round(info.get('currentPrice', latest.get('Close', 0)), 2),
                    'open': round(latest.get('Open', 0), 2),
                    'high': round(latest.get('High', 0), 2),
                    'low': round(latest.get('Low', 0), 2),
                    'prev_close': round(info.get('previousClose', 0), 2),
                    'volume': int(latest.get('Volume', 0))
                })
        except Exception as e:
            print(f"Error {symbol}: {e}")
            continue
    return data

@app.route('/')
def index():
    data = fetch_data()
    last_update = datetime.now().strftime("%H:%M:%S IST")
    return render_template('index.html', data=data, last_update=last_update)

if __name__ == '__main__':
    app.run(debug=True)
