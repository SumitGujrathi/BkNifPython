import requests
import pandas as pd
import time

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
}

def get_option_chain():
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

        response = session.get(url, headers=headers, timeout=10)
        status = response.status_code

        if status != 200:
            print(f"❌ NSE Error: HTTP {status}")
            print("Most likely: Blocked / Captcha / Rate-limited")
            return pd.DataFrame()

        data = response.json()

        records = data.get("records", {}).get("data", [])

        if not records:
            print("⚠ NSE returned EMPTY data (blocked or no records found).")
            return pd.DataFrame()

        rows = []
        for row in records:
            strike = row.get("strikePrice", None)
            ce = row.get("CE", {})
            pe = row.get("PE", {})

            rows.append({
                "strike": strike,
                "CE_ltp": ce.get("lastPrice"),
                "CE_oi": ce.get("openInterest"),
                "CE_chg_oi": ce.get("changeinOpenInterest"),
                "PE_ltp": pe.get("lastPrice"),
                "PE_oi": pe.get("openInterest"),
                "PE_chg_oi": pe.get("changeinOpenInterest"),
            })

        df = pd.DataFrame(rows)

        if "strike" not in df.columns:
            print("⚠ ERROR: No strike column returned from NSE API")
            print("Most likely NSE blocked your network IP.")
            return pd.DataFrame()

        df = df.dropna(subset=["strike"])
        df = df.sort_values("strike")
        return df

    except Exception as e:
        print("❌ Exception:", e)
        return pd.DataFrame()


# Continuous fetch every 1 minute
if __name__ == "__main__":
    while True:
        df = get_option_chain()
        if df.empty:
            print("⚠ Empty DataFrame returned.")
        else:
            print(df)
        print("-" * 80)
        time.sleep(60)
        
