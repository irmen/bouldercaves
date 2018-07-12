"""
Boulder Caves - a Boulder Dash (tm) clone.

This module contains the GUI window logic, handles keyboard input
and screen drawing via tkinter bitmaps.

Written by Irmen de Jong (irmen@razorvine.net)
License: GNU GPL 3.0, see LICENSE
"""

import os
import random
import sys
import math
import tkinter
import tkinter.messagebox
from tkinter import simpledialog
import pkgutil
import time
from typing import Tuple, Sequence, List, Iterable, Callable, Optional
from .gamelogic import GameState, Direction, GameStatus, HighScores
from .caves import colorpalette, Palette
from . import audio, synthsamples, tiles, objects, bdcff

__version__ = "4.4"


class BoulderWindow(tkinter.Tk):
    update_fps = 30
    update_timestep = 1 / update_fps
    visible_columns = 40
    visible_rows = 22
    scalexy = 2.0

    def __init__(self, title: str, fps: int=30, scale: float=2, c64colors: bool=False, smallwindow: bool=False) -> None:
        scale = scale / 2
        self.smallwindow = smallwindow
        if smallwindow:
            if int(scale) != scale:
                raise ValueError("Scaling must be integer, not a fraction, when using the small scrolling window")
            self.visible_columns = 20
            self.visible_rows = 12
        super().__init__()
        self.update_fps = fps
        self.update_timestep = 1 / fps
        self.scalexy = scale
        self.c64colors = c64colors
        if self.visible_columns <= 4 or self.visible_columns > 100 or self.visible_rows <= 4 or self.visible_rows > 100:
            raise ValueError("invalid visible size")
        if self.scalexy not in (1, 1.5, 2, 2.5, 3):
            raise ValueError("invalid scalexy factor", self.scalexy)
        self.geometry("+200+40")
        self.resizable(0, 0)
        self.configure(borderwidth=16, background="black")
        self.wm_title(title)
        self.appicon = tkinter.PhotoImage(data=pkgutil.get_data(__name__, "gfx/gdash_icon_48.gif"))
        self.wm_iconphoto(self, self.appicon)
        if sys.platform == "win32":
            # tell windows to use a new toolbar icon
            import ctypes
            myappid = 'net.Razorvine.Bouldercaves.game'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        if smallwindow:
            self.tilesheet_score = tiles.Tilesheet(self.visible_columns * 2, 2, self.visible_columns * 2, 2)
            score_canvas_height = 16 * self.scalexy
        else:
            self.tilesheet_score = tiles.Tilesheet(self.visible_columns, 2, self.visible_columns, 2)
            score_canvas_height = 32 * self.scalexy
        self.popup_tiles_save = None   # type: Optional[Tuple[int, int, int, int, Sequence[Iterable[int]]]]
        self.on_popup_closed = None   # type: Optional[Callable]
        self.scrolling_into_view = False
        self.scorecanvas = tkinter.Canvas(self, width=self.visible_columns * 16 * self.scalexy,
                                          height=score_canvas_height, borderwidth=0, highlightthickness=0, background="black")
        self.canvas = tkinter.Canvas(self, width=self.visible_columns * 16 * self.scalexy,
                                     height=self.visible_rows * 16 * self.scalexy,
                                     borderwidth=0, highlightthickness=0, background="black",
                                     xscrollincrement=self.scalexy, yscrollincrement=self.scalexy)
        self.c_tiles = []         # type: List[str]
        self.cscore_tiles = []    # type: List[str]
        self.view_x = 0
        self.view_y = 0
        self.canvas.view_x = self.view_x    # type: ignore
        self.canvas.view_y = self.view_y    # type: ignore
        self.tile_images = []  # type: List[tkinter.PhotoImage]
        self.playfield_columns = 0
        self.playfield_rows = 0
        self.create_tile_images()
        self.create_canvas_playfield_and_tilesheet(40, 22)
        self.bind("<KeyPress>", self.keypress)
        self.bind("<KeyRelease>", self.keyrelease)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.scorecanvas.pack(pady=(0, 10))
        self.canvas.pack()
        self.gfxupdate_starttime = 0.0
        self.game_update_dt = 0.0
        self.graphics_update_dt = 0.0
        self.graphics_frame = 0
        self.popup_frame = 0
        self.last_demo_or_highscore_frame = 0
        self.gamestate = GameState(self)

    def destroy(self) -> None:
        audio.shutdown_audio()
        self.gamestate.destroy()
        super().destroy()

    def start(self) -> None:
        self.gfxupdate_starttime = time.perf_counter()
        self.game_update_dt = 0.0
        self.graphics_update_dt = 0.0
        self.graphics_frame = 0
        if not self.gamestate.playtesting:
            cs = self.gamestate.caveset
            if self.smallwindow:
                fmt = "Playing caveset:\n\n{name}\n\nby {author}\n\n({date})"
            else:
                fmt = "Playing caveset:\n\n\x0f\x0f`{name}'\n\n\x0f\x0fby {author}\n\n\x0f\x0f\x0f\x0f({date})"
            self.popup(fmt.format(name=cs.name, author=cs.author, date=cs.date), duration=3)
        self.tick_loop()

    def tick_loop(self) -> None:
        now = time.perf_counter()
        dt = now - self.gfxupdate_starttime
        self.game_update_dt += dt
        while self.game_update_dt > self.gamestate.update_timestep:
            self.game_update_dt -= self.gamestate.update_timestep
            self.update_game()
        self.graphics_update_dt += dt
        if self.gamestate.game_status in (GameStatus.REVEALING_DEMO, GameStatus.REVEALING_PLAY) and not self.popup_tiles_save:
            self.do_reveal()
        if self.graphics_update_dt > self.update_timestep:
            self.graphics_update_dt -= self.update_timestep
            if self.graphics_update_dt >= self.update_timestep:
                print("Gfx update too slow to reach {:d} fps!".format(self.update_fps))
            self.repaint()
        self.gfxupdate_starttime = now
        self.after(1000 // 60, self.tick_loop)

    def keypress(self, event) -> None:
        if event.keysym.startswith("Shift") or event.state & 1:
            self.gamestate.movement.start_grab()
        if event.keysym == "Down":
            self.gamestate.movement.start_down()
        elif event.keysym == "Up":
            self.gamestate.movement.start_up()
        elif event.keysym == "Left":
            self.gamestate.movement.start_left()
        elif event.keysym == "Right":
            self.gamestate.movement.start_right()
        elif event.keysym == "space":
            self.gamestate.pause()
        elif event.keysym == "Escape":
            self.popup_close()
            if self.gamestate.game_status in (GameStatus.LOST, GameStatus.WON):
                self.restart()
            elif self.gamestate.game_status == GameStatus.PLAYING:
                self.gamestate.suicide()
            elif self.gamestate.game_status in (GameStatus.DEMO, GameStatus.HIGHSCORE):
                self.restart()
        elif event.keysym == "F1":
            self.popup_close()
            if self.gamestate.game_status in (GameStatus.LOST, GameStatus.WON):
                self.restart()
            elif self.gamestate.game_status in (GameStatus.DEMO, GameStatus.HIGHSCORE):
                self.restart()
            elif self.gamestate.game_status == GameStatus.PLAYING and not self.gamestate.rockford_cell:
                self.gamestate.suicide()
            else:
                if self.gamestate.lives < 0:
                    self.restart()
                if self.gamestate.level < 1:
                    self.gamestate.level = self.gamestate.start_level_number - 1
                    self.gamestate.load_next_level()
        elif event.keysym == "F5":
            self.gamestate.cheat_used = True
            self.gamestate.add_extra_life()
        elif event.keysym == "F6":
            self.gamestate.cheat_used = True
            self.gamestate.add_extra_time(10)

    def restart(self):
        if self.gamestate.playtesting:
            print("Exiting game because of playtest mode (returning to editor).")
            raise SystemExit
        self.create_canvas_playfield_and_tilesheet(40, 22)
        self.scrollxypixels(0, 0)
        self.gamestate.restart()

    def keyrelease(self, event) -> None:
        if event.keysym.startswith("Shift") or not (event.state & 1):
            self.gamestate.movement.stop_grab()
        if event.keysym == "Down":
            self.gamestate.movement.stop_down()
        elif event.keysym == "Up":
            self.gamestate.movement.stop_up()
        elif event.keysym == "Left":
            self.gamestate.movement.stop_left()
        elif event.keysym == "Right":
            self.gamestate.movement.stop_right()
        elif event.keysym == "F7":
            self.gamestate.cheat_skip_level()
        elif event.keysym == "F8":
            # choose a random color scheme (only works when using retro C-64 colors)
            colors = Palette()
            colors.randomize()
            print("random colors:", colors)
            self.create_colored_tiles(colors)
            self.set_screen_colors(colors.rgb_screen, colors.rgb_border)
            self.tilesheet.all_dirty()
        elif event.keysym == "F4":
            self.gamestate.show_highscores()
        elif event.keysym == "F9":
            self.gamestate.start_demo()
        elif event.keysym == "F12":
            # launch the editor in a separate process
            import subprocess
            from . import editor
            env = os.environ.copy()
            env["PYTHONPATH"] = sys.path[0]
            subprocess.Popen([sys.executable, "-m", editor.__name__], env=env)

    def repaint(self) -> None:
        self.graphics_frame += 1
        self.scroll_focuscell_into_view()
        if self.smallwindow and self.gamestate.game_status == GameStatus.WAITING and self.popup_frame < self.graphics_frame:
            # move the waiting screen (title screen) around so you can see it all :)
            wavew, waveh = tiles.tile2pixels(self.playfield_columns - self.visible_columns, self.playfield_rows - self.visible_rows)
            x = (1 + math.sin(1.5 * math.pi + self.graphics_frame / self.update_fps)) * wavew / 2
            y = (1 + math.cos(math.pi + self.graphics_frame / self.update_fps / 1.4)) * waveh / 2
            self.scrollxypixels(x, y)
        for index, tile in self.tilesheet_score.dirty():
            self.scorecanvas.itemconfigure(self.cscore_tiles[index], image=self.tile_images[tile])
        # smooth scroll
        if self.canvas.view_x != self.view_x:       # type: ignore
            self.canvas.xview_moveto(0)
            self.canvas.xview_scroll(self.view_x, tkinter.UNITS)
            self.canvas.view_x = self.view_x        # type: ignore
        if self.canvas.view_y != self.view_y:       # type: ignore
            self.canvas.yview_moveto(0)
            self.canvas.yview_scroll(self.view_y, tkinter.UNITS)
            self.canvas.view_y = self.view_y        # type: ignore
        self.tilesheet.set_view(self.view_x // 16, self.view_y // 16)

        if self.popup_frame > self.graphics_frame:
            for index, tile in self.tilesheet.dirty():
                self.canvas.itemconfigure(self.c_tiles[index], image=self.tile_images[tile])
            return
        elif self.popup_tiles_save:
            self.popup_close()

        if self.gamestate.game_status in (GameStatus.REVEALING_PLAY, GameStatus.REVEALING_DEMO):
            return

        if self.gamestate.rockford_cell:
            # is rockford moving or pushing left/right?
            rockford_sprite = objects.ROCKFORD   # type: objects.GameObject
            animframe = 0
            if self.gamestate.movement.direction == Direction.LEFT or \
                    (self.gamestate.movement.direction in (Direction.UP, Direction.DOWN) and
                     self.gamestate.movement.lastXdir == Direction.LEFT):
                if self.gamestate.movement.pushing:
                    rockford_sprite = objects.ROCKFORD.pushleft
                else:
                    rockford_sprite = objects.ROCKFORD.left
            elif self.gamestate.movement.direction == Direction.RIGHT or \
                    (self.gamestate.movement.direction in (Direction.UP, Direction.DOWN) and
                     self.gamestate.movement.lastXdir == Direction.RIGHT):
                if self.gamestate.movement.pushing:
                    rockford_sprite = objects.ROCKFORD.pushright
                else:
                    rockford_sprite = objects.ROCKFORD.right
            # handle rockford idle state/animation
            elif self.gamestate.idle["tap"] and self.gamestate.idle["blink"]:
                rockford_sprite = objects.ROCKFORD.tapblink
            elif self.gamestate.idle["tap"]:
                rockford_sprite = objects.ROCKFORD.tap
            elif self.gamestate.idle["blink"]:
                rockford_sprite = objects.ROCKFORD.blink
            if rockford_sprite.sframes:
                animframe = int(rockford_sprite.sfps / self.update_fps *
                                (self.graphics_frame - self.gamestate.rockford_cell.anim_start_gfx_frame)) % rockford_sprite.sframes
            self.tilesheet[self.gamestate.rockford_cell.x, self.gamestate.rockford_cell.y] = rockford_sprite.tile(animframe)
        # other animations:
        for cell in self.gamestate.cells_with_animations():
            obj = cell.obj
            if obj is objects.MAGICWALL:
                if not self.gamestate.magicwall["active"]:
                    obj = objects.BRICK
            animframe = int(obj.sfps / self.update_fps * (self.graphics_frame - cell.anim_start_gfx_frame))
            self.tilesheet[cell.x, cell.y] = obj.tile(animframe)
            if animframe >= obj.sframes and obj.anim_end_callback:
                # the animation reached the last frame
                obj.anim_end_callback(cell)
        # flash
        if self.gamestate.flash > self.gamestate.frame:
            self.configure(background=self.tkcolor(15) if self.graphics_frame % 2 else self.tkcolor(0))
        elif self.gamestate.flash > 0:
            self.configure(background="black")
        for index, tile in self.tilesheet.dirty():
            self.canvas.itemconfigure(self.c_tiles[index], image=self.tile_images[tile])

    def create_colored_tiles(self, colors: Palette) -> None:
        if self.c64colors:
            source_images = tiles.load_sprites(colors if self.c64colors else None, scale=self.scalexy)
            for i, image in enumerate(source_images):
                self.tile_images[i] = tkinter.PhotoImage(data=image)

    def create_tile_images(self) -> None:
        initial_palette = Palette(2, 4, 13, 5, 6)
        source_images = tiles.load_sprites(initial_palette if self.c64colors else None, scale=self.scalexy)
        self.tile_images = [tkinter.PhotoImage(data=image) for image in source_images]
        source_images = tiles.load_font(self.scalexy if self.smallwindow else 2 * self.scalexy)
        self.tile_images.extend([tkinter.PhotoImage(data=image) for image in source_images])

    def create_canvas_playfield_and_tilesheet(self, width: int, height: int) -> None:
        # create the images on the canvas for all tiles (fixed position):
        if width == self.playfield_columns and height == self.playfield_rows:
            return
        if width < 4 or width > 100 or height < 4 or height > 100:
            raise ValueError("invalid playfield/cave width or height (4-100)")
        self.playfield_columns = width
        self.playfield_rows = height
        self.canvas.delete(tkinter.ALL)
        self.c_tiles.clear()
        for y in range(self.playfield_rows):
            for x in range(self.playfield_columns):
                sx, sy = self.physcoor(*tiles.tile2pixels(x, y))
                tile = self.canvas.create_image(sx, sy, image=self.tile_images[0], anchor=tkinter.NW, tags="tile")
                self.c_tiles.append(tile)
        # create the images on the score canvas for all tiles (fixed position):
        self.scorecanvas.delete(tkinter.ALL)
        self.cscore_tiles.clear()
        vcols = self.visible_columns if not self.smallwindow else 2 * self.visible_columns
        for y in range(2):
            for x in range(vcols):
                sx, sy = self.physcoor(*tiles.tile2pixels(x, y))
                if self.smallwindow:
                    sx //= 2
                    sy //= 2
                self.tilesheet_score[x, y] = 0
                tile = self.scorecanvas.create_image(sx, sy, image=None, anchor=tkinter.NW, tags="tile")
                self.cscore_tiles.append(tile)
        self.tilesheet = tiles.Tilesheet(self.playfield_columns, self.playfield_rows, self.visible_columns, self.visible_rows)

    def set_screen_colors(self, screencolorrgb: int, bordercolorrgb: int) -> None:
        if self.c64colors:
            self.configure(background="#{:06x}".format(bordercolorrgb))
            self.canvas.configure(background="#{:06x}".format(screencolorrgb))

    def set_canvas_tile(self, x: int, y: int, obj: objects.GameObject) -> None:
        self.tilesheet[x, y] = obj.tile()

    def set_scorebar_tiles(self, x: int, y: int, tiles: Sequence[int]) -> None:
        self.tilesheet_score.set_tiles(x, y, tiles)

    def clear_tilesheet(self) -> None:
        self.tilesheet.set_tiles(0, 0, [objects.DIRT2.tile()] * self.playfield_columns * self.playfield_rows)

    def prepare_reveal(self) -> None:
        c = objects.COVERED.tile()
        for c_tile in self.c_tiles:
            self.canvas.itemconfigure(c_tile, image=self.tile_images[c])
        self.tiles_revealed = bytearray(len(self.c_tiles))

    def do_reveal(self) -> None:
        # reveal tiles during the reveal period
        if self.graphics_frame % 2 == 0:
            return
        times = 1 if self.playfield_columns < 44 else 2
        for _ in range(0, times):
            for y in range(0, self.playfield_rows):
                x = random.randrange(0, self.playfield_columns)
                tile = self.tilesheet[x, y]
                idx = x + self.playfield_columns * y
                self.tiles_revealed[idx] = 1
                self.canvas.itemconfigure(self.c_tiles[idx], image=self.tile_images[tile])
        # animate the cover-tiles
        cover_tile = objects.COVERED.tile(self.graphics_frame)
        for i, c_tile in enumerate(self.c_tiles):
            if self.tiles_revealed[i] == 0:
                self.canvas.itemconfigure(c_tile, image=self.tile_images[cover_tile])

    def physcoor(self, sx: int, sy: int) -> Tuple[int, int]:
        return int(sx * self.scalexy), int(sy * self.scalexy)

    def tkcolor(self, color: int) -> str:
        return "#{:06x}".format(colorpalette[color & len(colorpalette) - 1])

    def scrollxypixels(self, x: float, y: float) -> None:
        self.view_x, self.view_y = self.clamp_scroll_xy(x, y)

    def clamp_scroll_xy(self, x: float, y: float) -> Tuple[int, int]:
        xlimit, ylimit = tiles.tile2pixels(self.playfield_columns - self.visible_columns, self.playfield_rows - self.visible_rows)
        return min(max(0, round(x)), xlimit), min(max(0, round(y)), ylimit)

    def update_game(self) -> None:
        if self.popup_frame < self.graphics_frame:
            self.gamestate.update(self.graphics_frame)
        self.gamestate.update_scorebar()
        music_duration = audio.samples["music"].duration   # type: ignore
        if self.gamestate.game_status == GameStatus.WAITING and \
                self.last_demo_or_highscore_frame + self.update_fps * max(15, music_duration) < self.graphics_frame:
            self.gamestate.tile_music_ended()
            self.last_demo_or_highscore_frame = self.graphics_frame

    def scroll_focuscell_into_view(self, immediate: bool=False) -> None:
        focus_cell = self.gamestate.focus_cell()
        if focus_cell:
            x, y = focus_cell.x, focus_cell.y
            curx, cury = self.view_x / 16 + self.visible_columns / 2, self.view_y / 16 + self.visible_rows / 2
            if not self.scrolling_into_view and abs(curx - x) < self.visible_columns // 3 and abs(cury - y) < self.visible_rows // 3:
                return  # don't always keep it exactly in the center at all times, add some movement slack area
            # scroll the view to the focus cell
            viewx, viewy = tiles.tile2pixels(x - self.visible_columns // 2, y - self.visible_rows // 2)
            viewx, viewy = self.clamp_scroll_xy(viewx, viewy)
            if immediate:
                # directly jump to new scroll position (no interpolation)
                self.scrollxypixels(viewx, viewy)
            else:
                if viewx == self.view_x and viewy == self.view_y:
                    # we reached the end
                    self.scrolling_into_view = False
                else:
                    # interpolate towards the new view position
                    self.scrolling_into_view = True
                    dx = (viewx - self.view_x) / self.update_fps * 2.0
                    dy = (viewy - self.view_y) / self.update_fps * 2.0
                    if dx:
                        viewx = int(self.view_x + math.copysign(max(1, abs(dx)), dx))
                    if dy:
                        viewy = int(self.view_y + math.copysign(max(1, abs(dy)), dy))
                    self.scrollxypixels(viewx, viewy)

    def popup(self, text: str, duration: float=5.0, on_close: Callable=None) -> None:
        self.popup_close()
        self.scroll_focuscell_into_view(immediate=True)   # snap the view to the focus cell otherwise popup may appear off-screen
        lines = []
        width = self.visible_columns - 4 if self.smallwindow else int(self.visible_columns * 0.6)
        for line in text.splitlines():
            output = ""
            for word in line.split():
                if len(output) + len(word) < (width + 1):
                    output += word + " "
                else:
                    lines.append(output.rstrip())
                    output = word + " "
            if output:
                lines.append(output.rstrip())
            else:
                lines.append("")
        if self.smallwindow:
            bchar = ""
            popupwidth = width + 4
            popupheight = len(lines) + 3
        else:
            bchar = "\x0e"
            popupwidth = width + 6
            popupheight = len(lines) + 6
        x, y = (self.visible_columns - popupwidth) // 2, int((self.visible_rows - popupheight + 1) / 2)

        # move the popup inside the currently viewable portion of the playfield
        x += self.view_x // 16
        y += self.view_y // 16
        x = min(x, self.playfield_columns - popupwidth)
        y = min(y, self.playfield_rows - popupheight)

        self.popup_tiles_save = (
            x, y, popupwidth, popupheight,
            self.tilesheet.get_tiles(x, y, popupwidth, popupheight)
        )
        self.tilesheet.set_tiles(x, y, [objects.STEELSLOPEDUPLEFT.tile()] +
                                 [objects.STEEL.tile()] * (popupwidth - 2) + [objects.STEELSLOPEDUPRIGHT.tile()])
        y += 1
        if not self.smallwindow:
            self.tilesheet.set_tiles(x + 1, y, tiles.text2tiles(bchar * (popupwidth - 2)))
            self.tilesheet[x, y] = objects.STEEL.tile()
            self.tilesheet[x + popupwidth - 1, y] = objects.STEEL.tile()
            y += 1
        lines.insert(0, "")
        if not self.smallwindow:
            lines.append("")
        for line in lines:
            if not line:
                line = " "
            line_tiles = tiles.text2tiles(bchar + " " + line.ljust(width) + " " + bchar)
            self.tilesheet[x, y] = objects.STEEL.tile()
            self.tilesheet[x + popupwidth - 1, y] = objects.STEEL.tile()
            self.tilesheet.set_tiles(x + 1, y, line_tiles)
            y += 1
        if not self.smallwindow:
            self.tilesheet[x, y] = objects.STEEL.tile()
            self.tilesheet[x + popupwidth - 1, y] = objects.STEEL.tile()
            self.tilesheet.set_tiles(x + 1, y, tiles.text2tiles(bchar * (popupwidth - 2)))
            y += 1
        self.tilesheet.set_tiles(x, y, [objects.STEELSLOPEDDOWNLEFT.tile()] +
                                 [objects.STEEL.tile()] * (popupwidth - 2) + [objects.STEELSLOPEDDOWNRIGHT.tile()])
        self.popup_frame = int(self.graphics_frame + self.update_fps * duration)
        self.on_popup_closed = on_close

    def popup_close(self) -> None:
        if not self.popup_tiles_save:
            return
        x, y, width, height, saved_tiles = self.popup_tiles_save
        for tiles in saved_tiles:
            self.tilesheet.set_tiles(x, y, tiles)
            y += 1
        self.popup_tiles_save = None
        self.popup_frame = 0
        if self.on_popup_closed:
            self.on_popup_closed()
            self.on_popup_closed = None

    def ask_highscore_name(self, score_pos: int, score: int) -> str:
        username = bdcff.get_system_username()[:HighScores.max_namelen]
        while True:
            name = simpledialog.askstring("Enter your name", "Enter your name for the high-score table!\n\n"
                                          "#{:d} score:  {:d}\n\n(max {:d} letters)"
                                          .format(score_pos, score, HighScores.max_namelen),
                                          initialvalue=username, parent=self) or ""
            name = name.strip()
            if 0 < len(name) <= HighScores.max_namelen:
                return name


def start(sargs: Sequence[str]=None) -> None:
    if sargs is None:
        sargs = sys.argv[1:]
    import argparse
    ap = argparse.ArgumentParser(description="Boulder Caves - a Boulder Dash (tm) clone",
                                 epilog="This software is licensed under the GNU GPL 3.0, see https://www.gnu.org/licenses/gpl.html")
    ap.add_argument("-g", "--game", help="specify cave data file to play, leave empty to play original built-in BD1 caves")
    ap.add_argument("-f", "--fps", type=int, help="frames per second (default=%(default)d)", default=30)
    ap.add_argument("-s", "--size", type=int, help="graphics size (default=%(default)d)", default=3, choices=(1, 2, 3, 4, 5))
    ap.add_argument("-c", "--c64colors", help="use Commodore-64 colors", action="store_true")
    ap.add_argument("-a", "--authentic", help="use C-64 colors AND limited window size", action="store_true")
    ap.add_argument("-y", "--synth", help="use synthesized sounds instead of samples", action="store_true")
    ap.add_argument("-l", "--level", help="select start level (cave number). When using this, no highscores will be recorded.", type=int, default=1)
    ap.add_argument("--editor", help="run the cave editor instead of the game.", action="store_true")
    ap.add_argument("--playtest", help="playtest the cave.", action="store_true")
    args = ap.parse_args(sargs)
    print("This software is licensed under the GNU GPL 3.0, see https://www.gnu.org/licenses/gpl.html")

    if args.editor:
        from . import editor
        editor.start()
        raise SystemExit

    # validate required libraries
    audio_api = audio.best_api()
    args.c64colors |= args.authentic
    if args.c64colors:
        print("Using the original Commodore-64 colors.")
        print("Start without the '--c64colors' or '--authentic' arguments to use the multicolor replacement graphics.")
    else:
        print("Using multicolor replacement graphics.")
        print("You can use the '-c' or '--c64colors' argument to get the original C-64 colors.")

    # initialize the audio system
    audio.norm_samplerate = 22050
    audio.norm_samplewidth = 2
    audio.norm_channels = 2
    samples = {
        "music": ("bdmusic.ogg", 1),
        "cover": ("cover.ogg", 1),
        "crack": ("crack.ogg", 2),
        "boulder": ("boulder.ogg", 4),
        "finished": ("finished.ogg", 1),
        "explosion": ("explosion.ogg", 2),
        "voodoo_explosion": ("voodoo_explosion.ogg", 2),
        "extra_life": ("bonus_life.ogg", 1),
        "walk_empty": ("walk_empty.ogg", 2),
        "walk_dirt": ("walk_dirt.ogg", 2),
        "collect_diamond": ("collectdiamond.ogg", 1),
        "box_push": ("box_push.ogg", 2),
        "amoeba": ("amoeba.ogg", 1),
        "slime": ("slime.ogg", 1),
        "magic_wall": ("magic_wall.ogg", 1),
        "game_over": ("game_over.ogg", 1),
        "diamond1": ("diamond1.ogg", 2),
        "diamond2": ("diamond2.ogg", 2),
        "diamond3": ("diamond3.ogg", 2),
        "diamond4": ("diamond4.ogg", 2),
        "diamond5": ("diamond5.ogg", 2),
        "diamond6": ("diamond6.ogg", 2),
        "timeout1": ("timeout1.ogg", 1),
        "timeout2": ("timeout2.ogg", 1),
        "timeout3": ("timeout3.ogg", 1),
        "timeout4": ("timeout4.ogg", 1),
        "timeout5": ("timeout5.ogg", 1),
        "timeout6": ("timeout6.ogg", 1),
        "timeout7": ("timeout7.ogg", 1),
        "timeout8": ("timeout8.ogg", 1),
        "timeout9": ("timeout9.ogg", 1),
    }

    if args.synth:
        print("Pre-synthesizing sounds...")
        diamond = synthsamples.Diamond()   # is randomized everytime it is played
        synthesized = {
            "music": synthsamples.TitleMusic(),
            "cover": synthsamples.Cover(),
            "crack": synthsamples.Crack(),
            "boulder": synthsamples.Boulder(),
            "amoeba": synthsamples.Amoeba(),
            "slime": synthsamples.Slime(),
            "magic_wall": synthsamples.MagicWall(),
            "finished": synthsamples.Finished(),
            "explosion": synthsamples.Explosion(),
            "voodoo_explosion": synthsamples.VoodooExplosion(),
            "collect_diamond": synthsamples.CollectDiamond(),
            "walk_empty": synthsamples.WalkEmpty(),
            "walk_dirt": synthsamples.WalkDirt(),
            "box_push": synthsamples.BoxPush(),
            "extra_life": synthsamples.ExtraLife(),
            "game_over": synthsamples.GameOver(),
            "diamond1": diamond,
            "diamond2": diamond,
            "diamond3": diamond,
            "diamond4": diamond,
            "diamond5": diamond,
            "diamond6": diamond,
            "timeout1": synthsamples.Timeout(1),
            "timeout2": synthsamples.Timeout(2),
            "timeout3": synthsamples.Timeout(3),
            "timeout4": synthsamples.Timeout(4),
            "timeout5": synthsamples.Timeout(5),
            "timeout6": synthsamples.Timeout(6),
            "timeout7": synthsamples.Timeout(7),
            "timeout8": synthsamples.Timeout(8),
            "timeout9": synthsamples.Timeout(9),
        }
        assert len(synthesized.keys() - samples.keys()) == 0
        missing = samples.keys() - synthesized.keys()
        if missing:
            raise SystemExit("Synths missing for: " + str(missing))
        for name, sample in synthesized.items():
            max_simul = samples[name][1]
            samples[name] = (sample, max_simul)    # type: ignore

    audio.init_audio(samples)
    title = "Boulder Caves {version:s} {sound:s} {playtest:s} - by Irmen de Jong"\
        .format(version=__version__,
                sound="[using synthesizer]" if args.synth else "",
                playtest="[playtesting]" if args.playtest else "")
    window = BoulderWindow(title, args.fps, args.size + 1, args.c64colors | args.authentic, args.authentic)
    if args.game:
        window.gamestate.use_bdcff(args.game)
    if args.level:
        window.gamestate.use_startlevel(args.level)
    if args.playtest:
        window.gamestate.use_playtesting()
    cs = window.gamestate.caveset
    print("Playing caveset '{name}' (by {author}, {date})".format(name=cs.name, author=cs.author, date=cs.date))
    window.start()
    window.mainloop()


if __name__ == "__main__":
    start(sys.argv[1:])
