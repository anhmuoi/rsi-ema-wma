from re import M
import ccxt
import config
import schedule
import pandas as pd
import pandas_ta as ta
import talib as ta

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

import warnings
warnings.filterwarnings('ignore')

from datetime import datetime
import time


LIMIT = 500

TIME_FRAME = '5m'

SLOPE = 15
#this is the slope of rsi

exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY,
    'options': { 'adjustForTimeDifference': True }
})
exchange.set_sandbox_mode(True)



def rsi_signal(df):
    
    for i in range(45,len(df)-1):
        tmp = (df['rsi'][i] + df['rsi'][i+1]) / 2
        if (((abs(df['rsi'][i] - df['rsi_wma'][i]) < 1.5) and (abs(df['rsi'][i] - df['rsi_ema'][i])) < 1.5) or ((abs(tmp - df['rsi_wma'][i]) < 1.5) and (abs(tmp - df['rsi_ema'][i]) < 1.5))) and (abs(df['rsi_ema'][i] - df['rsi_wma'][i]) < 1.5):
            df.at[i, 'rsi_start'] = True
            if (df['rsi_ema'][i+1] < df['rsi_wma'][i+1]):
                for j in range(i+1, len(df)-1):
                    if (df['rsi_start'][i] == True):
                        if(((df['rsi'][j] == df['rsi_ema'][j]) or ((df['rsi_ema'][j] - df['rsi'][j]>0) and (df['rsi_ema'][j+1] - df['rsi'][j+1]<0))) and (abs(df['rsi'][i] - df['rsi'][j]) > SLOPE)):
                            df.at[j, 'start_buy'] = True
                            print(abs(df['rsi'][i] - df['rsi'][j]),i,j,'buy')
                        elif (df['rsi_wma'][j] < df['rsi_ema'][j]) or (df['rsi'][j] > df['rsi_wma'][j]):
                            df.at[i, 'rsi_start'] = False
            elif (df['rsi_ema'][i+1] > df['rsi_wma'][i+1]): 
                for j in range(i+1, len(df)-1):
                    if (df['rsi_start'][i] == True):
                        if(((df['rsi'][j] == df['rsi_ema'][j]) or ((df['rsi_ema'][j] - df['rsi'][j]<0) and (df['rsi_ema'][j+1] - df['rsi'][j+1]>0))) and (abs(df['rsi'][i] - df['rsi'][j]) > SLOPE)):
                            df.at[j, 'start_sell'] = True
                            print(abs(df['rsi'][i] - df['rsi'][j]),i,j,'sell')
                        elif (df['rsi_wma'][j] > df['rsi_ema'][j]) or (df['rsi'][j] < df['rsi_wma'][j]):
                            df.at[i, 'rsi_start'] = False                                              
    return df

    
# check buy sell signals
def check_buy_sell_signals(df):
    last_row_index = len(df.index) - 1

    if (exchange.fetch_balance()['BTC']['free'] >= 0.001):
        if (df['start_buy'][last_row_index] and df['start_buy'][last_row_index] == True):
                print('buy buy buy')
                order = exchange.create_market_sell_order('BTC/USDT', 0.0005)
                print(order)
        if (df['start_sell'][last_row_index] and df['start_sell'][last_row_index] == True):
            print('sell sell sell')
            order = exchange.create_market_buy_order('BTC/USDT', 0.0005)
            print(order)


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    # order = exchange.create_order(symbol='BTC/USDT',type='market',amount=0.01,side='buy')
    # print(order)
    bars = exchange.fetch_ohlcv('BTC/USDT', timeframe=TIME_FRAME, limit=LIMIT)

    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # rsi
    df['rsi'] = ta.RSI(df['close'], timeperiod=14)
    # wma of rsi
    df['rsi_wma'] = ta.WMA(df['rsi'], timeperiod=45)
    # ema of rsi
    df['rsi_ema'] = ta.EMA(df['rsi'], timeperiod=9)

    rsi_signal(df)
    check_buy_sell_signals(df)
    print(df)



# mỗi 2 giây chạy một lần  
schedule.every(2).seconds.do(run_bot)


while True:
    schedule.run_pending()
    # time sleep
    time.sleep(1)