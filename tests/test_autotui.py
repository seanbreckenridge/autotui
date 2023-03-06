import sys
import os
import json
import tempfile
import warnings
from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NamedTuple, Optional, List, Set, Dict, Any
from enum import Enum

import pytest
import autotui
from yaml import safe_load
from autotui.exceptions import AutoTUIException
from autotui.shortcuts import load_from, dump_to
from autotui.options import options

Json = Dict[str, Any]


class P(NamedTuple):
    a: int
    b: float
    c: str
    d: datetime


class O(NamedTuple):
    a: Optional[int] = None
    b: Optional[str] = None


def test_int_converts_to_float_no_warning() -> None:
    p = P(a=5, b=5, c="test", d=datetime.now())

    with warnings.catch_warnings(record=True) as record:
        serialized = autotui.serialize_namedtuple(p)
        # not converted when serialized
        assert serialized["b"] == 5

        # since the type hint specifies a float, convert
        # the 5 to a float
        deserialized: P = autotui.deserialize_namedtuple(serialized, to=P)
        assert isinstance(deserialized.b, float)
        assert deserialized.b == 5.0

    assert len(record) == 0


def test_default_values() -> None:
    now = datetime.now()
    current_datetime_func = lambda: now

    # shouldnt prompt interactively because were setting defaults
    val = autotui.prompt_namedtuple(
        P,
        attr_use_values={"a": 5, "b": 10.0},
        type_use_values={str: "something", datetime: current_datetime_func},
    )

    assert P(a=5, b=10.0, c="something", d=now) == val


class Def(NamedTuple):
    x: int
    y: str

    @staticmethod
    def attr_use_values() -> Dict:
        return {"x": 5}

    @staticmethod
    def type_use_values() -> Dict:
        return {str: "default"}


def test_default_values_w_class() -> None:
    d = autotui.prompt_namedtuple(Def)
    assert d == Def(x=5, y="default")

    # override with kwarg
    d = autotui.prompt_namedtuple(Def, type_use_values={str: "something"})
    assert d == Def(x=5, y="something")


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


def test_type_auto_handler() -> None:
    handler = autotui.AutoHandler(func=Weight, catch_errors=[ValueError])
    # use handler to specify how to create/catch
    funcs = autotui.namedtuple_prompt_funcs(
        WeightData, type_validators={Weight: handler}
    )
    assert len(funcs.keys()) == 2


def test_attr_auto_handler() -> None:
    handler = autotui.AutoHandler(func=Weight, catch_errors=[ValueError])
    funcs = autotui.namedtuple_prompt_funcs(
        WeightData, attr_validators={"data": handler}
    )
    assert len(funcs.keys()) == 2


def test_cant_handle() -> None:
    with pytest.raises(AutoTUIException):
        autotui.namedtuple_prompt_funcs(WeightData)


def test_prompt_funcs() -> None:
    autotui.namedtuple_prompt_funcs(P)
    autotui.namedtuple_prompt_funcs(L)
    autotui.namedtuple_prompt_funcs(O)


def test_basic_serialize() -> None:
    cur: datetime = datetime.now()
    timestamp: int = int(cur.timestamp())
    x = P(a=1, b=2.0, c="test", d=cur)
    xd = autotui.serialize_namedtuple(x)
    assert type(xd) == dict
    assert xd["a"] == 1
    assert xd["b"] == 2
    assert xd["c"] == "test"
    assert xd["d"] == timestamp
    json.dumps(xd)


def weight_serializer(weight_obj: Weight) -> float:
    return weight_obj.weight


def weight_deserializer(weight_val: float) -> Weight:
    return Weight(f"{weight_val}lbs")


