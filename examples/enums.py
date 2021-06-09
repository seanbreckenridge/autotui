from pathlib import Path
from typing import NamedTuple
from enum import Enum

from autotui.shortcuts import load_prompt_and_writeback


class Status(Enum):
    STARTED = 1
    COMPLETED = 2
    IN_PROGRESS = 1
    DELAYED = 3
    PLANNED = 4
    FINISHED = 5


class Task(NamedTuple):
    status: Status
    note: str


f = "~/.local/share/enums.json"

print(load_prompt_and_writeback(Task, f))
print(Path(f).expanduser().read_text())
