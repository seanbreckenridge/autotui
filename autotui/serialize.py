import warnings
import inspect
from typing import Dict, Type, Callable, NamedTuple, Any
from datetime import datetime, timezone

from .typehelpers import (
    is_supported_container,
    get_collection_types,
    is_primitive,
    strip_optional,
)


def _serialize_datetime(dt: datetime) -> int:
    assert type(dt) == datetime
    return int(dt.timestamp())


def _serialize_type(value: Any, cls: Type, type_serializers: Dict[Type, Callable]):
    """
    Gets one of the built-in serializers or a type_serializers from the user,
    and serializes the value from the NamedTuple to that
    """
    if cls in type_serializers:
        return type_serializers[cls](value)
    if is_primitive(cls):
        if cls == datetime:
            # serialize into epoch time
            return _serialize_datetime(value)
        else:
            return value  # all other primitives are JSON compatible
    warnings.warn(f"No known way to serialize {cls}")
    return value
    # raise? it'll fail when simplejson fails to do it anyways, so
    # might as well leave it
    # raise AutoTUIException(f"no known way to serialize {cls}")


def serialize_namedtuple(
    nt: NamedTuple,
    attr_serializers: Dict[str, Callable] = {},
    type_serializers: Dict[Type, Callable] = {},
) -> Dict:
    """
    Serializes a List of NamedTuples to a JSON-compatible dictionary

    If the user provides attr_serializers or type_serializers, uses those
    instead of the defaults.

    by default, supports:
    int
    float
    str
    datetime (converts to epoch time)
    Optional[<supported_types>]
    List[<supported_types>]
    Set[<supported_types>] (Uses a List)
    """
    sig = inspect.signature(nt.__class__)
    json_dict: Dict[str, Any] = {}

    for attr_name, param_type in sig.parameters.items():
        nt_annotation = param_type.annotation
        attr_type, is_optional = strip_optional(nt_annotation)

        attr_value = getattr(nt, attr_name)

        # if the user specified a serializer for this attribute name, use that
        if attr_name in attr_serializers.keys():
            # serialize the value into the return dict
            json_dict[attr_name] = attr_serializers[attr_name](attr_value)
            continue
        # if the user didn't supply a way to handle this by attr_name,
        # and if its still none, it should be serialized to null
        if attr_value is None:
            if not is_optional:
                warnings.warn("Non-optional attribute {attr_value} has a value of None")
            json_dict[attr_name] = None
        if is_supported_container(attr_type):
            container_type, internal_type = get_collection_types(attr_type)
            json_dict[attr_name] = [
                _serialize_type(x, internal_type, type_serializers) for x in attr_value
            ]
        else:
            # single type, like:
            # a: int
            # b: Optional[str]
            json_dict[attr_name] = _serialize_type(
                attr_value, attr_type, type_serializers
            )
    return json_dict


def _deserialize_datetime(secs_since_epoch: int) -> datetime:
    return datetime.fromtimestamp(secs_since_epoch, timezone.utc)


def _deserialize_type(value: Any, cls: Type, is_optional: bool, type_deserializers: Dict[Type, Callable]):
    """
    Gets one of the built-in deserializers or a type_deserializers from the user,
    and deserializes the loaded value to the NamedTuple representation
    """
    if cls in type_deserializers:
        return type_deserializers[cls](value)
    if is_optional and value is None:
        return value
    if is_primitive(cls):
        if cls == datetime:
            # serialize into epoch time
            return _deserialize_datetime(value)
        else:
            for expected_type in [float, int, bool, str]:
                if cls == expected_type:
                    if type(value) != expected_type:
                        warnings.warn(f"For value {value}, expected type {expected_type.__name__}, found {type(value).__name__}")
            return value  # all other primitives are JSON compatible
    warnings.warn(f"No known way to deserialize {cls}")
    return value


def deserialize_namedtuple(
    obj: Dict[str, Any],
    to: NamedTuple,
    attr_deserializers: Dict[str, Callable] = {},
    type_deserializers: Dict[Type, Callable] = {},
):
    """
    Deserializes a Dict loaded from JSON into a NamedTuple object

    If the user provides attr_deserializers or type_deserializers, uses those
    instead of the defaults.

    by default, supports:
    int
    float
    str
    datetime (converts to from epoch seconds to UTC)
    Optional[<supported_types>]
    List[<supported_types>]
    Set[<supported_types>] (Removes duplicates if any exist in the JSON list)
    """
    sig = inspect.signature(to)
    # temporary to hold values, will splat into namedtuple at the end of func
    json_dict: Dict[str, Any] = {}

    for attr_name, param_type in sig.parameters.items():
        nt_annotation = param_type.annotation
        attr_type, is_optional = strip_optional(nt_annotation)

        # could be None
        loaded_value: Any = obj.get(attr_name)

        # if the user specified a deserializer for this attribute name, use that
        # do attr_deserializers first, user func may have specified a way to deserialize None
        if attr_name in attr_deserializers.keys():
            json_dict[attr_name] = attr_deserializers[attr_name](loaded_value)
            continue


        # key wasnt in loaded value
        if loaded_value is None and not is_optional:
            warnings.warn(
                f"Expected key {attr_name} on non-optional field, no such key existed in loaded data"
            )

        if is_supported_container(attr_type):
            container_type, internal_type = get_collection_types(attr_type)
            # if we didnt load anything (null or key didnt exist)
            if loaded_value is None:
                if not is_optional:
                    warnings.warn(
                        f"No value loaded for non-optional type {attr_name}, defaulting to empty container"
                    )
                    json_dict[attr_name] = container_type([])
                else:
                    # else, set the optional container to none
                    # e.g. Optional[List[int]]
                    json_dict[attr_name] = None
            else:
                # if list contains nulls, _deserialize_type warns
                # its sort of up to the user how they want to use
                # - Optional[List[int]]
                # should the value be null? should it be empty list?
                # Does it somehow mean
                # - List[Optional[int]] (it shouldnt)
                # this warns in cases I think are wrong, but doesn't enforce anything
                json_dict[attr_name] = container_type(
                    [
                        _deserialize_type(x, internal_type, is_optional, type_deserializers)
                        for x in loaded_value
                    ]
                )
        else:
            json_dict[attr_name] = _deserialize_type(
                loaded_value, attr_type, is_optional, type_deserializers
            )
    return to(**json_dict)
