from pathlib import Path
from datetime import datetime
from typing import NamedTuple

from autotui.shortcuts import load_prompt_and_writeback


class Water(NamedTuple):
    at: datetime
    glasses: int
    per_glass_ml: float


def main():
    load_prompt_and_writeback(Water, "~/.local/share/water.json")
    load_prompt_and_writeback(Water, "~/.local/share/water.json")
    print(Path("~/.local/share/water.json").expanduser().read_text())


if __name__ == "__main__":
    main()
