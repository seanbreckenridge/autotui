#!/usr/bin/env python3

"""
So that I can test how changes to the code affect the performance of the code
"""

from functools import wraps
from cProfile import run
from pstats import SortKey
from time import perf_counter
from typing import NamedTuple, Optional, List
from datetime import datetime, timedelta

from autotui import (
    namedtuple_sequence_dumps,
    namedtuple_sequence_loads,
)

ITERATIONS = 10000


class Typical(NamedTuple):
    x: int
    y: datetime


class Complex(NamedTuple):
    a: int
    b: str
    c: datetime
    d: List[bool]
    e: Optional[int]
    f: timedelta


def to_seconds(t: timedelta) -> int:
    return int(t.total_seconds())


def from_seconds(seconds: int) -> timedelta:
    return timedelta(seconds=seconds)


class TypeSerializer(NamedTuple):
    x: int
    y: timedelta


typical_items = [
    Typical(x=5, y=datetime.now()),
    Typical(x=9, y=datetime.now()),
    Typical(x=-1, y=datetime.now()),
]

typical_json = (
    '[{"x": 5, "y": 1617131093}, {"x": 9, "y": 1617131093}, {"x": -1, "y": 1617131093}]'
)

complex_items = [
    Complex(
        a=5,
        b="something",
        c=datetime.now(),
        d=[True, False],
        e=None,
        f=timedelta(hours=5),
    ),
    Complex(
        a=10,
        b="something",
        c=datetime.now(),
        d=[True, False],
        e=5,
        f=timedelta(seconds=5),
    ),
    Complex(
        a=5,
        b="something",
        c=datetime.now(),
        d=[True, False],
        e=5,
        f=timedelta(minutes=5),
    ),
]

complex_type_serializer = {timedelta: to_seconds}

complex_type_deserializer = {timedelta: from_seconds}

complex_json = '[{"a": 5, "b": "something", "c": 1617131493, "d": [true, false], "e": null, "f": 18000}, {"a": 10, "b": "something", "c": 1617131493, "d": [true, false], "e": 5, "f": 5}, {"a": 5, "b": "something", "c": 1617131493, "d": [true, false], "e": 5, "f": 300}]'


def benchmark(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print("Running {}...".format(f.__name__))
        start = perf_counter()
        for _ in range(ITERATIONS):
            f(*args, **kwargs)
        end = perf_counter()
        elapsed = end - start
        print("Elapsed time: {}".format(elapsed))
        print("Time per loop: {}".format(elapsed / ITERATIONS))

    return wrapper


def typical_dumps():
    namedtuple_sequence_dumps(typical_items)


def typical_loads():
    namedtuple_sequence_loads(typical_json, Typical)


def complex_dumps():
    return namedtuple_sequence_dumps(
        complex_items, type_serializers=complex_type_serializer
    )


def complex_loads():
    namedtuple_sequence_loads(
        complex_json, Complex, type_deserializers=complex_type_deserializer
    )


def run_benchmarks() -> None:
    benchmark(typical_dumps)()
    benchmark(typical_loads)()
    benchmark(complex_dumps)()
    benchmark(complex_loads)()
    print("typical_dumps():")
    run("typical_dumps()", sort=SortKey.CUMULATIVE)
    print("typical_loads():")
    run("typical_loads()", sort=SortKey.CUMULATIVE)
    print("complex_dumps():")
    run("complex_dumps()", sort=SortKey.CUMULATIVE)
    print("complex_loads():")
    run("complex_loads()", sort=SortKey.CUMULATIVE)


if __name__ == "__main__":
    run_benchmarks()
