from typing import List, Dict, Callable, Type, NamedTuple, Any

import simplejson

from .serialize import serialize_namedtuple, deserialize_namedtuple


def _pretty_print(kwargs):
    if "indent" not in kwargs:
        kwargs["indent"] = 4 * " "
    return kwargs


def namedtuple_sequence_dumps(
    nt_items: List[NamedTuple],
    attr_serializers: Dict[str, Callable] = {},
    type_serializers: Dict[Type, Callable] = {},
    **kwargs,
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
    fp,
    attr_serializers: Dict[str, Callable] = {},
    type_serializers: Dict[Type, Callable] = {},
    **kwargs,
):
    """
    Dump the list of namedtuples to a file-like object as JSON
    Additional arguments are passed onto simplejson.dump
    """
    kwargs = _pretty_print(kwargs)
    s_obj: List[Dict[str, Any]] = []
    for nt in nt_items:
        s_obj.append(serialize_namedtuple(nt, attr_serializers, type_serializers))
    return simplejson.dump(s_obj, fp, **kwargs)


def namedtuple_sequence_loads(
    nt_string,
    to: NamedTuple,
    attr_deserializers: Dict[str, Callable] = {},
    type_deserializers: Dict[Type, Callable] = {},
    **kwargs,
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
    fp,
    to: NamedTuple,
    attr_deserializers: Dict[str, Callable] = {},
    type_deserializers: Dict[Type, Callable] = {},
    **kwargs,
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
