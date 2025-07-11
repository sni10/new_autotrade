# Issue #013: BackupService - Резервное копирование
### Статус: запланировано

**🏗️ Milestone:** M3  
**📈 Приоритет:** LOW  
**🔗 Зависимости:** Issue #6 (DatabaseService)

---

## 📝 Описание проблемы

Нет системы резервного копирования торговых данных. При сбоях или потере данных невозможно восстановить историю сделок и настройки.

### 🔍 Текущие проблемы:
- Отсутствие резервного копирования БД
- Нет backup конфигурационных файлов
- Потеря данных при hardware сбоях
- Отсутствие versioning для настроек
- Нет автоматического восстановления

### 🎯 Желаемый результат:
- Автоматические backup по расписанию
- Incremental и full backup
- Безопасное хранение backup файлов
- Быстрое восстановление данных
- Versioning критических настроек

---

## 📋 Технические требования

### 🏗️ Архитектура

```python
class BackupService:
    \"\"\"Служба резервного копирования\"\"\"
    
    def __init__(self, storage_backends: List[BackupStorage]):
        self.storage_backends = storage_backends
        self.scheduler = BackupScheduler()
        self.compression = BackupCompression()
        
    async def create_full_backup(self) -> BackupInfo:
    async def create_incremental_backup(self, since: datetime) -> BackupInfo:
    async def restore_from_backup(self, backup_id: str) -> bool:
    async def schedule_automatic_backups(self, schedule: BackupSchedule):
    async def list_available_backups(self) -> List[BackupInfo]:
    async def verify_backup_integrity(self, backup_id: str) -> bool:
    async def cleanup_old_backups(self, retention_policy: RetentionPolicy);

class BackupStorage:
    \"\"\"Абстрактное хранилище backup\"\"\"
    
    async def store_backup(self, backup_data: bytes, metadata: BackupMetadata) -> str:
    async def retrieve_backup(self, backup_id: str) -> bytes:
    async def delete_backup(self, backup_id: str) -> bool:
    async def list_backups(self) -> List[BackupInfo]:

class BackupScheduler:
    \"\"\"Планировщик backup\"\"\"
    
    async def start_scheduler(self):
    async def stop_scheduler(self):
    async def add_schedule(self, schedule: BackupSchedule);
    async def remove_schedule(self, schedule_id: str);
```

### 📊 Структуры данных

```python
@dataclass
class BackupInfo:
    backup_id: str
    backup_type: str  # 'FULL', 'INCREMENTAL'
    created_at: datetime
    size_bytes: int
    checksum: str
    metadata: BackupMetadata
    storage_location: str

@dataclass
class BackupMetadata:
    database_version: str
    config_version: str
    included_tables: List[str]
    excluded_data: List[str]
    compression_type: str
    encryption_enabled: bool

@dataclass
class BackupSchedule:
    schedule_id: str
    backup_type: str
    cron_expression: str  # '0 2 * * *' for daily at 2 AM
    retention_days: int
    enabled: bool
    storage_backends: List[str]

@dataclass
class RetentionPolicy:
    daily_keep: int = 7     # Keep 7 daily backups
    weekly_keep: int = 4    # Keep 4 weekly backups  
    monthly_keep: int = 12  # Keep 12 monthly backups
    yearly_keep: int = 2    # Keep 2 yearly backups
```

---

## 🛠️ Детальная реализация

### 1. **Основной BackupService**

**Файл:** `domain/services/backup_service.py`

