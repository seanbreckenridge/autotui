from typing import NamedTuple

from datetime import datetime
from autotui.edit import edit_namedtuple


class Water(NamedTuple):
    at: datetime
    glass_count: float


water = Water(datetime.now(), 1)
water = edit_namedtuple(
    water, print_namedtuple=True, attr_use_values={"at": datetime.now}
)
print(water)
