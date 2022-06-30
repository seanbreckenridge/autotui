from pprint import pprint
from autotui import pick_namedtuple
from autotui.shortcuts import load_from

# from the ./shortcuts_example.py file in this directory
from shortcuts_example import Water

if __name__ == "__main__":
    picked = pick_namedtuple(load_from(Water, "~/.local/share/water.json"))
    pprint(picked)
