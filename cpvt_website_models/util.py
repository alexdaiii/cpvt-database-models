import inspect
import os
from types import NoneType


def get_location(file: str | None = None) -> str:
    """
    Get the absolute path of the file that called this function.
    """
    # https://stackoverflow.com/questions/13699283/how-to-get-the-callers-filename-method-name-in-python
    if file is None:
        frame = inspect.stack()[1]
        file = frame[0].f_code.co_filename

    return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(file)))


def mkdir_p(path: str) -> None:
    """ 
    Make a directory if it doesn't exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def to_dict(obj: object, depth: int = 0, max_depth: int = 3):
    """
    Converts an object into a dictionary
    """
    if depth > max_depth:
        return obj.__str__()

    prim_types = (int, float, str, bool, NoneType)

    return {
        o_attr: (
            getattr(obj, o_attr)
            if isinstance(
                getattr(obj, o_attr),
                prim_types,
            )
            else to_dict(getattr(obj, o_attr), depth + 1, max_depth)
        )
        for o_attr in dir(obj)
        if not o_attr.startswith("_") and not callable(getattr(obj, o_attr))
    } | {"__class": obj.__class__.__name__}


__all__ = ["get_location", "mkdir_p", "to_dict"]
