import os
import hashlib
import pyotp
import requests
from NorenRestApiPy.NorenApi import NorenApi

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWClientAPI/',
            websocket='wss://api.shoonya.com/NorenWSAPI/'
        )
        self.is_logged_in = False

        # Set standard browser user agent to prevent Cloudflare/Gateway blocking
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def login_automatically(self):
        user_id = os.environ.get("SHOONYA_USER_ID", "").strip()
        password = os.environ.get("SHOONYA_PASSWORD", "").strip()
        totp_secret = os.environ.get("SHOONYA_TOTP_SECRET", "").strip()
        
        # DEFAULT: Retail accounts must use "FA_VC" unless assigned a custom Vendor Code in Prism
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE", "FA_VC").strip()
        if not vendor_code:
            vendor_code = "FA_VC"

        api_key = os.environ.get("SHOONYA_API_KEY", "").strip()
        imei = os.environ.get("SHOONYA_IMEI", "123456").strip()

        if not all([user_id, password, totp_secret, api_key]):
            print("CRITICAL: Missing required environment variables!", flush=True)
            self.is_logged_in = False
            return False

        try:
            # 1. Clean TOTP Secret & Generate 6-digit TOTP
            clean_totp = totp_secret.replace(" ", "").upper()
            totp = pyotp.TOTP(clean_totp)
            current_totp = totp.now()

            # 2. SHA-256 Hashes
            pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
            app_key_str = f"{user_id}|{api_key}"
            app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

            print(f"--- ATTEMPTING SHOONYA LOGIN ---", flush=True)
            print(f"User ID: {user_id}", flush=True)
            print(f"Vendor Code: {vendor_code}", flush=True)
            print(f"Generated TOTP Code: {current_totp}", flush=True)

            # 3. Direct Login Call
            res = self.login(
                userid=user_id,
                password=pwd_sha256,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=app_key_sha256,
                imei=imei
            )

            print(f"RAW SHOONYA RESPONSE: {res}", flush=True)

            if res and isinstance(res, dict) and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!", flush=True)
                self.is_logged_in = True
                return True
            else:
                emsg = res.get('emsg', 'No response dictionary from Shoonya') if isinstance(res, dict) else str(res)
                print(f"Shoonya API Login Rejected: {emsg}", flush=True)
                self.is_logged_in = False
                return False

        except Exception as e:
            print(f"Exception during Shoonya Login: {str(e)}", flush=True)
            self.is_logged_in = False
            return False

shoonya_api = ShoonyaSessionManager()
