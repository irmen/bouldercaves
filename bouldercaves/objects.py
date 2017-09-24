"""
Boulder Caves - a Boulder Dash (tm) clone.

This module contains the objects definitions.

Written by Irmen de Jong (irmen@razorvine.net)
License: GNU GPL 3.0, see LICENSE
"""

from enum import Enum
from typing import Callable


class GameObject:
    def __init__(self, name: str, rounded: bool, explodable: bool, consumable: bool,
                 spritex: int, spritey: int, sframes: int=0, sfps: int=0,
                 anim_end_callback: Callable=None) -> None:
        self.name = name
        self.rounded = rounded
        self.explodable = explodable
        self.consumable = consumable
        self.spritex = spritex
        self.spritey = spritey
        self._tile = spritex + 8 * spritey
        self.sframes = sframes
        self.sfps = sfps
        self.anim_end_callback = anim_end_callback

    def __repr__(self):
        return "<{cls} {name} (#{tile}) at {oid}>".format(cls=self.__class__.__name__, name=self.name, tile=self._tile, oid=hex(id(self)))

    def tile(self, animframe: int = 0) -> int:
        if self.sframes:
            return self._tile + animframe % self.sframes
        return self._tile


class Direction(Enum):
    NOWHERE = ""
    LEFT = "l"
    RIGHT = "r"
    UP = "u"
    DOWN = "d"
    LEFTUP = "lu"
    RIGHTUP = "ru"
    LEFTDOWN = "ld"
    RIGHTDOWN = "rd"

    def rotate90left(self: 'Direction') -> 'Direction':
        return {
            Direction.NOWHERE: Direction.NOWHERE,
            Direction.UP: Direction.LEFT,
            Direction.LEFT: Direction.DOWN,
            Direction.DOWN: Direction.RIGHT,
            Direction.RIGHT: Direction.UP,
            Direction.LEFTUP: Direction.LEFTDOWN,
            Direction.LEFTDOWN: Direction.RIGHTDOWN,
            Direction.RIGHTDOWN: Direction.RIGHTUP,
            Direction.RIGHTUP: Direction.LEFTUP
        }[self]

    def rotate90right(self: 'Direction') -> 'Direction':
        return {
            Direction.NOWHERE: Direction.NOWHERE,
            Direction.UP: Direction.RIGHT,
            Direction.RIGHT: Direction.DOWN,
            Direction.DOWN: Direction.LEFT,
            Direction.LEFT: Direction.UP,
            Direction.LEFTUP: Direction.RIGHTUP,
            Direction.RIGHTUP: Direction.RIGHTDOWN,
            Direction.RIGHTDOWN: Direction.LEFTDOWN,
            Direction.LEFTDOWN: Direction.LEFTUP
        }[self]


