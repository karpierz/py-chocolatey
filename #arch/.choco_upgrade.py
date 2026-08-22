from chocolatey import Chocolatey

Chocolatey.setup(upgrade=True)
choco = Chocolatey()

print("choco version:", choco.version)

