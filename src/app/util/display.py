"""
Command-line display management.

:author: Max Milazzo
"""


import os


def clear() -> None:
    """
    Clear console display.
    """
    
    os.system("cls" if os.name == "nt" else "clear")