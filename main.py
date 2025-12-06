from flask import Flask
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)

# ------------------------
# NSE symbols
# ------------------------
SYMBOLS = [
    "ACC","ADANIPORTS","SBIN","AMBUJACEM","WIPRO","APOLLOTYRE","ASIANPAINT",
    "AUROPHARMA","AXISBANK","BAJFINANCE","IOC","BANKBARODA","BATAINDIA",
    "BERGEPAINT","BHARATFORG","COALINDIA","INDUSINDBK","DRREDDY","INFY",
    "JSWSTEEL","POWERGRID","LICHSGFIN","CANBK","MGL","M&MFIN","HDFCBANK",
    "MANAPPURAM","MARICO","SUNTV","HINDZINC","ICICIBANK","ZEEL"
]

# Indices
INDICES = ["NIFTY 50", "NIFTY BANK"]

# ------------------------
# NSE session for cookies
# ------------------------
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://www.nseindia.com",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

# ------------------------
# Cache to store latest data
# ------------------------
CACHE = {}
CACHE_LOCK = threading.Lock()

# ------------------------
# Initialize NSE session
# ------------------------
def init_nse():
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    except:
        pass

# ------------------------
# Fetch NIFTY indices
# ------------------------
def fetch_indices():
    try:
        url = "https://www.nseindia.com/api/allIndices"
        r = session.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        indices_data = {}
        for idx in data["data"]:
            if idx["index"] in INDICES:
                indices_data[idx["index"]] = {
                    "symbol": idx["index"],
                    "ltp": idx.get("last", "—"),
                    "open": idx.get("open", "—"),
                    "high": idx.get("high", "—"),
                    "low": idx.get("low", "—"),
                    "prev_close": idx.get("previousClose", "—"),
                    "volume": idx.get("tradedVolume", "—"),
                    "change": idx.get("variation", "—")
                }
        return indices_data
    except:
        # fallback to cache
        return {idx: CACHE.get(idx, {}) for idx in INDICES}

# ------------------------
# Fetch individual stock
# ------------------------
def fetch_stock(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        r = session.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        price = data.get("priceInfo", {})
        sec = data.get("securityInfo", {})
        ltp = price.get("lastPrice") or "—"
        prev_close = price.get("previousClose") or "—"
        change = round(float(ltp)-float(prev_close),2) if ltp != "—" and prev_close != "—" else "—"
        return {
            "symbol": symbol,
            "ltp": ltp,
            "open": price.get("open","—"),
            "high": price.get("intraDayHighLow",{}).get("max","—"),
            "low": price.get("intraDayHighLow",{}).get("min","—"),
            "prev_close": prev_close,
            "volume": sec.get("totalTradedVolume","—"),
            "change": change
        }
    except:
        return CACHE.get(symbol, {"symbol": symbol,"ltp":"—","open":"—","high":"—",
                                  "low":"—","prev_close":"—","volume":"—","change":"—"})

# ------------------------
# Background fetch thread
# ------------------------
def background_fetch():
    init_nse()
    while True:
        results = {}
        # Fetch indices
        indices_data = fetch_indices()
        results.update(indices_data)
        # Fetch stocks
        for sym in SYMBOLS:
            results[sym] = fetch_stock(sym)
            time.sleep(0.3)  # prevent throttling
        # Update cache
        with CACHE_LOCK:
            CACHE.clear()
            CACHE.update(results)
        time.sleep(30)  # refresh every 30 sec

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
