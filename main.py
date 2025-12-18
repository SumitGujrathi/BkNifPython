import os
import requests
import json
import pandas as pd
from flask import Flask, render_template_string, request, make_response
from datetime import datetime
import io
import csv

app = Flask(__name__)

class RealNSEFetcher:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.nseindia.com/option-chain"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_data(self, symbol="NIFTY"):
        try:
            # Step 1: Initialize cookies (Crucial for NSE)
            self.session.get("https://www.nseindia.com", timeout=10)
            
            # Step 2: Fetch real JSON
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return self.parse_nse_data(response.json(), symbol)
            else:
                return {"error": f"NSE Blocked Cloud IP (Status {response.status_code})", "is_real": False}
        except Exception as e:
            return {"error": str(e), "is_real": False}

    def parse_nse_data(self, data, symbol):
        records = data.get('records', {})
        expiry = records.get('expiryDates', [])[0]
        spot = records.get('underlyingValue', 0)
        
        raw_list = [obj for obj in data.get('filtered', {}).get('data', [])]
        formatted = []
        for item in raw_list:
            formatted.append({
                "strikePrice": item['strikePrice'],
                "calls": self.extract_side(item.get('CE', {})),
                "puts": self.extract_side(item.get('PE', {}))
            })
        
        return {
            "symbol": symbol,
            "spotPrice": spot,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "data": formatted,
            "is_real": True
        }

    def extract_side(self, side):
        return {
            "oi": side.get("openInterest", 0),
            "changeInOi": side.get("changeinOpenInterest", 0),
            "volume": side.get("totalTradedVolume", 0),
            "iv": side.get("impliedVolatility", 0),
            "ltp": side.get("lastPrice", 0),
            "change": side.get("change", 0)
        }

fetcher = RealNSEFetcher()

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetcher.get_data(symbol)
    
    # If blocked by NSE, show clear status
    if "error" in result:
        return f"<h2>Real Data Error: {result['error']}</h2><p>Cloud servers are often blocked by NSE. To get real data, use a Broker API (Dhan/Upstox).</p>"

    html = """
    <html>
    <head>
        <title>NSE Real-Time Chain</title>
        <style>
            body { font-family: sans-serif; font-size: 13px; background: #f8f9fa; }
            .header { background: #003366; color: white; padding: 15px; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
            th { background: #333; color: white; padding: 8px; border: 1px solid #ddd; }
            td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            .strike { background: #eee; font-weight: bold; }
            .call-side { background: #f0fff0; }
            .put-side { background: #fff5f5; }
        </style>
    </head>
    <body>
        <div class="header">
            <div><b>{{ data.symbol }}</b> | Spot: {{ data.spotPrice }}</div>
            <div>Time: {{ data.timestamp }} (REAL DATA)</div>
        </div>
        <form method="GET" style="padding:10px;">
            <select name="symbol" onchange="this.form.submit()">
                <option value="NIFTY" {% if data.symbol == 'NIFTY' %}selected{% endif %}>NIFTY</option>
                <option value="BANKNIFTY" {% if data.symbol == 'BANKNIFTY' %}selected{% endif %}>BANKNIFTY</option>
            </select>
        </form>
        <table>
            <thead>
                <tr>
                    <th colspan="6">CALLS</th>
                    <th>STRIKE</th>
                    <th colspan="6">PUTS</th>
                </tr>
                <tr>
                    <th>OI</th><th>Chng OI</th><th>Vol</th><th>IV</th><th>LTP</th><th>Chng</th>
                    <th>Price</th>
                    <th>LTP</th><th>Chng</th><th>IV</th><th>Vol</th><th>Chng OI</th><th>OI</th>
                </tr>
            </thead>
            <tbody>
                {% for row in data.data %}
                <tr>
                    <td class="call-side">{{ row.calls.oi }}</td>
                    <td class="call-side">{{ row.calls.changeInOi }}</td>
                    <td class="call-side">{{ row.calls.volume }}</td>
                    <td class="call-side">{{ row.calls.iv }}</td>
                    <td class="call-side"><b>{{ row.calls.ltp }}</b></td>
                    <td class="call-side">{{ row.calls.change }}</td>
                    
                    <td class="strike">{{ row.strikePrice }}</td>
                    
                    <td class="put-side"><b>{{ row.puts.ltp }}</b></td>
                    <td class="put-side">{{ row.puts.change }}</td>
                    <td class="put-side">{{ row.puts.iv }}</td>
                    <td class="put-side">{{ row.puts.volume }}</td>
                    <td class="put-side">{{ row.puts.changeInOi }}</td>
                    <td class="put-side">{{ row.puts.oi }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    return render_template_string(html, data=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

