from datetime import datetime
from typing import NamedTuple

from autotui.shortcuts import load_prompt_and_writeback


class Water(NamedTuple):
    at: datetime
    glass_count: float


if __name__ == "__main__":
    load_prompt_and_writeback(Water, "~/.local/share/water.json")
