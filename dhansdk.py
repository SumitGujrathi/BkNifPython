import requests

class Dhan:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.headers = {
            "Content-Type": "application/json",
            "Client-Id": client_id,
            "Access-Token": access_token
        }
        self.base_url = "https://api.dhan.co"

    def option_chain(self, symbol="NIFTY"):
        url = f"{self.base_url}/v1/market/option-chain?symbol={symbol}"
        r = requests.get(url, headers=self.headers, timeout=10)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "detail": r.text}
        return r.json()
