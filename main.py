from flask import Flask
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)

# ------------------------
# Yahoo Finance symbols
# ------------------------
SYMBOLS = [
    ("NIFTY 50", "^NSEI"),
    ("NIFTY BANK", "^NSEBANK"),
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
# In-memory cache
# ------------------------
CACHE = {}
CACHE_LOCK = threading.Lock()

# ------------------------
# Fetch stock/index from Yahoo Finance
# ------------------------
def fetch_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        r = requests.get(url, timeout=10)
        data = r.json()
        result = data.get("quoteResponse", {}).get("result", [])
        if not result:
            return CACHE.get(symbol, {"symbol": symbol,"ltp":"—","open":"—","high":"—",
                                      "low":"—","prev_close":"—","volume":"—","change":"—"})
        quote = result[0]
        ltp = quote.get("regularMarketPrice") or 0
        prev_close = quote.get("regularMarketPreviousClose") or 0
        change = round(ltp - prev_close, 2) if ltp and prev_close else "—"
        return {
            "symbol": quote.get("shortName", symbol),
            "ltp": ltp or "—",
            "open": quote.get("regularMarketOpen") or "—",
            "high": quote.get("regularMarketDayHigh") or "—",
            "low": quote.get("regularMarketDayLow") or "—",
            "prev_close": prev_close or "—",
            "volume": quote.get("regularMarketVolume") or "—",
            "change": change
        }
    except:
        return CACHE.get(symbol, {"symbol": symbol,"ltp":"—","open":"—","high":"—",
                                  "low":"—","prev_close":"—","volume":"—","change":"—"})

# ------------------------
# Background thread to update cache
# ------------------------
def background_fetch():
    while True:
        results = {}
        for name, symbol in SYMBOLS:
            results[symbol] = fetch_yahoo(symbol)
            time.sleep(0.3)  # prevent throttling
        with CACHE_LOCK:
            CACHE.clear()
            CACHE.update(results)
        time.sleep(30)  # refresh every 30 seconds

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
        
