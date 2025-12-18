import os
from flask import Flask, render_template_string, request, make_response
from dhanhq import dhanhq
import pandas as pd
import io
import csv
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
# Replace these with your actual Dhan credentials or set them in Render Environment Variables
CLIENT_ID = os.environ.get("DHAN_CLIENT_ID", "1109528371")
ACCESS_TOKEN = os.environ.get("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY2MTU3Mjk5LCJpYXQiOjE3NjYwNzA4OTksInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5NTI4MzcxIn0.ffxq74gMdPMpuARwjZcOhJ6B7bCewr1SnuuPUyM-uaXqYXEaQiPCkynWv4SZMXzoLLqPmvSgyJb4a4JVGVTlVQ")

# Initialize Dhan Client
dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# Mapping for Index Security IDs in Dhan (NSE Indices)
INDEX_MAP = {
    "NIFTY": {"id": "13", "segment": "IDX_I"},
    "BANKNIFTY": {"id": "25", "segment": "IDX_I"}
}

def fetch_dhan_option_chain(symbol):
    try:
        idx_info = INDEX_MAP.get(symbol)
        
        # 1. Get Expiry List
        expiry_data = dhan.expiry_list(
            under_security_id=idx_info["id"],
            under_exchange_segment=idx_info["segment"]
        )
        
        if expiry_data.get('status') != 'success':
            return {"error": "Failed to fetch expiry dates"}
            
        latest_expiry = expiry_data['data'][0] # Pick the nearest expiry
        
        # 2. Get Full Option Chain
        oc_data = dhan.option_chain(
            under_security_id=idx_info["id"],
            under_exchange_segment=idx_info["segment"],
            expiry=latest_expiry
        )
        
        if oc_data.get('status') != 'success':
            return {"error": "Failed to fetch Option Chain data"}

        # 3. Parse and Format Data
        raw_oc = oc_data['data']['oc']
        spot_price = oc_data['data'].get('last_price', 0)
        
        formatted_list = []
        # Dhan returns data as a dictionary where keys are strike prices
        for strike, data in raw_oc.items():
            ce = data.get('ce', {})
            pe = data.get('pe', {})
            
            formatted_list.append({
                "strikePrice": float(strike),
                "calls": {
                    "oi": ce.get("oi", 0),
                    "changeInOi": ce.get("oi", 0) - ce.get("previous_oi", 0),
                    "volume": ce.get("volume", 0),
                    "iv": round(ce.get("implied_volatility", 0), 2),
                    "ltp": ce.get("last_price", 0),
                    "change": round(ce.get("last_price", 0) - ce.get("previous_close_price", 0), 2)
                },
                "puts": {
                    "oi": pe.get("oi", 0),
                    "changeInOi": pe.get("oi", 0) - pe.get("previous_oi", 0),
                    "volume": pe.get("volume", 0),
                    "iv": round(pe.get("implied_volatility", 0), 2),
                    "ltp": pe.get("last_price", 0),
                    "change": round(pe.get("last_price", 0) - pe.get("previous_close_price", 0), 2)
                }
            })
            
        # Sort by strike price
        formatted_list.sort(key=lambda x: x['strikePrice'])
        
        return {
            "symbol": symbol,
            "spotPrice": spot_price,
            "expiry": latest_expiry,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "data": formatted_list
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetch_dhan_option_chain(symbol)
    
    if "error" in result:
        return f"<h3>Error: {result['error']}</h3><p>Ensure your Client ID and Access Token are correct.</p>"

    html = """
    <html>
    <head>
        <title>Dhan Real-Time Option Chain</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body { font-family: Arial; font-size: 12px; margin: 0; background: #f4f7f6; }
            .nav { background: #121212; color: #00d09c; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
            .container { padding: 20px; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
            th { background: #262626; color: white; padding: 10px; border: 1px solid #333; }
            td { padding: 8px; border: 1px solid #eee; text-align: center; }
            .strike { background: #f9f9f9; font-weight: bold; font-size: 13px; color: #333; }
            .ce-side { background: #f0fff4; }
            .pe-side { background: #fff5f5; }
            .pos { color: #008a00; } .neg { color: #d60000; }
            .btn-csv { background: #00d09c; color: #121212; padding: 8px 15px; border-radius: 4px; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="nav">
            <div>
                <span style="font-size: 18px; font-weight: bold;">{{ data.symbol }}</span> 
                <span style="margin-left: 10px;">Spot: {{ data.spotPrice }}</span>
                <span style="margin-left: 10px; color: #888;">Expiry: {{ data.expiry }}</span>
            </div>
            <div>
                <span>Updated: {{ data.timestamp }}</span> &nbsp;
                <a href="/download?symbol={{ data.symbol }}" class="btn-csv">Download CSV</a>
            </div>
        </div>
        <div class="container">
            <form method="GET" style="margin-bottom: 20px;">
                <select name="symbol" onchange="this.form.submit()" style="padding: 8px; border-radius: 4px;">
                    <option value="NIFTY" {% if data.symbol == 'NIFTY' %}selected{% endif %}>NIFTY</option>
                    <option value="BANKNIFTY" {% if data.symbol == 'BANKNIFTY' %}selected{% endif %}>BANKNIFTY</option>
                </select>
            </form>
            <table>
                <thead>
                    <tr><th colspan="6">CALLS</th><th>STRIKE</th><th colspan="6">PUTS</th></tr>
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
def download():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = fetch_dhan_option_chain(symbol)
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Strike", "C-OI", "C-ChngOI", "C-Vol", "C-IV", "C-LTP", "P-LTP", "P-IV", "P-Vol", "P-ChngOI", "P-OI"])
    for r in result['data']:
        cw.writerow([r['strikePrice'], r['calls']['oi'], r['calls']['changeInOi'], r['calls']['volume'], r['calls']['iv'], r['calls']['ltp'], r['puts']['ltp'], r['puts']['iv'], r['puts']['volume'], r['puts']['changeInOi'], r['puts']['oi']])
    
    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={symbol}_dhan.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
