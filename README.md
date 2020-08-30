## autotui

This uses type hints to convert `NamedTuple`'s to JSON, and back to python objects.

It also wraps [`prompt_toolkit`](https://python-prompt-toolkit.readthedocs.io/en/master/index.html) to prompt the user and validate the input for common types, and is extendible to whatever types you want.

This has built-ins to prompt, validate and serialize:

* `int`
* `float`
* `bool`
* `str`
* `datetime`
* `Optional[<type>]`
* `List[<type>]`
* `Set[<type>]`

Note: Doesn't support all of these recursively, if your [algebraic data type](https://en.wikipedia.org/wiki/Algebraic_data_type) is getting to complicated and `autotui` can't parse it, you can always specify another `NamedTuple` as the type and pass a `type_validators`/`type_[de]serializer` to handle the validation/serialization/deserialization for that type/attribute name. (see below for examples)

I wrote this so that I don't have to repeatedly write boilerplate-y python code to validate/serialize/deserialize data. As an example, if I want to log whenever I drink water to a file:

```
from autotui import *

# something to persist to a file
class Water(NamedTuple):
    at: datetime
    glass_count: float

w = prompt_namedtuple(Water)  # prompts me and validates the input by inpsecting types
# Water(at=datetime.datetime(2020, 8, 30, 9, 26, 24, 168034), glass_count=5.0)

# convert it to JSON
s = namedtuple_sequence_dumps([w], indent=None)
# [{"at": 1598805438, "glass_count": 5.0}]

# and back to the NamedTuple
b = autotui.namedtuple_sequence_loads(s, to=Water)
# [Water(at=datetime.datetime(2020, 8, 30, 16, 40, 1, tzinfo=datetime.timezone.utc), glass_count=5.0)]
```

For what the user input/validation looks like, see [Video Demo]()

TODO:

- push a real release to pypi
- add documentation to readme (look at [tests](https://github.com/seanbreckenridge/autotui/blob/master/tests/test_autotui.py) for now)
- add demo and videos
- add shortcut to serialize/deserialize to XDG data dir automatically

## Installation

#### Requires:

This requires `python3.8+`, specifically for modern [`typing`](https://docs.python.org/3/library/typing.html) support.

To install with pip, run:

    pip3 install autotui

## Run

```
TODO: Fill this out

Usage: ...
```

# Tests

    pip3 install 'autotui[testing]'
    pytest  # in the root directory
