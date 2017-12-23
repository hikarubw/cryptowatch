import json
import time
import requests
from abc import ABCMeta
from collections import defaultdict
from cryptowatch.exception import CryptWatchApiException


class CryptoWatchApi(metaclass=ABCMeta):
    def __init__(self):
        self._latest_cost = None
        self._latest_remaining = None

    def _get(self, url, params=None):
        _RETRY_COUNT = 5
        _WAIT_TIME = 3
        _TOO_MATCH = 'too match execute api'
        latest_exception_type = None
        for count in range(_RETRY_COUNT):
            api_response = requests.get(url, params=params)
            if api_response.status_code in [200, 400]:
                api_result = json.loads(api_response.text)
                self._latest_cost = api_result['allowance']['cost']
                self._latest_cost = api_result['allowance']['remaining']
                if api_response.status_code == 200:
                    return api_result['result']
                CryptWatchApiException(api_result['error'])
            time.sleep(_WAIT_TIME)
            if api_response.status_code == 429:
                latest_exception_type = _TOO_MATCH
                continue
            latest_exception_type = api_response.status_code
            break
        if latest_exception_type == _TOO_MATCH:
            CryptWatchApiException(_TOO_MATCH)
        raise CryptWatchApiException('status code:{}'.format(latest_exception_type))

    @property
    def latest_cost(self):
        return self._latest_cost

    @property
    def latest_remaining(self):
        return self._latest_remaining


class CryptoWatchExchange(CryptoWatchApi):
    def __init__(self, only_active=True):
        super().__init__()
        self._only_active = only_active
        self._market_info = defaultdict(list)
        for market in self._get_market_info():
            self._market_info[market['exchange']].append(market)

    def _get_market_info(self):
        market_info_result = self._get('https://api.cryptowat.ch/markets')
        for one_data in market_info_result:
            if self._only_active and one_data['active'] is False:
                continue
            yield one_data

    def get_market_info(self, exchange, pair):
        info = self._market_info[exchange]
        if len(info) == 0:
            return None
        result = list(filter(lambda x: x['pair'] == pair, info))
        if len(result) == 0:
            return None
        return result[0]

    def get_market_info_detail(self, exchange, pair):
        info = self.get_market_info(exchange, pair)
        if info is None:
            return None
        return self._get(info['route'])

    def exchanges(self):
        return list(self._market_info.keys())

    def pairs(self, exchange):
        return [market['pair'] for market in self._market_info[exchange]]


class CryptoWatchMarket(CryptoWatchApi):
    def __init__(self, exchange_name, pair):
        super().__init__()
        self._exchange_name = exchange_name
        self._pair = pair
        self._route = self._get_routes()

    def _get_routes(self):
        market_info = CryptoWatchMarket().get_market_info_detail(self._exchange_name, self._pair)
        if market_info is None:
            return defaultdict(str)
        return market_info['routes']

    def get_price(self):
        return self._get(self._route['price'])['price']

    def get_summary(self):
        return self._get(self._route['summary'])

    def get_order_book(self):
        def convert(data):
            result = []
            for one_data in data:
                result.append(
                    {
                        'price': one_data[0],
                        'amount': one_data[1]
                    }
                )
            return result

        api_result = self._get(self._route['orderbook'])
        return {
            'asks': convert(api_result['asks']),
            'bids': convert(api_result['bids'])
        }

    def get_trade(self, since=None, limit=None):
        def get_params():
            params = {}
            if since is not None:
                params['since'] = since
            if limit is not None:
                params['limit'] = limit
            return params

        api_result = self._get(self._route['trades'], get_params())
        trade_result = []
        for trade in api_result:
            trade_result.append(
                {
                    'id': trade[0],
                    'timestamp': trade[1],
                    'price': trade[2],
                    'amount': trade[3]
                }
            )
        return trade_result

    def get_ohlc(self, before=None, after=None, period=None):
        def get_params():
            params = {}
            if period is not None:
                params['period'] = period
            if after is not None:
                params['after'] = after
            if before is not None:
                params['before'] = before
            return params

        api_result = self._get(self._route['ohlc'], get_params())
        ohlc_result = defaultdict(list)
        for period, records in api_result.items():
            for record in records:
                ohlc_result[period].append(
                    {
                        'close_time': record[0],
                        'open_price': record[1],
                        'high_price': record[2],
                        'low_price': record[3],
                        'close_price': record[4],
                        'volume': record[5]
                    }
                )
        return ohlc_result
