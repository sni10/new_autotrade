```
📂 Запуск из директории: F:/HOME/new_autotrade

├── .gitignore
├── .run
│   └── main.run.xml
├── CHANGELOG.md
├── ORDERBOOK_INTEGRATION.md
├── README.md
├── RELEASE_NOTES.md
├── RELEASE_NOTES_v2.1.0.md
├── ROADMAP.md
├── all_code.txt
├── application
│   ├── __init__.py
│   ├── use_cases
│   │   └── run_realtime_trading.py
│   └── utils
│       ├── __init__.py
│       └── performance_logger.py
├── binance_keys
│   ├── id_ed25519.pem
│   ├── id_ed25519pub.pem
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
│       ├── orderbook_analyzer.py
│       ├── orderbook_service.py
│       ├── signal_cooldown_manager.py
│       ├── signal_service.py
│       ├── ticker_service.py
│       ├── trading_decision_engine.py
│       └── trading_service.py
├── file_tree.md
├── infrastructure
│   ├── connectors
│   │   ├── exchange_connector.py
│   │   └── pro_exchange_connector.py
│   └── repositories
│       ├── deals_repository.py
│       ├── orders_repository.py
│       └── tickers_repository.py
├── main.py
├── project_management
│   ├── implementation_plan.md
│   ├── issues
│   │   ├── issue_001_trading_orchestrator.md
│   │   ├── issue_002_order_execution_service.md
│   │   ├── issue_003_risk_management_service.md
│   │   ├── issue_006_database_service.md
│   │   ├── issue_007_state_management_service.md
│   │   ├── issue_008_configuration_service.md
│   │   └── issue_010_error_handling_service.md
│   ├── issues_summary.md
│   └── milestones.md
├── sandbox.py
├── sandbox_websocket.py
├── sandbox_websocket_watch_order_book.py
├── sandbox_websocket_watch_trades.py
├── schema-app.puml
└── schema-app.svg
```