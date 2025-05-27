# cond_handler.py

import asyncio
from exchange_listeners.base_listener import BaseExchangeListener
from db.bd import add_signal_in_db, count_symbol_in_db, add_history_in_db, get_historical_oi, add_signal_in_total_db

AVAILABLE_INTERVAL = {
    "5": 5,
    "15": 15,
    "30": 30
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
        self.symbols = symbols#[:10]
        self.interval = interval
        self.threshold_period = threshold_period
        self.limit = int(self.threshold_period / AVAILABLE_INTERVAL[self.interval])
        self.threshold = threshold
        start_date: int = None
        end_date: int = None
        signal_coins = []
        historical_oi = []

        print("threshold_period = ",  self.threshold_period)
        print(f"threshold = {self.threshold*100}%")

        # Скачиваем с биржи данные по OI
        tasks = [self.client.fetch_oi(symbol.upper(), self.interval, self.limit) for symbol in self.symbols]
        coins = await asyncio.gather(*tasks)

        for coin in coins:
            coin = self.sort_by_timestamp(coin)
            flag = True
            #print("coin = ", coin)

            for i in range(1,len(coin)):
                # Находим изменение OI
                historical_oi.clear()  # если выполняется условие сигнала, очищаем словарь
                exchange_name = coin[0]['exchange']
                symbol = coin[0]['symbol']

                delta_oi = self.delta_calculate(coin[i]['open_interest'], coin[0]['open_interest'])
                formatted_delta_oi = f"{delta_oi*100:.2f}%"

                if flag:
                    # Собираю свою историю по каждому символу
                    timestamp = coin[-1]['timestamp']
                    open_interest = coin[-1]['open_interest']
                    await add_history_in_db(symbol, exchange_name, timestamp, open_interest)
                    flag = False

                #print('coin[i] = ', coin[i])

                # Сравниваем изменение OI с пороговым значением
                if delta_oi > self.threshold:

                    count_signal = 0  # количество сигналов за последние сутки
                    start_date = coin[0]['timestamp']
                    end_date = coin[i]['timestamp']

                    # Скачиваем исторические данные по цене и объему на периоде, где выполнилось условие по OI
                    signal_coin_price_volume = await self.client.fetch_ohlcv(coin[0]['symbol'], start_date, end_date, str(self.interval))
                    print("signal_coin_price_volume = ",signal_coin_price_volume)
                    # Если данные пустые или пришла ошибка, пропускаем итерацию
                    if not signal_coin_price_volume or len(signal_coin_price_volume) < 2:
                        continue

                    # Добавляем данные о сигнале в БД
                    await add_signal_in_db(symbol, exchange_name, self.threshold_period, self.threshold, delta_oi, start_date)
                    # Подсчитываем количество сигналов в БД
                    count_signal = await count_symbol_in_db(symbol, exchange_name, self.threshold_period, self.threshold)
                    print("count_signal первый вызов = ",count_signal)



                    # Если единственный сигнал, открываем суточную историю и подсчитываем количество сигналов.
                    if count_signal == 1:
                        new_count_signal = 0
                        historical_oi = await get_historical_oi(symbol, exchange_name, end_date)
                        print("Выполнилось условие if count_signal == 1:")
                        print('historical_oi = ',historical_oi)
                        print('len(historical_oi) = ', len(historical_oi))

                        for j in range(len(historical_oi)-self.limit+1):
                            for k in range(1, self.limit):
                                delta_historical_oi = self.delta_calculate(historical_oi[j]['open_interest'], historical_oi[j-k]['open_interest'])
                                if delta_historical_oi > self.threshold:
                                    new_count_signal += 1
                                    print("new_count_signal в цикле = ", count_signal)
                                    await add_signal_in_db(symbol, exchange_name, self.threshold_period, self.threshold,
                                                           delta_historical_oi, historical_oi[j]['timestamp'])
                                    break
                        if new_count_signal > 0:
                            count_signal = new_count_signal



                    delta_price = self.delta_calculate(signal_coin_price_volume[-1]['close'], signal_coin_price_volume[0]['close'])
                    delta_volume = self.delta_calculate(signal_coin_price_volume[-1]['volume'], signal_coin_price_volume[0]['volume'])
                    formatted_delta_price = f"{delta_price * 100:.2f}%"
                    formatted_delta_volume = f"{delta_volume * 100:.2f}%"

                    delta_time = coin[i]['datetime'] - coin[0]['datetime']
                    delta_minutes = delta_time.total_seconds() / 60

                    # формируем выходные данные по конкретному сигналу
                    is_signal_coin = {
                        'exchange': exchange_name,
                        'symbol': symbol,
                        'timestamp': coin[i]['timestamp'],
                        'datetime': coin[i]['datetime'],
                        'delta_oi_%': formatted_delta_oi,
                        'delta_price_%': formatted_delta_price,
                        'delta_volume_%': formatted_delta_volume,
                        'delta_time_minutes': delta_minutes,
                        'count_signal_24h': count_signal,
                        'threshold_period': self.threshold_period,
                        'threshold': self.threshold
                    }

                    # Добавляем в долговременную БД запись о сигнале
                    await add_signal_in_total_db(symbol, exchange_name, coin[i]['timestamp'], delta_oi,
                                                     delta_price, delta_volume,
                                                     self.threshold_period, self.threshold)

                    # Собираем все сигналы по одной бирже в одном списке
                    signal_coins.append(is_signal_coin)
                    break

        return signal_coins



