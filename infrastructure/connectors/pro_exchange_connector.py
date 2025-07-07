import json

import ccxt.pro as ccxtpro

class CcxtProMarketDataConnector:
    def __init__(self, exchange_name="binance", use_sandbox=False):
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox
        self.config = None
        self._load_config()
        self.client = self._init_exchange_client()

    def _load_config(self):

        with open(r'F:\HOME\new_autotrade\config\config.json', 'r') as f:
            config = json.load(f)

        if self.use_sandbox:
            pss = r'F:\HOME\new_autotrade\binance_keys\test-prv-key.pem'
            with open(pss, 'r') as f:
                private_key_pem = f.read()
            config = {
                "binance": {
                    "sandbox": {
                        'apiKey': '3RLY68IYS76Uz3cetlQg2IsJnfkZXxUbohJ6sDv5gCdpHbnJ5vzKcA2BdDmz3pNm',
                        'privateKey': private_key_pem,
                    }
                }
            }

        self.config = config[self.exchange_name]['sandbox' if self.use_sandbox else 'production']

    def _init_exchange_client(self):
        exchange_class = getattr(ccxtpro, self.exchange_name)

        settings = {
            'apiKey': self.config.get('apiKey', ''),
            'privateKey': self.config.get('privateKey', ''),  # или 'secret'
            'enableRateLimit': True,
            'newUpdates': True,
            'options': {
                'defaultType': 'spot',  # ВАЖНО! Указываем spot явно
            }
        }

        client = exchange_class(settings)

        # ПОСЛЕ создания клиента включаем sandbox
        if self.use_sandbox:
            client.set_sandbox_mode(True)

        return client