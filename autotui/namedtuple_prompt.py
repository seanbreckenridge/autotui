import functools
import inspect
import warnings
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

from .typehelpers import (
    is_primitive,
    is_supported_container,
    strip_optional,
    get_collection_types,
    add_to_container,
    PrimitiveType,
    AnyContainerType,
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


def _get_validator(
    cls: Type, attr_name: str, type_validators: Dict[Type, AutoHandler]
) -> Callable[[], Union[PrimitiveType, Any]]:
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
    nt: NamedTuple,
    attr_validators: Dict[str, AutoHandler] = {},
    type_validators: Dict[Type, AutoHandler] = {},
) -> Dict[str, Callable[[], Any]]:
    """
    Parses the signature of a NamedTuple received from the User

    If any of the parameters cant be handled by autotui supported validators,
    checks the vaidators dict for user-supplied ones.

    Else, prints an error and fails
    """

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
    sig = inspect.signature(nt)  # type: ignore[arg-type]
    # the dict of attribute names -> validator functions
    # to populate the namedtuple fields
    validator_map: Dict[str, Callable[[], Any]] = {}

    # example:
    # [('a', <Parameter "a: int">), ('b', <Parameter "b: float">), ('c', <Parameter "c: str">)]
    for attr_name, param_type in sig.parameters.items():

        # <class 'int'>
        nt_annotation = param_type.annotation
        # (<class 'int'>, False)
        attr_type, is_optional = strip_optional(nt_annotation)

        # if the user specified a validator for this attribute name, use that
        if attr_name in attr_validators.keys():
            handler: AutoHandler = attr_validators[attr_name]
            validator_map[attr_name] = _maybe_wrap_optional(
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
            promptfunc = _get_validator(internal_type, attr_name, type_validators)
            # wrap to ask one or more times
            # wrap in container_type List/Set
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
            promptfunc = _get_validator(attr_type, attr_name, type_validators)
            validator_map[attr_name] = _maybe_wrap_optional(
                attr_name, promptfunc, is_optional
            )
    # warn if no attributes are extracted
    if len(validator_map) == 0:
        warnings.warn("No parameters extracted from object, may not be NamedTuple?")
    return validator_map


def prompt_namedtuple(
    nt: NamedTuple,
    attr_validators: Dict[str, AutoHandler] = {},
    type_validators: Dict[Type, AutoHandler] = {},
) -> NamedTuple:
    """
    Generate the list of functions using namedtuple_prompt_funcs
    and prompt the user for each of them
    """

    funcs: Dict[str, Callable[[], Any]] = namedtuple_prompt_funcs(
        nt, attr_validators, type_validators
    )
    nt_values: Dict[str, Any] = {
        attr_key: attr_func() for attr_key, attr_func in funcs.items()
    }
    return nt(**nt_values)  # type: ignore[operator, no-any-return]
