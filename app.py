from flask import Flask, jsonify, render_template
from shoonya_auth import shoonya_api

app = Flask(__name__)

def ensure_authenticated():
    """Validates session health; automatically logs back in if token expired."""
    limits = shoonya_api.get_limits()
    if not limits or limits.get('stat') != 'Ok':
        print("Session expired. Triggering silent background login...")
        return shoonya_api.login_automatically()
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        # Guarantee session is live
        if not ensure_authenticated():
            return jsonify({"error": "Authentication with Shoonya API failed"})

        # Fetch live Nifty Option Chain from NFO exchange
        response = shoonya_api.get_option_chain(
            exchange='NFO',
            tradingsymbol='NIFTY',
            strikeprice=24000.0,  # Center strike price
            count=10              # Number of strike prices on each side (ITM/OTM)
        )
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    shoonya_api.login_automatically()
    app.run(host='0.0.0.0', port=5000)
