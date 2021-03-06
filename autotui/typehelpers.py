import typing
import inspect
from functools import lru_cache
from datetime import datetime
from typing import (
    Optional,
    Tuple,
    Type,
    Union,
    List,
    Any,
    Set,
    Sequence,
    NamedTuple,
    Dict,
)

# A lot of these are helpers from:
# https://github.com/karlicoss/cachew/blob/f4db4a6c6609170642c6cd09d50b52ac4c0edec9/src/cachew/__init__.py#L144

# items that can serialized directly into JSON by json.dumps
# datetime is converted to UTC before storing
PRIMITIVES = {
    str: Type[str],
    int: Type[int],
    float: Type[float],
    bool: Type[bool],
    datetime: Type[datetime],
}

PrimitiveType = Union[str, int, float, bool, datetime, dict]


CONTAINERS = {
    list: Type[List],
    set: Type[Set],
}

AnyContainerType = Union[List[Any], Set[Any]]


def cache(user_function):
    'Simple lightweight unbounded cache. Sometimes called "memoize".'
    return lru_cache(maxsize=None)(user_function)


def add_to_container(container: Union[List, Set], item: Any) -> AnyContainerType:
    if isinstance(container, list):
        container.append(item)
    elif isinstance(container, set):
        container.add(item)
    else:
        raise RuntimeError(
            f"{type(container)} is not a list/set, not sure how to add to"
        )
    return container


@cache
def get_union_args(cls: Type) -> Optional[List[Type[Any]]]:
    """
    >>> get_union_args(Union[str, int])
    [<class 'str'>, <class 'int'>]
    >>> get_union_args(Optional[str])
    [<class 'str'>]
    """
    if getattr(cls, "__origin__", None) != Union:
        return None

    args: Type = cls.__args__
    arg_list: List[Type] = [e for e in args if e != type(None)]
    assert len(arg_list) > 0
    return arg_list


# an estimation, someone could always trick
# this if they really wanted to...
# this should be passed the NamedTuple object,
# not a class type
def is_namedtuple_obj(thing: Any) -> bool:
    _asdict = getattr(thing, "_asdict", None)
    return _asdict is not None and callable(_asdict)


# this should be passed a NamedTuple type (typically
# created with class(NamedTuple), not an instance
def is_namedtuple_type(thing: Type) -> bool:
    return hasattr(thing, "_fields") and issubclass(thing, tuple) and callable(thing)


def is_union(cls: Type) -> bool:
    return get_union_args(cls) is not None


@cache
def get_collection_types(cls: Type) -> Tuple[Type, Type]:
    """
    >>> from typing import List
    >>> get_collection_types(List[int])
    (<class 'list'>, <class 'int'>)
    >>> get_collection_types(Set[bool])
    (<class 'set'>, <class 'bool'>)
    """
    container_type: Type = strip_generic(cls)
    # e.g. if List[int], internal[0] == int
    internal: Sequence[Type] = typing.get_args(cls)  # requires 3.8
    assert (
        len(internal) == 1
    ), f"Expected 1 argument for {container_type}, got {len(internal)}"
    return container_type, internal[0]


@cache
def strip_optional(cls: Type) -> Tuple[Type, bool]:
    """
    >>> from typing import Optional
    >>> strip_optional(Optional[int])
    (<class 'int'>, True)
    >>> strip_optional(int)
    (<class 'int'>, False)
    >>> strip_optional(Optional[List[int]])
    (typing.List[int], True)
    """
    is_opt: bool = False

    args: Optional[List[Type[Any]]] = get_union_args(cls)
    if args is not None and len(args) == 1:
        cls = args[0]  # meh
        is_opt = True

    return (cls, is_opt)


@cache
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
    >>> is_primitive(str)
    True
    >>> is_primitive(float)
    True
    >>> is_primitive(bool)
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


@cache
def inspect_signature_dict(
    nt: Type[NamedTuple],
) -> Dict[str, Type]:
    return {
        name: param.annotation
        for name, param in inspect.signature(nt).parameters.items()
    }
