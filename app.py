from flask import Flask, jsonify, render_template
from shoonya_auth import shoonya_api

app = Flask(__name__)

def ensure_authenticated():
    """Checks session health; triggers auto-login if token expired."""
    limits = shoonya_api.get_limits()
    if not limits or limits.get('stat') != 'Ok':
        print("Session expired or uninitialized. Auto-logging in...")
        return shoonya_api.login_automatically()
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Shoonya Authentication Failed. Check environment variables."})

        # Fetch option chain for NIFTY near strike price 24000
        response = shoonya_api.get_option_chain(
            exchange='NFO',
            tradingsymbol='NIFTY',
            strikeprice=24000.0,
            count=10
        )
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    shoonya_api.login_automatically()
    app.run(host='0.0.0.0', port=5000)
