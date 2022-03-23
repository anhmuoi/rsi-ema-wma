import ccxt
import config
import schedule
import pandas as pd
import talib as ta
import math as math
from datetime import datetime  
from datetime import timedelta  

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


import warnings
warnings.filterwarnings('ignore')

from datetime import datetime
import time

SYMBOL = 'BTC/USDT'
SYMBOL_FREE = 'BTC'
LIMIT = 300
ANGLE = 10

TIME_FRAME = '5m'

SLOPE = 10
#this is the slope of rsi


exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY,
    'options': { 'adjustForTimeDifference': True }
})
exchange.set_sandbox_mode(True)



def lengthSquare(X, Y):
    xDiff = X[0] - Y[0]
    yDiff = X[1] - Y[1]
    return xDiff * xDiff + yDiff * yDiff        

def printAngle(A, B, C):
     
    # Square of lengths be a2, b2, c2
    a2 = lengthSquare(B, C)
    b2 = lengthSquare(A, C)
    c2 = lengthSquare(A, B)
 
    # length of sides be a, b, c
    a = math.sqrt(a2)
    b = math.sqrt(b2)
    c = math.sqrt(c2)
 
    # From Cosine law
    alpha = math.acos((b2 + c2 - a2) / (2 * b * c))
    # betta = math.acos((a2 + c2 - b2) / (2 * a * c))
    # gamma = math.acos((a2 + b2 - c2) / (2 * a * b))
    # Converting to degree
    alpha = alpha * 180 / math.pi
    # betta = betta * 180 / math.pi
    # gamma = gamma * 180 / math.pi
 
    return alpha


