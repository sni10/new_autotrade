import os
import sys

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ['PYTHONPATH'] = SRC_PATH + os.pathsep + os.environ.get('PYTHONPATH', '')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
