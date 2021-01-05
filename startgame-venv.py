#! /usr/bin/env python3

import venv
import os
import subprocess

# determine user data directory to store the virtual env files
if os.name == "posix":
    venv_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share")) + "/bouldercaves/venv"
    symlink = True
    executable = venv_dir + "/bin/python3"
elif os.name == "nt":
    venv_dir = os.getenv("APPDATA") + "/bouldercaves/venv"
    symlink = False
    executable = venv_dir + "/Scripts/python.exe"
else:
    venv_dir = os.expanduser("~/bouldercaves/venv")
    symlink = True
    executable = venv_dir + "/bin/python3"

print("Creating virtual python environment in: ", venv_dir)

builder = venv.EnvBuilder(system_site_packages=False, symlinks=symlink, upgrade=True, with_pip=True)
builder.create(venv_dir)

print("Installing game dependencies...")
subprocess.check_call([executable, "-m", "pip", "install", "-r", "requirements.txt"])

print("\n\n\n\n\n\n\n\nBoulderCaves can be played in two ways:\n")
print("  1)  RETRO style (small screen, original colors, original sounds)")
print("  2)  REMAKE style (large screen, modern colors, synthesized sounds)")
print("\n(there are even more possibilities if you use the command-line arguments yourself)")
choice = input("\nWhich style do you want to play (1/2)? ").strip()
print()

if choice == "1":
    subprocess.call([executable, "-m", "bouldercaves", "--authentic"])
elif choice == "2":
    subprocess.call([executable, "-m", "bouldercaves", "--synth"])
else:
    print("Invalid choice.")
