import os
import hashlib
import pyotp
from NorenRestApiPy.NorenApi import NorenApi

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        # NEW ACTIVE ENDPOINTS (Updated by Shoonya)
        super().__init__(
            host='https://api.shoonya.com/NorenWClientAPI/',
            websocket='wss://api.shoonya.com/NorenWSAPI/'
        )
        self.is_logged_in = False
        
    def login_automatically(self):
        # HARDCODE TEMPORARILY FOR TESTING IF ENV VARS ARE FAILING:
        # Replace the right-side values with your actual plain-text strings.
        user_id = os.environ.get("SHOONYA_USER_ID", "FN229754").strip()
        password = os.environ.get("SHOONYA_PASSWORD", "YOUR_PLAIN_PASSWORD").strip()
        totp_secret = os.environ.get("SHOONYA_TOTP_SECRET", "YOUR_32_CHAR_TOTP_SECRET").strip()
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE", "FN229754_VC").strip()
        api_key = os.environ.get("SHOONYA_API_KEY", "YOUR_API_KEY_FROM_PRISM").strip()
        imei = os.environ.get("SHOONYA_IMEI", "123456").strip()

        try:
            # 1. Generate live TOTP
            totp = pyotp.TOTP(totp_secret)
            current_totp = totp.now()

            # 2. Compute Hashes
            pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
            app_key_str = f"{user_id}|{api_key}"
            app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

            print(f"Connecting to Shoonya API for user: {user_id}...")

            # 3. Authenticate with Shoonya
            res = self.login(
                userid=user_id,
                password=pwd_sha256,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=app_key_sha256,
                imei=imei
            )

            if res and isinstance(res, dict) and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!")
                self.is_logged_in = True
                return True
            else:
                emsg = res.get('emsg', 'Unknown Error') if isinstance(res, dict) else str(res)
                print(f"Shoonya API Login Rejected: {emsg}")
                self.is_logged_in = False
                return False

        except Exception as e:
            print(f"Exception during Shoonya Login: {str(e)}")
            self.is_logged_in = False
            return False

shoonya_api = ShoonyaSessionManager()
