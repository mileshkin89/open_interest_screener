import asyncio
from exchange_listeners.base_listener import BaseExchangeListener

AVAILABLE_INTERVAL = {
    "5": 5,
    "15": 15,
    "30": 30,
    # "1h": 60,
    # "2h": 120,
    # "4h": 240,
    # "6h": 360,
    # "12h": 720,
    # "1d": 1440
}


class ConditionHandler:
    def __init__(self):
        self.client: BaseExchangeListener = None
        self.symbols = ""
        self.interval = ""
        self.limit = None
        self.threshold = None
        self.threshold_period: int = None


    def set_client(self, client: BaseExchangeListener):
        self.client = client

    def sort_by_timestamp(self, coin_list: list[dict]) -> list[dict]:
        return sorted(coin_list, key=lambda x: x['timestamp'])

    def delta_calculate(self, data_last, data_first) -> float:
        delta = (float(data_last) - float(data_first)) / float(data_last)
        return delta


    async def is_signal(self, symbols: list, threshold_period: int = 15, interval: str = "5", threshold: float = 0.04):
        self.symbols = symbols#[:5]
        self.interval = interval
        self.threshold_period = threshold_period
        self.limit = int(self.threshold_period / AVAILABLE_INTERVAL[self.interval])
        self.threshold = threshold
        signal_coins = []

        print("threshold_period = ",  self.threshold_period)
        print(f"threshold = {self.threshold*100}%")

        tasks = [self.client.fetch_oi(symbol.upper(), self.interval, self.limit) for symbol in self.symbols]
        coins = await asyncio.gather(*tasks)

        for coin in coins:
            coin = self.sort_by_timestamp(coin)
            #print("coin = ", coin)

            for i in range(1,len(coin)):
                delta_oi = self.delta_calculate(coin[i]['OpenInterest'], coin[0]['OpenInterest'])
                formatted_delta_oi = f"{delta_oi*100:.2f}%"

                if delta_oi > self.threshold:

                    start_date = coin[0]['timestamp']
                    end_date = coin[i]['timestamp']
                    exchange_name = coin[i]['exchange']

                    signal_coin_price_volume = await self.client.fetch_ohlcv(coin[0]['symbol'], start_date, end_date, str(self.interval))

                    print("signal_coin_price_volume = ",signal_coin_price_volume)

                    if signal_coin_price_volume and len(signal_coin_price_volume) >= 2:
                        delta_price = self.delta_calculate(signal_coin_price_volume[-1]['close'], signal_coin_price_volume[0]['close'])
                        delta_volume = self.delta_calculate(signal_coin_price_volume[-1]['volume'], signal_coin_price_volume[0]['volume'])
                        formatted_delta_price = f"{delta_price * 100:.2f}%"
                        formatted_delta_volume = f"{delta_volume * 100:.2f}%"

                        delta_time = coin[i]['datetime'] - coin[0]['datetime']
                        delta_minutes = delta_time.total_seconds() / 60

                        is_signal_coin = {
                            'exchange': exchange_name,
                            'symbol': coin[i]['symbol'],
                            'timestamp': coin[i]['timestamp'],
                            'datetime': coin[i]['datetime'],
                            'delta_oi_%': formatted_delta_oi,
                            'delta_price_%': formatted_delta_price,
                            'delta_volume_%': formatted_delta_volume,
                            'delta_time_minutes': delta_minutes,
                        }
                        signal_coins.append(is_signal_coin)
                    break

        return signal_coins