def test_supply_serializer_deserializer() -> None:
    cur: datetime = datetime.now()
    timestamp: int = int(cur.timestamp())
    w = WeightData(when=cur, data=Weight("20lbs"))
    wd = autotui.serialize_namedtuple(w, type_serializers={Weight: weight_serializer})
    assert type(wd) == dict
    assert wd["data"] == 20.0
    assert wd["when"] == timestamp

    # test dumping to JSON
    assert json.dumps(wd) == '{"when": ' + str(timestamp) + ', "data": 20.0}'

    # JSON, there and back
    w_jsonstr: str = json.dumps(wd)
    w_loaded: Json = json.loads(w_jsonstr)
    w_loaded_obj: Json = autotui.deserialize_namedtuple(
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
    # annoyig because of tz_info
    # assert bw.when == cur
    assert int(bw.when.timestamp()) == timestamp
    assert bw.data == Weight("20lbs")

    # supply attr_deserializers instead
    bw = autotui.deserialize_namedtuple(
        wd, WeightData, attr_deserializers={"data": weight_deserializer}
    )
    assert type(bw) == type(w)
    # annoyig because of tz_info
    # assert bw.when == cur
    assert int(bw.when.timestamp()) == timestamp
    assert bw.data == Weight("20lbs")


class L(NamedTuple):
    a: Optional[List[int]]
    b: Set[bool]


def test_is_namedtuple() -> None:
    from autotui.typehelpers import is_namedtuple_type, is_namedtuple_obj

    l = L(a=[], b=set())
    assert is_namedtuple_obj(l)
    assert is_namedtuple_type(L)
    assert not is_namedtuple_obj([5])
    assert not is_namedtuple_type(int)


def test_basic_iterable_deserialize() -> None:
    loaded: Json = json.loads('{"a": [1, 2, 3], "b": [true]}')
    l = autotui.deserialize_namedtuple(loaded, L)
    l.a == [1, 2, 3]
    l.b == {True}


def test_leave_optional_collection_none() -> None:
    loaded: Json = json.loads('{"b": [true]}')
    l = autotui.deserialize_namedtuple(loaded, L)
    # shouldnt warn, just serializes to None
    assert l.a == None
    assert l.b == {True}


def test_default_value_on_non_optional_collection():
    loaded: Json = json.loads("{}")
    with warnings.catch_warnings(record=True) as record:
        l = autotui.deserialize_namedtuple(loaded, L)
    assert len(record) == 2
    assert (
        "Expected key b on non-optional field, no such key existed in loaded data"
        == str(record[0].message)
    )
    assert (
        "No value loaded for non-optional type b, defaulting to empty container"
        in str(record[1].message)
    )
    assert l.a == None
    assert l.b == set()


class X(NamedTuple):
    a: int


def test_expected_key_warning() -> None:
    loaded = json.loads("{}")
    with warnings.catch_warnings(record=True) as record:
        x = autotui.deserialize_namedtuple(loaded, X)
    assert len(record) == 2
    assert "Expected key a on non-optional field" in str(record[0].message)
    assert x.a == None
    assert "For value None, expected type int, found NoneType" == str(record[1].message)


class X_OPT(NamedTuple):
    a: Optional[int]


def test_optional_key_loads_with_no_warnings() -> None:
    loaded = json.loads("{}")
    x = autotui.deserialize_namedtuple(loaded, X_OPT)
    assert x.a is None


# this is a way to handle serializing null types into
# some default value
def deserialize_a(x: Optional[int]) -> int:
    if x is None:
        return 0
    else:
        return x


# could be done similarly to serialize nulls into a default


def test_optional_specified_null_deserializer() -> None:
    # note: type_deserializers dont specify the type of the dynamically loaded value,
    # they specify the type specified by the namedtuple.
    # so cant do something like
    # loaded = json.loads("{}")
    # none_deserializer = {type(None): lambda _x: 0}
    # x = autotui.deserialize_namedtuple(loaded, X_OPT, type_deserializers=none_deserializer)
    # assert x.a == 0
    # in this case, because it expects int. The none_deserializer is never used, because
    # None is not a type on X_OPT. Could do it against int,
    # should use an attr_deserializer in this case
    loaded = json.loads('{"a": null}')
    attr_deserializers = {"a": deserialize_a}
    x = autotui.deserialize_namedtuple(
        loaded, X_OPT, attr_deserializers=attr_deserializers
    )
    assert x.a == 0

    # could also do like
    loaded = json.loads('{"a": null}')
    type_deserializers = {int: deserialize_a}  # specify int, not NoneType
    x = autotui.deserialize_namedtuple(
        loaded, X_OPT, type_deserializers=type_deserializers
    )
    assert x.a == 0


class LL(NamedTuple):
    a: List[int]


def test_no_value_for_collection_non_optional_warning() -> None:
    l = LL(a=None)  # type: ignore
    with pytest.warns(
        UserWarning,
        match=r"No value found for non-optional type a, defaulting to empty container",
    ):
        lnt = autotui.serialize_namedtuple(l)
    assert lnt["a"] == []


def test_null_in_containers_warns() -> None:
    loaded = json.loads('{"a": [1,null,3]}')
    with pytest.warns(Warning, match=r"expected type int, found NoneType"):
        x = autotui.deserialize_namedtuple(loaded, LL)
    assert x.a == [1, None, 3]


def test_no_way_to_serialize_warning() -> None:
    x = X(a=None)  # type: ignore
    with pytest.warns(
        UserWarning,
        match=r"No value for non-optional type None, attempting to be serialized to int",
    ):
        sx = autotui.serialize_namedtuple(x)
    assert sx["a"] is None


def test_basic_sequence_dumps_loads() -> None:
    x = [X(a=1), X(a=5)]
    xlist_str: str = autotui.namedtuple_sequence_dumps(x, indent=None)
    assert xlist_str == """[{"a": 1}, {"a": 5}]"""
    back_to_x: List[X] = autotui.namedtuple_sequence_loads(xlist_str, to=X)
    assert type(back_to_x) == list
    assert back_to_x[0] == X(a=1)
    assert back_to_x[1] == X(a=5)


def test_doesnt_load_non_iterable() -> None:
    non_iterable = '{"a": 1}'
    with pytest.raises(
        TypeError,
        match=r"{'a': 1} is a dict, expected a top-level list from JSON source",
    ):
        autotui.namedtuple_sequence_loads(non_iterable, X)


class Internal(NamedTuple):
    x: int


class Wrapper(NamedTuple):
    y: int
    z: Internal


def test_recursive() -> None:
    obj = Wrapper(y=5, z=Internal(x=10))
    [dumped_obj] = json.loads(autotui.namedtuple_sequence_dumps([obj]))
    assert dumped_obj["y"] == 5
    assert type(dumped_obj["z"]) == dict
    assert dumped_obj["z"]["x"] == 10

    # dump to JSON and re-load
    [reloaded] = autotui.namedtuple_sequence_loads(json.dumps([dumped_obj]), to=Wrapper)
    assert obj == reloaded


@dataclass(init=False)
class Temperature:
    celsius: float

    def __init__(self, reading_raw: str):
        if len(reading_raw) < 1:
            raise ValueError("Not enough data provided!")
        scale = reading_raw[-1]
        if scale not in ["F", "C"]:
            raise TypeError("Must end with 'F' or 'C'")
        tempstr = reading_raw.rstrip("C").rstrip("F")
        if scale == "C":
            self.celsius = float(tempstr)  # could raise ValueError
        else:
            self.celsius = (float(tempstr) - 32) * 5 / 9


class Reading(NamedTuple):
    when: datetime
    temp: Temperature


def serialize_temp(x: Temperature) -> float:
    return x.celsius


def deserialize_temp(x: float) -> Temperature:
    return Temperature(f"{x}C")


def test_custom_handles_serializers() -> None:
    t = Temperature("20C")
    assert t.celsius == 20.0
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
            readings, fp, type_serializers=type_serializers
        )

    # loads first, check warning when no deserializer provided
    with open(f.name) as fp:
        str_contents = fp.read()

    with warnings.catch_warnings(record=True) as record:
        readings_back = autotui.namedtuple_sequence_loads(str_contents, to=Reading)
    assert len(record) >= 1
    assert "No known way to deserialize" in str(record[0].message)
    assert len(readings_back) == 2
    assert readings_back[0].temp == 20.0

    # then load properly
    with open(f.name) as fp:
        rbr = autotui.namedtuple_sequence_load(
            fp, to=Reading, attr_deserializers=attr_deserializers
        )
    assert len(rbr) == 2
    assert int(rbr[0].when.timestamp()) == int(d1.timestamp())
    assert rbr[0].temp == Temperature("20C")

    # delete file
    os.unlink(f.name)


