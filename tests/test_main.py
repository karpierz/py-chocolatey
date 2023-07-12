# Copyright (c) 2022-2023 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/licenses/Zlib

import unittest

import chocolatey
from chocolatey import Chocolatey


class MainTestCase(unittest.TestCase):

    def setUp(self):
        self.choco = Chocolatey()
