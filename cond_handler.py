import asyncio
from exchange_listeners.binance_listener import BinanceListener

AVAILABLE_INTERVAL = {
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "6h": 360,
    "12h": 720,
    "1d": 1440
}

client_binance = BinanceListener()

class ConditionHandler:
    def __init__(self):
        self.symbols = ""
        self.interval = ""
        self.limit = None
        self.threshold = None
        self.threshold_period: int = None


    def delta_calculate(self, data_last, data_first) -> float:
        delta = (float(data_last) - float(data_first)) / float(data_last)
        return delta


    async def is_signal(self, symbols: list, threshold_period: int = 15, interval: str = "5m", threshold: float = 0.04):
        self.symbols = symbols
        self.interval = interval.lower()
        self.threshold_period = threshold_period
        self.limit = int(self.threshold_period / AVAILABLE_INTERVAL[self.interval])
        self.threshold = threshold
        signal_coins = []

        print("threshold_period = ",  self.threshold_period)
        print(f"threshold = {self.threshold*100}%")

        tasks = [client_binance.fetch_oi(symbol.upper(), self.interval, self.limit) for symbol in self.symbols]
        coins = await asyncio.gather(*tasks)

        for coin in coins:
            for i in range(1,len(coin)):
                delta_oi = self.delta_calculate(coin[i]['OpenInterest'], coin[0]['OpenInterest']) #(float(coin[i]['OpenInterest']) - float(coin[0]['OpenInterest'])) / float(coin[i]['OpenInterest'])
                formatted_delta_oi = f"{delta_oi*100:.2f}%"

                if delta_oi > self.threshold:

                    start_date = coin[0]['timestamp']
                    end_date = coin[i]['timestamp']

                    signal_coin_price_volume = await client_binance.fetch_ohlcv(coin[0]['symbol'], self.interval, start_date, end_date)

                    delta_price = self.delta_calculate(signal_coin_price_volume[-1]['close'], signal_coin_price_volume[0]['close'])
                    delta_volume = self.delta_calculate(signal_coin_price_volume[-1]['volume'], signal_coin_price_volume[0]['volume'])
                    formatted_delta_price = f"{delta_price * 100:.2f}%"
                    formatted_delta_volume = f"{delta_volume * 100:.2f}%"

                    delta_time = coin[i]['datetime'] - coin[0]['datetime']
                    delta_minutes = delta_time.total_seconds() / 60

                    is_signal_coin = {
                        'exchange': 'Binance',
                        'symbol': coin[i]['symbol'],
                        'timestamp': coin[i]['timestamp'],
                        'datetime': coin[i]['datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                        'delta_oi_%': formatted_delta_oi,
                        'delta_price_%': formatted_delta_price,
                        'delta_volume_%': formatted_delta_volume,
                        'delta_time_minutes': delta_minutes,
                    }
                    signal_coins.append(is_signal_coin)
                    break

        return signal_coins



