import os
from flask import Flask, jsonify, render_template
from shoonya_auth import shoonya_api

app = Flask(__name__)

def ensure_authenticated():
    """Ensure Shoonya API is logged in before proceeding."""
    try:
        if not getattr(shoonya_api, 'is_logged_in', False):
            print("Session uninitialized or invalid. Attempting login...", flush=True)
            return shoonya_api.login_automatically()
        return True
    except Exception as e:
        print(f"Error checking/performing authentication: {str(e)}", flush=True)
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    try:
        print("API endpoint called by browser...", flush=True)

        # 1. Check Authentication
        if not ensure_authenticated():
            return jsonify({
                "error": "Shoonya Authentication Failed. Verify credentials in .env file."
            }), 401

        # 2. Call Shoonya Option Chain with CORRECT parameters
        # Correct Shoonya parameters: exch, tsym, strprc, cnt
        response = shoonya_api.api.get_option_chain(
            exch='NFO',
            tsym='NIFTY',
            strprc='24000',
            cnt=10
        )
        
        print(f"Option Chain Response: {response}", flush=True)

        # 3. Handle Empty or Faulty Responses
        if not response:
            return jsonify({"error": "Empty response received from Shoonya API"}), 500

        if isinstance(response, dict) and response.get('stat') == 'Not_Ok':
            emsg = response.get('emsg', 'Failed to fetch option chain')
            
            # If session expired, attempt re-login once automatically
            if "Session Expired" in emsg or "Invalid Session" in emsg:
                shoonya_api.is_logged_in = False
                if ensure_authenticated():
                    response = shoonya_api.api.get_option_chain(
                        exch='NFO',
                        tsym='NIFTY',
                        strprc='24000',
                        cnt=10
                    )

            if not response or response.get('stat') == 'Not_Ok':
                return jsonify({"error": emsg}), 400

        return jsonify(response)

    except Exception as e:
        print(f"Exception in /api/data: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initial Login on Startup
    print("Initializing Shoonya connection on startup...", flush=True)
    ensure_authenticated()
    
    # Run server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
