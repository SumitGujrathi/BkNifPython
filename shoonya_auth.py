import os
import hashlib
import pyotp
from NorenRestApiPy.NorenApi import NorenApi
from dotenv import load_dotenv

# Load local .env file during development (ignored in Render production)
load_dotenv()

class ShoonyaSessionManager(NorenApi):
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWST/',
            websocket='wss://api.shoonya.com/NorenWST/'
        )
        
    def login_automatically(self):
        # 1. Fetch credentials securely from environment variables
        user_id = os.environ.get("SHOONYA_USER_ID")
        password = os.environ.get("SHOONYA_PASSWORD")
        totp_secret = os.environ.get("SHOONYA_TOTP_SECRET")
        vendor_code = os.environ.get("SHOONYA_VENDOR_CODE")
        api_key = os.environ.get("SHOONYA_API_KEY")
        imei = os.environ.get("SHOONYA_IMEI", "123456")

        if not all([user_id, password, totp_secret, vendor_code, api_key]):
            print("Error: Missing required environment variables!")
            return False

        # 2. Generate live 6-digit TOTP code dynamically
        totp = pyotp.TOTP(totp_secret)
        current_totp = totp.now()

        # 3. Calculate SHA-256 Hashes required by Shoonya OMS
        pwd_sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
        app_key_str = user_id + "|" + api_key
        app_key_sha256 = hashlib.sha256(app_key_str.encode('utf-8')).hexdigest()

        # 4. Authenticate session
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
            return True
        else:
            print("Shoonya Auto-Login Failed:", res)
            return False

# Export global instance
shoonya_api = ShoonyaSessionManager()
