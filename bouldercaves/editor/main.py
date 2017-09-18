"""
Boulder Caves Editor.

Cave Set editor

Written by Irmen de Jong (irmen@razorvine.net)
License: MIT open-source.
"""

import sys
import tkinter
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.ttk
import pkgutil
from typing import Tuple, List, Dict
from ..gfxwindow import __version__
from ..caves import colorpalette, C64Cave
from ..game import Objects, GameObject
from .. import tiles


class ScrollableImageSelector(tkinter.Frame):
    def __init__(self, master: tkinter.Widget, listener: 'EditorWindow') -> None:
        super().__init__(master)
        self.treeview = tkinter.ttk.Treeview(self, columns=("tile",), displaycolumns=("tile",), height="5")
        self.treeview.heading("tile", text="Tile")
        self.treeview.column("#0", stretch=False, minwidth=40, width=40)
        self.treeview.column("tile", stretch=True, width=120)
        tkinter.ttk.Style(self).configure("Treeview", rowheight=24, background="#201000", foreground="#e0e0e0")
        sy = tkinter.Scrollbar(self, orient=tkinter.VERTICAL, command=self.treeview.yview)
        sy.pack(side=tkinter.RIGHT, expand=1, fill=tkinter.Y)
        self.treeview["yscrollcommand"] = sy.set
        self.treeview.pack(expand=1, fill=tkinter.Y)
        self.treeview.bind("<<TreeviewSelect>>", self.on_selected)
        self.treeview.bind("<Double-Button-1>", self.on_selected_doubleclick)
        self.selected_object = Objects.BOULDER
        self.selected_tile = Objects.BOULDER.tile()
        self.selected_erase_object = Objects.EMPTY
        self.selected_erase_tile = Objects.EMPTY.tile()
        self.listener = listener

    def on_selected_doubleclick(self, event) -> None:
        item = self.treeview.focus()
        item = self.treeview.item(item)
        selected_name = item["values"][0].lower()
        self.selected_erase_object = Objects.EMPTY
        self.selected_erase_tile = Objects.EMPTY.tile()
        for obj, displaytile in EDITOR_OBJECTS.items():
            if obj.name.lower() == selected_name:
                self.selected_erase_object = obj
                self.selected_erase_tile = displaytile
                self.listener.tile_erase_selection_changed(obj, displaytile)
                break

    def on_selected(self, event) -> None:
        item = self.treeview.focus()
        item = self.treeview.item(item)
        selected_name = item["values"][0].lower()
        self.selected_object = Objects.BOULDER
        self.selected_tile = Objects.BOULDER.tile()
        for obj, displaytile in EDITOR_OBJECTS.items():
            if obj.name.lower() == selected_name:
                self.selected_object = obj
                self.selected_tile = displaytile
                self.listener.tile_selection_changed(obj, displaytile)
                break

    def populate(self, rows: List) -> None:
        for row in self.treeview.get_children():
            self.treeview.delete(row)
        for image, name in rows:
            self.treeview.insert("", tkinter.END, image=image, values=(name,))
        self.treeview.configure(height=min(16, len(rows)))


