# Utility funcions
from enum import Enum


class Color:
    def __init__(self, code):
        self.code = code
    
BLACK = Color("0")
RED = Color("1")
GREEN = Color("2")
YELLOW = Color("3")
PINK = Color("5")
GRAY = Color("7")
NONE_COLOR = Color("")


class DecorationTypes(Enum):
    TEXT = 3
    BACKGROUND = 4
    BOLD = 1
    UNDERLINE = 4
    
class ColorDecoration:
    def __init__(self, decoration: DecorationTypes, color: Color = NONE_COLOR):
        self.code = f"{decoration.value}{color.code}"


TEXT_RED = ColorDecoration(DecorationTypes.TEXT, RED)
TEXT_GREEN = ColorDecoration(DecorationTypes.TEXT, GREEN)
TEXT_YELLOW = ColorDecoration(DecorationTypes.TEXT, YELLOW)
BACKGROUND_GRAY = ColorDecoration(DecorationTypes.BACKGROUND, GRAY)
BACKGROUND_PINK = ColorDecoration(DecorationTypes.BACKGROUND, PINK)
BACKGROUND_BLACK = ColorDecoration(DecorationTypes.BACKGROUND, BLACK)
BOLD = ColorDecoration(DecorationTypes.BOLD)
UNDERLINE = ColorDecoration(DecorationTypes.UNDERLINE)

def decorate(s: str, decorations: list[ColorDecoration]) -> str:
    return f"\x1b[{';'.join([deco.code for deco in decorations])}m{s}\x1b[0m"



# print(decorate("andthen", [Decorations.TEXT_YELLOW, Decorations.BACKGROUND_PINK]))