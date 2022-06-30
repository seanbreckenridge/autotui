import sys
from typing import (
    Union,
    Iterable,
    List,
    Iterator,
    Optional,
    Sequence,
    Dict,
    Callable,
    Any,
    cast,
)
from .typehelpers import NT
from .warn import warn


def _default_key(val: Any) -> str:
    return str(val)


def _remember(
    items: Union[Iterable[NT], Iterator[NT]],
    memory: Dict[str, NT],
    key_func: Optional[Callable[[NT], str]] = None,
) -> Iterator[str]:
    """
    convert each namedtuple to a string representation, using either
    the user provided key function, or the default by converting it to
    a string and removing newlines

    this 'saves' the string representation and the NT object itself in memory
    before yielding, which means the string line the users picks can later on
    be related back to the object (assuming the string representation is a unique key)
    """
    kfunc = key_func if key_func is not None else _default_key
    for i in items:
        key = kfunc(i)
        memory[key] = i
        yield key


def pick_namedtuple(
    items: Union[Iterable[NT], Iterator[NT]],
    *,
    fzf_options: Sequence[Union[str, Sequence[str]]] = (),
    key_func: Optional[Callable[[NT], str]] = None,
) -> Optional[NT]:
    try:
        import pyfzf
    except ImportError as e:
        print(
            "Could not import fzf wrapper, install with 'pip install pyfzf-iter'",
            file=sys.stderr,
        )
        raise e
    memory: Dict[str, NT] = {}
    picker = pyfzf.FzfPrompt(default_options="--no-multi")
    # use null char to delimit items, so namedtuples can have newlines
    chosen_lst: List[str] = cast(
        List[str],
        picker.prompt(
            _remember(items, memory, key_func), "--read0", *fzf_options, delimiter="\0"
        ),
    )
    assert isinstance(
        chosen_lst, list
    ), f"Unexpected return value '{chosen_lst}', expected list"
    if len(chosen_lst) == 0:
        return None
    elif len(chosen_lst) != 1:
        warn(f"Expected 1 item in return value from fzf, found '{chosen_lst}'")
    chosen = chosen_lst[0]
    if chosen.strip() == "":
        return None
    elif chosen not in memory:
        warn(f"Error relating '{chosen}' to python value")
        return None
    else:
        return memory[chosen]
