import os
import hashlib
import pyotp
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

load_dotenv()

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        # NOTE: Removed trailing slash from host URL to prevent '//QuickAuth' double slash errors
        super().__init__(
            host='https://api.shoonya.com/NorenWClientTP',
            websocket='wss://api.shoonya.com/NorenWSTP'
        )
        self.is_logged_in = False

        # Apply User-Agent header bypass
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
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE", "FA_VC").strip()
        api_key = os.environ.get("SHOONYA_API_KEY", "").strip()
        imei = os.environ.get("SHOONYA_IMEI", "123456").strip()

        if not all([user_id, password, totp_secret, api_key]):
            print("CRITICAL ERROR: Missing SHOONYA environment variables in .env!", flush=True)
            self.is_logged_in = False
            return False

        try:
            # 1. Clean TOTP secret and generate token
            clean_totp = totp_secret.replace(" ", "").upper()
            current_totp = pyotp.TOTP(clean_totp).now()

            # 2. Hash Password and API Secret as required by Shoonya
            pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            api_secret_str = f"{user_id}:{api_key}"
            api_secret_hash = hashlib.sha256(api_secret_str.encode('utf-8')).hexdigest()

            print(f"Connecting to Shoonya API for user: {user_id}...", flush=True)

            # 3. Submit Login
            res = self.login(
                userid=user_id,
                password=pwd_hash,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=api_secret_hash,
                imei=imei
            )

            if res and isinstance(res, dict) and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!", flush=True)
                self.is_logged_in = True
                return True
            else:
                emsg = res.get('emsg', 'Invalid response from Shoonya servers') if isinstance(res, dict) else 'Non-JSON response received'
                print(f"Shoonya API Login Rejected: {emsg}", flush=True)
                self.is_logged_in = False
                return False

        except Exception as e:
            print(f"Exception during Shoonya Login: {str(e)}", flush=True)
            self.is_logged_in = False
            return False

shoonya_api = ShoonyaSessionManager()
