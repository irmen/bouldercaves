"""
Boulder Caves - a Boulder Dash (tm) clone.

This module contains the game logic.

Written by Irmen de Jong (irmen@razorvine.net)
License: GNU GPL 3.0, see LICENSE
"""

import datetime
import random
import json
from enum import Enum
from typing import List, Optional, Sequence, Generator
from .objects import Direction
from . import caves, audio, user_data_dir, tiles, objects


class GameStatus(Enum):
    WAITING = 1
    REVEALING_PLAY = 2
    REVEALING_DEMO = 3
    PLAYING = 4
    PAUSED = 5
    LOST = 6
    WON = 7
    DEMO = 8
    HIGHSCORE = 9


class HighScores:
    # high score table is 8 entries, name len=7 max, score max=999999
    # table starts with score then the name, for easy sorting
    max_namelen = 7

    def __init__(self, cavesetname) -> None:
        self.name = cavesetname.lower().replace(' ', '_').replace('.', '_')
        self.load()

    def __del__(self):
        self.save()

    def __iter__(self):
        yield from self.scores

    def save(self) -> None:
        with open(user_data_dir + "highscores-{:s}.json".format(self.name), "wt") as out:
            json.dump(self.scores, out)

    def load(self) -> None:
        try:
            with open(user_data_dir + "highscores-{:s}.json".format(self.name), "rt") as scorefile:
                self.scores = json.load(scorefile)
        except FileNotFoundError:
            print("Using new high-score table.")
            self.scores = [[200, "idj"]] * 8
            self.save()

    def score_pos(self, playerscore: int) -> Optional[int]:
        for pos, (score, _) in enumerate(self.scores, start=1):
            if score < playerscore:
                return pos
        return None

    def add(self, name: str, score: int) -> None:
        pos = self.score_pos(score)
        if not pos:
            raise ValueError("score is not a new high score")
        self.scores.insert(pos - 1, [score, name])
        self.scores = self.scores[:8]


class Cell:
    __slots__ = ("obj", "x", "y", "frame", "falling", "direction", "anim_start_gfx_frame")

    def __init__(self, obj: objects.GameObject, x: int, y: int) -> None:
        self.obj = obj  # what object is in the cell
        self.x = x
        self.y = y
        self.frame = 0
        self.falling = False
        self.direction = Direction.NOWHERE
        self.anim_start_gfx_frame = 0

    def __repr__(self):
        return "<Cell {:s} @{:d},{:d}>".format(self.obj.name, self.x, self.y)

    def isempty(self) -> bool:
        return self.obj in {objects.EMPTY, objects.BONUSBG, None}

    def isdirt(self) -> bool:
        return self.obj in {objects.DIRTBALL, objects.DIRT, objects.DIRT2, objects.DIRTLOOSE,
                            objects.DIRTSLOPEDDOWNLEFT, objects.DIRTSLOPEDDOWNRIGHT,
                            objects.DIRTSLOPEDUPLEFT, objects.DIRTSLOPEDUPRIGHT}

    def isrockford(self) -> bool:
        return self.obj is objects.ROCKFORD

    def isrounded(self) -> bool:
        return self.obj.rounded

    def isexplodable(self) -> bool:
        return self.obj.explodable

    def isconsumable(self) -> bool:
        return self.obj.consumable

    def ismagic(self) -> bool:
        return self.obj is objects.MAGICWALL

    def isslime(self) -> bool:
        return self.obj is objects.SLIME

    def isbutterfly(self) -> bool:
        # these explode to diamonds
        return self.obj is objects.BUTTERFLY or self.obj is objects.ALTBUTTERFLY

    def isamoeba(self) -> bool:
        return self.obj is objects.AMOEBA or self.obj is objects.AMOEBARECTANGLE

    def isfirefly(self) -> bool:
        return self.obj is objects.FIREFLY or self.obj is objects.ALTFIREFLY

    def isdiamond(self) -> bool:
        return self.obj is objects.DIAMOND or self.obj is objects.FLYINGDIAMOND

    def isboulder(self) -> bool:
        return self.obj in {objects.BOULDER, objects.MEGABOULDER, objects.CHASINGBOULDER, objects.FLYINGBOULDER}

    def iswall(self) -> bool:
        return self.obj in {objects.HEXPANDINGWALL, objects.VEXPANDINGWALL, objects.BRICK,
                            objects.MAGICWALL, objects.STEEL, objects.STEELWALLBIRTH,
                            objects.BRICKSLOPEDDOWNRIGHT, objects.BRICKSLOPEDDOWNLEFT,
                            objects.BRICKSLOPEDUPRIGHT, objects.BRICKSLOPEDUPLEFT,
                            objects.STEELSLOPEDDOWNLEFT, objects.STEELSLOPEDDOWNRIGHT,
                            objects.STEELSLOPEDUPLEFT, objects.STEELSLOPEDUPRIGHT}

    def isoutbox(self) -> bool:
        return self.obj in (objects.OUTBOXBLINKING, objects.OUTBOXHIDDENOPEN)

    def canfall(self) -> bool:
        return self.obj in {objects.BOULDER, objects.SWEET, objects.DIAMONDKEY, objects.BOMB,
                            objects.IGNITEDBOMB, objects.KEY1, objects.KEY2, objects.KEY3,
                            objects.DIAMOND, objects.MEGABOULDER, objects.SKELETON, objects.NITROFLASK,
                            objects.DIRTBALL, objects.COCONUT, objects.ROCKETLAUNCHER}


