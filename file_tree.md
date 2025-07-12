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
│   │   ├── issue_020_trading_orchestrator.md
│   │   ├── issue_019_order_execution_service.md
│   │   ├── issue_018_risk_management_service.md
│   │   ├── issue_008_market_data_analyzer.md
│   │   ├── issue_007_signal_aggregation_service.md
│   │   ├── issue_017_database_service.md
│   │   ├── issue_016_state_management_service.md
│   │   ├── issue_015_configuration_service.md
│   │   ├── issue_006_data_repositories.md
│   │   ├── issue_014_error_handling_service.md
│   │   ├── issue_013_security_service.md
│   │   ├── issue_021_health_check_service.md
│   │   ├── issue_005_backup_service.md
│   │   ├── issue_012_performance_optimization_service.md
│   │   └── issue_011_multi_pair_trading_service.md
│   ├── issues_summary.md
│   └── milestones.md
├── sandbox.py
├── sandbox_websocket.py
├── sandbox_websocket_watch_order_book.py
├── sandbox_websocket_watch_trades.py
├── schema-app.puml
└── schema-app.svg
```
