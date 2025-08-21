import os
from dotenv import load_dotenv
import websocket, json
import datetime

load_dotenv()
api_key = os.getenv("api_key")

current_bucket = None
candle = {}
interval = 10

def on_message(ws, message):
    global current_bucket, candle
    data = json.loads(message)

    if data.get("type") != "trade":
        return
    
    for trade in data["data"]:
        price = trade["p"]
        volume = trade["v"]
        ts = trade["t"] // 1000
        bucket = ts // interval

        if current_bucket is None:
            candle = {
                "High": price,
                "Low": price,
                "Open": price,
                "Close": price,
                "Volume": volume,
                "Time": ts
            }

            current_bucket = bucket
        
        elif current_bucket != bucket:
            print_candle(candle)
            current_bucket = bucket

            candle = {
                "High": price,
                "Low": price,
                "Open": price,
                "Close": price,
                "Volume": volume,
                "Time": ts
            }
        
        else:
            candle["High"] = max(candle["High"], price)
            candle["Low"] = min(candle["Low"], price)
            candle["Close"] = price
            candle["Volume"] += volume

def print_candle(candle):
    candle_time = datetime.datetime.fromtimestamp(candle["Time"]).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{candle_time}] O: {candle['Open']:.2f}; C: {candle['Close']:.2f}; H: {candle['High']:.2f}; L: {candle['Low']:.2f}; V: {candle['Volume']:.2f}")


def on_open(ws):
    print("Connected to Finnhub...")
    ws.send(json.dumps({"type": "subscribe", "symbol": "AAPL"}))

def on_error(ws, error):
    print("ERROR: ", error)

def on_close(ws, close_status_code, close_msg):
    print("Connecton Interruptted...")

ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={api_key}", on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)

try:
    ws.run_forever()
except KeyboardInterrupt:
    ws.close()