# row 0
g = GameObject
EMPTY = g("EMPTY", False, False, True, 0, 0)
BOULDER = g("BOULDER", True, False, True, 1, 0)
DIRT = g("DIRT", False, False, True, 2, 0)
DIRT2 = g("DIRT2", False, False, True, 3, 0)
STEEL = g("STEEL", False, False, False, 4, 0)
BRICK = g("BRICK", True, False, True, 5, 0)
BLADDERSPENDER = g("BLADDERSPENDER", False, False, False, 6, 0)
VOODOO = g("VOODOO", True, True, True, 7, 0)
# row 1
SWEET = g("SWEET", True, False, True, 0, 1)
GRAVESTONE = g("GRAVESTONE", True, False, False, 1, 1)
TRAPPEDDIAMOND = g("TRAPPEDDIAMOND", False, False, False, 2, 1)
DIAMONDKEY = g("DIAMONDKEY", True, True, True, 3, 1)
BITERSWITCH1 = g("BITERSWITCH1", False, False, True, 4, 1)
BITERSWITCH2 = g("BITERSWITCH2", False, False, True, 5, 1)
BITERSWITCH3 = g("BITERSWITCH3", False, False, True, 6, 1)
BITERSWITCH4 = g("BITERSWITCH4", False, False, True, 7, 1)
# row 2
CLOCK = g("CLOCK", True, False, True, 0, 2)
CHASINGBOULDER = g("CHASINGBOULDER", True, False, True, 1, 2)
CREATURESWITCH = g("CREATURESWITCH", False, False, False, 2, 2)
CREATURESWITCHON = g("CREATURESWITCHON", False, False, False, 3, 2)
ACID = g("ACID", False, False, False, 4, 2)
SOKOBANBOX = g("SOKOBANBOX", False, False, False, 5, 2)
INBOXBLINKING = g("INBOXBLINKING", False, False, False, 6, 2, sframes=2, sfps=4)
OUTBOXBLINKING = g("OUTBOXBLINKING", False, False, False, 6, 2, sframes=2, sfps=4)
OUTBOXCLOSED = g("OUTBOXCLOSED", False, False, False, 6, 2)
OUTBOXHIDDEN = g("OUTBOXHIDDEN", False, False, False, 6, 2)
OUTBOXHIDDENOPEN = g("OUTBOXHIDDENOPEN", False, False, False, 6, 2)
# row 3
STEELWALLBIRTH = g("STEELWALLBIRTH", False, False, False, 0, 3, sframes=4, sfps=10)
CLOCKBIRTH = g("CLOCKBIRTH", False, False, False, 4, 3, sframes=4, sfps=10)
# row 4
ROCKFORDBIRTH = g("ROCKFORDBIRTH", False, False, False, 0, 4, sframes=4, sfps=10)
ROCKFORD = g("ROCKFORD", False, True, True, 3, 4)  # standing still
BOULDERBIRTH = g("BOULDERBIRTH", False, False, False, 4, 4, sframes=4, sfps=10)
# row 5
HEXPANDINGWALL = g("HEXPANDINGWALL", False, False, True, 0, 5)
VEXPANDINGWALL = g("VEXPANDINGWALL", False, False, True, 1, 5)
ROCKFORD.bomb = g("ROCKFORD.BOMB", False, True, True, 2, 5)
EXPLOSION = g("EXPLOSION", False, False, False, 3, 5, sframes=5, sfps=10)
# row 6
BOMB = g("BOMB", True, False, True, 0, 6)
IGNITEDBOMB = g("IGNITEDBOMB", True, False, True, 1, 6, sframes=7, sfps=10)
# row 7
DIAMONDBIRTH = g("DIAMONDBIRTH", False, False, False, 0, 7, sframes=5, sfps=10)
TELEPORTER = g("TELEPORTER", False, False, False, 5, 7)
HAMMER = g("HAMMER", True, False, False, 6, 7)
POT = g("POT", True, False, False, 7, 7)
# row 8
DOOR1 = g("DOOR1", False, False, False, 0, 8)
DOOR2 = g("DOOR2", False, False, False, 1, 8)
DOOR3 = g("DOOR3", False, False, False, 2, 8)
KEY1 = g("KEY1", False, False, False, 3, 8)
KEY2 = g("KEY2", False, False, False, 4, 8)
KEY3 = g("KEY3", False, False, False, 5, 8)
EDIT_QUESTION = g("E_QUESTION", False, False, False, 6, 8)
EDIT_EAT = g("E_EAT", False, False, False, 7, 8)
# row 9
STEELWALLDESTRUCTABLE = g("STEELWALLDESTRUCTABLE", False, False, True, 0, 9)
EDIT_DOWN_ARROW = g("E_DOWNARROW", False, False, False, 1, 9)
EDIT_LEFTRIGHT_ARROW = g("E_LEFTRIGHTARROW", False, False, False, 2, 9)
EDIT_EVERYDIR_ARROW = g("E_EVERYDIRARROW", False, False, False, 3, 9)
EDIT_LOCKED = g("E_LOCKED", False, False, False, 4, 9)
EDIT_OUT = g("E_OUIT", False, False, False, 5, 9)
EDIT_EXCLAM = g("E_EXCLAM", False, False, False, 6, 9)
EDIT_CROSS = g("E_CROSS", False, False, False, 7, 9)
# row 10
GHOSTEXPLODE = g("GHOSTEXPLODE", False, False, False, 0, 10, sframes=4, sfps=10)
BOMBEXPLODE = g("BOMBEXPLODE", False, False, False, 4, 10, sframes=4, sfps=10)
# row 11
COW = g("COW", False, True, True, 0, 11, sframes=8, sfps=10)
# row 12
WATER = g("WATER", False, False, True, 0, 12, sframes=8, sfps=20)
# row 13
ALTFIREFLY = g("ALTFIREFLY", False, True, True, 0, 13, sframes=8, sfps=20)
# row 14
ALTBUTTERFLY = g("ALTBUTTERFLY", False, True, True, 0, 14, sframes=8, sfps=20)
# row 15
BONUSBG = g("BONUSBG", False, False, True, 0, 15, sframes=8, sfps=10)
# row 16
COVERED = g("COVERED", False, False, False, 0, 16, sframes=8, sfps=20)
# row 17
FIREFLY = g("FIREFLY", False, True, True, 0, 17, sframes=8, sfps=20)
# row 18
BUTTERFLY = g("BUTTERFLY", False, True, True, 0, 18, sframes=8, sfps=20)
# row 19
STONEFLY = g("STONEFLY", False, True, True, 0, 19, sframes=8, sfps=20)
# row 20
GHOST = g("GHOST", False, True, True, 0, 20, sframes=8, sfps=20)
# row 21
BITER = g("BITER", False, True, True, 0, 21, sframes=8, sfps=20)
# row 22
BLADDER = g("BLADDER", False, True, True, 0, 22, sframes=8, sfps=20)
# row 23
MAGICWALL = g("MAGICWALL", False, False, True, 0, 23, sframes=8, sfps=20)
# row 24
AMOEBA = g("AMOEBA", False, False, True, 0, 24, sframes=8, sfps=20)
# row 25
SLIME = g("SLIME", False, False, True, 0, 25, sframes=8, sfps=20)
# row 26 - 30
ROCKFORD.blink = g("ROCKFORD.BLINK", False, True, True, 0, 26, sframes=8, sfps=20)
ROCKFORD.tap = g("ROCKFORD.TAP", False, True, True, 0, 27, sframes=8, sfps=20)
ROCKFORD.tapblink = g("ROCKFORD.TAPBLINK", False, True, True, 0, 28, sframes=8, sfps=20)
ROCKFORD.left = g("ROCKFORD.LEFT", False, True, True, 0, 29, sframes=8, sfps=20)
ROCKFORD.right = g("ROCKFORD.RIGHT", False, True, True, 0, 30, sframes=8, sfps=20)
# row 31
DIAMOND = g("DIAMOND", True, False, True, 0, 31, sframes=8, sfps=20)
# row 32
ROCKFORD.stirring = g("ROCKFORD.STIRRING", False, True, True, 0, 32, sframes=8, sfps=20)
# row 33   # ...contains hammer
# row 34
MEGABOULDER = g("MEGABOULDER", True, False, True, 0, 34)
SKELETON = g("SKELETON", True, False, True, 1, 34)
GRAVITYSWITCH = g("GRAVITYSWITCH", False, False, False, 2, 34)
GRAVITYSWITCHON = g("GRAVITYSWITCHON", False, False, False, 3, 34)
BRICKSLOPEDUPRIGHT = g("BRICKSLOPEDUPRIGHT", True, False, True, 4, 34)
BRICKSLOPEDUPLEFT = g("BRICKSLOPEDUPLEFT", True, False, True, 5, 34)
BRICKSLOPEDDOWNLEFT = g("BRICKSLOPEDDOWNLEFT", True, False, True, 6, 34)
BRICKSLOPEDDOWNRIGHT = g("BRICKSLOPEDDOWNRIGHT", True, False, True, 7, 34)
# row 35
DIRTSLOPEDUPRIGHT = g("DIRTSLOPEDUPRIGHT", True, False, True, 0, 35)
DIRTSLOPEDUPLEFT = g("DIRTSLOPEDUPLEFT", True, False, True, 1, 35)
DIRTSLOPEDDOWNLEFT = g("DIRTSLOPEDDOWNLEFT", True, False, True, 2, 35)
DIRTSLOPEDDOWNRIGHT = g("DIRTSLOPEDDOWNRIGHT", True, False, True, 3, 35)
STEELSLOPEDUPRIGHT = g("STEELSLOPEDUPRIGHT", True, False, True, 4, 35)
STEELSLOPEDUPLEFT = g("STEELSLOPEDUPLEFT", True, False, True, 5, 35)
STEELSLOPEDDOWNLEFT = g("STEELSLOPEDDOWNLEFT", True, False, True, 6, 35)
STEELSLOPEDDOWNRIGHT = g("STEELSLOPEDDOWNRIGHT", True, False, True, 7, 35)
# row 36
NITROFLASK = g("NITROFLASK", True, False, True, 0, 36)
DIRTBALL = g("DIRTBALL", True, False, True, 1, 36)
REPLICATORSWITCHON = g("REPLICATORSWITCHON", False, False, False, 2, 36)
REPLICATORSWITCHOFF = g("REPLICATORSWITCHOFF", False, False, False, 3, 36)
AMOEBAEXPLODE = g("AMOEBAEXPLODE", False, False, False, 4, 36, sframes=4, sfps=10)
# row 37
AMOEBARECTANGLE = g("AMOEBARECTANGLE", False, True, True, 0, 37, sframes=8, sfps=10)
# row 38
REPLICATOR = g("REPLICATOR", False, False, False, 0, 38, sframes=8, sfps=20)
# row 39
LAVA = g("LAVA", False, False, True, 0, 39, sframes=8, sfps=20)
# row 40
CONVEYORRIGHT = g("CONVEYORRIGHT", False, False, True, 0, 40, sframes=8, sfps=20)
# row 41
CONVEYORLEFT = g("CONVEYORLEFT", False, False, True, 0, 41, sframes=8, sfps=20)
# row 42
DRAGONFLY = g("DRAGONFLY", False, True, True, 0, 42, sframes=8, sfps=20)
# row 43
FLYINGDIAMOND = g("FLYINGDIAMOND", True, False, True, 0, 43, sframes=8, sfps=20)
# row 44
DIRTLOOSE = g("DIRTLOOSE", False, False, True, 0, 44)
CONVEYORDIRECTIONSWITCHNORMAL = g("CONVEYORDIRECTIONSWITCHNORMAL", False, False, False, 1, 44)
CONVEYORDIRECTIONSWITCHCHANGED = g("CONVEYORDIRECTIONSWITCHCHANGED", False, False, False, 2, 44)
CONVEYORDIRECTIONSWITCHOFF = g("CONVEYORDIRECTIONSWITCHOFF", False, False, False, 3, 44)
CONVEYORDIRECTIONSWITCHON = g("CONVEYORDIRECTIONSWITCHON", False, False, False, 4, 44)
FLYINGBOULDER = g("FLYINGBOULDER", False, True, True, 5, 44)
COCONUT = g("COCONUT", False, False, True, 6, 44)
# row 45
NUTCRACK = g("NUTCRACK", False, False, False, 0, 45, sframes=4, sfps=10)
ROCKETRIGHT = g("ROCKETRIGHT", False, False, True, 4, 45)
ROCKETUP = g("ROCKETUP", False, False, True, 5, 45)
ROCKETLEFT = g("ROCKETLEFT", False, False, True, 6, 45)
ROCKETDOWN = g("ROCKETDOWN", False, False, True, 7, 45)
# row 46
ROCKETLAUNCHER = g("ROCKETLAUNCHER", False, False, True, 0, 46)
ROCKFORD.rocketlauncher = g("ROCKFORD.ROCKETLAUNCHER", False, True, True, 1, 46, sframes=0, sfps=0)
# row 49 - 50
ROCKFORD.pushleft = g("ROCKFORD.PUSHLEFT", False, True, True, 0, 49, sframes=8, sfps=20)
ROCKFORD.pushright = g("ROCKFORD.PUSHRIGHT", False, True, True, 0, 50, sframes=8, sfps=20)