def rsi_signal(df):
    
    # set start_buy and start_sell to False
    df['start_buy'] = False
    df['start_sell'] = False


    for i in range(45,len(df)-1):
        tmp = (df['rsi'][i] + df['rsi'][i+1]) / 2
        if (((abs(df['rsi'][i] - df['rsi_wma'][i]) < 2.5) and (abs(df['rsi'][i] - df['rsi_ema'][i])) < 2.5) or ((abs(tmp - df['rsi_wma'][i]) < 2.5) and (abs(tmp - df['rsi_ema'][i]) < 2.5))) and (abs(df['rsi_ema'][i] - df['rsi_wma'][i]) < 2.5) :
            df.at[i, 'rsi_start'] = True
            if (df['rsi'][i+1] < df['rsi_wma'][i+1]) and (printAngle((20, df['rsi'][i]),(22, df['rsi_ema'][i+1]),(22, df['rsi'][i+1])) > ANGLE):
                count = 0
                for j in range(i+1, len(df)-1):
                    if (df['rsi_start'][i] == True):
                        if(((df['rsi'][j] == df['rsi_ema'][j]) or ((df['rsi_ema'][j] - df['rsi'][j]>0) and (df['rsi_ema'][j+1] - df['rsi'][j+1]<0))) and (abs(df['rsi'][i] - df['rsi'][j]) > SLOPE)) and count<2:
                            if(count == 0):
                                tmp = df['rsi'][i]
                                tmp_index = 0
                                for k in range(i+1, j):
                                    
                                    if(df['rsi'][k] < df['rsi_ema'][k]):
                                        if (k>i+1) and (abs(df['rsi'][k] - df['rsi_wma'][k]) < 1):
                                            tmp = df['rsi'][i]
                                            break 
                                        tmp_index +=1
                                        tmp = df['rsi'][k]
                                    else:
                                        break
                                if (df['rsi'][i] - tmp > 20):
                                    df.at[j+1, 'start_buy'] = True
                                    df.at[j+1, 'start_sell'] = False
                                    count = count + 1
                                    # print(abs(df['rsi'][i] - df['rsi'][j]),i,j,tmp,'buy')
                                # else:
                                #     print(tmp,df['timestamp'][i])
                            elif count == 1:
                                df.at[j+1, 'start_buy'] = True
                                df.at[j+1, 'start_sell'] = False
                                count = count + 1
                                
                        elif (df['rsi'][j] > df['rsi_wma'][j]) or count == 2:
                            df.at[i, 'rsi_start'] = False
                            count = 0
                        if(df['rsi'][len(df)-1] == df['rsi_ema'][len(df)-1]) or ((df['rsi_ema'][len(df)-2] - df['rsi'][len(df)-2]>0) and (df['rsi_ema'][len(df)-1] - df['rsi'][len(df)-1]<0)) and count<2 and j == len(df)-2:
                            if count == 0:
                                tmp = df['rsi'][i]
                                tmp_index = 0
                                for k in range(i+1, len(df)-1):
                                    
                                    if (df['rsi'][k] < df['rsi_ema'][k]):
                                        if (k>i+1) and (abs(df['rsi'][k] - df['rsi_wma'][k]) < 1):
                                            tmp = df['rsi'][i]
                                            break 
                                        tmp_index +=1
                                        tmp = df['rsi'][k]
                                    else:
                                        break
                                if (df['rsi'][i] - tmp > 20):
                                    df.at[len(df)-1, 'start_buy'] = True
                                    df.at[len(df)-1, 'start_sell'] = False
                                    count = count + 1
                                    # print(abs(df['rsi'][i] - df['rsi'][j]),i,len(df)-1,tmp,'buy')
                            elif count == 1:
                                df.at[len(df)-1, 'start_buy'] = True
                                df.at[len(df)-1, 'start_sell'] = False
                                count = count + 1
                                

            elif (df['rsi'][i+1] > df['rsi_wma'][i+1]) and (printAngle((20, df['rsi'][i]),(25, df['rsi_ema'][i+1]),(25, df['rsi'][i+1])) > ANGLE):
                count = 0
                for j in range(i+1, len(df)-1):
                    if (df['rsi_start'][i] == True):
                        if(((df['rsi'][j] == df['rsi_ema'][j]) or ((df['rsi_ema'][j] - df['rsi'][j]<0) and (df['rsi_ema'][j+1] - df['rsi'][j+1]>0))) and (abs(df['rsi'][i] - df['rsi'][j]) > SLOPE)) and count<2:
                            if (count == 0):
                                tmp_s = df['rsi'][i]
                                tmp_s_index = 0
                                for k in range(i+1, j):
                                    
                                    if (df['rsi'][k] > df['rsi_ema'][k]):
                                        if (k>i+1) and (abs(df['rsi'][k] - df['rsi_wma'][k]) < 1):
                                            tmp_s = df['rsi'][i]
                                            break 
                                        tmp_s_index+=1
                                        tmp_s = df['rsi'][k]
                                    else:
                                        # print(tmp_s,df['timestamp'][i],'break')
                                        break
                                if (tmp_s - df['rsi'][i] > 18):
                                    df.at[j+1, 'start_sell'] = True
                                    df.at[j+1, 'start_buy'] = False
                                    # print(tmp_s_index)
                                    count = count + 1
                                    # print(abs(df['rsi'][i] - df['rsi'][j]),i,j,df['timestamp'][j],'sell')
                            elif count == 1:
                                df.at[j+1, 'start_sell'] = True
                                df.at[j+1, 'start_buy'] = False 
                                # print(abs(df['rsi'][i] - df['rsi'][j]),i,j,df['timestamp'][j], count,'sell')
                                count = count + 1      
                        elif (df['rsi'][j] < df['rsi_wma'][j]) or count == 2:
                            df.at[i, 'rsi_start'] = False 
                            count = 0
                        if(df['rsi'][len(df)-1] == df['rsi_ema'][len(df)-1]) or ((df['rsi_ema'][len(df)-2] - df['rsi'][len(df)-2]<0) and (df['rsi_ema'][len(df)-1] - df['rsi'][len(df)-1]>0)) and count<2 and j == len(df)-2:
                            if (count == 0):
                                tmp_s = df['rsi'][i]
                                tmp_s_index = 0
                                for k in range(i+1, len(df)-1):
                                    
                                    if (df['rsi'][k] > df['rsi_ema'][k]):
                                        if (k>i+1) and (abs(df['rsi'][k] - df['rsi_wma'][k]) < 1):
                                            tmp_s = df['rsi'][i]
                                            break 
                                        tmp_s_index+=1
                                        tmp_s = df['rsi'][k]
                                    else:
                                        break
                                if (tmp_s - df['rsi'][i] > 20):
                                    df.at[len(df)-1, 'start_sell'] = True
                                    df.at[len(df)-1, 'start_buy'] = False
                                    # print(tmp_s_index)
                                    count = count + 1
                                    # print(abs(df['rsi'][i] - df['rsi'][[len(df)-1]]),i,[len(df)-1],'sell')
                            elif count == 1:
                                df.at[len(df)-1, 'start_sell'] = True
                                df.at[len(df)-1, 'start_buy'] = False 
                                count = count + 1      
    return df

