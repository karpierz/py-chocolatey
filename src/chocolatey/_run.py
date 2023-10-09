# Copyright (c) 2012-2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

__all__ = ('run', 'split_kwargs')

from typing import Any, Sequence, Tuple, List, Dict
import subprocess
import logging

log = logging.getLogger(__name__)


def run(*args, start_terminal_window=False, **kwargs):
    """
    Run the command described by args.
    Wait for command to complete, then return a subprocess.CompletedProcess instance.
    :param args: command line arguments which are provided to E-Sys.bat
    :param start_terminal_window: start E-Sys.bat in separate console window (for server mode)
    :param kwargs: arguments tu control subprocess execution
    :return: subprocess.CompletedProcess instance
    """
    if start_terminal_window:
        args = ["cmd.exe", "/C", "start", *args]
    output = subprocess.run([str(arg) for arg in args], check=kwargs.pop("check", True), **kwargs)
    print_cmd = [("*****" if isinstance(arg, run.SafeString) else arg) for arg in args]
    log.debug(f"cmd:{print_cmd}, returncode:{output.returncode}")#, stdout:{output.stdout}, stderr:{output.stderr}")
    return output


run.CompletedProcess = subprocess.CompletedProcess

run.PIPE    = subprocess.PIPE
run.STDOUT  = subprocess.STDOUT
run.DEVNULL = subprocess.DEVNULL

run.SubprocessError    = subprocess.SubprocessError
run.TimeoutExpired     = subprocess.TimeoutExpired
run.CalledProcessError = subprocess.CalledProcessError

run.SafeString = type("SafeString", (str,), dict())


def split_kwargs(kwargs: Dict[str, Any], forbidden_kwargs: Sequence[str]) \
    -> Tuple[Dict[str, Any], Dict[str, Any]]:
    allowed_kwargs  = {key: val for key, val in kwargs.items()
                       if key not in forbidden_kwargs}
    reserved_kwargs = {key: val for key, val in kwargs.items()
                       if key in forbidden_kwargs}
    return (allowed_kwargs, reserved_kwargs)
