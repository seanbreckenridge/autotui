from typing import NamedTuple
from datetime import timedelta
from dataclasses import dataclass
from autotui import (
    prompt_namedtuple,
    namedtuple_sequence_dumps,
    namedtuple_sequence_loads,
    AutoHandler,
    namedtuple_prompt_funcs,
)

# handle validating the user input
# can throw a ValueError
def _timedelta(user_input: str) -> timedelta:
    if len(user_input.strip()) == 0:
        raise ValueError("Not enough input!")
    minutes, _, seconds = user_input.partition(":")
    # could throw ValueError
    return timedelta(minutes=float(minutes), seconds=float(seconds))


# serializer for timedelta, converts to JSON-compatible integer
def to_seconds(t: timedelta) -> int:
    return int(t.total_seconds())


# deserializer from integer to timedelta
def from_seconds(seconds: int) -> timedelta:
    return timedelta(seconds=seconds)


# The data we want to persist to the file
class Action(NamedTuple):
    name: str
    duration: timedelta


# AutoHandler describes what function to use to validate
# user input, and which errors to wrap while validating
timedelta_handler = AutoHandler(
    func=_timedelta,  # accepts the string the user is typing as input
    catch_errors=[ValueError],
)

# Note: validators are of type
# Dict[Type, AutoHandler]
# serializer/deserializers are
# Dict[Type, Callable]
# the Callable accepts one argument,
# which is either the python value being serialized
# or the JSON value being deserialized

# use the validator to prompt the user for the NamedTuple data
# name: str automatically uses a generic string prompt
# duration: timedelta gets handled by the type_validator
a = prompt_namedtuple(
    Action,
    type_validators={
        timedelta: timedelta_handler,
    },
)


# Note: this specifies timedelta as the type,
# not int. It uses what the NamedTuple
# specifies as the type for that field, not
# the type of the value thats loaded from JSON

# dump to JSON
a_str: str = namedtuple_sequence_dumps(
    [a],
    type_serializers={
        timedelta: to_seconds,
    },
    indent=None,
)

# load from JSON
a_load = namedtuple_sequence_loads(
    a_str,
    to=Action,
    type_deserializers={
        timedelta: from_seconds,
    },
)[0]

# can also specify with attributes instead of types
a_load2 = namedtuple_sequence_loads(
    a_str,
    to=Action,
    attr_deserializers={
        "duration": from_seconds,
    },
)[0]

print(a)
print(a_str)
print(a_load)
print(a_load2)
