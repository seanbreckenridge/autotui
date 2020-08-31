from pprint import pprint
from autotui.shortcuts import load_from

# from the ./shortcuts.py file in this directory
from shortcuts import Water

if __name__ == "__main__":
    pprint(load_from(Water, "~/.local/share/water.json"))
