#! /usr/bin/env python3

from bouldercaves import game

print("\nBoulderCaves can be played in two ways:\n")
print("  1)  RETRO style (small screen, original colors, original sounds)")
print("  2)  REMAKE style (large screen, modern colors, synthesized sounds)")
print("\n(there are even more possibilities if you use the command-line arguments yourself)")
choice = input("\nWhich style do you want to play (1/2)? ").strip()
print()

if choice == "1":
    game.start(["--authentic"])
elif choice == "2":
    game.start(["--synth"])
else:
    print("Invalid choice.")