```python
import asyncio
import gzip
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import tempfile
import os

class BackupService:
    def __init__(self):
        self.storage_backends = []
        self.scheduler = BackupScheduler(self)
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Регистрация хранилищ по умолчанию
        self._register_default_storages()
        
    def add_storage_backend(self, storage: BackupStorage):
        \"\"\"Добавление backend для хранения\"\"\"
        self.storage_backends.append(storage)
        
    async def create_full_backup(self) -> BackupInfo:
        \"\"\"Создание полного backup\"\"\"
        backup_id = self._generate_backup_id('FULL')
        
        try:
            # Создание временной папки для backup
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Backup базы данных
                await self._backup_database(temp_path / 'database.sql')
                
                # Backup конфигурационных файлов
                await self._backup_configuration(temp_path / 'config')
                
                # Backup ключей (зашифрованно)
                await self._backup_keys(temp_path / 'keys')
                
                # Backup логов (последние 7 дней)
                await self._backup_logs(temp_path / 'logs')
                
                # Создание архива
                archive_path = await self._create_archive(temp_path, backup_id)
                
                # Вычисление checksum
                checksum = await self._calculate_checksum(archive_path)
                
                # Metadata
                metadata = BackupMetadata(
                    database_version='1.0',
                    config_version='2.1.0',
                    included_tables=['deals', 'orders', 'tickers'],
                    excluded_data=['temporary_data'],
                    compression_type='gzip',
                    encryption_enabled=False
                )
                
                # Сохранение в storage backends
                storage_locations = []
                archive_size = os.path.getsize(archive_path)
                
                with open(archive_path, 'rb') as f:
                    archive_data = f.read()
                    
                for storage in self.storage_backends:
                    location = await storage.store_backup(archive_data, metadata)
                    storage_locations.append(location)
                    
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    backup_type='FULL',
                    created_at=datetime.now(),
                    size_bytes=archive_size,
                    checksum=checksum,
                    metadata=metadata,
                    storage_location=';'.join(storage_locations)
                )
                
                # Сохранение info о backup
                await self._save_backup_info(backup_info)
                
                return backup_info
                
        except Exception as e:
            raise BackupException(f\"Full backup failed: {str(e)}\")
            
    async def create_incremental_backup(self, since: datetime) -> BackupInfo:
        \"\"\"Создание инкрементального backup\"\"\"
        backup_id = self._generate_backup_id('INCREMENTAL')
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Backup только изменившихся данных
                await self._backup_database_incremental(temp_path / 'database_changes.sql', since)
                
                # Backup измененных конфигов
                await self._backup_configuration_incremental(temp_path / 'config_changes', since)
                
                # Backup новых логов
                await self._backup_logs_incremental(temp_path / 'new_logs', since)
                
                # Создание архива
                archive_path = await self._create_archive(temp_path, backup_id)
                checksum = await self._calculate_checksum(archive_path)
                
                metadata = BackupMetadata(
                    database_version='1.0',
                    config_version='2.1.0',
                    included_tables=['deals', 'orders', 'tickers'],
                    excluded_data=[],
                    compression_type='gzip',
                    encryption_enabled=False
                )
                
                # Сохранение
                storage_locations = []
                archive_size = os.path.getsize(archive_path)
                
                with open(archive_path, 'rb') as f:
                    archive_data = f.read()
                    
                for storage in self.storage_backends:
                    location = await storage.store_backup(archive_data, metadata)
                    storage_locations.append(location)
                    
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    backup_type='INCREMENTAL',
                    created_at=datetime.now(),
                    size_bytes=archive_size,
                    checksum=checksum,
                    metadata=metadata,
                    storage_location=';'.join(storage_locations)
                )
                
                await self._save_backup_info(backup_info)
                return backup_info
                
        except Exception as e:
            raise BackupException(f\"Incremental backup failed: {str(e)}\")
            
    async def restore_from_backup(self, backup_id: str) -> bool:
        \"\"\"Восстановление из backup\"\"\"
        try:
            # Получение информации о backup
            backup_info = await self._get_backup_info(backup_id)
            if not backup_info:
                raise BackupException(f\"Backup {backup_id} not found\")
                
            # Загрузка backup data
            backup_data = None
            for storage in self.storage_backends:
                try:
                    backup_data = await storage.retrieve_backup(backup_id)
                    if backup_data:
                        break
                except Exception:
                    continue
                    
            if not backup_data:
                raise BackupException(f\"Cannot retrieve backup data for {backup_id}\")
                
            # Проверка целостности
            actual_checksum = hashlib.sha256(backup_data).hexdigest()
            if actual_checksum != backup_info.checksum:
                raise BackupException(f\"Backup checksum mismatch for {backup_id}\")
                
            # Распаковка и восстановление
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                archive_path = temp_path / f\"{backup_id}.tar.gz\"
                
                # Сохранение архива
                with open(archive_path, 'wb') as f:
                    f.write(backup_data)
                    
                # Распаковка
                extract_path = temp_path / 'extracted'
                await self._extract_archive(archive_path, extract_path)
                
                # Восстановление компонентов
                if backup_info.backup_type == 'FULL':
                    await self._restore_full_backup(extract_path)
                else:
                    await self._restore_incremental_backup(extract_path)
                    
            return True
            
        except Exception as e:
            print(f\"❌ Restore failed: {str(e)}\")
            return False
            
    async def _backup_database(self, output_path: Path):
        \"\"\"Backup базы данных\"\"\"
        database_path = 'data/trading_bot.db'  # Путь к БД
        
        if os.path.exists(database_path):
            # SQLite backup
            with sqlite3.connect(database_path) as source:
                with sqlite3.connect(str(output_path)) as backup:
                    source.backup(backup)
        else:
            # Создать пустой SQL файл
            with open(output_path, 'w') as f:
                f.write('-- No database found\\n')
                
    async def _backup_configuration(self, output_dir: Path):
        \"\"\"Backup конфигурационных файлов\"\"\"
        output_dir.mkdir(exist_ok=True)
        
        config_files = [
            'config/config.json',
            '.env',
            'security/salt.key'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                dest_path = output_dir / Path(config_file).name
                shutil.copy2(config_file, dest_path)
                
    async def _backup_keys(self, output_dir: Path):
        \"\"\"Backup ключей и сертификатов\"\"\"
        output_dir.mkdir(exist_ok=True)
        
        keys_dir = Path('binance_keys')
        if keys_dir.exists():
            for key_file in keys_dir.glob('*'):
                if key_file.is_file():
                    shutil.copy2(key_file, output_dir / key_file.name)
                    
    async def _backup_logs(self, output_dir: Path):
        \"\"\"Backup логов за последние дни\"\"\"
        output_dir.mkdir(exist_ok=True)
        
        # Backup только последние логи
        cutoff_date = datetime.now() - timedelta(days=7)
        
        log_files = ['app.log', 'trading.log', 'security/audit.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                # В реальности нужно фильтровать по дате
                shutil.copy2(log_file, output_dir / Path(log_file).name)
                
    async def _create_archive(self, source_dir: Path, backup_id: str) -> Path:
        \"\"\"Создание сжатого архива\"\"\"
        archive_path = self.backup_dir / f\"{backup_id}.tar.gz\"
        
        # Создание tar.gz архива
        import tarfile
        with tarfile.open(archive_path, 'w:gz') as tar:
            for item in source_dir.rglob('*'):
                if item.is_file():
                    arcname = item.relative_to(source_dir)
                    tar.add(item, arcname=arcname)
                    
        return archive_path
        
    async def _calculate_checksum(self, file_path: Path) -> str:
        \"\"\"Вычисление checksum файла\"\"\"
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b\"\"):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def _generate_backup_id(self, backup_type: str) -> str:
        \"\"\"Генерация ID для backup\"\"\"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f\"{backup_type.lower()}_{timestamp}\"
        
    async def _save_backup_info(self, backup_info: BackupInfo):
        \"\"\"Сохранение информации о backup\"\"\"
        info_file = self.backup_dir / f\"{backup_info.backup_id}.json\"
        
        info_dict = {
            'backup_id': backup_info.backup_id,
            'backup_type': backup_info.backup_type,
            'created_at': backup_info.created_at.isoformat(),
            'size_bytes': backup_info.size_bytes,
            'checksum': backup_info.checksum,
            'storage_location': backup_info.storage_location,
            'metadata': {
                'database_version': backup_info.metadata.database_version,
                'config_version': backup_info.metadata.config_version,
                'included_tables': backup_info.metadata.included_tables,
                'compression_type': backup_info.metadata.compression_type
            }
        }
        
        with open(info_file, 'w') as f:
            json.dump(info_dict, f, indent=2)
            
    def _register_default_storages(self):
        \"\"\"Регистрация storage backends по умолчанию\"\"\"
        
        # Local file system storage
        self.add_storage_backend(LocalFileStorage(self.backup_dir / 'local'))
        
        # В будущем можно добавить:
        # self.add_storage_backend(S3Storage(bucket='trading-bot-backups'))
        # self.add_storage_backend(GoogleCloudStorage(bucket='trading-bot-backups'))

# Storage backends
class LocalFileStorage(BackupStorage):
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        
    async def store_backup(self, backup_data: bytes, metadata: BackupMetadata) -> str:
        backup_id = f\"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}\"
        backup_path = self.storage_dir / f\"{backup_id}.backup\"
        
        with open(backup_path, 'wb') as f:
            f.write(backup_data)
            
        return str(backup_path)
        
    async def retrieve_backup(self, backup_id: str) -> bytes:
        backup_path = self.storage_dir / f\"{backup_id}.backup\"
        
        if backup_path.exists():
            with open(backup_path, 'rb') as f:
                return f.read()
        else:
            raise BackupException(f\"Backup file not found: {backup_path}\")
            
    async def delete_backup(self, backup_id: str) -> bool:
        backup_path = self.storage_dir / f\"{backup_id}.backup\"
        
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False

class BackupScheduler:
    def __init__(self, backup_service: BackupService):
        self.backup_service = backup_service
        self.schedules = []
        self.running = False
        self.scheduler_task = None
        
    async def start_scheduler(self):
        \"\"\"Запуск планировщика\"\"\"
        if self.running:
            return
            
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Добавление стандартных расписаний
        await self._add_default_schedules()
        
    async def _add_default_schedules(self):
        \"\"\"Добавление стандартных расписаний\"\"\"
        
        # Ежедневный incremental backup в 2:00
        daily_schedule = BackupSchedule(
            schedule_id='daily_incremental',
            backup_type='INCREMENTAL',
            cron_expression='0 2 * * *',  # Every day at 2 AM
            retention_days=7,
            enabled=True,
            storage_backends=['local']
        )
        self.schedules.append(daily_schedule)
        
        # Еженедельный full backup в воскресенье в 3:00
        weekly_schedule = BackupSchedule(
            schedule_id='weekly_full',
            backup_type='FULL',
            cron_expression='0 3 * * 0',  # Every Sunday at 3 AM
            retention_days=28,
            enabled=True,
            storage_backends=['local']
        )
        self.schedules.append(weekly_schedule)
        
    async def _scheduler_loop(self):
        \"\"\"Основной цикл планировщика\"\"\"
        while self.running:
            try:
                current_time = datetime.now()
                
                for schedule in self.schedules:
                    if schedule.enabled and self._should_run_backup(schedule, current_time):
                        await self._execute_scheduled_backup(schedule)
                        
            except Exception as e:
                print(f\"❌ Scheduler error: {str(e)}\")
                
            # Проверка каждые 60 секунд
            await asyncio.sleep(60)
            
    def _should_run_backup(self, schedule: BackupSchedule, current_time: datetime) -> bool:
        \"\"\"Проверка нужно ли запускать backup\"\"\"
        # Упрощенная проверка - в реальности нужен полноценный cron parser
        # Для демонстрации проверяем только час
        
        if schedule.cron_expression == '0 2 * * *':  # Daily at 2 AM
            return current_time.hour == 2 and current_time.minute == 0
        elif schedule.cron_expression == '0 3 * * 0':  # Weekly Sunday at 3 AM
            return (current_time.weekday() == 6 and  # Sunday
                   current_time.hour == 3 and 
                   current_time.minute == 0)
        
        return False
        
    async def _execute_scheduled_backup(self, schedule: BackupSchedule):
        \"\"\"Выполнение запланированного backup\"\"\"
        try:
            if schedule.backup_type == 'FULL':
                backup_info = await self.backup_service.create_full_backup()
            else:
                # Incremental since last backup
                last_backup_time = datetime.now() - timedelta(days=1)
                backup_info = await self.backup_service.create_incremental_backup(last_backup_time)
                
            print(f\"✅ Scheduled {schedule.backup_type} backup completed: {backup_info.backup_id}\")
            
        except Exception as e:
            print(f\"❌ Scheduled backup failed: {str(e)}\")

class BackupException(Exception):
    \"\"\"Исключение backup операций\"\"\"
    pass
```

---

## ✅ Критерии приемки

### Функциональные требования:
- [ ] Full и incremental backup
- [ ] Автоматическое планирование backup
- [ ] Сжатие и проверка целостности
- [ ] Восстановление из backup
- [ ] Multiple storage backends

### Надежность:
- [ ] Backup не влияет на торговлю
- [ ] Проверка целостности backup
- [ ] Graceful handling ошибок
- [ ] Atomic backup операции

### Производительность:
- [ ] Incremental backup < 30s
- [ ] Full backup < 5 минут
- [ ] Восстановление < 10 минут

---

## 🚧 Риски и митигация

### Риск 1: Большой размер backup файлов
**Митигация:** Сжатие, incremental backup, retention policy

### Риск 2: Backup во время торговли
**Митигация:** Lock-free backup методы, off-peak scheduling

### Риск 3: Поврежденные backup
**Митигация:** Checksum validation, multiple storage locations

---

## 📚 Связанные материалы

- Issue #6: DatabaseService
- [Database Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
- [3-2-1 Backup Strategy](https://www.veeam.com/blog/321-backup-rule.html)
