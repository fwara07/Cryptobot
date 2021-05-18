import websocket
import talib, json
import numpy as np
from binance.client import Client
import config
from binance.enums import *

symbol = "btcusdt"
interval = "1m"

socket = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"

aroon_time_period = 14

core_quantity = 0
is_trade = True

amount = 50
core_trade_amount = amount * 0.80
trade_amount = amount * 0.20
money_end = amount
portfolio = 0
investement, cls, highs, lows = [], [], [], []
real_time_portfolio_value = []

client = Client(config.API_KEY, config.API_SECRET, tld="us")


def buy(allocated_money, price):
    global money_end, portfolio, investement
    quantity = allocated_money / price
    order = client.create_order(
        symbol="BTCUSD", side="BUY", type="MARKET", quantity=quantity
    )
    print(order)
    money_end -= quantity * price
    portfolio += quantity
    if investement == []:
        investement.append(allocated_money)
    else:
        investement.append(allocated_money)
        investement[-1] += investement[-2]


def sell(allocated_money, price):
    global money_end, portfolio, investement
    quantity = allocated_money / price
    order = client.create_order(
        symbol="BTCUSD", side="SELL", type="MARKET", quantity=quantity
    )
    print(order)
    money_end += quantity * price
    portfolio -= quantity
    investement.append(-allocated_money)
    investement[-1] += investement[-2]


def on_open(ws):
    print("Opened connection")


def on_close(ws):
    global portfolio, cls
    portfolio_value = portfolio * cls[-1]
    if portfolio_value > 0:
        sell(portfolio_value, price=cls[-1])
    else:
        buy(-portfolio_value, price=cls[-1])
    money_end += investement[-1]
    print("All trades settled")


def on_message(ws, message):
    global cls, highs, lows, is_trade, core_trade_amount, core_quantity, money_end, portfolio, real_time_portfolio_value, aroon_time_period, trade_amount
    json_msg = json.loads(message)
    cs = json_msg["k"]
    is_close, close, high, low = cs["x"], cs["c"], cs["h"], cs["l"]

    if is_close:
        cls.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        last_price = cls[-1]
        print(f"Closes: {cls}")

        if is_trade:
            buy(core_trade_amount, price=cls[-1])
            print(f"Investment: Bought ${core_trade_amount} worth of bitcoin", "\n")
            core_quantity += core_trade_amount / cls[-1]
            is_trade = False

        aroon = talib.AROONOSC(np.array(highs), np.array(lows), aroon_time_period)
        aroon = list(aroon)
        last_aroon = round(float(aroon[-1]), 2)
        amt = last_aroon * trade_amount / 100
        port_value = portfolio * last_price - core_quantity * last_price
        trade_amt = amt - port_value

        print(f"Port Val: {port_value}")
        print(f"Money End: {money_end}")
        print(f"Core Quantity: {core_quantity}")
        print(f"Last Price: {last_price}")

        rt_port_value = port_value + core_quantity * last_price + money_end
        real_time_portfolio_value.append(float(rt_port_value))

        print(f'Last Aroon is "{last_aroon}" and recommended exposure is ${amt}')
        print(f"Reat-Time Portfolio Value ${rt_port_value}", "\n")

        if trade_amt > 0:
            buy(trade_amt, price=last_price)
            print(f"We bought ${trade_amt} worth of bitcoin", "\n", "\n")
        elif trade_amt < 0:
            sell(-trade_amt, price=last_price)
            print(f"We sold ${-trade_amt} worth of bitcoin", "\n", "\n")


ws = websocket.WebSocketApp(
    socket, on_message=on_message, on_close=on_close, on_open=on_open
)

ws.run_forever()
