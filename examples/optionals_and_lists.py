from datetime import datetime
from typing import NamedTuple, Optional, List

from autotui import prompt_namedtuple

# describe a meeting with one or more people
class Meeting(NamedTuple):
    when: datetime
    where: Optional[str]  # asks if you want to add this
    people: List[str]  # asks if you want to add another item


m = prompt_namedtuple(Meeting)
print(m)
