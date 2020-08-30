import functools
import inspect
from datetime import datetime
from typing import (
    Any,
    Type,
    Optional,
    Union,
    List,
    NamedTuple,
    Dict,
    Callable,
)

from logzero import logger

from .typehelpers import (
    is_primitive,
    is_supported_container,
    strip_optional,
    get_collection_types,
    add_to_container,
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
    func: Callable
    # if no exceptions are passed, catches all exceptions
    catch_errors: List[Type] = [Exception]
    prompt_msg: Optional[str] = None


def _get_validator(
    cls: Type, attr_name: str, type_validators: Dict[Type, AutoHandler]
) -> Callable:
    """
    Gets one of the built-in validators or a type_validator from the user.
    This returns a validator for a particular type, it doesn't handle collections (List/Set)
    """
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
    raise AutoTUIException(f"no way to handle prompting {cls}")


# ask first would be set if is_optional was true
def _prompt_many(
    attr_name: str, promptfunc: Callable, container_type: Type, ask_first: bool
) -> Callable:
    """
    A helper to prompt for an item zero or more times, for populating List/Set
    """

    def pm_lambda():
        # do-while-esque
        if ask_first:
            if not prompt_ask_another(attr_name):
                return container_type([])
        ret = container_type([])
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
    attr_name: str, handler: Union[AutoHandler, Callable], is_optional: bool
) -> Callable:
    """
    If a NamedTuple attribute is optional, wrap it
    with a dialog asking if the user wants to enter information for it
    """
    callf: Callable = lambda: None  # dummy value
    if isinstance(
        handler, AutoHandler
    ):  # if user provided function/errors to catch for validation
        callf = _create_callable_prompt(attr_name, handler)
    else:  # is already a function
        callf = handler
    if not is_optional:
        return callf
    else:
        # if optional, wrap the typical
        # validator/callable with a yes/no prompt to add it
        return lambda: prompt_optional(func=callf, for_attr=attr_name)


def _create_callable_prompt(attr_name: str, handler: AutoHandler) -> Callable:
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
    nt: NamedTuple,
    attr_validators: Dict[str, AutoHandler] = {},
    type_validators: Dict[Type, AutoHandler] = {},
):
    """
    Parses the signature of a NamedTuple recieved from the User

    If any of the parameters cant be handled by autotui supported validators,
    checks the vaidators dict for user-supplied ones.

    Else, prints an error and fails
    """
    # example:
    # class X(NamedTuple):
    #    a: int
    #    b: float
    #    c: str
    # >>> inspect.signature(X)
    # <Signature (a: int, b: float, c: str)>
    sig = inspect.signature(nt)
    # the dict of attribute names -> validator functions
    # to populate the namedtuple fields
    validator_map: Dict[str, Callable] = {}

    logger.debug(f"Creating functions for {nt}")

    # example:
    # [('a', <Parameter "a: int">), ('b', <Parameter "b: float">), ('c', <Parameter "c: str">)]
    for attr_name, param_type in sig.parameters.items():

        # <class 'int'>
        nt_annotation = param_type.annotation
        # (<class 'int'>, False)
        attr_type, is_optional = strip_optional(nt_annotation)
        logger.debug(f"==> For attr: {attr_name}")
        logger.debug(f"Type: {attr_type}")
        logger.debug(f"Optional?: {is_optional}")

        # if the user specified a validator for this attribute name, use that
        if attr_name in attr_validators.keys():
            handler: AutoHandler = attr_validators[attr_name]
            validator_map[attr_name] = _maybe_wrap_optional(
                attr_name, handler, is_optional
            )
            # check return type of callable to see if it matches expected type?
            continue
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
            promptfunc: Callable = _get_validator(
                internal_type, attr_name, type_validators
            )
            # wrap to ask one or more times
            # wrap in container_type List/Set
            logger.debug(f"Container internal attribute type: {attr_type}")
            logger.debug(f"Container type: {container_type}")
            validator_map[attr_name] = _prompt_many(
                attr_name, promptfunc, container_type, is_optional
            )
            # TODO: recursive container support? Though if a type is getting that complicated
            # should you be using autotui in general? would be simpler to create a class and
            # supply that as a type_validator
        else:
            # single type, like:
            # a: int
            # b: Optional[str]
            promptfunc: Callable = _get_validator(attr_type, attr_name, type_validators)
            validator_map[attr_name] = _maybe_wrap_optional(
                attr_name, promptfunc, is_optional
            )
    return validator_map


def prompt_namedtuple(
    nt: NamedTuple,
    attr_validators: Dict[str, AutoHandler] = {},
    type_validators: Dict[Type, AutoHandler] = {},
):
    """
    Generate the list of functions using namedtuple_prompt_funcs
    and prompt the user for each of them
    """
    funcs: Dict[str, Callable] = namedtuple_prompt_funcs(
        nt, attr_validators, type_validators
    )
    nt_values: Dict[str, Any] = {
        attr_key: attr_func() for attr_key, attr_func in funcs.items()
    }
    return nt(**nt_values)