class Cave:
    def __init__(self, width: int, height: int, editor: 'EditorWindow') -> None:
        self.width = width
        self.height = height
        self.cells = [(Objects.EMPTY, Objects.EMPTY.tile())] * width * height
        self.cells_snapshot = []   # type: List[Tuple[GameObject, int]]
        self.editor = editor

    def __setitem__(self, xy: Tuple[int, int], thing: Tuple[GameObject, int]) -> None:
        x, y = xy
        obj, displaytile = thing
        self.cells[x + self.width * y] = (obj, displaytile)
        self.editor.set_tile(x, y, displaytile)

    def __getitem__(self, xy: Tuple[int, int]) -> Tuple[GameObject, int]:
        x, y = xy
        return self.cells[x + self.width * y]

    def horiz_line(self, x: int, y: int, length: int, thing: Tuple[GameObject, int]) -> None:
        for xx in range(x, x + length):
            self[xx, y] = thing

    def vert_line(self, x: int, y: int, length: int, thing: Tuple[GameObject, int]) -> None:
        for yy in range(y, y + length):
            self[x, yy] = thing

    def snapshot(self) -> None:
        self.cells_snapshot = self.cells.copy()

    def restore(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self[x, y] = self.cells_snapshot[x + self.width * y]


EDITOR_OBJECTS = {
    Objects.AMOEBA: Objects.AMOEBA.tile(),
    Objects.BOULDER: Objects.BOULDER.tile(),
    Objects.BRICK: Objects.BRICK.tile(),
    Objects.BUTTERFLY: Objects.BUTTERFLY.tile(2),
    Objects.DIAMOND: Objects.DIAMOND.tile(),
    Objects.DIRT: Objects.DIRT2.tile(),
    Objects.EMPTY: Objects.EMPTY.tile(),
    Objects.FIREFLY: Objects.FIREFLY.tile(1),
    Objects.HEXPANDINGWALL: Objects.HEXPANDINGWALL.tile(),
    Objects.INBOXBLINKING: Objects.ROCKFORD.tile(),
    Objects.MAGICWALL: Objects.MAGICWALL.tile(),
    Objects.OUTBOXBLINKING: Objects.OUTBOXBLINKING.tile(1),
    Objects.SLIME: Objects.SLIME.tile(1),
    Objects.STEEL: Objects.STEEL.tile(),
    Objects.VEXPANDINGWALL: Objects.VEXPANDINGWALL.tile(),
    Objects.VOODOO: Objects.VOODOO.tile()
}


class EditorWindow(tkinter.Tk):
    visible_columns = 40
    visible_rows = 22
    max_columns = 200
    max_rows = 200

    def __init__(self) -> None:
        super().__init__()
        self.geometry("+200+40")
        title = "Boulder Caves Editor {version:s} - created by Irmen de Jong - irmen@razorvine.net".format(version=__version__)
        self.wm_title(title)
        self.appicon = tkinter.PhotoImage(data=pkgutil.get_data(__name__, "../gfx/gdash_icon_48.gif"))
        self.wm_iconphoto(self, self.appicon)
        if sys.platform == "win32":
            # tell windows to use a new toolbar icon
            import ctypes
            myappid = 'net.Razorvine.Bouldercaves.editor'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        cf = tkinter.Frame(self)
        w, h = tiles.tile2pixels(self.visible_columns, self.visible_rows)
        self.canvas = tkinter.Canvas(cf, width=w * 2, height=h * 2, borderwidth=8,
                                     highlightthickness=6, background="red", highlightcolor="#206040")
        self.canvas.grid(row=0, column=0)
        sy = tkinter.Scrollbar(cf, orient=tkinter.VERTICAL, command=self.canvas.yview)
        sx = tkinter.Scrollbar(cf, orient=tkinter.HORIZONTAL, command=self.canvas.xview)
        self.canvas["xscrollcommand"] = sx.set
        self.canvas["yscrollcommand"] = sy.set
        sy.grid(row=0, column=1, sticky=tkinter.N + tkinter.S)
        sx.grid(row=1, column=0, sticky=tkinter.E + tkinter.W)
        cf.pack(side=tkinter.RIGHT, padx=4, pady=4, fill=tkinter.BOTH, expand=1)
        buttonsframe = tkinter.Frame(self)
        lf = tkinter.LabelFrame(buttonsframe, text="Select object")
        self.imageselector = ScrollableImageSelector(lf, self)
        self.imageselector.pack()
        f = tkinter.Frame(lf)
        tkinter.Label(f, text=" Draw: \n(Lmb)").grid(row=0, column=0)
        self.draw_label = tkinter.Label(f)
        self.draw_label.grid(row=0, column=1)
        tkinter.Label(f, text=" Erase: \n(Rmb)").grid(row=0, column=2)
        self.erase_label = tkinter.Label(f)
        self.erase_label.grid(row=0, column=3)
        tkinter.Label(f, text="Select for draw,\ndoubleclick to set erase.").grid(row=1, column=0, columnspan=4)
        f.pack(pady=4)
        lf.pack(expand=1, fill=tkinter.Y)
        lf = tkinter.LabelFrame(buttonsframe, text="Keyboard commands")
        tkinter.Label(lf, text="F - flood fill").pack(anchor=tkinter.W, padx=4)
        tkinter.Label(lf, text="S - make snapshot").pack(anchor=tkinter.W, padx=4)
        tkinter.Label(lf, text="R - restore snapshot").pack(anchor=tkinter.W, padx=4)
        lf.pack(expand=1, fill=tkinter.Y)
        tkinter.Button(buttonsframe, text="Randomize", command=self.randomize).pack()
        tkinter.Button(buttonsframe, text="Wipe", command=self.wipe).pack()
        buttonsframe.pack(side=tkinter.LEFT, anchor=tkinter.N)
        self.buttonsframe = buttonsframe
        self.bind("<KeyPress>", self.keypress)
        self.bind("<KeyRelease>", self.keyrelease)
        self.canvas.bind("<Button-1>", self.mousebutton_left)
        self.canvas.bind("<Button-2>", self.mousebutton_middle)
        self.canvas.bind("<Button-3>", self.mousebutton_right)
        self.canvas.bind("<Motion>", self.mouse_motion)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.c_tiles = []      # type: List[str]
        self.tile_images = []  # type: List[tkinter.PhotoImage]
        self.c64colors = False
        self.playfield_rows = self.playfield_columns = 0
        self.canvas_tag_to_tilexy = {}      # type: Dict[int, Tuple[int, int]]
        self.create_tile_images()
        self.create_canvas_playfield(40, 22)
        w, h = tiles.tile2pixels(self.playfield_columns, self.playfield_rows)
        self.canvas.configure(scrollregion=(0, 0, w * 2, h * 2))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.populate_imageselector()
        self.draw_label.configure(image=self.tile_images[self.imageselector.selected_tile])
        self.erase_label.configure(image=self.tile_images[self.imageselector.selected_erase_tile])
        self.wipe(False)
        self.randomize_initial_values = None   # type: Tuple

    def init_new_cave(self, only_steel_border=False):
        if not only_steel_border:
            self.cave = Cave(self.playfield_columns, self.playfield_rows, self)
        steel = (Objects.STEEL, Objects.STEEL.tile())
        self.cave.horiz_line(0, 0, self.playfield_columns, steel)
        self.cave.horiz_line(0, self.playfield_rows - 1, self.playfield_columns, steel)
        self.cave.vert_line(0, 1, self.playfield_rows - 2, steel)
        self.cave.vert_line(self.playfield_columns - 1, 1, self.playfield_rows - 2, steel)
        if not only_steel_border:
            self.flood_fill(2, 2, (Objects.DIRT, EDITOR_OBJECTS[Objects.DIRT]))

    def populate_imageselector(self):
        rows = []
        for obj, displaytile in sorted(EDITOR_OBJECTS.items(), key=lambda t: t[0].name):
            rows.append((self.tile_images_small[displaytile], obj.name.title()))
        self.imageselector.populate(rows)

    def destroy(self) -> None:
        super().destroy()

    def keypress(self, event) -> None:
        if event.char == 'f':
            current = self.canvas.find_withtag(tkinter.CURRENT)
            if current:
                tx, ty = self.canvas_tag_to_tilexy[current[0]]
                self.flood_fill(tx, ty, (self.imageselector.selected_object, self.imageselector.selected_tile))
        elif event.char == 's':
            self.snapshot()
        elif event.char == 'r':
            self.restore()

    def keyrelease(self, event) -> None:
        pass

    def mousebutton_left(self, event) -> None:
        self.canvas.focus_set()
        current = self.canvas.find_withtag(tkinter.CURRENT)
        if current:
            if self.imageselector.selected_object:
                x, y = self.canvas_tag_to_tilexy[current[0]]
                self.cave[x, y] = (self.imageselector.selected_object, self.imageselector.selected_tile)

    def mousebutton_middle(self, event) -> None:
        pass

    def mousebutton_right(self, event) -> None:
        current = self.canvas.find_withtag(tkinter.CURRENT)
        if current:
            x, y = self.canvas_tag_to_tilexy[current[0]]
            self.cave[x, y] = (self.imageselector.selected_erase_object, self.imageselector.selected_erase_tile)

    def mouse_motion(self, event) -> None:
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        current = self.canvas.find_closest(cx, cy)
        if current:
            x, y = self.canvas_tag_to_tilexy[current[0]]
            if event.state & 0x100:
                # left mouse button drag
                self.cave[x, y] = (self.imageselector.selected_object, self.imageselector.selected_tile)
            elif event.state & 0x600:
                # right / middle mouse button drag
                self.cave[x, y] = (self.imageselector.selected_erase_object, self.imageselector.selected_erase_tile)

    def create_tile_images(self) -> None:
        source_images = tiles.load_sprites(self.c64colors, colorpalette[2], colorpalette[14], colorpalette[13], 0, scale=2)
        self.tile_images = [tkinter.PhotoImage(data=image) for image in source_images]
        source_images = tiles.load_sprites(self.c64colors, colorpalette[2], colorpalette[14], colorpalette[13], 0, scale=1)
        self.tile_images_small = [tkinter.PhotoImage(data=image) for image in source_images]

    def create_canvas_playfield(self, width: int, height: int) -> None:
        # create the images on the canvas for all tiles (fixed position):
        if width == self.playfield_columns and height == self.playfield_rows:
            return
        if width < 4 or width > 200 or height < 4 or height > 200:
            raise ValueError("invalid playfield/cave width or height")
        self.playfield_columns = width
        self.playfield_rows = height
        self.canvas.delete(tkinter.ALL)
        self.c_tiles.clear()
        self.canvas_tag_to_tilexy.clear()
        boulder_tile = Objects.DIRT2.tile()
        for y in range(self.playfield_rows):
            for x in range(self.playfield_columns):
                sx, sy = tiles.tile2pixels(x, y)
                tile = self.canvas.create_image(sx * 2, sy * 2, image=self.tile_images[boulder_tile],
                                                activeimage=self.tile_images[self.imageselector.selected_tile],
                                                anchor=tkinter.NW, tags="tile")
                self.c_tiles.append(tile)
                self.canvas_tag_to_tilexy[tile] = (x, y)

    def tile_selection_changed(self, object: GameObject, tile: int) -> None:
        image = self.tile_images[tile]
        self.draw_label.configure(image=image)
        for c_tile in self.c_tiles:
            self.canvas.itemconfigure(c_tile, activeimage=image)

    def tile_erase_selection_changed(self, object: GameObject, tile: int) -> None:
        image = self.tile_images[tile]
        self.erase_label.configure(image=image)

    def set_tile(self, x: int, y: int, tile: int) -> None:
        c_tile = self.canvas.find_closest(x * 32, y * 32)
        self.canvas.itemconfigure(c_tile, image=self.tile_images[tile])

    def flood_fill(self, x: int, y: int, thing: Tuple[GameObject, int]) -> None:
        target = self.cave[x, y][0]
        if target == thing[0]:
            return

        def flood(x, y):
            t = self.cave[x, y][0]
            if t != target:
                return
            self.cave[x, y] = thing
            flood(x - 1, y)
            flood(x + 1, y)
            flood(x, y - 1)
            flood(x, y + 1)

        flood(x, y)

    def snapshot(self) -> None:
        self.cave.snapshot()

    def restore(self) -> None:
        self.cave.restore()

    def wipe(self, confirm=True) -> None:
        if confirm and not tkinter.messagebox.askokcancel("Confirm", "Wipe cave?", parent=self.buttonsframe):
            return
        self.init_new_cave()
        self.snapshot()

    def randomize(self) -> None:
        RandomizeDialog(self.buttonsframe, "Randomize Cave", self, self.randomize_initial_values)

    def do_random_fill(self, rseed: int, randomprobs: Tuple[int, int, int, int], randomobjs: Tuple[str, str, str, str]) -> None:
        randomseeds = [0, rseed]
        for y in range(1, self.playfield_rows - 1):
            for x in range(0, self.playfield_columns):
                objname = Objects.DIRT.name.lower()
                C64Cave.bdrandom(randomseeds)
                for randomobj, randomprob in zip(randomobjs, randomprobs):
                    if randomseeds[0] < randomprob:
                        objname = randomobj.lower()

                for obj, displaytile in EDITOR_OBJECTS.items():
                    if obj.name.lower() == objname:
                        self.cave[x, y] = (obj, displaytile)
        self.init_new_cave(only_steel_border=True)
        self.randomize_initial_values = (rseed, randomprobs, randomobjs)


class RandomizeDialog(tkinter.simpledialog.Dialog):
    def __init__(self, parent, title, editor, initial_values):
        self.editor = editor
        self.initial_values = initial_values
        super().__init__(parent=parent, title=title)

    def body(self, master):
        if not self.initial_values:
            self.initial_values = (199, (100, 60, 25, 15),
                                   (Objects.EMPTY.name, Objects.BOULDER.name, Objects.DIAMOND.name, Objects.FIREFLY.name))
        self.rseed_var = tkinter.IntVar(value=self.initial_values[0])
        self.rp1_var = tkinter.IntVar(value=self.initial_values[1][0])
        self.rp2_var = tkinter.IntVar(value=self.initial_values[1][1])
        self.rp3_var = tkinter.IntVar(value=self.initial_values[1][2])
        self.rp4_var = tkinter.IntVar(value=self.initial_values[1][3])
        self.robj1_var = tkinter.StringVar(value=self.initial_values[2][0].title())
        self.robj2_var = tkinter.StringVar(value=self.initial_values[2][1].title())
        self.robj3_var = tkinter.StringVar(value=self.initial_values[2][2].title())
        self.robj4_var = tkinter.StringVar(value=self.initial_values[2][3].title())
        tkinter.Label(master, text="Fill the cave with randomized stuff, using the C-64 BD randomizer.\n").pack()
        f = tkinter.Frame(master)
        tkinter.Label(f, text="Random seed (0-255): ").grid(row=0, column=0)
        tkinter.Label(f, text="Random probability (0-255): ").grid(row=1, column=0)
        tkinter.Label(f, text="Random probability (0-255): ").grid(row=2, column=0)
        tkinter.Label(f, text="Random probability (0-255): ").grid(row=3, column=0)
        tkinter.Label(f, text="Random probability (0-255): ").grid(row=4, column=0)
        rseed = tkinter.Entry(f, textvariable=self.rseed_var, width=4, font="monospace")
        rp1 = tkinter.Entry(f, textvariable=self.rp1_var, width=4, font="monospace")
        rp2 = tkinter.Entry(f, textvariable=self.rp2_var, width=4, font="monospace")
        rp3 = tkinter.Entry(f, textvariable=self.rp3_var, width=4, font="monospace")
        rp4 = tkinter.Entry(f, textvariable=self.rp4_var, width=4, font="monospace")
        rseed.grid(row=0, column=1)
        rp1.grid(row=1, column=1)
        rp2.grid(row=2, column=1)
        rp3.grid(row=3, column=1)
        rp4.grid(row=4, column=1)
        options = sorted([obj.name.title() for obj in EDITOR_OBJECTS])
        tkinter.OptionMenu(f, self.robj1_var, *options).grid(row=1, column=2, stick=tkinter.W)
        tkinter.OptionMenu(f, self.robj2_var, *options).grid(row=2, column=2, stick=tkinter.W)
        tkinter.OptionMenu(f, self.robj3_var, *options).grid(row=3, column=2, stick=tkinter.W)
        tkinter.OptionMenu(f, self.robj4_var, *options).grid(row=4, column=2, stick=tkinter.W)
        f.pack()
        tkinter.Label(master, text="\n\nWARNING: DOING THIS WILL WIPE THE CURRENT CAVE!").pack()
        return rp1

    def validate(self):
        try:
            vs = self.rseed_var.get()
            v1 = self.rp1_var.get()
            v2 = self.rp1_var.get()
            v3 = self.rp1_var.get()
            v4 = self.rp1_var.get()
        except tkinter.TclError as x:
            tkinter.messagebox.showerror("Invalid entry", str(x), parent=self)
            return False
        else:
            if not (0 <= vs <= 255) or not (0 <= v1 <= 255) or not(0 <= v2 <= 255) or not(0 <= v3 <= 255) or not(0 <= v4 <= 255):
                tkinter.messagebox.showerror("Invalid entry", "One or more of the values is invalid.", parent=self)
                return False
        return True

    def apply(self):
        vs = self.rseed_var.get()
        v1 = self.rp1_var.get()
        v2 = self.rp2_var.get()
        v3 = self.rp3_var.get()
        v4 = self.rp4_var.get()
        o1 = self.robj1_var.get()
        o2 = self.robj2_var.get()
        o3 = self.robj3_var.get()
        o4 = self.robj4_var.get()
        self.editor.do_random_fill(vs, (v1, v2, v3, v4), (o1, o2, o3, o4))


def start() -> None:
    window = EditorWindow()
    window.mainloop()


if __name__ == "__main__":
    start()
