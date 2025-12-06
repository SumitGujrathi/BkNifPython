from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

YAHOO_URL = "https://query1.finance.yahoo.com/v7/finance/quote"

symbols = [
    "^NSEI", "^NSEBANK",
    "SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "INFY.NS", "TCS.NS", "RELIANCE.NS",
    "LT.NS", "BHARTIARTL.NS"
]

display_map = {
    "^NSEI": "NIFTY 50",
    "^NSEBANK": "BANKNIFTY",
    "SBIN.NS": "SBIN",
    "HDFCBANK.NS": "HDFCBANK",
    "ICICIBANK.NS": "ICICIBANK",
    "INFY.NS": "INFY",
    "TCS.NS": "TCS",
    "RELIANCE.NS": "RELIANCE",
    "LT.NS": "LT",
    "BHARTIARTL.NS": "BHARTIARTL"
}

# Required headers to bypass Yahoo blocks
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive"
}

def fetch_yahoo_data():
    try:
        session = requests.Session()
        session.headers.update(headers)

        # Yahoo requires initial cookie request
        session.get("https://query1.finance.yahoo.com", timeout=8)

        params = {"symbols": ",".join(symbols)}
        r = session.get(YAHOO_URL, params=params, timeout=10)
        result = r.json()["quoteResponse"]["result"]

        final = []

        for item in result:
            sym = item["symbol"]
            final.append({
                "symbol": display_map.get(sym, sym),
                "ltp": item.get("regularMarketPrice", 0),
                "open": item.get("regularMarketOpen", 0),
                "high": item.get("regularMarketDayHigh", 0),
                "low": item.get("regularMarketDayLow", 0),
                "prev_close": item.get("regularMarketPreviousClose", 0),
                "volume": item.get("regularMarketVolume", 0),
                "change": round(
                    item.get("regularMarketPrice", 0) -
                    item.get("regularMarketPreviousClose", 0), 2
                )
            })

        return final

    except Exception as e:
        print("Yahoo Fetch Error:", e)
        return []


@app.route("/")
def home():
    data = fetch_yahoo_data()
    timestamp = datetime.now().strftime("%H:%M:%S")

    if not data:
        return "<h1>No data received — Yahoo blocked or unreachable.</h1>"

    html = f"""
    <html>
    <head>
        <title>NSE LIVE (Sumit Gujrathi)</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{ background:#111; color:white; font-family:Arial; padding:20px; }}
            table {{ width:100%; border-collapse:collapse; }}
            th {{ background:#00d4ff; color:black; padding:12px; }}
            td {{ padding:10px; border-bottom:1px solid #333; }}
            .pos {{ color:#00ff88; }}
            .neg {{ color:#ff4444; }}
        </style>
    </head>

    <body>
        <h1>NSE LIVE — Yahoo Finance</h1>
        <p>Updated: {timestamp}</p>

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
        cls = "pos" if row["change"] >= 0 else "neg"
        vol = f"{row['volume']:,}" if row["volume"] else "—"

        html += f"""
            <tr>
                <td>{row['symbol']}</td>
                <td>{row['ltp']}</td>
                <td>{row['open']}</td>
                <td>{row['high']}</td>
                <td>{row['low']}</td>
                <td>{row['prev_close']}</td>
                <td>{vol}</td>
                <td class='{cls}'>{row['change']}</td>
            </tr>
        """

    html += "</table></body></html>"
    return html


app.run(host="0.0.0.0", port=5000, debug=True)
        
