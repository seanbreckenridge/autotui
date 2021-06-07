import warnings
from typing import Dict, Type, Callable, Any, Union, Optional
from datetime import datetime, timezone

from .typehelpers import (
    is_supported_container,
    get_collection_types,
    is_primitive,
    strip_optional,
    PrimitiveType,
    inspect_signature_dict,
    is_namedtuple_type,
    NT,
    T,
)


def _serialize_type(
    value: Any,
    cls: Type,
    is_optional: bool,
    type_serializers: Dict[Type, Callable[[Any], PrimitiveType]],
) -> Optional[Union[PrimitiveType, Any]]:
    """
    Gets one of the built-in serializers or a type_serializers from the user,
    and serializes the value from the NamedTuple to that
    """
    # use type serializers first, user may have already specified some way
    # to handle nulls using a custom function
    if cls in type_serializers:
        return type_serializers[cls](value)
    # value can still be None here, we checked against namedtuple field type, not the dynamic
    # type of the value given
    if value is None:
        if not is_optional:
            warnings.warn(
                f"No value for non-optional type {value}, attempting to be serialized to {cls.__name__}"
            )
        return None  # serialized to null
    else:
        if cls == datetime:
            return int(value.timestamp())
        elif is_primitive(cls):
            return value  # all other primitives are JSON compatible
        elif is_namedtuple_type(cls):
            # if the attribute for this value is another NamedTuple,
            # recursively serialize the value
            return serialize_namedtuple(value, type_serializers=type_serializers)
    warnings.warn(f"No known way to serialize {cls.__name__}")
    return value
    # raise? it'll fail when json module fails to do it anyways, so
    # might as well leave it
    # raise AutoTUIException(f"no known way to serialize {cls}")


def serialize_namedtuple(
    nt: NT,
    attr_serializers: Optional[Dict[str, Callable[[T], PrimitiveType]]] = None,
    type_serializers: Optional[Dict[Type, Callable[[T], PrimitiveType]]] = None,
) -> Dict[str, Any]:
    """
    Serializes a NamedTuples to a JSON-compatible dictionary

    If the user provides attr_serializers or type_serializers, uses those
    instead of the defaults.
    """
    attr_serializers = attr_serializers or {}
    type_serializers = type_serializers or {}

    json_dict: Dict[str, Any] = {}

    for attr_name, nt_annotation in inspect_signature_dict(nt.__class__).items():
        attr_type, is_optional = strip_optional(nt_annotation)

        attr_value = getattr(nt, attr_name)

        # if the user specified a serializer for this attribute name, use that
        if attr_name in attr_serializers.keys():
            # serialize the value into the return dict
            json_dict[attr_name] = attr_serializers[attr_name](attr_value)
            continue
        if is_supported_container(attr_type):
            container_type, internal_type = get_collection_types(attr_type)
            # if is_optional == True, attr_value can't be None
            # if we're serialzing an non-optional, and the value is null,
            # set it to an empty container...
            # you can't pass a type_serializer (which is passed to _serialize_type)
            # to handle the internal type of a collection, if the collection is None
            # you *can* use an attr_serializer to handle the entire field, but
            # not the internal type
            if attr_value is None:
                if not is_optional:
                    warnings.warn(
                        f"No value found for non-optional type {attr_name}, defaulting to empty container"
                    )
                    json_dict[attr_name] = container_type([])
                else:
                    json_dict[attr_name] = None
                continue
            # TODO: wrap TypeError? if attr_value is iterable,
            # might not work as expected if attr_value is a string, and we iterate over chars
            json_dict[attr_name] = [
                _serialize_type(x, internal_type, False, type_serializers)
                for x in attr_value
            ]
        else:
            # single type, like:
            # a: int
            # b: Optional[str]
            # contrary to above, if attr_value here is None, we can try to use
            # any type_serializers for the attr_type that the user passed.
            # If that doesn't work, it warns the user that theres no way to
            # serialize a NoneType
            json_dict[attr_name] = _serialize_type(
                attr_value, attr_type, is_optional, type_serializers
            )
    return json_dict


def _deserialize_type(
    value: Any,
    cls: Type,
    is_optional: bool,
    type_deserializers: Dict[Type, Callable[[PrimitiveType], T]],
) -> Optional[Union[PrimitiveType, Any]]:
    """
    Gets one of the built-in deserializers or a type_deserializers from the user,
    and deserializes the loaded value to the NamedTuple representation
    """
    if cls in type_deserializers:
        return type_deserializers[cls](value)
    # is falsey value
    if value is None:
        if is_optional:
            return None
        else:
            if type(value) != cls:
                warnings.warn(
                    f"For value {value}, expected type {cls.__name__}, found {type(value).__name__}"
                )
            return value
    elif cls == datetime:
        # serialize into epoch time
        return datetime.fromtimestamp(int(value), timezone.utc)
    elif cls == int:
        return int(value)
    elif cls == float:
        return float(value)
    elif cls == str:
        return str(value)
    elif cls == bool:
        if type(value) == str:
            lval = value.lower()
            if lval == "true":
                return True
            elif lval == "false":
                return False
        return bool(value)
    else:
        if is_primitive(cls):
            return value  # all other primitives are JSON compatible
        elif is_namedtuple_type(cls):
            return deserialize_namedtuple(
                value, to=cls, type_deserializers=type_deserializers
            )
    warnings.warn(f"No known way to deserialize {cls}")
    return value


def deserialize_namedtuple(
    obj: Dict[str, Any],
    to: Type[NT],
    attr_deserializers: Optional[Dict[str, Callable[[PrimitiveType], T]]] = None,
    type_deserializers: Optional[Dict[Type, Callable[[PrimitiveType], T]]] = None,
) -> NT:
    """
    Deserializes a Dict loaded from JSON into a NamedTuple object

    If the user provides attr_deserializers or type_deserializers, uses those
    instead of the defaults.
    """
    attr_deserializers = attr_deserializers or {}
    type_deserializers = type_deserializers or {}

    # temporary to hold values, will splat into namedtuple at the end of func
    json_dict: Dict[str, Any] = {}

    for attr_name, nt_annotation in inspect_signature_dict(to).items():
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
                        _deserialize_type(
                            x, internal_type, is_optional, type_deserializers
                        )
                        for x in loaded_value
                    ]
                )
        else:
            json_dict[attr_name] = _deserialize_type(
                loaded_value, attr_type, is_optional, type_deserializers
            )
    return to(**json_dict)  # type: ignore[operator,no-any-return,call-arg]
