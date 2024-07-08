import ccxt
import time
import logging
import creds
import numpy as np

# Replace these with your actual API keys and password
api_key = creds.api_key
secret = creds.secret
password = creds.password

# Initialize logging
logging.basicConfig(filename='trading_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    logging.info(message)
    print(message)

# Trade trigger logging
canTrade = False
buyTrade = False
sellTrade = False
leverage = 64
numSidesTested = 0
priceSet = False

# Initialize the KuCoin Futures exchange object
exchange = ccxt.kucoinfutures({
    'apiKey': api_key,
    'secret': secret,
    'password': password,
    'enableRateLimit': True,  # This enables rate limiting, which protects your account
    'options': {
        'defaultType': 'future',  # Specify the default market type (spot or future)
    }
})



def get_high_low_and_atr(symbol, timeframe, n):
    try:
        # Load markets
        exchange.load_markets()

        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=n + 1)  # Fetch one more candle for accurate ATR calculation

        # Extract the High, Low, and Close prices from the OHLCV data
        highs = [candle[2] for candle in ohlcv]  # High prices
        lows = [candle[3] for candle in ohlcv]   # Low prices
        closes = [candle[4] for candle in ohlcv] # Close prices

        # Find the highest and lowest prices in the range
        highest_price = max(highs[-n:])
        lowest_price = min(lows[-n:])

        # Calculate True Range (TR)
        trs = [highs[i] - lows[i] for i in range(1, len(ohlcv))]
        trs += [abs(highs[i] - closes[i-1]) for i in range(1, len(ohlcv))]
        trs += [abs(lows[i] - closes[i-1]) for i in range(1, len(ohlcv))]

        # Calculate ATR
        atr = np.mean(trs[-n:])

        # calculate stops
        highest_stop = highest_price - (atr*3)
        lowest_stop = lowest_price + (atr*3)


        return highest_price, highest_stop, lowest_price, lowest_stop, atr

    except ccxt.NetworkError as e:
        print(f'Network error: {e}')
        return None, None, None

    except ccxt.ExchangeError as e:
        print(f'Exchange error: {e}')
        return None, None, None

    except Exception as e:
        print(f'Error: {e}')
        return None, None, None


# User-defined input variables

# User input
symbol = 'ETHUSDTM'
timeframe = '1m'  # You can change this to any valid timeframe, e.g., '1m', '5m', '1d'
n = int(input("Enter the number of candles: "))
highest, highest_stop, lowest, lowest_stop, atr = get_high_low_and_atr(symbol, timeframe, n)


buyPrice = 0  # User input for buy price
sellPrice = 0  # User input for sell price
amount = 1  # User input for amount to trade

# Function to fetch the current price of a symbol
def fetch_current_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']  # Last traded price for the symbol
    except ccxt.NetworkError as e:
        log(f'Network error: {e}')
    except ccxt.ExchangeError as e:
        log(f'Exchange error: {e}')
    except Exception as e:
        log(f'Error: {e}')
    return None

# Function to execute a market buy order
def execute_market_buy(symbol, amount):
    try:
        order = exchange.createOrder(symbol, 'market', 'buy', amount, params={'leverage': leverage})
        log(f'Buy order executed for {amount} {symbol}. Order details: {order}')
        return True
    except ccxt.NetworkError as e:
        log(f'Network error: {e}')
    except ccxt.ExchangeError as e:
        log(f'Exchange error: {e}')
    except Exception as e:
        log(f'Error: {e}')
    return False

# Function to execute a market sell order
def execute_market_sell(symbol, amount):
    try:
        order = exchange.createOrder(symbol, 'market', 'sell', amount, params={'leverage': leverage})
        log(f'Sell order executed for {amount} {symbol}. Order details: {order}')
        return True
    except ccxt.NetworkError as e:
        log(f'Network error: {e}')
    except ccxt.ExchangeError as e:
        log(f'Exchange error: {e}')
    except Exception as e:
        log(f'Error: {e}')
    return False

# Function to close all open positions at market price
def close_all_positions():
    global posCount
    try:
        positions = exchange.fetch_positions()

        if not positions:
            log('No open positions to close.')
            posCount = 0
            return

        log(f'Closing {len(positions)} positions...')

        for position in positions:
            if position['symbol'] == symbol:
                amount = position['contracts']
                if amount > 0:
                    order = exchange.create_order(symbol, 'market', 'sell', amount)
                else:
                    order = exchange.create_order(symbol, 'market', 'buy', -amount)
                log(f'Closed position for {symbol} with amount {amount}. Order details: {order}')

        log('All positions closed.')
    except ccxt.NetworkError as e:
        log(f'Network error: {e}')
    except ccxt.ExchangeError as e:
        log(f'Exchange error: {e}')
    except Exception as e:
        log(f'Error: {e}')




if highest is not None and lowest is not None and atr is not None:
    print(f'Highest price over the last {n} candles: {highest}')
    print(f'Highest stop price over the last {n} candles: {highest_stop}')
    print(f'Lowest price over the last {n} candles: {lowest}')
    print(f'Lowest stop price over the last {n} candles: {lowest_stop}')
    print(f'ATR over the last {n} candles: {atr}')
    

    # Main loop to fetch price and execute trades based on user-defined conditions
    while True:
        current_price = fetch_current_price(symbol)

        if current_price is not None:
            log(f'Current price of {symbol}: {current_price}')

            # checks to prime trade high
            if not priceSet and current_price < highest and current_price > highest_stop:
                buyPrice = highest
                sellPrice = highest_stop
                canTrade = True
                priceSet = True

            # checks to prime trade low
            if not priceSet and current_price > lowest and current_price < lowest_stop:
                buyPrice = lowest_stop
                sellPrice = lowest
                canTrade = True
                priceSet = True

            # Check buy condition
            if canTrade and current_price > buyPrice and not buyTrade:
                close_all_positions()                
                time.sleep(2)  # Delay after closing positions before opening a new buy position
                numSidesTested+=1
                if posCount < 3:
                    # Open a new buy position
                    execute_market_buy(symbol, amount)
                    if numSidesTested > 1:
                        time.sleep(3)
                        execute_market_buy(symbol, amount)
                    sellTrade = False
                    buyTrade = True
                    log('Buy trade executed.')

            # Check sell condition
            if canTrade and current_price < sellPrice and not sellTrade:
                close_all_positions()
                time.sleep(2)  # Delay after closing positions before opening a new sell position
                numSidesTested+=1
                if posCount < 3:
                    # Open a new sell position
                    execute_market_sell(symbol, amount)
                    if numSidesTested > 1:
                        time.sleep(3)
                        execute_market_sell(symbol, amount)
                    buyTrade = False
                    sellTrade = True
                    log('Sell trade executed.')

        time.sleep(0.5)  # Sleep for 0.5 seconds before fetching price again
