from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    symbols = ["NIFTY_50", "NIFTY_BANK", "SBIN", "HDFCBANK"]
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NSE Live Dashboard</title>
    <style>
        body {{ font-family: Arial; background: #1a1a1a; color: #fff; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #00d4ff; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; background: #2a2a2a; }}
        th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid #444; }}
        th {{ background: #00d4ff; color: #000; }}
        .ltp {{ color: #ffd700; font-weight: bold; font-size: 1.1em; }}
        tr:hover {{ background: #3a3a3a; }}
        .footer {{ text-align: center; color: #888; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NSE Live Quotes - {datetime.now().strftime("%H:%M:%S IST")}</h1>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th><th>LTP</th><th>Open</th><th>High</th><th>Low</th><th>Prev</th><th>Volume</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add test data FIRST (always shows table)
    test_data = [
        {"symbol": "NIFTY_50", "ltp": 24350.25, "open": 24320.00, "high": 24400.75, "low": 24280.50, "prev": 24300.00, "volume": 1250000},
        {"symbol": "NIFTY_BANK", "ltp": 51250.75, "open": 51180.25, "high": 51320.00, "low": 51120.00, "prev": 51200.50, "volume": 850000},
        {"symbol": "SBIN", "ltp": 825.50, "open": 823.25, "high": 828.75, "low": 822.00, "prev": 824.00, "volume": 4500000},
        {"symbol": "HDFCBANK", "ltp": 1650.25, "open": 1648.00, "high": 1655.50, "low": 1645.00, "prev": 1649.75, "volume": 3200000}
    ]
    
    for row in test_data:
        html += f"""
                <tr>
                    <td>{row['symbol']}</td>
                    <td class="ltp">{row['ltp']}</td>
                    <td>{row['open']}</td>
                    <td>{row['high']}</td>
                    <td>{row['low']}</td>
                    <td>{row['prev']}</td>
                    <td>{row['volume']:,}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        <div class="footer">TEST DATA - Working! | NSE: 9:15 AM - 3:30 PM IST | Auto-refresh 60s</div>
    </div>
    <script>setInterval(() => location.reload(), 60000);</script>
</body>
</html>
    """
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
