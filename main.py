import requests
import threading
import time
import logging
from fastapi import FastAPI

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

CLIENT_ID = "YOUR_DHAN_CLIENT_ID"
ACCESS_TOKEN = "YOUR_DHAN_ACCESS_TOKEN"

# Dummy Dhan wrapper; replace with your real call
class Dhan:
    def __init__(self, client_id, token):
        self.client_id = client_id
        self.token = token

    def option_chain(self, symbol="NIFTY"):
        url = f"https://api.dhan.co/v1/market/option-chain?symbol={symbol}"
        r = requests.get(url, headers={
            "Client-Id": self.client_id,
            "Access-Token": self.token
        }, timeout=10)
        r.raise_for_status()
        return r.json()

dhan = Dhan(CLIENT_ID, ACCESS_TOKEN)

cached_data = None
last_updated = None

def update_loop():
    global cached_data, last_updated
    while True:
        try:
            logging.info("Fetching option chain from Dhan...")
            data = dhan.option_chain("NIFTY")
            cached_data = data
            last_updated = time.time()
            logging.info("Fetched successfully at %s", last_updated)
        except Exception as e:
            logging.error("Error fetching data: %s", e)
        time.sleep(60)

# Fetch once immediately on startup
def startup_fetch():
    try:
        logging.info("Initial fetch on startup...")
        data = dhan.option_chain("NIFTY")
        global cached_data, last_updated
        cached_data = data
        last_updated = time.time()
        logging.info("Initial fetch success at %s", last_updated)
    except Exception as e:
        logging.error("Initial fetch failed: %s", e)

@app.on_event("startup")
def on_startup():
    startup_fetch()
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()

@app.get("/")
def home():
    return {"status": "running", "message": "Nifty Option Chain API"}

@app.get("/optionchain/nifty")
def get_chain():
    return {
        "updated_at": last_updated,
        "data": cached_data
}
    
