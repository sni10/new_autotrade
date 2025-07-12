```
📂 Запуск из директории: F:/HOME/new_autotrade

├── .dockerignore
├── .env
├── .github
│   └── workflows
│       ├── python-tests.yml
│       └── versioning.yml
├── .gitignore
├── AGENTS.md
├── BUY_ORDER_MONITOR_GUIDE.md
├── CHANGELOG.md
├── CLAUDE.md
├── Dockerfile
├── GEMINI.md
├── ISSUE_06_IMPLEMENTATION_GUIDE.md
├── ISSUE_07_IMPLEMENTATION_GUIDE.md
├── ISSUE_08_IMPLEMENTATION_GUIDE.md
├── ISSUE_15_IMPLEMENTATION_GUIDE.md
├── ISSUE_18_IMPLEMENTATION_GUIDE.md
├── ISSUE_19_IMPLEMENTATION_GUIDE.md
├── ISSUE_20_IMPLEMENTATION_GUIDE.md
├── MODULE_OVERVIEW.md
├── ORDERBOOK_INTEGRATION.md
├── PROJECT_OVERVIEW_SUMM.md
├── README.md
├── RELEASE_NOTES.md
├── RELEASE_NOTES_v2.1.0.md
├── RELEASE_NOTES_v2.2.0.md
├── RELEASE_NOTES_v2.3.0.md
├── ROADMAP.md
├── binance_keys
│   ├── id_ed25519.pem
│   └── id_ed25519pub.pem
├── file_tree.md
├── main.py
├── project_management
│   ├── implementation_plan.md
│   ├── issues
│   │   ├── issue_005_backup_service.md
│   │   ├── issue_006_data_repositories.md
│   │   ├── issue_007_signal_aggregation_service.md
│   │   ├── issue_008_market_data_analyzer.md
│   │   ├── issue_011_multi_pair_trading_service.md
│   │   ├── issue_012_performance_optimization_service.md
│   │   ├── issue_013_security_service.md
│   │   ├── issue_014_error_handling_service.md
│   │   ├── issue_015_configuration_service.md
│   │   ├── issue_016_state_management_service.md
│   │   ├── issue_017_database_service.md
│   │   ├── issue_018_risk_management_service.md
│   │   ├── issue_019_order_execution_service.md
│   │   ├── issue_020_trading_orchestrator.md
│   │   └── issue_021_health_check_service.md
│   ├── issues_summary.md
│   └── milestones.md
├── requirements.txt
├── sandbox.py
├── sandbox_websocket.py
├── sandbox_websocket_watch_order_book.py
├── sandbox_websocket_watch_trades.py
├── schema-app.puml
├── schema-app.svg
├── src
│   ├── __init__.py
│   ├── application
│   │   ├── __init__.py
│   │   ├── use_cases
│   │   │   ├── __init__.py
│   │   │   └── run_realtime_trading.py
│   │   └── utils
│   │       ├── __init__.py
│   │       └── performance_logger.py
│   ├── config
│   │   ├── __init__.py
│   │   ├── config.json
│   │   └── config_loader.py
│   ├── domain
│   │   ├── __init__.py
│   │   ├── entities
│   │   │   ├── __init__.py
│   │   │   ├── currency_pair.py
│   │   │   ├── deal.py
│   │   │   ├── order.py
│   │   │   └── ticker.py
│   │   ├── factories
│   │   │   ├── __init__.py
│   │   │   ├── deal_factory.py
│   │   │   └── order_factory.py
│   │   └── services
│   │       ├── __init__.py
│   │       ├── deals
│   │       │   ├── __init__.py
│   │       │   └── deal_service.py
│   │       ├── indicators
│   │       │   ├── __init__.py
│   │       │   └── cached_indicator_service.py
│   │       ├── market_data
│   │       │   ├── __init__.py
│   │       │   ├── market_analysis_service.py
│   │       │   ├── orderbook_analyzer.py
│   │       │   ├── orderbook_service.py
│   │       │   └── ticker_service.py
│   │       ├── orders
│   │       │   ├── __init__.py
│   │       │   ├── buy_order_monitor.py
│   │       │   ├── order_execution_service.py
│   │       │   ├── order_service.py
│   │       │   └── order_timeout_service.py
│   │       └── trading
│   │           ├── __init__.py
│   │           ├── signal_cooldown_manager.py
│   │           ├── trading_decision_engine.py
│   │           └── trading_service.py
│   └── infrastrucсупер.ture
│       ├── __init__.py
│       ├── connectors
│       │   ├── __init__.py
│       │   ├── exchange_connector.py
│       │   └── pro_exchange_connector.py
│       └── repositories
│           ├── __init__.py
│           ├── deals_repository.py
│           ├── orders_repository.py
│           └── tickers_repository.py
├── test_prod.py
└── tests
    ├── __init__.py
    ├── test_config_loader_env.py
    ├── test_currency_pair.py
    ├── test_deal.py
    ├── test_deal_factory.py
    ├── test_deals_repository.py
    ├── test_execution_stats_dataframe.py
    ├── test_order_entity.py
    ├── test_order_execution_service_integration.py
    ├── test_order_execution_service_unit.py
    ├── test_order_factory.py
    ├── test_orders_repository.py
    ├── test_ticker_entity.py
    └── test_tickers_repository.py
```
