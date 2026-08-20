import os
import hashlib
import pyotp
import json
import requests
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

load_dotenv()

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        # We use NorenWClientTP/ which is the standard Shoonya retail endpoint
        super().__init__(
            host='https://api.shoonya.com/NorenWClientTP/',
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )
        self.is_logged_in = False

        for attr_name in ['_session', '_NorenApi__session', 'session']:
            session_obj = getattr(self, attr_name, None)
            if session_obj and hasattr(session_obj, 'headers'):
                session_obj.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
        
    def login_automatically(self):
        user_id = os.environ.get("SHOONYA_USER_ID", "").strip()
        password = os.environ.get("SHOONYA_PASSWORD", "").strip()
        totp_secret = os.environ.get("SHOONYA_TOTP_SECRET", "").strip()
        
        # Test with FA_VC first. If 404/Invalid, we change to your specific User ID VC
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE", "FA_VC").strip()
        if not vendor_code:
            vendor_code = "FA_VC"

        api_key = os.environ.get("SHOONYA_API_KEY", "").strip()
        imei = os.environ.get("SHOONYA_IMEI", "123456").strip()

        if not all([user_id, password, totp_secret, api_key]):
            print("CRITICAL: Environment variables are missing!", flush=True)
            self.is_logged_in = False
            return False

        try:
            clean_totp = totp_secret.replace(" ", "").upper()
            totp = pyotp.TOTP(clean_totp)
            current_totp = totp.now()

            pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
            app_key_str = f"{user_id}|{api_key}"
            app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

            print(f"--- ATTEMPTING SHOONYA LOGIN ---", flush=True)
            print(f"User ID: {user_id}", flush=True)
            print(f"Vendor Code: {vendor_code}", flush=True)
            print(f"Generated TOTP Code: {current_totp}", flush=True)

            # =========================================================
            # DIAGNOSTIC: Direct HTTP Probe to see Cloudflare/Server block
            # =========================================================
            print("--- RUNNING DIRECT HTTP PROBE ---", flush=True)
            probe_payload = {
                "uid": user_id, "pwd": pwd_sha256, "factor2": current_totp,
                "vc": vendor_code, "appkey": app_key_sha256, "imei": imei, "source": "API"
            }
            try:
                probe_res = requests.post(
                    "https://api.shoonya.com/NorenWClientTP/QuickAuth",
                    data="jData=" + json.dumps(probe_payload),
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                print(f"PROBE HTTP STATUS: {probe_res.status_code}", flush=True)
                print(f"PROBE RAW TEXT: {probe_res.text[:300]}", flush=True)
            except Exception as probe_err:
                print(f"PROBE NETWORK FAILURE: {str(probe_err)}", flush=True)
            print("---------------------------------", flush=True)
            # =========================================================

            res = self.login(
                userid=user_id,
                password=pwd_sha256,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=app_key_sha256,
                imei=imei
            )

            print(f"SDK RESPONSE: {res}", flush=True)

            if res and isinstance(res, dict) and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!", flush=True)
                self.is_logged_in = True
                return True
            else:
                emsg = res.get('emsg', 'No JSON parsed from Shoonya') if isinstance(res, dict) else str(res)
                print(f"Shoonya API Login Rejected: {emsg}", flush=True)
                self.is_logged_in = False
                return False

        except Exception as e:
            print(f"Exception during Shoonya Login: {str(e)}", flush=True)
            self.is_logged_in = False
            return False

shoonya_api = ShoonyaSessionManager()
