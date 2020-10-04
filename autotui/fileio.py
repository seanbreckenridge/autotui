from typing import List, Dict, Callable, Type, NamedTuple, Any, TextIO

import simplejson

from .serialize import serialize_namedtuple, deserialize_namedtuple, PrimitiveType


def _pretty_print(kwargs):
    if "indent" not in kwargs:
        kwargs["indent"] = 4 * " "
    return kwargs


# need to types for *one* argument for **kwargs: https://stackoverflow.com/a/37032111/9348376
def namedtuple_sequence_dumps(
    nt_items: List[NamedTuple],
    attr_serializers: Dict[str, Callable[[Any], PrimitiveType]] = {},
    type_serializers: Dict[Type, Callable[[Any], PrimitiveType]] = {},
    **kwargs: str,  # doesn't really matter, I arbitrary chose to specify the 'encoding' kwarg
) -> str:
    """
    Dump the list of namedtuples to a JSON string
    Additional arguments are passed onto simplejson.dumps
    """
    kwargs = _pretty_print(kwargs)
    s_obj: List[Dict[str, Any]] = []
    for nt in nt_items:
        s_obj.append(serialize_namedtuple(nt, attr_serializers, type_serializers))
    return simplejson.dumps(s_obj, **kwargs)


def namedtuple_sequence_dump(
    nt_items: List[NamedTuple],
    fp: TextIO,
    attr_serializers: Dict[str, Callable[[Any], PrimitiveType]] = {},
    type_serializers: Dict[Type, Callable[[Any], PrimitiveType]] = {},
    **kwargs: str,
) -> None:
    """
    Dump the list of namedtuples to a file-like object as JSON
    Additional arguments are passed onto simplejson.dump
    """
    kwargs = _pretty_print(kwargs)
    s_obj: List[Dict[str, Any]] = []
    for nt in nt_items:
        s_obj.append(serialize_namedtuple(nt, attr_serializers, type_serializers))
    # dump to string first, so JSON serialization errors dont cause data losses
    nt_string: str = simplejson.dumps(s_obj, **kwargs)
    fp.write(nt_string)


def namedtuple_sequence_loads(
    nt_string: str,
    to: NamedTuple,
    attr_deserializers: Dict[str, Callable[[PrimitiveType], Any]] = {},
    type_deserializers: Dict[Type, Callable[[PrimitiveType], Any]] = {},
    **kwargs: str,
) -> List[NamedTuple]:
    """
    Load a list of namedtuples specificed by 'to' from a JSON string
    Additional arguments are passed onto simplejson.loads
    """
    loaded_obj = simplejson.loads(nt_string)
    if not isinstance(loaded_obj, list):
        raise TypeError(
            f"{loaded_obj} is a {type(loaded_obj).__name__}, expected a top-level list from JSON source"
        )
    ds_items: List[NamedTuple] = []
    for lo in loaded_obj:
        ds_items.append(
            deserialize_namedtuple(lo, to, attr_deserializers, type_deserializers)
        )
    return ds_items


def namedtuple_sequence_load(
    fp: TextIO,
    to: NamedTuple,
    attr_deserializers: Dict[str, Callable[[PrimitiveType], Any]] = {},
    type_deserializers: Dict[Type, Callable[[PrimitiveType], Any]] = {},
    **kwargs: str,
) -> List[NamedTuple]:
    """
    Load a list of namedtuples to the namedtuple specificed by 'to'
    from a file-like object containing JSON
    Additional arguments are passed onto simplejson.load
    """
    loaded_obj = simplejson.load(fp)
    if not isinstance(loaded_obj, list):
        raise TypeError(
            f"{loaded_obj} is a {type(loaded_obj).__name__}, expected a top-level list from JSON source"
        )
    ds_items: List[NamedTuple] = []
    for lo in loaded_obj:
        ds_items.append(
            deserialize_namedtuple(lo, to, attr_deserializers, type_deserializers)
        )
    return ds_items