# noinspection PyAttributeOutsideInit
class GameState:
    def __init__(self, game) -> None:
        self.game = game
        self.graphics_frame_counter = 0    # will be set via the update() method
        self.fps = 7      # game logic updates 7 fps which is about ~143 ms per frame (original game = ~150 ms)
        self.update_timestep = 1 / self.fps
        self.caveset = caves.CaveSet()
        self.start_level_number = 1
        self.reveal_duration = 3.0
        # set the anim end callbacks:
        objects.ROCKFORDBIRTH.anim_end_callback = self.end_rockfordbirth
        objects.EXPLOSION.anim_end_callback = self.end_explosion
        objects.DIAMONDBIRTH.anim_end_callback = self.end_diamondbirth
        self.highscores = HighScores(self.caveset.name)
        self.playtesting = False
        # and start the game on the title screen.
        self.restart()

    def destroy(self) -> None:
        self.highscores.save()

    def restart(self) -> None:
        audio.silence_audio()
        audio.play_sample("music", repeat=True)
        self.frame = 0
        self.demo_or_highscore = True
        self.game.set_screen_colors(0, 0)
        self.bonusbg_frame = 0    # till what frame should the bg be the bonus sparkly things instead of spaces
        self.level = -1
        self.level_name = self.level_description = "???"
        self.level_won = False
        self.game_status = GameStatus.PLAYING if self.playtesting else GameStatus.WAITING
        self.intermission = False
        self.score = self.extralife_score = 0
        self.cheat_used = self.start_level_number > 1
        self.death_by_voodoo = False
        self.slime_permeability = 0
        self.diamondvalue_initial = self.diamondvalue_extra = 0
        self.diamonds = self.diamonds_needed = 0
        self.lives = 3
        self.idle = {
            "blink": False,
            "tap": False
        }
        self.keys = {
            "diamond": 0,
            "one": True,
            "two": True,
            "three": True
        }
        self.magicwall = {
            "active": False,
            "time": 0.0
        }
        self.amoeba = {
            "size": 0,
            "max": 0,
            "slow": 0.0,
            "enclosed": False,
            "dormant": True,
            "dead": None
        }
        self.timeremaining = datetime.timedelta(0)
        self.timelimit = None   # type: Optional[datetime.datetime]
        self.rockford_cell = self.inbox_cell = self.last_focus_cell = None   # type: Cell
        self.rockford_found_frame = -1
        self.movement = MovementInfo()
        self.flash = 0
        # draw the 'title screen'
        self._create_cave(40, 22)
        self.draw_rectangle(objects.DIRT2, 0, 0, self.width, self.height, objects.EMPTY)
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
                    '*': objects.BRICK,
                    '/': objects.BRICKSLOPEDUPLEFT,
                    '\\': objects.BRICKSLOPEDUPRIGHT,
                    '@': objects.BRICKSLOPEDDOWNLEFT,
                    '$': objects.BRICKSLOPEDDOWNRIGHT,
                    '+': objects.FLYINGDIAMOND,
                    '#': objects.BOULDER,
                    'f': objects.ALTFIREFLY
                }[c]
                self.draw_single(obj, 3 + x, 1 + y)

        self.draw_line(objects.LAVA, 4, self.height - 3, self.width - 8, Direction.RIGHT)
        self.draw_line(objects.DIRT, 3, self.height - 2, self.width - 6, Direction.RIGHT)
        self.draw_single(objects.DIRTSLOPEDUPLEFT, 3, self.height - 3)
        self.draw_single(objects.DIRTSLOPEDUPLEFT, 2, self.height - 2)
        self.draw_single(objects.DIRTSLOPEDUPRIGHT, self.width - 4, self.height - 3)
        self.draw_single(objects.DIRTSLOPEDUPRIGHT, self.width - 3, self.height - 2)

    def _create_cave(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._dirxy = {
            Direction.NOWHERE: 0,
            Direction.UP: -self.width,
            Direction.DOWN: self.width,
            Direction.LEFT: -1,
            Direction.RIGHT: 1,
            Direction.LEFTUP: -self.width - 1,
            Direction.RIGHTUP: -self.width + 1,
            Direction.LEFTDOWN: self.width - 1,
            Direction.RIGHTDOWN: self.width + 1
        }
        self.cave = []   # type: List[Cell]
        for y in range(self.height):
            for x in range(self.width):
                self.cave.append(Cell(objects.EMPTY, x, y))

    def use_bdcff(self, filename: str) -> None:
        self.caveset = caves.CaveSet(filename)
        self.highscores = HighScores(self.caveset.name)

    def use_startlevel(self, levelnumber: int) -> None:
        if levelnumber < 1 or levelnumber > self.caveset.num_caves:
            raise ValueError("invalid level number")
        self.cheat_used = levelnumber > 1
        self.start_level_number = levelnumber

    def use_playtesting(self) -> None:
        # enable playtest mode, used from the editor.
        # skips all intro popups and title screen and immediately drops into the level.
        self.cheat_used = True
        self.playtesting = True
        self.level = self.start_level_number - 1
        self.reveal_duration = 0.0
        self.load_next_level(False)

    def load_level(self, levelnumber: int, level_intro_popup: bool=True) -> None:
        audio.silence_audio()
        self.game.popup_close()    # make sure any open popup won't restore the old tiles
        self.cheat_used = self.cheat_used or (self.start_level_number > 1)
        cave = self.caveset.cave(levelnumber)
        if cave.width < self.game.visible_columns or cave.height < self.game.visible_columns:
            cave.resize(self.game.visible_columns, self.game.visible_rows)
        self._create_cave(cave.width, cave.height)
        self.game.create_canvas_playfield_and_tilesheet(cave.width, cave.height)
        self.level_name = cave.name
        self.level_description = cave.description
        self.intermission = cave.intermission
        self.wraparound = cave.wraparound
        level_intro_popup = level_intro_popup and levelnumber != self.level
        self.level = levelnumber
        self.level_won = False
        self.frame = 0
        self.bonusbg_frame = 0
        self.game_status = GameStatus.PLAYING if self.playtesting else GameStatus.REVEALING_PLAY
        self.reveal_frame = 0 if self.playtesting else self.fps * self.reveal_duration
        self.flash = 0
        self.diamonds = 0
        self.diamonds_needed = cave.diamonds_required
        self.diamondvalue_initial = cave.diamondvalue_normal
        self.diamondvalue_extra = cave.diamondvalue_extra
        self.timeremaining = datetime.timedelta(seconds=cave.time)
        self.slime_permeability = cave.slime_permeability
        self.death_by_voodoo = False
        self.timelimit = None   # will be set as soon as Rockford spawned
        self.idle["blink"] = self.idle["tap"] = False
        self.magicwall["active"] = False
        self.magicwall["time"] = cave.magicwall_millingtime / self.update_timestep
        self.rockford_cell = None     # the cell where Rockford currently is
        self.inbox_cell = self.last_focus_cell = None
        self.rockford_found_frame = 0
        self.movement = MovementInfo()
        self.amoeba = {
            "size": 0,
            "max": cave.amoebafactor * self.width * self.height,
            "slow": cave.amoeba_slowgrowthtime / self.update_timestep,
            "enclosed": False,
            "dormant": True,
            "dead": None
        }
        # clear the previous cave data and replace with data from new cave
        self.game.clear_tilesheet()
        self.draw_rectangle(objects.STEEL, 0, 0, self.width, self.height, objects.STEEL)
        for i, (gobj, direction) in enumerate(cave.map):
            y, x = divmod(i, cave.width)
            self.draw_single(gobj, x, y, initial_direction=direction)
        self.game.create_colored_tiles(cave.colors)
        self.game.set_screen_colors(cave.colors.rgb_screen, cave.colors.rgb_border)
        self.check_initial_amoeba_dormant()

        def prepare_reveal() -> None:
            self.game.prepare_reveal()
            audio.play_sample("cover", repeat=True)

        if level_intro_popup and self.level_description:
            audio.play_sample("diamond2")
            self.game.popup("{:s}\n\n{:s}".format(self.level_name, self.level_description), on_close=prepare_reveal)
        elif not self.playtesting:
            prepare_reveal()

    def check_initial_amoeba_dormant(self) -> None:
        if self.amoeba["dormant"]:
            for cell in self.cave:
                if cell.isamoeba():
                    if self.get(cell, Direction.UP).isempty() or self.get(cell, Direction.DOWN).isempty() \
                            or self.get(cell, Direction.RIGHT).isempty() or self.get(cell, Direction.LEFT).isempty() \
                            or self.get(cell, Direction.UP).isdirt() or self.get(cell, Direction.DOWN).isdirt() \
                            or self.get(cell, Direction.RIGHT).isdirt() or self.get(cell, Direction.LEFT).isdirt():
                        # amoeba can grow, so is not dormant
                        self.amoeba["dormant"] = False
                        audio.play_sample("amoeba", repeat=True)  # start playing amoeba sound
                        return

    def tile_music_ended(self) -> None:
        # do one of two things: play the demo, or show the highscore list for a short time
        self.demo_or_highscore = (not self.demo_or_highscore) and self.caveset.cave_demo is not None
        if self.demo_or_highscore:
            self.start_demo()
        else:
            self.show_highscores()

    def start_demo(self) -> None:
        if self.game_status == GameStatus.WAITING:
            if self.caveset.cave_demo:
                self.level = 0
                self.load_next_level(intro_popup=False)
                self.game_status = GameStatus.REVEALING_DEMO     # the sound is already being played.
                self.reveal_frame = self.frame + self.fps * self.reveal_duration
                self.movement = DemoMovementInfo(self.caveset.cave_demo)  # is reset to regular handling when demo ends/new level
            else:
                self.game.popup("This cave set doesn't have a demo.", duration=3)

    def show_highscores(self) -> None:
        def reset_game_status():
            self.game_status = GameStatus.WAITING
        if self.game_status == GameStatus.WAITING:
            self.game_status = GameStatus.HIGHSCORE
            if self.game.smallwindow:
                smallname = self.caveset.name.replace('.', '').replace("Vol", "").replace("vol", "")[:16]
                txt = [smallname, "\x0e\x0e\x0eHigh Scores\x0e\x0e"]
                for pos, (score, name) in enumerate(self.highscores, start=1):
                    txt.append("{:d} {:\x0f<7s} {:_>6d}".format(pos, name, score))
            else:
                txt = ["\x05 " + self.caveset.name + " \x05", "\n\x0e\x0e\x0e High Scores \x0e\x0e\x0e\n-------------------\n"]
                for pos, (score, name) in enumerate(self.highscores, start=1):
                    txt.append("\x0f{:d}\x0f {:\x0f<7s}\x0f {:_>6d}".format(pos, name, score))
            self.game.popup("\n".join(txt), 12, on_close=reset_game_status)

    def pause(self) -> None:
        if self.game_status == GameStatus.PLAYING:
            self.time_paused = datetime.datetime.now()
            self.game_status = GameStatus.PAUSED
        elif self.game_status == GameStatus.PAUSED:
            if self.timelimit:
                pause_duration = datetime.datetime.now() - self.time_paused
                self.timelimit = self.timelimit + pause_duration
            self.game_status = GameStatus.PLAYING

    def suicide(self) -> None:
        if self.rockford_cell:
            self.explode(self.rockford_cell)
        else:
            self.life_lost()

    def cheat_skip_level(self) -> None:
        if self.game_status in (GameStatus.PLAYING, GameStatus.PAUSED):
            self.cheat_used = True
            self.load_level(self.level % self.caveset.num_caves + 1)

    def draw_rectangle(self, obj: objects.GameObject, x1: int, y1: int, width: int, height: int,
                       fillobject: objects.GameObject=None) -> None:
        self.draw_line(obj, x1, y1, width, Direction.RIGHT)
        self.draw_line(obj, x1, y1 + height - 1, width, Direction.RIGHT)
        self.draw_line(obj, x1, y1 + 1, height - 2, Direction.DOWN)
        self.draw_line(obj, x1 + width - 1, y1 + 1, height - 2, Direction.DOWN)
        if fillobject is not None:
            for y in range(y1 + 1, y1 + height - 1):
                self.draw_line(fillobject, x1 + 1, y, width - 2, Direction.RIGHT)

    def draw_line(self, obj: objects.GameObject, x: int, y: int, length: int, direction: Direction) -> None:
        dx, dy = {
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0),
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFTUP: (-1, -1),
            Direction.RIGHTUP: (1, -1),
            Direction.LEFTDOWN: (-1, 1),
            Direction.RIGHTDOWN: (1, 1)
        }[direction]
        for _ in range(length):
            self.draw_single(obj, x, y)
            x += dx
            y += dy

    def draw_single(self, obj: objects.GameObject, x: int, y: int, initial_direction: Direction=Direction.NOWHERE) -> None:
        self.draw_single_cell(self.cave[x + y * self.width], obj, initial_direction)

    def draw_single_cell(self, cell: Cell, obj: objects.GameObject, initial_direction: Direction=Direction.NOWHERE) -> None:
        cell.obj = obj
        cell.direction = initial_direction
        cell.frame = self.frame   # make sure the new cell is not immediately scanned
        cell.anim_start_gfx_frame = self.graphics_frame_counter   # this makes sure that (new) anims start from the first frame
        cell.falling = False
        if obj is objects.MAGICWALL:
            if not self.magicwall["active"]:
                obj = objects.BRICK
        self.game.set_canvas_tile(cell.x, cell.y, obj)
        # animation is handled by the graphics refresh

    def clear_cell(self, cell: Cell) -> None:
        self.draw_single_cell(cell, objects.BONUSBG if self.bonusbg_frame > self.frame else objects.EMPTY)

    def get(self, cell: Cell, direction: Direction=Direction.NOWHERE) -> Cell:
        # retrieve the cell relative to the given cell
        # deals with wrapping around the up/bottom edge
        cell_index = cell.x + cell.y * self.width + self._dirxy[direction]
        if self.wraparound:
            if cell_index >= len(self.cave):
                cell_index %= self.width        # wrap around lower edge
            elif cell_index < 0:
                cell_index += len(self.cave)    # wrap around upper edge
        elif cell_index < 0 or cell_index >= len(self.cave):
            return Cell(objects.STEEL, cell.x, cell.y)   # treat upper/lower edge as steel wall
        return self.cave[cell_index]

    def move(self, cell: Cell, direction: Direction=Direction.NOWHERE) -> Cell:
        # move the object in the cell to the given relative direction
        if direction == Direction.NOWHERE:
            return None  # no movement...
        newcell = self.get(cell, direction)
        self.draw_single_cell(newcell, cell.obj)
        newcell.falling = cell.falling
        newcell.direction = cell.direction
        self.clear_cell(cell)
        cell.falling = False
        cell.direction = Direction.NOWHERE
        return newcell

    def push(self, cell: Cell, direction: Direction=Direction.NOWHERE) -> Cell:
        # try to push the thing in the given direction
        pushedcell = self.get(cell, direction)
        targetcell = self.get(pushedcell, direction)
        if targetcell.isempty():
            if random.randint(1, 8) == 1:
                self.move(pushedcell, direction)
                self.fall_sound(targetcell, pushing=True)
                if not self.movement.grab:
                    cell = self.move(cell, direction)
        self.movement.pushing = True
        return cell

    def do_magic(self, cell: Cell) -> None:
        # something (diamond, boulder) is falling on a magic wall
        if self.magicwall["time"] > 0:
            if not self.magicwall["active"]:
                # magic wall activates! play sound. Will be silenced once the milling timer runs out.
                audio.play_sample("magic_wall", repeat=True)
            self.magicwall["active"] = True
            obj = cell.obj
            self.clear_cell(cell)
            cell_under_wall = self.get(self.get(cell, Direction.DOWN), Direction.DOWN)
            if cell_under_wall.isempty():
                if obj is objects.DIAMOND:
                    self.draw_single_cell(cell_under_wall, objects.BOULDER)
                    audio.play_sample("boulder")
                elif obj is objects.BOULDER:
                    self.draw_single_cell(cell_under_wall, objects.DIAMOND)
                    audio.play_sample("diamond" + str(random.randint(1, 6)))
                cell_under_wall.falling = True
        else:
            # magic wall is disabled, stuff falling on it just disappears (a sound is already played)
            self.clear_cell(cell)

    def do_slime(self, cell: Cell) -> None:
        # something (diamond, boulder) is falling on a slime
        if random.random() < self.slime_permeability:
            cell_under_wall = self.get(self.get(cell, Direction.DOWN), Direction.DOWN)
            if cell_under_wall.isempty():
                audio.play_sample("slime")
                obj = cell.obj
                self.clear_cell(cell)
                self.draw_single_cell(cell_under_wall, obj)
                cell_under_wall.falling = True

    def cells_with_animations(self) -> List[Cell]:
        return [cell for cell in self.cave if cell.obj.sframes]

    def update(self, graphics_frame_counter: int) -> None:
        self.graphics_frame_counter = graphics_frame_counter    # we store this to properly sync up animation frames
        self.frame_start()
        if self.game_status in (GameStatus.REVEALING_DEMO, GameStatus. REVEALING_PLAY):
            if self.reveal_frame > self.frame:
                return
            # reveal period has ended
            audio.silence_audio("cover")
            self.game.tilesheet.all_dirty()  # force full redraw
            if self.game_status == GameStatus.REVEALING_DEMO:
                self.game_status = GameStatus.DEMO
            elif self.game_status == GameStatus.REVEALING_PLAY:
                self.game_status = GameStatus.PLAYING
        if self.game_status not in (GameStatus.PLAYING, GameStatus.DEMO):
            return
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
                    elif cell.obj is objects.INBOXBLINKING:
                        self.update_inbox(cell)
                    elif cell.isrockford():
                        self.update_rockford(cell)
                    elif cell.isamoeba():
                        self.update_amoeba(cell)
                    elif cell.obj is objects.OUTBOXCLOSED:
                        self.update_outboxclosed(cell)
                    elif cell.obj is objects.OUTBOXHIDDEN:
                        self.update_outboxhidden(cell)
                    elif cell.obj is objects.BONUSBG:
                        if self.bonusbg_frame < self.frame:
                            self.draw_single_cell(cell, objects.EMPTY)
                    elif cell.obj in (objects.HEXPANDINGWALL, objects.VEXPANDINGWALL):
                        self.update_expandingwall(cell)
        self.frame_end()

    def frame_start(self) -> None:
        # called at beginning of every game logic update
        self.frame += 1
        self.movement.pushing = False
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

    def frame_end(self) -> None:
        # called at end of every game logic update
        if self.amoeba["dead"] is None:
            if self.amoeba["enclosed"] and not self.amoeba["dormant"]:
                self.amoeba["dead"] = objects.DIAMOND
                audio.silence_audio("amoeba")
                audio.play_sample("diamond1")
            elif self.amoeba["size"] > self.amoeba["max"]:
                self.amoeba["dead"] = objects.BOULDER
                audio.silence_audio("amoeba")
                audio.play_sample("boulder")
            elif self.amoeba["slow"] > 0:
                self.amoeba["slow"] -= 1
        if self.magicwall["active"]:
            self.magicwall["time"] -= 1
            still_magic = self.magicwall["time"] > 0
            if self.magicwall["active"] and not still_magic:
                # magic wall has stopped! stop playing the milling sound
                audio.silence_audio("magic_wall")
            self.magicwall["active"] = still_magic
        if self.timelimit and not self.level_won and self.rockford_cell:
            secs_before = self.timeremaining.seconds
            self.timeremaining = self.timelimit - datetime.datetime.now()
            secs_after = self.timeremaining.seconds
            if secs_after <= 0:
                self.timeremaining = datetime.timedelta(0)
            if secs_after != secs_before and 1 <= secs_after <= 9:
                audio.play_sample("timeout" + str(10 - secs_after))
        if self.level_won:
            if self.timeremaining.seconds > 0:
                add_score = min(self.timeremaining.seconds, 5)
                self.score += add_score
                self.extralife_score += add_score
                self.check_extralife_score()
                self.timeremaining -= datetime.timedelta(seconds=add_score)
            else:
                if self.game_status == GameStatus.DEMO:
                    self.restart()  # go back to title screen when demo finishes
                else:
                    self.load_next_level()
        elif self.timelimit and self.update_timestep * (self.frame - self.rockford_found_frame) > 10:
            # after 10 seconds with dead rockford we reload the current level
            self.life_lost()

    def focus_cell(self) -> Cell:
        focus_cell = self.rockford_cell or self.inbox_cell or self.last_focus_cell
        if focus_cell:
            self.last_focus_cell = focus_cell
            return focus_cell
        # search for the inbox when the game isn't running yet
        if self.level > 0:
            for cell in self.cave:
                if cell.obj is objects.INBOXBLINKING:
                    self.last_focus_cell = cell
                    break
        return self.last_focus_cell

    def life_lost(self) -> None:
        if self.intermission:
            self.load_next_level()  # don't lose a life, instead skip out of the intermission.
            return
        self.lives = max(0, self.lives - 1)
        if self.lives > 0:
            self.load_level(self.level)  # retry current level
        else:
            self.stop_game(GameStatus.LOST)

    def stop_game(self, status: GameStatus) -> None:
        self.game_status = status
        if self.rockford_cell:
            self.clear_cell(self.rockford_cell)
        self.rockford_found_frame = 0
        if status == GameStatus.LOST:
            audio.play_sample("game_over")
            popuptxt = "Game Over.\n\nScore: {:d}".format(self.score)
        elif status == GameStatus.WON:
            self.lives = 0
            audio.play_sample("extra_life")
            popuptxt = "Congratulations, you finished the game!\n\nScore: {:d}".format(self.score)
        else:
            popuptxt = "??invalid status??"
        if self.cheat_used or self.start_level_number > 1:
            popuptxt += "\n\nYou cheated, so the score is not recorded."
            score_pos = 0
        else:
            score_pos = self.highscores.score_pos(self.score)
            if score_pos:
                popuptxt += "\n\nYou got a new #{:d} high score!".format(score_pos)

        def ask_highscore_name(score_pos, score):
            if score_pos:
                name = self.game.ask_highscore_name(score_pos, score)
                self.highscores.add(name, score)
        self.game.popup(popuptxt, on_close=lambda: ask_highscore_name(score_pos, self.score))

    def load_next_level(self, intro_popup: bool=True) -> None:
        level = self.level + 1
        if level > self.caveset.num_caves:
            self.stop_game(GameStatus.WON)
        else:
            audio.silence_audio()
            self.load_level(level, level_intro_popup=intro_popup)

    def update_canfall(self, cell: Cell) -> None:
        # if the cell below this one is empty, or slime, the object starts to fall
        # (in case of slime, it only falls through ofcourse if the space below the slime is empty)
        cellbelow = self.get(cell, Direction.DOWN)
        if cellbelow.isempty():
            if not cell.falling:
                self.fall_sound(cell)
                cell.falling = True
                self.update_falling(cell)
        elif cellbelow.isslime():
            cell.falling = True
        elif cellbelow.isrounded():
            if self.get(cell, Direction.LEFT).isempty() and self.get(cell, Direction.LEFTDOWN).isempty():
                self.move(cell, Direction.LEFT).falling = True
            elif self.get(cell, Direction.RIGHT).isempty() and self.get(cell, Direction.RIGHTDOWN).isempty():
                self.move(cell, Direction.RIGHT).falling = True

    def update_falling(self, cell: Cell) -> None:
        # let the object fall down, explode stuff if explodable!
        cellbelow = self.get(cell, Direction.DOWN)
        if cellbelow.isempty():
            # cell below is empty, move down and continue falling
            cell = self.move(cell, Direction.DOWN)
        elif cellbelow.obj is objects.VOODOO and cell.obj is objects.DIAMOND:
            self.clear_cell(cell)
            self.collect_diamond()  # voodoo doll catches falling diamond
        elif cellbelow.isexplodable():
            self.explode(cell, Direction.DOWN)
        elif cellbelow.ismagic():
            self.do_magic(cell)
        elif cellbelow.isslime():
            self.do_slime(cell)
        elif cellbelow.isrounded() and self.get(cell, Direction.LEFT).isempty() and self.get(cell, Direction.LEFTDOWN).isempty():
            self.fall_sound(cell)
            self.move(cell, Direction.LEFT)
        elif cellbelow.isrounded() and self.get(cell, Direction.RIGHT).isempty() and self.get(cell, Direction.RIGHTDOWN).isempty():
            self.fall_sound(cell)
            self.move(cell, Direction.RIGHT)
        else:
            cell.falling = False  # falling was blocked by something
            self.fall_sound(cell)

    def update_firefly(self, cell: Cell) -> None:
        # if it hits Rockford or Amoeba it explodes
        # tries to rotate 90 degrees left and move to empty cell in new or original direction
        # if not possible rotate 90 right and wait for next update
        newdir = cell.direction.rotate90left()
        if self.get(cell, Direction.UP).isrockford() or self.get(cell, Direction.DOWN).isrockford() \
                or self.get(cell, Direction.LEFT).isrockford() or self.get(cell, Direction.RIGHT).isrockford():
            self.explode(cell)
        elif self.get(cell, Direction.UP).isamoeba() or self.get(cell, Direction.DOWN).isamoeba() \
                or self.get(cell, Direction.LEFT).isamoeba() or self.get(cell, Direction.RIGHT).isamoeba():
            self.explode(cell)
        elif self.get(cell, Direction.UP).obj is objects.VOODOO or self.get(cell, Direction.DOWN).obj is objects.VOODOO \
                or self.get(cell, Direction.LEFT).obj is objects.VOODOO or self.get(cell, Direction.RIGHT).obj is objects.VOODOO:
            self.explode(cell)
            self.death_by_voodoo = True
        elif self.get(cell, newdir).isempty():
            self.move(cell, newdir).direction = newdir
        elif self.get(cell, cell.direction).isempty():
            self.move(cell, cell.direction)
        else:
            cell.direction = cell.direction.rotate90right()

    def update_butterfly(self, cell: Cell) -> None:
        # same as firefly except butterflies rotate in the opposite direction
        newdir = cell.direction.rotate90right()
        if self.get(cell, Direction.UP).isrockford() or self.get(cell, Direction.DOWN).isrockford() \
                or self.get(cell, Direction.LEFT).isrockford() or self.get(cell, Direction.RIGHT).isrockford():
            self.explode(cell)
        elif self.get(cell, Direction.UP).isamoeba() or self.get(cell, Direction.DOWN).isamoeba() \
                or self.get(cell, Direction.LEFT).isamoeba() or self.get(cell, Direction.RIGHT).isamoeba():
            self.explode(cell)
        elif self.get(cell, Direction.UP).obj is objects.VOODOO or self.get(cell, Direction.DOWN).obj is objects.VOODOO \
                or self.get(cell, Direction.LEFT).obj is objects.VOODOO or self.get(cell, Direction.RIGHT).obj is objects.VOODOO:
            self.explode(cell)
            self.death_by_voodoo = True
        elif self.get(cell, newdir).isempty():
            self.move(cell, newdir).direction = newdir
        elif self.get(cell, cell.direction).isempty():
            self.move(cell, cell.direction)
        else:
            cell.direction = cell.direction.rotate90left()

    def update_inbox(self, cell: Cell) -> None:
        # after 4 blinks (=2 seconds), Rockford spawns in the inbox.
        self.inbox_cell = cell
        if self.update_timestep * self.frame > (2.0 + self.reveal_duration):
            self.draw_single_cell(cell, objects.ROCKFORDBIRTH)
            audio.play_sample("crack")

    def update_outboxclosed(self, cell: Cell) -> None:
        if self.rockford_found_frame <= 0:
            return   # do nothing if rockford hasn't appeared yet
        if self.diamonds >= self.diamonds_needed:
            if cell.obj is not objects.OUTBOXBLINKING:
                audio.play_sample("crack")
            self.draw_single_cell(cell, objects.OUTBOXBLINKING)

    def update_outboxhidden(self, cell: Cell) -> None:
        if self.rockford_found_frame <= 0:
            return   # do nothing if rockford hasn't appeared yet
        if self.diamonds >= self.diamonds_needed:
            if cell.obj is not objects.OUTBOXHIDDENOPEN:
                audio.play_sample("crack")
            self.draw_single_cell(cell, objects.OUTBOXHIDDENOPEN)

    def update_amoeba(self, cell: Cell) -> None:
        if self.amoeba["dead"] is not None:
            self.draw_single_cell(cell, self.amoeba["dead"])
        else:
            self.amoeba["size"] += 1
            if self.get(cell, Direction.UP).isempty() or self.get(cell, Direction.DOWN).isempty() \
                    or self.get(cell, Direction.RIGHT).isempty() or self.get(cell, Direction.LEFT).isempty() \
                    or self.get(cell, Direction.UP).isdirt() or self.get(cell, Direction.DOWN).isdirt() \
                    or self.get(cell, Direction.RIGHT).isdirt() or self.get(cell, Direction.LEFT).isdirt():
                self.amoeba["enclosed"] = False
                if self.amoeba["dormant"]:
                    # amoeba can grow, so is not dormant anymore
                    self.amoeba["dormant"] = False
                    audio.play_sample("amoeba", repeat=True)  # start playing amoeba sound
            if self.timelimit:
                grow = random.randint(1, 128) < 4 if self.amoeba["slow"] else random.randint(1, 4) == 1
                direction = random.choice([Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT])
                if grow and (self.get(cell, direction).isdirt() or self.get(cell, direction).isempty()):
                    self.draw_single_cell(self.get(cell, direction), cell.obj)

    def update_rockford(self, cell: Cell) -> None:
        self.rockford_cell = cell
        self.rockford_found_frame = self.frame
        if self.level_won:
            return
        if self.timeremaining.seconds <= 0 or self.death_by_voodoo:
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
                elif self.movement.direction in (Direction.LEFT, Direction.RIGHT) and targetcell.isboulder():
                    self.push(cell, self.movement.direction)
            elif targetcell.isempty():
                audio.play_sample("walk_empty")
                cell = self.move(cell, self.movement.direction)
            elif targetcell.isdirt():
                audio.play_sample("walk_dirt")
                cell = self.move(cell, self.movement.direction)
            elif targetcell.isboulder() and self.movement.direction in (Direction.LEFT, Direction.RIGHT):
                cell = self.push(cell, self.movement.direction)
            elif targetcell.isdiamond():
                self.collect_diamond()
                cell = self.move(cell, self.movement.direction)
            elif targetcell.isoutbox():
                cell = self.move(cell, self.movement.direction)
                self.level_won = True   # exit found!
                audio.silence_audio()
                audio.play_sample("finished")
                self.movement.stop_all()
            self.movement.move_done()
        if cell is not self.rockford_cell:
            # rockford has moved, tweak his walk animation so it keeps going and is not reset to the first anim frame
            cell.anim_start_gfx_frame = 0
        self.rockford_cell = cell

    def update_expandingwall(self, cell: Cell) -> None:
        # cell is an expanding wall (horizontally or vertically)
        if cell.obj is objects.HEXPANDINGWALL:
            left = self.get(cell, Direction.LEFT)
            right = self.get(cell, Direction.RIGHT)
            if left.isempty():
                self.draw_single_cell(left, objects.HEXPANDINGWALL)
                self.fall_sound(cell, pushing=True)
            if right.isempty():
                self.draw_single_cell(right, objects.HEXPANDINGWALL)
                self.fall_sound(cell, pushing=True)
        elif cell.obj is objects.VEXPANDINGWALL:
            up = self.get(cell, Direction.UP)
            down = self.get(cell, Direction.DOWN)
            if up.isempty():
                self.draw_single_cell(up, objects.VEXPANDINGWALL)
                self.fall_sound(cell, pushing=True)
            if down.isempty():
                self.draw_single_cell(down, objects.VEXPANDINGWALL)
                self.fall_sound(cell, pushing=True)

    def update_scorebar(self) -> None:
        # draw the score bar.
        # note: the following is a complex score bar including keys, but those are not used in the C64 boulderdash:
        # text = ("\x08{lives:2d}  \x0c {keys:02d}\x7f\x7f\x7f  {diamonds:<10s}  {time:s}  $ {score:06d}".format(
        #     lives=self.lives,
        #     time=str(self.timeremaining)[3:7],
        #     score=self.score,
        #     diamonds="\x0e {:02d}/{:02d}".format(self.diamonds, self.diamonds_needed),
        #     keys=self.keys["diamond"]
        # )).ljust(width)
        # self.game.tilesheet_score.set_tiles(0, 0, tiles.text2tiles(text))
        # if self.keys["one"]:
        #     self.game.tilesheet_score[9, 0] = objects.KEY1.spritex + objects.KEY1.spritey * self.game.tile_image_numcolumns
        # if self.keys["two"]:
        #     self.game.tilesheet_score[10, 0] = objects.KEY2.spritex + objects.KEY2.spritey * self.game.tile_image_numcolumns
        # if self.keys["three"]:
        #     self.game.tilesheet_score[11, 0] = objects.KEY3.spritex + objects.KEY3.spritey * self.game.tile_image_numcolumns
        width = self.game.tilesheet_score.width
        if self.level < 1:
            # level has not been loaded yet (we're still at the title screen)
            if self.game.smallwindow and self.game.c64colors:
                self.game.set_scorebar_tiles(0, 0, tiles.text2tiles("Welcome to Boulder Caves 'authentic'".center(width)))
            else:
                self.game.set_scorebar_tiles(0, 0, tiles.text2tiles("Welcome to Boulder Caves".center(width)))
            self.game.set_scorebar_tiles(0, 1, tiles.text2tiles("F1\x04New game! F4\x04Scores F9\x04Demo".center(width)))
            if not self.game.smallwindow:
                left = [objects.MEGABOULDER.tile(), objects.FLYINGDIAMOND.tile(), objects.DIAMOND.tile(), objects.ROCKFORD.pushleft.tile()]
                right = [objects.ROCKFORD.pushright.tile(), objects.DIAMOND.tile(), objects.FLYINGDIAMOND.tile(), objects.MEGABOULDER.tile()]
                self.game.set_scorebar_tiles(0, 0, left)
                self.game.set_scorebar_tiles(0, 1, left)
                self.game.set_scorebar_tiles(width - len(right), 0, right)
                self.game.set_scorebar_tiles(width - len(right), 1, right)
            return
        text = ("\x08{lives:2d}   {normal:d}\x0e{extra:d}  {diamonds:<10s}  {time:s}  $ {score:06d}".format(
            lives=self.lives,
            time=str(self.timeremaining)[3:7],
            score=self.score,
            normal=self.diamondvalue_initial,
            extra=self.diamondvalue_extra,
            diamonds="{:02d}/{:02d}".format(self.diamonds, self.diamonds_needed),
        )).ljust(width)
        self.game.tilesheet_score.set_tiles(0, 0, tiles.text2tiles(text))
        if self.game_status == GameStatus.WON:
            line_tiles = tiles.text2tiles("\x0e  C O N G R A T U L A T I O N S  \x0e".center(width))
        elif self.game_status == GameStatus.LOST:
            line_tiles = tiles.text2tiles("\x0b  G A M E   O V E R  \x0b".center(width))
        elif self.game_status == GameStatus.PAUSED:
            line_tiles = tiles.text2tiles("\x08  P A U S E D  \x08".center(width))
        else:
            if self.level_name.lower().startswith(("cave ", "intermission ")):
                fmt = "{:s}"
            else:
                fmt = "Bonus: {:s}" if self.intermission else "Cave: {:s}"
            if self.game_status == GameStatus.DEMO:
                fmt += " [Demo]"
            if self.playtesting:
                fmt += " [Testing]"
            line_tiles = tiles.text2tiles(fmt.format(self.level_name).center(width))
        self.game.set_scorebar_tiles(0, 1, line_tiles[:40])  # line 2

    def fall_sound(self, cell: Cell, pushing: bool=False) -> None:
        if cell.isboulder() or cell.iswall():
            if pushing:
                audio.play_sample("box_push")
            else:
                audio.play_sample("boulder")
        elif cell.isdiamond():
            audio.play_sample("diamond" + str(random.randint(1, 6)))

    def collect_diamond(self) -> None:
        audio.silence_audio("collect_diamond")
        audio.play_sample("collect_diamond")
        self.diamonds += 1
        points = self.diamondvalue_extra if self.diamonds > self.diamonds_needed else self.diamondvalue_initial
        self.score += points
        self.extralife_score += points
        if self.diamonds >= self.diamonds_needed and not self.flash:
            self.flash = self.frame + self.fps // 2
        self.check_extralife_score()

    def check_extralife_score(self) -> None:
        # extra life every 500 points
        if self.extralife_score >= 500:
            self.extralife_score -= 500
            self.add_extra_life()

    def add_extra_life(self) -> None:
        if self.lives < 9:   # 9 is the maximum number of lives
            self.lives += 1
            audio.play_sample("extra_life")
            for cell in self.cave:
                if cell.obj is objects.EMPTY:
                    self.draw_single_cell(cell, objects.BONUSBG)
                    self.bonusbg_frame = self.frame + self.fps * 6   # sparkle for 6 seconds

    def add_extra_time(self, seconds: float) -> None:
        self.timelimit += datetime.timedelta(seconds=seconds)

    def end_rockfordbirth(self, cell: Cell) -> None:
        # rockfordbirth eventually creates the real Rockford and starts the level timer.
        if self.game_status in (GameStatus.PLAYING, GameStatus.DEMO):
            self.draw_single_cell(cell, objects.ROCKFORD)
            self.timelimit = datetime.datetime.now() + self.timeremaining
            self.inbox_cell = None
            if self.diamonds_needed <= 0:
                # need to subtract this from the current number of diamonds in the cave
                numdiamonds = sum([1 for c in self.cave if c.isdiamond()])
                self.diamonds_needed = max(0, numdiamonds + self.diamonds_needed)

    def end_explosion(self, cell: Cell) -> None:
        # a normal explosion ends with an empty cell
        self.clear_cell(cell)

    def end_diamondbirth(self, cell: Cell) -> None:
        # diamondbirth ends with a diamond
        self.draw_single_cell(cell, objects.DIAMOND)

    def explode(self, cell: Cell, direction: Direction=Direction.NOWHERE) -> None:
        explosion_sample = "explosion"
        explosioncell = self.get(cell, direction)
        if explosioncell.isbutterfly():
            explode_obj = objects.DIAMONDBIRTH
        else:
            explode_obj = objects.EXPLOSION
        if explosioncell.obj is objects.VOODOO:
            explosion_sample = "voodoo_explosion"
            self.draw_single_cell(explosioncell, objects.GRAVESTONE)
        else:
            self.draw_single_cell(explosioncell, explode_obj)
        for direction in Direction:
            if direction == Direction.NOWHERE:
                continue
            cell = self.get(explosioncell, direction)
            if cell.isconsumable():
                if cell.obj is objects.VOODOO:
                    explosion_sample = "voodoo_explosion"
                    self.draw_single_cell(cell, objects.GRAVESTONE)
                else:
                    self.draw_single_cell(cell, explode_obj)
        audio.play_sample(explosion_sample)


