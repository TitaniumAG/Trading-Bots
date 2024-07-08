import ccxt
import creds
import numpy as np

# Replace these with your actual API keys and password
api_key = creds.api_key
secret = creds.secret
password = creds.password

# Initialize the KuCoin Futures exchange object
exchange = ccxt.kucoinfutures({
    'apiKey': api_key,
    'secret': secret,
    'password': password,
    'enableRateLimit': True,  # This enables rate limiting, which protects your account
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

# User input
symbol = 'ETHUSDTM'
timeframe = '1m'  # You can change this to any valid timeframe, e.g., '1m', '5m', '1d'
n = int(input("Enter the number of candles: "))

highest, highest_stop, lowest, lowest_stop, atr = get_high_low_and_atr(symbol, timeframe, n)

if highest is not None and lowest is not None and atr is not None:
    print(f'Highest price over the last {n} candles: {highest}')
    print(f'Highest stop price over the last {n} candles: {highest_stop}')
    print(f'Lowest price over the last {n} candles: {lowest}')
    print(f'Lowest stop price over the last {n} candles: {lowest_stop}')
    print(f'ATR over the last {n} candles: {atr}')
