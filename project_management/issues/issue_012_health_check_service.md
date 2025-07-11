# Issue #012: HealthCheckService - Мониторинг системы
### Статус: запланировано

**🏗️ Milestone:** M3  
**📈 Приоритет:** MEDIUM  
**🔗 Зависимости:** Issue #6 (DatabaseService), Issue #10 (ErrorHandlingService)

---

## 📝 Описание проблемы

Нет системы мониторинга здоровья торгового бота. Нужна система health checks для proactive обнаружения проблем до их критического воздействия.

### 🔍 Текущие проблемы:
- Нет мониторинга состояния компонентов
- Проблемы обнаруживаются только после сбоев
- Отсутствие метрик производительности
- Нет автоматических уведомлений о проблемах
- Невозможно предсказать деградацию системы

### 🎯 Желаемый результат:
- Continuous мониторинг всех компонентов
- Proactive обнаружение проблем
- Система метрик и алертов
- Health dashboard для визуализации
- Автоматические recovery действия

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class HealthCheckService:
    \"\"\"Централизованный мониторинг здоровья системы\"\"\"
    
    def __init__(self, components: List[HealthCheckable]):
        self.components = components
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
    async def start_monitoring(self, interval: int = 30):
    async def check_all_components(self) -> SystemHealthReport:
    async def check_component(self, component_name: str) -> ComponentHealth:
    async def get_system_metrics(self) -> SystemMetrics:
    async def trigger_recovery_action(self, component: str, issue: str):

class ComponentHealthChecker:
    \"\"\"Базовый класс для проверки здоровья компонентов\"\"\"
    
    async def check_health(self) -> HealthStatus:
    async def get_metrics(self) -> Dict[str, float]:
    async def perform_recovery(self) -> bool:

class MetricsCollector:
    \"\"\"Сбор и агрегация метрик\"\"\"
    
    async def collect_metric(self, name: str, value: float, labels: Dict[str, str]):
    async def get_time_series(self, metric: str, period: timedelta) -> List[MetricPoint]:
    async def get_aggregated_metrics(self, period: timedelta) -> Dict[str, AggregatedMetric]:

class AlertManager:
    \"\"\"Управление алертами и уведомлениями\"\"\"
    
    async def send_alert(self, alert: Alert):
    async def check_alert_conditions(self, metrics: SystemMetrics) -> List[Alert]:
    async def escalate_alert(self, alert: Alert);
```

### 📊 Структуры данных

```python
@dataclass
class HealthStatus:
    component: str
    status: str  # 'HEALTHY', 'WARNING', 'CRITICAL', 'DOWN'
    message: str
    timestamp: datetime
    metrics: Dict[str, float]
    details: Dict[str, Any]

@dataclass
class SystemHealthReport:
    overall_status: str
    timestamp: datetime
    component_statuses: List[HealthStatus]
    system_metrics: SystemMetrics
    alerts: List[Alert]
    recommendations: List[str]

@dataclass
class Alert:
    severity: str  # 'INFO', 'WARNING', 'CRITICAL'
    component: str
    message: str
    timestamp: datetime
    metric_name: str
    current_value: float
    threshold: float
    suggested_action: str
```

---

## 🛠️ Детальная реализация

### 1. **Основной HealthCheckService**

**Файл:** `domain/services/health_check_service.py`

```python
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import psutil
import time

