import warnings
from pathlib import Path
from typing import (
    Callable,
    Type,
    NamedTuple,
    Union,
    Dict,
    List,
    Any,
)


from . import (
    AutoHandler,
    prompt_namedtuple,
    namedtuple_sequence_dumps,
    namedtuple_sequence_load,
)
from .typehelpers import PrimitiveType


def _normalize(_path: Union[Path, str]) -> Path:
    p = None
    if isinstance(_path, str):
        p = Path(_path)
    else:
        p = _path
    return p.expanduser().absolute()


# doesnt expose underlying kwargs from namedtuple_sequence_dump
# and namedtuple_sequence_load on purpose -- so that its less
# likely its mistyped. Can always use the underlying
# functions if you'd prefer to do that.


def dump_to(
    items: List[NamedTuple],
    path: Union[Path, str],
    attr_serializers: Dict[str, Callable[[Any], PrimitiveType]] = {},
    type_serializers: Dict[Type, Callable[[Any], PrimitiveType]] = {},
) -> None:
    """
    Takes a list of NamedTuples (or subclasses) and a path to a file.
    Serializes the items into a string, using the attr_serializers and
    type_serializers to handle custom types if specified.

    If serialization succeeds, writes to the file.
    """
    p = _normalize(path)
    # serialize to string before opening file
    # if serialization fails, file is left alone
    nt_string: str = namedtuple_sequence_dumps(
        items, attr_serializers=attr_serializers, type_serializers=type_serializers
    )
    with p.open(mode="w") as f:
        f.write(nt_string)


# args are slightly reordered here, comapared to json.load
# to be consistent with dump_to
def load_from(
    to: NamedTuple,
    path: Union[Path, str],
    attr_deserializers: Dict[str, Callable[[PrimitiveType], Any]] = {},
    type_deserializers: Dict[Type, Callable[[PrimitiveType], Any]] = {},
) -> List[NamedTuple]:
    """
    Takes a type to load and a path to a file containing JSON.
    Reads from the file, and deserializes the items into a list,
    using the attr_deserializers and type_deserializers to handle
    custom types if specified.

    Returns the list of items read from the file.
    """
    p: Path = _normalize(path)
    with p.open(mode="r") as f:
        items: List[NamedTuple] = namedtuple_sequence_load(
            f,
            to,
            attr_deserializers=attr_deserializers,
            type_deserializers=type_deserializers,
        )
    return items


def load_prompt_and_writeback(
    to: NamedTuple,
    path: Union[Path, str],
    attr_validators: Dict[str, AutoHandler] = {},
    type_validators: Dict[Type, AutoHandler] = {},
    attr_serializers: Dict[str, Callable[[Any], PrimitiveType]] = {},
    type_serializers: Dict[Type, Callable[[Any], PrimitiveType]] = {},
    attr_deserializers: Dict[str, Callable[[PrimitiveType], Any]] = {},
    type_deserializers: Dict[Type, Callable[[PrimitiveType], Any]] = {},
    create_file: bool = True,
) -> List[NamedTuple]:
    """
    An entry point to entire library, essentially.

    Load the NamedTuples from the JSON file specified by 'path' and 'to'

    If the file doesn't exist and the create_file flag is True, ignores the
    FileNotFound error when trying to read from the file.

    After reading the NamedTuples from the file, prompts you to add a new item,
    adds that to the list it reads in, and writes back to the file

    accepts validators, serializers and deserializers for each step of the process.
    """
    p: Path = _normalize(path)
    # read from file
    items: List[NamedTuple] = []
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
