from pathlib import Path
import logging
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

here = Path(__file__).resolve().parent
docs_dir = here.parent/"docs"/".org"

choco_commands = (  # "support",
    "license", "apikey", "cache", "config", "export", "feature",
    "info", "install", "list", "new", "outdated", "pack", "pin", "push",
    "rule", "search", "source", "template", "uninstall", "upgrade",
)

from chocolatey import Chocolatey
choco = Chocolatey()

print("choco version:", choco.version)

fpath = docs_dir/"help.txt"
fpath.open("w", newline="").write(choco.help(command="help"))
for command in choco_commands:
    fpath = docs_dir/f"help_{command}.txt"
    fpath.open("w", newline="").write(choco.help(command=command))
