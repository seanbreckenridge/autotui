import typing

from typing import Optional, Tuple, Type, Union, List, Any, Set
from datetime import datetime

# A lot of these are helpers from:
# https://github.com/karlicoss/cachew/blob/f4db4a6c6609170642c6cd09d50b52ac4c0edec9/src/cachew/__init__.py#L144

# items that can serialized directly into JSON by simplejson.dump
# datetime is converted to UTC before storing
PRIMITIVES = {
    str: Type[str],
    int: Type[int],
    float: Type[float],
    bool: Type[bool],
    datetime: Type[datetime],
}


CONTAINERS = {
    list: Type[List],
    set: Type[Set],
}

def add_to_container(container: Union[List, Set], item: Any):
    if isinstance(container, list):
        container.append(item)
    elif isinstance(container, set):
        container.add(item)
    else:
        raise RuntimeError(f"{type(container)} is not a list/set, not sure how to add to")
    return container


def get_union_args(cls) -> Optional[Tuple[Type]]:
    if getattr(cls, "__origin__", None) != Union:
        return None

    args = cls.__args__
    args = [e for e in args if e != type(None)]
    assert len(args) > 0
    return args


def is_union(cls):
    return get_union_args(cls) is not None


def strip_optional(cls) -> Tuple[Type, bool]:
    """
    >>> from typing import Optional, NamedTuple
    >>> strip_optional(Optional[int])
    (<class 'int'>, True)
    >>> strip_optional(int)
    (<class 'int'>, False)
    >>> strip_optional(Optional[List[int]])
    (typing.List[int], True)
    """
    is_opt: bool = False

    args = get_union_args(cls)
    if args is not None and len(args) == 1:
        cls = args[0]  # meh
        is_opt = True

    return (cls, is_opt)


def strip_generic(tp):
    """
    >>> from typing import List
    >>> strip_generic(List[int])
    <class 'list'>
    >>> strip_generic(str)
    <class 'str'>
    """
    GA = getattr(typing, "_GenericAlias")
    if isinstance(tp, GA):
        return tp.__origin__
    return tp


def is_primitive(cls: Type) -> bool:
    """
    Whether or not this is a supported, serializable primitive

    >>> from typing import Dict
    >>> is_primitive(int)
    True
    >>> is_primitive(set)
    False
    """
    return cls in PRIMITIVES


def is_supported_container(cls: Type) -> bool:
    """
    >>> from typing import Dict, List, Set, Tuple
    >>> is_supported_container(List[int])
    True
    >>> is_supported_container(Set[str])
    True
    >>> is_supported_container(Tuple[int])
    False
    >>> is_supported_container(Dict[int, str])
    False
    """
    return strip_generic(cls) in CONTAINERS


def is_string(a: Any) -> bool:
    return type(a) == str


def is_int(a: Any) -> bool:
    return type(a) == int


def is_float(a: Any) -> bool:
    return type(a) == float


def is_bool(a: Any) -> bool:
    return type(a) == bool


def is_datetime(a: Any) -> bool:
    return type(a) == datetime

