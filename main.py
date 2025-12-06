from flask import Flask
import requests
import time
from datetime import datetime
import json

app = Flask(__name__)

# Your full NSE symbols list
SYMBOLS = {
    "^NSEI": "NIFTY_50",
    "^NSEBANK": "NIFTY_BANK",
    "ACC.NS": "ACC",
    "ADANIPORTS.NS": "ADANIPORTS",
    "SBIN.NS": "SBIN",
    "AMBUJACEM.NS": "AMBUJACEM",
    "WIPRO.NS": "WIPRO",
    "APOLLOTYRE.NS": "APOLLOTYRE",
    "ASIANPAINT.NS": "ASIANPAINT",
    "AUROPHARMA.NS": "AUROPHARMA",
    "AXISBANK.NS": "AXISBANK",
    "BAJFINANCE.NS": "BAJFINANCE",
    "IOC.NS": "IOC",
    "BANKBARODA.NS": "BANKBARODA",
    "BATAINDIA.NS": "BATAINDIA",
    "BERGEPAINT.NS": "BERGEPAINT",
    "BHARATFORG.NS": "BHARATFORG",
    "COALINDIA.NS": "COALINDIA",
    "INDUSINDBK.NS": "INDUSINDBK",
    "DRREDDY.NS": "DRREDDY",
    "INFY.NS": "INFY",
    "JSWSTEEL.NS": "JSWSTEEL",
    "POWERGRID.NS": "POWERGRID",
    "LICHSGFIN.NS": "LICHSGFIN",
    "CANBK.NS": "CANBK",
    "MGL.NS": "MGL",
    "M&MFIN.NS": "M&MFIN",
    "HDFCBANK.NS": "HDFCBANK",
    "MANAPPURAM.NS": "MANAPPURAM",
    "MARICO.NS": "MARICO",
    "SUNTV.NS": "SUNTV",
    "HINDZINC.NS": "HINDZINC",
    "ICICIBANK.NS": "ICICIBANK",
    "ZEEL.NS": "ZEEL"
}

def get_live_price(symbol):
    """Fetch LIVE price from Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'period1': int(time.time()) - 3600,  # 1 hour ago
            'period2': int(time.time()),         # now
            'interval': '1m',
            'includePrePost': 'true'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if 'chart' in data and data['chart']['result']:
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            return {
                'ltp': meta.get('regularMarketPrice', 0),
                'open': meta.get('regularMarketOpen', 0),
                'high': meta.get('regularMarketDayHigh', 0),
                'low': meta.get('regularMarketDayLow', 0),
                'prev_close': meta.get('regularMarketPreviousClose', 0),
                'volume': meta.get('regularMarketVolume', 0)
            }
    except:
        pass
    return {'ltp': 0, 'open': 0, 'high': 0, 'low': 0, 'prev_close': 0, 'volume': 0}

@app.route('/')
def index():
    # Fetch LIVE data
    live_data = []
    for yahoo_symbol, display_name in SYMBOLS.items():
        prices = get_live_price(yahoo_symbol)
        live_data.append({
            'symbol': display_name,
            'ltp': round(prices['ltp'], 2),
            'open': round(prices['open'], 2),
            'high': round(prices['high'], 2),
            'low': round(prices['low'], 2),
            'prev_close': round(prices['prev_close'], 2),
            'volume': int(prices['volume']) if prices['volume'] else 0,
            'change': round(prices['ltp'] - prices['prev_close'], 2)
        })
    
    # Generate HTML with LIVE data
    timestamp = datetime.now().strftime("%H:%M:%S IST")
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NSE Live Dashboard by Sumit Gujrathi- Auto Refresh 60s</title>
    <meta http-equiv="refresh" content="60">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); color: #fff; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2.5em; background: linear-gradient(45deg, #00d4ff, #ff6b9d); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }}
        .timestamp {{ font-size: 1.1em; color: #a0a0a0; }}
        table {{ width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 15px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.3); }}
        th {{ background: linear-gradient(45deg, #00d4ff, #0099cc); color: white; padding: 15px 12px; text-align: left; font-weight: 600; font-size: 0.95em; text-transform: uppercase; letter-spacing: 0.5px; }}
        td {{ padding: 14px 12px; border-bottom: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; }}
        tr:hover {{ background: rgba(255,255,255,0.08); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,212,255,0.2); }}
        .symbol {{ font-weight: 600; color: #00d4ff; font-size: 1em; }}
        .ltp {{ font-size: 1.3em; font-weight: bold; min-width: 100px; }}
        .positive {{ color: #00ff88; }}
        .negative {{ color: #ff4444; }}
        .volume {{ font-family: 'Courier New', monospace; color: #a0a0a0; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px; color: #888; }}
        @media (max-width: 768px) {{ .container {{ padding: 10px; }} th, td {{ padding: 8px 6px; font-size: 0.85em; }} .ltp {{ font-size: 1.1em; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇮🇳 NSE LIVE QUOTES</h1>
            <div class="timestamp">Updated: {timestamp} | Auto-refresh every 60 seconds</div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>LTP</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Prev Close</th>
                    <th>Volume</th>
                    <th>Change</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for row in live_data:
        change_class = "positive" if row['change'] >= 0 else "negative"
        html += f"""
                <tr>
                    <td class="symbol">{row['symbol']}</td>
                    <td class="ltp">{row['ltp'] or '—'}</td>
                    <td>{row['open'] or '—'}</td>
                    <td>{row['high'] or '—'}</td>
                    <td>{row['low'] or '—'}</td>
                    <td>{row['prev_close'] or '—'}</td>
                    <td class="volume">{row['volume']:, if row['volume'] else '—'}</td>
                    <td class="{change_class}">{row['change']:+.2f}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        <div class="footer">
            📈 NSE Market Hours: 9:15 AM - 3:30 PM IST | Powered by Yahoo Finance API | Render.com
        </div>
    </div>
</body>
</html>
    """
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
