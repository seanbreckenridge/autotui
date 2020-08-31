import autotui
from typing import NamedTuple
from datetime import datetime

# something to persist to a file
class Water(NamedTuple):
    at: datetime
    glass_count: float


w = autotui.prompt_namedtuple(Water)
print(w)

s = autotui.namedtuple_sequence_dumps([w], indent=None)
print(s)

b = autotui.namedtuple_sequence_loads(s, to=Water)
print(b[0])
