import warnings
from pathlib import Path
from typing import (
    Callable,
    Type,
    NamedTuple,
    Union,
    Dict,
    List,
)


from . import (
    AutoHandler,
    prompt_namedtuple,
    namedtuple_sequence_dump,
    namedtuple_sequence_load,
)

def _normalize(_path: Union[Path, str]) -> Path:
    p = _path
    if isinstance(_path, str):
        p = Path(_path)
    return p.expanduser().absolute()


# doesnt expose underlying kwargs from namedtuple_sequence_dump
# and namedtuple_sequence_load on purpose -- so that its less
# likely its mistyped. Can always use the underlying
# functions if you'd prefer to do that.

def dump_to(
    items: List[NamedTuple],
    path: Union[Path, str],
    attr_serializers: Dict[str, Callable] = {},
    type_serializers: Dict[Type, Callable] = {},
) -> None:
    p = _normalize(path)
    with p.open(mode='w') as f:
        namedtuple_sequence_dump(items, f,
                                 attr_serializers=attr_serializers,
                                 type_serializers=type_serializers,
                                 )

# args are slightly reordered here, comapared to json.load
# to be consistent with dump_to
def load_from(
    to: NamedTuple,
    path: Union[Path, str],
    attr_deserializers: Dict[str, Callable] = {},
    type_deserializers: Dict[Type, Callable] = {},
) -> List[NamedTuple]:
    p = _normalize(path)
    with p.open(mode='r') as f:
        items = namedtuple_sequence_load(f, to,
                                         attr_deserializers=attr_deserializers,
                                         type_deserializers=type_deserializers)
    return items


def load_prompt_and_writeback(
    to: NamedTuple,
    path: Union[Path, str],
    attr_validators: Dict[str, AutoHandler] = {},
    type_validators: Dict[str, AutoHandler] = {},
    attr_serializers: Dict[str, Callable] = {},
    type_serializers: Dict[str, Callable] = {},
    attr_deserializers: Dict[str, Callable] = {},
    type_deserializers: Dict[str, Callable] = {},
    create_file=True) -> List[NamedTuple]:
    """
    Load the NamedTuples from the JSON file specified by 'path' and 'to'

    If the file doesn't exist and the create_file flag is True, ignores the
    FileNotFound error when trying to read from the file.

    After reading the NamedTuples from the file, prompts you to add a new item,
    adds that to the list it reads in, and writes back to the file
    """
    p = _normalize(path)
    # read from file
    items: List[NamedTuple] = []  # default incase
    try:
        items = load_from(to, p, attr_deserializers, type_deserializers)
    except FileNotFoundError as fne:
        if not create_file:
            raise fne
        warnings.warn(f"File at {p} didn't exist, using empty list")
    # prompt for the new item
    new_item: NamedTuple = prompt_namedtuple(to, attr_validators, type_validators)
    items.append(new_item)
    # dump back to file
    dump_to(items, p, attr_serializers, type_serializers)
    return items

