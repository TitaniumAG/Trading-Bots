import ccxt
import time
import logging
import creds

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
posCount = 2

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

# User-defined input variables
symbol = 'ETHUSDTM'
buyPrice = float(input("Enter buy price: "))  # User input for buy price
sellPrice = float(input("Enter sell price: "))  # User input for sell price
amount = float(input("Enter amount to trade: "))  # User input for amount to trade

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

# Main loop to fetch price and execute trades based on user-defined conditions
while True:
    current_price = fetch_current_price(symbol)

    if current_price is not None:
        log(f'Current price of {symbol}: {current_price}')

        if current_price < buyPrice and current_price > sellPrice:
            canTrade = True

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
