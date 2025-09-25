# Copyright (c) 2022 Adam Karpierz
# SPDX-License-Identifier: Zlib

from __future__ import annotations

"""Chocolatey API"""

import typing
from typing import TypeAlias, Any
from typing_extensions import Self
from collections.abc import Sequence
from os import PathLike
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
import builtins
import tempfile
import shutil
import textwrap
# import enum
# from rich import print

from utlx import public
from utlx import module_path
from utlx import run
from nocasedict import NocaseDict
import regex as re

from ._chocolatey_cmd import ChocolateyCmd

StrPath: TypeAlias = str | PathLike[str]


@public
@dataclass
class version_info:
    major:  int = 0
    minor:  int = 0
    micro:  int = 0
    serial: int = 0


@public
@dataclass
class Package:
    id: str  # noqa: A003
    version: str


@public
@dataclass
class PackageOutdated(Package):
    available_version: str | None = None
    pinned: bool = False

    def __post_init__(self) -> None:
        """Post-init"""
        self.pinned = _str2bool("pinned", self.pinned)


@public
@dataclass
class PackageInfo(Package):
    description: str = ""
    title: str = ""
    summary: str = ""
    # additional
    published: str = ""


@public
@dataclass
class Config:
    name: str
    value: str | bool | None = None
    description: str = ""

    def __post_init__(self) -> None:
        """Post-init"""
        self.value = _str2none("value", self.value)
        self.value = _str2bool("value", self.value, with_check=False)


@public
@dataclass
class Source:
    name: str
    value: str = ""
    disabled: bool = False
    user: str | None = None
    password: str | None = None
    priority: int = 0
    bypass_proxy: bool = False
    self_service: bool = False
    admin_only: bool = False

    def __post_init__(self) -> None:
        """Post-init"""
        self.disabled     = _str2bool("disabled", self.disabled)
        self.user         = _str2none("user", self.user)
        self.password     = _str2none("password", self.password)
        self.priority     = _str2int("priority", self.priority)
        self.bypass_proxy = _str2bool("bypass_proxy", self.bypass_proxy)
        self.self_service = _str2bool("self_service", self.self_service)
        self.admin_only   = _str2bool("admin_only", self.admin_only)


@public
@dataclass
class Feature:
    name: str
    enabled: bool = False
    description: str = ""
    # set_explicitly: bool = False

    def __post_init__(self) -> None:
        """Post-init"""
        self.enabled = _str2bool("enabled", self.enabled,
                                 literals=("enabled", "disabled"))


@public
@dataclass
class ApiKey:
    source: str
    info: str


@public
@dataclass
class Template:
    name: str
    version: str


