import json
from io import StringIO
from yaml import safe_dump, safe_load

from typing import List, Dict, Callable, Type, Any, TextIO, Optional, Literal

from .serialize import serialize_namedtuple, deserialize_namedtuple, PrimitiveType
from .typehelpers import NT, T


Format = Literal["json", "yaml"]


def _pretty_print(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if "indent" not in kwargs:
        kwargs["indent"] = "    "
    return kwargs


def namedtuple_sequence_dumps(
    nt_items: List[NT],
    *,
    attr_serializers: Optional[Dict[str, Callable[[T], PrimitiveType]]] = None,
    type_serializers: Optional[Dict[Type, Callable[[Any], PrimitiveType]]] = None,
    format: Optional[Format] = "json",
    **kwargs: Any,
) -> str:
    """
    Dump the list of namedtuples to a JSON string
    """
    s_obj: List[Dict[str, Any]] = []
    for nt in nt_items:
        s_obj.append(serialize_namedtuple(nt, attr_serializers, type_serializers))
    if format == "json":
        return json.dumps(s_obj, **_pretty_print(kwargs))
    elif format == "yaml":
        buf = StringIO()
        safe_dump(s_obj, buf, **kwargs)
        return buf.getvalue()
    else:
        raise ValueError(
            f"Format is None while trying to dump {nt_items[0] if len(nt_items) > 0 else nt_items}"
        )


def namedtuple_sequence_dump(
    nt_items: List[NT],
    fp: TextIO,
    *,
    attr_serializers: Optional[Dict[str, Callable[[T], PrimitiveType]]] = None,
    type_serializers: Optional[Dict[Type, Callable[[Any], PrimitiveType]]] = None,
    format: Optional[Format] = "json",
    **kwargs: Any,
) -> None:
    """
    Dump the list of namedtuples to a file-like object as JSON
    """
    # dump to string first, so JSON serialization errors dont cause data losses
    dumped: str = namedtuple_sequence_dumps(
        nt_items,
        attr_serializers=attr_serializers,
        type_serializers=type_serializers,
        format=format,
        **kwargs,
    )
    fp.write(dumped)


def _load_json(nt_string: str) -> Any:
    try:
        # speedup load if orjson is installed
        import orjson

        return orjson.loads(nt_string)
    except ImportError:
        pass
    return json.loads(nt_string)


def namedtuple_sequence_loads(
    nt_string: str,
    to: Type[NT],
    *,
    attr_deserializers: Optional[Dict[str, Callable[[PrimitiveType], Any]]] = None,
    type_deserializers: Optional[Dict[Type, Callable[[PrimitiveType], Any]]] = None,
    format: Optional[Format] = "json",
) -> List[NT]:
    """
    Load a list of namedtuples specificed by 'to' from a JSON string
    """
    if format == "json":
        loaded_obj = _load_json(nt_string)
    elif format == "yaml":
        loaded_obj = safe_load(nt_string)
    else:
        raise ValueError("unset format while trying to dump")
    if not isinstance(loaded_obj, list):
        raise TypeError(
            f"{loaded_obj} is a {type(loaded_obj).__name__}, expected a top-level list from JSON source"
        )
    ds_items: List[NT] = []
    for lo in loaded_obj:
        ds_items.append(
            deserialize_namedtuple(
                lo,
                to,
                attr_deserializers=attr_deserializers,
                type_deserializers=type_deserializers,
            )
        )
    return ds_items


def namedtuple_sequence_load(
    fp: TextIO,
    to: Type[NT],
    *,
    attr_deserializers: Optional[Dict[str, Callable[[PrimitiveType], Any]]] = None,
    type_deserializers: Optional[Dict[Type, Callable[[PrimitiveType], Any]]] = None,
    format: Optional[Format] = "json",
) -> List[NT]:
    """
    Load a list of namedtuples to the namedtuple specificed by 'to'
    from a file-like object containing JSON
    """
    return namedtuple_sequence_loads(
        fp.read(),
        to,
        attr_deserializers=attr_deserializers,
        type_deserializers=type_deserializers,
        format=format,
    )
