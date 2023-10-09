# Copyright (c) 2022-2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

"""
Low-level Chocolatey API
"""

import sys
import ctypes
from pathlib   import Path
from functools import partialmethod

from public import public

from . import _run
from ._run import run


@public
class ChocolateyCmd:
    """Chocolatey commands"""

    _CHOCOLATEY_EXE = Path("C:/ProgramData/chocolatey/bin/choco.exe")
    _LAUNCHER_EXE   = Path(__file__).resolve().parent/"exe-bin"/"launcher.exe"


    def __new__(cls, source: str = None):
        self = super().__new__(cls)
        self.source = source
        return self

    ## Low-level Chocolatey API ##

    def choco(self, *args, **kwargs) -> run.CompletedProcess:
        """Run raw choco executable."""
        return self._cmd(*args, source=self._get_source(kwargs), **kwargs)

    def help(self, *args, **kwargs) -> run.CompletedProcess:
        """Displays top level help information for choco."""
        return self._cmd("help", *args, source=self._get_source(kwargs), **kwargs)

    def apikey(self, *args, **kwargs) -> run.CompletedProcess:
        """Retrieves, saves or deletes an API key for a particular source."""
        return self._cmd("apikey", *args, source=self._get_source(kwargs), **kwargs)

    setapikey = apikey  # alias for apikey

    def cache(self, *args, **kwargs) -> run.CompletedProcess:
        """Manage the local HTTP caches used to store queries (v2.1.0+)."""
        return self._cmd_elevated("cache", *args, source=self._get_source(kwargs), **kwargs)

    def config(self, *args, **kwargs) -> run.CompletedProcess:
        """Retrieve and configure config file settings."""
        cmd = self._cmd if args[0] in ("list",) else self._cmd_elevated
        return cmd("config", *args, source=self._get_source(kwargs), **kwargs)

    def export(self, *args, **kwargs) -> run.CompletedProcess:
        """Exports list of currently installed packages."""
        return self._cmd("export", *args, source=self._get_source(kwargs), **kwargs)

    def feature(self, *args, **kwargs) -> run.CompletedProcess:
        """View and configure choco features."""
        return self._cmd("feature", *args, source=self._get_source(kwargs), **kwargs)

    features = feature  # alias for feature

    def search(self, *args, **kwargs) -> run.CompletedProcess:
        """Searches remote packages."""
        return self._cmd("search", *args, source=self._get_source(kwargs), **kwargs)

    find = search  # alias for search

    def info(self, *args, **kwargs) -> run.CompletedProcess:
        """Retrieves package information.
           Shorthand for choco search pkgname --exact --verbose."""
        return self._cmd("info", *args, source=self._get_source(kwargs), **kwargs)

    def list(self, *args, **kwargs) -> run.CompletedProcess:
        """Lists local packages."""
        return self._cmd("list", *args, source=self._get_source(kwargs), **kwargs)

    def outdated(self, *args, **kwargs) -> run.CompletedProcess:
        """Retrieves information about packages that are outdated.
           Similar to upgrade all --noop."""
        return self._cmd("outdated", *args, source=self._get_source(kwargs), **kwargs)

    def install(self, *args, **kwargs) -> run.CompletedProcess:
        """Installs packages using configured sources."""
        return self._cmd_elevated("install", *args, source=self._get_source(kwargs), **kwargs)

    def upgrade(self, *args, **kwargs) -> run.CompletedProcess:
        """Upgrades packages from various sources."""
        output = self._cmd_elevated("upgrade", *args, source=self._get_source(kwargs), **kwargs)

    def uninstall(self, *args, **kwargs) -> run.CompletedProcess:
        """Uninstalls a package."""
        return self._cmd_elevated("uninstall", *args, source=self._get_source(kwargs), **kwargs)

    def new(self, *args, **kwargs) -> run.CompletedProcess:
        """Creates template files for creating a new Chocolatey package."""
        return self._cmd("new", *args, source=self._get_source(kwargs), **kwargs)

    def pack(self, *args, **kwargs) -> run.CompletedProcess:
        """Packages nuspec, scripts, and other Chocolatey package resources into a nupkg file."""
        return self._cmd("pack", *args, source=self._get_source(kwargs), **kwargs)

    def pin(self, *args, **kwargs) -> run.CompletedProcess:
        """Suppress upgrades for a package."""
        cmd = self._cmd if args[0] in ("list",) else self._cmd_elevated
        return cmd("pin", *args, source=self._get_source(kwargs), **kwargs)

    def push(self, *args, **kwargs) -> run.CompletedProcess:
        """Pushes a compiled nupkg to a source."""
        return self._cmd("push", *args, source=self._get_source(kwargs), **kwargs)

    def sources(self, *args, **kwargs) -> run.CompletedProcess:
        """View and configure default sources."""
        return self._cmd("sources", *args, source=self._get_source(kwargs), **kwargs)

    def template(self, *args, **kwargs) -> run.CompletedProcess:
        """Get information about installed templates."""
        return self._cmd("template", *args, source=self._get_source(kwargs), **kwargs)

    templates = template  # alias for template

    def unpackself(self, *args, **kwargs) -> run.CompletedProcess:
        """Re-installs Chocolatey base files."""
        return self._cmd("unpackself", *args, source=self._get_source(kwargs), **kwargs)

    #------ internals ------#

    def _get_source(self, kwargs):
        return kwargs.pop("source", f'"{self.source}"' if self.source else False)

    _common_args = ["--accept-license", "--no-progress"]

    @classmethod
    def _run_wrapper(cls, run_fun, *args, __format="--{}", **kwargs):
        normal_args = (arg for arg in args if arg is not None)
        allowed_kwargs, reserved_kwargs = _run.split_kwargs(kwargs, cls._run_reserved_kwargs)
        allowed_args = sum(([__format.format(key.replace("_", "-") +
                                             ("" if val is True else f"={val}"))]
                            for key, val in allowed_kwargs.items() if val is not False),
                           []) + cls._common_args
        return run_fun(*normal_args, *allowed_args, **reserved_kwargs)

    _run_reserved_kwargs = {"stdin", "input", "stdout", "stderr", "capture_output",
                            "shell", "cwd", "timeout", "check", "encoding", "errors",
                            "text", "env", "universal_newlines"}

    @property
    def _in_elevated(self):
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        win_ver  = sys.getwindowsversion()
        return is_admin or win_ver.build < 6000

    @property
    def _cmd_elevated(self):
        return self._cmd if self._in_elevated else self._cmd_launched

    _cmd = partialmethod(_run_wrapper, run, _CHOCOLATEY_EXE)
    _cmd_launched = partialmethod(_run_wrapper, run, _LAUNCHER_EXE, _CHOCOLATEY_EXE)
