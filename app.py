from flask import Flask, jsonify, render_template
from shoonya_auth import shoonya_api

app = Flask(__name__)

def ensure_authenticated():
    if not shoonya_api.is_logged_in:
        print("Session uninitialized or invalid. Attempting login...", flush=True)
        return shoonya_api.login_automatically()
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        print("API endpoint called by browser...", flush=True)
        if not ensure_authenticated():
            return jsonify({
                "error": "Shoonya Authentication Failed. Check Render logs for RAW SHOONYA RESPONSE."
            })

        response = shoonya_api.get_option_chain(
            exchange='NFO',
            tradingsymbol='NIFTY-I',
            strikeprice=24000.0,
            count=10
        )
        
        print(f"Option Chain Response: {response}", flush=True)

        if not response or response.get('stat') == 'Not_Ok':
            emsg = response.get('emsg', 'Failed to fetch option chain') if response else 'Empty response from Shoonya'
            return jsonify({"error": emsg})

        return jsonify(response)
    except Exception as e:
        print(f"Exception in /api/data: {str(e)}", flush=True)
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    shoonya_api.login_automatically()
    app.run(host='0.0.0.0', port=5000)
