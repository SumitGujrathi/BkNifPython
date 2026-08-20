import os
import hashlib
import pyotp
import json
from NorenRestApiPy.NorenApi import NorenApi

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWClientAPI/',
            websocket='wss://api.shoonya.com/NorenWSAPI/'
        )
        self.is_logged_in = False
        
    def login_automatically(self):
        user_id = os.environ.get("SHOONYA_USER_ID", "").strip()
        password = os.environ.get("SHOONYA_PASSWORD", "").strip()
        totp_secret = os.environ.get("SHOONYA_TOTP_SECRET", "").strip()
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE", "").strip()
        api_key = os.environ.get("SHOONYA_API_KEY", "").strip()
        imei = os.environ.get("SHOONYA_IMEI", "123456").strip()

        if not all([user_id, password, totp_secret, vendor_code, api_key]):
            print("CRITICAL: Missing one or more credentials!")
            self.is_logged_in = False
            return False

        try:
            # Clean TOTP Secret (remove any extra spaces)
            clean_totp_secret = totp_secret.replace(" ", "").upper()
            totp = pyotp.TOTP(clean_totp_secret)
            current_totp = totp.now()

            # Hash Password (SHA-256)
            pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()

            # Hash AppKey: User_ID|API_Key (SHA-256)
            app_key_str = f"{user_id}|{api_key}"
            app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

            print(f"--- ATTEMPTING SHOONYA LOGIN ---")
            print(f"User ID: {user_id}")
            print(f"Vendor Code: {vendor_code}")
            print(f"Generated TOTP Code: {current_totp}")

            # Send Login Request
            res = self.login(
                userid=user_id,
                password=pwd_sha256,
                twoFA=current_totp,
                vendor_code=vendor_code,
                api_secret=app_key_sha256,
                imei=imei
            )

            print(f"RAW SHOONYA RESPONSE: {res}")

            if res and isinstance(res, dict) and res.get('stat') == 'Ok':
                print("Shoonya Auto-Login Successful!")
                self.is_logged_in = True
                return True
            else:
                emsg = res.get('emsg', 'No error message provided by Shoonya') if isinstance(res, dict) else str(res)
                print(f"Shoonya API Login Rejected: {emsg}")
                self.is_logged_in = False
                return False

        except Exception as e:
            print(f"Exception during Shoonya Login: {str(e)}")
            self.is_logged_in = False
            return False

shoonya_api = ShoonyaSessionManager()
