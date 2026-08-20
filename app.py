from flask import Flask, jsonify, render_template
from shoonya_auth import shoonya_api

app = Flask(__name__)

def ensure_authenticated():
    if not shoonya_api.is_logged_in:
        print("Session uninitialized or invalid. Attempting login...")
        return shoonya_api.login_automatically()
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        if not ensure_authenticated():
            return jsonify({
                "error": "Shoonya Authentication Failed. Check Render Logs to see the exact login error message."
            })

        response = shoonya_api.get_option_chain(
            exchange='NFO',
            tradingsymbol='NIFTY',
            strikeprice=24000.0,
            count=10
        )
        
        if response and response.get('stat') == 'Not_Ok':
            return jsonify({"error": response.get('emsg', 'Failed to fetch option chain')})

        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    shoonya_api.login_automatically()
    app.run(host='0.0.0.0', port=5000)
