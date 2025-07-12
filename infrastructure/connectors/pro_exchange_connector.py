import ccxt.pro as ccxtpro
from pathlib import Path
from config.config_loader import load_config

class CcxtProMarketDataConnector:
    def __init__(self, exchange_name="binance", use_sandbox=False):
        self.exchange_name = exchange_name
        self.use_sandbox = use_sandbox
        self.config = None
        self._load_config()
        self.client = self._init_exchange_client()

    def _load_config(self):

        config = load_config()
        env_key = 'sandbox' if self.use_sandbox else 'production'
        self.config = config.get('binance', {}).get(env_key, {})

        private_key_pem = self.config.get('privateKeyPath')
        if private_key_pem and Path(private_key_pem).exists():
            with open(private_key_pem, 'r') as f:
                self.config['secret'] = f.read()

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