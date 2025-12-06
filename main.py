from flask import Flask
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)

# ------------------------
# NSE symbols (indices + stocks)
# ------------------------
SYMBOLS = [
    ("NIFTY 50", "NIFTY 50"),
    ("NIFTY BANK", "NIFTY BANK"),
    ("ACC", "ACC.NS"),
    ("ADANIPORTS", "ADANIPORTS.NS"),
    ("SBIN", "SBIN.NS"),
    ("AMBUJACEM", "AMBUJACEM.NS"),
    ("WIPRO", "WIPRO.NS"),
    ("APOLLOTYRE", "APOLLOTYRE.NS"),
    ("ASIANPAINT", "ASIANPAINT.NS"),
    ("AUROPHARMA", "AUROPHARMA.NS"),
    ("AXISBANK", "AXISBANK.NS"),
    ("BAJFINANCE", "BAJFINANCE.NS"),
    ("IOC", "IOC.NS"),
    ("BANKBARODA", "BANKBARODA.NS"),
    ("BATAINDIA", "BATAINDIA.NS"),
    ("BERGEPAINT", "BERGEPAINT.NS"),
    ("BHARATFORG", "BHARATFORG.NS"),
    ("COALINDIA", "COALINDIA.NS"),
    ("INDUSINDBK", "INDUSINDBK.NS"),
    ("DRREDDY", "DRREDDY.NS"),
    ("INFY", "INFY.NS"),
    ("JSWSTEEL", "JSWSTEEL.NS"),
    ("POWERGRID", "POWERGRID.NS"),
    ("LICHSGFIN", "LICHSGFIN.NS"),
    ("CANBK", "CANBK.NS"),
    ("MGL", "MGL.NS"),
    ("M&MFIN", "M&MFIN.NS"),
    ("HDFCBANK", "HDFCBANK.NS"),
    ("MANAPPURAM", "MANAPPURAM.NS"),
    ("MARICO", "MARICO.NS"),
    ("SUNTV", "SUNTV.NS"),
    ("HINDZINC", "HINDZINC.NS"),
    ("ICICIBANK", "ICICIBANK.NS"),
    ("ZEEL", "ZEEL.NS")
]

# ------------------------
# NSE session for indices
# ------------------------
nse_session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://www.nseindia.com",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

# ------------------------
# In-memory cache
# ------------------------
CACHE = {}
CACHE_LOCK = threading.Lock()

# ------------------------
# Initialize NSE session
# ------------------------
def init_nse():
    try:
        nse_session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    except:
        pass

# ------------------------
# Fetch NIFTY indices
# ------------------------
def fetch_indices():
    try:
        url = "https://www.nseindia.com/api/allIndices"
        r = nse_session.get(url, headers=HEADERS, timeout=10)
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
        # fallback
        return {idx: CACHE.get(idx, {}) for idx in ["NIFTY 50", "NIFTY BANK"]}

# ------------------------
# Fetch stock data from Yahoo Finance
# ------------------------
def fetch_stock_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        r = requests.get(url, timeout=10)
        data = r.json()
        quote = data["quoteResponse"]["result"][0]
        return {
            "symbol": quote.get("shortName", symbol),
            "ltp": quote.get("regularMarketPrice", "—"),
            "open": quote.get("regularMarketOpen", "—"),
            "high": quote.get("regularMarketDayHigh", "—"),
            "low": quote.get("regularMarketDayLow", "—"),
            "prev_close": quote.get("regularMarketPreviousClose", "—"),
            "volume": quote.get("regularMarketVolume", "—"),
            "change": round(quote.get("regularMarketPrice", 0) - quote.get("regularMarketPreviousClose", 0), 2)
        }
    except:
        return CACHE.get(symbol, {"symbol": symbol, "ltp":"—","open":"—","high":"—",
                                  "low":"—","prev_close":"—","volume":"—","change":"—"})

# ------------------------
# Background thread to update cache
# ------------------------
def background_fetch():
    init_nse()
    while True:
        results = {}
        # Fetch indices
        indices = fetch_indices()
        results.update(indices)
        # Fetch stocks
        for name, symbol in SYMBOLS:
            if symbol not in ["NIFTY 50", "NIFTY BANK"]:
                results[symbol] = fetch_stock_yahoo(symbol)
                time.sleep(0.1)  # small delay
        # Update cache
        with CACHE_LOCK:
            CACHE.clear()
            CACHE.update(results)
        time.sleep(30)  # fetch every 30 seconds

threading.Thread(target=background_fetch, daemon=True).start()

# ------------------------
# Flask route
# ------------------------
@app.route("/")
def index():
    timestamp = datetime.now().strftime("%H:%M:%S")
    with CACHE_LOCK:
        results = CACHE.copy()
    html = f"""
    <html>
    <head>
        <title>NSE LIVE DASHBOARD</title>
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
        <h2>📈 NSE LIVE DASHBOARD by Sumit Gujrathi</h2>
        <p style='text-align:center;color:#ccc;'>Updated: {timestamp} (Auto-refresh 60s)</p>
        <table>
            <tr>
                <th>Symbol</th><th>LTP</th><th>Open</th><th>High</th><th>Low</th>
                <th>Prev Close</th><th>Volume</th><th>Change</th>
            </tr>
    """
    for symbol, row in results.items():
        cls = "green" if isinstance(row.get("change"), (int,float)) and row["change"] >= 0 else "red"
        html += f"""
            <tr>
                <td>{row.get("symbol","—")}</td>
                <td class='yellow'>{row.get("ltp","—")}</td>
                <td>{row.get("open","—")}</td>
                <td>{row.get("high","—")}</td>
                <td>{row.get("low","—")}</td>
                <td>{row.get("prev_close","—")}</td>
                <td>{row.get("volume","—")}</td>
                <td class='{cls}'>{row.get("change","—")}</td>
            </tr>
        """
    html += "</table></body></html>"
    return html

# ------------------------
# Run Flask
# ------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
        
