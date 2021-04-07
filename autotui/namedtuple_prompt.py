import functools
import warnings
from datetime import datetime
from typing import (
    Any,
    Optional,
    Union,
    List,
    NamedTuple,
    Type,
    Dict,
    Callable,
)

from .typehelpers import (
    is_primitive,
    is_supported_container,
    strip_optional,
    get_collection_types,
    add_to_container,
    PrimitiveType,
    AnyContainerType,
    inspect_signature_dict,
    is_namedtuple_type,
)

from .validators import (
    prompt_str,
    prompt_int,
    prompt_float,
    prompt_bool,
    prompt_datetime,
    prompt_ask_another,
    prompt_wrap_error,
    prompt_optional,
)

from .exceptions import AutoTUIException


class AutoHandler(NamedTuple):
    func: Callable[[str], Any]
    # if no exceptions are passed, catches no exceptions
    catch_errors: List[Type] = []
    prompt_msg: Optional[str] = None


# wraps a value in a function with no arguments if needed,
# else assumes the user passed a function they wanted
# to be called, instead of prompting using prompt_toolkit
# with the attr/type validators
def _create_callable_for_default(value: Any) -> Callable[[], Any]:
    if callable(value):
        return value  # type: ignore[no-any-return]
    else:
        return lambda: value


def _get_validator(
    cls: Type,
    attr_name: str,
    type_validators: Dict[Type, AutoHandler],
    type_use_values: Dict[Type, Any],
) -> Callable[[], Union[PrimitiveType, Any]]:
    """
    Gets one of the built-in validators or a type_validator from the user.
    This returns a validator for a particular type, it doesn't handle collections (List/Set)
    """
    if cls in type_use_values:
        # assuming this is a custom prompt function the user wrote, or
        # a function which returns the value to use for this
        return _create_callable_for_default(type_use_values[cls])
    if cls in type_validators:
        return _create_callable_prompt(attr_name, type_validators[cls])
    if is_primitive(cls):
        if cls == str:
            return lambda: prompt_str(attr_name)
        elif cls == int:
            return lambda: prompt_int(attr_name)
        elif cls == float:
            return lambda: prompt_float(attr_name)
        elif cls == bool:
            return lambda: prompt_bool(attr_name)
        elif cls == datetime:
            return lambda: prompt_datetime(attr_name)
    # if this is another NamedTuple, call prompt_namedtuple recursively
    if is_namedtuple_type(cls):
        return lambda: prompt_namedtuple(cls, type_validators=type_validators)
    raise AutoTUIException(f"no way to handle prompting {cls.__name__}")


# ask first would be set if is_optional was true
def _prompt_many(
    attr_name: str,
    promptfunc: Callable[[], Union[PrimitiveType, Any]],
    container_type: Type,
    ask_first: bool,
) -> Callable[[], AnyContainerType]:
    """
    A helper to prompt for an item zero or more times, for populating List/Set
    """

    def pm_lambda() -> AnyContainerType:
        empty_return: AnyContainerType = container_type([])
        # do-while-esque
        if ask_first:
            if not prompt_ask_another(attr_name):
                return empty_return
        ret: AnyContainerType = empty_return
        continue_prompting: bool = True
        continue_ = functools.partial(
            prompt_ask_another,
            for_attr=attr_name,
            dialog_title=f"Add another item to {attr_name}?",
        )
        while continue_prompting:
            ret = add_to_container(ret, promptfunc())
            # interpolate the current list into the continue? prompt
            # TODO: truncate based on terminal column width?
            continue_prompting = continue_(prompt_msg=f"Currently => {ret}")
        return ret

    return pm_lambda


def _maybe_wrap_optional(
    attr_name: str, handler: Union[AutoHandler, Callable[[], Any]], is_optional: bool
) -> Callable[[], Any]:
    """
    If a NamedTuple attribute is optional, wrap it
    with a dialog asking if the user wants to enter information for it
    """
    callf: Callable[[], Any] = lambda: None  # dummy value
    # if user provided function/errors to catch for validation
    if isinstance(handler, AutoHandler):
        callf = _create_callable_prompt(attr_name, handler)
    else:  # is already a function
        callf = handler
    if not is_optional:
        return callf
    else:
        # if optional, wrap the typical
        # validator/callable with a yes/no prompt to add it
        return lambda: prompt_optional(func=callf, for_attr=attr_name)


def _create_callable_prompt(attr_name: str, handler: AutoHandler) -> Callable[[], Any]:
    """
    Create a callable function with the informaton from a AutoHandler
    """
    return lambda: prompt_wrap_error(
        func=handler.func,
        catch_errors=handler.catch_errors,
        for_attr=attr_name,
        prompt_msg=handler.prompt_msg,
    )