stoploss = 0
takeprofit = 0
rsi_tmp = 0
buy = False    
sell = False
count_buy = 0
count_sell = 0
# check buy sell signals
def check_buy_sell_signals(df):
    last_row_index = len(df.index) - 1
    global stoploss
    global takeprofit
    global rsi_tmp 
    global buy
    global sell
    global count_buy
    global count_sell

    if (exchange.fetch_balance()[SYMBOL_FREE]['free'] >= 0.001):
        if (df['start_buy'][last_row_index] == True) and ((count_buy == 0) or (count_buy == 1)):
            print('buy buy buy')
            order = exchange.create_market_buy_order(SYMBOL, 0.0005)
            print(order)
            rsi_tmp = df['rsi'][last_row_index]
            if (30 <= rsi_tmp <= 40):
                takeprofit = df['close'][last_row_index] + df['close'][last_row_index] * 0.08
            stoploss = df['close'][last_row_index] - df['close'][last_row_index] * 0.1
            buy = True
            count_buy+=1


        if ((df['close'][last_row_index] <= stoploss) and (stoploss != 0)) or ((df['close'][last_row_index] >= takeprofit) and (takeprofit != 0)) or ((rsi_tmp < 30 and (rsi_tmp != 0) and (df['rsi'][last_row_index] > 65))) or (((df['rsi'][last_row_index] == df['rsi_ema'][last_row_index])  or ((df['rsi'][last_row_index-1] > df['rsi_ema'][last_row_index-1]) and (df['rsi'][last_row_index] < df['rsi_ema'][last_row_index]))) and (df['rsi_wma'][last_row_index] < df['rsi_ema'][last_row_index]) and buy == True) and (count_buy != 0):
            print('sell')
            order = exchange.create_market_sell_order(SYMBOL, 0.0005)
            print(order)
            stoploss = 0
            takeprofit = 0
            rsi_tmp = 0    
            buy = False
            count_buy = 0


        if (df['start_sell'][last_row_index] == True) and ((count_sell == 0) or (count_sell == 1)):
            print('sell sell sell')
            order = exchange.create_market_sell_order(SYMBOL, 0.0005)
            print(order) 
            rsi_tmp = df['rsi'][last_row_index]
            stoploss = df['close'][last_row_index] + df['close'][last_row_index] * 0.1
            takeprofit = df['close'][last_row_index] - df['close'][last_row_index] * 0.2
            sell = True
            count_sell += 1


        if ((df['close'][last_row_index] >= stoploss) and (stoploss != 0)) or ((df['close'][last_row_index] <= takeprofit) and (takeprofit != 0)) or ((rsi_tmp >= 65 and rsi_tmp != 0) and (df['rsi'][last_row_index] <= 40)) or (((df['rsi'][last_row_index] == df['rsi_ema'][last_row_index])  or ((df['rsi'][last_row_index-1] < df['rsi_ema'][last_row_index-1]) and (df['rsi'][last_row_index] > df['rsi_ema'][last_row_index]))) and (df['rsi_wma'][last_row_index] > df['rsi_ema'][last_row_index]) and sell == True) and (count_sell != 0):
            print('buy')
            order = exchange.create_market_buy_order(SYMBOL, 0.0005)
            print(order)
            stoploss = 0
            takeprofit = 0
            rsi_tmp = 0   
            sell = False 
            count_sell = 0




def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    # order = exchange.create_order(symbol='BTC/USDT',type='market',amount=0.01,side='buy')
    # # print(order)
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIME_FRAME, limit=LIMIT)

    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'] , unit='ms')
    df['timestamp'] = df['timestamp'] + timedelta(hours=7)


    # rsi
    df['rsi'] = ta.RSI(df['close'], timeperiod=14)
    # wma of rsi
    df['rsi_wma'] = ta.WMA(df['rsi'], timeperiod=45)
    # ema of rsi
    df['rsi_ema'] = ta.EMA(df['rsi'], timeperiod=9)
    rsi_df =  rsi_signal(df)
    check_buy_sell_signals(rsi_df)
    rsi_df = pd.DataFrame(rsi_df, columns=['timestamp','start_buy', 'start_sell'])

    result = rsi_df[(rsi_df['start_buy'] == True) | (rsi_df['start_sell'] == True)]
    print(result)
# mỗi 2 giây chạy một lần  
schedule.every(5).seconds.do(run_bot)


while True:
    schedule.run_pending()
    # time sleep
    time.sleep(1)