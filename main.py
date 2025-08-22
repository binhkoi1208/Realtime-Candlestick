import os
from dotenv import load_dotenv
import websocket, json
import datetime
import plotly.graph_objects as go
import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Output, Input
import threading

# Get ENV
load_dotenv()
api_key = os.getenv("api_key")

# Set up variables
current_bucket = None
candle = {}
interval = 60
candles_list = []

# Websocket Func
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
            candles_list.append(candle.copy())
        
        elif current_bucket != bucket:
            current_bucket = bucket
            candles_list.append(candle.copy())
            if len(candles_list) > 50:
                candles_list.pop(0)

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

def on_open(ws):
    print("Connected to Finnhub...")
    ws.send(json.dumps({"type": "subscribe", "symbol": "BINANCE:BTCUSDT"}))

def on_error(ws, error):
    print("ERROR: ", error)

def on_close(ws, close_status_code, close_msg):
    print("Connecton Interruptted...")

ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={api_key}", on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)

# Create Plotly
df = pd.DataFrame(candles_list, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
fig = go.Figure(data=[go.Candlestick(
    x=pd.to_datetime(df["Time"], unit='s'),
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    increasing_line_color="green",
    decreasing_line_color="red",
)])
fig.update_xaxes(type="date")
fig.update_traces(whiskerwidth=0.2, increasing_line_width=1.5, decreasing_line_width=1.5)


# Create Layout for Candlesticks
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Realtime Candlesticks"),
    dcc.Graph(id="candlestick-graph"),
    dcc.Interval(
        id="interval-component",
        interval=1*1000,
        n_intervals=0
    )
])

# Create Callback
@app.callback(
    Output('candlestick-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)

# Update Graph Func
def update_graph(n):
    if not candles_list:
        return go.Figure()
    
    df = pd.DataFrame(candles_list)

    fig = go.Figure(data=[go.Candlestick(
        x=pd.to_datetime(df["Time"], unit='s'),
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        increasing_line_color="green",
        decreasing_line_color="red",
    )])

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_xaxes(type="date")
    fig.update_traces(whiskerwidth=0.2, increasing_line_width=1.5, decreasing_line_width=1.5)

    return fig

# Run Websocket 
def run_websocket(ws):
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()

# Main: Websocket on Threads and Dash on mainstream
if __name__ == "__main__":
    ws_thread = threading.Thread(target=run_websocket, args=(ws,))
    ws_thread.daemon = True
    ws_thread.start()

    app.run(debug=True)