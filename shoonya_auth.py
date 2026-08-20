import os
import hashlib
import pyotp
import logging
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWST/',
            websocket='wss://api.shoonya.com/NorenWST/'
        )
        self.is_logged_in = False
        
    def login_automatically(self):
        user_id = os.environ.get("SHOONYA_USER_ID")
        password = os.environ.get("SHOONYA_PASSWORD")
        totp_secret = os.environ.get("SHOONYA_TOTP_SECRET")
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE")
        api_key = os.environ.get("SHOONYA_API_KEY")
        imei = os.environ.get("SHOONYA_IMEI", "123456")

        if not all([user_id, password, totp_secret, vendor_code, api_key]):
            print("CRITICAL: One or more environment variables are missing in Render!")
            self.is_logged_in = False
            return False

        try:
            # Generate live 6-digit TOTP from secret key
            totp = pyotp.TOTP(totp_secret.strip())
            current_totp = totp.now()

            # Hash Password and AppKey (User_ID | API_Key)
            pwd_sha256 = hashlib.sha256(password.strip().encode('utf-8')).hexdigest()
            app_key_str = f"{user_id.strip()}|{api_key.strip()}"
            app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

            print(f"Attempting login for User: {user_id}...")

            res = self.login(
                userid=user_id.strip(),
                password=pwd_sha256,
                twoFA=current_totp,
                vendor_code=vendor_code.strip(),
                api_secret=app_key_sha256,
                imei=imei.strip()
            )

            if res and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!")
                self.is_logged_in = True
                return True
            else:
                error_msg = res.get('emsg', 'Unknown Login Error') if res else 'No response'
                print(f"Shoonya Auto-Login Failed: {error_msg}")
                self.is_logged_in = False
                return False

        except Exception as e:
            print("Error during Shoonya login execution:", str(e))
            self.is_logged_in = False
            return False

shoonya_api = ShoonyaSessionManager()
