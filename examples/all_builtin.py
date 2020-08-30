import autotui
from typing import NamedTuple
from datetime import datetime

# something to persist to a file
class Water(NamedTuple):
    at: datetime
    glass_count: float

w = autotui.prompt_namedtuple(Water)
print(w)

