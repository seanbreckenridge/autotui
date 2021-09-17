from os import environ
import warnings


def warn(message: str) -> None:
    """
    If AUTOTUI_DISABLE_WARNINGS=1 is set as an environment variable
    ignore this warning

    Otherwise, print with the normal warnings.warn call
    """
    if "AUTOTUI_DISABLE_WARNINGS" in environ:
        disabled = bool(int(environ["AUTOTUI_DISABLE_WARNINGS"]))
        if disabled:
            return
    warnings.warn(message)
