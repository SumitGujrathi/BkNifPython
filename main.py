from flask import Flask, render_template
import requests
import json
from datetime import datetime

app = Flask(__name__)

symbols = ["^NSEI", "^NSEBANK", "ACC.NS", "ADANIPORTS.NS", "SBIN.NS", "HDFCBANK.NS"]

def fetch_yahoo_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {'period1': '0', 'period2': '9999999999', 'interval': '1m'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        if data['chart']['result']:
            quote = data['chart']['result'][0]
            meta = quote['meta']
            timestamps = quote['timestamp']
            if timestamps:
                latest = quote['indicators']['quote'][0]
                return {
                    'symbol': symbol.replace('.NS', '').replace('^NSEI', 'NIFTY_50').replace('^NSEBANK', 'NIFTY_BANK'),
                    'ltp': round(latest['close'][-1] if latest['close'] else 0, 2),
                    'open': round(meta.get('regularMarketOpen', 0), 2),
                    'high': round(meta.get('regularMarketDayHigh', 0), 2),
                    'low': round(meta.get('regularMarketDayLow', 0), 2),
                    'prev_close': round(meta.get('regularMarketPreviousClose', 0), 2),
                    'volume': int(latest['volume'][-1]) if latest['volume'] else 0
                }
    except:
        pass
    return None

def fetch_data():
    data = []
    for symbol in symbols:
        result = fetch_yahoo_data(symbol)
        if result:
            data.append(result)
    return data

@app.route('/')
def index():
    data = fetch_data()
    last_update = datetime.now().strftime("%H:%M:%S IST")
    return render_template('index.html', data=data, last_update=last_update)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
