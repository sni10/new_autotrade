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

        private_key_pem = config[self.exchange_name]['sandbox']['privateKeyPath']
        with open(private_key_pem, 'r') as f:
            private_key_pem = f.read()

        self.config = config[self.exchange_name]['sandbox' if self.use_sandbox else 'production']
        self.config['secret'] = private_key_pem

    def _init_exchange_client(self):
        exchange_class = getattr(ccxtpro, self.exchange_name)

        settings = {
            'apiKey': self.config.get('apiKey', ''),
            'privateKey': self.config.get('secret', ''),  # или 'secret'
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