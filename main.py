from fastapi import FastAPI
import uvicorn
from dhansdk import Dhan
import time
import threading

app = FastAPI()

# ⬇️ Put your credentials here
CLIENT_ID = "YOUR_DHAN_CLIENT_ID"
ACCESS_TOKEN = "YOUR_DHAN_ACCESS_TOKEN"

dhan = Dhan(CLIENT_ID, ACCESS_TOKEN)

cached_data = None
last_updated = 0

# Auto-refresh every 60 seconds in background thread
def background_updater():
    global cached_data, last_updated
    while True:
        try:
            cached_data = dhan.option_chain("NIFTY")
            last_updated = time.time()
            print("Updated option chain at:", last_updated)
        except Exception as e:
            print("Update error:", e)
        time.sleep(60)

threading.Thread(target=background_updater, daemon=True).start()


@app.get("/")
def home():
    return {"status": "running", "message": "Nifty Option Chain API"}

@app.get("/optionchain/nifty")
def get_nifty_chain():
    return {
        "updated_at": last_updated,
        "data": cached_data
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
                
