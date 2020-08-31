import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NamedTuple, Optional, List, Set

import simplejson
import pytest
import autotui
from autotui.exceptions import AutoTUIException


class P(NamedTuple):
    a: int
    b: float
    c: str
    d: datetime


class O(NamedTuple):
    a: Optional[int] = None
    b: Optional[str] = None


@dataclass(init=False)
class Weight(object):
    weight: float

    def __init__(self, some: str):
        if some.endswith("lbs"):
            self.weight = float(some.rstrip("lbs"))  # raises ValueError
        else:
            raise ValueError("weight doesn't end with 'lbs'")


class WeightData(NamedTuple):
    when: datetime
    data: Weight


def test_type_auto_handler():
    handler = autotui.AutoHandler(func=Weight, catch_errors=[ValueError])
    # use handler to specify how to create/catch
    funcs = autotui.namedtuple_prompt_funcs(
        WeightData, type_validators={Weight: handler}
    )
    assert len(funcs.keys()) == 2


def test_attr_auto_handler():
    handler = autotui.AutoHandler(func=Weight, catch_errors=[ValueError])
    funcs = autotui.namedtuple_prompt_funcs(
        WeightData, attr_validators={"data": handler}
    )
    assert len(funcs.keys()) == 2


def test_cant_handle():
    with pytest.raises(AutoTUIException):
        autotui.namedtuple_prompt_funcs(WeightData)


def test_prompt_funcs():
    autotui.namedtuple_prompt_funcs(P)
    autotui.namedtuple_prompt_funcs(L)
    autotui.namedtuple_prompt_funcs(O)


def test_basic_serialize():
    cur: datetime = datetime.now()
    timestamp: int = int(cur.timestamp())
    x = P(a=1, b=2.0, c="test", d=cur)
    xd = autotui.serialize_namedtuple(x)
    assert type(xd) == dict
    assert xd["a"] == 1
    assert xd["b"] == 2
    assert xd["c"] == "test"
    assert xd["d"] == timestamp
    simplejson.dumps(xd)


def weight_serializer(weight_obj: Weight) -> float:
    return weight_obj.weight


def weight_deserializer(weight_val: float) -> Weight:
    return Weight(f"{weight_val}lbs")


def test_supply_serializer_deserializer():
    cur: datetime = datetime.now()
    timestamp: int = int(cur.timestamp())
    w = WeightData(when=cur, data=Weight("20lbs"))
    wd = autotui.serialize_namedtuple(w, type_serializers={Weight: weight_serializer})
    assert type(wd) == dict
    assert wd["data"] == 20.0
    assert wd["when"] == timestamp

    # test dumping to JSON
    assert simplejson.dumps(wd) == '{"when": ' + str(timestamp) + ', "data": 20.0}'

    # JSON, there and back
    w_jsonstr = simplejson.dumps(wd)
    w_loaded = simplejson.loads(w_jsonstr)
    w_loaded_obj = autotui.deserialize_namedtuple(
        w_loaded, WeightData, type_deserializers={Weight: weight_deserializer}
    )
    assert int(w_loaded_obj.when.timestamp()) == timestamp
    assert w_loaded_obj.data == Weight("20lbs")

    wd = autotui.serialize_namedtuple(w, attr_serializers={"data": weight_serializer})
    assert type(wd) == dict
    assert wd["data"] == 20.0
    assert wd["when"] == timestamp

    bw = autotui.deserialize_namedtuple(
        wd, WeightData, type_deserializers={Weight: weight_deserializer}
    )
    assert type(bw) == type(w)
    # annoyig becuase of tz_info
    # assert bw.when == cur
    assert int(bw.when.timestamp()) == timestamp
    assert bw.data == Weight("20lbs")

    # supply attr_deserializers instead
    bw = autotui.deserialize_namedtuple(
        wd, WeightData, attr_deserializers={"data": weight_deserializer}
    )
    assert type(bw) == type(w)
    # annoyig becuase of tz_info
    # assert bw.when == cur
    assert int(bw.when.timestamp()) == timestamp
    assert bw.data == Weight("20lbs")


class L(NamedTuple):
    a: Optional[List[int]]
    b: Set[bool]


def test_basic_iterable_deserialize():
    loaded = simplejson.loads('{"a": [1, 2, 3], "b": [true]}')
    l = autotui.deserialize_namedtuple(loaded, L)
    l.a == [1, 2, 3]
    l.b == {True}


def test_leave_optional_collection_none():
    loaded = simplejson.loads('{"b": [true]}')
    l = autotui.deserialize_namedtuple(loaded, L)
    assert l.a == None
    assert l.b == {True}


def test_non_optional_default_to_empty_collection():
    loaded = {"b": [True]}
    l = autotui.deserialize_namedtuple(loaded, L)
    assert l.b == {True}


def test_default_value_on_non_optional_collection():
    loaded = simplejson.loads("{}")
    with pytest.warns(None) as record:
        l = autotui.deserialize_namedtuple(loaded, L)
    assert len(record) == 2
    assert "Expected key b on non-optional field" in str(record[0].message)
    assert (
        "No value loaded for non-optional type b, defaulting to empty container"
        in str(record[1].message)
    )
    assert l.a == None
    assert l.b == set()


class X(NamedTuple):
    a: int


def test_expected_key_warning():
    loaded = simplejson.loads("{}")
    with pytest.warns(None) as record:
        x = autotui.deserialize_namedtuple(loaded, X)
    assert len(record) == 2
    assert "Expected key a on non-optional field" in str(record[0].message)
    assert x.a == None
    assert 'For value None, expected type int, found NoneType' == str(record[1].message)

