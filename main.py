import os
import requests
from flask import Flask, render_template_string, request, redirect
from datetime import datetime
import upstox_client
from upstox_client.rest import ApiException

app = Flask(__name__)

# --- YOUR UPSTOX CREDENTIALS ---
API_KEY = "48ad120b-126c-4cfe-899e-6699a85874e5"
API_SECRET = "4cnxn3sluq"
REDIRECT_URI = "https://127.0.0.1:5000/"  # Must match what you put in Upstox Dashboard

# Global variable to store today's token
# In a real app, you would save this to a file or database
ACCESS_TOKEN = None

# Index Mapping for Upstox
INDEX_KEYS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}

def get_upstox_data(symbol):
    if not ACCESS_TOKEN:
        return {"error": "No Access Token found. Please login first."}
    
    try:
        config = upstox_client.Configuration()
        config.access_token = ACCESS_TOKEN
        api_client = upstox_client.ApiClient(config)
        
        # 1. Fetch Option Chain
        # Note: 'target_expiry' usually needs to be the next Thursday's date
        # We are using a placeholder date; you should update this weekly
        target_expiry = "2025-12-24" 
        
        api_instance = upstox_client.OptionsApi(api_client)
        api_response = api_instance.get_put_call_option_chain(INDEX_KEYS[symbol], target_expiry)
        
        if api_response.status != 'success':
            return {"error": "Failed to fetch data from Upstox"}

        raw_data = api_response.data
        spot = raw_data[0].underlying_spot_price if raw_data else 0
        
        formatted = []
        for item in raw_data:
            ce = item.call_options.market_data if item.call_options else {}
            pe = item.put_options.market_data if item.put_options else {}
            
            formatted.append({
                "strike": item.strike_price,
                "ce": {"oi": ce.get('oi', 0), "ltp": ce.get('ltp', 0), "iv": round(ce.get('iv', 0)*100, 2)},
                "pe": {"oi": pe.get('oi', 0), "ltp": pe.get('ltp', 0), "iv": round(pe.get('iv', 0)*100, 2)}
            })
            
        return {"symbol": symbol, "spot": spot, "expiry": target_expiry, "data": formatted, "time": datetime.now().strftime("%H:%M:%S")}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    global ACCESS_TOKEN
    # Check if this is a redirect back from Upstox login (contains ?code=...)
    auth_code = request.args.get('code')
    if auth_code:
        # Exchange Code for Access Token
        url = "https://api.upstox.com/v2/login/authorization/token"
        headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'code': auth_code,
            'client_id': API_KEY,
            'client_secret': API_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        res = requests.post(url, headers=headers, data=data).json()
        ACCESS_TOKEN = res.get('access_token')
        return redirect('/')

    if not ACCESS_TOKEN:
        login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
        return f'<h3>Upstox Token Expired</h3><a href="{login_url}" style="padding:10px; background:blue; color:white; text-decoration:none; border-radius:5px;">Click here to Login & Refresh Token</a>'

    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = get_upstox_data(symbol)
    
    if "error" in result:
        return f"<p style='color:red'>Error: {result['error']}</p>"

    # HTML UI (Scannable Table)
    html = """
    <html>
    <head>
        <title>Upstox Option Chain</title>
        <meta http-equiv="refresh" content="60">
        <style>
            body { font-family: sans-serif; font-size: 13px; margin:0; }
            .header { background: #0037b4; color: white; padding: 15px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #eee; padding: 8px; border: 1px solid #ccc; }
            td { padding: 8px; border: 1px solid #eee; text-align: center; }
            .strike { background: #f9f9f9; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">Upstox Live: {{ res.symbol }} | Spot: {{ res.spot }} | {{ res.time }}</div>
        <table>
            <tr><th colspan="3">CALLS</th><th>STRIKE</th><th colspan="3">PUTS</th></tr>
            <tr><th>OI</th><th>IV</th><th>LTP</th><th>Price</th><th>LTP</th><th>IV</th><th>OI</th></tr>
            {% for r in res.data %}
            <tr>
                <td>{{ r.ce.oi }}</td><td>{{ r.ce.iv }}</td><td style="color:green"><b>{{ r.ce.ltp }}</b></td>
                <td class="strike">{{ r.strike }}</td>
                <td style="color:red"><b>{{ r.pe.ltp }}</b></td><td>{{ r.pe.iv }}</td><td>{{ r.pe.oi }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, res=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
