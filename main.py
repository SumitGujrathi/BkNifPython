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
            self.session.get(self.base_url, timeout=5)
            return True
        except Exception:
            return False

    def get_real_spot_price(self, symbol: str) -> float:
        ticker_map = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}
        try:
            ticker = ticker_map.get(symbol)
            if not ticker: return 0.0
            data = yf.Ticker(ticker)
            price = data.fast_info.last_price
            if price: return price
            hist = data.history(period="1d")
            if not hist.empty: return hist['Close'].iloc[-1]
        except Exception:
            pass
        return 25815.55 if symbol == "NIFTY" else 53500.00

    def generate_simulation(self, symbol: str, spot_price: float) -> Dict[str, Any]:
        step = 50 if symbol == "NIFTY" else 100
        center_strike = round(spot_price / step) * step
        strikes = []
        expiry = datetime.now().strftime("%d-%b-%Y").upper()
        
        for i in range(-15, 16):
            strike = center_strike + (i * step)
            distance = abs(strike - spot_price)
            # Simulated data for fields
            strikes.append({
                "strikePrice": strike,
                "expiryDate": expiry,
                "calls": {
                    "oi": random.randint(5000, 100000), "changeInOi": random.randint(-1000, 5000),
                    "volume": random.randint(10000, 500000), "iv": round(12 + random.random()*5, 2),
                    "ltp": round(max(0.05, (spot_price - strike) + 10 if strike < spot_price else 100 * math.exp(-0.005 * distance)), 2),
                    "change": round(random.uniform(-50, 50), 2)
                },
                "puts": {
                    "oi": random.randint(5000, 100000), "changeInOi": random.randint(-1000, 5000),
                    "volume": random.randint(10000, 500000), "iv": round(12 + random.random()*5, 2),
                    "ltp": round(max(0.05, (strike - spot_price) + 10 if strike > spot_price else 100 * math.exp(-0.005 * distance)), 2),
                    "change": round(random.uniform(-50, 50), 2)
                }
            })
        return {
            "symbol": symbol, "spotPrice": spot_price, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": strikes, "isSimulation": True, "message": "Showing live-spot simulation (NSE Blocked)."
        }

    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        try:
            if not self.session.cookies: self.initialize_session()
            api_url = f"{self.base_url}/api/option-chain-indices"
            response = self.session.get(api_url, params={"symbol": symbol}, timeout=5)
            if response.status_code == 200:
                return self.parse_option_data(response.json(), symbol)
        except Exception:
            pass
        return self.generate_simulation(symbol, self.get_real_spot_price(symbol))

    def parse_option_data(self, data: Dict, symbol: str) -> Dict[str, Any]:
        records = data.get("records", {})
        spot_price = records.get("underlyingValue", 0)
        option_data = records.get("data", [])
        current_expiry = records.get("expiryDates", [""])[0]
        strikes = [o for o in option_data if o.get("expiryDate") == current_expiry]
        
        formatted_data = []
        for s in strikes:
            formatted_data.append({
                "strikePrice": s["strikePrice"],
                "calls": self.format_side(s.get("CE", {})),
                "puts": self.format_side(s.get("PE", {}))
            })
        
        return {
            "symbol": symbol, "spotPrice": spot_price, "data": formatted_data, 
            "isSimulation": False, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def format_side(self, side: Dict) -> Dict:
        return {
            "oi": side.get("openInterest", 0),
            "changeInOi": side.get("changeinOpenInterest", 0),
            "volume": side.get("totalTradedVolume", 0),
            "iv": side.get("impliedVolatility", 0),
            "ltp": side.get("lastPrice", 0),
            "change": side.get("change", 0)
        }

fetcher = NSEOptionChainFetcher()

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetcher.get_option_chain(symbol)
    
    html = """
    <html>
        <head>
            <title>NSE Option Chain</title>
            <meta http-equiv="refresh" content="60">
            <style>
                body { font-family: Arial, sans-serif; font-size: 12px; margin: 10px; background: #f4f4f4; }
                .card { background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                table { border-collapse: collapse; width: 100%; background: white; }
                th, td { border: 1px solid #ccc; padding: 6px; text-align: center; }
                th { background: #2c3e50; color: white; font-size: 11px; }
                .strike-cell { background: #ecf0f1; font-weight: bold; width: 80px; }
                .call-bg { background: #e8f8f5; }
                .put-bg { background: #fef9e7; }
                .pos { color: green; } .neg { color: red; }
                .header-flex { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
                .btn { padding: 6px 12px; text-decoration: none; border-radius: 3px; font-weight: bold; color: white; border: none; font-size: 12px; }
                .btn-csv { background: #27ae60; }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header-flex">
                    <div>
                        <h2 style="margin:0">{{ data.symbol }} Chain</h2>
                        <span>Spot: <b>{{ data.spotPrice }}</b> | Updated: {{ data.timestamp }}</span>
                    </div>
                    <div>
                        <a href="/download?symbol={{ data.symbol }}" class="btn btn-csv">Download CSV</a>
                    </div>
                </div>

                <form method="GET">
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
                            <td class="call-bg">{{ "{:,}".format(row.calls.oi) }}</td>
                            <td class="call-bg {{ 'pos' if row.calls.changeInOi > 0 else 'neg' }}">{{ row.calls.changeInOi }}</td>
                            <td class="call-bg">{{ "{:,}".format(row.calls.volume) }}</td>
                            <td class="call-bg">{{ row.calls.iv }}</td>
                            <td class="call-bg"><b>{{ row.calls.ltp }}</b></td>
                            <td class="call-bg {{ 'pos' if row.calls.change > 0 else 'neg' }}">{{ row.calls.change }}</td>
                            
                            <td class="strike-cell">{{ row.strikePrice }}</td>
                            
                            <td class="put-bg"><b>{{ row.puts.ltp }}</b></td>
                            <td class="put-bg {{ 'pos' if row.puts.change > 0 else 'neg' }}">{{ row.puts.change }}</td>
                            <td class="put-bg">{{ row.puts.iv }}</td>
                            <td class="put-bg">{{ "{:,}".format(row.puts.volume) }}</td>
                            <td class="put-bg {{ 'pos' if row.puts.changeInOi > 0 else 'neg' }}">{{ row.puts.changeInOi }}</td>
                            <td class="put-bg">{{ "{:,}".format(row.puts.oi) }}</td>
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
    cw.writerow(["Symbol", result['symbol'], "Spot", result['spotPrice'], "Time", result['timestamp']])
    cw.writerow(["Strike", "C-OI", "C-ChngOI", "C-Vol", "C-IV", "C-LTP", "P-LTP", "P-IV", "P-Vol", "P-ChngOI", "P-OI"])
    for r in result['data']:
        cw.writerow([r['strikePrice'], r['calls']['oi'], r['calls']['changeInOi'], r['calls']['volume'], r['calls']['iv'], r['calls']['ltp'], r['puts']['ltp'], r['puts']['iv'], r['puts']['volume'], r['puts']['changeInOi'], r['puts']['oi']])
    
    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={symbol}_full_chain.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
