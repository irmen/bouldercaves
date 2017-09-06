"""
Boulder Caves - a Boulder Dash (tm) clone.

This module is the game logic.

Written by Irmen de Jong (irmen@razorvine.net)
License: MIT open-source.
"""

import datetime
import random
from . import caves, audio


class GameObject:
    def __init__(self, name, rounded, explodable, consumable, spritex, spritey, sframes=0, sfps=0, anim_end_callback=None):
        self.name = name
        self.rounded = rounded
        self.explodable = explodable
        self.consumable = consumable
        self.spritex = spritex
        self.spritey = spritey
        self.sframes = sframes
        self.sfps = sfps
        self.anim_end_callback = anim_end_callback

# row 0
GameObject.EMPTY = GameObject("EMPTY", False, False, True, 0, 0)
GameObject.BOULDER = GameObject("BOULDER", True, False, True, 1, 0)
GameObject.DIRT = GameObject("DIRT", False, False, True, 2, 0)
GameObject.DIRT2 = GameObject("DIRT2", False, False, True, 3, 0)
GameObject.STEEL = GameObject("STEEL", False, False, False, 4, 0)
GameObject.BRICK = GameObject("BRICK", True, False, True, 5, 0)
GameObject.BLADDERSPENDER = GameObject("BLADDERSPENDER", False, False, False, 6, 0)
GameObject.VOODOO = GameObject("VOODOO", True, False, True, 7, 0)
# row 1
GameObject.SWEET = GameObject("SWEET", True, False, True, 0, 1)
GameObject.GRAVESTONE = GameObject("GRAVESTONE", True, False, False, 1, 1)
GameObject.TRAPPEDDIAMOND = GameObject("TRAPPEDDIAMOND", False, False, False, 2, 1)
GameObject.DIAMONDKEY = GameObject("DIAMONDKEY", True, True, True, 3, 1)
GameObject.BITERSWITCH1 = GameObject("BITERSWITCH1", False, False, True, 4, 1)
GameObject.BITERSWITCH2 = GameObject("BITERSWITCH2", False, False, True, 5, 1)
GameObject.BITERSWITCH3 = GameObject("BITERSWITCH3", False, False, True, 6, 1)
GameObject.BITERSWITCH4 = GameObject("BITERSWITCH4", False, False, True, 7, 1)
# row 2
GameObject.CLOCK = GameObject("CLOCK", True, False, True, 0, 2)
GameObject.CHASINGBOULDER = GameObject("CHASINGBOULDER", True, False, True, 1, 2)
GameObject.CREATURESWITCH = GameObject("CREATURESWITCH", False, False, False, 2, 2)
GameObject.CREATURESWITCHON = GameObject("CREATURESWITCHON", False, False, False, 3, 2)
GameObject.ACID = GameObject("ACID", False, False, False, 4, 2)
GameObject.SOKOBANBOX = GameObject("SOKOBANBOX", False, False, False, 5, 2)
GameObject.INBOXBLINKING = GameObject("INBOXBLINKING", False, False, False, 6, 2, sframes=2, sfps=4)
GameObject.OUTBOXBLINKING = GameObject("OUTBOXBLINKING", False, False, False, 6, 2, sframes=2, sfps=4)
GameObject.OUTBOXCLOSED = GameObject("OUTBOXCLOSED", False, False, False, 6, 2)
# row 3
GameObject.STEELWALLBIRTH = GameObject("STEELWALLBIRTH", False, False, False, 0, 3, sframes=4, sfps=10)
GameObject.CLOCKBIRTH = GameObject("CLOCKBIRTH", False, False, False, 4, 3, sframes=4, sfps=10)
# row 4
GameObject.ROCKFORDBIRTH = GameObject("ROCKFORDBIRTH", False, False, False, 0, 4, sframes=4, sfps=10)
GameObject.ROCKFORD = GameObject("ROCKFORD", False, True, True, 3, 4)  # standing still
GameObject.BOULDERBIRTH = GameObject("BOULDERBIRTH", False, False, False, 4, 4, sframes=4, sfps=10)
# row 5
GameObject.EXPANDINGWALLSWITCHHORIZ = GameObject("EXPANDINGWALLSWITCHHORIZ", False, False, False, 0, 5)
GameObject.EXPANDINGWALLSWITCHVERT = GameObject("EXPANDINGWALLSWITCHVERT", False, False, False, 1, 5)
GameObject.ROCKFORD.bomb = (2, 5, 0, 0)
GameObject.EXPLOSION = GameObject("EXPLOSION", False, False, False, 3, 5, sframes=5, sfps=10)
# row 6
GameObject.BOMB = GameObject("BOMB", True, False, True, 0, 6)
GameObject.IGNITEDBOMB = GameObject("IGNITEDBOMB", True, False, True, 1, 6, sframes=7, sfps=10)
# row 7
GameObject.DIAMONDBIRTH = GameObject("DIAMONDBIRTH", False, False, False, 0, 7, sframes=5, sfps=10)
GameObject.TELEPORTER = GameObject("TELEPORTER", False, False, False, 5, 7)
GameObject.HAMMER = GameObject("HAMMER", True, False, False, 6, 7)
GameObject.POT = GameObject("POT", True, False, False, 7, 7)
# row 8
GameObject.DOOR1 = GameObject("DOOR1", False, False, False, 0, 8)
GameObject.DOOR2 = GameObject("DOOR2", False, False, False, 1, 8)
GameObject.DOOR3 = GameObject("DOOR3", False, False, False, 2, 8)
GameObject.KEY1 = GameObject("KEY1", False, False, False, 3, 8)
GameObject.KEY2 = GameObject("KEY2", False, False, False, 4, 8)
GameObject.KEY3 = GameObject("KEY3", False, False, False, 5, 8)
# row 10
GameObject.GHOSTEXPLODE = GameObject("GHOSTEXPLODE", False, False, False, 0, 10, sframes=4, sfps=10)
GameObject.BOMBEXPLODE = GameObject("BOMBEXPLODE", False, False, False, 4, 10, sframes=4, sfps=10)
# row 11
GameObject.COW = GameObject("COW", False, True, True, 0, 11, sframes=8, sfps=10)
# row 12
GameObject.WATER = GameObject("WATER", False, False, True, 0, 12, sframes=8, sfps=20)
# row 13
GameObject.ALTFIREFLY = GameObject("ALTFIREFLY", False, True, True, 0, 13, sframes=8, sfps=20)
# row 14
GameObject.ALTBUTTERFLY = GameObject("ALTBUTTERFLY", False, True, True, 0, 14, sframes=8, sfps=20)
# row 15
GameObject.BONUSBG = GameObject("BONUSBG", False, False, True, 0, 15, sframes=8, sfps=10)
# row 16
GameObject.COVERED = GameObject("COVERED", False, False, False, 0, 16, sframes=8, sfps=20)
# row 17
GameObject.FIREFLY = GameObject("FIREFLY", False, True, True, 0, 17, sframes=8, sfps=20)
# row 18
GameObject.BUTTERFLY = GameObject("BUTTERFLY", False, True, True, 0, 18, sframes=8, sfps=20)
# row 19
GameObject.STONEFLY = GameObject("STONEFLY", False, True, True, 0, 19, sframes=8, sfps=20)
# row 20
GameObject.GHOST = GameObject("GHOST", False, True, True, 0, 20, sframes=8, sfps=20)
# row 21
GameObject.BITER = GameObject("BITER", False, True, True, 0, 21, sframes=8, sfps=20)
# row 22
GameObject.BLADDER = GameObject("BLADDER", False, True, True, 0, 22, sframes=8, sfps=20)
# row 23
GameObject.MAGICWALL = GameObject("MAGICWALL", False, False, True, 0, 23, sframes=8, sfps=20)
# row 24
GameObject.AMOEBA = GameObject("AMOEBA", False, False, True, 0, 24, sframes=8, sfps=20)
# row 25
GameObject.SLIME = GameObject("SLIME", False, False, True, 0, 25, sframes=8, sfps=20)
# row 26 - 30
GameObject.ROCKFORD.blink = (0, 26, 8, 20)
GameObject.ROCKFORD.tap = (0, 27, 8, 20)
GameObject.ROCKFORD.tapblink = (0, 28, 8, 20)
GameObject.ROCKFORD.left = (0, 29, 8, 20)
GameObject.ROCKFORD.right = (0, 30, 8, 20)
# row 31
GameObject.DIAMOND = GameObject("DIAMOND", True, False, True, 0, 31, sframes=8, sfps=20)
# row 32
GameObject.ROCKFORD.stirring = (0, 32, 8, 20)
# row 33   # ...contains hammer
# row 34
GameObject.MEGABOULDER = GameObject("MEGABOULDER", True, False, True, 0, 34)
GameObject.SKELETON = GameObject("SKELETON", True, False, True, 1, 34)
GameObject.GRAVITYSWITCH = GameObject("GRAVITYSWITCH", False, False, False, 2, 34)
GameObject.GRAVITYSWITCHON = GameObject("GRAVITYSWITCHON", False, False, False, 3, 34)
GameObject.BRICKSLOPEDUPRIGHT = GameObject("BRICKSLOPEDUPRIGHT", True, False, True, 4, 34)
GameObject.BRICKSLOPEDUPLEFT = GameObject("BRICKSLOPEDUPLEFT", True, False, True, 5, 34)
GameObject.BRICKSLOPEDDOWNLEFT = GameObject("BRICKSLOPEDDOWNLEFT", True, False, True, 6, 34)
GameObject.BRICKSLOPEDDOWNRIGHT = GameObject("BRICKSLOPEDDOWNRIGHT", True, False, True, 7, 34)
# row 35
GameObject.DIRTSLOPEDUPRIGHT = GameObject("DIRTSLOPEDUPRIGHT", True, False, True, 0, 35)
GameObject.DIRTSLOPEDUPLEFT = GameObject("DIRTSLOPEDUPLEFT", True, False, True, 1, 35)
GameObject.DIRTSLOPEDDOWNLEFT = GameObject("DIRTSLOPEDDOWNLEFT", True, False, True, 2, 35)
GameObject.DIRTSLOPEDDOWNRIGHT = GameObject("DIRTSLOPEDDOWNRIGHT", True, False, True, 3, 35)
GameObject.STEELSLOPEDUPRIGHT = GameObject("STEELSLOPEDUPRIGHT", True, False, True, 4, 35)
GameObject.STEELSLOPEDUPLEFT = GameObject("STEELSLOPEDUPLEFT", True, False, True, 5, 35)
GameObject.STEELSLOPEDDOWNLEFT = GameObject("STEELSLOPEDDOWNLEFT", True, False, True, 6, 35)
GameObject.STEELSLOPEDDOWNRIGHT = GameObject("STEELSLOPEDDOWNRIGHT", True, False, True, 7, 35)
# row 36
GameObject.NITROFLASK = GameObject("NITROFLASK", True, False, True, 0, 36)
GameObject.DIRTBALL = GameObject("DIRTBALL", True, False, True, 1, 36)
GameObject.REPLICATORSWITCHON = GameObject("REPLICATORSWITCHON", False, False, False, 2, 36)
GameObject.REPLICATORSWITCHOFF = GameObject("REPLICATORSWITCHOFF", False, False, False, 3, 36)
GameObject.AMOEBAEXPLODE = GameObject("AMOEBAEXPLODE", False, False, False, 4, 36, sframes=4, sfps=10)
# row 37
GameObject.AMOEBARECTANGLE = GameObject("AMOEBARECTANGLE", False, True, True, 0, 37, sframes=8, sfps=10)
# row 38
GameObject.REPLICATOR = GameObject("REPLICATOR", False, False, False, 0, 38, sframes=8, sfps=20)
# row 39
GameObject.LAVA = GameObject("LAVA", False, False, True, 0, 39, sframes=8, sfps=20)
# row 40
GameObject.CONVEYORRIGHT = GameObject("CONVEYORRIGHT", False, False, True, 0, 40, sframes=8, sfps=20)
# row 41
GameObject.CONVEYORLEFT = GameObject("CONVEYORLEFT", False, False, True, 0, 41, sframes=8, sfps=20)
# row 42
GameObject.DRAGONFLY = GameObject("DRAGONFLY", False, True, True, 0, 42, sframes=8, sfps=20)
# row 43
GameObject.FLYINGDIAMOND = GameObject("FLYINGDIAMOND", True, False, True, 0, 43, sframes=8, sfps=20)
# row 44
GameObject.DIRTLOOSE = GameObject("DIRTLOOSE", False, False, True, 0, 44)
GameObject.CONVEYORDIRECTIONSWITCHNORMAL = GameObject("CONVEYORDIRECTIONSWITCHNORMAL", False, False, False, 1, 44)
GameObject.CONVEYORDIRECTIONSWITCHCHANGED = GameObject("CONVEYORDIRECTIONSWITCHCHANGED", False, False, False, 2, 44)
GameObject.CONVEYORDIRECTIONSWITCHOFF = GameObject("CONVEYORDIRECTIONSWITCHOFF", False, False, False, 3, 44)
GameObject.CONVEYORDIRECTIONSWITCHON = GameObject("CONVEYORDIRECTIONSWITCHON", False, False, False, 4, 44)
GameObject.FLYINGBOULDER = GameObject("FLYINGBOULDER", False, True, True, 5, 44)
GameObject.COCONUT = GameObject("COCONUT", False, False, True, 6, 44)
# row 45
GameObject.NUTCRACK = GameObject("NUTCRACK", False, False, False, 0, 45, sframes=4, sfps=10)
GameObject.ROCKETRIGHT = GameObject("ROCKETRIGHT", False, False, True, 4, 45)
GameObject.ROCKETUP = GameObject("ROCKETUP", False, False, True, 5, 45)
GameObject.ROCKETLEFT = GameObject("ROCKETLEFT", False, False, True, 6, 45)
GameObject.ROCKETDOWN = GameObject("ROCKETDOWN", False, False, True, 7, 45)
# row 46
GameObject.ROCKETLAUNCHER = GameObject("ROCKETLAUNCHER", False, False, True, 0, 46)
GameObject.ROCKFORD.rocketlauncher = (1, 46, 0, 0)
# row 49 - 50
GameObject.ROCKFORD.pushleft = (0, 49, 8, 20)
GameObject.ROCKFORD.pushright = (0, 50, 8, 20)


