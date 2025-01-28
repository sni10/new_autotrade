import os


def generate_file_tree(startpath, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []

    def is_excluded(path):
        # Проверяем, содержит ли путь любую из исключаемых папок
        for ex_dir in exclude_dirs:
            if ex_dir in os.path.abspath(path).split(os.path.sep):
                return True
        return False

    def walk_dir(current_path, indent=""):
        tree = []

        if is_excluded(current_path):
            return tree  # Возвращаем пустой список, если папка исключена

        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            tree.append(f"{indent}├── [Permission Denied]")
            log_error(f"Permission Denied: {current_path}")
            return tree
        except FileNotFoundError:
            tree.append(f"{indent}├── [File Not Found]")
            log_error(f"File Not Found: {current_path}")
            return tree

        items = [item for item in items if not is_excluded(os.path.join(current_path, item))]

        for index, item in enumerate(items):
            path = os.path.join(current_path, item)
            if os.path.isdir(path):
                tree.append(f"{indent}├── {item}/")
                tree.extend(walk_dir(path, indent + "│   "))
            else:
                if index == len(items) - 1:
                    tree.append(f"{indent}└── {item}")
                else:
                    tree.append(f"{indent}├── {item}")

        return tree

    return "\n".join(walk_dir(startpath))


def log_error(message):
    with open('error_log.txt', 'a') as log_file:
        log_file.write(f"{message}\n")


def save_tree_to_file(startpath, exclude_dirs, output_file):
    file_tree = generate_file_tree(startpath, exclude_dirs)
    print(file_tree)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(file_tree)


def collect_python_code(startpath, exclude_dirs, output_file):
    python_code_content = []

    def walk_and_collect_code(current_path):
        if any(ex_dir in os.path.abspath(current_path).split(os.path.sep) for ex_dir in exclude_dirs):
            return

        try:
            items = sorted(os.listdir(current_path))
        except (PermissionError, FileNotFoundError):
            return

        for item in items:
            path = os.path.join(current_path, item)
            if os.path.isdir(path):
                walk_and_collect_code(path)
            elif path.endswith('.py'):
                try:
                    with open(path, 'r', encoding='utf-8') as py_file:
                        code = py_file.read()
                    relative_path = os.path.relpath(path, startpath)
                    python_code_content.append(f"# {relative_path}\n{code}\n")
                except (PermissionError, FileNotFoundError):
                    log_error(f"Cannot read file: {path}")

    walk_and_collect_code(startpath)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(python_code_content))


# Параметры F:\HOME\new_autotrade
startpath = 'F:\\HOME\\new_autotrade'
exclude_dirs = [
    'local_utils', 'local_utils', 'local_utils', 'local_utils', 'public', 'db-data', 'img', 'config', 'db', 'logs',
    'var', 'tests', 'origins', '.composer', 'venv', 'build', '.output', 'cypress', '.nuxt',
    'vendor', 'framework', 'coverage-report', 'node_modules', 'dbdata', 'media', '.git', 'temp', 'log', 'lib', 'sql', 'storage',
    'img', 'dbdata', 'parser_upc_asin', 'googleapis',
    '.idea', '__pycache__'
]
output_file_tree = os.path.join(startpath, 'file_tree.txt')
output_python_code = os.path.join(startpath, 'all_code.txt')

# Сохранение дерева файлов
save_tree_to_file(startpath, exclude_dirs, output_file_tree)
# Сохранение всех Python кодов
collect_python_code(startpath, exclude_dirs, output_python_code)
