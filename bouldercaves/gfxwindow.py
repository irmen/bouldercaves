"""
Boulder Caves - a Boulder Dash (tm) clone.

This module contains the GUI window logic, handles keyboard input
and screen drawing via tkinter bitmaps.

Written by Irmen de Jong (irmen@razorvine.net)
License: MIT open-source.
"""

import random
import array
import io
import sys
import math
import tkinter
import tkinter.messagebox
import pkgutil
import time
from typing import Tuple, Union, Sequence, List, Set, Iterable
try:
    from PIL import Image
except ImportError:
    r = tkinter.Tk()
    r.withdraw()
    tkinter.messagebox.showerror("missing Python library", "The 'pillow' or 'pil' python library is required.")
    raise SystemExit
from .game import GameState, GameObject, Direction, GameStatus
from .caves import colorpalette
from . import audio, synthsamples


class Tilesheet:
    def __init__(self, width: int, height: int, view_width: int, view_height: int) -> None:
        self.tiles = array.array('H', [0] * width * height)
        self.dirty_tiles = bytearray(width * height)
        self._dirty_clean = bytearray(width * height)
        self.width = width
        self.height = height
        self.view_width = view_width
        self.view_height = view_height
        self.view_x = 0
        self.view_y = 0

    def set_view(self, vx: int, vy: int) -> None:
        new_vx = min(max(0, vx), self.width - self.view_width)
        new_vy = min(max(0, vy), self.height - self.view_height)
        if new_vx != self.view_x or new_vy != self.view_y:
            # the viewport has been moved, mark all tiles as dirty
            self.dirty_tiles[:] = b'\x01' * self.width * self.height
        self.view_x = new_vx
        self.view_y = new_vy

    def __getitem__(self, xy: Tuple[int, int]) -> int:
        x, y = xy
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("tile xy out of bounds")
        return self.tiles[x + self.width * y]

    def __setitem__(self, xy: Tuple[int, int], tilenum: int) -> None:
        x, y = xy
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("tile xy out of bounds")
        pos = x + self.width * y
        old_value = self.tiles[pos]
        if tilenum != old_value:
            self.tiles[pos] = tilenum
            self.dirty_tiles[pos] = 1

    def set_tiles(self, x: int, y: int, tile_or_tiles: Union[int, Iterable[int]]) -> None:
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError("tile xy out of bounds")
        if isinstance(tile_or_tiles, int):
            enum_tiles = enumerate([tile_or_tiles], start=x + self.width * y)
        else:
            enum_tiles = enumerate(tile_or_tiles, start=x + self.width * y)
        for i, t in enum_tiles:
            old_value = self.tiles[i]
            if t != old_value:
                self.tiles[i] = t
                self.dirty_tiles[i] = 1

    def get_tiles(self, x: int, y: int, width: int, height: int) -> Sequence[Iterable[int]]:
        if x < 0 or x >= self.width or y < 0 or y > self.height:
            raise ValueError("tile xy out of bounds")
        if width <= 0 or x + width > self.width or height <= 0 or y + height > self.height:
            raise ValueError("width or height out of bounds")
        offset = x + self.width * y
        result = []
        for dy in range(height):
            result.append(self.tiles[offset + self.width * dy: offset + self.width * dy + width])
        return result       # type: ignore

    def all_dirty(self) -> None:
        for i in range(self.width * self.height):
            self.dirty_tiles[i] = True

    def dirty(self) -> Sequence[Tuple[int, int]]:
        # return only the dirty part of the viewable area of the tilesheet
        # (including a border of 1 tile to allow smooth scroll into view)
        tiles = self.tiles
        dirty_tiles = self.dirty_tiles
        diff = []
        for y in range(max(self.view_y - 1, 0), min(self.view_y + self.view_height + 1, self.height)):
            yy = self.width * y
            for x in range(max(self.view_x - 1, 0), min(self.view_x + self.view_width + 1, self.width)):
                if dirty_tiles[x + yy]:
                    diff.append((x + yy, tiles[x + yy]))
        self.dirty_tiles[:] = self._dirty_clean
        return diff


