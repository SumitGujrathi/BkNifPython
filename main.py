import os
import requests
import json
import sys
import time
import random
import math
import logging
import io
import csv
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, jsonify, request, render_template_string, make_response
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class NSEOptionChainFetcher:
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/option-chain",
            "Connection": "keep-alive"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def initialize_session(self):
        try:
            self.session.get(self.base_url, timeout=10)
            return True
        except Exception as e:
            logger.error(f"Session init failed: {e}")
            return False

    def get_real_spot_price(self, symbol: str) -> float:
        ticker_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}
        try:
            ticker = ticker_map.get(symbol)
            data = yf.Ticker(ticker)
            price = data.fast_info.last_price
            if price: return round(float(price), 2)
        except Exception:
            pass
        return 24500.00 if symbol == "NIFTY" else 52000.00

    def generate_simulation(self, symbol: str, spot_price: float) -> Dict[str, Any]:
        step = 50 if symbol == "NIFTY" else 100
        center_strike = round(spot_price / step) * step
        strikes = []
        for i in range(-15, 16):
            strike = center_strike + (i * step)
            dist = abs(strike - spot_price)
            strikes.append({
                "strikePrice": strike,
                "calls": {
                    "oi": random.randint(10000, 50000), "changeInOi": random.randint(-5000, 5000),
                    "volume": random.randint(50000, 200000), "iv": 14.5, 
                    "ltp": round(max(0.05, (spot_price - strike) + 5 if strike < spot_price else 150 * math.exp(-0.005 * dist)), 2),
                    "change": round(random.uniform(-20, 20), 2)
                },
                "puts": {
                    "oi": random.randint(10000, 50000), "changeInOi": random.randint(-5000, 5000),
                    "volume": random.randint(50000, 200000), "iv": 15.2, 
                    "ltp": round(max(0.05, (strike - spot_price) + 5 if strike > spot_price else 150 * math.exp(-0.005 * dist)), 2),
                    "change": round(random.uniform(-20, 20), 2)
                }
            })
        return {
            "symbol": symbol, "spotPrice": spot_price, "timestamp": datetime.now().strftime("%H:%M:%S"),
            "data": strikes, "isSimulation": True
        }

    def format_side(self, side: Dict) -> Dict:
        # Ensures no 'None' values are passed to the frontend
        return {
            "oi": side.get("openInterest", 0) or 0,
            "changeInOi": side.get("changeinOpenInterest", 0) or 0,
            "volume": side.get("totalTradedVolume", 0) or 0,
            "iv": side.get("impliedVolatility", 0) or 0,
            "ltp": side.get("lastPrice", 0) or 0,
            "change": side.get("change", 0) or 0
        }

    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        try:
            if not self.session.cookies: self.initialize_session()
            url = f"{self.base_url}/api/option-chain-indices?symbol={symbol}"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                json_data = resp.json()
                records = json_data.get("records", {})
                spot_price = records.get("underlyingValue", 0)
                expiry = records.get("expiryDates", [""])[0]
                
                # Filter for current expiry and near ATM
                all_data = [o for o in records.get("data", []) if o.get("expiryDate") == expiry]
                
                # Sort by strike and pick 30 strikes around spot
                all_data.sort(key=lambda x: x["strikePrice"])
                closest_idx = min(range(len(all_data)), key=lambda i: abs(all_data[i]["strikePrice"] - spot_price))
                start = max(0, closest_idx - 15)
                end = min(len(all_data), closest_idx + 15)
                filtered = all_data[start:end]

                formatted = []
                for s in filtered:
                    formatted.append({
                        "strikePrice": s["strikePrice"],
                        "calls": self.format_side(s.get("CE", {})),
                        "puts": self.format_side(s.get("PE", {}))
                    })
                
                return {
                    "symbol": symbol, "spotPrice": spot_price, "data": formatted, 
                    "isSimulation": False, "timestamp": datetime.now().strftime("%H:%M:%S")
                }
        except Exception as e:
            logger.error(f"Fetch Error: {e}")
        
        return self.generate_simulation(symbol, self.get_real_spot_price(symbol))

fetcher = NSEOptionChainFetcher()

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetcher.get_option_chain(symbol)
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Option Chain</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body { font-family: 'Segoe UI', Arial; font-size: 12px; margin: 0; background: #f0f2f5; }
            .navbar { background: #1e3a8a; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
            .container { padding: 20px; }
            table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            th { background: #334155; color: white; padding: 10px; border: 1px solid #475569; }
            td { padding: 8px; border: 1px solid #e2e8f0; text-align: center; }
            .strike { background: #f8fafc; font-weight: bold; color: #1e293b; font-size: 14px; }
            .ce-side { background: #f0fdf4; }
            .pe-side { background: #fffaf0; }
            .pos { color: #16a34a; font-weight: bold; }
            .neg { color: #dc2626; font-weight: bold; }
            .btn { background: #16a34a; color: white; text-decoration: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
            .tag { font-size: 10px; padding: 2px 6px; border-radius: 10px; background: #eab308; color: black; margin-left: 10px; }
        </style>
    </head>
    <body>
        <div class="navbar">
            <div>
                <b style="font-size: 18px;">{{ data.symbol }}</b> 
                <span>Spot: {{ data.spotPrice }}</span>
                {% if data.isSimulation %}<span class="tag">SIMULATION MODE</span>{% endif %}
            </div>
            <div>
                <small>Last Updated: {{ data.timestamp }}</small> &nbsp;
                <a href="/download?symbol={{ data.symbol }}" class="btn">Download CSV</a>
            </div>
        </div>
        <div class="container">
            <form method="GET" style="margin-bottom: 15px;">
                <select name="symbol" onchange="this.form.submit()" style="padding: 5px;">
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
                        <td class="ce-side">{{ row.calls.oi }}</td>
                        <td class="ce-side {{ 'pos' if row.calls.changeInOi > 0 else 'neg' }}">{{ row.calls.changeInOi }}</td>
                        <td class="ce-side">{{ row.calls.volume }}</td>
                        <td class="ce-side">{{ row.calls.iv }}</td>
                        <td class="ce-side" style="font-weight:bold;">{{ row.calls.ltp }}</td>
                        <td class="ce-side {{ 'pos' if row.calls.change > 0 else 'neg' }}">{{ row.calls.change }}</td>
                        
                        <td class="strike">{{ row.strikePrice }}</td>
                        
                        <td class="pe-side" style="font-weight:bold;">{{ row.puts.ltp }}</td>
                        <td class="pe-side {{ 'pos' if row.puts.change > 0 else 'neg' }}">{{ row.puts.change }}</td>
                        <td class="pe-side">{{ row.puts.iv }}</td>
                        <td class="pe-side">{{ row.puts.volume }}</td>
                        <td class="pe-side {{ 'pos' if row.puts.changeInOi > 0 else 'neg' }}">{{ row.puts.changeInOi }}</td>
                        <td class="pe-side">{{ row.puts.oi }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, data=result)

@app.route('/download')
def download_csv():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetcher.get_option_chain(symbol)
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Strike", "C-OI", "C-ChngOI", "C-Vol", "C-IV", "C-LTP", "P-LTP", "P-IV", "P-Vol", "P-ChngOI", "P-OI"])
    for r in result['data']:
        cw.writerow([r['strikePrice'], r['calls']['oi'], r['calls']['changeInOi'], r['calls']['volume'], r['calls']['iv'], r['calls']['ltp'], r['puts']['ltp'], r['puts']['iv'], r['puts']['volume'], r['puts']['changeInOi'], r['puts']['oi']])
    
    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={symbol}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
