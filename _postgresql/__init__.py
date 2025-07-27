"""
Tests for PostgreSQL repository implementations.

This module contains comprehensive unit tests for all PostgreSQL repository
implementations in the AutoTrade v2.4.0 refactoring project. The tests cover:

- PostgreSQLIndicatorRepository: Technical indicators storage and analysis
- PostgreSQLOrderBookRepository: Order book data and liquidity analysis  
- PostgreSQLTradingSignalRepository: Trading signals and consensus analysis
- PostgreSQLStatisticsRepository: System metrics and performance statistics
- PostgreSQLConfigurationRepository: Dynamic configuration management
- PostgreSQLCacheRepository: Caching with TTL support

All tests use mock database managers to ensure isolation and fast execution.
The tests verify:
- Basic CRUD operations
- Data validation and type conversion
- Error handling and edge cases
- Concurrent operations
- Database-specific features (aggregations, analytics, etc.)
"""