from flask import Flask
import requests
from datetime import datetime
import time

app = Flask(__name__)

# ------------------------
# NSE symbols (indices + stocks)
# ------------------------
SYMBOLS = [
    ("NIFTY 50", "NIFTY 50"),
    ("NIFTY BANK", "NIFTY BANK"),
    ("ACC", "ACC"),
    ("ADANIPORTS", "ADANIPORTS"),
    ("SBIN", "SBIN"),
    ("AMBUJACEM", "AMBUJACEM"),
    ("WIPRO", "WIPRO"),
    ("APOLLOTYRE", "APOLLOTYRE"),
    ("ASIANPAINT", "ASIANPAINT"),
    ("AUROPHARMA", "AUROPHARMA"),
    ("AXISBANK", "AXISBANK"),
    ("BAJFINANCE", "BAJFINANCE"),
    ("IOC", "IOC"),
    ("BANKBARODA", "BANKBARODA"),
    ("BATAINDIA", "BATAINDIA"),
    ("BERGEPAINT", "BERGEPAINT"),
    ("BHARATFORG", "BHARATFORG"),
    ("COALINDIA", "COALINDIA"),
    ("INDUSINDBK", "INDUSINDBK"),
    ("DRREDDY", "DRREDDY"),
    ("INFY", "INFY"),
    ("JSWSTEEL", "JSWSTEEL"),
    ("POWERGRID", "POWERGRID"),
    ("LICHSGFIN", "LICHSGFIN"),
    ("CANBK", "CANBK"),
    ("MGL", "MGL"),
    ("M&MFIN", "M&MFIN"),
    ("HDFCBANK", "HDFCBANK"),
    ("MANAPPURAM", "MANAPPURAM"),
    ("MARICO", "MARICO"),
    ("SUNTV", "SUNTV"),
    ("HINDZINC", "HINDZINC"),
    ("ICICIBANK", "ICICIBANK"),
    ("ZEEL", "ZEEL")
]

# ------------------------
# NSE session + headers
# ------------------------
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://www.nseindia.com",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

# ------------------------
# Cache last stock values to prevent blank display
# ------------------------
LAST_RESULTS = {}

# ------------------------
# Initialize NSE session (fetch cookies)
# ------------------------
def init_nse():
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    except:
        pass

# ------------------------
# Fetch indices (NIFTY 50 & BANK NIFTY) in one request
# ------------------------
def fetch_indices():
    try:
        url = "https://www.nseindia.com/api/allIndices"
        r = session.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        indices = {}
        for idx in data["data"]:
            if idx["index"] in ["NIFTY 50", "NIFTY BANK"]:
                indices[idx["index"]] = {
                    "symbol": idx["index"],
                    "ltp": idx.get("last", "—"),
                    "open": idx.get("open", "—"),
                    "high": idx.get("high", "—"),
                    "low": idx.get("low", "—"),
                    "prev_close": idx.get("previousClose", "—"),
                    "volume": idx.get("tradedVolume", "—"),
                    "change": idx.get("variation", "—")
                }
        return indices
    except:
        # fallback to last results
        return {idx: LAST_RESULTS.get(idx, {}) for idx in ["NIFTY 50", "NIFTY BANK"]}

# ------------------------
# Fetch individual stock data
# ------------------------
def fetch_stock(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        r = session.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        p = data["priceInfo"]
        stock_data = {
            "symbol": symbol,
            "ltp": p.get("lastPrice", "—"),
            "open": p.get("open", "—"),
            "high": p.get("intraDayHighLow", {}).get("max", "—"),
            "low": p.get("intraDayHighLow", {}).get("min", "—"),
            "prev_close": p.get("previousClose", "—"),
            "volume": data.get("securityInfo", {}).get("totalTradedVolume", "—"),
            "change": p.get("change", "—")
        }
        return stock_data
    except:
        # fallback to last result
        return LAST_RESULTS.get(symbol, {"symbol": symbol, "ltp":"—","open":"—","high":"—","low":"—","prev_close":"—","volume":"—","change":"—"})

# ------------------------
# Flask route
# ------------------------
@app.route("/")
def index():
    init_nse()

    results = {}

    # Fetch indices first
    indices_data = fetch_indices()
    results.update(indices_data)

    # Fetch individual stocks
    for name, symbol in SYMBOLS:
        if symbol not in ["NIFTY 50", "NIFTY BANK"]:
            stock_data = fetch_stock(symbol)
            results[symbol] = stock_data
            time.sleep(0.15)  # small delay to prevent NSE throttling

    # Store results in LAST_RESULTS cache
    LAST_RESULTS.update(results)

    timestamp = datetime.now().strftime("%H:%M:%S")

    # Generate HTML
    html = f"""
    <html>
    <head>
        <title>NSE LIVE DASHBOARD by Sumit Gujrathi</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body {{ background:#121212; color:white; font-family:Arial; padding:20px; }}
            h2 {{ text-align:center; color:#00eaff; }}
            table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
            th {{ background:#00eaff; color:black; padding:10px; }}
            td {{ padding:10px; border-bottom:1px solid #333; }}
            tr:hover {{ background:#1f1f1f; }}
            .green {{ color:#00ff88; font-weight:bold; }}
            .red {{ color:#ff4444; font-weight:bold; }}
            .yellow {{ color:#ffdd33; font-weight:bold; }}
        </style>
    </head>
    <body>
        <h2>📈 NSE LIVE MARKET DATA by Sumit Gujrathi</h2>
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

    for symbol, row in results.items():
        cls = "green" if isinstance(row["change"], (int, float)) and row["change"] >= 0 else "red"
        html += f"""
            <tr>
                <td>{row["symbol"]}</td>
                <td class='yellow'>{row["ltp"]}</td>
                <td>{row["open"]}</td>
                <td>{row["high"]}</td>
                <td>{row["low"]}</td>
                <td>{row["prev_close"]}</td>
                <td>{row["volume"]}</td>
                <td class='{cls}'>{row["change"]}</td>
            </tr>
        """

    html += "</table></body></html>"

    return html

# ------------------------
# Run Flask app
# ------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
