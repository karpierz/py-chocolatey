from pathlib import Path
import logging
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

here = Path(__file__).resolve().parent

from chocolatey import Chocolatey
choco = Chocolatey()

print("choco version:", choco.version)

(here/"help.txt").open("w", newline="").write(choco.help(command="help"))
for command in ("apikey", "cache", "config", "export", "feature", "info",
                "install", "list", "new", "outdated", "pack", "pin", "push",
                "search", "source", "template", "uninstall", "unpackself",
                "upgrade"):
    fpath = here/f"help_{command}.txt"
    fpath.open("w", newline="").write(choco.help(command=command))
