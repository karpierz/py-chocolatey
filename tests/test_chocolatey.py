# Copyright (c) 2022-2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

from typing import Any, Optional, Union, Sequence, Tuple, List, Dict
import unittest
from functools import partial
from pathlib import Path
import os, shutil, tempfile
import threading

from rich.pretty import pprint
pprint = partial(pprint, max_length=500)
from ._util import pushd

import chocolatey
from chocolatey import Chocolatey

here = Path(__file__).resolve().parent
data_dir = here/"data"


class ChocolateyCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.choco = Chocolatey()
        cls.lock = threading.Lock()

    ### High-level API ###

    def test_version(self):
        """Gets the Chocolatey version."""
        print()
        version = self.choco.version
        self.assertIsInstance(version, str)
        print("CHOCO VERSION:", version)

    def test_version_info(self):
        """Gets the Chocolatey version info."""
        print()
        version_info = self.choco.version_info
        self.assertIsInstance(version_info, chocolatey.version_info)
        self.assertIsInstance(version_info.major,  int)
        self.assertIsInstance(version_info.minor,  int)
        self.assertIsInstance(version_info.micro,  int)
        self.assertIsInstance(version_info.serial, int)
        print("CHOCO VERSION INFO:", version_info)

    def test_help(self):
        """Gets the help information for choco and choco commands."""
        self.assertTrue(1 == 1)

    def test_installed(self):
        """Retrieves a list of locally installed packages."""
        print()
        installed = self.choco.installed()
        self.assertIsInstance(installed, Dict)
        print("INSTALLED:") ; pprint(installed)

    def test_outdated(self):
        """Retrieves information about packages that are outdated."""
        print()
        outdated = self.choco.outdated()
        self.assertIsInstance(outdated, Dict)
        print("OUTDATED:") ; pprint(outdated)

    def test_search(self):
        """Searches remote packages."""
        #print("INSTALLED:") ; pprint(choco.search(local_only=True))
        #print("SEARCH:")    ; pprint(choco.search())
        self.assertTrue(1 == 1)

    def test_info(self):
        """Retrieves package information."""
        print()
        pkg_info = self.choco.info(pkg_id="chocolatey")
        self.assertIsInstance(pkg_info, chocolatey.PackageInfo)
        print("PACKAGE INFO:") ; pprint(pkg_info)

    def test_export(self):
        """Exports list of currently installed packages."""
        print()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            pkg_config    = temp_dir/"packages.config"
            pkg_config0   = temp_dir/"packages0.config"
            pkg_config0v  = temp_dir/"packages0v.config"
            pkg_config0nv = temp_dir/"packages0nv.config"
            pkg_config1   = temp_dir/"packages1.config"
            pkg_config1v  = temp_dir/"packages1v.config"
            pkg_config1nv = temp_dir/"packages1nv.config"
            pkg_config2   = temp_dir/"packages2.config"
            pkg_config2v  = temp_dir/"packages2v.config"
            pkg_config2nv = temp_dir/"packages2nv.config"
            with pushd(temp_dir):
                self.choco.export()
                shutil.move(pkg_config, pkg_config0)
                self.choco.export(include_version=True)
                shutil.move(pkg_config, pkg_config0v)
                self.choco.export(include_version=False)
                shutil.move(pkg_config, pkg_config0nv)
            self.choco.export(pkg_config1)
            self.choco.export(pkg_config1v,  include_version=True)
            self.choco.export(pkg_config1nv, include_version=False)
            self.choco.export(output_file_path=pkg_config2)
            self.choco.export(output_file_path=pkg_config2v,  include_version=True)
            self.choco.export(output_file_path=pkg_config2nv, include_version=False)
            self.assertTrue(pkg_config0.exists())
            self.assertTrue(pkg_config0v.exists())
            self.assertTrue(pkg_config0nv.exists())
            self.assertTrue(pkg_config1.exists())
            self.assertTrue(pkg_config1v.exists())
            self.assertTrue(pkg_config1nv.exists())
            self.assertTrue(pkg_config2.exists())
            self.assertTrue(pkg_config2v.exists())
            self.assertTrue(pkg_config2nv.exists())

    def test_install(self):
        """Installs packages using configured sources."""
        with self.lock:
            print()
            package = "py_choco.Test1"
            if package in self.choco.installed(): self.choco.uninstall(package)
            installed_before = self.choco.installed()
            print("INSTALLED BEFORE INSTALL:") ; pprint(installed_before)
            try:
                self.choco.install(package, source=data_dir)
                installed_after = self.choco.installed()
                print("INSTALLED AFTER INSTALL:") ; pprint(installed_after)
            finally:
                if package in self.choco.installed(): self.choco.uninstall(package)

    def test_upgrade(self):
        """Upgrades packages from various sources."""
        with self.lock:
            print()
            package = "py_choco.Test2"
            if package in self.choco.installed(): self.choco.uninstall(package)
            installed_before = self.choco.installed()
            print("INSTALLED BEFORE UPGRADE:") ; pprint(installed_before)
            try:
                self.choco.upgrade(package, source=data_dir)
                installed_after = self.choco.installed()
                print("INSTALLED AFTER UPGRADE:") ; pprint(installed_after)
            finally:
                if package in self.choco.installed(): self.choco.uninstall(package)

    def test_uninstall(self):
        """Uninstalls packages."""
        with self.lock:
            print()
            package = "py_choco.Test3"
            try:
                self.choco.install(package, source=data_dir)
                installed_before = self.choco.installed()
                print("INSTALLED BEFORE UNINSTALL:") ; pprint(installed_before)
                self.choco.uninstall(package)
                installed_after = self.choco.installed()
                print("INSTALLED AFTER UNINSTALL:") ; pprint(installed_after)
            except:
                if package in self.choco.installed(): self.choco.uninstall(package)

    def test_pinned(self):
        """Retrieves a list of packages suppress for upgrades."""
        print()
        pinned = self.choco.pinned()
        self.assertIsInstance(pinned, Dict)
        print("PINNED:") ; pprint(pinned)

    def test_pin_add(self):
        """Suppress upgrades for a package."""
        with self.lock:
            print()
            pinned_saved = self.choco.pinned()
            self.choco.pin_remove(pkg_id="chocolatey")
            pinned_before = self.choco.pinned()
            print("PINNED BEFORE ADD:") ; pprint(pinned_before)
            self.choco.pin_add(pkg_id="chocolatey")
            pinned_after = self.choco.pinned()
            print("PINNED AFTER ADD:") ; pprint(pinned_after)
            self.choco.pin_remove(pkg_id="chocolatey")

    def test_pin_remove(self):
        """Remove suppressing of upgrades for a package."""
        with self.lock:
            print()
            pinned_saved = self.choco.pinned()
            self.choco.pin_add(pkg_id="chocolatey")
            pinned_before = self.choco.pinned()
            print("PINNED BEFORE REMOVE:") ; pprint(pinned_before)
            self.choco.pin_remove(pkg_id="chocolatey")
            pinned_after = self.choco.pinned()
            print("PINNED AFTER REMOVE:") ; pprint(pinned_after)

    def test_pack(self):
        """Packages nuspec, scripts, and other Chocolatey package resources
           into a nupkg file."""
        print()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            with pushd(temp_dir):
                package4 = "py_choco.Test4"
                package5 = "py_choco.Test5"
                self.choco.pack(data_dir/package4/(package4 + ".nuspec"))
                self.choco.pack(nuspec_file_path=data_dir/package5/(package5 + ".nuspec"))
                self.assertTrue(Path(package4 + ".1.0.4.nupkg").exists())
                self.assertTrue(Path(package5 + ".1.0.5.nupkg").exists())

    def test_push(self):
        """Pushes a compiled nupkg to a source."""
        self.assertTrue(1 == 1)

    def test_unpackself(self):
        """Re-installs Chocolatey base files."""
        self.assertTrue(1 == 1)

    def test_new_package(self):
        """Creates template files for creating a new Chocolatey package."""
        self.assertTrue(1 == 1)

    def test_config(self):
        """Retrieve config settings."""
        print()
        config = self.choco.config()
        self.assertIsInstance(config, Dict)
        print("CONFIG:") ; pprint(config)

    def test_config_get(self):
        """Get config value."""
        print()
        print("CONFIG SET:")   ; self.choco.config_set(name="AAA", value="TRALALA")
        print("CONFIG GET:")   ; pprint(self.choco.config_get(name="AAA"))
        print("CONFIG SET:")   ; self.choco.config_set(name="AAA", value="BLABLAB")
        print("CONFIG GET:")   ; pprint(self.choco.config_get(name="AAA"))
        print("CONFIG UNSET:") ; self.choco.config_unset(name="AAA")
        print("CONFIG: GET")   ; pprint(self.choco.config_get(name="AAA"))
        print("CONFIG: UNSET") ; self.choco.config_unset(name="AAA")
        print("CONFIG: UNSET") ; self.choco.config_unset(name="AAA")

    def test_config_set(self):
        """Set config value."""
        self.assertTrue(1 == 1)

    def test_config_unset(self):
        """Unset config."""
        self.assertTrue(1 == 1)

    def test_sources(self):
        """Retrieve default sources."""
        print()
        sources = self.choco.sources()
        self.assertIsInstance(sources, Dict)
        print("SOURCES:") ; pprint(sources)

    def test_source_enable(self):
        """Enable source."""
        self.assertTrue(1 == 1)

    def test_source_disable(self):
        """Disable source."""
        self.assertTrue(1 == 1)

    def test_source_remove(self):
        """Remove source."""
        self.assertTrue(1 == 1)

    def test_features(self):
        """Retrieve features."""
        print()
        features = self.choco.features()
        self.assertIsInstance(features, Dict)
        print("FEATURES:") ; pprint(features)

    def test_feature_get(self):
        """Get feature value."""
        self.assertTrue(1 == 1)

    def test_feature_enable(self):
        """Enable feature."""
        self.assertTrue(1 == 1)

    def test_feature_disable(self):
        """Disable feature."""
        self.assertTrue(1 == 1)

    def test_apikeys(self):
        """Retrieve the list of API keys."""
        print()
        apikeys = self.choco.apikeys()
        self.assertIsInstance(apikeys, List)
        print("APIKEYS:") ; pprint(apikeys)

    def test_apikey_add(self):
        """Add API key for source."""
        self.assertTrue(1 == 1)

    def test_apikey_remove(self):
        """Remove API key for source."""
        self.assertTrue(1 == 1)

    def test_templates(self):
        """Retrieve templates."""
        print()
        templates = self.choco.templates()
        self.assertIsInstance(templates, Dict)
        print("TEMPLATES:") ; pprint(templates)

    def test_template_info(self):
        """Retrieve template info."""
        self.assertTrue(1 == 1)

    def test_cache_list(self):
        """Displays information about the local HTTP caches used to store
           queries."""
        self.choco.cache_list()

    def test_cache_remove(self):
        """Remove the local HTTP caches used to store queries."""
        self.choco.cache_remove(expired=True)
        self.choco.cache_remove()
