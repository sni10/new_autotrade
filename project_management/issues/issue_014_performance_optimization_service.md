# Issue #014: PerformanceOptimizationService
### Статус: запланировано

**🏗️ Milestone:** M4  
**📈 Приоритет:** MEDIUM  
**🔗 Зависимости:** Issue #1 (TradingOrchestrator), Issue #6 (DatabaseService)

---

## 📝 Описание проблемы

Система требует оптимизации для достижения цели < 1ms обработки тика в 95% случаев. Текущая производительность не оптимизирована для high-frequency торговли.

### 🔍 Текущие узкие места:
- Синхронные операции в async коде
- Неоптимизированные запросы к БД
- Избыточные вычисления индикаторов
- Memory leaks при длительной работе
- Отсутствие профилирования и метрик

### 🎯 Желаемый результат:
- Обработка тика < 1ms в 95% случаев
- Memory-efficient длительная работа 24/7
- Оптимизированные алгоритмы и структуры данных
- Continuous performance monitoring
- Auto-scaling возможности

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class PerformanceOptimizationService:
    \"\"\"Сервис оптимизации производительности\"\"\"
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.cache_manager = CacheManager()
        self.memory_optimizer = MemoryOptimizer()
        self.database_optimizer = DatabaseOptimizer()
        
    async def start_monitoring(self):
    async def optimize_tick_processing(self, ticker: Ticker) -> TickProcessingResult:
    async def optimize_database_queries(self):
    async def optimize_memory_usage(self):
    async def get_performance_report(self) -> PerformanceReport:
    async def auto_tune_parameters(self);

class PerformanceProfiler:
    \"\"\"Профайлер производительности\"\"\"
    
    async def start_profiling(self, operation: str):
    async def end_profiling(self, operation: str) -> ProfileResult:
    async def profile_function(self, func, *args, **kwargs):
    async def get_bottlenecks(self) -> List[Bottleneck]:

class CacheManager:
    \"\"\"Управление кешированием\"\"\"
    
    async def cache_indicators(self, symbol: str, indicators: Dict):
    async def get_cached_indicators(self, symbol: str) -> Optional[Dict]:
    async def invalidate_cache(self, symbol: str):
    async def optimize_cache_sizes(self);

class MemoryOptimizer:
    \"\"\"Оптимизация памяти\"\"\"
    
    async def monitor_memory_usage(self) -> MemoryStats:
    async def cleanup_old_data(self);
    async def optimize_object_pools(self);
    async def detect_memory_leaks(self) -> List[MemoryLeak];
```

### 📊 Структуры данных

```python
@dataclass
class PerformanceMetrics:
    tick_processing_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    database_query_time_ms: float
    cache_hit_ratio: float
    throughput_ticks_per_second: float
    timestamp: datetime

@dataclass 
class TickProcessingResult:
    processing_time_ms: float
    optimizations_applied: List[str]
    cache_hits: int
    database_queries: int
    memory_allocated_mb: float
    bottlenecks: List[str]

@dataclass
class Bottleneck:
    operation: str
    average_time_ms: float
    call_count: int
    total_time_ms: float
    optimization_suggestions: List[str]

@dataclass
class MemoryLeak:
    object_type: str
    instance_count: int
    growth_rate_per_hour: float
    estimated_leak_size_mb: float
```

---

## 🛠️ Детальная реализация

### 1. **Основной PerformanceOptimizationService**

**Файл:** `domain/services/performance_optimization_service.py`

```python
import asyncio
import time
import gc
import sys
import psutil
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import weakref
import cProfile
import pstats
from functools import wraps

