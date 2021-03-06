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


LIMIT = 50

# góc tõe ra giữa rsi và ema khi 3 đường giao nhau
ANGLE = 10

# số lượng coin khi vào lệnh bán và mua
AMOUNT = 0.0005

# khung giờ
TIME_FRAME = '5m'

# độ chênh lệch giữa rsi tại điểm giao nhau và rsi tại điểm vào
SLOPE = 10


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
        if (((abs(df['rsi'][i] - df['rsi_wma'][i]) < 3.5) and (abs(df['rsi'][i] - df['rsi_ema'][i])) < 3.5) or ((abs(tmp - df['rsi_wma'][i]) < 3.5) and (abs(tmp - df['rsi_ema'][i]) < 3.5))) and (abs(df['rsi_ema'][i] - df['rsi_wma'][i]) < 3.5) :
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
                                        tmp = df['rsi'][k]
                                    else:
                                        break
                                    if(abs(df['rsi'][k] - df['rsi_ema'][k]) < 2):
                                        tmp_index +=1
                                if (df['rsi'][i] - tmp > 20) and (tmp_index<3):
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
                                        tmp = df['rsi'][k]
                                    else:
                                        break
                                    if(abs(df['rsi'][k] - df['rsi_ema'][k]) < 2):
                                        tmp_index +=1
                                if (df['rsi'][i] - tmp > 20) and (tmp_index<3):
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
                                        tmp_s = df['rsi'][k]
                                    else:
                                        # print(tmp_s,df['timestamp'][i],'break')
                                        break
                                    if(abs(df['rsi'][k] - df['rsi_ema'][k]) < 2):
                                        tmp_s_index +=1
                                if (tmp_s - df['rsi'][i] > 20) and (tmp_s_index<3):
                                    df.at[j+1, 'start_sell'] = True
                                    df.at[j+1, 'start_buy'] = False
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
                                        tmp_s = df['rsi'][k]
                                    else:
                                        break
                                    if(abs(df['rsi'][k] - df['rsi_ema'][k]) < 2):
                                        tmp_s_index +=1
                                if (tmp_s - df['rsi'][i] > 20) and (tmp_s_index<3):
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

