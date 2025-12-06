from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

# Index & stock symbols
SYMBOLS = {
    "NIFTY 50": "NIFTY 50",
    "NIFTY BANK": "NIFTY BANK",
    "RELIANCE": "RELIANCE",
    "TCS": "TCS",
    "HDFCBANK": "HDFCBANK",
    "ICICIBANK": "ICICIBANK",
    "INFY": "INFY",
    "SBIN": "SBIN",
    "LT": "LT",
    "BHARTIARTL": "BHARTIARTL"
}

# NSE requires session + headers
session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

def init_nse_session():
    """Initialize session for NSE India"""
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    except:
        pass

def fetch_from_nse(symbol):
    """Fetch LIVE data from NSE India"""

    # Resolve index vs stock
    if symbol in ["NIFTY 50", "NIFTY BANK"]:
        url = f"https://www.nseindia.com/api/marketStatus"
        try:
            r = session.get(url, headers=HEADERS, timeout=10)
            data = r.json()

            for idx in data["marketState"]:
                if idx["index"] == symbol:
                    return {
                        "symbol": symbol,
                        "ltp": idx.get("last", "—"),
                        "open": "—",
                        "high": "—",
                        "low": "—",
                        "prev_close": idx.get("previousClose", "—"),
                        "volume": "—",
                        "change": idx.get("change", "—")
                    }
        except:
            pass

    # Stock Quote API (LIVE)
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

    try:
        r = session.get(url, headers=HEADERS, timeout=10)
        data = r.json()

        price_data = data["priceInfo"]

        return {
            "symbol": symbol,
            "ltp": price_data.get("lastPrice", "—"),
            "open": price_data.get("open", "—"),
            "high": price_data.get("intraDayHighLow", {}).get("max", "—"),
            "low": price_data.get("intraDayHighLow", {}).get("min", "—"),
            "prev_close": price_data.get("previousClose", "—"),
            "volume": data.get("securityInfo", {}).get("totalTradedVolume", "—"),
            "change": price_data.get("change", "—")
        }

    except Exception as e:
        return {
            "symbol": symbol,
            "ltp": "—",
            "open": "—",
            "high": "—",
            "low": "—",
            "prev_close": "—",
            "volume": "—",
            "change": "—"
        }


@app.route("/")
def index():
    init_nse_session()

    data = [fetch_from_nse(sym) for sym in SYMBOLS.values()]
    timestamp = datetime.now().strftime("%H:%M:%S")

    html = f"""
    <html>
    <head>
        <title>NSE INDIA LIVE</title>
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
        <h2>📈 NSE INDIA LIVE MARKET DATA</h2>
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
        cls = "green" if str(row["change"]).startswith("+") else "red"
        html += f"""
            <tr>
                <td>{row['symbol']}</td>
                <td class='yellow'>{row['ltp']}</td>
                <td>{row['open']}</td>
                <td>{row['high']}</td>
                <td>{row['low']}</td>
                <td>{row['prev_close']}</td>
                <td>{row['volume']}</td>
                <td class='{cls}'>{row['change']}</td>
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
                                          
