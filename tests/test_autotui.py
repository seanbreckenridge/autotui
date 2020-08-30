import pytest
import autotui

from typing import NamedTuple, Optional, List, Set

class P(NamedTuple):
    a: int
    b: float
    c: str

class L(NamedTuple):
    a: List[int]
    b: Set[bool]

class O(NamedTuple):
    a: Optional[int] = None
    b: Optional[str] = None

def test_auto_primitives():
    autotui.namedtuple_prompt_funcs(P)
    autotui.namedtuple_prompt_funcs(L)
    autotui.namedtuple_prompt_funcs(O)

