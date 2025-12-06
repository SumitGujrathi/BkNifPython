from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

# NSE symbols with Yahoo keys
SYMBOLS = {
    "%5ENSEI": "NIFTY 50",
    "%5ENSEBANK": "BANKNIFTY",
    "RELIANCE.NS": "RELIANCE",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFCBANK",
    "ICICIBANK.NS": "ICICIBANK",
    "INFY.NS": "INFY",
    "SBIN.NS": "SBIN",
    "LT.NS": "LT",
    "BHARTIARTL.NS": "AIRTEL"
}

def fetch_yahoo(symbol):
    """Fetch price from Yahoo using AllOrigins unblocker"""
    yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    proxy_url = "https://api.allorigins.win/raw?url=" + requests.utils.quote(yahoo_url)

    try:
        r = requests.get(proxy_url, timeout=10)
        data = r.json()

        meta = data["chart"]["result"][0]["meta"]

        price = meta.get("regularMarketPrice", 0)
        prev = meta.get("chartPreviousClose", 0)
        change = round(price - prev, 2)

        return {
            "symbol": SYMBOLS[symbol],
            "price": round(price, 2),
            "prev_close": round(prev, 2),
            "change": change,
            "open": meta.get("regularMarketOpen", 0),
            "high": meta.get("regularMarketDayHigh", 0),
            "low": meta.get("regularMarketDayLow", 0),
            "volume": meta.get("regularMarketVolume", 0)
        }

    except:
        return {
            "symbol": SYMBOLS[symbol],
            "price": "—",
            "prev_close": "—",
            "change": "—",
            "open": "—",
            "high": "—",
            "low": "—",
            "volume": "—"
        }

@app.route("/")
def index():
    data = [fetch_yahoo(sym) for sym in SYMBOLS]

    timestamp = datetime.now().strftime("%H:%M:%S")

    html = f"""
    <html>
    <head>
        <title>NSE LIVE DASHBOARD</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{
                background:#121212;
                color:white;
                font-family:Arial;
                padding:20px;
            }}
            h2 {{
                text-align:center;
                color:#00eaff;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
                margin-top:20px;
            }}
            th {{
                background:#00eaff;
                color:black;
                padding:10px;
                text-align:left;
            }}
            td {{
                padding:10px;
                border-bottom:1px solid #333;
            }}
            tr:hover {{
                background:#1f1f1f;
            }}
            .green {{ color:#00ff88; font-weight:bold; }}
            .red {{ color:#ff4444; font-weight:bold; }}
            .yellow {{ color:#ffdd33; font-weight:bold; }}
        </style>
    </head>
    <body>
        <h2>📈 NSE LIVE MARKET DATA</h2>
        <p style='text-align:center;color:#ccc;'>Updated: {timestamp} (Auto-refresh 60s)</p>

        <table>
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
    """

    for row in data:
        change_class = "green" if isinstance(row["change"], (int, float)) and row["change"] >= 0 else "red"

        html += f"""
            <tr>
                <td>{row['symbol']}</td>
                <td class='yellow'>{row['price']}</td>
                <td>{row['open']}</td>
                <td>{row['high']}</td>
                <td>{row['low']}</td>
                <td>{row['prev_close']}</td>
                <td>{row['volume']}</td>
                <td class='{change_class}'>{row['change']}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
    