class PerformanceOptimizationService:
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.cache_manager = CacheManager()
        self.memory_optimizer = MemoryOptimizer()
        self.database_optimizer = DatabaseOptimizer()
        
        # Performance targets
        self.target_tick_time_ms = 1.0
        self.target_memory_mb = 100.0
        self.target_cache_hit_ratio = 0.8
        
        # Metrics storage
        self.metrics_history = deque(maxlen=1000)
        self.performance_counters = defaultdict(list)
        
    async def start_monitoring(self):
        \"\"\"Запуск continuous мониторинга производительности\"\"\"
        
        # Запуск фонового мониторинга
        asyncio.create_task(self._performance_monitoring_loop())
        asyncio.create_task(self._memory_monitoring_loop())
        asyncio.create_task(self._auto_optimization_loop())
        
    async def optimize_tick_processing(self, ticker: Ticker) -> TickProcessingResult:
        \"\"\"Оптимизация обработки тика\"\"\"
        
        start_time = time.perf_counter()
        optimizations_applied = []
        cache_hits = 0
        database_queries = 0
        bottlenecks = []
        
        # 1. Кеширование индикаторов
        cached_indicators = await self.cache_manager.get_cached_indicators(ticker.symbol)
        if cached_indicators:
            ticker.signals.update(cached_indicators)
            cache_hits += 1
            optimizations_applied.append('indicator_cache_hit')
        else:
            # Вычисление индикаторов только если нет в кеше
            # indicators = await self._calculate_indicators(ticker)
            # await self.cache_manager.cache_indicators(ticker.symbol, indicators)
            pass
            
        # 2. Batch операции с БД
        if self._should_batch_database_operations():
            # Группировка операций для batch выполнения
            optimizations_applied.append('database_batching')
        else:
            database_queries += 1
            
        # 3. Object pooling для тиков
        optimized_ticker = await self._get_pooled_ticker_object(ticker)
        if optimized_ticker != ticker:
            optimizations_applied.append('object_pooling')
            
        # 4. Lazy evaluation для тяжелых вычислений
        if self._can_skip_heavy_calculations(ticker):
            optimizations_applied.append('lazy_evaluation')
            
        # 5. Memory-mapped операции для больших данных
        if self._should_use_memory_mapping():
            optimizations_applied.append('memory_mapping')
            
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Обнаружение bottlenecks
        if processing_time > self.target_tick_time_ms:
            bottlenecks.append(f'slow_tick_processing_{processing_time:.2f}ms')
            
        # Запись метрик
        await self._record_tick_metrics(processing_time, optimizations_applied)
        
        return TickProcessingResult(
            processing_time_ms=processing_time,
            optimizations_applied=optimizations_applied,
            cache_hits=cache_hits,
            database_queries=database_queries,
            memory_allocated_mb=self._get_current_memory_mb(),
            bottlenecks=bottlenecks
        )
        
    async def optimize_database_queries(self):
        \"\"\"Оптимизация запросов к БД\"\"\"
        
        # 1. Анализ медленных запросов
        slow_queries = await self.database_optimizer.analyze_slow_queries()
        
        # 2. Добавление недостающих индексов
        missing_indexes = await self.database_optimizer.suggest_indexes()
        for index in missing_indexes:
            await self.database_optimizer.create_index(index)
            
        # 3. Оптимизация connection pool
        await self.database_optimizer.optimize_connection_pool()
        
        await self.database_optimizer.setup_query_batching()
        
    async def optimize_memory_usage(self):
        \"\"\"Оптимизация использования памяти\"\"\"
        
        # 1. Принудительная garbage collection
        collected = gc.collect()
        
        # 2. Очистка старых данных
        await self.memory_optimizer.cleanup_old_data()
        
        # 3. Оптимизация object pools
        await self.memory_optimizer.optimize_object_pools()
        
        # 4. Проверка memory leaks
        leaks = await self.memory_optimizer.detect_memory_leaks()
        if leaks:
            for leak in leaks:
                print(f\"⚠️ Memory leak detected: {leak.object_type} ({leak.instance_count} instances)\")
                
        return collected
        
    async def get_performance_report(self) -> PerformanceReport:
        \"\"\"Генерация отчета о производительности\"\"\"
        
        current_metrics = await self._collect_current_metrics()
        bottlenecks = await self.profiler.get_bottlenecks()
        
        # Анализ трендов
        if len(self.metrics_history) > 10:
            recent_metrics = list(self.metrics_history)[-10:]
            avg_tick_time = sum(m.tick_processing_time_ms for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        else:
            avg_tick_time = current_metrics.tick_processing_time_ms
            avg_memory = current_metrics.memory_usage_mb
            
        # Рекомендации по оптимизации
        recommendations = self._generate_optimization_recommendations(
            current_metrics, bottlenecks
        )
        
        return PerformanceReport(
            timestamp=datetime.now(),
            current_metrics=current_metrics,
            average_tick_time_ms=avg_tick_time,
            average_memory_mb=avg_memory,
            bottlenecks=bottlenecks,
            performance_grade=self._calculate_performance_grade(current_metrics),
            recommendations=recommendations
        )
        
    async def auto_tune_parameters(self):
        \"\"\"Автоматическая настройка параметров производительности\"\"\"
        
        current_metrics = await self._collect_current_metrics()
        
        # Автонастройка cache sizes
        if current_metrics.cache_hit_ratio < 0.7:
            await self.cache_manager.increase_cache_sizes()
        elif current_metrics.cache_hit_ratio > 0.95:
            await self.cache_manager.decrease_cache_sizes()
            
        # Автонастройка batch sizes
        if current_metrics.tick_processing_time_ms > 2.0:
            await self.database_optimizer.increase_batch_sizes()
        elif current_metrics.tick_processing_time_ms < 0.5:
            await self.database_optimizer.decrease_batch_sizes()
            
        # Автонастройка memory limits
        if current_metrics.memory_usage_mb > self.target_memory_mb:
            await self.memory_optimizer.reduce_memory_limits()
            
    async def _performance_monitoring_loop(self):
        \"\"\"Цикл мониторинга производительности\"\"\"
        while True:
            try:
                metrics = await self._collect_current_metrics()
                self.metrics_history.append(metrics)
                
                # Алерты на критические проблемы
                if metrics.tick_processing_time_ms > 5.0:
                    print(f\"🚨 CRITICAL: Tick processing too slow: {metrics.tick_processing_time_ms:.2f}ms\")
                    
                if metrics.memory_usage_mb > 200.0:
                    print(f\"🚨 CRITICAL: High memory usage: {metrics.memory_usage_mb:.1f}MB\")
                    
            except Exception as e:
                pass
                
            await asyncio.sleep(10)  # Мониторинг каждые 10 секунд
            
    async def _memory_monitoring_loop(self):
        \"\"\"Цикл мониторинга памяти\"\"\"
        while True:
            try:
                memory_stats = await self.memory_optimizer.monitor_memory_usage()
                
                # Автоматическая очистка памяти при необходимости
                if memory_stats.usage_percent > 80:
                    await self.optimize_memory_usage()
                    
            except Exception as e:
                pass
                
            await asyncio.sleep(60)  # Проверка памяти каждую минуту
            
    async def _auto_optimization_loop(self):
        \"\"\"Цикл автоматической оптимизации\"\"\"
        while True:
            try:
                await self.auto_tune_parameters()
            except Exception as e:
                pass
                
            await asyncio.sleep(300)  # Автонастройка каждые 5 минут

    def _get_current_memory_mb(self) -> float:
        \"\"\"Получение текущего использования памяти в MB\"\"\"
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
        
    async def _collect_current_metrics(self) -> PerformanceMetrics:
        \"\"\"Сбор текущих метрик производительности\"\"\"
        
        # CPU и память
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        
        # Последнее время обработки тика
        recent_tick_times = self.performance_counters.get('tick_processing', [])
        avg_tick_time = sum(recent_tick_times[-10:]) / len(recent_tick_times[-10:]) if recent_tick_times else 0
        
        # Cache hit ratio
        cache_stats = await self.cache_manager.get_cache_statistics()
        cache_hit_ratio = cache_stats.get('hit_ratio', 0.0)
        
        return PerformanceMetrics(
            tick_processing_time_ms=avg_tick_time,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            database_query_time_ms=0.0,  # TODO: get from database_optimizer
            cache_hit_ratio=cache_hit_ratio,
            throughput_ticks_per_second=len(recent_tick_times) / 60 if recent_tick_times else 0,
            timestamp=datetime.now()
        )

class PerformanceProfiler:
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.active_operations = {}
        
    async def start_profiling(self, operation: str):
        \"\"\"Начало профилирования операции\"\"\"
        self.active_operations[operation] = time.perf_counter()
        
    async def end_profiling(self, operation: str) -> ProfileResult:
        \"\"\"Окончание профилирования операции\"\"\"
        if operation in self.active_operations:
            start_time = self.active_operations.pop(operation)
            duration = (time.perf_counter() - start_time) * 1000
            self.operation_times[operation].append(duration)
            
            return ProfileResult(
                operation=operation,
                duration_ms=duration,
                average_ms=sum(self.operation_times[operation]) / len(self.operation_times[operation])
            )
        return None
        
    def profile_function(self, func: Callable):
        \"\"\"Декоратор для профилирования функций\"\"\"
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation_name = f\"{func.__module__}.{func.__name__}\"
            await self.start_profiling(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                await self.end_profiling(operation_name)
                
        return wrapper
        
    async def get_bottlenecks(self) -> List[Bottleneck]:
        \"\"\"Получение узких мест производительности\"\"\"
        bottlenecks = []
        
        for operation, times in self.operation_times.items():
            if len(times) > 5:  # Достаточно данных для анализа
                avg_time = sum(times) / len(times)
                total_time = sum(times)
                call_count = len(times)
                
                # Операция считается bottleneck если:
                # 1. Среднее время > 10ms
                # 2. Общее время > 1000ms
                if avg_time > 10.0 or total_time > 1000.0:
                    suggestions = self._generate_optimization_suggestions(operation, avg_time)
                    
                    bottlenecks.append(Bottleneck(
                        operation=operation,
                        average_time_ms=avg_time,
                        call_count=call_count,
                        total_time_ms=total_time,
                        optimization_suggestions=suggestions
                    ))
                    
        # Сортировка по total_time (самые затратные операции первыми)
        bottlenecks.sort(key=lambda x: x.total_time_ms, reverse=True)
        return bottlenecks
        
    def _generate_optimization_suggestions(self, operation: str, avg_time: float) -> List[str]:
        \"\"\"Генерация предложений по оптимизации\"\"\"
        suggestions = []
        
        if 'database' in operation.lower():
            suggestions.append(\"Consider adding database indexes\")
            suggestions.append(\"Use connection pooling\")
            suggestions.append(\"Implement query batching\")
            
        if 'indicator' in operation.lower():
            suggestions.append(\"Implement indicator caching\")
            suggestions.append(\"Use vectorized calculations\")
            suggestions.append(\"Consider pre-computed indicators\")
            
        if avg_time > 50.0:
            suggestions.append(\"Consider async/await optimization\")
            suggestions.append(\"Profile individual sub-operations\")
            
        return suggestions

class CacheManager:
    def __init__(self):
        self.indicator_cache = {}
        self.cache_stats = defaultdict(int)
        self.max_cache_size = 1000
        
    async def cache_indicators(self, symbol: str, indicators: Dict):
        \"\"\"Кеширование индикаторов\"\"\"
        cache_key = f\"{symbol}_indicators\"
        self.indicator_cache[cache_key] = {
            'data': indicators,
            'timestamp': datetime.now(),
            'ttl': 60  # TTL в секундах
        }
        
        # Очистка старого кеша при превышении лимита
        if len(self.indicator_cache) > self.max_cache_size:
            await self._cleanup_expired_cache()
            
    async def get_cached_indicators(self, symbol: str) -> Optional[Dict]:
        \"\"\"Получение кешированных индикаторов\"\"\"
        cache_key = f\"{symbol}_indicators\"
        
        if cache_key in self.indicator_cache:
            cache_entry = self.indicator_cache[cache_key]
            
            # Проверка TTL
            elapsed = (datetime.now() - cache_entry['timestamp']).total_seconds()
            if elapsed < cache_entry['ttl']:
                self.cache_stats['hits'] += 1
                return cache_entry['data']
            else:
                # Удаление просроченного кеша
                del self.indicator_cache[cache_key]
                
        self.cache_stats['misses'] += 1
        return None
        
    async def get_cache_statistics(self) -> Dict[str, float]:
        \"\"\"Получение статистики кеша\"\"\"
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_ratio = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0.0
        
        return {
            'hit_ratio': hit_ratio,
            'total_entries': len(self.indicator_cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses']
        }

@dataclass
class PerformanceReport:
    timestamp: datetime
    current_metrics: PerformanceMetrics
    average_tick_time_ms: float
    average_memory_mb: float
    bottlenecks: List[Bottleneck]
    performance_grade: str  # 'A', 'B', 'C', 'D', 'F'
    recommendations: List[str]

@dataclass
class ProfileResult:
    operation: str
    duration_ms: float
    average_ms: float
```

---

## ✅ Критерии приемки

### Производительность:
- [ ] 95% тиков обрабатываются < 1ms
- [ ] Memory usage стабильно < 100MB
- [ ] CPU usage < 50% при нормальной нагрузке
- [ ] Cache hit ratio > 80%
- [ ] Database queries < 10ms среднее время

### Мониторинг:
- [ ] Continuous performance профилирование
- [ ] Автоматическое обнаружение bottlenecks
- [ ] Real-time алерты на проблемы
- [ ] Детальные performance отчеты

### Оптимизация:
- [ ] Автонастройка параметров производительности
- [ ] Memory leak detection и prevention
- [ ] Database query optimization
- [ ] Intelligent caching strategies

---

## 🚧 Риски и митигация

### Риск 1: Over-optimization приводит к сложности
**Митигация:** Измеряемые улучшения, профилирование до и после

### Риск 2: Memory leaks от оптимизаций
**Митигация:** Extensive тестирование, continuous мониторинг

### Риск 3: Снижение надежности ради скорости
**Митигация:** Performance тесты в CI, rollback возможности

---

## 📚 Связанные материалы

- Issue #1: TradingOrchestrator
- Issue #6: DatabaseService  
- [High Performance Python](https://www.oreilly.com/library/view/high-performance-python/9781449361747/)
- [Python Performance Optimization](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
