import json

from typing import List, Dict, Callable, Type, Any, TextIO, Optional

from .serialize import serialize_namedtuple, deserialize_namedtuple, PrimitiveType
from .typehelpers import NT, T


def _pretty_print(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if "indent" not in kwargs:
        kwargs["indent"] = "    "
    return kwargs


def namedtuple_sequence_dumps(
    nt_items: List[NT],
    attr_serializers: Optional[Dict[str, Callable[[T], PrimitiveType]]] = None,
    type_serializers: Optional[Dict[Type, Callable[[Any], PrimitiveType]]] = None,
    **kwargs: Any,
) -> str:
    """
    Dump the list of namedtuples to a JSON string
    """
    s_obj: List[Dict[str, Any]] = []
    for nt in nt_items:
        s_obj.append(serialize_namedtuple(nt, attr_serializers, type_serializers))
    return json.dumps(s_obj, **_pretty_print(kwargs))


def namedtuple_sequence_dump(
    nt_items: List[NT],
    fp: TextIO,
    attr_serializers: Optional[Dict[str, Callable[[T], PrimitiveType]]] = None,
    type_serializers: Optional[Dict[Type, Callable[[Any], PrimitiveType]]] = None,
    **kwargs: Any,
) -> None:
    """
    Dump the list of namedtuples to a file-like object as JSON
    """
    # dump to string first, so JSON serialization errors dont cause data losses
    dumped: str = namedtuple_sequence_dumps(
        nt_items, attr_serializers, type_serializers, **kwargs
    )
    fp.write(dumped)


def namedtuple_sequence_loads(
    nt_string: str,
    to: Type[NT],
    attr_deserializers: Optional[Dict[str, Callable[[PrimitiveType], Any]]] = None,
    type_deserializers: Optional[Dict[Type, Callable[[PrimitiveType], Any]]] = None,
) -> List[NT]:
    """
    Load a list of namedtuples specificed by 'to' from a JSON string
    """
    loaded_obj = json.loads(nt_string)
    if not isinstance(loaded_obj, list):
        raise TypeError(
            f"{loaded_obj} is a {type(loaded_obj).__name__}, expected a top-level list from JSON source"
        )
    ds_items: List[NT] = []
    for lo in loaded_obj:
        ds_items.append(
            deserialize_namedtuple(lo, to, attr_deserializers, type_deserializers)
        )
    return ds_items


def namedtuple_sequence_load(
    fp: TextIO,
    to: Type[NT],
    attr_deserializers: Optional[Dict[str, Callable[[PrimitiveType], Any]]] = None,
    type_deserializers: Optional[Dict[Type, Callable[[PrimitiveType], Any]]] = None,
) -> List[NT]:
    """
    Load a list of namedtuples to the namedtuple specificed by 'to'
    from a file-like object containing JSON
    """
    return namedtuple_sequence_loads(
        fp.read(), to, attr_deserializers, type_deserializers
    )
