import requests
import pandas as pd
import time

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/option-chain",
}

def get_option_chain():
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        r = session.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            print("Error:", r.status_code)
            return pd.DataFrame()

        data = r.json()
        rows = data.get("records", {}).get("data", [])

        out = []
        for row in rows:
            strike = row.get("strikePrice")
            ce = row.get("CE", {})
            pe = row.get("PE", {})
            out.append({
                "strike": strike,
                "CE_ltp": ce.get("lastPrice"),
                "CE_oi": ce.get("openInterest"),
                "PE_ltp": pe.get("lastPrice"),
                "PE_oi": pe.get("openInterest")
            })

        df = pd.DataFrame(out)
        return df

    except Exception as e:
        print("EXCEPTION:", e)
        return pd.DataFrame()

if __name__ == "__main__":
    print("🚀 Worker started…")
    while True:
        df = get_option_chain()
        print(df)
        time.sleep(60)
    
