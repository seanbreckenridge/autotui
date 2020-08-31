import sys
import warnings

# check python version
if sys.version_info[0] == 3 and sys.version_info[1] < 8:
    warnings.warn("autotui requires at least python3.8")

import os

from .validators import (
    prompt_str,
    prompt_int,
    prompt_float,
    prompt_bool,
    prompt_datetime,
    prompt_ask_another,
    prompt_wrap_error,
    prompt_optional,
)
from .namedtuple_prompt import (
    namedtuple_prompt_funcs,
    prompt_namedtuple,
    AutoHandler,
)
from .serialize import (
    serialize_namedtuple,
    deserialize_namedtuple,
)
from .fileio import (
    namedtuple_sequence_dump,
    namedtuple_sequence_dumps,
    namedtuple_sequence_load,
    namedtuple_sequence_loads,
)
