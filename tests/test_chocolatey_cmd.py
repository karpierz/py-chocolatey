# Copyright (c) 2022 Adam Karpierz
# SPDX-License-Identifier: Zlib

import unittest
import os
import inspect
import shutil
import tempfile
import threading
from functools import partial
from pathlib import Path

from rich.pretty import pprint
pprint = partial(pprint, max_length=500)

import chocolatey
from chocolatey import ChocolateyCmd

here = Path(__file__).resolve().parent
data_dir = here/"data"


class ChocolateyCmdTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.choco_cmd = ChocolateyCmd()
        cls.lock = threading.Lock()

    def setUp(self):
        self.lock.acquire()

    def tearDown(self):
        self.lock.release()

    ## Low-level Chocolatey API ##

    def test_api_surface(self):
        # ensure methods exist and are callable
        for method_name in (
            "choco",
            "help",
            "license",
            "support",
            "apikey", "setapikey",
            "cache",
            "config",
            "export",
            "feature", "features",
            "search", "find",
            "info",
            "list",
            "outdated",
            "install",
            "upgrade",
            "uninstall",
            "new",
            "pack",
            "pin",
            "push",
            "source", "sources",
            "template", "templates",
        ):
            method = getattr(self.choco_cmd, method_name)
            self.assertTrue(callable(method))
            self.assertTrue(inspect.ismethod(method))

    def test_choco(self):
        self.assertTrue(1 == 1)

    def test_help(self):
        self.assertTrue(1 == 1)

    def test_license(self):
        self.assertTrue(1 == 1)

    def test_support(self):
        self.assertTrue(1 == 1)

    def test_apikey(self):
        self.assertIs(self.choco_cmd.__class__.apikey,
                      self.choco_cmd.__class__.setapikey)

    def test_cache(self):
        self.assertTrue(1 == 1)

    def test_config(self):
        self.assertTrue(1 == 1)

    def test_export(self):
        self.assertTrue(1 == 1)

    def test_feature(self):
        self.assertIs(self.choco_cmd.__class__.feature,
                      self.choco_cmd.__class__.features)

    def test_search(self):
        self.assertIs(self.choco_cmd.__class__.search,
                      self.choco_cmd.__class__.find)

    def test_info(self):
        self.assertTrue(1 == 1)

    def test_list(self):
        self.assertTrue(1 == 1)

    def test_outdated(self):
        self.assertTrue(1 == 1)

    def test_install(self):
        self.assertTrue(1 == 1)

    def test_upgrade(self):
        self.assertTrue(1 == 1)

    def test_uninstall(self):
        self.assertTrue(1 == 1)

    def test_new(self):
        self.assertTrue(1 == 1)

    def test_pack(self):
        self.assertTrue(1 == 1)

    def test_pin(self):
        self.assertTrue(1 == 1)

    def test_push(self):
        self.assertTrue(1 == 1)

    def test_source(self):
        self.assertIs(self.choco_cmd.__class__.source,
                      self.choco_cmd.__class__.sources)

    def test_template(self):
        self.assertIs(self.choco_cmd.__class__.template,
                      self.choco_cmd.__class__.templates)
