```
📂 Запуск из директории: F:/HOME/new_autotrade

├── .gitignore
├── .run
│   └── main.run.xml
├── README.md
├── ROADMAP.md
├── analyzer.py
├── application
│   ├── use_cases
│   │   └── run_realtime_trading.py
│   └── utils
│       └── performance_logger.py
├── binance_keys
│   ├── test-prv-key.pem
│   └── test-pub-key.pem
├── domain
│   ├── entities
│   │   ├── currency_pair.py
│   │   ├── deal.py
│   │   ├── order.py
│   │   └── ticker.py
│   ├── factories
│   │   ├── deal_factory.py
│   │   └── order_factory.py
│   └── services
│       ├── cached_indicator_service.py
│       ├── deal_service.py
│       ├── market_analysis_service.py
│       ├── order_service.py
│       ├── signal_service.py
│       ├── ticker_service.py
│       └── trading_service.py
├── file_tree.txt
├── infrastructure
│   ├── connectors
│   │   ├── exchange_connector.py
│   │   └── pro_exchange_connector.py
│   └── repositories
│       ├── deals_repository.py
│       ├── orders_repository.py
│       └── tickers_repository.py
├── main.py
├── sandbox.py
└── test_api_keys.py
```