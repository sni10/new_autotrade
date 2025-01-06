[schema-app.puml](schema-app.puml)

![schema-app.svg](schema-app.svg)



```
my_trading_app/
│
├── domain/
│   ├── entities/
│   │   ├── deal.py
│   │   ├── order.py
│   │   ├── currency_pair.py
│   │   ├── exchange_settings.py
│   │   ...
│   ├── factories/
│   │   ├── deal_factory.py
│   │   ├── order_factory.py
│   │   └── ...
│   ├── services/
│   │   ├── trading_service.py
│   │   ├── order_service.py
│   │   ├── signal_service.py     # опционально
│   │   └── ...
│   ├── events/
│   │   └── deal_opened_event.py
│   │   ...
│   └── __init__.py
│
├── application/
│   ├── use_cases/
│   │   ├── run_trading.py        # классический сценарий торговли
│   │   ├── run_realtime_trading.py
│   │   ├── handle_signals.py
│   │   └── ...
│   ├── trading_loop.py           # асинхронный цикл, вызывающий use-cases
│   └── __init__.py
│
├── infrastructure/
│   ├── repositories/
│   │   ├── deals_repository.py
│   │   ├── orders_repository.py
│   │   ├── currency_pairs_repository.py
│   │   └── __init__.py
│   ├── connectors/
│   │   ├── exchange_connector.py
│   │   ├── market_data_connector.py
│   │   ├── db_connector.py
│   │   └── __init__.py
│   └── config/
│       ├── settings.py
│       └── __init__.py
│
├── interfaces/
│   ├── cli/
│   │   ├── main_cli.py
│   │   └── ...
│   ├── # потенциально REST API
│   └── __init__.py
│
├── utils/
│   ├── utils.py
│   └── __init__.py
│
├── tests/
│   └── ...
│
└── main.py

```

<details>
  <summary>SCHEMA PLANT UML</summary>

```@startuml
namespace domain.entities {
  class Deal {
    - id: int
    - currency_pair_id: int
    - status: string
    - buy_order: Order
    - sell_order: Order
    - created_at: int
    - closed_at: int
    + open()
    + close()
    + cancel()
  }

  class Order {
    - id: int
    - type: string
    - side: string
    - status: string
    - price: float
    - amount: float
    - exchange_id: string
    + place()
    + cancel()
    + is_open()
    + is_closed()
  }

  class CurrencyPair {
    - base_currency: string
    - quote_currency: string
    - symbol: string
    - order_life_time: int
    - deal_quota: float
    - profit_markup: float
    - deal_count: int
  }
}

namespace domain.factories {
  class DealFactory {
    + create_new_deal(cp: CurrencyPair, ...): Deal
  }

  class OrderFactory {
    + create_buy_order(cp: CurrencyPair, ...): Order
    + create_sell_order(cp: CurrencyPair, ...): Order
  }
}

namespace domain.services {
  class TradingService {
    - deal_factory: DealFactory
    - deals_repo: DealsRepository
    - order_service: OrderService
    + open_deal_if_needed(signals, cp: CurrencyPair)
    + update_deal_status(deal: Deal, orders_info): void
  }

  class OrderService {
    - order_factory: OrderFactory
    - orders_repo: OrdersRepository
    - exchange_connector: ExchangeConnector
    + place_buy_order(...)
    + place_sell_order(...)
    + cancel_order(...)
  }
}

namespace infrastructure.connectors {
  interface ExchangeConnector {
    + fetch_balance()
    + create_order(symbol, side, type, amount, price)
    + cancel_order(order_id, symbol)
    + fetch_ohlcv(symbol, timeframe, since, limit)
    + fetch_orders(symbol)
  }
}

namespace infrastructure.repositories {
  interface DealsRepository {
    + save(deal: Deal)
    + get_by_id(deal_id: int): Deal
    + get_open_deals(): List<Deal>
  }

  interface OrdersRepository {
    + save(order: Order)
    + get_by_id(order_id: int): Order
    + get_all_by_deal(deal_id: int): List<Order>
  }
}

domain.entities.Deal --> domain.entities.Order : uses buy_order, sell_order

domain.services.TradingService --> domain.entities.Deal
domain.services.TradingService --> domain.entities.CurrencyPair
domain.services.TradingService --> domain.factories.DealFactory
domain.services.TradingService --> infrastructure.repositories.DealsRepository
domain.services.TradingService --> domain.services.OrderService

domain.services.OrderService --> domain.entities.Order
domain.services.OrderService --> domain.factories.OrderFactory
domain.services.OrderService --> infrastructure.connectors.ExchangeConnector
domain.services.OrderService --> infrastructure.repositories.OrdersRepository

@enduml
```

</details>