# noinspection PyAttributeOutsideInit
class GameState:
    class Cell:
        __slots__ = ("obj", "x", "y", "frame", "falling", "direction", "anim_start_gfx_frame")

        def __init__(self, obj, x, y):
            self.obj = obj  # what object is in the cell
            self.x = x
            self.y = y
            self.frame = 0
            self.falling = False
            self.direction = None
            self.anim_start_gfx_frame = 0

        def __repr__(self):
            return "<Cell {:s} @{:d},{:d}>".format(self.obj.name, self.x, self.y)

        def isempty(self):
            return self.obj in {GameObject.EMPTY, GameObject.BONUSBG, None}

        def isdirt(self):
            return self.obj in {GameObject.DIRTBALL, GameObject.DIRT, GameObject.DIRT2, GameObject.DIRTLOOSE,
                                GameObject.DIRTSLOPEDDOWNLEFT, GameObject.DIRTSLOPEDDOWNRIGHT,
                                GameObject.DIRTSLOPEDUPLEFT, GameObject.DIRTSLOPEDUPRIGHT}

        def isrockford(self):
            return self.obj is GameObject.ROCKFORD

        def isrounded(self):
            return self.obj.rounded

        def isexplodable(self):
            return self.obj.explodable

        def isconsumable(self):
            return self.obj.consumable

        def ismagic(self):
            return self.obj is GameObject.MAGICWALL

        def isbutterfly(self):
            # these explode to diamonds
            return self.obj is GameObject.BUTTERFLY or self.obj is GameObject.ALTBUTTERFLY

        def isamoeba(self):
            return self.obj is GameObject.AMOEBA or self.obj is GameObject.AMOEBARECTANGLE

        def isfirefly(self):
            return self.obj is GameObject.FIREFLY or self.obj is GameObject.ALTFIREFLY

        def isdiamond(self):
            return self.obj is GameObject.DIAMOND or self.obj is GameObject.FLYINGDIAMOND

        def isboulder(self):
            return self.obj in {GameObject.BOULDER, GameObject.MEGABOULDER, GameObject.CHASINGBOULDER, GameObject.FLYINGBOULDER}

        def isoutbox(self):
            return self.obj is GameObject.OUTBOXBLINKING

        def canfall(self):
            return self.obj in {GameObject.BOULDER, GameObject.SWEET, GameObject.DIAMONDKEY, GameObject.BOMB,
                                GameObject.IGNITEDBOMB, GameObject.KEY1, GameObject.KEY2, GameObject.KEY3,
                                GameObject.DIAMOND, GameObject.MEGABOULDER, GameObject.SKELETON, GameObject.NITROFLASK,
                                GameObject.DIRTBALL, GameObject.COCONUT, GameObject.ROCKETLAUNCHER}

    class MovementInfo:
        def __init__(self):
            self.direction = self.lastXdir = None
            self.up = self.down = self.left = self.right = False
            self.grab = False

        @property
        def moving(self):
            return self.direction is not None

        def start_up(self):
            self.direction = "u"
            self.up = True

        def start_down(self):
            self.direction = "d"
            self.down = True

        def start_left(self):
            self.direction = "l"
            self.left = True
            self.lastXdir = "l"

        def start_right(self):
            self.direction = "r"
            self.right = True
            self.lastXdir = "r"

        def start_grab(self):
            self.grab = True

        def stop_all(self):
            self.grab = self.up = self.down = self.left = self.right = False
            self.direction = None

        def stop_grab(self):
            self.grab = False

        def stop_up(self):
            self.up = False
            self.direction = self.where() if self.direction == "u" else self.direction

        def stop_down(self):
            self.down = False
            self.direction = self.where() if self.direction == "d" else self.direction

        def stop_left(self):
            self.left = False
            self.direction = self.where() if self.direction == "l" else self.direction

        def stop_right(self):
            self.right = False
            self.direction = self.where() if self.direction == "r" else self.direction

        def where(self):
            if self.up:
                return "u"
            elif self.down:
                return "d"
            elif self.left:
                return "l"
            elif self.right:
                return "r"

    def __init__(self, gfxwindow):
        self.gfxwindow = gfxwindow
        self.graphics_frame_counter = 0    # will be set via the update() method
        self.fps = 8      # game logic updates every 1/8 seconds
        self.update_timestep = 1 / self.fps
        self.width = gfxwindow.tilesheet.width
        self.height = gfxwindow.tilesheet.height
        self._dirxy = {
            None: 0,
            "u": -self.width,
            "d": self.width,
            "l": -1,
            "r": 1,
            "lu": -self.width - 1,
            "ru": -self.width + 1,
            "ld": self.width - 1,
            "rd": self.width + 1
        }
        self.cave = []
        for y in range(self.height):
            for x in range(self.width):
                self.cave.append(self.Cell(GameObject.EMPTY, x, y))
        # set the anim end callbacks:
        GameObject.ROCKFORDBIRTH.anim_end_callback = self.end_rockfordbirth
        GameObject.EXPLOSION.anim_end_callback = self.end_explosion
        GameObject.DIAMONDBIRTH.anim_end_callback = self.end_diamondbirth
        # and start the game on the title screen.
        self.restart()

    def restart(self):
        audio.play_sample("music", repeat=True)
        self.frame = 0
        self.bonusbg_frame = 0    # till what frame should the bg be the bonus sparkly things instead of spaces
        self.level = -1
        self.level_name = self.level_description = "???"
        self.level_won = False
        self.game_status = "waiting"    # waiting / playing / lost / won
        self.intermission = False
        self.score = self.extralife_score = 0
        self.diamondvalue_initial = self.diamondvalue_extra = 0
        self.diamonds = self.diamonds_needed = 0
        self.lives = 3
        self.idle = {
            "blink": False,
            "tap": False,
            "uncover": False
        }
        self.keys = {
            "diamond": 0,
            "one": True,
            "two": True,
            "three": True
        }
        self.magicwall = {
            "active": False,
            "time": 0
        }
        self.amoeba = {
            "size": 0,
            "max": 0,
            "slow": 0,
            "enclosed": False,
            "dead": None
        }
        self.timeremaining = None
        self.timelimit = None
        self.rockford_cell = None
        self.rockford_found_frame = -1
        self.movement = self.MovementInfo()
        self.flash = 0
        # draw the 'title screen'
        self.draw_rectangle(GameObject.DIRT2, 0, 0, self.width, self.height, GameObject.EMPTY)
        title = r"""
/**\           *\     *
*  *   +        *   + *        +
****\ /**\ *  * *  /*** /**\ */*\
*   * *  * *  * *  *  * *  * **
*   * *  * *  * *  *  * ***$ *$   f
* #+* *  * *+ * *  * #* *    *
@***$ @**$ @**$ @* @*** @**\ *#

     /*\
 f   *      +              +
     *    /**\  \  / /**\ /**\
     *    *  *  *  * *+ * * +    f
  f  *+   *  *  *  * ***$ @**\
     *#+  *  *  @  $ * #   # *  f
     @*** @***\  @$  @**\ ***$
"""
        for y, tl in enumerate(title.splitlines()):
            for x, c in enumerate(tl):
                if c == ' ':
                    continue
                obj = {
                    '*': GameObject.BRICK,
                    '/': GameObject.BRICKSLOPEDUPLEFT,
                    '\\': GameObject.BRICKSLOPEDUPRIGHT,
                    '@': GameObject.BRICKSLOPEDDOWNLEFT,
                    '$': GameObject.BRICKSLOPEDDOWNRIGHT,
                    '+': GameObject.FLYINGDIAMOND,
                    '#': GameObject.BOULDER,
                    'f': GameObject.ALTFIREFLY
                }[c]
                self.draw_single(obj, 2 + x, 1 + y)

        self.draw_line(GameObject.LAVA, 4, self.height - 3, self.width - 8, "r")
        self.draw_line(GameObject.DIRT, 3, self.height - 2, self.width - 6, "r")
        self.draw_single(GameObject.DIRTSLOPEDUPLEFT, 3, self.height - 3)
        self.draw_single(GameObject.DIRTSLOPEDUPLEFT, 2, self.height - 2)
        self.draw_single(GameObject.DIRTSLOPEDUPRIGHT, self.width - 4, self.height - 3)
        self.draw_single(GameObject.DIRTSLOPEDUPRIGHT, self.width - 3, self.height - 2)

    def load_c64level(self, levelnumber):
        c64cave = caves.Cave.decode_from_lvl(levelnumber)
        assert c64cave.width == self.width and c64cave.height == self.height
        self.level_name = c64cave.name
        self.level_description = c64cave.description
        self.intermission = c64cave.intermission
        level_intro_popup = levelnumber != self.level
        self.level = levelnumber
        self.level_won = False
        self.game_status = "playing"
        self.flash = 0
        self.diamonds = 0
        self.diamonds_needed = c64cave.diamonds_needed
        self.diamondvalue_initial = c64cave.diamondvalue_initial
        self.diamondvalue_extra = c64cave.diamondvalue_extra
        self.timeremaining = datetime.timedelta(seconds=c64cave.time)
        self.frame = 0
        self.bonusbg_frame = 0
        self.timelimit = None   # will be set as soon as Rockford spawned
        self.idle["blink"] = self.idle["tap"] = False
        self.idle["uncover"] = True
        self.magicwall["active"] = False
        self.magicwall["time"] = c64cave.magicwall_millingtime / self.update_timestep
        self.rockford_cell = None     # the cell where Rockford currently is
        self.rockford_found_frame = 0
        self.movement = self.MovementInfo()
        self.amoeba = {
            "size": 0,
            "max": c64cave.amoebamaxsize,
            "slow": c64cave.amoeba_slowgrowthtime / self.update_timestep,
            "enclosed": False,
            "dead": None
        }
        # convert the c64 cave map
        conversion = {
            0x00: (GameObject.EMPTY, None),
            0x01: (GameObject.DIRT, None),
            0x02: (GameObject.BRICK, None),
            0x03: (GameObject.MAGICWALL, None),
            0x04: (GameObject.OUTBOXCLOSED, None),
            0x05: (GameObject.OUTBOXBLINKING, None),
            0x07: (GameObject.STEEL, None),
            0x08: (GameObject.FIREFLY, 'l'),
            0x09: (GameObject.FIREFLY, 'u'),
            0x0a: (GameObject.FIREFLY, 'r'),
            0x0b: (GameObject.FIREFLY, 'd'),
            0x10: (GameObject.BOULDER, None),
            0x12: (GameObject.BOULDER, None),
            0x14: (GameObject.DIAMOND, None),
            0x16: (GameObject.DIAMOND, None),
            0x25: (GameObject.INBOXBLINKING, None),
            0x30: (GameObject.BUTTERFLY, 'd'),
            0x31: (GameObject.BUTTERFLY, 'l'),
            0x32: (GameObject.BUTTERFLY, 'u'),
            0x33: (GameObject.BUTTERFLY, 'r'),
            0x38: (GameObject.ROCKFORD, None),
            0x3a: (GameObject.AMOEBA, None)
        }
        for i, obj in enumerate(c64cave.map):
            y, x = divmod(i, self.width)
            obj, direction = conversion[obj]
            self.draw_single(obj, x, y, initial_direction=direction)
        self.gfxwindow.create_colored_tiles(c64cave.bgcolor1, c64cave.bgcolor2, c64cave.fgcolor)
        self.gfxwindow.tilesheet.all_dirty()
        if level_intro_popup:
            audio.play_sample("diamond2")
            self.gfxwindow.popup("Level {:d}: {:s}\n\n{:s}".format(self.level, self.level_name, self.level_description))

    def cheat_skip_level(self):
        self.load_c64level(self.level % len(caves.CAVES) + 1)

    def draw_rectangle(self, obj, x1, y1, width, height, fillobject=None):
        self.draw_line(obj, x1, y1, width, 'r')
        self.draw_line(obj, x1, y1 + height - 1, width, 'r')
        self.draw_line(obj, x1, y1 + 1, height - 2, 'd')
        self.draw_line(obj, x1 + width - 1, y1 + 1, height - 2, 'd')
        if fillobject is not None:
            for y in range(y1 + 1, y1 + height - 1):
                self.draw_line(fillobject, x1 + 1, y, width - 2, 'r')

    def draw_line(self, obj, x, y, length, direction):
        dx, dy = {
            "l": (-1, 0),
            "r": (1, 0),
            "u": (0, -1),
            "d": (0, 1),
            "lu": (-1, -1),
            "ru": (1, -1),
            "ld": (-1, 1),
            "rd": (1, 1)
        }[direction.lower()]
        for _ in range(length):
            self.draw_single(obj, x, y)
            x += dx
            y += dy

    def draw_single(self, obj, x, y, initial_direction=None):
        self.draw_single_cell(self.cave[x + y * self.width], obj, initial_direction)

    def draw_single_cell(self, cell, obj, initial_direction=None):
        cell.obj = obj
        cell.direction = initial_direction
        cell.frame = self.frame
        cell.anim_start_gfx_frame = self.graphics_frame_counter
        cell.falling = False
        if obj is GameObject.MAGICWALL:
            if not self.magicwall["active"]:
                obj = GameObject.BRICK
        self.gfxwindow.tilesheet[cell.x, cell.y] = obj.spritex + self.gfxwindow.tile_image_numcolumns * obj.spritey
        # animation is handled by the graphics refresh

    def clear_cell(self, cell):
        self.draw_single_cell(cell, GameObject.BONUSBG if self.bonusbg_frame > self.frame else GameObject.EMPTY)

    def get(self, cell, direction=None):
        # retrieve the cell relative to the given cell
        return self.cave[cell.x + cell.y * self.width + self._dirxy[direction]]

    def move(self, cell, direction):
        # move the object in the cell to the given relative direction
        if not direction:
            return  # no movement...
        newcell = self.cave[cell.x + cell.y * self.width + self._dirxy[direction]]
        self.draw_single_cell(newcell, cell.obj)
        newcell.falling = cell.falling
        newcell.direction = cell.direction
        self.clear_cell(cell)
        cell.falling = False
        cell.direction = None
        return newcell

    def push(self, cell, direction):
        # try to push the thing in the given direction
        pushedcell = self.get(cell, direction)
        targetcell = self.get(pushedcell, direction)
        if targetcell.isempty():
            if random.randint(1, 8) == 1:
                self.move(pushedcell, direction)
                self.fall_sound(targetcell, pushing=True)
                if not self.movement.grab:
                    cell = self.move(cell, direction)
        return cell

    def domagic(self, cell):
        # something (diamond, boulder) is falling on a magic wall
        if self.magicwall["time"] > 0:
            if not self.magicwall["active"]:
                # magic wall activates! play sound. Will be silenced once the milling timer runs out.
                self.draw_single(GameObject.DIAMOND, 14, 10)
                self.draw_single(GameObject.DIAMOND, 15, 10)
                audio.play_sample("magic_wall", repeat=True)
            self.magicwall["active"] = True
            obj = cell.obj
            self.clear_cell(cell)
            cell_under_wall = self.get(self.get(cell, 'd'), 'd')
            if cell_under_wall.isempty():
                if obj is GameObject.DIAMOND:
                    self.draw_single_cell(cell_under_wall, GameObject.BOULDER)
                    audio.play_sample("boulder")
                elif obj is GameObject.BOULDER:
                    self.draw_single_cell(cell_under_wall, GameObject.DIAMOND)
                    audio.play_sample("diamond" + str(random.randint(1, 6)))
        else:
            # magic wall is disabled, stuff falling on it just disappears (a sound is already played)
            self.clear_cell(cell)

    def cells_with_animations(self):
        return [cell for cell in self.cave if cell.obj.sframes]

    def update(self, graphics_frame_counter):
        self.graphics_frame_counter = graphics_frame_counter    # we store this to properly sync up animation frames
        if self.game_status != "playing":
            return
        self.frame_start()
        if not self.level_won:
            # sweep the cave
            for cell in self.cave:
                if cell.frame < self.frame:
                    if cell.falling:
                        self.update_falling(cell)
                    elif cell.canfall():
                        self.update_canfall(cell)
                    elif cell.isfirefly():
                        self.update_firefly(cell)
                    elif cell.isbutterfly():
                        self.update_butterfly(cell)
                    elif cell.obj is GameObject.INBOXBLINKING:
                        self.update_inbox(cell)
                    elif cell.isrockford():
                        self.update_rockford(cell)
                    elif cell.isamoeba():
                        self.update_amoeba(cell)
                    elif cell.obj is GameObject.OUTBOXCLOSED:
                        self.update_outboxclosed(cell)
                    elif cell.obj is GameObject.BONUSBG:
                        if self.bonusbg_frame < self.frame:
                            self.draw_single_cell(cell, GameObject.EMPTY)
        self.frame_end()

    def frame_start(self):
        self.frame += 1
        # idle animation (when not moving)
        if not self.movement.moving:
            if random.randint(1, 4) == 1:
                self.idle["blink"] = not self.idle["blink"]
            if random.randint(1, 16) == 1:
                self.idle["tap"] = not self.idle["tap"]
        else:
            self.idle["blink"] = self.idle["tap"] = False
        self.amoeba["size"] = 0
        self.amoeba["enclosed"] = True
        self.rockford_cell = None
        self.fall_sound_to_play = None

    def frame_end(self):
        if self.fall_sound_to_play:
            audio.play_sample(self.fall_sound_to_play)
            self.fall_sound_to_play = None
        if self.amoeba["dead"] is None:
            if self.amoeba["enclosed"]:
                self.amoeba["dead"] = GameObject.DIAMOND
            elif self.amoeba["size"] > self.amoeba["max"]:
                self.amoeba["dead"] = GameObject.BOULDER
            elif self.amoeba["slow"] > 0:
                self.amoeba["slow"] -= 1
        if self.magicwall["active"]:
            self.magicwall["time"] -= 1
            still_magic = self.magicwall["time"] > 0
            if self.magicwall["active"] and not still_magic:
                # magic wall has stopped! stop playing the milling sound
                audio.silence_audio()
            self.magicwall["active"] = still_magic
        if self.timelimit and not self.level_won and self.rockford_cell:
            secs_before = self.timeremaining.seconds
            self.timeremaining = self.timelimit - datetime.datetime.now()
            secs_after = self.timeremaining.seconds
            if secs_after <= 0:
                self.timeremaining = datetime.timedelta(0)
            if secs_after != secs_before and 1 <= secs_after <= 9:
                audio.play_sample("timeout"+str(10-secs_after))
        if self.level_won:
            if self.timeremaining.seconds > 0:
                add_score = min(self.timeremaining.seconds, 5)
                self.score += add_score
                self.extralife_score += add_score
                self.check_extralife_score()
                self.timeremaining -= datetime.timedelta(seconds=add_score)
            else:
                self.load_next_level()
        elif self.timelimit and self.update_timestep * (self.frame - self.rockford_found_frame) > 5:
            # after 5 seconds with dead rockford we reload the current level
            self.life_lost()

    def life_lost(self):
        if self.intermission:
            self.load_next_level()  # don't lose a life, instead skip out of the intermission.
            return
        self.lives = max(0, self.lives - 1)
        if self.lives > 0:
            self.load_c64level(self.level)  # retry current level
        else:
            self.stop_game("lost")

    def stop_game(self, status):
        self.game_status = status
        if self.rockford_cell:
            self.clear_cell(self.rockford_cell)
        self.rockford_found_frame = 0
        if status == "lost":
            audio.play_sample("game_over")
            self.gfxwindow.popup("Game Over.\n\nYour final score: {:d}\n\npress Escape to return to the title screen".format(self.score))
        elif status == "won":
            self.lives = 0
            audio.play_sample("extra_life")
            self.gfxwindow.popup("Congratulations, you finished the game!\n\nYour final score: {:d}\n\n"
                                 "press Escape to return to the title screen".format(self.score))

    def load_next_level(self):
        level = self.level + 1
        if level > len(caves.CAVES):
            self.stop_game("won")
        else:
            audio.silence_audio()
            self.load_c64level(level)

    def update_canfall(self, cell):
        # if the cell below this one is empty, the object starts to fall
        if self.get(cell, 'd').isempty():
            if not cell.falling:
                self.fall_sound(cell)
                cell.falling = True
        elif self.get(cell, 'd').isrounded():
            if self.get(cell, 'l').isempty() and self.get(cell, 'ld').isempty():
                self.move(cell, 'l').falling = True
            elif self.get(cell, 'r').isempty() and self.get(cell, 'rd').isempty():
                self.move(cell, 'r').falling = True

    def update_falling(self, cell):
        # let the object fall down, explode stuff if explodable!
        cellbelow = self.get(cell, 'd')
        if cellbelow.isempty():
            cell = self.move(cell, 'd')
            if not self.get(cell, 'd').isempty():
                self.fall_sound(cell)  # play a sound as soon as we hit something.
        elif cellbelow.isexplodable():
            self.explode(cell, 'd')
        elif cellbelow.ismagic():
            self.domagic(cell)
        elif cellbelow.isrounded() and self.get(cell, 'l').isempty() and self.get(cell, 'ld').isempty():
            self.move(cell, 'l')
        elif cellbelow.isrounded() and self.get(cell, 'r').isempty() and self.get(cell, 'rd').isempty():
            self.move(cell, 'r')
        else:
            cell.falling = False  # falling was blocked by something

    def update_firefly(self, cell):
        # if it hits Rockford or Amoeba it explodes
        # tries to rotate 90 degrees left and move to empty cell in new or original direction
        # if not possible rotate 90 right and wait for next update
        newdir = self.rotate90left(cell.direction)
        if self.get(cell, 'u').isrockford() or self.get(cell, 'd').isrockford() \
                or self.get(cell, 'l').isrockford() or self.get(cell, 'r').isrockford():
            self.explode(cell)
        elif self.get(cell, 'u').isamoeba() or self.get(cell, 'd').isamoeba() \
                or self.get(cell, 'l').isamoeba() or self.get(cell, 'r').isamoeba():
            self.explode(cell)
        elif self.get(cell, newdir).isempty():
            self.move(cell, newdir).direction = newdir
        elif self.get(cell, cell.direction).isempty():
            self.move(cell, cell.direction)
        else:
            cell.direction = self.rotate90right(cell.direction)

    def update_butterfly(self, cell):
        # same as firefly except butterflies rotate in the opposite direction
        newdir = self.rotate90right(cell.direction)
        if self.get(cell, 'u').isrockford() or self.get(cell, 'd').isrockford() \
                or self.get(cell, 'l').isrockford() or self.get(cell, 'r').isrockford():
            self.explode(cell)
        elif self.get(cell, 'u').isamoeba() or self.get(cell, 'd').isamoeba() \
                or self.get(cell, 'l').isamoeba() or self.get(cell, 'r').isamoeba():
            self.explode(cell)
        elif self.get(cell, newdir).isempty():
            self.move(cell, newdir).direction = newdir
        elif self.get(cell, cell.direction).isempty():
            self.move(cell, cell.direction)
        else:
            cell.direction = self.rotate90left(cell.direction)

    def update_inbox(self, cell):
        # after 4 blinks (=2 seconds), Rockford spawns in the inbox.
        if self.update_timestep * self.frame > 2.0:
            self.draw_single_cell(cell, GameObject.ROCKFORDBIRTH)
            audio.play_sample("crack")

    def update_outboxclosed(self, cell):
        if self.diamonds >= self.diamonds_needed:
            if cell.obj is not GameObject.OUTBOXBLINKING:
                audio.play_sample("crack")
            self.draw_single_cell(cell, GameObject.OUTBOXBLINKING)

    def update_amoeba(self, cell):
        # @todo amoeba sound
        if self.amoeba["dead"] is not None:
            self.draw_single_cell(cell, self.amoeba["dead"])
        else:
            self.amoeba["size"] += 1
            if self.get(cell, 'u').isempty() or self.get(cell, 'd').isempty() \
                    or self.get(cell, 'r').isempty() or self.get(cell, 'l').isempty() \
                    or self.get(cell, 'u').isdirt() or self.get(cell, 'd').isdirt() \
                    or self.get(cell, 'r').isdirt() or self.get(cell, 'l').isdirt():
                self.amoeba["enclosed"] = False
            if self.timelimit:
                grow = random.randint(1, 128) < 4 if self.amoeba["slow"] else random.randint(1, 4) == 1
                direction = random.choice("udlr")
                if grow and (self.get(cell, direction).isdirt() or self.get(cell, direction).isempty()):
                    self.draw_single_cell(self.get(cell, direction), cell.obj)

    def update_rockford(self, cell):
        self.rockford_cell = cell
        self.rockford_found_frame = self.frame
        if self.level_won:
            return
        if self.timeremaining.seconds <= 0:
            self.explode(cell)
        elif self.movement.moving:
            targetcell = self.get(cell, self.movement.direction)
            if self.movement.grab:
                if targetcell.isdirt():
                    audio.play_sample("walk_dirt")
                    self.clear_cell(targetcell)
                elif targetcell.isdiamond():
                    self.collect_diamond()
                    self.clear_cell(targetcell)
                elif self.movement.direction in ("l", "r") and targetcell.isboulder():
                    self.push(cell, self.movement.direction)
            elif targetcell.isempty():
                audio.play_sample("walk_empty")
                cell = self.move(cell, self.movement.direction)
            elif targetcell.isdirt():
                audio.play_sample("walk_dirt")
                cell = self.move(cell, self.movement.direction)
            elif targetcell.isboulder() and self.movement.direction in ("l", "r"):
                cell = self.push(cell, self.movement.direction)
            elif targetcell.isdiamond():
                self.collect_diamond()
                cell = self.move(cell, self.movement.direction)
            elif targetcell.isoutbox():
                cell = self.move(cell, self.movement.direction)
                self.level_won = True   # exit found!
                audio.play_sample("finished")
                self.movement.stop_all()
        self.rockford_cell = cell

    def fall_sound(self, cell, pushing=False):
        if cell.isboulder():
            if pushing:
                self.fall_sound_to_play = "box_push"
            else:
                self.fall_sound_to_play = "boulder"
        elif cell.isdiamond():
            self.fall_sound_to_play = "diamond" + str(random.randint(1, 6))

    def collect_diamond(self):
        audio.play_sample("collect_diamond")
        self.diamonds += 1
        points = self.diamondvalue_extra if self.diamonds > self.diamonds_needed else self.diamondvalue_initial
        self.score += points
        self.extralife_score += points
        if self.diamonds >= self.diamonds_needed and not self.flash:
            self.flash = self.frame + self.fps // 2
        self.check_extralife_score()

    def check_extralife_score(self):
        # extra life every 500 points
        if self.extralife_score >= 500:
            self.extralife_score -= 500
            self.add_extra_life()

    def add_extra_life(self):
        self.lives += 1
        audio.play_sample("extra_life")
        for cell in self.cave:
            if cell.obj is GameObject.EMPTY:
                self.draw_single_cell(cell, GameObject.BONUSBG)
                self.bonusbg_frame = self.frame + self.fps * 6   # sparkle for 6 seconds

    def add_extra_time(self, seconds):
        self.timelimit += datetime.timedelta(seconds=seconds)

    def end_rockfordbirth(self, cell):
        # rockfordbirth eventually creates the real Rockford and starts the level timer.
        if self.game_status == "playing":
            self.draw_single_cell(cell, GameObject.ROCKFORD)
            self.timelimit = datetime.datetime.now() + self.timeremaining

    def end_explosion(self, cell):
        # a normal explosion ends with an empty cell
        self.clear_cell(cell)

    def end_diamondbirth(self, cell):
        # diamondbirth ends with a diamond
        self.draw_single_cell(cell, GameObject.DIAMOND)

    def explode(self, cell, direction=None):
        audio.play_sample("explosion")
        explosioncell = self.cave[cell.x + cell.y * self.width + self._dirxy[direction]]
        if explosioncell.isbutterfly():
            obj = GameObject.DIAMONDBIRTH
        else:
            obj = GameObject.EXPLOSION
        self.draw_single_cell(explosioncell, obj)
        for direction in ["u", "ru", "r", "rd", "d", "ld", "l", "lu"]:
            cell = self.cave[explosioncell.x + explosioncell.y * self.width + self._dirxy[direction]]
            if cell.isexplodable():
                self.explode(cell, None)
            elif cell.isconsumable():
                self.draw_single_cell(cell, obj)

    @staticmethod
    def rotate90left(direction):
        return {
            None: None,
            "u": "l",
            "d": "r",
            "l": "d",
            "r": "u",
            "lu": "ld",
            "ru": "lu",
            "ld": "rd",
            "rd": "ru"
        }[direction]

    @staticmethod
    def rotate90right(direction):
        return {
            None: None,
            "u": "r",
            "d": "l",
            "l": "u",
            "r": "d",
            "lu": "ru",
            "ru": "rd",
            "ld": "lu",
            "rd": "ld"
        }[direction]

    def update_scorebar(self):
        # draw the score bar.
        # note: the following is a complex score bar including keys, but those are not used in the C64 boulderdash:
        # text = ("\x08{lives:2d}  \x0c {keys:02d}\x7f\x7f\x7f  {diamonds:<10s}  {time:s}  $ {score:06d}".format(
        #     lives=self.lives,
        #     time=str(self.timeremaining)[3:7],
        #     score=self.score,
        #     diamonds="\x0e {:02d}/{:02d}".format(self.diamonds, self.diamonds_needed),
        #     keys=self.keys["diamond"]
        # )).ljust(self.width)
        # self.gfxwindow.tilesheet_score.set_tiles(0, 0, self.gfxwindow.text2tiles(text))
        # if self.keys["one"]:
        #     self.gfxwindow.tilesheet_score[9, 0] = GameObject.KEY1.spritex + GameObject.KEY1.spritey * self.gfxwindow.tile_image_numcolumns
        # if self.keys["two"]:
        #     self.gfxwindow.tilesheet_score[10, 0] = GameObject.KEY2.spritex + GameObject.KEY2.spritey * self.gfxwindow.tile_image_numcolumns
        # if self.keys["three"]:
        #     self.gfxwindow.tilesheet_score[11, 0] = GameObject.KEY3.spritex + GameObject.KEY3.spritey * self.gfxwindow.tile_image_numcolumns
        if self.level < 1:
            # level has not been loaded yet (we're still at the title screen)
            ts = self.gfxwindow.tilesheet_score
            ts.set_tiles(0, 0, self.gfxwindow.text2tiles("Boulder Caves".center(self.width)))
            ts.set_tiles(0, 1, self.gfxwindow.text2tiles("F1  to start new game!".center(self.width)))
            ts[0, 0] = ts[self.width - 1, 0] = ts[0, 1] = ts[self.width - 1, 1] = self.gfxwindow.sprite2tile(GameObject.MEGABOULDER)
            ts[1, 0] = ts[self.width - 2, 0] = ts[1, 1] = ts[self.width - 2, 1] = self.gfxwindow.sprite2tile(GameObject.FLYINGDIAMOND)
            ts[2, 0] = ts[self.width - 3, 0] = ts[2, 1] = ts[self.width - 3, 1] = self.gfxwindow.sprite2tile(GameObject.DIAMOND)
            ts[3, 0] = ts[3, 1] = self.gfxwindow.sprite2tile(GameObject.ROCKFORD.pushleft)
            ts[self.width - 4, 0] = ts[self.width - 4, 1] = self.gfxwindow.sprite2tile(GameObject.ROCKFORD.pushright)
            return
        text = ("\x08{lives:2d}   {normal:d}\x0e{extra:d}  {diamonds:<10s}  {time:s}  $ {score:06d}".format(
            lives=self.lives,
            time=str(self.timeremaining)[3:7],
            score=self.score,
            normal=self.diamondvalue_initial,
            extra=self.diamondvalue_extra,
            diamonds="{:02d}/{:02d}".format(self.diamonds, self.diamonds_needed),
        )).ljust(self.width)
        self.gfxwindow.tilesheet_score.set_tiles(0, 0, self.gfxwindow.text2tiles(text))
        if self.game_status == "won":
            tiles = self.gfxwindow.text2tiles("\x0e  C O N G R A T U L A T I O N S  \x0e".center(self.width))
        elif self.game_status == "lost":
            tiles = self.gfxwindow.text2tiles("\x0b  G A M E   O V E R  \x0b".center(self.width))
        else:
            tiles = self.gfxwindow.text2tiles("Level {:d}: {:s}".format(self.level, self.level_name).center(self.width))
        self.gfxwindow.tilesheet_score.set_tiles(0, 1, tiles[:40])
