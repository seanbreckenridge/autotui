from datetime import datetime
from typing import NamedTuple, List, Optional

from autotui.shortcuts import load_prompt_and_writeback

import click


def edit_in_vim() -> str:
    m = click.edit(text=None)
    return m if m is None else m.strip()


class JournalEntry(NamedTuple):
    creation_date: datetime
    tags: Optional[List[str]]  # one or more tags to tag this journal entry with
    content: str


if __name__ == "__main__":
    load_prompt_and_writeback(
        JournalEntry,
        "~/Documents/journal.json",
        attr_use_values={"content": edit_in_vim},
    )