@public
class Chocolatey:
    """Chocolatey API"""

    _allow_multiple: bool = False

    _SETUP_DIR = module_path()/"choco-setup"

    source: str | None
    cmd: ChocolateyCmd

    def __new__(cls, source: str | None = None) -> Self:
        """Constructor"""
        self = super().__new__(cls)
        self.source = source
        self.cmd = ChocolateyCmd(self.source)
        return self

    ### High-level API ###

    @classmethod
    def setup(cls) -> None:
        """Setup chocolatey software."""
        choco_pkg = next(cls._SETUP_DIR.glob("chocolatey.*.nupkg"))
        # Install chocolatey
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file = Path(temp_dir)/"chocolatey.zip"
            shutil.copy2(str(choco_pkg), str(zip_file))
            run(shutil.which("powershell.exe"), "-ExecutionPolicy", "Bypass",
                cls._SETUP_DIR/"install.ps1", "-ChocolateyDownloadUrl", zip_file)

    @property
    def version(self) -> str:
        """Gets the Chocolatey version."""
        try:
            output = self.cmd.choco(version=True, limit_output=True,
                                    source=False, **self._capture_output)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return output.stdout.strip()

    @property
    def version_info(self) -> version_info:
        """Gets the Chocolatey version info."""
        parts = [int(item) for item in self.version.split(".")]
        parts[len(parts):] =  (4 - len(parts)) * [0]
        return version_info(*parts)

    def help(self, *, command: str | None = None) -> str:  # noqa: A003
        """Gets the help information for choco and choco commands."""
        try:
            if not command:
                output = self.cmd.help(limit_output=True,
                                       **self._capture_output)
            else:
                output = self.cmd.choco(command, help=True,
                                        limit_output=True,
                                        **self._capture_output)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return output.stdout.lstrip().replace("\r\n", "\n").replace("\r", "\n")

    def license(self, **kwargs: Any) -> str:  # noqa: A003
        """Gets the information about the current Chocolatey CLI license [v2.5.0+]."""
        self._omit_args(kwargs, "limit_output")
        try:
            output = self.cmd.license(limit_output=True,
                                      **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return output.stdout.lstrip().replace("\r\n", "\n").replace("\r", "\n")

    def support(self, **kwargs: Any) -> str:
        """Provides support information [v2.5.0+]."""
        self._omit_args(kwargs, "limit_output")
        try:
            output = self.cmd.support(limit_output=True,
                                      **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return output.stdout.lstrip().replace("\r\n", "\n").replace("\r", "\n")

    # run_silent = partial(subprocess.run, stdout=open(os.devnull, 'wb'))
    # FIXME: look at python_vagrant to achieve hide of out and/or err stream

    def installed(self, *filters: str, **kwargs: Any) -> dict[str, list[Package]]:
        """Retrieves a list of locally installed packages."""
        self._omit_args(kwargs, "all_versions",  # Removed from choco list since v2.0.0
                        "limit_output", "local_only",
                        "verbose", "detail", "detailed", "idonly", "id_only")
        try:
            output = self.cmd.list(*filters, limit_output=True,
                                   local_only=True, source=False,
                                   **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._packages(output.stdout)

    def outdated(self, *, ignore_pinned: bool = True, ignore_unfound: bool = True,
                 **kwargs: Any) -> dict[str, list[PackageOutdated]]:
        """Retrieves information about packages that are outdated."""
        self._omit_args(kwargs, "limit_output",
                        "verbose", "detail", "detailed", "idonly", "id_only")
        try:
            output = self.cmd.outdated(limit_output=True,
                                       ignore_pinned=ignore_pinned,
                                       ignore_unfound=ignore_unfound,
                                       **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        packages = self._packages(output.stdout, klass=PackageOutdated)
        for pkg_id, val in list(packages.items()):
            pkgs = [val] if isinstance(val, PackageOutdated) else val
            for idx, pkg in enumerate(pkgs[:]):
                if pkg.version == pkg.available_version: del pkgs[idx]
            if not pkgs: del packages[pkg_id]
        return packages

    def search(self, filter: str | bool = False, *,  # noqa: A002
               all_versions: bool = False, exact: bool = False,
               **kwargs: Any) -> dict[str, list[Package]]:
        """Searches remote packages."""
        self._omit_args(kwargs, "limit_output", "page", "page_size",
                        "verbose", "detail", "detailed", "idonly", "id_only")
        out  = "" ; page = 0
        while True:
            try:
                arg = [filter] if filter is not False else []
                output = self.cmd.search(*arg, limit_output=True, page=page,
                                         all_versions=all_versions, exact=exact,
                                         **self._capture_output, **kwargs)
            except run.CalledProcessError as exc:
                self._handle_exception(exc)
            if not output.stdout: break
            out += output.stdout ; page += 1
            if exact: break
        return self._packages(out, allow_multiple=all_versions)

    def info(self, *, pkg_id: str, local_only: bool = False,
             **kwargs: Any) -> PackageInfo | None:
        """Retrieves package information."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.info(pkg_id, limit_output=True,
                                   local_only=local_only,
                                   **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        # if not found, returns None
        if not output.stdout.strip():
            return None  # pragma: no cover
        packages = self._packages(output.stdout, klass=PackageInfo)
        if not packages:
            return None  # pragma: no cover
        pkg_info = list(packages.values())[0]
        try:
            output = self.cmd.info(pkg_id,
                                   local_only=local_only,
                                   **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._info(output.stdout, pkg_info)

    def export(self, output_file_path: StrPath | bool = False, *,
               include_version_numbers: bool = True, **kwargs: Any) -> None:
        """Exports list of currently installed packages."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.export(output_file_path=output_file_path,
                            include_version_numbers=include_version_numbers,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def install(self, *pkg_ids: str, yes: bool = True, **kwargs: Any) -> None:
        """Installs packages using configured sources."""
        if not pkg_ids:
            raise Chocolatey.TypeError("install() "
                                       "missing at least 1 required positional argument")
        self._omit_args(kwargs, "yes")  # , "verbose")
        try:
            self.cmd.install(*pkg_ids, yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def upgrade(self, *pkg_ids: str, install_if_not_installed: bool = True,
                yes: bool = True, **kwargs: Any) -> None:
        """Upgrades packages from various sources."""
        if not pkg_ids:
            raise Chocolatey.TypeError("upgrade() "
                                       "missing at least 1 required positional argument")
        self._omit_args(kwargs, "install_if_not_installed", "yes")  # , "verbose")
        try:
            self.cmd.upgrade(*pkg_ids,
                             install_if_not_installed=install_if_not_installed,
                             yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def uninstall(self, *pkg_ids: str, yes: bool = True, all_versions: bool = False,
                  **kwargs: Any) -> None:
        """Uninstalls packages."""
        if not pkg_ids:
            raise Chocolatey.TypeError("uninstall() "
                                       "missing at least 1 required positional argument")
        self._omit_args(kwargs, "yes")  # , "verbose")
        try:
            self.cmd.uninstall(*pkg_ids, all_versions=all_versions,
                               yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def pinned(self, **kwargs: Any) -> dict[str, list[Package]]:
        """Retrieves a list of packages suppress for upgrades."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.pin("list", limit_output=True,
                                  **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._packages(output.stdout)

    def pin_add(self, *, pkg_id: str, **kwargs: Any) -> None:
        """Suppress upgrades for a package."""
        self._omit_args(kwargs, "reason")  # , "verbose") # --reason don't work
        try:
            self.cmd.pin("add", name=pkg_id,
                         # reason=reason if reason is False else f'"{reason}"',
                         **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def pin_remove(self, *, pkg_id: str, **kwargs: Any) -> None:
        """Remove suppressing of upgrades for a package."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.pin("remove", name=pkg_id, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def pack(self, nuspec_file_path: StrPath | bool = False, *,
             output_directory: StrPath | bool = False, **kwargs: Any) -> None:
        """Packages nuspec, scripts, and other package resources into a nupkg file."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            arg = [nuspec_file_path] if nuspec_file_path is not False else []
            self.cmd.pack(*arg, output_directory=output_directory, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def push(self, nupkg_file_path: StrPath | bool = False, yes: bool = True,
             **kwargs: Any) -> None:  # pragma: no cover
        """Pushes a compiled nupkg to a source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            arg = [nupkg_file_path] if nupkg_file_path is not False else []
            self.cmd.push(*arg, yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def new_package(self, *, pkg_id: str,
                    properties: dict[str, str] | None = None,
                    **kwargs: Any) -> None:
        """Creates template files for creating a new Chocolatey package."""
        # <name> [<options/switches>] [<property=value> <propertyN=valueN>]
        self._omit_args(kwargs)  # , "verbose")
        props = ([] if properties is None else
                 [f'"{prop}={value}"' for prop, value in properties.items()])
        try:
            self.cmd.new(pkg_id, *props, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    # Configuration - https://docs.chocolatey.org/en-us/configuration

    def config(self, **kwargs: Any) -> dict[str, Config]:
        """Retrieve config settings."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.config("list", limit_output=True,
                                     **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Config)

    def config_get(self, *, name: str, **kwargs: Any) -> str | bool:
        """Get config value."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            output = self.cmd.config("get", name=name, limit_output=True,
                                     **self._capture_output, **kwargs)
            value = output.stdout
            if value and value[-1] == "\n": value = value[:-1]
            if value and value[-1] == "\r": value = value[:-1]
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return typing.cast(str | bool, _str2bool("stdout", value,
                                                 with_check=False))

    def config_set(self, *, name: str, value: Any, **kwargs: Any) -> None:
        """Set config value."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            if value is None or value == "":
                self.cmd.config("unset", name=name,
                                **self._capture_output, **kwargs)
            else:
                self.cmd.config("set", name=name, value=_bool2str(name, value),
                                **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def config_unset(self, *, name: str, **kwargs: Any) -> None:
        """Unset config."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.config("unset", name=name,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def sources(self, **kwargs: Any) -> dict[str, Source]:
        """Retrieve default sources."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.source("list", limit_output=True,
                                     **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Source)

    def source_add(self, *, name: str, source: str, **kwargs: Any) -> None:
        """Add source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.source("add", name=name, source=source,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def source_enable(self, *, name: str, **kwargs: Any) -> None:
        """Enable source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.source("enable", name=name,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def source_disable(self, *, name: str, **kwargs: Any) -> None:
        """Disable source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.source("disable", name=name,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def source_remove(self, *, name: str, **kwargs: Any) -> None:
        """Remove source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.source("remove", name=name,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def features(self, **kwargs: Any) -> dict[str, Feature]:
        """Retrieve features."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.feature("list", limit_output=True,
                                      **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Feature)

    def feature_get(self, *, name: str, **kwargs: Any) -> bool:
        """Get feature value."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            output = self.cmd.feature("get", name=name, limit_output=True,
                                      **self._capture_output, **kwargs)
            value = output.stdout.strip()
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return typing.cast(bool, _str2bool("stdout", value,
                                           literals=("enabled", "disabled")))

    def feature_enable(self, *, name: str, **kwargs: Any) -> None:
        """Enable feature."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.feature("enable", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def feature_disable(self, *, name: str, **kwargs: Any) -> None:
        """Disable feature."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.feature("disable", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def apikeys(self, **kwargs: Any) -> list[ApiKey]:
        """Retrieve the list of API keys."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.apikey("list", limit_output=True,
                                     **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return list(self._config(output.stdout, klass=ApiKey).values())

    def apikey_add(self, *, source: str, api_key: str, **kwargs: Any) -> None:
        """Add API key for source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.apikey("add", source=source, api_key=api_key,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def apikey_remove(self, *, source: str, **kwargs: Any) -> None:
        """Remove API key for source."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.apikey("remove", source=source,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def templates(self, **kwargs: Any) -> dict[str, Template]:
        """Retrieve templates."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.template("list", limit_output=True,
                                       **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Template)

    def template_info(self, *, name: str, **kwargs: Any) -> Template:
        """Retrieve template info."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.template("info", name=name, limit_output=True,
                                       **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        templates: dict[str, Template] = self._config(output.stdout, klass=Template)
        return list(templates.values())[0]

    def cache_list(self, **kwargs: Any) -> None:
        """Displays information about the local HTTP caches used to store queries."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.cache("list", **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def cache_remove(self, **kwargs: Any) -> None:
        """Remove the local HTTP caches used to store queries."""
        self._omit_args(kwargs)  # , "verbose")
        try:
            self.cmd.cache("remove", **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    # ----- internals ----- #

    # OUTPUT_QUIET ERROR_QUIET
    # quiet_stdout=True,
    # quiet_stderr=True,
    # env=None,
    # out_cm=None,
    # err_cm=None,

    _capture_output = dict(text=True, capture_output=True)

    def _packages(self, out: str, *, klass: type = Package,
                  allow_multiple: bool | None = None) -> dict[str, Any]:
        lines = [line.strip() for line in out.strip().splitlines()]
        lines.sort(key=str.casefold)
        packages = defaultdict(list)
        for line in lines:
            # print("LINE:", line)
            package = klass(*line.split("|"))
            # print("PKG: ", package)
            if self._allow_multiple if allow_multiple is None else allow_multiple:
                packages[package.id].append(package)
            else:
                packages[package.id] = package
        return dict(packages)

    @classmethod
    def _info(cls, out: str,
              pkg_info: PackageInfo | None) -> PackageInfo | None:
        # if not found, returns None
        if not out.strip() or pkg_info is None:
            return None  # pragma: no cover

        out = out.replace("\r\n", "\n").replace("\r", "\n")

        # pre-parse
        out = re.sub(r"[\t ]*\|", "\n", out)
        out = re.sub(r"\n[\t ]*Package url[\t ]*\n", "\n Package url: n/a\n", out)
        # parse
        info_header_pattern = r"\s*Chocolatey[\t ]+v.+?([\t ]*\n)+" + \
                              rf"\s*{pkg_info.id}[\t ]+{pkg_info.version}([\t ]+\[\w+\])?" + \
                              r"([\t ]*\n)+"
        info_pattern        = r"(?P<info>(.*\n)*)"
        info_footer_pattern = r"\n(?P<pkgs_found>\d+)" + \
                              r"[\t ]+packages[\t ]+(found|installed)[\t ]*\.([\t ]*\n)*"
        match = re.match(info_header_pattern
                         + info_pattern
                         + info_footer_pattern, out)
        if not match: return pkg_info  # pragma: no cover
        info_text = textwrap.dedent(match.captures("info")[0])
        if not info_text.endswith("\n"): info_text += "\n"

        info_key_pattern   = r"(?P<info_key>[^\t :]+([\t ]+[^\t :]+)*)"
        info_value_pattern = r"(?P<info_value>.*(\n([\t ]+.*)?)*)"
        info_item_pattern  = rf"{info_key_pattern}[\t ]*:[\t ]*{info_value_pattern}"
        info_items_pattern = rf"(?P<info_items>({info_item_pattern}\n)+)"

        match = re.match(info_items_pattern, info_text)
        if not match: return pkg_info  # pragma: no cover
        info = NocaseDict(zip(match.captures("info_key"),
                              match.captures("info_value")))
        # print("============================")
        # print(dict(info))
        # print("============================")
        pkg_info.description = info.pop("Description", "")
        pkg_info.title       = info.pop("Title", "")
        pkg_info.summary     = info.pop("Summary", "")
        # additional
        pkg_info.published   = info.pop("Published", "")

        # TODO:
        """
        Exist in package with empty metadata (only required fields set).
        ----------------------------------------------------------------
        Number of Downloads: n/a
        Downloads for this version: n/a
        Package url
        Chocolatey Package Source: n/a
        Tags:
        Software Site: n/a
        Software License: n/a
        """
        return pkg_info

    @classmethod
    def _config(cls, out: str, *, klass: type) -> dict[str, Any]:
        lines = [line.strip() for line in out.strip().splitlines()]
        lines.sort(key=str.casefold)
        configs = {}
        for line in lines:
            fields = line.split("|")
            configs[fields[0]] = klass(*fields)
        return configs

    @classmethod
    def _omit_args(cls, kwargs: dict[str, Any], *unnecessary: Any) -> None:
        for omit in unnecessary:
            kwargs.pop(omit, None)

    def _handle_exception(self, exc: BaseException, **kwargs: Any) -> None:
        raise exc  # pragma: no cover
        # raise Chocolatey.RuntimeError(???)

    class Error(Exception):
        """Chocolatey error."""

    class TypeError(builtins.TypeError, Error):  # noqa: A001
        """Chocolatey type error."""

    class ValueError(builtins.ValueError, Error):  # noqa: A001
        """Chocolatey value error."""

    class RuntimeError(builtins.RuntimeError, Error):  # noqa: A001
        """Chocolatey runtime error."""


def _bool2str(name: str, value: Any, *,
              literals: Sequence[str] = ("true", "false")) -> Any:
    if not isinstance(value, bool):
        return value
    return literals[0 if value else 1]


def _str2bool(name: str, value: Any, *, with_check: bool = True,
              literals: Sequence[str] = ("true", "false")) -> Any:
    if not isinstance(value, str):
        return value
    if not (value.lower() in literals):
        if not with_check: return value
        raise Chocolatey.ValueError(f"Improper value ({value}) for '{name}' attribute!")
    return (value.lower() == literals[0])


def _str2int(name: str, value: Any, *, with_check: bool = True) -> Any:
    if not isinstance(value, str):
        return value
    if not (value.isdigit()
            or value[1:].isdigit() and value[1:] in ("+", "-")):
        if not with_check: return value
        raise Chocolatey.ValueError(f"Improper value ({value}) for '{name}' attribute!")
    return int(value)


def _str2none(name: str, value: Any) -> Any:
    return None if isinstance(value, str) and not value else value
