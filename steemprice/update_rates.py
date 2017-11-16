from decimal import Decimal

import redis
import requests
import time

import settings


class BaseAdapter(object):
    def __init__(self, redis_conn):
        self.redis_conn = redis_conn
        self.provider_code = None

    def cache_key(self, pair):
        return ":".join([self.provider_code, pair])

    def set_rates(self):
        for pair, value in self.fetch_rates().items():
            self.redis_conn.set(
                self.cache_key(pair),
                value
            )

    def get_rate(self, pair):
        return self.redis_conn.get(self.cache_key(pair))

    def get_rates(self):
        rates = {}
        for pair in ["BTC-SBD", "BTC-STEEM"]:
            pair_rate = Decimal(self.get_rate(pair))
            rates[pair] = "%.8f" % pair_rate
            usd_pair_name = "USD-%s" % pair.split("-")[1]
            btc_usd_rate = Decimal(self.redis_conn.get('blockchain:BTC-USD'))
            rates[usd_pair_name] = "%.2f" % (btc_usd_rate * pair_rate)

        return rates


class PoloniexAdapter(BaseAdapter):
    def __init__(self, redis_conn):
        super(PoloniexAdapter, self).__init__(redis_conn)
        self.provider_code = "poloniex"

    def fetch_rates(self):
        r = requests.get(
            "https://poloniex.com/public?command=returnTicker").json()
        return {
            "BTC-SBD": Decimal(r["BTC_SBD"]["last"]),
            "BTC-STEEM": Decimal(r["BTC_STEEM"]["last"]),
        }


class BittrexAdapter(BaseAdapter):
    def __init__(self, redis_conn):
        super(BittrexAdapter, self).__init__(redis_conn)
        self.provider_code = "bittrex"

    def fetch_rates(self):
        rates = {}
        r = requests.get(
            "https://bittrex.com/api/v1.1/public/getticker?market=BTC-SBD").json()
        rates["BTC-SBD"] = Decimal(r["result"]["Last"])
        r = requests.get(
            "https://bittrex.com/api/v1.1/public/getticker?market=BTC-STEEM"
        ).json()
        rates["BTC-STEEM"] = Decimal(r["result"]["Last"])

        return rates


class BlockchainAdapter(BaseAdapter):
    def __init__(self, redis_conn):
        super(BlockchainAdapter, self).__init__(redis_conn)
        self.provider_code = "blockchain"

    def fetch_rates(self):
        r = requests.get("https://blockchain.info/ticker").json()
        rates = {"BTC-USD": "%.4f" % Decimal(r["USD"]["last"])}
        return rates


def update():
    redis_conn = redis.Redis(**settings.REDIS_INFO)
    while True:
        adapters = [
            PoloniexAdapter(redis_conn),
            BittrexAdapter(redis_conn),
            BlockchainAdapter(redis_conn),
        ]
        for adapter in adapters:
            adapter.set_rates()
        timestamp = str(int(time.time()))
        redis_conn.set("last_update", timestamp)
        print("Updated rates. Timestamp: %s" % timestamp)
        time.sleep(10)