class HealthCheckService:
    def __init__(self):
        self.components = {}
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.monitoring_task = None
        self.is_monitoring = False
        
        # Регистрация стандартных компонентов
        self._register_system_components()
        
    def register_component(self, name: str, checker: ComponentHealthChecker):
        \"\"\"Регистрация компонента для мониторинга\"\"\"
        self.components[name] = checker
        
    async def start_monitoring(self, interval: int = 30):
        \"\"\"Запуск continuous мониторинга\"\"\"
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        
    async def stop_monitoring(self):
        \"\"\"Остановка мониторинга\"\"\"
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            
    async def check_all_components(self) -> SystemHealthReport:
        \"\"\"Проверка всех компонентов\"\"\"
        component_statuses = []
        overall_status = 'HEALTHY'
        
        # Проверка каждого компонента
        for name, checker in self.components.items():
            try:
                status = await checker.check_health()
                component_statuses.append(status)
                
                # Определение общего статуса
                if status.status == 'CRITICAL' or status.status == 'DOWN':
                    overall_status = 'CRITICAL'
                elif status.status == 'WARNING' and overall_status == 'HEALTHY':
                    overall_status = 'WARNING'
                    
            except Exception as e:
                # Если не можем проверить компонент - это критично
                error_status = HealthStatus(
                    component=name,
                    status='DOWN',
                    message=f\"Health check failed: {str(e)}\",
                    timestamp=datetime.now(),
                    metrics={},
                    details={'error': str(e)}
                )
                component_statuses.append(error_status)
                overall_status = 'CRITICAL'
                
        # Сбор системных метрик
        system_metrics = await self._collect_system_metrics()
        
        # Проверка алертов
        alerts = await self.alert_manager.check_alert_conditions(system_metrics)
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(component_statuses, system_metrics)
        
        return SystemHealthReport(
            overall_status=overall_status,
            timestamp=datetime.now(),
            component_statuses=component_statuses,
            system_metrics=system_metrics,
            alerts=alerts,
            recommendations=recommendations
        )
        
    async def check_component(self, component_name: str) -> Optional[HealthStatus]:
        \"\"\"Проверка конкретного компонента\"\"\"
        if component_name not in self.components:
            return None
            
        checker = self.components[component_name]
        return await checker.check_health()
        
    async def trigger_recovery_action(self, component: str, issue: str):
        \"\"\"Запуск recovery действия для компонента\"\"\"
        if component not in self.components:
            return False
            
        checker = self.components[component]
        
        try:
            success = await checker.perform_recovery()
            
            # Логирование recovery действия
            await self.metrics_collector.collect_metric(
                'recovery_attempts',
                1.0,
                {'component': component, 'issue': issue, 'success': str(success)}
            )
            
            return success
        except Exception as e:
            return False
            
    async def _monitoring_loop(self, interval: int):
        \"\"\"Основной цикл мониторинга\"\"\"
        while self.is_monitoring:
            try:
                # Проверка всех компонентов
                health_report = await self.check_all_components()
                
                # Отправка алертов если есть
                for alert in health_report.alerts:
                    await self.alert_manager.send_alert(alert)
                    
                # Автоматические recovery действия для критических проблем
                for status in health_report.component_statuses:
                    if status.status == 'CRITICAL':
                        await self.trigger_recovery_action(
                            status.component, 
                            status.message
                        )
                        
                # Сохранение метрик
                await self._save_health_metrics(health_report)
                
            except Exception as e:
                # Не падаем если мониторинг сломался
                pass
                
            await asyncio.sleep(interval)
            
    async def _collect_system_metrics(self) -> 'SystemMetrics':
        \"\"\"Сбор системных метрик\"\"\"
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = memory.available / (1024 * 1024 * 1024)  # GB
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free = disk.free / (1024 * 1024 * 1024)  # GB
        
        # Network metrics (if needed)
        network = psutil.net_io_counters()
        
        # Process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info().rss / (1024 * 1024)  # MB
        process_cpu = process.cpu_percent()
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available,
            disk_percent=disk_percent,
            disk_free_gb=disk_free,
            process_memory_mb=process_memory,
            process_cpu_percent=process_cpu,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv
        )
        
    def _register_system_components(self):
        \"\"\"Регистрация стандартных системных компонентов\"\"\"
        
        # Database health checker
        self.register_component('database', DatabaseHealthChecker())
        
        # Exchange connection health checker  
        self.register_component('exchange', ExchangeHealthChecker())
        
        # Trading system health checker
        self.register_component('trading', TradingSystemHealthChecker())
        
        # Memory health checker
        self.register_component('memory', MemoryHealthChecker())
        
        # Disk space health checker
        self.register_component('disk', DiskHealthChecker())
        
    def _generate_recommendations(self, statuses: List[HealthStatus], 
                                metrics: 'SystemMetrics') -> List[str]:
        \"\"\"Генерация рекомендаций на основе статусов\"\"\"
        recommendations = []
        
        # Проверка памяти
        if metrics.memory_percent > 85:
            recommendations.append(\"Consider increasing available memory or optimizing memory usage\")
            
        # Проверка диска
        if metrics.disk_percent > 90:
            recommendations.append(\"Clean up disk space or increase storage capacity\")
            
        # Проверка CPU
        if metrics.cpu_percent > 80:
            recommendations.append(\"High CPU usage detected, consider optimizing algorithms\")
            
        # Проверка компонентов
        critical_components = [s for s in statuses if s.status in ['CRITICAL', 'DOWN']]
        if critical_components:
            recommendations.append(f\"Critical issues in: {', '.join([c.component for c in critical_components])}\")
            
        return recommendations

# Системные health checkers
class DatabaseHealthChecker(ComponentHealthChecker):
    async def check_health(self) -> HealthStatus:
        try:
            # Проверка подключения к БД
            start_time = time.time()
            # await database.execute(\"SELECT 1\")
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response_time > 1000:  # > 1 second
                status = 'WARNING'
                message = f\"Slow database response: {response_time:.0f}ms\"
            else:
                status = 'HEALTHY'
                message = f\"Database responsive: {response_time:.0f}ms\"
                
            return HealthStatus(
                component='database',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={'response_time_ms': response_time},
                details={'connection_pool_size': 10}  # from actual pool
            )
        except Exception as e:
            return HealthStatus(
                component='database',
                status='DOWN',
                message=f\"Database connection failed: {str(e)}\",
                timestamp=datetime.now(),
                metrics={},
                details={'error': str(e)}
            )
            
    async def perform_recovery(self) -> bool:
        try:
            # Попытка переподключения к БД
            # await database.reconnect()
            return True
        except Exception:
            return False

class ExchangeHealthChecker(ComponentHealthChecker):
    async def check_health(self) -> HealthStatus:
        try:
            # Проверка подключения к бирже
            start_time = time.time()
            # ping_result = await exchange.ping()
            response_time = (time.time() - start_time) * 1000
            
            # Проверка server time offset
            # server_time = await exchange.fetch_time()
            # time_offset = abs(server_time - time.time() * 1000)
            time_offset = 100  # mock
            
            if response_time > 2000:
                status = 'CRITICAL'
                message = f\"Exchange very slow: {response_time:.0f}ms\"
            elif response_time > 500:
                status = 'WARNING'  
                message = f\"Exchange slow: {response_time:.0f}ms\"
            elif time_offset > 5000:
                status = 'WARNING'
                message = f\"Time sync issue: {time_offset:.0f}ms offset\"
            else:
                status = 'HEALTHY'
                message = f\"Exchange healthy: {response_time:.0f}ms\"
                
            return HealthStatus(
                component='exchange',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={
                    'response_time_ms': response_time,
                    'time_offset_ms': time_offset
                },
                details={}
            )
        except Exception as e:
            return HealthStatus(
                component='exchange',
                status='DOWN',
                message=f\"Exchange connection failed: {str(e)}\",
                timestamp=datetime.now(),
                metrics={},
                details={'error': str(e)}
            )

class TradingSystemHealthChecker(ComponentHealthChecker):
    async def check_health(self) -> HealthStatus:
        try:
            # Проверка последней активности
            # last_tick_time = await trading_service.get_last_tick_time()
            last_tick_time = datetime.now()  # mock
            
            time_since_last_tick = (datetime.now() - last_tick_time).total_seconds()
            
            if time_since_last_tick > 300:  # 5 minutes
                status = 'CRITICAL'
                message = f\"No trading activity for {time_since_last_tick:.0f}s\"
            elif time_since_last_tick > 60:  # 1 minute
                status = 'WARNING'
                message = f\"Reduced trading activity: {time_since_last_tick:.0f}s\"
            else:
                status = 'HEALTHY'
                message = f\"Trading active: {time_since_last_tick:.0f}s ago\"
                
            # Проверка открытых сделок
            # open_deals_count = await deals_repository.count_open_deals()
            open_deals_count = 1  # mock
            
            return HealthStatus(
                component='trading',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={
                    'seconds_since_last_tick': time_since_last_tick,
                    'open_deals_count': open_deals_count
                },
                details={}
            )
        except Exception as e:
            return HealthStatus(
                component='trading',
                status='DOWN',
                message=f\"Trading system check failed: {str(e)}\",
                timestamp=datetime.now(),
                metrics={},
                details={'error': str(e)}
            )

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_percent: float
    disk_free_gb: float
    process_memory_mb: float
    process_cpu_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
```

### 2. **AlertManager для уведомлений**

```python
class AlertManager:
    def __init__(self):
        self.alert_thresholds = {
            'cpu_percent': {'warning': 70, 'critical': 85},
            'memory_percent': {'warning': 80, 'critical': 90},
            'disk_percent': {'warning': 85, 'critical': 95},
            'response_time_ms': {'warning': 500, 'critical': 2000}
        }
        
    async def check_alert_conditions(self, metrics: SystemMetrics) -> List[Alert]:
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']['critical']:
            alerts.append(Alert(
                severity='CRITICAL',
                component='system',
                message=f\"High CPU usage: {metrics.cpu_percent:.1f}%\",
                timestamp=datetime.now(),
                metric_name='cpu_percent',
                current_value=metrics.cpu_percent,
                threshold=self.alert_thresholds['cpu_percent']['critical'],
                suggested_action=\"Optimize CPU-intensive operations\"
            ))
        elif metrics.cpu_percent > self.alert_thresholds['cpu_percent']['warning']:
            alerts.append(Alert(
                severity='WARNING',
                component='system',
                message=f\"Elevated CPU usage: {metrics.cpu_percent:.1f}%\",
                timestamp=datetime.now(),
                metric_name='cpu_percent',
                current_value=metrics.cpu_percent,
                threshold=self.alert_thresholds['cpu_percent']['warning'],
                suggested_action=\"Monitor CPU usage trends\"
            ))
            
        # Memory alert
        if metrics.memory_percent > self.alert_thresholds['memory_percent']['critical']:
            alerts.append(Alert(
                severity='CRITICAL',
                component='system',
                message=f\"High memory usage: {metrics.memory_percent:.1f}%\",
                timestamp=datetime.now(),
                metric_name='memory_percent',
                current_value=metrics.memory_percent,
                threshold=self.alert_thresholds['memory_percent']['critical'],
                suggested_action=\"Free memory or increase RAM\"
            ))
            
        return alerts
        
    async def send_alert(self, alert: Alert):
        # В будущем можно добавить отправку в Telegram, Email, etc.
        print(f\"🚨 {alert.severity} ALERT: {alert.message}\")
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] Мониторинг всех ключевых компонентов (БД, биржа, торговля)
- [ ] Сбор системных метрик (CPU, память, диск)
- [ ] Система алертов с порогами
- [ ] Автоматические recovery действия
- [ ] Health dashboard через логи

### Производительность:
- [ ] Health check всех компонентов < 5s
- [ ] Минимальное влияние на производительность торговли
- [ ] Эффективное хранение метрик

### Надежность:
- [ ] Мониторинг не падает при сбоях компонентов
- [ ] Graceful degradation при отказах
- [ ] Сохранность истории метрик

---

## 🚧 Риски и митигация

### Риск 1: Overhead от мониторинга
**Митигация:** Оптимизированные health checks, настраиваемые интервалы

### Риск 2: False positive алерты
**Митигация:** Тщательная калибровка порогов, тестирование

### Риск 3: Сложность добавления новых компонентов
**Митигация:** Простой интерфейс ComponentHealthChecker

---

## 📚 Связанные материалы

- Issue #6: DatabaseService
- Issue #10: ErrorHandlingService
- [System Monitoring Best Practices](https://sre.google/sre-book/monitoring-distributed-systems/)
