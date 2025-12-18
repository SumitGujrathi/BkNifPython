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
        except Exception as e:
            logger.error(f"Error fetching spot price: {e}")
        return 25815.55 if symbol == "NIFTY" else 53500.00

    def generate_simulation(self, symbol: str, spot_price: float) -> Dict[str, Any]:
        step = 50 if symbol == "NIFTY" else 100
        center_strike = round(spot_price / step) * step
        strikes = []
        expiry = datetime.now().strftime("%d-%b-%Y").upper()
        for i in range(-15, 16):
            strike = center_strike + (i * step)
            distance = abs(strike - spot_price)
            ce_itm = strike < spot_price
            ce_ltp = max(0.05, (spot_price - strike) + 5) if ce_itm else max(0.05, 100 * math.exp(-0.005 * distance))
            pe_itm = strike > spot_price
            pe_ltp = max(0.05, (strike - spot_price) + 5) if pe_itm else max(0.05, 100 * math.exp(-0.005 * distance))
            strikes.append({
                "strikePrice": strike,
                "expiryDate": expiry,
                "calls": {"oi": random.randint(1000, 50000), "iv": 15.2, "ltp": round(ce_ltp + random.uniform(-1,1), 2)},
                "puts": {"oi": random.randint(1000, 50000), "iv": 14.8, "ltp": round(pe_ltp + random.uniform(-1,1), 2)}
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
        except Exception as e:
            logger.warning(f"NSE Fetch Failed: {e}")
        return self.generate_simulation(symbol, self.get_real_spot_price(symbol))

    def parse_option_data(self, data: Dict, symbol: str) -> Dict[str, Any]:
        records = data.get("records", {})
        spot_price = records.get("underlyingValue", 0)
        option_data = records.get("data", [])
        if not option_data: return self.generate_simulation(symbol, self.get_real_spot_price(symbol))
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
        return {"oi": side.get("openInterest", 0), "ltp": side.get("lastPrice", 0), "iv": side.get("impliedVolatility", 0)}

fetcher = NSEOptionChainFetcher()

# --- WEB ROUTES ---

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetcher.get_option_chain(symbol)
    
    html = """
    <html>
        <head>
            <title>NSE Option Chain - Live</title>
            <meta http-equiv="refresh" content="60">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background: #f0f2f5; color: #333; }
                .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }
                table { border-collapse: collapse; width: 100%; margin-top: 10px; }
                th, td { border: 1px solid #e0e0e0; padding: 12px; text-align: center; }
                th { background-color: #007bff; color: white; font-weight: 600; }
                tr:nth-child(even) { background-color: #fafafa; }
                .atm { background-color: #fff9c4; font-weight: bold; }
                .btn { padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; cursor: pointer; border: none; }
                .btn-download { background-color: #28a745; color: white; margin-right: 10px; }
                .btn-refresh { background-color: #6c757d; color: white; }
                .status { font-size: 0.9em; color: #666; margin-top: 5px; }
                .simulation-tag { background: #ffebee; color: #c62828; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div>
                        <h1 style="margin:0;">{{ data.symbol }} Option Chain</h1>
                        <div class="status">
                            Spot: <b>{{ data.spotPrice }}</b> | Last Update: {{ data.timestamp }}
                            {% if data.isSimulation %} <span class="simulation-tag">SIMULATION</span> {% endif %}
                        </div>
                    </div>
                    <div>
                        <a href="/download?symbol={{ data.symbol }}" class="btn btn-download">Download .CSV</a>
                        <a href="/?symbol={{ data.symbol }}" class="btn btn-refresh">Refresh Now</a>
                    </div>
                </div>

                <form method="GET" style="margin-bottom: 20px;">
                    <label>Select Index: </label>
                    <select name="symbol" onchange="this.form.submit()" style="padding: 5px; border-radius: 4px;">
                        <option value="NIFTY" {% if data.symbol == 'NIFTY' %}selected{% endif %}>NIFTY</option>
                        <option value="BANKNIFTY" {% if data.symbol == 'BANKNIFTY' %}selected{% endif %}>BANKNIFTY</option>
                    </select>
                </form>

                <table>
                    <thead>
                        <tr>
                            <th colspan="2">CALLS</th>
                            <th>STRIKE</th>
                            <th colspan="2">PUTS</th>
                        </tr>
                        <tr>
                            <th>OI</th><th>LTP</th>
                            <th>Price</th>
                            <th>LTP</th><th>OI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in data.data %}
                        <tr>
                            <td>{{ "{:,}".format(row.calls.oi) }}</td>
                            <td style="color: #2e7d32;">{{ row.calls.ltp }}</td>
                            <td class="atm">{{ row.strikePrice }}</td>
                            <td style="color: #c62828;">{{ row.puts.ltp }}</td>
                            <td>{{ "{:,}".format(row.puts.oi) }}</td>
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
    
    # Create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Headers
    cw.writerow(["Symbol", result['symbol'], "Spot Price", result['spotPrice'], "Time", result['timestamp']])
    cw.writerow([])
    cw.writerow(["Strike Price", "Call OI", "Call LTP", "Put OI", "Put LTP"])
    
    # Data rows
    for row in result['data']:
        cw.writerow([
            row['strikePrice'], 
            row['calls']['oi'], 
            row['calls']['ltp'], 
            row['puts']['oi'], 
            row['puts']['ltp']
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={symbol}_option_chain.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
