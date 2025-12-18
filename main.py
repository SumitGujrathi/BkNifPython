import os
from datetime import datetime
from flask import Flask, render_template_string, request
from dhanhq import dhanhq

app = Flask(__name__)

# --- CREDENTIALS ---
CLIENT_ID = "1109528371"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY2MTU3Mjk5LCJpYXQiOjE3NjYwNzA4OTksInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5NTI4MzcxIn0.ffxq74gMdPMpuARwjZcOhJ6B7bCewr1SnuuPUyM-uaXqYXEaQiPCkynWv4SZMXzoLLqPmvSgyJb4a4JVGVTlVQ"

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

# Index Mapping: Using integer IDs as per the latest Dhan SDK
INDEX_MAP = {
    "NIFTY": {"id": 13, "segment": "IDX_I"},
    "BANKNIFTY": {"id": 25, "segment": "IDX_I"}
}

def get_dhan_data(symbol):
    try:
        idx = INDEX_MAP.get(symbol)
        
        # 1. Fetch Expiry List (Explicit parameters)
        expiry_response = dhan.expiry_list(
            under_security_id=idx["id"],
            under_exchange_segment=idx["segment"]
        )
        
        # Check if the response actually contains data
        if expiry_response.get('status') != 'success' or not expiry_response.get('data'):
            error_msg = expiry_response.get('remarks') or expiry_response.get('errors', {}).get('message', "No data returned")
            return {"error": f"Dhan API Error: {error_msg}. Check if Data API is active in your Dhan Dashboard."}
        
        latest_expiry = expiry_response['data'][0]
        
        # 2. Fetch Option Chain
        oc_response = dhan.option_chain(
            under_security_id=idx["id"],
            under_exchange_segment=idx["segment"],
            expiry=latest_expiry
        )
        
        if oc_response.get('status') != 'success':
            return {"error": "Option Chain fetch failed. Access Token might be restricted."}

        data = oc_response['data']
        spot = data.get('last_price', 0)
        raw_oc = data.get('oc', {})

        formatted = []
        for strike, values in raw_oc.items():
            ce = values.get('ce', {})
            pe = values.get('pe', {})
            formatted.append({
                "strikePrice": float(strike),
                "calls": format_side(ce),
                "puts": format_side(pe)
            })

        formatted.sort(key=lambda x: x['strikePrice'])
        return {"symbol": symbol, "spot": spot, "expiry": latest_expiry, "data": formatted, "time": datetime.now().strftime("%H:%M:%S")}

    except Exception as e:
        return {"error": f"System Exception: {str(e)}"}

def format_side(side):
    return {
        "oi": side.get("oi", 0),
        "changeInOi": side.get("oi", 0) - side.get("previous_oi", 0),
        "volume": side.get("volume", 0),
        "iv": round(side.get("implied_volatility", 0), 2),
        "ltp": side.get("last_price", 0),
        "change": round(side.get("last_price", 0) - side.get("previous_close_price", 0), 2)
    }

@app.route('/')
def index():
    symbol = request.args.get('symbol', 'NIFTY').upper()
    result = get_dhan_data(symbol)
    
    if "error" in result:
        return f"""
        <div style='font-family:sans-serif; padding:40px; border:2px solid red; margin:20px; border-radius:10px;'>
            <h2 style='color:red;'>⚠️ API Error</h2>
            <p><b>Reason:</b> {result['error']}</p>
            <hr>
            <h4>How to fix this:</h4>
            <ul>
                <li>Login to <b>web.dhan.co</b></li>
                <li>Go to <b>My Profile</b> > <b>DhanHQ Trading APIs</b></li>
                <li>Ensure <b>"Data APIs"</b> is toggled <b>ON</b> (it's a separate subscription from Trading API).</li>
                <li>Verify your <b>Access Token</b> has not expired.</li>
            </ul>
        </div>
        """

    # ... (Keep the same HTML template from previous response)
    return render_template_string(html_template, res=result) # Note: Refer to previous template

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
