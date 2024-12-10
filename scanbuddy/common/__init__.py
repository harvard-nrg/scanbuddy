import sys
import platform
from tabulate import tabulate

def print_platform_info():
    table = [
        ['Platform', platform.platform()],
        ['Processor', platform.processor()],
        ['Python version', platform.python_version()],
        ['GIL enabled', sys._is_gil_enabled()]
    ]
    print(tabulate(table, tablefmt='simple_grid'))