class BoulderWindow(tkinter.Tk):
    update_fps = 30
    update_timestep = 1 / update_fps
    visible_columns = 40
    visible_rows = 22
    playfield_columns = 40
    playfield_rows = 22
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
        if self.playfield_columns <= 0 or self.playfield_columns > 128 or self.playfield_rows <= 0 or self.playfield_rows > 128:
            raise ValueError("invalid playfield size")
        if self.visible_columns <= 0 or self.visible_columns > 128 or self.visible_rows <= 0 or self.visible_rows > 128:
            raise ValueError("invalid visible size")
        if self.scalexy not in (1, 1.5, 2, 2.5, 3):
            raise ValueError("invalid scalexy factor", self.scalexy)
        self.geometry("+200+40")
        self.configure(borderwidth=16, background="black")
        self.wm_title(title)
        self.appicon = tkinter.PhotoImage(data=pkgutil.get_data(__name__, "gfx/gdash_icon_48.gif"))
        self.wm_iconphoto(self, self.appicon)
        if sys.platform == "win32":
            # tell windows to use a new toolbar icon
            import ctypes
            myappid = 'net.Razorvine.Tale.story'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.tilesheet = Tilesheet(self.playfield_columns, self.playfield_rows, self.visible_columns, self.visible_rows)
        if smallwindow:
            self.tilesheet_score = Tilesheet(self.visible_columns * 2, 2, self.visible_columns * 2, 2)
            score_canvas_height = 16 * self.scalexy
        else:
            self.tilesheet_score = Tilesheet(self.visible_columns, 2, self.visible_columns, 2)
            score_canvas_height = 32 * self.scalexy
        self.popup_tiles_save = None   # type: Tuple[int, int, int, int, Sequence[Iterable[int]]]
        self.scrolling_into_view = False
        self.scorecanvas = tkinter.Canvas(self, width=self.visible_columns * 16 * self.scalexy,
                                          height=score_canvas_height, borderwidth=0, highlightthickness=0, background="black")
        self.canvas = tkinter.Canvas(self, width=self.visible_columns * 16 * self.scalexy,
                                     height=self.visible_rows * 16 * self.scalexy,
                                     borderwidth=0, highlightthickness=0, background="black",
                                     xscrollincrement=self.scalexy, yscrollincrement=self.scalexy)
        self.tile_images = []     # type: List[tkinter.PhotoImage]
        self.c_tiles = []         # type: List[str]
        self.cscore_tiles = []    # type: List[str]
        self.uncover_tiles = set()    # type: Set[int]
        self.tile_image_numcolumns = 0
        self.view_x = 0
        self.view_y = 0
        self.canvas.view_x = self.view_x    # type: ignore
        self.canvas.view_y = self.view_y    # type: ignore
        self.create_tile_images()
        self.font_tiles_startindex = self.create_font_tiles()
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
        self.gamestate = GameState(self)

    def destroy(self) -> None:
        audio.shutdown_audio()
        super().destroy()

    def start(self) -> None:
        self.gfxupdate_starttime = time.perf_counter()
        self.game_update_dt = 0.0
        self.graphics_update_dt = 0.0
        self.graphics_frame = 0
        self.tick_loop()

    def tick_loop(self) -> None:
        now = time.perf_counter()
        dt = now - self.gfxupdate_starttime
        self.game_update_dt += dt
        while self.game_update_dt > self.gamestate.update_timestep:
            self.game_update_dt -= self.gamestate.update_timestep
            self.update_game()
        self.graphics_update_dt += dt
        if self.graphics_update_dt > self.update_timestep:
            self.graphics_update_dt -= self.update_timestep
            if self.graphics_update_dt >= self.update_timestep:
                print("Gfx update too slow to reach {:d} fps!".format(self.update_fps))
            if self.gamestate.idle["uncover"]:
                self.uncover_tiles = set(range(self.playfield_rows * self.playfield_columns))
                self.gamestate.idle["uncover"] = False
            self.repaint()
        self.gfxupdate_starttime = now
        self.after(1000 // 120, self.tick_loop)

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
            if self.gamestate.game_status in (GameStatus.LOST, GameStatus.WON):
                self.popup_frame = 0
                self.popup_tiles_save = None
                self.gamestate.restart()
            elif self.gamestate.game_status == GameStatus.PLAYING and not self.uncover_tiles:
                self.popup_frame = 0
                self.popup_tiles_save = None
                self.gamestate.suicide()
            elif self.gamestate.game_status == GameStatus.DEMO:
                self.gamestate.restart()
        elif event.keysym == "F1":
            self.popup_frame = 0
            if self.gamestate.game_status == GameStatus.DEMO:
                self.gamestate.restart()
            else:
                if not self.uncover_tiles and self.gamestate.lives < 0:
                    self.gamestate.restart()
                if self.gamestate.level < 1:
                    self.gamestate.level = 0
                    self.gamestate.load_next_level()
        elif event.keysym == "F5":
            self.gamestate.add_extra_life()
        elif event.keysym == "F6":
            self.gamestate.add_extra_time(10)

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
            c1 = random.randint(1, 15)
            c2 = random.randint(1, 15)
            c3 = random.randint(1, 15)
            print("random colors:", c1, c2, c3)
            self.create_colored_tiles(colorpalette[c1], colorpalette[c2], colorpalette[c3])
            self.tilesheet.all_dirty()
        elif event.keysym == "F9":
            self.gamestate.start_demo()

    def repaint(self) -> None:
        self.graphics_frame += 1
        self.scroll_focuscell_into_view()
        if self.smallwindow and self.gamestate.game_status == GameStatus.WAITING and self.popup_frame < self.graphics_frame:
            # move the waiting screen (title screen) around so you can see it all :)
            wavew, waveh = self.tile2screencor(self.playfield_columns - self.visible_columns, self.playfield_rows - self.visible_rows)
            x = (1 + math.sin(self.graphics_frame / 25)) * wavew / 2
            y = (1 + math.cos(self.graphics_frame / 30)) * waveh / 2
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

        if self.uncover_tiles:
            # perform random uncover animation before the level starts
            if len(self.uncover_tiles) == self.playfield_rows * self.playfield_columns:
                audio.play_sample("cover")
            for _ in range(int(30 * 30 / self.update_fps)):
                reveal = random.randrange(1 + self.playfield_columns, self.playfield_columns * (self.playfield_rows - 1))
                revealy, revealx = divmod(reveal, self.playfield_columns)
                self.uncover_tiles.discard(reveal)
                tile = self.tilesheet[revealx, revealy]
                self.canvas.itemconfigure(self.c_tiles[reveal], image=self.tile_images[tile])
            covered = GameObject.COVERED
            animframe = int(covered.sfps / self.update_fps * self.graphics_frame) % covered.sframes
            tile = self.sprite2tile(covered, animframe)
            for index in self.uncover_tiles:
                self.canvas.itemconfigure(self.c_tiles[index], image=self.tile_images[tile])
            if len(self.uncover_tiles) < self.playfield_columns * self.playfield_rows // 4:
                self.uncover_tiles = set()   # this ends the uncover animation and starts the level
                self.tilesheet.all_dirty()
        else:
            if self.gamestate.rockford_cell:
                # moving left/right
                if self.gamestate.movement.direction == Direction.LEFT or \
                        (self.gamestate.movement.direction in (Direction.UP, Direction.DOWN) and
                         self.gamestate.movement.lastXdir == Direction.LEFT):
                    spritex, spritey, sframes, sfps = GameObject.ROCKFORD.left
                elif self.gamestate.movement.direction == Direction.RIGHT or \
                        (self.gamestate.movement.direction in (Direction.UP, Direction.DOWN) and
                         self.gamestate.movement.lastXdir == Direction.RIGHT):
                    spritex, spritey, sframes, sfps = GameObject.ROCKFORD.right
                # handle rockford idle state/animation
                elif self.gamestate.idle["tap"] and self.gamestate.idle["blink"]:
                    spritex, spritey, sframes, sfps = GameObject.ROCKFORD.tapblink
                elif self.gamestate.idle["tap"]:
                    spritex, spritey, sframes, sfps = GameObject.ROCKFORD.tap
                elif self.gamestate.idle["blink"]:
                    spritex, spritey, sframes, sfps = GameObject.ROCKFORD.blink
                else:
                    spritex, spritey, sframes, sfps = GameObject.ROCKFORD.spritex, GameObject.ROCKFORD.spritey,\
                        GameObject.ROCKFORD.sframes, GameObject.ROCKFORD.sfps
                if sframes:
                    animframe = int(sfps / self.update_fps *
                                    (self.graphics_frame - self.gamestate.rockford_cell.anim_start_gfx_frame)) % sframes
                else:
                    animframe = 0
                self.tilesheet[self.gamestate.rockford_cell.x, self.gamestate.rockford_cell.y] = \
                    self.sprite2tile((spritex, spritey), animframe)
            # other animations:
            for cell in self.gamestate.cells_with_animations():
                obj = cell.obj
                if obj is GameObject.MAGICWALL:
                    if not self.gamestate.magicwall["active"]:
                        obj = GameObject.BRICK
                animframe = int(obj.sfps / self.update_fps * (self.graphics_frame - cell.anim_start_gfx_frame))
                tile = self.sprite2tile(obj, animframe)
                self.tilesheet[cell.x, cell.y] = tile
                if animframe >= obj.sframes and obj.anim_end_callback:
                    # the animation reached the last frame
                    obj.anim_end_callback(cell)
            # flash
            if self.gamestate.flash > self.gamestate.frame:
                self.configure(background="yellow" if self.graphics_frame % 2 else "black")
            elif self.gamestate.flash > 0:
                self.configure(background="black")
            for index, tile in self.tilesheet.dirty():
                self.canvas.itemconfigure(self.c_tiles[index], image=self.tile_images[tile])

    def sprite2tile(self, gameobject_or_spritexy: Union[GameObject, Tuple[int, int]], animframe: int=0) -> int:
        if isinstance(gameobject_or_spritexy, GameObject):
            if gameobject_or_spritexy.sframes:
                return gameobject_or_spritexy.spritex + self.tile_image_numcolumns * gameobject_or_spritexy.spritey +\
                    animframe % gameobject_or_spritexy.sframes
            return gameobject_or_spritexy.spritex + self.tile_image_numcolumns * gameobject_or_spritexy.spritey
        return gameobject_or_spritexy[0] + self.tile_image_numcolumns * gameobject_or_spritexy[1] + animframe

    def create_tile_images(self) -> None:
        self.tile_images = [None] * 432    # the number of tiles in the tile image(s)
        self.create_colored_tiles(colorpalette[2], colorpalette[14], colorpalette[13])
        # create the images on the canvas for all tiles (fixed position):
        for y in range(self.playfield_rows):
            for x in range(self.playfield_columns):
                sx, sy = self.physcoor(*self.tile2screencor(x, y))
                tile = self.canvas.create_image(sx, sy, image=self.tile_images[0], anchor=tkinter.NW, tags="tile")
                self.c_tiles.append(tile)
        # create the images on the score canvas for all tiles (fixed position):
        vcols = self.visible_columns if not self.smallwindow else 2 * self.visible_columns
        for y in range(2):
            for x in range(vcols):
                sx, sy = self.physcoor(*self.tile2screencor(x, y))
                if self.smallwindow:
                    sx //= 2
                    sy //= 2
                self.tilesheet_score[x, y] = 0
                tile = self.scorecanvas.create_image(sx, sy, image=None, anchor=tkinter.NW, tags="tile")
                self.cscore_tiles.append(tile)

    def create_colored_tiles(self, color1: int=0, color2: int=0, color3: int=0) -> None:
        if self.tile_images[0] is not None and not self.c64colors:
            # can only recolor tiles if the c64 colors tile image is used
            return
        tiles_filename = "c64_gfx.png" if self.c64colors else "boulder_rush.png"
        with Image.open(io.BytesIO(pkgutil.get_data(__name__, "gfx/" + tiles_filename))) as tile_image:
            num_tiles = tile_image.width * tile_image.height // 16 // 16
            assert num_tiles == 432, "tile image should contain 432 tiles"
            if self.c64colors:
                tile_image = tile_image.copy().convert('P', 0)
                palettevalues = tile_image.getpalette()
                assert 768 - palettevalues.count(0) <= 16, "must be an image with <= 16 colors"
                palette = [(r, g, b) for r, g, b in zip(palettevalues[0:16 * 3:3], palettevalues[1:16 * 3:3], palettevalues[2:16 * 3:3])]
                pc1 = palette.index((255, 0, 255))
                pc2 = palette.index((255, 0, 0))
                pc3 = palette.index((255, 255, 0))
                pc4 = palette.index((0, 255, 0))
                palette[pc1] = (color2 >> 16, (color2 & 0xff00) >> 8, color2 & 0xff)
                palette[pc2] = (color1 >> 16, (color1 & 0xff00) >> 8, color1 & 0xff)
                if color3 < 0x808080:
                    color3 = 0xffffff
                palette[pc3] = (color3 >> 16, (color3 & 0xff00) >> 8, color3 & 0xff)
                palette[pc4] = (color3 >> 16, (color3 & 0xff00) >> 8, color3 & 0xff)
                palettevalues = []
                for rgb in palette:
                    palettevalues.extend(rgb)
                tile_image.putpalette(palettevalues)
            tile_num = 0
            self.tile_image_numcolumns = tile_image.width // 16      # the tileset image contains 16x16 pixel tiles
            while True:
                row, col = divmod(tile_num, self.tile_image_numcolumns)
                if row * 16 >= tile_image.height:
                    break
                ci = tile_image.crop((col * 16, row * 16, col * 16 + 16, row * 16 + 16))
                if self.scalexy != 1:
                    ci = ci.resize((int(16 * self.scalexy), int(16 * self.scalexy)), Image.NONE)
                out = io.BytesIO()
                ci.save(out, "png")
                img = tkinter.PhotoImage(data=out.getvalue())
                self.tile_images[tile_num] = img
                tile_num += 1

    def create_font_tiles(self) -> int:
        font_tiles_startindex = len(self.tile_images)
        fontsize = 8 if self.smallwindow else 16
        with Image.open(io.BytesIO(pkgutil.get_data(__name__, "gfx/font.png"))) as image:
            for c in range(0, 128):
                row, col = divmod(c, image.width // 8)       # the font image contains 8x8 pixel tiles
                if row * 8 > image.height:
                    break
                ci = image.crop((col * 8, row * 8, col * 8 + 8, row * 8 + 8))
                ci = ci.resize((int(fontsize * self.scalexy), int(fontsize * self.scalexy)), Image.NONE)
                out = io.BytesIO()
                ci.save(out, "png")
                img = tkinter.PhotoImage(data=out.getvalue())
                self.tile_images.append(img)
        return font_tiles_startindex

    @staticmethod
    def tile2screencor(cx: int, cy: int) -> Tuple[int, int]:
        return cx * 16, cy * 16     # a tile is 16x16 pixels

    def physcoor(self, sx: int, sy: int) -> Tuple[int, int]:
        return int(sx * self.scalexy), int(sy * self.scalexy)

    def tkcolor(self, color: int) -> str:
        return "#{:06x}".format(self.colorpalette[color & len(self.colorpalette) - 1])

    def scrollxypixels(self, x: float, y: float) -> None:
        self.view_x, self.view_y = self.clamp_scroll_xy(x, y)

    def clamp_scroll_xy(self, x: float, y: float) -> Tuple[int, int]:
        xlimit, ylimit = self.tile2screencor(self.playfield_columns - self.visible_columns, self.playfield_rows - self.visible_rows)
        return min(max(0, round(x)), xlimit), min(max(0, round(y)), ylimit)

    def update_game(self) -> None:
        if not self.uncover_tiles and self.popup_frame < self.graphics_frame:
            self.gamestate.update(self.graphics_frame)
        self.gamestate.update_scorebar()
        if self.gamestate.game_status == GameStatus.WAITING and \
                self.update_timestep * self.graphics_frame >= audio.samples["music"].duration:
            self.gamestate.start_demo()

    def scroll_focuscell_into_view(self, immediate: bool=False) -> None:
        focus_cell = self.gamestate.focus_cell()
        if focus_cell:
            x, y = focus_cell.x, focus_cell.y
            curx, cury = self.view_x / 16 + self.visible_columns / 2, self.view_y / 16 + self.visible_rows / 2
            if not self.scrolling_into_view and abs(curx - x) < 6 and abs(cury - y) < 3:
                return  # don't always keep it exactly in the center at all times, add some movement slack area
            # scroll the view to the focus cell
            viewx, viewy = self.tile2screencor(x - self.visible_columns // 2, y - self.visible_rows // 2)
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
                    dx = (viewx - self.view_x) / self.update_fps * 1.5
                    dy = (viewy - self.view_y) / self.update_fps * 1.5
                    if dx:
                        viewx = int(self.view_x + math.copysign(max(1, abs(dx)), dx))
                    if dy:
                        viewy = int(self.view_y + math.copysign(max(1, abs(dy)), dy))
                    self.scrollxypixels(viewx, viewy)

    def text2tiles(self, text: str) -> Sequence[int]:
        return [self.font_tiles_startindex + ord(c) for c in text]

    def popup(self, text: str) -> None:
        self.scroll_focuscell_into_view(immediate=True)   # snap the view to the focus cell
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
                lines.append(None)
        if self.smallwindow:
            bchar = ""
            x = y = 0
            popupwidth = width + 4
            popupheight = len(lines) + 4
        else:
            bchar = "\x0e"
            x, y = (self.visible_columns - width - 6) // 2, self.visible_rows // 4
            popupwidth = width + 6
            popupheight = len(lines) + 6

        # move the popup inside the currently viewable portion of the playfield
        x += self.view_x // 16
        y += self.view_y // 16

        self.popup_tiles_save = (
            x, y, popupwidth, popupheight,
            self.tilesheet.get_tiles(x, y, popupwidth, popupheight)
        )
        self.tilesheet.set_tiles(x, y, [self.sprite2tile(GameObject.STEELSLOPEDUPLEFT)] +
                                 [self.sprite2tile(GameObject.STEEL)] * (popupwidth - 2) +
                                 [self.sprite2tile(GameObject.STEELSLOPEDUPRIGHT)])
        y += 1
        if not self.smallwindow:
            self.tilesheet.set_tiles(x + 1, y, self.text2tiles(bchar * (popupwidth - 2)))
            self.tilesheet[x, y] = self.sprite2tile(GameObject.STEEL)
            self.tilesheet[x + popupwidth - 1, y] = self.sprite2tile(GameObject.STEEL)
            y += 1
        lines.insert(0, "")
        lines.append("")
        for line in lines:
            if not line:
                line = " "
            tiles = self.text2tiles(bchar + " " + line.ljust(width) + " " + bchar)
            self.tilesheet[x, y] = self.sprite2tile(GameObject.STEEL)
            self.tilesheet[x + popupwidth - 1, y] = self.sprite2tile(GameObject.STEEL)
            self.tilesheet.set_tiles(x + 1, y, tiles)
            y += 1
        if not self.smallwindow:
            self.tilesheet[x, y] = self.sprite2tile(GameObject.STEEL)
            self.tilesheet[x + popupwidth - 1, y] = self.sprite2tile(GameObject.STEEL)
            self.tilesheet.set_tiles(x + 1, y, self.text2tiles(bchar * (popupwidth - 2)))
            y += 1
        self.tilesheet.set_tiles(x, y, [self.sprite2tile(GameObject.STEELSLOPEDDOWNLEFT)] +
                                 [self.sprite2tile(GameObject.STEEL)] * (popupwidth - 2) +
                                 [self.sprite2tile(GameObject.STEELSLOPEDDOWNRIGHT)])
        self.popup_frame = self.graphics_frame + self.update_fps * 5   # popup remains for 5 seconds

    def popup_close(self) -> None:
        x, y, width, height, saved_tiles = self.popup_tiles_save
        for tiles in saved_tiles:
            self.tilesheet.set_tiles(x, y, tiles)
            y += 1
        self.popup_tiles_save = None


def start(sargs: Sequence[str]=None) -> None:
    if sargs is None:
        sargs = sys.argv[1:]
    import argparse
    ap = argparse.ArgumentParser(description="Boulder Caves - a Boulder Dash (tm) clone")
    ap.add_argument("-f", "--fps", type=int, help="frames per second (default=%(default)d)", default=30)
    ap.add_argument("-s", "--size", type=int, help="graphics size (default=%(default)d)", default=3, choices=(1, 2, 3, 4, 5))
    ap.add_argument("-c", "--c64colors", help="use Commodore-64 colors", action="store_true")
    ap.add_argument("-a", "--authentic", help="use C-64 colors AND limited window size", action="store_true")
    ap.add_argument("-n", "--nosound", help="don't use sound", action="store_true")
    args = ap.parse_args(sargs)

    # validate required libraries
    if not args.nosound:
        audio_api = audio.best_api(dummy_enabled=True)
        if isinstance(audio_api, audio.DummyAudio):
            r = tkinter.Tk()
            r.withdraw()
            tkinter.messagebox.showerror("missing Python library",
                                         "No suitable python audio library is available, try installing 'sounddevice'.")
            raise SystemExit
        if isinstance(audio_api, audio.Winsound):
            r = tkinter.Tk()
            r.withdraw()
            tkinter.messagebox.showinfo("inferior Python audio library detected",
                                        "Winsound is used as python audio library. This library cannot play all sounds correctly.\n\n"
                                        "Try installing 'sounddevice' to hear properly mixed sounds.")
            r.destroy()

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
        "music": "bdmusic.ogg",
        "cover": "cover.ogg",
        "crack": "crack.ogg",
        "boulder": "boulder.ogg",
        "finished": "finished.ogg",
        "explosion": "explosion.ogg",
        "extra_life": "bonus_life.ogg",
        "walk_empty": "walk_empty.ogg",
        "walk_dirt": "walk_dirt.ogg",
        "collect_diamond": "collectdiamond.ogg",
        "box_push": "box_push.ogg",
        "amoeba": "amoeba.ogg",
        "magic_wall": "magicwall.ogg",
        "diamond1": "diamond1.ogg",
        "diamond2": "diamond2.ogg",
        "diamond3": "diamond3.ogg",
        "diamond4": "diamond4.ogg",
        "diamond5": "diamond5.ogg",
        "diamond6": "diamond6.ogg",
        "game_over": "game_over.ogg",
        "timeout1": "timeout1.ogg",
        "timeout2": "timeout2.ogg",
        "timeout3": "timeout3.ogg",
        "timeout4": "timeout4.ogg",
        "timeout5": "timeout5.ogg",
        "timeout6": "timeout6.ogg",
        "timeout7": "timeout7.ogg",
        "timeout8": "timeout8.ogg",
        "timeout9": "timeout9.ogg",
    }

    print("Synthesizing sounds...")
    synthesized = {
        "music": synthsamples.TitleMusic(),
        "cover": synthsamples.Cover(),
        "crack": synthsamples.Crack(),
        "boulder": synthsamples.Boulder(),
        "amoeba": synthsamples.Amoeba(),
        "magic_wall": synthsamples.MagicWall(),
        "finished": synthsamples.Finished(),
        "explosion": synthsamples.Explosion(),
        "collect_diamond": synthsamples.CollectDiamond(),
        "walk_empty": synthsamples.WalkEmpty(),
        "walk_dirt": synthsamples.WalkDirt(),
        "diamond1": synthsamples.Diamond(),   # @todo randomize diamond sound everytime it is played
        "diamond2": synthsamples.Diamond(),
        "diamond3": synthsamples.Diamond(),
        "diamond4": synthsamples.Diamond(),
        "diamond5": synthsamples.Diamond(),
        "diamond6": synthsamples.Diamond(),
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
    print("Synths missing for:", samples.keys()-synthesized.keys())
    assert len(synthesized.keys() - samples.keys()) == 0
    samples.update(synthesized)

    if args.nosound:
        print("No sound output selected.")
        audio.init_audio(samples, dummy=True)
    else:
        audio.init_audio(samples)
    window = BoulderWindow("Boulder Caves v1.3 - created by Irmen de Jong",
                           args.fps, args.size + 1, args.c64colors | args.authentic, args.authentic)
    window.start()
    window.mainloop()


if __name__ == "__main__":
    start(sys.argv[1:])
