from pathlib import Path
from functools import partial
import logging
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

from rich import print
from rich.pretty import pprint
pprint = partial(pprint, max_length=500)

from chocolatey import Chocolatey
choco = Chocolatey()

input("Press a key...")
