import sys
import os
from datetime import datetime
from typing import Type, Optional, Callable, List, Union

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError, Document
from prompt_toolkit.shortcuts import button_dialog, input_dialog, message_dialog

from .typehelpers import T

STYLE = Style.from_dict(
    {
        "dialog": "bg:#000000",
        "dialog frame.label": "bg:#ffffff #000000",
        "dialog.body": "bg:#000000 #D3D3D3",
        "dialog shadow": "bg:#000000",
        "text-area": "#000000",
    }
)


def create_repl_prompt_str(prompt_msg: str) -> str:
    """
    >>> create_repl_prompt_str("give string!")
    'give string! > '
    >>> create_repl_prompt_str("enter an int >")
    'enter an int > '
    """
    msg = prompt_msg.strip()
    if msg.endswith(">"):
        return f"{msg} "
    else:
        return f"{msg} > "


# handles the repetitive task of validating passed kwargs for prompt string for attrs
def create_prompt_string(
    for_type: Union[str, Type], for_attr: Optional[str], prompt_msg: Optional[str]
) -> str:
    # if user supplied one, use that
    pmsg = prompt_msg
    if pmsg is not None:
        return pmsg
    assert for_attr is not None, "Expected 'for_attr'; an attribute name to prompt for!"
    describe: str = for_type.__name__ if isinstance(for_type, type) else str(for_type)
    return create_repl_prompt_str(f"'{for_attr}' ({describe})")


## STRING


def prompt_str(for_attr: Optional[str] = None, prompt_msg: Optional[str] = None) -> str:

    m: str = create_prompt_string(str, for_attr, prompt_msg)
    return prompt(m)


## INT


class IntValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text
        try:
            int(text)
        except ValueError as ve:
            raise ValidationError(message=str(ve))


def prompt_int(for_attr: Optional[str] = None, prompt_msg: Optional[str] = None) -> int:
    m: str = create_prompt_string(int, for_attr, prompt_msg)
    return int(prompt(m, validator=IntValidator()))


## FLOAT


class FloatValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text
        try:
            float(text)
        except ValueError as ve:
            raise ValidationError(message=str(ve))


def prompt_float(
    for_attr: Optional[str] = None, prompt_msg: Optional[str] = None
) -> float:
    m: str = create_prompt_string(float, for_attr, prompt_msg)
    return float(prompt(m, validator=FloatValidator()))


## BOOL


def prompt_bool(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> bool:

    m: str = create_prompt_string(bool, for_attr, prompt_msg)
    return button_dialog(
        title=dialog_title,
        text=m,
        buttons=[("True", True), ("False", False)],
        style=STYLE,
    ).run()


## DATETIME

DatetimeParserFunc = Callable[[str], Optional[datetime]]


class LiveDatetimeValidator(Validator):
    def __init__(
        self,
        *,
        parser_func: DatetimeParserFunc,
    ):
        super().__init__()
        self.parser_func = parser_func
        # defaults
        self.text = ""
        self.parsed: Optional[datetime] = None

    def validate(self, document: Document) -> None:
        text = document.text.strip().lower()
        self.text = text
        self.parsed = None  # reset so previous results dont stay
        if len(text) == 0:
            raise ValidationError(message="Not enough input...")
        val: Optional[datetime] = self.parser_func(text)
        if val is None:
            raise ValidationError(message=f"Couldn't parse {text} into a datetime")
        else:
            self.parsed = val

    def toolbar(self) -> str:
        result = "..."
        if len(self.text) == 0:
            return result
        if self.parsed is not None:
            result = str(self.parsed)
        else:
            result = "Couldn't parse..."
        return result


def prompt_datetime(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
) -> datetime:
    m: str = create_prompt_string(datetime, for_attr, prompt_msg)
    import dateparser  # type: ignore[import]

    # can cause lag on slower machines because of the constant
    # recomputes - put it behind a envvar-enabled feature
    if "AUTOTUI_DATETIME_LIVE" in os.environ:
        validator = LiveDatetimeValidator(parser_func=dateparser.parse)
        toolbar_func: Callable[[], str] = validator.toolbar
        prompt(m, validator=validator, bottom_toolbar=toolbar_func)
        dt = validator.parsed  # grab from state instead of parsing again
        assert isinstance(dt, datetime)
        return dt
    else:
        parsed_time: Optional[datetime] = None
        while parsed_time is None:
            time_str: Optional[str] = input_dialog(
                title="Describe the datetime:",
                text="For example:\n'now', '2 hours ago', 'noon', 'tomorrow at 10PM', 'may 30th at 8PM'",
                style=STYLE,
            ).run()
            if time_str is None:
                # hmm -- is this dangerous? user is prompting, so unless they've left the file
                # open this should be fine. everything in shortcuts.py is atomic-like
                # on purpose so this doesnt run into a problem there
                #
                # the alternative is to write bogus info, but perhaps that runs into
                # less problems with losing data?
                print("Cancelled, exiting...")
                sys.exit(1)
            parsed_time = dateparser.parse(time_str)
            if parsed_time is None:
                message_dialog(
                    title="Error",
                    text=f"Could not parse '{time_str}' into datetime...",
                    style=STYLE,
                ).run()
        return parsed_time


## LIST/SET repeat-prompt?


def prompt_ask_another(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> bool:
    m = prompt_msg
    if m is None:
        assert (
            for_attr is not None
        ), "Expected 'for_attr'; an attribute name to prompt for!"
        m = f"Add another item to '{for_attr}'?"
    return button_dialog(
        title=dialog_title,
        text=m,
        buttons=[("Yes", True), ("No", False)],
        style=STYLE,
    ).run()


## Optional


def prompt_optional(
    func: Callable[[], T],
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> Optional[T]:
    """
    A helper to ask if the user wants to enter information for an optional.
    If the user confirms, calls func (which asks the user for input)
    """
    m: Optional[str] = prompt_msg
    if m is None:
        assert (
            for_attr is not None
        ), "Expected 'for_attr'; an attribute name to prompt for!"
        m = f"'{for_attr}' is optional. Add?"
    if button_dialog(
        title=dialog_title,
        text=m,
        buttons=[("Add", True), ("Skip", False)],
        style=STYLE,
    ).run():
        return func()
    else:
        return None


##  wrap some function and display the specified thrown errors as validation errors


def prompt_wrap_error(
    func: Callable[[str], T],
    catch_errors: List[Type],
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
) -> T:
    """
    Takes the prompt string, some function which takes the string the user
    is typing as input, and possible errors to catch.

    If the function raises one of those errors, raise it as a ValidationError instead.

    This is pretty similar to prompt_toolkit.validators.Validation.from_callable
    but it allows you to specify the error message from the callable instead.
    """
    m: str = create_prompt_string(func.__name__, for_attr, prompt_msg)

    class LambdaPromptValidator(Validator):
        def validate(self, document: Document) -> None:
            text = document.text
            try:
                func(text)
            except Exception as e:
                for catchable in catch_errors:
                    if isinstance(e, catchable):
                        raise ValidationError(message=str(e))
                else:
                    # if the user didnt specify this as an error to catch
                    raise e

    return func(prompt(m, validator=LambdaPromptValidator()))
