import os
from typing import Set, Generator, Dict, Optional, List, Union
from collections import defaultdict
from enum import auto, Enum
from contextlib import contextmanager


class Option(Enum):
    DATETIME_LIVE = auto()
    LIVE_DATETIME = DATETIME_LIVE  # here for backwards compatibility

    @property
    def names(self) -> List[str]:
        lst: List[str] = []

        # dedupe duplicate names (keys present for backwards compatibility)
        seen: Set[Option] = set()
        for name, val in Option.__members__.items():
            if val in seen:
                continue
            seen.add(val)
            lst.append(name.casefold())
        return lst


# set which gets modified by contextmanager
# to enable/disable flags
_ENABLED: Dict[Option, Set[object]] = defaultdict(set)


def str_to_option(op: str) -> Optional[Option]:
    try:
        val: Option = getattr(Option, op.upper())
        return val
    except AttributeError:
        return None


@contextmanager
def options(*opts: Union[str, Option]) -> Generator[None, None, None]:
    """
    A contextmanager (meant to be used with a 'with' block) to temporarily enable options
    This way, disparate parts of the library don't have to have optional keyword arguments
    passed all the way down to change small things about prompts, which prompts are used,
    formats etc.

    e.g.,:

    with options("LIVE_DATETIME"):
        autotui.prompt_namedtuple(...)

    """
    # use object ID as a unique ID for this call, so the options can be removed afterwards
    # that means this can support nested contextmanagers with conflicting information, an option
    # is enabled as long as one contextmanager using it is still active
    this_call = object()
    try:
        # add options
        for op in opts:
            opt: Optional[Option] = None
            if isinstance(op, Option):
                opt = op
            elif isinstance(op, str):
                opt = str_to_option(op)
                if opt is None:
                    raise ValueError(
                        f"Unknown option {op}. Valid Options: {Option.names}"
                    )
            if opt is None:
                raise TypeError(f"{op} not of type option or string")
            _ENABLED[opt].add(this_call)
        yield
    finally:
        # remove options
        for opt, obj_set in list(_ENABLED.items()):
            obj_set.remove(this_call)
            # if no items left in the value set, no longer in any contexts
            # which enabled the option, remove it
            if len(obj_set) == 0:
                del _ENABLED[opt]


def is_enabled(opt: Option) -> bool:
    """
    checks the global state for a particular option, to see if its enabled or not
    """
    return opt in _ENABLED


def _load_global_options() -> None:
    """
    load global, library-wide options using environment variables
    do this once, when the file is loaded
    """
    # if environment variable is set, permanently set the option using a local global_id
    # option. That should always remain in the set, so this will remain enabled irregardless
    # of any other contextmanager calls
    global_id = object()
    for key in os.environ:
        if key.casefold().startswith("autotui_"):
            _, _, part = key.partition("_")
            enum_val = str_to_option(part)
            if enum_val is not None:
                _ENABLED[enum_val].add(global_id)


# load global options, any environment variables should already be set
_load_global_options()