def namedtuple_prompt_funcs(
    nt: Type,
    attr_validators: Optional[Dict[str, AutoHandler]] = None,
    type_validators: Optional[Dict[Type, AutoHandler]] = None,
    attr_use_values: Optional[Dict[str, Any]] = None,
    type_use_values: Optional[Dict[Type, Any]] = None,
) -> Dict[str, Callable[[], Any]]:
    """
    Parses the signature of a NamedTuple received from the User

    If any of the parameters cant be handled by autotui supported validators,
    checks the vaidators dict for user-supplied ones.

    Else, prints an error and fails
    """

    attr_validators = attr_validators or {}
    type_validators = type_validators or {}

    attr_use_values = attr_use_values or {}
    type_use_values = type_use_values or {}

    # warn if not a subclass of a NamedTuple
    # if not isinstance(nt, NamedTuple):
    # warnings.warn(f"{nt.__name__} isn't an instance of a NamedTuple")

    # example:
    # class X(NamedTuple):
    #    a: int
    #    b: float
    #    c: str
    # >>> inspect.signature(X)
    # <Signature (a: int, b: float, c: str)>
    # the dict of attribute names -> validator (prompt) functions
    # to populate the namedtuple fields
    prompt_functions: Dict[str, Callable[[], Any]] = {}

    # example:
    # [('a', <Parameter "a: int">), ('b', <Parameter "b: float">), ('c', <Parameter "c: str">)]
    # nt_annotation is the type
    for attr_name, nt_annotation in inspect_signature_dict(nt).items():

        if attr_name in attr_use_values:
            prompt_functions[attr_name] = _create_callable_for_default(
                attr_use_values[attr_name]
            )
            continue

        # (<class 'int'>, False)
        attr_type, is_optional = strip_optional(nt_annotation)

        # if the user specified a validator for this attribute name, use that
        if attr_name in attr_validators:
            handler: AutoHandler = attr_validators[attr_name]
            prompt_functions[attr_name] = _maybe_wrap_optional(
                attr_name, handler, is_optional
            )
            # check return type of callable to see if it matches expected type?
            continue
        promptfunc: Callable[[], Union[PrimitiveType, Any]] = lambda: None
        if is_supported_container(attr_type):
            # check internal types to see if those are supported
            # optional is this context means maybe they dont want to add anything?
            # if optional present:
            #   ask before adding first item
            # else:
            #   ask after adding first item

            # e.g. if List[int], internal_type == int

            container_type, internal_type = get_collection_types(attr_type)

            # TODO: pass prompt_msg from internal type to prompt another kwarg??
            promptfunc = _get_validator(
                internal_type, attr_name, type_validators, type_use_values
            )
            # wrap to ask one or more times
            # wrap in container_type List/Set
            prompt_functions[attr_name] = _prompt_many(
                attr_name, promptfunc, container_type, is_optional
            )
            # TODO: recursive container support? Though if a type is getting that complicated
            # should you be using autotui in general? would be simpler to create a class and
            # supply that as a type_validator
        else:
            # single type, like:
            # a: int
            # b: Optional[str]
            promptfunc = _get_validator(
                attr_type, attr_name, type_validators, type_use_values
            )
            prompt_functions[attr_name] = _maybe_wrap_optional(
                attr_name, promptfunc, is_optional
            )
    # warn if no attributes are extracted
    if len(prompt_functions) == 0:
        warnings.warn("No parameters extracted from object, may not be NamedTuple?")
    return prompt_functions


def prompt_namedtuple(
    nt: Type,
    *,
    attr_validators: Optional[Dict[str, AutoHandler]] = None,
    type_validators: Optional[Dict[Type, AutoHandler]] = None,
    attr_use_values: Optional[Dict[str, Any]] = None,
    type_use_values: Optional[Dict[Type, Any]] = None,
) -> NamedTuple:
    """
    Generate the list of functions using namedtuple_prompt_funcs
    and prompt the user for each of them

    attr_validators and type_validators use those functions
    to validate while prompting interactively

    attr_use_values and type_use_values let you pass default values
    to use for some attribute/type on the NamedTuple instead of prompting. the
    values for those can either be a function to call (if you wanted
    write custom code to prompt the user), or just a default value
    """

    funcs: Dict[str, Callable[[], Any]] = namedtuple_prompt_funcs(
        nt, attr_validators, type_validators, attr_use_values, type_use_values
    )
    nt_values: Dict[str, Any] = {
        attr_key: attr_func() for attr_key, attr_func in funcs.items()
    }
    return nt(**nt_values)  # type: ignore[operator, no-any-return]
