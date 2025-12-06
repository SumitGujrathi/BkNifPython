from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

# All Yahoo symbols in one list (FAST API)
symbols = [
    "^NSEI", "^NSEBANK",
    "SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "INFY.NS", "TCS.NS", "RELIANCE.NS",
    "LT.NS", "BHARTIARTL.NS"
]

# Mapping for display
display_map = {
    "^NSEI": "NIFTY_50",
    "^NSEBANK": "NIFTY_BANK",
    "SBIN.NS": "SBIN",
    "HDFCBANK.NS": "HDFCBANK",
    "ICICIBANK.NS": "ICICIBANK",
    "INFY.NS": "INFY",
    "TCS.NS": "TCS",
    "RELIANCE.NS": "RELIANCE",
    "LT.NS": "LT",
    "BHARTIARTL.NS": "BHARTIARTL"
}

def fetch_live_nse_data():
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ",".join(symbols)}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        result = r.json()["quoteResponse"]["result"]

        live_data = []

        for item in result:
            sym = item["symbol"]
            live_data.append({
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

        return live_data

    except Exception as e:
        print("ERROR FETCHING DATA →", e)
        return []


@app.route("/")
def home():
    data = fetch_live_nse_data()
    timestamp = datetime.now().strftime("%H:%M:%S")

    # If no data comes, show text (debug)
    if not data:
        return "<h1 style='color:white;background:black'>No data received. Yahoo API blocked or error.</h1>"

    html = f"""
    <html>
    <head>
        <title>NSE LIVE by Sumit Gujrathi</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{ background:#111; color:white; font-family:Arial; padding:20px; }}
            table {{ width:100%; border-collapse:collapse; }}
            th {{ background:#00d4ff; color:black; padding:12px; }}
            td {{ padding:10px; border-bottom:1px solid #333; }}
            .positive {{ color:#00ff88; }}
            .negative {{ color:#ff4444; }}
        </style>
    </head>
    <body>
        <h1>NSE LIVE QUOTES</h1>
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
        cls = "positive" if row["change"] >= 0 else "negative"
        volume = f"{row['volume']:,}" if row["volume"] else "—"

        html += f"""
            <tr>
                <td>{row['symbol']}</td>
                <td>{row['ltp']}</td>
                <td>{row['open']}</td>
                <td>{row['high']}</td>
                <td>{row['low']}</td>
                <td>{row['prev_close']}</td>
                <td>{volume}</td>
                <td class='{cls}'>{row['change']}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html


app.run(host="0.0.0.0", port=5000, debug=True)
        
