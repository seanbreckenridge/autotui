# autotui

[![PyPi version](https://img.shields.io/pypi/v/autotui.svg)](https://pypi.python.org/pypi/autotui) [![Python 3.8](https://img.shields.io/pypi/pyversions/autotui.svg)](https://pypi.python.org/pypi/autotui) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

This uses type hints to convert [`NamedTuple`](https://docs.python.org/3.9/library/typing.html#typing.NamedTuple)'s (short struct-like classes) to JSON, and back to python objects.

It also wraps [`prompt_toolkit`](https://python-prompt-toolkit.readthedocs.io/en/master/index.html) to prompt the user and validate the input for common types, and is extendible to whatever types you want.

This has built-ins to prompt, validate and serialize:

- `int`
- `float`
- `bool`
- `str`
- `datetime`
- `Optional[<type>]`
- `List[<type>]`
- `Set[<type>]`
- other `NamedTuple`s (recursively)

I wrote this so that I don't have to repeatedly write boilerplate-y python code to validate/serialize/deserialize data. As a more extensive example of its usage, you can see my [`ttally`](https://github.com/seanbreckenridge/ttally) repo, which I use to track things like calories/water etc...

## Install

This requires `python3.8+`, specifically for modern [`typing`](https://docs.python.org/3/library/typing.html) support.

To install with pip, run:

    pip install autotui
    pip install 'autotui[optional]'  # to install dateparser, for parsing human-readable times

---

As an example, if I want to log whenever I drink water to a file:

```python
from datetime import datetime
from typing import NamedTuple

from autotui.shortcuts import load_prompt_and_writeback

class Water(NamedTuple):
    at: datetime
    glass_count: float

if __name__ == "__main__":
    load_prompt_and_writeback(Water, "~/.local/share/water.json")
```

<img src="https://raw.githubusercontent.com/seanbreckenridge/autotui/master/.assets/builtin_demo.gif">

Which, after running a few times, would create:

`~/.local/share/water.json`

```json
[
  {
    "at": 1598856786,
    "glass_count": 2.0
  },
  {
    "at": 1598856800,
    "glass_count": 1.0
  }
]
```

_(datetimes are serialized into epoch time)_

If I want to load the values back into python, its just:

```python
from autotui.shortcuts import load_from

class Water(NamedTuple):
    #... (same as above)

if __name__ == "__main__":
    print(load_from(Water, "~/.local/share/water.json"))

#[Water(at=datetime.datetime(2020, 8, 31, 6, 53, 6, tzinfo=datetime.timezone.utc), glass_count=2.0),
# Water(at=datetime.datetime(2020, 8, 31, 6, 53, 20, tzinfo=datetime.timezone.utc), glass_count=1.0)]
```

A lot of my usage of this only ever uses 3 functions in the [`autotui.shortcuts`](https://github.com/seanbreckenridge/autotui/blob/master/autotui/shortcuts.py) module; `dump_to` to dump a sequence of my `NamedTuple`s to a file, `load_from` to do the opposite, and `load_prompt_and_writeback`, to load values in, prompt me, and write back to the file.

#### Datetime prompt

There are two versions of the `datetime` prompt

- The one you see above using a dialog
- A live version which displays the parsed datetime while typing. Since that can cause some lag, it can be enabled by setting the `AUTOTUI_DATETIME_LIVE` environment variable, e.g., add `export AUTOTUI_DATETIME_LIVE=1` to your `.bashrc`/`.zshrc`

### Partial prompts

If you want to prompt for only a few fields, you can supply the `attr_use_values` or `type_use_values` to supply default values:

```python
# water-now script -- set any datetime values to now
from datetime import datetime
from typing import NamedTuple

from autotui import prompt_namedtuple
from autotui.shortcuts import load_prompt_and_writeback

class Water(NamedTuple):
    at: datetime
    glass_count: float

load_prompt_and_writeback(Water, "./water.json", type_use_values={datetime: datetime.now()})
# or specify it with a function (don't call datetime.now, just pass the function)
# so its called when its needed
val = prompt_namedtuple(Water, attr_use_values={"at": datetime.now})
```

Since you can specify a function to either of those arguments -- you're free to [write a completely custom prompt function](https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html) to prompt/grab data for that field however you want

### Custom Types

If you want to support custom types, or specify a special way to serialize another NamedTuple recursively, you can specify `type_validators`, and `type_[de]serializer` to handle the validation, serialization, deserialization for that type/attribute name.

As a more complicated example, heres a validator for [`timedelta`](https://docs.python.org/3.8/library/datetime.html#datetime.timedelta) (duration of time), being entered as MM:SS, and the corresponding serializers.

```python
# see examples/timedelta_serializer.py for imports

# handle validating the user input interactively
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
```

Output:

```
$ python3 ./examples/timedelta_serializer.py
'name' (str) > on the bus
'duration' (_timedelta) > 30:00
Action(name='on the bus', duration=datetime.timedelta(seconds=1800))
[{"name": "on the bus", "duration": 1800}]
Action(name='on the bus', duration=datetime.timedelta(seconds=1800))
Action(name='on the bus', duration=datetime.timedelta(seconds=1800))
```

The general philosophy I've taken for serialization and deserialization is send a warning if the types aren't what the NamedTuple expects, but load the values anyways. If serialization can't serialize something, it warns, and if `json.dump` doesn't have a way to handle it, it throws an error. When deserializing, all values are loaded from their JSON primitives, and then converted into their corresponding python equivalents; If the value doesn't exist, it warns and sets it to None, if theres a deserializer supplied, it uses that. This is meant to help facilitate quick TUIs, I don't want to have to fight with it.

Theres lots of examples on how this is handled/edge-cases in the [`tests`](./tests/test_autotui.py).

You can also take a look at the [`examples`](./examples)

# Tests

```bash
git clone https://github.com/seanbreckenridge/autotui
cd ./autotui
pip install '.[testing,optional]'
mypy ./autotui
pytest
```
