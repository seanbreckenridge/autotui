from typing import Sequence, Any, Dict
from functools import partial
from pprint import pformat

import click

from .typehelpers import NT, is_namedtuple_obj
from .namedtuple_prompt import prompt_namedtuple

eprint = partial(click.echo, err=True)


def _ui_getchar_pick(choices: Sequence[str], prompt: str = "Select from: ") -> int:
    """
    Basic menu allowing the user to select one of the choices
    returns the index the user chose
    """
    assert len(choices) > 0, "Didnt receive any choices to prompt!"
    eprint(prompt + "\n")

    # prompts like 1,2,3,4,5,6,7,8,9,a,b,c,d,e,f...
    chr_offset = ord("a") - 10

    # dict from key user can press -> resulting index
    result_map = {}
    for i, opt in enumerate(choices, 1):
        char: str = str(i) if i < 10 else chr(i + chr_offset)
        result_map[char] = i - 1
        eprint(f"\t{char}. {opt}")

    eprint("")
    while True:
        ch = click.getchar()
        if ch not in result_map:
            eprint(f"{ch} not in {list(result_map.keys())}")
            continue
        return result_map[ch]


DONE_EDITING = "DONE EDITING"


def edit_namedtuple(nt: NT, print_namedtuple: bool = False, loop: bool = False, **kwargs: Any) -> NT:
    """Edit a namedtuple."""
    assert is_namedtuple_obj(nt), f"nt {nt} is not a namedtuple"
    nt_dict: Dict[str, Any] = nt._asdict()  # type: ignore
    while True:
        assert isinstance(nt_dict, dict)
        keys = list(nt_dict.keys())
        if loop is True:
            keys.append(DONE_EDITING)
        if print_namedtuple is True:
            eprint(pformat(nt))
        key = _ui_getchar_pick(keys, "Which field to edit: ")
        if loop is True and keys[key] == DONE_EDITING:
            return nt
        choice = keys[key]
        assert choice in nt_dict, f"choice {choice} not in nt_dict {nt_dict}"
        partial_values = {k: v for k, v in nt_dict.items() if k != choice}
        nt = prompt_namedtuple(type(nt), attr_use_values=partial_values, **kwargs)
        if loop is False:
            return nt
        nt_dict = nt._asdict()  # type: ignore
