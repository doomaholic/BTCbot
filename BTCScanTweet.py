#
# This is the same program  as BTCScan but tweets every 5 minutes if price is oversold
#
from binance.client import Client
from finta import TA
from datetime import datetime, date
import time as t
import creds # Binance API key
import ticker_list2 # List of all tickers on binance. 
import pandas as pd
import numpy as np
import datetime
import tweepy


while True:
    
    # Set up binance API
    api_key = creds.APIkey
    api_secret = creds.SecretKey
    client = Client(api_key, api_secret)

    # Set up tweepy API
    auth = tweepy.OAuthHandler(creds.consumer_key, creds.consumer_secret)
    auth.set_access_token(creds.access_token, creds.access_token_secret)
    api = tweepy.API(auth)

    # Gets all symbol tickers into a list. 
    tickers = client.get_orderbook_tickers() #All tickers and quotes
    x=0 #iter
    complete_ticker_list = []
    for i in tickers: #for each stock in tickers, print only the ticker value
        y = tickers[x]
        x+=1
        symbol = y['symbol']
        complete_ticker_list.append(symbol)

    #Function to get ohlc values for a cryptocurrency on binance, and calculate if its above 1 or below 0 on %B
    def create_db(stock):
        open_val = []
        high_val = []
        low_val = []
        close_val = []
        time_val = []                                                         #KLINE_INTERVAL_15MINUTE
        ticker = []                                                           #KLINE_INTERVAL_1DAY
                                                                              #KLINE_INTERVAL_4HOUR
        for kline in client.get_historical_klines_generator(f"{stock}", Client.KLINE_INTERVAL_15MINUTE, "25 hours ago UTC"):
            
            #Code that converts unix timestamp to readable output
            timestamp = kline[0] #UTC time code
            timestamp = timestamp / 1000 #divides by 1000 because timestamp expects time in seconds but it comes in milliseconds and was giving the wrong date
            timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            time_val.append(timestamp)

            #Adds ohlc values to lists
            open_val.append(float(kline[1]))
            high_val.append(float(kline[2]))
            low_val.append(float(kline[3]))
            close_val.append(float(kline[4]))
            ticker.append(stock)
            
        # Combines ohlc value lists into one object then creates a pandas dataframe with that data.
        zippedList = list(zip(open_val, high_val, low_val, close_val))
        df = pd.DataFrame(zippedList, columns = ['open' , 'high', 'low', 'close'])
        
        # %B indicator added to DF
        bb = TA.PERCENT_B(df)
        bb = np.nan_to_num(bb) #replaces NaN values with 0.0 
        df["%BB"] = bb #Adds %b value column to df
        trade_signal = [] 

        for i in bb:
                try:
                    if i == 0:
                        trade_signal.append(''),              
                    elif i > 1:
                        trade_signal.append(''),               
                    elif i < 0:
                        trade_signal.append('Oversold'),    
                    elif i <= 1 and i >= 0:
                        trade_signal.append(''),
                except KeyError:
                    print(f"Incomplete data for {i}, KeyError.")
                
        #Adds trade column to df
        df['Trade'] = pd.DataFrame(trade_signal)

        # Insert date and ticker to front of DF
        df.insert(0,"Date",time_val)
        df.insert(1,"Ticker",ticker)

        # Format for console, prints dataframe
        pd.set_option('display.width', None)
        pd.set_option('display.max_rows', None)
        
        # Iterates through rows and looks for oversold tickers
        tail = df.tail(1)
        print(f"{tail}\n") # Shows the last db row of each stock (last day of the 100 day period)
        tickerx = df['Ticker']
        signal = df['Trade']
        datex = df['Date']
        price = df['close']
        var = signal.tail(1)
        booly = var.str.contains('Oversold')
        
        try:
            if booly[99] == True:
                tweet = f"\n{datex[99]} - {tickerx[99]} - OVERSOLD\n"
                print(tweet)
                api.update_status(tweet)
        except KeyError:
            print(f"Incomplete data for {tickerx} KeyError at line 99")
        t.sleep(300) #300 = 5 minutes
        
    # Method to feed ticker into main function
    def feed_ticker(complete_ticker_list2):
        for i in ticker_list2.ticker_list2:
             create_db(i)

    #Method that starts the program
    feed_ticker(complete_ticker_list)