stoploss_sell = 0
takeprofit_sell = 0
stoploss_buy = 0
takeprofit_buy = 0
rsi_tmp_buy = 0
rsi_tmp_sell = 0
buy = False    
sell = False
count_buy = 0
count_sell = 0
check_buy_signal = 0
check_sell_signal = 0
# check buy sell signals
def check_buy_sell_signals(df):
    last_row_index = len(df.index) - 1
    global stoploss_buy
    global takeprofit_buy
    global stoploss_sell
    global takeprofit_sell
    global rsi_tmp_buy
    global rsi_tmp_sell 
    global buy
    global sell
    global count_buy
    global count_sell
    global check_buy_signal
    global check_sell_signal

    # check số dư của tài khoản
    if (exchange.fetch_balance()[SYMBOL_FREE]['free'] >= 2 * AMOUNT):
        if (df['start_buy'][last_row_index] == True) and ((count_buy == 0) or (count_buy == 1)) and (check_buy_signal != df['timestamp'][last_row_index]):
            print('buy buy buy')
            order = exchange.create_market_buy_order(SYMBOL, AMOUNT)
            print(order)
            rsi_tmp_buy = (df['rsi'][last_row_index-1]+df['rsi'][last_row_index])/2
            if (30 <= rsi_tmp_buy <= 40):
                takeprofit_buy = df['close'][last_row_index] + df['close'][last_row_index] * 0.08
            stoploss_buy = df['close'][last_row_index] - df['close'][last_row_index] * 0.1
            if sell == True:
                sell = False
            buy = True
            count_buy+=1
            check_buy_signal = df['timestamp'][last_row_index]


        if ((df['close'][last_row_index] <= stoploss_buy) and (stoploss_buy != 0)) or ((df['close'][last_row_index] >= takeprofit_buy) and (takeprofit_buy != 0)) or ((rsi_tmp_buy < 30 and (rsi_tmp_buy != 0) and (df['rsi'][last_row_index] > 65))) or (((df['rsi'][last_row_index] == df['rsi_ema'][last_row_index])  or ((df['rsi'][last_row_index-1] > df['rsi_ema'][last_row_index-1]) and (df['rsi'][last_row_index] < df['rsi_ema'][last_row_index]))) and (df['rsi_wma'][last_row_index] < df['rsi_ema'][last_row_index])) and (buy == True) and (count_buy != 0):
            print('sell')
            if(count_buy == 2):
                order = exchange.create_market_sell_order(SYMBOL, 2*AMOUNT)
                print(order)
            elif(count_buy == 1):
                order = exchange.create_market_sell_order(SYMBOL, AMOUNT)
                print(order)
            stoploss_buy = 0
            takeprofit_buy = 0
            rsi_tmp_buy = 0    
            buy = False
            count_buy = 0
            check_buy_signal = 0


        if (df['start_sell'][last_row_index] == True) and ((count_sell == 0) or (count_sell == 1)) and (check_sell_signal != df['timestamp'][last_row_index]):
            print('sell sell sell')
            order = exchange.create_market_sell_order(SYMBOL, AMOUNT)
            print(order) 
            rsi_tmp_sell = (df['rsi'][last_row_index]+ df['rsi'][last_row_index-1])/2
            stoploss_sell = df['close'][last_row_index] + df['close'][last_row_index] * 0.1
            takeprofit_sell = df['close'][last_row_index] - df['close'][last_row_index] * 0.2
            if buy == True:
                buy = False
            sell = True
            count_sell += 1
            check_sell_signal = df['timestamp'][last_row_index]


        if ((df['close'][last_row_index] >= stoploss_sell) and (stoploss_sell != 0)) or ((df['close'][last_row_index] <= takeprofit_sell) and (takeprofit_sell != 0)) or ((rsi_tmp_sell >= 65 and rsi_tmp_sell != 0) and (df['rsi'][last_row_index] <= 40)) or (((df['rsi'][last_row_index] == df['rsi_ema'][last_row_index])  or ((df['rsi'][last_row_index-1] < df['rsi_ema'][last_row_index-1]) and (df['rsi'][last_row_index] > df['rsi_ema'][last_row_index]))) and (df['rsi_wma'][last_row_index] > df['rsi_ema'][last_row_index])) and (sell == True) and (count_sell != 0):
            print('buy')
            if (count_sell == 2):
                order = exchange.create_market_buy_order(SYMBOL, 2*AMOUNT)
                print(order)
            elif (count_sell == 1):
                order = exchange.create_market_buy_order(SYMBOL, AMOUNT)
                print(order)
            stoploss_sell = 0
            takeprofit_sell = 0
            rsi_tmp_sell = 0   
            sell = False 
            count_sell = 0
            check_sell_signal = 0




def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    # order = exchange.create_order(symbol='BTC/USDT',type='market',amount=0.01,side='buy')
    # # print(order)
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIME_FRAME, limit=LIMIT)

    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'] , unit='ms')
    df['datetime'] = df['datetime'] + timedelta(hours=7)


    # rsi
    df['rsi'] = ta.RSI(df['close'], timeperiod=14)
    # wma of rsi
    df['rsi_wma'] = ta.WMA(df['rsi'], timeperiod=45)
    # ema of rsi
    df['rsi_ema'] = ta.EMA(df['rsi'], timeperiod=9)
    rsi_df =  rsi_signal(df)
    check_buy_sell_signals(rsi_df)
    rsi_df = pd.DataFrame(rsi_df, columns=['datetime','start_buy', 'start_sell'])

    result = rsi_df[(rsi_df['start_buy'] == True) | (rsi_df['start_sell'] == True)]
    # print(result)
# mỗi 5 giây chạy một lần  
schedule.every(5).seconds.do(run_bot)


while True:
    schedule.run_pending()
    # time sleep
    time.sleep(1)