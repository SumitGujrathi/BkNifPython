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
# Initialize NSE session (fetch cookies)
# ------------------------
def init_nse():
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    except:
        pass

# ------------------------
# Fetch stock or index data
# ------------------------
def fetch_stock(symbol):
    """Fetch stock or index data from NSE API."""
    try:
        # Indices
        if symbol in ["NIFTY 50", "NIFTY BANK"]:
            url = f"https://www.nseindia.com/api/equity-stockIndices?index={symbol.replace(' ', '%20')}"
            r = session.get(url, headers=HEADERS, timeout=10)
            data = r.json()
            idx = data["data"][0]
            return {
                "symbol": symbol,
                "ltp": idx.get("last", "—"),
                "open": idx.get("open", "—"),
                "high": idx.get("high", "—"),
                "low": idx.get("low", "—"),
                "prev_close": idx.get("previousClose", "—"),
                "volume": idx.get("tradedVolume", "—"),
                "change": idx.get("variation", "—"),
            }

        # Stocks
        else:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            r = session.get(url, headers=HEADERS, timeout=10)
            data = r.json()
            p = data["priceInfo"]
            return {
                "symbol": symbol,
                "ltp": p.get("lastPrice", "—"),
                "open": p.get("open", "—"),
                "high": p.get("intraDayHighLow", {}).get("max", "—"),
                "low": p.get("intraDayHighLow", {}).get("min", "—"),
                "prev_close": p.get("previousClose", "—"),
                "volume": data.get("securityInfo", {}).get("totalTradedVolume", "—"),
                "change": p.get("change", "—"),
            }

    except:
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

# ------------------------
# Flask route for webpage
# ------------------------
@app.route("/")
def index():
    init_nse()  # initialize cookies

    results = []

    # Fetch all data first
    for name, symbol in SYMBOLS:
        stock_data = fetch_stock(symbol)
        results.append(stock_data)
        time.sleep(0.2)  # small delay to prevent NSE throttling

    timestamp = datetime.now().strftime("%H:%M:%S")

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

    for row in results:
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
            
