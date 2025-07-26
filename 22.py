#!/usr/bin/env python3
"""
AutoTrade Code Collector
Собирает весь код проекта (кроме тестов) в один markdown файл
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set


class CodeCollector:
    """Класс для сборки всего кода проекта в единый markdown файл"""

    def __init__(self, project_path: str, output_file: str = None):
        self.project_path = Path(project_path)
        self.output_file = output_file or f"autotrade_complete_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        # Расширения файлов для включения
        self.include_extensions = {
            '.py', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini',
            '.txt', '.md', '.rst', '.requirements'
        }

        # Папки и файлы для исключения
        self.exclude_dirs = {
            '__pycache__', '.git', '.gitignore', 'venv', 'env', '.env',
            'node_modules', '.pytest_cache', '.mypy_cache', '.tox',
            'build', 'dist', '*.egg-info', '.idea', '.vscode',
            'test', 'tests', 'testing',  # Исключаем тесты
            'docker', 'Docker', 'dockerfile', 'Dockerfile',  # Docker
            'docs', 'documentation', 'doc',  # Документация
            'assets', 'static', 'media', 'images', 'img',  # Медиа
            'logs', 'log', 'tmp', 'temp', 'cache',  # Временные
            'backup', 'backups', 'old', 'archive',  # Бэкапы
            'vendor', 'lib', 'libs', 'external',  # Внешние либы
            'migrations', 'seeds', 'fixtures',  # БД файлы
            'coverage', 'htmlcov', '.coverage',  # Покрытие кода
            'scripts', 'tools', 'utils', 'bin',  # Утилиты
            'config', 'configs', 'settings',  # Конфиги (отдельно обработаем)
            'project_management', 'pm', 'roadmap'  # Управление проектом
        }

        self.exclude_files = {
            '.gitignore', '.dockerignore', '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '*.pyd', '__pycache__', '*.so',
            '*.log', '*.tmp', '*.temp', '*.swp', '*.swo'
        }

        # Конфиденциальные файлы (показываем структуру, но не содержимое)
        self.sensitive_files = {
            'config.json', 'secrets.json', 'credentials.json',
            '.env', '.env.local', '.env.production',
            'id_ed25519.pem', 'test-prv-key.pem'
        }

        # Статистика
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'total_lines': 0,
            'total_size': 0
        }

    def should_exclude_dir(self, dir_name: str) -> bool:
        """Проверяет, нужно ли исключить директорию"""
        dir_lower = dir_name.lower()

        # Проверяем точные совпадения
        if dir_lower in self.exclude_dirs:
            return True

        # Проверяем частичные совпадения для тестов
        test_keywords = ['test', 'testing', 'spec', 'specs']
        if any(keyword in dir_lower for keyword in test_keywords):
            return True

        # Скрытые папки (начинающиеся с точки)
        if dir_name.startswith('.') and dir_name not in {'.github', '.gitlab'}:
            return True

        return False

    def should_exclude_file(self, file_path: Path) -> bool:
        """Проверяет, нужно ли исключить файл"""
        file_name = file_path.name.lower()

        # Проверяем расширение
        if file_path.suffix not in self.include_extensions:
            return True

        # Проверяем имя файла
        if any(pattern in file_name for pattern in self.exclude_files):
            return True

        # Проверяем на тестовые файлы
        test_keywords = ['test_', '_test', 'test.py', 'tests.py', 'spec_', '_spec']
        if any(keyword in file_name for keyword in test_keywords):
            return True

        return False

    def is_sensitive_file(self, file_path: Path) -> bool:
        """Проверяет, является ли файл конфиденциальным"""
        return file_path.name in self.sensitive_files

    def get_file_tree(self) -> List[str]:
        """Генерирует дерево файлов проекта"""
        tree_lines = []

        def add_tree_node(path: Path, prefix: str = "", is_last: bool = True):
            if self.should_exclude_dir(path.name) and path.is_dir():
                return

            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{path.name}")

            if path.is_dir():
                try:
                    children = sorted([p for p in path.iterdir()
                                       if not self.should_exclude_dir(p.name) or not p.is_dir()])
                    for i, child in enumerate(children):
                        child_is_last = i == len(children) - 1
                        extension = "    " if is_last else "│   "
                        add_tree_node(child, prefix + extension, child_is_last)
                except PermissionError:
                    pass

        tree_lines.append(f"📁 {self.project_path.name}/")
        try:
            children = sorted([p for p in self.project_path.iterdir()
                               if not self.should_exclude_dir(p.name) or not p.is_dir()])
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                add_tree_node(child, "", is_last)
        except PermissionError:
            tree_lines.append("❌ Нет доступа к директории")

        return tree_lines

    def collect_files(self) -> Dict[str, List[Path]]:
        """Собирает все файлы проекта, группируя по типам"""
        files_by_type = {}

        def scan_directory(directory: Path):
            try:
                for item in directory.iterdir():
                    if item.is_dir():
                        if not self.should_exclude_dir(item.name):
                            scan_directory(item)
                    elif item.is_file():
                        self.stats['total_files'] += 1

                        if not self.should_exclude_file(item):
                            # Группируем по расширению
                            ext = item.suffix or 'no_extension'
                            if ext not in files_by_type:
                                files_by_type[ext] = []
                            files_by_type[ext].append(item)
                            self.stats['processed_files'] += 1
                        else:
                            self.stats['skipped_files'] += 1
            except PermissionError:
                print(f"⚠️  Нет доступа к директории: {directory}")

        scan_directory(self.project_path)
        return files_by_type

    def read_file_safely(self, file_path: Path) -> str:
        """Безопасно читает файл с обработкой различных кодировок"""
        encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    self.stats['total_lines'] += len(content.splitlines())
                    self.stats['total_size'] += len(content.encode('utf-8'))
                    return content
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                return f"❌ Ошибка чтения файла: {e}"

        return "❌ Не удалось декодировать файл с поддерживаемыми кодировками"

    def generate_markdown(self, files_by_type: Dict[str, List[Path]]) -> str:
        """Генерирует markdown файл с кодом"""
        md_content = []

        # Заголовок
        md_content.extend([
            f"# 🤖 AutoTrade - Полный код проекта",
            f"",
            f"**Сгенерировано:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Проект:** {self.project_path}  ",
            f"**Файлов обработано:** {self.stats['processed_files']} из {self.stats['total_files']}  ",
            f"**Общий размер:** {self.stats['total_size']:,} байт  ",
            f"**Строк кода:** {self.stats['total_lines']:,}  ",
            f"",
            "---",
            ""
        ])

        # Оглавление
        md_content.extend([
            "## 📑 Оглавление",
            "",
            "- [🌳 Структура проекта](#-структура-проекта)",
            "- [📊 Статистика файлов](#-статистика-файлов)"
        ])

        # Добавляем ссылки на секции
        for ext in sorted(files_by_type.keys()):
            if ext == '.py':
                md_content.append("- [🐍 Python файлы](#-python-файлы)")
            elif ext == '.json':
                md_content.append("- [⚙️ JSON конфигурации](#️-json-конфигурации)")
            elif ext in ['.md', '.rst']:
                md_content.append("- [📝 Документация](#-документация)")
            else:
                section_name = f"{ext.upper()[1:]} файлы" if ext.startswith('.') else f"{ext} файлы"
                anchor = section_name.lower().replace(' ', '-').replace('.', '')
                md_content.append(f"- [📄 {section_name}](#{anchor})")

        md_content.extend(["", "---", ""])

        # Структура проекта
        md_content.extend([
            "## 🌳 Структура проекта",
            "",
            "```",
            *self.get_file_tree(),
            "```",
            ""
        ])

        # Статистика
        md_content.extend([
            "## 📊 Статистика файлов",
            "",
            f"| Метрика | Значение |",
            f"|---------|----------|",
            f"| Всего файлов найдено | {self.stats['total_files']} |",
            f"| Обработано файлов | {self.stats['processed_files']} |",
            f"| Пропущено файлов | {self.stats['skipped_files']} |",
            f"| Общее количество строк | {self.stats['total_lines']:,} |",
            f"| Общий размер (байт) | {self.stats['total_size']:,} |",
            ""
        ])

        # Группировка файлов по типам
        type_stats = {}
        for ext, files in files_by_type.items():
            type_stats[ext] = len(files)

        if type_stats:
            md_content.extend([
                "### Распределение по типам файлов:",
                "",
                "| Тип | Количество |",
                "|-----|------------|"
            ])

            for ext in sorted(type_stats.keys()):
                ext_name = ext if ext != 'no_extension' else 'без расширения'
                md_content.append(f"| {ext_name} | {type_stats[ext]} |")

            md_content.append("")

        # Содержимое файлов по типам
        for ext in sorted(files_by_type.keys()):
            files = sorted(files_by_type[ext], key=lambda x: x.relative_to(self.project_path))

            # Определяем заголовок секции
            if ext == '.py':
                section_title = "🐍 Python файлы"
                lang = "python"
            elif ext == '.json':
                section_title = "⚙️ JSON конфигурации"
                lang = "json"
            elif ext in ['.yaml', '.yml']:
                section_title = "📋 YAML файлы"
                lang = "yaml"
            elif ext == '.md':
                section_title = "📝 Markdown документация"
                lang = "markdown"
            elif ext == '.rst':
                section_title = "📝 RestructuredText документация"
                lang = "rst"
            elif ext == '.toml':
                section_title = "⚙️ TOML конфигурации"
                lang = "toml"
            else:
                section_title = f"📄 {ext.upper()[1:]} файлы" if ext.startswith('.') else f"📄 {ext} файлы"
                lang = "text"

            md_content.extend([
                f"## {section_title}",
                ""
            ])

            for file_path in files:
                relative_path = file_path.relative_to(self.project_path)

                md_content.extend([
                    f"### 📄 `{relative_path}`",
                    ""
                ])

                # Проверяем, конфиденциальный ли файл
                if self.is_sensitive_file(file_path):
                    md_content.extend([
                        "```text",
                        "🔒 КОНФИДЕНЦИАЛЬНЫЙ ФАЙЛ - СОДЕРЖИМОЕ СКРЫТО",
                        f"Размер файла: {file_path.stat().st_size} байт",
                        f"Последнее изменение: {datetime.fromtimestamp(file_path.stat().st_mtime)}",
                        "```",
                        ""
                    ])
                else:
                    content = self.read_file_safely(file_path)

                    md_content.extend([
                        f"```{lang}",
                        content,
                        "```",
                        ""
                    ])

        return "\n".join(md_content)

    def run(self) -> bool:
        """Запускает процесс сборки"""
        print(f"🚀 Начинаем сборку кода проекта: {self.project_path}")

        if not self.project_path.exists():
            print(f"❌ Проект не найден: {self.project_path}")
            return False

        print("📁 Сканируем файлы...")
        files_by_type = self.collect_files()

        if not files_by_type:
            print("❌ Не найдено файлов для обработки")
            return False

        print(f"📝 Генерируем markdown файл: {self.output_file}")
        markdown_content = self.generate_markdown(files_by_type)

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✅ Успешно создан файл: {self.output_file}")
            print(f"📊 Статистика:")
            print(f"   - Обработано файлов: {self.stats['processed_files']}")
            print(f"   - Пропущено файлов: {self.stats['skipped_files']}")
            print(f"   - Строк кода: {self.stats['total_lines']:,}")
            print(f"   - Размер: {self.stats['total_size']:,} байт")

            return True

        except Exception as e:
            print(f"❌ Ошибка при записи файла: {e}")
            return False


def main():
    """Главная функция"""
    # Захардкоженный путь к проекту
    project_path = r"F:\HOME\new_autotrade"
    output_file = r"/autotrade_complete_code.md"

    print(f"🎯 Собираем код проекта: {project_path}")
    print(f"📝 Выходной файл: {output_file}")

    collector = CodeCollector(project_path, output_file)

    success = collector.run()

    if success:
        print(f"\n🎉 ГОТОВО! Файл создан: {output_file}")
    else:
        print(f"\n💥 ОШИБКА! Не удалось создать файл")

    input("\nНажмите Enter для выхода...")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()