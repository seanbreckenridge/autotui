from typing import Type, Optional, Callable, List, Union

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import button_dialog
from prompt_toolkit.styles import Style

dark_mode = Style.from_dict(
    {
        "dialog": "bg:#000000",
        "dialog frame.label": "bg:#ffffff #000000",
        "dialog.body": "bg:#000000 #D3D3D3",
        "dialog shadow": "bg:#000000",
    }
)


def create_repl_prompt_str(prompt_msg: str) -> str:
    """
    create_repl_prompt_str("give string!")
    'give string! > '
    create_repl_prompt_str("enter an int >")
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
    m: str = handle_prompt(str, for_attr, prompt_msg)
    return prompt(m)


## INT


class IntValidator(Validator):
    def validate(self, document):
        text = document.text
        try:
            int(text)
        except ValueError as ve:
            raise ValidationError(message=str(ve))


def prompt_int(for_attr: Optional[str] = None, prompt_msg: Optional[str] = None) -> int:
    m: str = handle_prompt(int, for_attr, prompt_msg)
    return int(prompt(m, validator=IntValidator()))


## FLOAT


class FloatValidator(Validator):
    def validate(self, document):
        text = document.text
        try:
            float(text)
        except ValueError as ve:
            raise ValidationError(message=str(ve))


def prompt_float(
    for_attr: Optional[str] = None, prompt_msg: Optional[str] = None
) -> float:
    m: str = handle_prompt(float, for_attr, prompt_msg)
    return float(prompt(m, validator=FloatValidator()))


## BOOL


def prompt_bool(
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "===",
) -> bool:
    m: str = handle_prompt(bool, for_attr, prompt_msg)
    return button_dialog(
        title=dialog_title,
        text=m,
        buttons=[("True", True), ("False", False)],
        style=dark_mode,
    ).run()


## LIST/SET repeat-prompt?

def prompt_ask_another(
    for_attr: Optional[str] = None, prompt_msg: Optional[str] = None, dialog_title: str = "==="
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
        style=dark_mode,
    ).run()

## Optional

def prompt_optional(
    func: Callable,
    for_attr: Optional[str] = None,
    prompt_msg: Optional[str] = None,
    dialog_title: str = "==="):
    """
    A helper to ask if the user wants to enter information for an optional.
    If the user confirms, calls func (which asks the user for input)
    """
    m = prompt_msg
    if m is None:
        assert (
            for_attr is not None
        ), "Expected 'for_attr'; an attribute name to prompt for!"
        m = f"'{for_attr}' is optional. Add?"
    if button_dialog(
        title=dialog_title,
        text=m,
        buttons=[("Add", True), ("Skip", False)],
        style=dark_mode,
    ).run():
        return func()
    else:
        return None

##  wrap some function and display the specified thrown errors as validation errors

def prompt_wrap_error(func: Callable,
                      catch_errors: Optional[List[Type]] = [],
                      for_attr: Optional[str] = None,
                      prompt_msg: Optional[str] = None):
    """
    Takes the prompt string, some function which takes the string the user
    is typing as input, and possible errors to catch.

    If the function raises one of those errors, raise it as a ValidationError instead.

    This is pretty similar to prompt_toolkit.validators.Validation.from_callable
    but it allows you to specify the error message from the callable instead.
    """
    m: str = handle_prompt(func.__name__, for_attr, prompt_msg)

    class LambdaPromptValidator(Validator):
        def validate(self, document):
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

