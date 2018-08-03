"""
Boulder Caves - a Boulder Dash (tm) clone.

Sprite loading and Tile sheet logic.

Written by Irmen de Jong (irmen@razorvine.net)
License: GNU GPL 3.0, see LICENSE
"""

import array
import io
import pkgutil
from typing import Tuple, Union, Iterable, Sequence
from PIL import Image
from .caves import Palette


class Tilesheet:
    """
    Keeps track of the tiles in a matrix that will be shown on the screen.
    For optimized rendering, it tracks 'dirty' tiles.
    """
    def __init__(self, width: int, height: int, view_width: int, view_height: int) -> None:
        self.tiles = array.array('H', [0] * width * height)
        self.dirty_tiles = bytearray(width * height)
        self.width = width
        self.height = height
        self.view_width = view_width
        self.view_height = view_height
        self.view_x = 0
        self.view_y = 0

    def set_view(self, vx: int, vy: int) -> None:
        new_vx = min(max(0, vx), self.width - self.view_width)
        new_vy = min(max(0, vy), self.height - self.view_height)
        # if viewport has been moved, we used to mark everything dirty to update the whole screen.
        # this is no longer needed because the 'dirty' flag is now sticky and
        # is only cleared when that tile is actually displayed. Tiles outside of the viewport
        # remain dirty and will be redrawn automatically as soon as they appear in the viewport.
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
            # i = x + self.width * y
            # ol
            enum_tiles = enumerate([tile_or_tiles], start=x + self.width * y)
        else:
            enum_tiles = enumerate(tile_or_tiles, start=x + self.width * y)
        for i, t in enum_tiles:
            if t != self.tiles[i]:
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
        return result

    def all_dirty(self) -> None:
        for i in range(self.width * self.height):
            self.dirty_tiles[i] = True

    def dirty(self) -> Sequence[Tuple[int, int]]:
        """
        Returns only the dirty part of the viewable area of the tilesheet
        (including a border of 1 tile to allow smooth scroll into view).
        Calling this will reset the dirty-flag so make sure to only call it once every refresh.
        Returns a list of (tilesheetindex, tilevalue) tuples.
        """
        tiles = self.tiles
        dirty_tiles = self.dirty_tiles
        diff = []
        for y in range(max(self.view_y - 1, 0), min(self.view_y + self.view_height + 1, self.height)):
            yy = self.width * y
            for x in range(max(self.view_x - 1, 0), min(self.view_x + self.view_width + 1, self.width)):
                if dirty_tiles[x + yy]:
                    diff.append((x + yy, tiles[x + yy]))
                    dirty_tiles[x + yy] = False
        return diff


# note: everything below assumes that the sprite graphics are 16*16 for one tile!

def tile2pixels(tx: int, ty: int) -> Tuple[int, int]:
    return tx * 16, ty * 16


# sprite image is 432 sprites of 16*16 pixels, 8 per row.
num_sprites = 432   # after these, the font tiles are placed


def text2tiles(text: str) -> Sequence[int]:
    return [num_sprites + ord(c) for c in text]


def load_sprites(c64colorpalette: Palette=None, scale: float=1.0, alt_c64tileset=False) -> Sequence[bytes]:
    if c64colorpalette:
        tiles_filename = "c64_gfx_alt.png" if alt_c64tileset else "c64_gfx.png"
    else:
        tiles_filename = "boulder_rush.png"
    sprite_src_images = []
    with Image.open(io.BytesIO(pkgutil.get_data(__name__, "gfx/" + tiles_filename) or b"")) as tile_image:
        if c64colorpalette:
            tile_image = tile_image.copy().convert('P', 0)
            palettevalues = tile_image.getpalette()
            assert 768 - palettevalues.count(0) <= 16, "must be an image with <= 16 colors"
            palette = [(r, g, b) for r, g, b in zip(palettevalues[0:16 * 3:3], palettevalues[1:16 * 3:3], palettevalues[2:16 * 3:3])]
            pc1 = palette.index((255, 0, 0))        # red, foreground 1
            pc2 = palette.index((255, 0, 255))      # purple, foreground 2
            pc3 = palette.index((255, 255, 0))      # yellow, foreground 3 (highlight)
            pc4 = palette.index((0, 255, 0))        # green, amoeba color
            pc5 = palette.index((0, 0, 255))        # blue, slime color
            pc_bg = palette.index((0, 0, 0))        # black, background color
            assert c64colorpalette
            palette[pc1] = (c64colorpalette.rgb_fg1 >> 16, (c64colorpalette.rgb_fg1 & 0xff00) >> 8, c64colorpalette.rgb_fg1 & 0xff)
            palette[pc2] = (c64colorpalette.rgb_fg2 >> 16, (c64colorpalette.rgb_fg2 & 0xff00) >> 8, c64colorpalette.rgb_fg2 & 0xff)
            palette[pc3] = (c64colorpalette.rgb_fg3 >> 16, (c64colorpalette.rgb_fg3 & 0xff00) >> 8, c64colorpalette.rgb_fg3 & 0xff)
            palette[pc4] = (c64colorpalette.rgb_amoeba >> 16, (c64colorpalette.rgb_amoeba & 0xff00) >> 8, c64colorpalette.rgb_amoeba & 0xff)
            palette[pc5] = (c64colorpalette.rgb_slime >> 16, (c64colorpalette.rgb_slime & 0xff00) >> 8, c64colorpalette.rgb_slime & 0xff)
            palette[pc_bg] = (c64colorpalette.rgb_screen >> 16, (c64colorpalette.rgb_screen & 0xff00) >> 8, c64colorpalette.rgb_screen & 0xff)
            palettevalues = []
            for rgb in palette:
                palettevalues.extend(rgb)
            tile_image.putpalette(palettevalues)
        tile_num = 0
        if tile_image.width != 128:
            raise IOError("sprites image width should be 8 sprites of 16 pixels = 128 pixels")
        scaling_method = Image.NEAREST
        if hasattr(Image, "HAMMING"):
            scaling_method = Image.HAMMING
        while True:
            row, col = divmod(tile_num, 8)
            if row * 16 >= tile_image.height:
                break
            ci = tile_image.crop((col * 16, row * 16, col * 16 + 16, row * 16 + 16))
            if scale != 1:
                ci = ci.resize((int(16 * scale), int(16 * scale)), scaling_method)
            out = io.BytesIO()
            ci = ci.convert(mode="P")
            ci.save(out, "png", compress_level=0)
            sprite_src_images.append(out.getvalue())
            tile_num += 1
    if len(sprite_src_images) != num_sprites:
        raise IOError("sprite sheet image should contain {:d} tiles of 16*16 pixels".format(num_sprites))
    return sprite_src_images


def load_font(scale: float=1.0) -> Sequence[bytes]:
    font_src_images = []
    scaling_method = Image.NEAREST
    if hasattr(Image, "HAMMING"):
        scaling_method = Image.HAMMING
    with Image.open(io.BytesIO(pkgutil.get_data(__name__, "gfx/font.png") or b"")) as image:
        for c in range(0, 128):
            row, col = divmod(c, image.width // 8)       # the font image contains 8x8 pixel tiles
            if row * 8 > image.height:
                break
            ci = image.crop((col * 8, row * 8, col * 8 + 8, row * 8 + 8))
            if scale != 1:
                ci = ci.resize((int(8 * scale), int(8 * scale)), scaling_method)
            out = io.BytesIO()
            ci.save(out, "png")
            font_src_images.append(out.getvalue())
    return font_src_images
