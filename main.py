import os
import requests
import json
import sys
import time
import random
import math
import logging
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, jsonify, request, render_template_string
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
        
        for i in range(-10, 11): # Simplified to 10 strikes for web view
            strike = center_strike + (i * step)
            distance = abs(strike - spot_price)
            ce_itm = strike < spot_price
            ce_ltp = max(0.05, (spot_price - strike) + 5) if ce_itm else max(0.05, 100 * math.exp(-0.005 * distance))
            pe_itm = strike > spot_price
            pe_ltp = max(0.05, (strike - spot_price) + 5) if pe_itm else max(0.05, 100 * math.exp(-0.005 * distance))
            
            strikes.append({
                "strikePrice": strike,
                "expiryDate": expiry,
                "calls": {"oi": random.randint(1000, 50000), "iv": 15.2, "ltp": round(ce_ltp, 2), "change": 1.2},
                "puts": {"oi": random.randint(1000, 50000), "iv": 14.8, "ltp": round(pe_ltp, 2), "change": -0.5}
            })
            
        return {
            "symbol": symbol, "spotPrice": spot_price, "timestamp": datetime.now().isoformat(),
            "data": strikes, "isSimulation": True, "message": "Render IP restricted. Showing live-spot simulation."
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
        
        # Simple extraction of first 20 records for current expiry
        current_expiry = records.get("expiryDates", [""])[0]
        strikes = [o for o in option_data if o.get("expiryDate") == current_expiry]
        
        formatted_data = []
        for s in strikes[:40]: # Top 40 strikes
            formatted_data.append({
                "strikePrice": s["strikePrice"],
                "calls": self.format_side(s.get("CE", {})),
                "puts": self.format_side(s.get("PE", {}))
            })
        
        return {"symbol": symbol, "spotPrice": spot_price, "data": formatted_data, "isSimulation": False}

    def format_side(self, side: Dict) -> Dict:
        return {"oi": side.get("openInterest", 0), "ltp": side.get("lastPrice", 0), "iv": side.get("impliedVolatility", 0)}

fetcher = NSEOptionChainFetcher()

# --- WEB ROUTES ---

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetcher.get_option_chain(symbol)
    
    # Simple HTML Template to show the data
    html = """
    <html>
        <head><title>NSE Option Chain</title><style>
            body { font-family: sans-serif; margin: 20px; background: #f4f4f9; }
            table { border-collapse: collapse; width: 100%; background: white; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #04AA6D; color: white; }
            .atm { background-color: #ffffcc; }
        </style></head>
        <body>
            <h1>{{ data.symbol }} Option Chain</h1>
            <p>Spot Price: <b>{{ data.spotPrice }}</b> | Time: {{ data.timestamp }}</p>
            <p style="color: red;">{{ data.message if data.isSimulation else "Live NSE Data" }}</p>
            <form method="GET">
                <select name="symbol" onchange="this.form.submit()">
                    <option value="NIFTY" {% if data.symbol == 'NIFTY' %}selected{% endif %}>NIFTY</option>
                    <option value="BANKNIFTY" {% if data.symbol == 'BANKNIFTY' %}selected{% endif %}>BANKNIFTY</option>
                </select>
            </form>
            <table>
                <tr><th>Call OI</th><th>Call LTP</th><th>Strike</th><th>Put LTP</th><th>Put OI</th></tr>
                {% for row in data.data %}
                <tr>
                    <td>{{ row.calls.oi }}</td><td>{{ row.calls.ltp }}</td>
                    <td class="atm"><b>{{ row.strikePrice }}</b></td>
                    <td>{{ row.puts.ltp }}</td><td>{{ row.puts.oi }}</td>
                </tr>
                {% endfor %}
            </table>
        </body>
    </html>
    """
    return render_template_string(html, data=result)

@app.route('/api')
def api_data():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    return jsonify(fetcher.get_option_chain(symbol))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
