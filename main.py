from flask import Flask
import requests
import time
from datetime import datetime

app = Flask(__name__)

def fetch_live_nse_data():
    """Fetch LIVE NSE data from Yahoo Finance API"""
    symbols = {
        "^NSEI": "NIFTY_50", "^NSEBANK": "NIFTY_BANK", "SBIN.NS": "SBIN", 
        "HDFCBANK.NS": "HDFCBANK", "ICICIBANK.NS": "ICICIBANK", "INFY.NS": "INFY",
        "TCS.NS": "TCS", "RELIANCE.NS": "RELIANCE", "LT.NS": "LT", "BHARTIARTL.NS": "BHARTIARTL"
    }
    
    live_data = []
    
    for yahoo_symbol, display_name in symbols.items():
        try:
            # Yahoo Finance quote summary API (fastest)
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{yahoo_symbol}"
            params = {'modules': 'price'}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=8)
            data = response.json()
            
            if 'quoteSummary' in data and data['quoteSummary']['result']:
                quote = data['quoteSummary']['result'][0]['price']
                
                live_data.append({
                    'symbol': display_name,
                    'ltp': round(float(quote.get('regularMarketPrice', 0)), 2),
                    'open': round(float(quote.get('regularMarketOpen', 0)), 2),
                    'high': round(float(quote.get('regularMarketDayHigh', 0)), 2),
                    'low': round(float(quote.get('regularMarketDayLow', 0)), 2),
                    'prev_close': round(float(quote.get('regularMarketPreviousClose', 0)), 2),
                    'volume': int(quote.get('regularMarketVolume', 0)),
                    'change': round(float(quote.get('regularMarketPrice', 0)) - float(quote.get('regularMarketPreviousClose', 0)), 2)
                })
        except:
            # Fallback - show symbol even if no data
            live_data.append({
                'symbol': display_name, 'ltp': 0, 'open': 0, 'high': 0, 
                'low': 0, 'prev_close': 0, 'volume': 0, 'change': 0
            })
    
    return live_data

@app.route('/')
def index():
    # Fetch LIVE data from Yahoo Finance
    data = fetch_live_nse_data()
    timestamp = datetime.now().strftime("%H:%M:%S IST")
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>🇮🇳 NSE LIVE DASHBOARD by Sumit Gujrathi</title>
    <meta http-equiv="refresh" content="60">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:Arial,sans-serif;background:#1a1a1a;color:#fff;min-height:100vh;padding:20px;}}
        .container{{max-width:1400px;margin:0 auto;}}
        h1{{color:#00d4ff;text-align:center;font-size:2.5em;margin-bottom:10px;}}
        .timestamp{{text-align:center;color:#a0a0a0;font-size:1.1em;margin-bottom:30px;}}
        table{{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:15px;overflow:hidden;box-shadow:0 20px 40px rgba(0,0,0,0.5);}}
        th{{background:#00d4ff;color:#000;padding:15px;font-weight:600;text-align:left;}}
        td{{padding:12px 15px;border-bottom:1px solid rgba(255,255,255,0.1);}}
        tr:hover{{background:rgba(255,255,255,0.1);}}
        .symbol{{font-weight:bold;color:#00d4ff;}}
        .ltp{{color:#ffd700;font-weight:bold;font-size:1.2em;}}
        .positive{{color:#00ff88;}}
        .negative{{color:#ff4444;}}
        .volume{{color:#a0a0a0;font-family:monospace;}}
        .footer{{text-align:center;margin-top:30px;color:#888;padding:20px;}}
    </style>
</head>
<body>
    <div class="container">
        <h1>🇮🇳 NSE LIVE QUOTES</h1>
        <div class="timestamp">Updated: {timestamp} | Auto Refresh: 60 seconds</div>
        
        <table>
            <tr>
                <th>Symbol</th><th>LTP</th><th>Open</th><th>High</th><th>Low</th><th>Prev Close</th><th>Volume</th><th>Change</th>
            </tr>
    '''
    
    for row in data:
        change_class = "positive" if row['change'] >= 0 else "negative"
        html += f'''
            <tr>
                <td class="symbol">{row['symbol']}</td>
                <td class="ltp">{row['ltp'] or '—'}</td>
                <td>{row['open'] or '—'}</td>
                <td>{row['high'] or '—'}</td>
                <td>{row['low'] or '—'}</td>
                <td>{row['prev_close'] or '—'}</td>
                <td class="volume">{row['volume']:, if row['volume'] else '—'}</td>
                <td class="{change_class}">{"+" if row["change"] >= 0 else ""}{row["change"]:.2f}</td>
            </tr>
        '''
    
    html += '''
        </table>
        <div class="footer">
            📈 LIVE from Yahoo Finance | NSE: 9:15 AM - 3:30 PM IST | Updates every 60s
        </div>
    </div>
</body>
</html>
    '''
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
