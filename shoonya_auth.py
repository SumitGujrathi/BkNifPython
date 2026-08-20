import os
import hashlib
import pyotp
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

load_dotenv()

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        # FIX: Removed trailing slashes from host & websocket URLs
        super().__init__(
            host='https://api.shoonya.com/NorenWST',
            websocket='wss://api.shoonya.com/NorenWST'
        )
        self.is_logged_in = False
        
    def login_automatically(self):
        env_vars = {
            "SHOONYA_USER_ID": os.environ.get("SHOONYA_USER_ID"),
            "SHOONYA_PASSWORD": os.environ.get("SHOONYA_PASSWORD"),
            "SHOONYA_TOTP_SECRET": os.environ.get("SHOONYA_TOTP_SECRET"),
            "SHOONYA_VENDOR_CODE": os.environ.get("SHOONYA_VENDOR_CODE"),
            "SHOONYA_API_KEY": os.environ.get("SHOONYA_API_KEY"),
            "SHOONYA_IMEI": os.environ.get("SHOONYA_IMEI", "123456")
        }

        missing_keys = [k for k, v in env_vars.items() if not v]
        if missing_keys:
            print(f"CRITICAL: Missing environment variables on Render: {', '.join(missing_keys)}")
            self.is_logged_in = False
            return False

        user_id = env_vars["SHOONYA_USER_ID"].strip()
        password = env_vars["SHOONYA_PASSWORD"].strip()
        totp_secret = env_vars["SHOONYA_TOTP_SECRET"].strip()
        vendor_code = env_vars["SHOONYA_VENDOR_CODE"].strip()
        api_key = env_vars["SHOONYA_API_KEY"].strip()
        imei = env_vars["SHOONYA_IMEI"].strip()

        try:
            # Generate 6-digit TOTP
            totp = pyotp.TOTP(totp_secret)
            current_totp = totp.now()

            # Hash Password and AppKey using SHA-256
            pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
            app_key_str = f"{user_id}|{api_key}"
            app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

            print(f"Connecting to Shoonya API for user: {user_id}...")

            res = self.login(
                userid=user_id,
                password=pwd_sha256,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=app_key_sha256,
                imei=imei
            )

            if res and res.get('stat') == 'Ok':
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
