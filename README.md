# Pakhin Daonan 6810545859
# Cryptocurrency Dashboard with Tkinter

Final Project for 01219114 / 01219115 Programming I  
Kasetsart University

## Overview
This project is a real-time cryptocurrency dashboard built with Python and Tkinter.
It displays live market data from Binance using WebSocket and REST APIs.

## Features
- Real-time price tickers (BTC, ETH, SOL)
- Color-coded price changes (green/red)
- 24-hour volume display
- Order book (Top 10 bids/asks)
- Recent trades feed
- Toggle buttons to show/hide tickers
- Responsive multi-panel layout
- Graceful shutdown with WebSocket cleanup

## Technologies Used
- Python
- Tkinter (GUI)
- Binance REST API
- Binance WebSocket API
- websocket-client
- requests
- matplotlib (prepared for charts)

## How to Run
pip install -r requirements.txt
python dashboard.py