def test_shortcuts() -> None:
    cur = datetime.now()
    t = Temperature("20C")
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".json")

    type_serializers = {Temperature: serialize_temp}
    attr_deserializers = {"temp": deserialize_temp}

    readings: List[Reading] = [Reading(when=cur, temp=t)]

    dump_to(readings, f.name, type_serializers=type_serializers)

    lr: List[Reading] = load_from(
        Reading, f.name, attr_deserializers=attr_deserializers
    )
    assert len(lr) == 1
    assert lr[0].temp == t
    assert int(lr[0].when.timestamp()) == int(cur.timestamp())

    # delete file
    os.unlink(f.name)

    y = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")

    dump_to(readings, f.name, type_serializers=type_serializers)

    # make sure can load/dumped yaml properly
    txt = Path(y.name).read_text()
    safe_load(txt)
    with pytest.raises(ValueError, match="Expecting value: line 1 column 1"):
        json.loads(txt)

    yr: List[Reading] = load_from(
        Reading, f.name, attr_deserializers=attr_deserializers
    )
    assert len(yr) == 1
    assert lr[0].temp == yr[0].temp
    assert lr[0].when.timestamp() == yr[0].when.timestamp()

    # set format explicitly
    yr_explicit: List[Reading] = load_from(
        Reading, f.name, format="yaml", attr_deserializers=attr_deserializers
    )

    assert yr == yr_explicit
    assert yr == lr


class Action(NamedTuple):
    t: timedelta


def test_no_way_to_handle_propting() -> None:
    with pytest.raises(AutoTUIException, match=r"no way to handle prompting timedelta"):
        autotui.prompt_namedtuple(Action)


