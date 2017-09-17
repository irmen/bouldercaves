import array
import io
import pkgutil
from typing import Tuple, Union, Iterable, Sequence
from PIL import Image
from .game import GameObject


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
        return result       # type: ignore

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


class Sprites:
    num_sprites = 432

    def __init__(self, scalexy: float=1.0) -> None:
        self.scalexy = scalexy
        self.tile_image_numcolumns = 0   # set after loading sprites

    def sprite2tile(self, gameobject_or_spritexy: Union[GameObject, Tuple[int, int]], animframe: int=0) -> int:
        if isinstance(gameobject_or_spritexy, GameObject):
            if gameobject_or_spritexy.sframes:
                return gameobject_or_spritexy.spritex + self.tile_image_numcolumns * gameobject_or_spritexy.spritey +\
                    animframe % gameobject_or_spritexy.sframes
            return gameobject_or_spritexy.spritex + self.tile_image_numcolumns * gameobject_or_spritexy.spritey
        return gameobject_or_spritexy[0] + self.tile_image_numcolumns * gameobject_or_spritexy[1] + animframe

    def text2tiles(self, text: str) -> Sequence[int]:
        return [self.num_sprites + ord(c) for c in text]

    def load_sprites(self, c64colors=False, color1: int=0, color2: int=0, color3: int=0, bgcolor: int=0) -> Sequence[bytes]:
        tiles_filename = "c64_gfx.png" if c64colors else "boulder_rush.png"
        sprite_src_images = []
        with Image.open(io.BytesIO(pkgutil.get_data(__name__, "gfx/" + tiles_filename))) as tile_image:
            if c64colors:
                tile_image = tile_image.copy().convert('P', 0)
                palettevalues = tile_image.getpalette()
                assert 768 - palettevalues.count(0) <= 16, "must be an image with <= 16 colors"
                palette = [(r, g, b) for r, g, b in zip(palettevalues[0:16 * 3:3], palettevalues[1:16 * 3:3], palettevalues[2:16 * 3:3])]
                pc1 = palette.index((255, 0, 255))
                pc2 = palette.index((255, 0, 0))
                pc3 = palette.index((255, 255, 0))
                pc4 = palette.index((0, 255, 0))
                pc_bg = palette.index((0, 0, 0))
                palette[pc1] = (color2 >> 16, (color2 & 0xff00) >> 8, color2 & 0xff)
                palette[pc2] = (color1 >> 16, (color1 & 0xff00) >> 8, color1 & 0xff)
                if color3 < 0x808080:
                    color3 = 0xffffff
                palette[pc3] = (color3 >> 16, (color3 & 0xff00) >> 8, color3 & 0xff)
                palette[pc4] = (color3 >> 16, (color3 & 0xff00) >> 8, color3 & 0xff)
                palette[pc_bg] = (bgcolor >> 16, (bgcolor & 0xff00) >> 8, bgcolor & 0xff)
                palettevalues = []
                for rgb in palette:
                    palettevalues.extend(rgb)
                tile_image.putpalette(palettevalues)
            tile_num = 0
            self.tile_image_numcolumns = tile_image.width // 16
            while True:
                row, col = divmod(tile_num, self.tile_image_numcolumns)
                if row * 16 >= tile_image.height:
                    break
                ci = tile_image.crop((col * 16, row * 16, col * 16 + 16, row * 16 + 16))
                if self.scalexy != 1:
                    ci = ci.resize((int(16 * self.scalexy), int(16 * self.scalexy)), Image.NONE)
                out = io.BytesIO()
                ci.save(out, "png", compress_level=0)
                sprite_src_images.append(out.getvalue())
                tile_num += 1
        if len(sprite_src_images) != self.num_sprites:
            raise IOError("sprite sheet image should contain {:d} tiles of 16*16 pixels".format(self.num_sprites))
        return sprite_src_images

    def load_font(self, small: bool=False) -> Sequence[bytes]:
        size = 8 if small else 16
        font_src_images = []
        with Image.open(io.BytesIO(pkgutil.get_data(__name__, "gfx/font.png"))) as image:
            for c in range(0, 128):
                row, col = divmod(c, image.width // 8)       # the font image contains 8x8 pixel tiles
                if row * 8 > image.height:
                    break
                ci = image.crop((col * 8, row * 8, col * 8 + 8, row * 8 + 8))
                ci = ci.resize((int(size * self.scalexy), int(size * self.scalexy)), Image.NONE)
                out = io.BytesIO()
                ci.save(out, "png")
                font_src_images.append(out.getvalue())
        return font_src_images
