import os
import pyotp
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWClientTP/',
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )
        self.is_logged_in = False

        # Set standard browser User-Agent header to prevent firewall blocks
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
            print("CRITICAL ERROR: One or more SHOONYA environment variables are missing in .env!", flush=True)
            self.is_logged_in = False
            return False

        try:
            # 1. Clean and Generate 6-digit TOTP
            clean_totp = totp_secret.replace(" ", "").upper()
            current_totp = pyotp.TOTP(clean_totp).now()

            print(f"Connecting to Shoonya API for user: {user_id}...", flush=True)

            # 2. Call SDK login method
            # NOTE: Pass raw 'password' and 'api_key' — NorenRestApiPy hashes them automatically.
            res = self.login(
                userid=user_id,
                password=password,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=api_key,
                imei=imei
            )

            # 3. Validate response
            if res and isinstance(res, dict) and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!", flush=True)
                self.is_logged_in = True
                return True
            else:
                emsg = res.get('emsg', 'Invalid or empty response from Shoonya servers') if isinstance(res, dict) else 'Shoonya server returned an invalid response or error page.'
                print(f"Shoonya API Login Rejected: {emsg}", flush=True)
                self.is_logged_in = False
                return False

        except Exception as e:
            print(f"Exception during Shoonya Login: {str(e)}", flush=True)
            self.is_logged_in = False
            return False

# Create a single instance to be imported across the application
shoonya_api = ShoonyaSessionManager()