def test_no_way_to_serialize() -> None:
    a = Action(t=timedelta(seconds=5))
    with pytest.warns(UserWarning, match=r"No known way to serialize timedelta"):
        not_serialized = autotui.serialize_namedtuple(a)
    with pytest.raises(
        TypeError, match=r"Object of type timedelta is not JSON serializable"
    ):
        json.dumps(not_serialized)


class Broken(object):
    pass


def test_passed_non_namedtuple() -> None:
    with warnings.catch_warnings(record=True) as record:
        autotui.namedtuple_prompt_funcs(Broken)

    assert len(record) == 2
    assert "No parameters extracted from object, may not be NamedTuple?" == str(
        record[1].message
    )


class EmptyNamedTuple(NamedTuple):
    pass


def test_passed_namedtuple_with_no_attrs() -> None:
    with pytest.warns(
        UserWarning,
        match=r"No parameters extracted from object, may not be NamedTuple?",
    ):
        autotui.namedtuple_prompt_funcs(EmptyNamedTuple)


class En(Enum):
    x = 1
    y = 1
    z = "something"


class DAT(NamedTuple):
    choice: En


def test_enum_serialization() -> None:
    d = DAT(choice=En.x)
    d2 = DAT(choice=En.z)
    ds = autotui.serialize_namedtuple(d)
    ds2 = autotui.serialize_namedtuple(d2)

    assert ds["choice"] == "x"
    assert ds2["choice"] == "z"

    assert d == autotui.deserialize_namedtuple(ds, DAT)
    assert d2 == autotui.deserialize_namedtuple(ds2, DAT)


def test_enum_use_key() -> None:
    d = DAT(choice=En.y)
    ds = {"choice": "y"}  # use key name instead of value

    assert autotui.deserialize_namedtuple(ds, DAT) == d


def test_enum_fails() -> None:
    ds = {"choice": "xx"}
    with pytest.raises(ValueError, match=r"Could not find xx on Enumeration"):
        autotui.deserialize_namedtuple(ds, DAT)


def test_hint_generics() -> None:
    # needed to check if we can type hint generics
    # https://www.python.org/dev/peps/pep-0585/
    above_39 = sys.version_info.major >= 3 and sys.version_info.minor >= 9
    # or have unions like X | Y
    # https://www.python.org/dev/peps/pep-0604/
    above_310 = sys.version_info.major >= 3 and sys.version_info.minor >= 10

    if above_39:
        from autotui.typehelpers import strip_generic

        assert strip_generic(list[int]) == list

    if above_310:
        from autotui.typehelpers import get_union_args

        assert None == get_union_args(5)
        assert None == get_union_args(None)
        assert None == get_union_args(int)
        assert ([int], True) == get_union_args(int | None)
        assert ([int], True) == get_union_args(Optional[int])
        assert ([int, float], False) == get_union_args(int | float)
        assert ([int, float, str], False) == get_union_args(int | float | str)
        assert ([int, float, str], True) == get_union_args(int | float | str | None)
        assert ([int], True) == get_union_args(int | None)
        assert None == get_union_args(int)
        assert ([int, X], True) == get_union_args(int | X | None)
        assert ([int, str, X], True) == get_union_args(int | str | X | None)
        assert ([int, X], False) == get_union_args(int | X)
        assert ([int, X], True) == get_union_args(int | X | None)


class Dec(NamedTuple):
    x: Decimal
    y: int


def test_decimal() -> None:
    d = Dec(x=Decimal("5"), y=2)
    ser = autotui.serialize_namedtuple(d)
    assert ser == {"x": "5", "y": 2}
    d2 = autotui.deserialize_namedtuple(ser, to=Dec)
    assert isinstance(d2.x, Decimal)
    assert d == d2


class UEnum(Enum):
    x = 1
    y = 2


class UDAT(NamedTuple):
    choice: UEnum


def test_removing_enum_value() -> None:
    assert autotui.deserialize_namedtuple({"choice": "x"}, UDAT) == UDAT(choice=UEnum.x)

    with pytest.raises(ValueError, match="Could not find z on Enumeration"):
        autotui.deserialize_namedtuple({"choice": "z"}, UDAT)

    with_none = UDAT(choice=None)  # type: ignore
    with options("CONVERT_UNKNOWN_ENUM_TO_NONE"):
        assert autotui.deserialize_namedtuple({"choice": "z"}, UDAT) == with_none

    # make sure it raises again after the option is turned off
    with pytest.raises(ValueError, match="Could not find z on Enumeration"):
        autotui.deserialize_namedtuple({"choice": "z"}, UDAT)
