# Copyright (c) 2022-2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

__all__ = ('issubtype', 'issequence', 'remove_all', 'pushd')

from typing import Any, Sequence, Tuple, List, Dict
from collections import abc
import contextlib


def issubtype(x: Any, t: Any) -> bool:
    return isinstance(x, type) and issubclass(x, t)


def issequence(x: Any) -> bool:
    return (isinstance(x, (Sequence, abc.Sequence)) and
            not isinstance(x, (bytes, type(u""))))


def remove_all(list: List, value: Any):
    list[:] = (item for item in list if item != value)


@contextlib.contextmanager
def pushd(path):
    import os
    curr_dir = os.getcwd()
    os.chdir(str(path) if isinstance(path, os.PathLike) else path)
    try:
        yield
    finally:
        os.chdir(curr_dir)


del contextlib