class MovementInfo:
    def __init__(self) -> None:
        self.direction = Direction.NOWHERE
        self.lastXdir = Direction.NOWHERE
        self.up = self.down = self.left = self.right = False
        self.grab = False           # is rockford grabbing something?
        self.pushing = False        # is rockford pushing something?

    @property
    def moving(self) -> bool:
        return bool(self.direction != Direction.NOWHERE)

    def start_up(self) -> None:
        self.direction = Direction.UP
        self.up = True

    def start_down(self) -> None:
        self.direction = Direction.DOWN
        self.down = True

    def start_left(self) -> None:
        self.direction = Direction.LEFT
        self.left = True
        self.lastXdir = Direction.LEFT

    def start_right(self) -> None:
        self.direction = Direction.RIGHT
        self.right = True
        self.lastXdir = Direction.RIGHT

    def start_grab(self) -> None:
        self.grab = True

    def stop_all(self) -> None:
        self.grab = self.up = self.down = self.left = self.right = False
        self.direction = None

    def stop_grab(self) -> None:
        self.grab = False

    def stop_up(self) -> None:
        self.up = False
        self.direction = self.where() if self.direction == Direction.UP else self.direction

    def stop_down(self) -> None:
        self.down = False
        self.direction = self.where() if self.direction == Direction.DOWN else self.direction

    def stop_left(self) -> None:
        self.left = False
        self.direction = self.where() if self.direction == Direction.LEFT else self.direction

    def stop_right(self) -> None:
        self.right = False
        self.direction = self.where() if self.direction == Direction.RIGHT else self.direction

    def where(self) -> Direction:
        if self.up:
            return Direction.UP
        elif self.down:
            return Direction.DOWN
        elif self.left:
            return Direction.LEFT
        elif self.right:
            return Direction.RIGHT
        else:
            return Direction.NOWHERE

    def move_done(self) -> None:
        pass