class X_OPT(NamedTuple):
    a: Optional[int]

def test_optional_key_loads_with_no_warnings():
    loaded = simplejson.loads("{}")
    x = autotui.deserialize_namedtuple(loaded, X_OPT)
    assert x.a is None

def deserialize_a(x: Optional[int]):
    if x is None:
        return 0
    else:
        return x

def test_optional_specified_null_deserializer():
    # note: type_deserializers dont specify the type of the dynamically loaded value,
    # they specify the type specified by the namedtuple.
    # so cant do something like
    # loaded = simplejson.loads("{}")
    # none_deserializer = {type(None): lambda _x: 0}
    # x = autotui.deserialize_namedtuple(loaded, X_OPT, type_deserializers=none_deserializer)
    # assert x.a == 0
    # in this case, because it expects int. The none_deserializer is never used, becuase
    # None is not a type on X_OPT. Could do it against int,
    # should use an attr_deserializer in this case
    loaded = simplejson.loads('{"a": null}')
    attr_deserializers = {'a': deserialize_a}
    x = autotui.deserialize_namedtuple(loaded, X_OPT, attr_deserializers=attr_deserializers)
    assert x.a == 0

    # could also do like
    loaded = simplejson.loads('{"a": null}')
    type_deserializers = {int: deserialize_a}  # specify int, not NoneType
    x = autotui.deserialize_namedtuple(loaded, X_OPT, type_deserializers=type_deserializers)
    assert x.a == 0

class LL(NamedTuple):
    a: List[int]

def test_null_in_containers_warns():
    loaded = simplejson.loads('{"a": [1,null,3]}')
    with pytest.warns(None) as record:
        x = autotui.deserialize_namedtuple(loaded, LL)
    assert len(record) == 1
    assert "expected type int, found NoneType" in str(record[0].message)
    assert x.a == [1, None, 3]

def test_serialize_none_warning():
    x = X(a=None)
    with pytest.warns(None) as record:
        sx = autotui.serialize_namedtuple(x)
    assert len(record) == 1
    assert "has a value of None" in str(record[0].message)
    assert sx["a"] is None


def test_basic_sequence_dumps_loads():
    x = [X(a=1), X(a=5)]
    xlist_str: str = autotui.namedtuple_sequence_dumps(x, indent=None)
    assert xlist_str == '[{"a": 1}, {"a": 5}]'
    back_to_x: List[X] = autotui.namedtuple_sequence_loads(xlist_str, to=X)
    assert type(back_to_x) == list
    assert back_to_x[0] == X(a=1)
    assert back_to_x[1] == X(a=5)


def test_doesnt_load_non_iterable():
    non_iterable = '{"a": 1}'
    with pytest.raises(TypeError) as err:
        autotui.namedtuple_sequence_loads(non_iterable, X, indent=None)
    assert "{'a': 1} is a dict, expected a top-level list from JSON source" in str(err)


@dataclass(init=False)
class Temperature:
    celcius: float

    def __init__(self, reading_raw: str):
        if len(reading_raw) < 1:
            raise ValueError("Not enough data provided!")
        scale = reading_raw[-1]
        if scale not in ["F", "C"]:
            raise TypeError("Must end with 'F' or 'C'")
        tempstr = reading_raw.rstrip("C").rstrip("F")
        if scale == "C":
            self.celcius = float(tempstr)  # could raise ValueError
        else:
            self.celcius = (float(tempstr) - 32) * 5 / 9


class Reading(NamedTuple):
    when: datetime
    temp: Temperature


def serialize_temp(x: Temperature) -> float:
    return x.celcius


def deserialize_temp(x: float) -> Temperature:
    return Temperature(f"{x}C")


def test_custom_handles_serializers():
    t = Temperature("20C")
    assert t.celcius == 20.0
    # just test creating the namedtuple prompt
    handler = autotui.AutoHandler(
        func=Temperature, catch_errors=[TypeError, ValueError]
    )
    funcs = autotui.namedtuple_prompt_funcs(
        Reading, type_validators={Temperature: handler}
    )
    assert len(funcs.keys()) == 2
    f = tempfile.NamedTemporaryFile(delete=False)
    type_serializers = {Temperature: serialize_temp}
    attr_deserializers = {"temp": deserialize_temp}
    d1 = datetime.now()
    d2 = datetime.now()
    readings: List[Reading] = [
        Reading(when=d1, temp=Temperature("20C")),
        Reading(when=d2, temp=Temperature("19C")),
    ]
    with open(f.name, "w") as fp:
        autotui.namedtuple_sequence_dump(
            readings, fp, type_serializers=type_serializers, indent=None
        )

    # loads first, check warning when no deserializer provided
    with open(f.name) as fp:
        str_contents = fp.read()

    with pytest.warns(None) as record:
        readings_back = autotui.namedtuple_sequence_loads(str_contents, to=Reading)
    assert len(record) >= 1
    assert "No known way to deserialize" in str(record[0].message)
    assert len(readings_back) == 2
    assert readings_back[0].temp == 20.0
    # then load
    with open(f.name) as fp:
        rbr = autotui.namedtuple_sequence_load(
            fp, to=Reading, attr_deserializers=attr_deserializers
        )
    assert len(rbr) == 2
    assert int(rbr[0].when.timestamp()) == int(d1.timestamp())
    assert rbr[0].temp == Temperature("20C")

    # delete file
    os.unlink(f.name)

class Action(NamedTuple):
    t: timedelta

def test_no_way_to_handle_propting():
    with pytest.raises(AutoTUIException) as aex:
        autotui.prompt_namedtuple(Action)
    assert str(aex.value) == "no way to handle prompting timedelta"

