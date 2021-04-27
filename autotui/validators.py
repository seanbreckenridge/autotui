import sys
from datetime import datetime
from typing import Type, Optional, Callable, List, Union, Any, TYPE_CHECKING
from functools import lru_cache


@lru_cache(maxsize=1)
def dark_mode():

    from prompt_toolkit.styles import Style

    return Style.from_dict(
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
def handle_prompt(
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
    from prompt_toolkit import prompt

    m: str = handle_prompt(str, for_attr, prompt_msg)
    return prompt(m)


## INT


# the Int/Float validators follow this pattern so that prompt_toolkit imports are not
# at the top level. allows the rest of the library to load fast without waiting
# for prompt_toolkit to import
#
# this does making extending/monkey patching these more annoying, but
# I think thats not the common case - the common case is waiting on
# the import while serializing/deserializing the information


@lru_cache(maxsize=1)
def IntValidator() -> Type["Validator"]:

    from prompt_toolkit.validation import Validator, ValidationError

    class _IntValidator(Validator):
        def validate(self, document):
            text = document.text
            try:
                int(text)
            except ValueError as ve:
                raise ValidationError(message=str(ve))

    return _IntValidator


def prompt_int(for_attr: Optional[str] = None, prompt_msg: Optional[str] = None) -> int:
    from prompt_toolkit import prompt

    m: str = handle_prompt(int, for_attr, prompt_msg)
    return int(prompt(m, validator=IntValidator()()))


## FLOAT


@lru_cache(maxsize=1)
def FloatValidator() -> Type["Validator"]:

    from prompt_toolkit.validation import Validator, ValidationError

    class _FloatValidator(Validator):
        def validate(self, document):
            text = document.text
            try:
                float(text)
            except ValueError as ve:
                raise ValidationError(message=str(ve))

    return _FloatValidator


def prompt_float(
    for_attr: Optional[str] = None, prompt_msg: Optional[str] = None
) -> float:
    from prompt_toolkit import prompt

    m: str = handle_prompt(float, for_attr, prompt_msg)
    return float(prompt(m, validator=FloatValidator()()))


## BOOL


def prompt_bool(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> bool:
    from prompt_toolkit.shortcuts import button_dialog

    m: str = handle_prompt(bool, for_attr, prompt_msg)
    return button_dialog(
        title=dialog_title,
        text=m,
        buttons=[("True", True), ("False", False)],
        style=dark_mode(),
    ).run()


## DATETIME


def prompt_datetime(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
) -> datetime:
    from prompt_toolkit.shortcuts import button_dialog, input_dialog, message_dialog

    m: str = handle_prompt(datetime, for_attr, prompt_msg)
    use_current_time = button_dialog(
        title="How to pick date?",
        text=m,
        buttons=[("Now", True), ("Describe", False)],
        style=dark_mode(),
    ).run()
    if use_current_time:
        return datetime.now()
    else:
        try:
            import dateparser  # type: ignore[import]
        except ImportError as e:
            print(str(e))
            print(
                "Could not find dateparser module, run 'pip3 install dateparser' to be able to parse date strings"
            )
            sys.exit(1)
        parsed_time: Optional[datetime] = None
        while parsed_time is None:
            time_str: Optional[str] = input_dialog(
                title="Describe the datetime:",
                text="For example:\n'2 hours ago', 'noon', 'tomorrow at 10PM', 'may 30th at 8PM'",
                style=dark_mode(),
            ).run()
            if time_str is None:
                print("Cancelled, using current time...")
                return datetime.now()
            parsed_time = dateparser.parse(time_str)
            if parsed_time is None:
                message_dialog(
                    title="Error",
                    text=f"Could not parse '{time_str}' into datetime...",
                    style=dark_mode(),
                ).run()
        return parsed_time


## LIST/SET repeat-prompt?


def prompt_ask_another(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> bool:
    from prompt_toolkit.shortcuts import button_dialog

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
        style=dark_mode(),
    ).run()


## Optional


def prompt_optional(
    func: Callable[[], Any],
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> Optional[Any]:
    """
    A helper to ask if the user wants to enter information for an optional.
    If the user confirms, calls func (which asks the user for input)
    """
    from prompt_toolkit.shortcuts import button_dialog

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
        style=dark_mode(),
    ).run():
        return func()
    else:
        return None


##  wrap some function and display the specified thrown errors as validation errors


def prompt_wrap_error(
    func: Callable[[str], Any],
    catch_errors: Optional[List[Type]] = None,
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
) -> Any:
    """
    Takes the prompt string, some function which takes the string the user
    is typing as input, and possible errors to catch.

    If the function raises one of those errors, raise it as a ValidationError instead.

    This is pretty similar to prompt_toolkit.validators.Validation.from_callable
    but it allows you to specify the error message from the callable instead.
    """
    from prompt_toolkit import prompt
    from prompt_toolkit.validation import Validator, ValidationError

    m: str = handle_prompt(func.__name__, for_attr, prompt_msg)

    errors_to_catch: List[Type] = catch_errors or []

    class LambdaPromptValidator(Validator):
        def validate(self, document):
            text = document.text
            try:
                func(text)
            except Exception as e:
                for catchable in errors_to_catch:
                    if isinstance(e, catchable):
                        raise ValidationError(message=str(e))
                else:
                    # if the user didnt specify this as an error to catch
                    raise e

    return func(prompt(m, validator=LambdaPromptValidator()))


if TYPE_CHECKING:
    from prompt_toolkit.validation import Validator
