# Copyright (c) 2022 Adam Karpierz
# SPDX-License-Identifier: Zlib

from __future__ import annotations

"""Low-level Chocolatey API"""

import typing
from typing import TypeAlias, Any
from typing_extensions import Self
from collections.abc import Callable
import sys
import ctypes
from functools import partialmethod

from utlx import public
from utlx import module_path
from utlx import run
import platformdirs

CompletedProcessCallable: TypeAlias = Callable[..., run.CompletedTextProcess]


@public
class ChocolateyCmd:
    """Chocolatey commands"""

    _CHOCOLATEY_EXE = platformdirs.site_data_path()/"chocolatey/bin/choco.exe"
    _LAUNCHER_EXE   = module_path()/"exe-bin/launcher.exe"

    _source: str | None

    def __new__(cls, source: str | None = None) -> Self:
        """Constructor"""
        self = super().__new__(cls)
        self._source = source
        return self

    ## Low-level Chocolatey API ##

    def choco(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Run raw choco executable."""
        return self._cmd(*args, source=self._get_source(kwargs), **kwargs)

    def help(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:  # noqa: A003
        """Displays top level help information for choco."""
        return self._cmd("help", *args, source=self._get_source(kwargs), **kwargs)

    def license(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:  # noqa: A003
        """Display Chocolatey license information (v2.5.0+)."""
        return self._cmd("license", *args, **kwargs)

    def support(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Provides support information (v2.5.0+)."""
        return self._cmd("support", *args, **kwargs)

    def apikey(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Retrieves, saves or deletes an API key for a particular source."""
        return self._cmd("apikey", *args, source=self._get_source(kwargs), **kwargs)

    setapikey = apikey  # alias for apikey

    def cache(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Manage the local HTTP caches used to store queries (v2.1.0+)."""
        return self._cmd_elevated("cache", *args, **kwargs)

    def config(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Retrieve and configure config file settings."""
        cmd = self._cmd if args[0] in ("list",) else self._cmd_elevated
        return cmd("config", *args, **kwargs)

    def export(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Exports list of currently installed packages."""
        return self._cmd("export", *args, **kwargs)

    def feature(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """View and configure choco features."""
        return self._cmd("feature", *args, **kwargs)

    features = feature  # alias for feature

    def search(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Searches remote packages."""
        return self._cmd("search", *args, source=self._get_source(kwargs), **kwargs)

    find = search  # alias for search

    def info(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Retrieves package information.

        Shorthand for choco search pkgname --exact --verbose.
        """
        return self._cmd("info", *args, source=self._get_source(kwargs), **kwargs)

    def list(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:  # noqa: A003
        """Lists local packages."""
        return self._cmd("list", *args, source=self._get_source(kwargs), **kwargs)

    def outdated(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Retrieves information about packages that are outdated.

        Similar to upgrade all --noop.
        """
        return self._cmd("outdated", *args, source=self._get_source(kwargs), **kwargs)

    def install(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Installs packages using configured sources."""
        return self._cmd_elevated("install", *args, source=self._get_source(kwargs), **kwargs)

    def upgrade(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Upgrades packages from various sources."""
        return self._cmd_elevated("upgrade", *args, source=self._get_source(kwargs), **kwargs)

    def uninstall(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Uninstalls a package."""
        return self._cmd_elevated("uninstall", *args, source=self._get_source(kwargs), **kwargs)

    def new(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Creates template files for creating a new Chocolatey package."""
        return self._cmd("new", *args, source=self._get_source(kwargs), **kwargs)

    def pack(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Packages nuspec, scripts, and other Chocolatey package resources into a nupkg file."""
        return self._cmd("pack", *args, **kwargs)

    def pin(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Suppress upgrades for a package."""
        cmd = self._cmd if args[0] in ("list",) else self._cmd_elevated
        return cmd("pin", *args, **kwargs)

    def push(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:  # pragma: no cover
        """Pushes a compiled nupkg to a source."""
        return self._cmd("push", *args, source=self._get_source(kwargs), **kwargs)

    def source(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """View and configure default sources."""
        cmd = self._cmd if args[0] in ("list",) else self._cmd_elevated
        return cmd("source", *args, **kwargs)

    sources = source  # alias for source

    def template(self, *args: Any, **kwargs: Any) -> run.CompletedTextProcess:
        """Get information about installed templates."""
        return self._cmd("template", *args, **kwargs)

    templates = template  # alias for template

    # ----- internals ----- #

    def _get_source(self, kwargs: dict[str, Any]) -> Any:
        return kwargs.pop("source", f'"{self._source}"' if self._source else False)

    _common_args = ["--accept-license", "--no-progress"]

    @classmethod
    def _run_wrapper(cls, run_fun: CompletedProcessCallable, *args: Any,
                     __format: str = "--{}", **kwargs: Any) -> run.CompletedTextProcess:
        normal_args = (arg for arg in args if arg is not None)
        allowed_kwargs, reserved_kwargs = run.split_kwargs(kwargs, cls._run_reserved_kwargs)
        allowed_args = sum(([__format.format(key.replace("_", "-")
                                             + ("" if val is True else f"={val}"))]
                            for key, val in allowed_kwargs.items() if val is not False),
                           []) + cls._common_args
        return run_fun(*normal_args, *allowed_args, **reserved_kwargs)

    _run_reserved_kwargs = {"stdin", "input", "stdout", "stderr", "capture_output",
                            "shell", "cwd", "timeout", "check", "encoding", "errors",
                            "text", "env", "universal_newlines"}

    @property
    def _in_elevated(self) -> bool:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        win_ver  = sys.getwindowsversion()
        return is_admin or win_ver.build < 6000

    @property
    def _cmd_elevated(self) -> CompletedProcessCallable:
        return self._cmd if self._in_elevated else self._cmd_launched

    _cmd = typing.cast(CompletedProcessCallable,
                       partialmethod(_run_wrapper, run, _CHOCOLATEY_EXE))
    _cmd_launched = typing.cast(CompletedProcessCallable,
                       partialmethod(_run_wrapper, run, _LAUNCHER_EXE, _CHOCOLATEY_EXE))
