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
from chocolatey import ChocolateyCmd

here = Path(__file__).resolve().parent
data_dir = here/"data"


class ChocolateyCmdCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.choco_cmd = ChocolateyCmd()
        cls.lock = threading.Lock()

    ## Low-level Chocolatey API ##

    def test_choco(self):
        self.assertTrue(1 == 1)

    def test_help(self):
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
        self.assertTrue(1 == 1)

    def test_template(self):
        self.assertIs(self.choco_cmd.__class__.template,
                      self.choco_cmd.__class__.templates)

    def test_unpackself(self):
        self.assertTrue(1 == 1)
