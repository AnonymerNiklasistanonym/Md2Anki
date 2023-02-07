import sys
from typing import Optional
from enum import Enum


class TerminalColors(str, Enum):
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def debug_print(
    *args, debug=False, color: Optional[TerminalColors] = None, sep: str = "", **kwargs
):
    if debug:
        print(
            *(
                args
                if color is None
                else [color.value, *args, TerminalColors.ENDC.value]
            ),
            sep=sep,
            **kwargs
        )


def warn_print(*args, sep: str = "", **kwargs):
    print("WARNING: ", *args, file=sys.stderr, sep=sep, **kwargs)
