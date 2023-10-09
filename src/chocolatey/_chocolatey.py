# Copyright (c) 2022-2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

"""
Chocolatey API
"""

from typing import Any, Optional, Union, Sequence, Tuple, List, Dict
#from typing import NamedTuple
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
#import enum

from public import public
from nocasedict import NocaseDict
import regex as re

from ._run import run
from ._chocolatey_cmd import ChocolateyCmd


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
    id: str
    version: str


@public
@dataclass
class PackageOutdated(Package):
    available_version: str = None
    pinned: bool = False

    def __post_init__(self):
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
    value: Optional[Union[str, bool]] = None
    description: str = ""

    def __post_init__(self):
        self.value = _str2none("value", self.value)
        self.value = _str2bool("value", self.value, with_check=False)


@public
@dataclass
class Source:
    name: str
    value: str = ""
    disabled: bool = False
    user: Optional[str] = None
    password: Optional[str] = None
    priority: int = 0
    bypass_proxy: bool = False
    self_service: bool = False
    admin_only: bool = False

    def __post_init__(self):
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

    def __post_init__(self):
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

    _allow_multiple = False

    def __new__(cls, source: str = None):
        self = super().__new__(cls)
        self.source = source
        self.cmd    = ChocolateyCmd(self.source)
        return self

    ### High-level API ###

    @property
    def version(self) -> str:
        """Gets the Chocolatey version."""
        try:
            output = self.cmd.choco(version=True, limit_output=True,
                                    **self._capture_output)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return output.stdout.strip()

    @property
    def version_info(self) -> version_info:
        """Gets the Chocolatey version info."""
        parts = [int(item) for item in self.version.split(".")]
        parts[len(parts):] =  (4 - len(parts)) * [0]
        return version_info(*parts)

    def help(self, *, command: str = None) -> str:
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
        return output.stdout.lstrip().replace("\r\n", "\n")

    # run_silent = partial(subprocess.run, stdout=open(os.devnull, 'wb'))
    # FIXME: look at python_vagrant to achieve hide of out and/or err stream

    def installed(self, *filters, all_versions=True,
                  **kwargs) -> Dict[str, List[Package]]:
        """Retrieves a list of locally installed packages."""
        self._omit_args(kwargs, "limit_output", "local_only",
                        "verbose", "detail", "detailed", "idonly", "id_only")
        try:
            output = self.cmd.list(*filters, limit_output=True, local_only=True,
                                   all_versions=all_versions,
                                   **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._packages(output.stdout)

    def outdated(self, *, ignore_pinned=True, ignore_unfound=True,
                 **kwargs) -> Dict[str, List[PackageOutdated]]:
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
        for id, val in list(packages.items()):
            pkgs = [val] if isinstance(val, PackageOutdated) else val
            for idx, pkg in enumerate(pkgs[:]):
                if pkg.version == pkg.available_version: del pkgs[idx]
            if not pkgs: del packages[id]
        return packages

    def search(self, filter=False, *, all_versions=True, **kwargs) \
        -> Dict[str, List[Package]]:
        """Searches remote packages."""
        self._omit_args(kwargs, "limit_output", "page", "page_size",
                        "verbose", "detail", "detailed", "idonly", "id_only")
        out  = "" ; page = 0
        while True:
            try:
                arg = [filter] if filter is not False else []
                output = self.cmd.search(*arg, limit_output=True, page=page,
                                         all_versions=all_versions,
                                         **self._capture_output, **kwargs)
            except run.CalledProcessError as exc:
                self._handle_exception(exc)
            if not output.stdout: break
            out += output.stdout ; page += 1
        return self._packages(out, klass=Package)

    def info(self, *, pkg_id: str, local_only=False, **kwargs) \
        -> Optional[PackageInfo]:
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
            return None
        pkg_info = list(self._packages(output.stdout,
                                       klass=PackageInfo).values())[0]
        try:
            output = self.cmd.info(pkg_id,
                                   local_only=local_only,
                                   **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._info(output.stdout, pkg_info)

    def export(self, output_file_path=False, *, include_version=True,
               **kwargs) -> None:
        """Exports list of currently installed packages."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.export(output_file_path=output_file_path,
                            include_version=include_version,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def install(self, *pkg_ids, yes=True, **kwargs) -> None:
        """Installs packages using configured sources."""
        if not pkg_ids:
            raise TypeError("install() "
                            "missing at least 1 required positional argument")
        self._omit_args(kwargs, "yes")#, "verbose")
        try:
            self.cmd.install(*pkg_ids, yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def upgrade(self, *pkg_ids, install_if_not_installed=True, yes=True,
                **kwargs) -> None:
        """Upgrades packages from various sources."""
        if not pkg_ids:
            raise TypeError("upgrade() "
                            "missing at least 1 required positional argument")
        self._omit_args(kwargs, "install_if_not_installed", "yes")#, "verbose")
        try:
            self.cmd.upgrade(*pkg_ids,
                             install_if_not_installed=install_if_not_installed,
                             yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def uninstall(self, *pkg_ids, yes=True, **kwargs) -> None:
        """Uninstalls packages."""
        if not pkg_ids:
            raise TypeError("uninstall() "
                            "missing at least 1 required positional argument")
        self._omit_args(kwargs, "yes")#, "verbose")
        try:
            self.cmd.uninstall(*pkg_ids, yes=yes, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def pinned(self, **kwargs) -> Dict[str, List[Package]]:
        """Retrieves a list of packages suppress for upgrades."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.pin("list", limit_output=True,
                                  **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._packages(output.stdout)

    def pin_add(self, *, pkg_id: str, **kwargs) -> None:
        """Suppress upgrades for a package."""
        self._omit_args(kwargs, "reason")#, "verbose") # --reason don't work
        try:
            self.cmd.pin("add", name=pkg_id,
                         # reason=reason if reason is False else f'"{reason}"',
                         **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def pin_remove(self, *, pkg_id: str, **kwargs) -> None:
        """Remove suppressing of upgrades for a package."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.pin("remove", name=pkg_id, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def pack(self, nuspec_file_path=False, *, output_directory=False,
             **kwargs) -> None:
        """Packages nuspec, scripts, and other Chocolatey package resources
           into a nupkg file."""
        self._omit_args(kwargs)#, "verbose")
        try:
            arg = [nuspec_file_path] if nuspec_file_path is not False else []
            self.cmd.pack(*arg, output_directory=output_directory, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def push(self, nupkg_file_path=False, **kwargs) -> None:
        """Pushes a compiled nupkg to a source."""
        self._omit_args(kwargs)#, "verbose")
        try:
            arg = [nupkg_file_path] if nupkg_file_path is not False else []
            self.cmd.push(*arg, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def unpackself(self, **kwargs) -> None:
        """Re-installs Chocolatey base files."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.unpackself(**kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def new_package(self, *, pkg_id: str,
                    properties: Optional[Dict[str, str]] = None,
                    **kwargs) -> None:
        """Creates template files for creating a new Chocolatey package."""
        # <name> [<options/switches>] [<property=value> <propertyN=valueN>]
        self._omit_args(kwargs)#, "verbose")
        props = [f'"{prop}={value}"' for prop, value in properties.items()]
        try:
            self.cmd.new(pkg_id, *props, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    # Configuration - https://docs.chocolatey.org/en-us/configuration

    def config(self, **kwargs) ->  Dict[str, Config]:
        """Retrieve config settings."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.config("list", limit_output=True,
                                     **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Config)

    def config_get(self, *, name: str, **kwargs) -> Union[str, bool]:
        """Get config value."""
        self._omit_args(kwargs)#, "verbose")
        try:
            output = self.cmd.config("get", name=name,
                                     **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return _str2bool("stdout", output.stdout, with_check=False)

    def config_set(self, *, name: str, value, **kwargs) -> None:
        """Set config value."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.config("set", name=name, value=(_none2str(name, value)
                                                     if value is None else
                                                     _bool2str(name, value)),
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def config_unset(self, *, name: str, **kwargs) -> None:
        """Unset config."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.config("unset", name=name,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def sources(self, **kwargs) -> Dict[str, Source]:
        """Retrieve default sources."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.sources("list", limit_output=True,
                                      **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Source)

    def source_enable(self, *, name: str, **kwargs) -> None:
        """Enable source."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.sources("enable", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def source_disable(self, *, name: str, **kwargs) -> None:
        """Disable source."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.sources("disable", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def source_remove(self, *, name: str, **kwargs) -> None:
        """Remove source."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.sources("remove", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def features(self, **kwargs) -> Dict[str, Feature]:
        """Retrieve features."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.feature("list", limit_output=True,
                                      **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Feature)

    def feature_get(self, *, name: str, **kwargs) -> bool:
        """Get feature value."""
        self._omit_args(kwargs)#, "verbose")
        try:
            output = self.cmd.feature("get", name=name,
                                      **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return _str2bool("stdout", output.stdout,
                         literals=("enabled", "disabled"))

    def feature_enable(self, *, name: str, **kwargs) -> None:
        """Enable feature."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.feature("enable", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def feature_disable(self, *, name: str, **kwargs) -> None:
        """Disable feature."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.feature("disable", name=name,
                             **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def apikeys(self, **kwargs) -> List[ApiKey]:
        """Retrieve the list of API keys."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.apikey("list", limit_output=True,
                                     **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return list(self._config(output.stdout, klass=ApiKey).values())

    def apikey_add(self, *, source: str, api_key: str, **kwargs) -> None:
        """Add API key for source."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.apikey("add", source=source, api_key=api_key,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def apikey_remove(self, *, source: str, **kwargs) -> None:
        """Remove API key for source."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.apikey("remove", source=source,
                            **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def templates(self, **kwargs) -> Dict[str, Template]:
        """Retrieve templates."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.template("list", limit_output=True,
                                       **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Template)

    def template_info(self, *, name: str, **kwargs) -> Template:
        """Retrieve template info."""
        self._omit_args(kwargs, "limit_output", "verbose")
        try:
            output = self.cmd.template("info", name=name, limit_output=True,
                                       **self._capture_output, **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)
        return self._config(output.stdout, klass=Template)[0]

    def cache_list(self, **kwargs) -> None:
        """Displays information about the local HTTP caches used to store
           queries."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.cache("list", **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    def cache_remove(self, **kwargs) -> None:
        """Remove the local HTTP caches used to store queries."""
        self._omit_args(kwargs)#, "verbose")
        try:
            self.cmd.cache("remove", **kwargs)
        except run.CalledProcessError as exc:
            self._handle_exception(exc)

    #------ internals ------#

    # OUTPUT_QUIET ERROR_QUIET
    # quiet_stdout=True,
    # quiet_stderr=True,
    # env=None,
    # out_cm=None,
    # err_cm=None,

    _capture_output = dict(text=True, capture_output=True)

    def _packages(self, out: str, *, klass=Package) -> Dict[str, Any]:
        lines = [line.strip() for line in out.strip().splitlines()]
        lines.sort(key=str.casefold)
        packages = defaultdict(list)
        for line in lines:
            #print("LINE:", line)
            package = klass(*line.split("|"))
            #print("PKG: ", package)
            if not self._allow_multiple:
                packages[package.id] = package
            else:
                packages[package.id].append(package)
        return dict(packages)

    @classmethod
    def _info(cls, out: str,
              pkg_info: Optional[PackageInfo]) -> Optional[PackageInfo]:
        # if not found, returns None
        if not out.strip() or pkg_info is None:
            return None

        # pre-parse
        out = re.sub("[\t ]*\|", "\n", out)
        out = re.sub("\n[\t ]*Package url[\t ]*\n",
                     "\n Package url: n/a\n", out)
        # parse
        info_header_pattern = rf"\s*Chocolatey[\t ]+v.+?[\t ]*\n" + \
                              rf"\s*(?P<pkg_id>{pkg_info.id})" + \
                              rf"[\t ]+(?P<pkg_version>{pkg_info.version})[\t ]*"
        info_key_pattern    = r"(?P<info_key>[^\t :]+([\t ]+[^\t :]+)*)[\t ]*"
        info_value_pattern  = r"(?P<info_value>.*(\n.*)*?)"
        info_item_pattern   = rf"([\t ]*\n)*?\n[\t ]{{0,2}}" + \
                              rf"{info_key_pattern}:[\t ]*{info_value_pattern}"
        info_items_pattern  = rf"(?P<info_items>({info_item_pattern})+)"
        info_footer_pattern = r"([\t ]*\n)+?\n[\t ]*(?P<pkgs_found>\d+)" + \
                              r"[\t ]+packages[\t ]+found[\t ]*\.[\t ]*"

        match = re.match(info_header_pattern +
                         info_items_pattern +
                         info_footer_pattern, out)

        info = NocaseDict(zip(match.captures("info_key"),
                              match.captures("info_value")))
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
    def _config(cls, out: str, *, klass) -> Dict[str, Any]:
        lines = [line.strip() for line in out.strip().splitlines()]
        lines.sort(key=str.casefold)
        configs = {}
        for line in lines:
            fields = line.split("|")
            configs[fields[0]] = klass(*fields)
        return configs

    @classmethod
    def _omit_args(cls, kwargs, *unnecessary):
        for omit in unnecessary:
            kwargs.pop(omit, None)

    def _handle_exception(self, exc, **kwargs):
        raise exc
        #raise ChocolateyError(???)


@public
class ChocolateyError(RuntimeError):
    """ """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def _str2bool(name: str, value: Any, *, with_check=True,
              literals=("true", "false")):
    if not isinstance(value, str):
        return value
    if not (value.lower() in literals):
        if not with_check: return value
        raise _value_error(name, value)
    return (value.lower() == literals[0])


def _bool2str(name: str, value: Any, *,
              literals=("true", "false")):
    if not isinstance(value, bool):
        return value
    return literals[0 if value else 1]


def _str2int(name: str, value: Any, *, with_check=True):
    if not isinstance(value, str):
        return value
    if not (value.isdigit() or
            value[1:].isdigit() and value[1:] in ("+", "-")):
        if not with_check: return value
        raise _value_error(name, value)
    return int(value)


def _str2none(name: str, value: Any):
    return None if isinstance(value, str) and not value else value


def _none2str(name: str, value: Any):
    return "" if value is None else value


def _value_error(name: str, value: Any):
    return ValueError(f"Improper value ({value}) for '{name}' attribute!")
