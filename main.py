import os
import io
import csv
from datetime import datetime
from flask import Flask, render_template_string, request, make_response
from dhanhq import dhanhq

app = Flask(__name__)

# --- YOUR PERSONAL DHAN CREDENTIALS ---
CLIENT_ID = "1109528371"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY2MTU3Mjk5LCJpYXQiOjE3NjYwNzA4OTksInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5NTI4MzcxIn0.ffxq74gMdPMpuARwjZcOhJ6B7bCewr1SnuuPUyM-uaXqYXEaQiPCkynWv4SZMXzoLLqPmvSgyJb4a4JVGVTlVQ"

# Initialize Dhan Client
dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# Instrument IDs for Dhan (Nifty = 13, Bank Nifty = 25)
INDEX_MAP = {
    "NIFTY": {"id": 13, "segment": "IDX_I"},
    "BANKNIFTY": {"id": 25, "segment": "IDX_I"}
}

def get_dhan_data(symbol):
    try:
        idx = INDEX_MAP.get(symbol)
        
        # 1. Fetch nearest Expiry
        expiry_response = dhan.expiry_list(idx["id"], idx["segment"])
        if expiry_response.get('status') != 'success':
            return {"error": "Could not fetch expiry dates from Dhan."}
        
        latest_expiry = expiry_response['data'][0]
        
        # 2. Fetch Option Chain
        oc_response = dhan.option_chain(idx["id"], idx["segment"], latest_expiry)
        if oc_response.get('status') != 'success':
            return {"error": "Option Chain fetch failed."}

        data = oc_response['data']
        spot = data.get('last_price', 0)
        raw_oc = data.get('oc', {})

        formatted = []
        for strike, values in raw_oc.items():
            ce = values.get('ce', {})
            pe = values.get('pe', {})
            
            formatted.append({
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

        formatted.sort(key=lambda x: x['strikePrice'])
        return {"symbol": symbol, "spot": spot, "expiry": latest_expiry, "data": formatted, "time": datetime.now().strftime("%H:%M:%S")}

    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = get_dhan_data(symbol)
    
    if "error" in result:
        return f"<div style='color:red; padding:20px;'><h3>API Error</h3>{result['error']}</div>"

    html = """
    <html>
    <head>
        <title>Dhan Live Chain</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body { font-family: sans-serif; font-size: 12px; margin: 0; background: #f4f4f4; }
            .header { background: #121212; color: #00d09c; padding: 15px; display: flex; justify-content: space-between; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th { background: #262626; color: white; padding: 8px; border: 1px solid #444; }
            td { padding: 8px; border: 1px solid #eee; text-align: center; }
            .strike { background: #f9f9f9; font-weight: bold; }
            .ce { background: #f0fff4; } .pe { background: #fff5f5; }
            .pos { color: green; } .neg { color: red; }
        </style>
    </head>
    <body>
        <div class="header">
            <b>{{ res.symbol }} Chain</b>
            <span>Spot: {{ res.spot }} | Expiry: {{ res.expiry }} | Last Sync: {{ res.time }}</span>
        </div>
        <form method="GET" style="padding:10px;">
            <select name="symbol" onchange="this.form.submit()">
                <option value="NIFTY" {% if res.symbol == 'NIFTY' %}selected{% endif %}>NIFTY</option>
                <option value="BANKNIFTY" {% if res.symbol == 'BANKNIFTY' %}selected{% endif %}>BANKNIFTY</option>
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
                {% for r in res.data %}
                <tr>
                    <td class="ce">{{ r.calls.oi }}</td>
                    <td class="ce {{ 'pos' if r.calls.changeInOi > 0 else 'neg' }}">{{ r.calls.changeInOi }}</td>
                    <td class="ce">{{ r.calls.volume }}</td>
                    <td class="ce">{{ r.calls.iv }}</td>
                    <td class="ce"><b>{{ r.calls.ltp }}</b></td>
                    <td class="ce {{ 'pos' if r.calls.change > 0 else 'neg' }}">{{ r.calls.change }}</td>
                    <td class="strike">{{ r.strikePrice }}</td>
                    <td class="pe"><b>{{ r.puts.ltp }}</b></td>
                    <td class="pe {{ 'pos' if r.puts.change > 0 else 'neg' }}">{{ r.puts.change }}</td>
                    <td class="pe">{{ r.puts.iv }}</td>
                    <td class="pe">{{ r.puts.volume }}</td>
                    <td class="pe {{ 'pos' if r.puts.changeInOi > 0 else 'neg' }}">{{ r.puts.changeInOi }}</td>
                    <td class="pe">{{ r.puts.oi }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    return render_template_string(html, res=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
