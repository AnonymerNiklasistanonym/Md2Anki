from typing import Optional


class TerminalColors:
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
            *(args if color is None else [color, *args, TerminalColors.ENDC]),
            sep=sep,
            **kwargs
        )
