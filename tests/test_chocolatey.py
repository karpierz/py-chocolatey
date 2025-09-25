# Copyright (c) 2022 Adam Karpierz
# SPDX-License-Identifier: Zlib

import unittest
import os
import shutil
import tempfile
import threading
from functools import partial
from pathlib import Path

from rich.pretty import pprint
pprint = partial(pprint, max_length=500)
from utlx import Path as EPath

import chocolatey
from chocolatey import Chocolatey

here = Path(__file__).resolve().parent
data_dir = here/"data"


def setUpModule():
    Chocolatey.setup()


class ChocolateyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.choco = Chocolatey()
        cls.lock = threading.Lock()

    def setUp(self):
        self.lock.acquire()

    def tearDown(self):
        self.lock.release()

    ### High-level API ###

    def test_version(self):
        """Gets the Chocolatey version."""
        version = self.choco.version
        self.assertIsInstance(version, str)
        print(flush=True)
        print("CHOCO VERSION:", version)

    def test_version_info(self):
        """Gets the Chocolatey version info."""
        version_info = self.choco.version_info
        self.assertIsInstance(version_info, chocolatey.version_info)
        self.assertIsInstance(version_info.major,  int)
        self.assertIsInstance(version_info.minor,  int)
        self.assertIsInstance(version_info.micro,  int)
        self.assertIsInstance(version_info.serial, int)

    def test_help(self):
        """Gets the help information for choco and choco commands."""
        help_str = self.choco.help()
        self.assertIsInstance(help_str, str)
        help_str = self.choco.help(command="search")
        self.assertIsInstance(help_str, str)

    def test_license(self):
        """Gets the information about the current Chocolatey CLI license [v2.5.0+]."""
        license_str = self.choco.license()
        self.assertIsInstance(license_str, str)

    def test_support(self):
        """Provides support information [v2.5.0+]."""
        support_str = self.choco.support()
        self.assertIsInstance(support_str, str)

    def test_installed(self):
        """Retrieves a list of locally installed packages."""
        installed = self.choco.installed()
        self.assertIsInstance(installed, dict)
        for pkg_id, package in installed.items():
            self.assertIsInstance(pkg_id, str)
            self.assertIsInstance(package, chocolatey.Package)
        pkg_id = "chocolatey"
        self.assertIsInstance(installed[pkg_id], chocolatey.Package)

    def test_outdated(self):
        """Retrieves information about packages that are outdated."""
        outdated = self.choco.outdated()
        self.assertIsInstance(outdated, dict)
        for pkg_id, package in outdated.items():
            self.assertIsInstance(pkg_id, str)
            self.assertIsInstance(package, chocolatey.PackageOutdated)

    def test_search(self):
        """Searches remote packages."""
        pkg_id = "chocolatey"
        # exact
        found = self.choco.search(pkg_id, exact=True)
        self.assertIsInstance(found, dict)
        self.assertIsInstance(found[pkg_id], chocolatey.Package)
        found = self.choco.search(pkg_id, exact=True, all_versions=True)
        self.assertIsInstance(found, dict)
        self.assertIsInstance(found[pkg_id], list)
        self.assertIsInstance(found[pkg_id][0], chocolatey.Package)
        # as filter
        found = self.choco.search(pkg_id, by_id_only=True)
        self.assertIsInstance(found, dict)
        self.assertIsInstance(list(found.values())[0], chocolatey.Package)
        found = self.choco.search(pkg_id, by_id_only=True, all_versions=True)
        self.assertIsInstance(found, dict)
        self.assertIsInstance(list(found.values())[0], list)
        self.assertIsInstance(list(found.values())[0][0], chocolatey.Package)

    def test_info(self):
        """Retrieves package information."""
        pkg_id = "chocolatey"
        pkg_info = self.choco.info(pkg_id=pkg_id)
        self.assertIsInstance(pkg_info, chocolatey.PackageInfo)

    def test_export(self):
        """Exports list of currently installed packages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = EPath(temp_dir)
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
            with temp_dir.pushd():
                self.choco.export()
                shutil.move(pkg_config, pkg_config0)
                self.choco.export(include_version_numbers=True)
                shutil.move(pkg_config, pkg_config0v)
                self.choco.export(include_version_numbers=False)
                shutil.move(pkg_config, pkg_config0nv)
            self.choco.export(pkg_config1)
            self.choco.export(pkg_config1v,  include_version_numbers=True)
            self.choco.export(pkg_config1nv, include_version_numbers=False)
            self.choco.export(output_file_path=pkg_config2)
            self.choco.export(output_file_path=pkg_config2v,  include_version_numbers=True)
            self.choco.export(output_file_path=pkg_config2nv, include_version_numbers=False)
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
        print(flush=True)
        pkg_id = "py-chocolatey.Test1"
        if pkg_id in self.choco.installed(): self.choco.uninstall(pkg_id)
        installed_before = self.choco.installed()
        try:
            self.choco.install(pkg_id, source=data_dir)
            installed_after = self.choco.installed()
            diff_keys = set(installed_after) - set(installed_before)
            self.assertEqual(diff_keys, set([pkg_id]))
        finally:
            if pkg_id in self.choco.installed(): self.choco.uninstall(pkg_id)
        with self.assertRaises(TypeError):
            self.choco.install(source=data_dir)

    def test_upgrade(self):
        """Upgrades packages from various sources."""
        print(flush=True)
        pkg_id = "py-chocolatey.Test2"
        if pkg_id in self.choco.installed(): self.choco.uninstall(pkg_id)
        installed_before = self.choco.installed()
        try:
            self.choco.upgrade(pkg_id, source=data_dir)
            installed_after = self.choco.installed()
            diff_keys = set(installed_after) - set(installed_before)
            self.assertEqual(diff_keys, set([pkg_id]))
        finally:
            if pkg_id in self.choco.installed(): self.choco.uninstall(pkg_id)
        with self.assertRaises(TypeError):
            self.choco.upgrade(source=data_dir)

    def test_uninstall(self):
        """Uninstalls packages."""
        print(flush=True)
        pkg_id = "py-chocolatey.Test3"
        try:
            self.choco.install(pkg_id, source=data_dir)
            installed_before = self.choco.installed()
            self.choco.uninstall(pkg_id)
            installed_after = self.choco.installed()
            diff_keys = set(installed_before) - set(installed_after)
            self.assertEqual(diff_keys, set([pkg_id]))
        except:  # pragma: no cover
            if pkg_id in self.choco.installed(): self.choco.uninstall(pkg_id)
        with self.assertRaises(TypeError):
            self.choco.uninstall()

    def test_pinned(self):
        """Retrieves a list of packages suppress for upgrades."""
        pinned = self.choco.pinned()
        self.assertIsInstance(pinned, dict)
        for pkg_id, package in pinned.items():
            self.assertIsInstance(pkg_id, str)
            self.assertIsInstance(package, chocolatey.Package)

    def test_pin_add(self):
        """Suppress upgrades for a package."""
        print(flush=True)
        pkg_id = "chocolatey"
        pinned_saved = self.choco.pinned()
        self.choco.pin_remove(pkg_id=pkg_id)
        pinned_before = self.choco.pinned()
        self.choco.pin_add(pkg_id=pkg_id)
        pinned_after = self.choco.pinned()
        self.assertIsInstance(pinned_before, dict)
        self.assertIsInstance(pinned_after, dict)
        diff_keys = set(pinned_after) - set(pinned_before)
        self.assertEqual(diff_keys, set([pkg_id]))
        self.choco.pin_remove(pkg_id=pkg_id)

    def test_pin_remove(self):
        """Remove suppressing of upgrades for a package."""
        print(flush=True)
        pkg_id = "chocolatey"
        pinned_saved = self.choco.pinned()
        self.choco.pin_add(pkg_id=pkg_id)
        pinned_before = self.choco.pinned()
        self.choco.pin_remove(pkg_id=pkg_id)
        pinned_after = self.choco.pinned()
        self.assertIsInstance(pinned_before, dict)
        self.assertIsInstance(pinned_after, dict)
        diff_keys = set(pinned_before) - set(pinned_after)
        self.assertEqual(diff_keys, set([pkg_id]))

    def test_pack(self):
        """Packages nuspec, scripts, and other Chocolatey package resources
        into a nupkg file."""
        print(flush=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = EPath(temp_dir)
            with temp_dir.pushd():
                pkg4_id = "py-chocolatey.Test4"
                pkg5_id = "py-chocolatey.Test5"
                self.choco.pack(data_dir/pkg4_id/(pkg4_id + ".nuspec"))
                self.choco.pack(nuspec_file_path=data_dir/pkg5_id/(pkg5_id + ".nuspec"))
                self.assertTrue(Path(pkg4_id + ".1.0.4.nupkg").exists())
                self.assertTrue(Path(pkg5_id + ".1.0.5.nupkg").exists())

    def test_push(self):
        """Pushes a compiled nupkg to a source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = EPath(temp_dir)
            with temp_dir.pushd():
                pkg_id = "py-chocolatey.Test0"
                self.choco.pack(nuspec_file_path=data_dir/pkg_id/(pkg_id + ".nuspec"))
                self.assertTrue(Path(pkg_id + ".1.0.0.nupkg").exists())

    def test_new_package(self):
        """Creates template files for creating a new Chocolatey package."""
        print(flush=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            pkg_id = "py-chocolatey.Test0"
            self.choco.new_package(pkg_id=pkg_id,  auto=True, version="1.2.0",
                                   outputdirectory=temp_dir,
                                   properties = dict(maintainername="This guy"))
            self.assertTrue((temp_dir/pkg_id).is_dir())
            self.assertTrue((temp_dir/pkg_id/(pkg_id + ".nuspec")).is_file())
            self.assertTrue((temp_dir/pkg_id/"_TODO.txt").is_file())
            self.assertTrue((temp_dir/pkg_id/"ReadMe.md").is_file())
            self.assertTrue((temp_dir/pkg_id/"tools").is_dir())
            self.assertTrue((temp_dir/pkg_id/"tools/chocolateybeforemodify.ps1").is_file())
            self.assertTrue((temp_dir/pkg_id/"tools/chocolateyinstall.ps1").is_file())
            self.assertTrue((temp_dir/pkg_id/"tools/chocolateyuninstall.ps1").is_file())
            self.assertTrue((temp_dir/pkg_id/"tools/LICENSE.txt").is_file())
            self.assertTrue((temp_dir/pkg_id/"tools/VERIFICATION.txt").is_file())

    def test_config(self):
        """Retrieve config settings."""
        configs = self.choco.config()
        self.assertIsInstance(configs, dict)
        for cfg_id, config in configs.items():
            self.assertIsInstance(cfg_id, str)
            self.assertIsInstance(config, chocolatey.Config)

    def test_config_get(self):
        """Get config value."""
        self.choco.config_unset(name="TEST1")
        self.choco.config_set(name="TEST1", value="TEST1_VALUE1")
        value = self.choco.config_get(name="TEST1")
        self.assertEqual(value, "TEST1_VALUE1")
        self.choco.config_set(name="TEST1", value="TEST1_VALUE2")
        value = self.choco.config_get(name="TEST1")
        self.assertEqual(value, "TEST1_VALUE2")
        self.choco.config_unset(name="TEST1")

    def test_config_set(self):
        """Set config value."""
        self.choco.config_unset(name="TEST2")
        self.choco.config_set(name="TEST2", value="TEST2_VALUE1")
        value = self.choco.config_get(name="TEST2")
        self.assertEqual(value, "TEST2_VALUE1")
        self.choco.config_set(name="TEST2", value="TEST2_VALUE2")
        value = self.choco.config_get(name="TEST2")
        self.assertEqual(value, "TEST2_VALUE2")
        self.choco.config_set(name="TEST2", value=True)
        value = self.choco.config_get(name="TEST2")
        self.assertTrue(value)
        self.choco.config_set(name="TEST2", value=None)
        value = self.choco.config_get(name="TEST2")
        self.assertIs(value, "")
        self.choco.config_set(name="TEST2", value="")
        value = self.choco.config_get(name="TEST2")
        self.assertIs(value, "")
        self.choco.config_unset(name="TEST2")

    def test_config_unset(self):
        """Unset config."""
        self.choco.config_unset(name="TEST3")
        self.choco.config_set(name="TEST3", value="TEST3_VALUE1")
        value = self.choco.config_get(name="TEST3")
        self.assertEqual(value, "TEST3_VALUE1")
        self.choco.config_unset(name="TEST3")
        #with self.assertRaises(Exception):
        value = self.choco.config_get(name="TEST3")

    def test_sources(self):
        """Retrieve default sources."""
        sources = self.choco.sources()
        self.assertIsInstance(sources, dict)
        for name, source in sources.items():
            self.assertIsInstance(source, chocolatey.Source)

    def test_source_add(self):
        """Add source."""
        source_name = "_test_source"
        sources_before = self.choco.sources()
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            sources_after = self.choco.sources()
            diff_keys = set(sources_after) - set(sources_before)
            self.assertEqual(diff_keys, set([source_name]))
        finally:
            self.choco.source_remove(name=source_name)

    def test_source_enable(self):
        """Enable source."""
        source_name = "_test_source"
        sources_before = self.choco.sources()
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            sources_after = self.choco.sources()
            diff_keys = set(sources_after) - set(sources_before)
            self.assertEqual(diff_keys, set([source_name]))
            self.choco.source_enable(name=source_name)
        finally:
            self.choco.source_remove(name=source_name)

    def test_source_disable(self):
        """Disable source."""
        source_name = "_test_source"
        sources_before = self.choco.sources()
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            sources_after = self.choco.sources()
            diff_keys = set(sources_after) - set(sources_before)
            self.assertEqual(diff_keys, set([source_name]))
            self.choco.source_disable(name=source_name)
        finally:
            self.choco.source_remove(name=source_name)

    def test_source_remove(self):
        """Remove source."""
        source_name = "_test_source"
        sources_before = self.choco.sources()
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            sources_after = self.choco.sources()
            diff_keys = set(sources_after) - set(sources_before)
            self.assertEqual(diff_keys, set([source_name]))
        finally:
            self.choco.source_remove(name=source_name)
        sources_after = self.choco.sources()
        self.assertEqual(set(sources_after), set(sources_before))

    def test_features(self):
        """Retrieve features."""
        features = self.choco.features()
        self.assertIsInstance(features, dict)
        for name, feature in features.items():
            self.assertIsInstance(feature, chocolatey.Feature)

    def test_feature_get(self):
        """Get feature value."""
        feature_name = "autoUninstaller"
        feature = self.choco.feature_get(name=feature_name)
        self.assertIsInstance(feature, bool)

    def test_feature_enable(self):
        """Enable feature."""
        feature_name = "autoUninstaller"
        feature_org = self.choco.feature_get(name=feature_name)
        self.assertIsInstance(feature_org, bool)
        try:
            self.choco.feature_disable(name=feature_name)
            feature = self.choco.feature_get(name=feature_name)
            self.assertIsInstance(feature, bool)
            self.assertFalse(feature)
            # enable feature
            self.choco.feature_enable(name=feature_name)
            feature = self.choco.feature_get(name=feature_name)
            self.assertIsInstance(feature, bool)
            self.assertTrue(feature)
        finally:
            (self.choco.feature_enable
             if feature_org else
             self.choco.feature_disable)(name=feature_name)

    def test_feature_disable(self):
        """Disable feature."""
        feature_name = "autoUninstaller"
        feature_org = self.choco.feature_get(name=feature_name)
        self.assertIsInstance(feature_org, bool)
        try:
            self.choco.feature_enable(name=feature_name)
            feature = self.choco.feature_get(name=feature_name)
            self.assertIsInstance(feature, bool)
            self.assertTrue(feature)
            # disable feature
            self.choco.feature_disable(name=feature_name)
            feature = self.choco.feature_get(name=feature_name)
            self.assertIsInstance(feature, bool)
            self.assertFalse(feature)
        finally:
            (self.choco.feature_enable
             if feature_org else
             self.choco.feature_disable)(name=feature_name)

    def test_apikeys(self):
        """Retrieve the list of API keys."""
        source_name = "_test_source"
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            api_key = "123-123123-123"
            self.choco.apikey_add(source=data_dir, api_key=api_key)
            try:
                apikeys = self.choco.apikeys()
                self.assertIsInstance(apikeys, list)
                for apikey in apikeys:
                    self.assertIsInstance(apikey, chocolatey.ApiKey)
            finally:
                self.choco.apikey_remove(source=data_dir)
        finally:
            self.choco.source_remove(name=source_name)

    def test_apikey_add(self):
        """Add API key for source."""
        source_name = "_test_source"
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            api_key = "123-123123-123"
            apikeys_before = self.choco.apikeys()
            self.choco.apikey_add(source=data_dir, api_key=api_key)
            try:
                apikeys_after = self.choco.apikeys()
                diff_lists = [item for item in apikeys_after
                              if item not in apikeys_before]
                self.assertTrue(bool(diff_lists))
                self.assertEqual(diff_lists[0].source, str(data_dir))
                self.assertEqual(diff_lists[0].info, "(Authenticated)")
            finally:
                self.choco.apikey_remove(source=data_dir)
        finally:
            self.choco.source_remove(name=source_name)

    def test_apikey_remove(self):
        """Remove API key for source."""
        apikeys_before = self.choco.apikeys()
        #self.choco.apikey_remove(source="")
        apikeys_after = self.choco.apikeys()

        source_name = "_test_source"
        self.choco.source_add(name=source_name, source=data_dir)
        try:
            api_key = "123-123123-123"
            self.choco.apikey_add(source=data_dir, api_key=api_key)
            apikeys_before = self.choco.apikeys()
            self.choco.apikey_remove(source=data_dir)
            apikeys_after = self.choco.apikeys()
            diff_lists = [item for item in apikeys_before
                          if item not in apikeys_after]
            self.assertTrue(bool(diff_lists))
            self.assertEqual(diff_lists[0].source, str(data_dir))
            self.assertEqual(diff_lists[0].info, "(Authenticated)")
        finally:
            self.choco.source_remove(name=source_name)

    def test_templates(self):
        """Retrieve templates."""
        templates = self.choco.templates()
        self.assertIsInstance(templates, dict)
        for name, template in templates.items():
            self.assertIsInstance(name, str)
            self.assertIsInstance(template, chocolatey.Template)

    def test_template_info(self):
        """Retrieve template info."""
        #template_name = "py-chocolatey.test_template"
        template_name = "built-in"
        template = self.choco.template_info(name=template_name)
        self.assertIsInstance(template, chocolatey.Template)

    def test_cache_list(self):
        """Displays information about the local HTTP caches used to store
        queries."""
        print(flush=True)
        self.choco.cache_list()

    def test_cache_remove(self):
        """Remove the local HTTP caches used to store queries."""
        print(flush=True)
        self.choco.cache_remove(expired=True)
        self.choco.cache_remove()

    def test_miscs(self):
        """Test internal utilities."""
        # _bool2str
        from chocolatey._chocolatey import _bool2str
        self.assertEqual(_bool2str("xyz", True), "true")
        self.assertEqual(_bool2str("xyz", False), "false")
        self.assertEqual(_bool2str("xyz", "abc"), "abc")
        self.assertEqual(_bool2str("xyz", 1), 1)
        self.assertEqual(_bool2str("xyz", 123), 123)
        # _str2bool
        from chocolatey._chocolatey import _str2bool
        self.assertEqual(_str2bool("xyz", "true", with_check=False), True)
        self.assertEqual(_str2bool("xyz", "false", with_check=False), False)
        self.assertEqual(_str2bool("xyz", "abc", with_check=False), "abc")
        self.assertEqual(_str2bool("xyz", True, with_check=False), True)
        self.assertEqual(_str2bool("xyz", False, with_check=False), False)
        self.assertEqual(_str2bool("xyz", 1, with_check=False), 1)
        self.assertEqual(_str2bool("xyz", 123, with_check=False), 123)
        self.assertEqual(_str2bool("xyz", "true"), True)
        self.assertEqual(_str2bool("xyz", "false"), False)
        with self.assertRaises(Chocolatey.ValueError):
            _str2bool("xyz", "abc")
        self.assertEqual(_str2bool("xyz", True), True)
        self.assertEqual(_str2bool("xyz", False), False)
        self.assertEqual(_str2bool("xyz", 1), 1)
        self.assertEqual(_str2bool("xyz", 123), 123)
        # _str2int
        from chocolatey._chocolatey import _str2int
        self.assertEqual(_str2int("xyz", "123", with_check=False), 123)
        self.assertEqual(_str2int("xyz", "abc", with_check=False), "abc")
        self.assertEqual(_str2int("xyz", True, with_check=False), True)
        self.assertEqual(_str2int("xyz", False, with_check=False), False)
        self.assertEqual(_str2int("xyz", 1, with_check=False), 1)
        self.assertEqual(_str2int("xyz", 123, with_check=False), 123)
        self.assertEqual(_str2int("xyz", "123"), 123)
        with self.assertRaises(Chocolatey.ValueError):
            _str2int("xyz", "abc")
        self.assertEqual(_str2int("xyz", True), True)
        self.assertEqual(_str2int("xyz", False), False)
        self.assertEqual(_str2int("xyz", 1), 1)
        self.assertEqual(_str2int("xyz", 123), 123)
        # _str2none
        from chocolatey._chocolatey import _str2none
        self.assertEqual(_str2none("xyz", ""), None)
        self.assertEqual(_str2none("xyz", None), None)
        self.assertEqual(_str2none("xyz", "abc"), "abc")
        self.assertEqual(_str2none("xyz", True), True)
        self.assertEqual(_str2none("xyz", False), False)
        self.assertEqual(_str2none("xyz", 1), 1)
        self.assertEqual(_str2none("xyz", 123), 123)