class DemoMovementInfo(MovementInfo):
    # movement controller that doesn't respond to user input,
    # and instead plays a prerecorded sequence of moves.
    def __init__(self, demo_moves: Sequence[int]) -> None:
        super().__init__()
        self.demo_direction = Direction.NOWHERE
        self.demo_moves = self.decompressed(demo_moves)
        self.demo_finished = False

    @property
    def moving(self) -> bool:
        return True

    @property
    def direction(self) -> Direction:
        return self.demo_direction

    @direction.setter
    def direction(self, value: Direction) -> None:
        pass

    def move_done(self) -> None:
        try:
            self.demo_direction = next(self.demo_moves)
            if self.demo_direction == Direction.LEFT:
                self.lastXdir = Direction.LEFT
            elif self.demo_direction == Direction.RIGHT:
                self.lastXdir = Direction.RIGHT
        except StopIteration:
            self.demo_finished = True
            self.demo_direction = Direction.NOWHERE

    def decompressed(self, demo: Sequence[int]) -> Generator[Direction, None, None]:
        for step in demo:
            d = step & 0x0f
            if d == 0:
                raise StopIteration
            direction = {
                0x0f: Direction.NOWHERE,
                0x07: Direction.RIGHT,
                0x0b: Direction.LEFT,
                0x0d: Direction.DOWN,
                0x0e: Direction.UP
            }[d]
            for _ in range(step >> 4):
                yield direction
