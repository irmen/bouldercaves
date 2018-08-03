from PIL import Image, ImageDraw

x,y = 32, 35
for num in range(1, 14):
    img = Image.open("ss{}.png".format(num))
    img=img.crop((x,y, x+16*16, y+16))

    for tilenum in range(8):
        tile = img.crop((tilenum*32, 0, tilenum*32+16, 16))
        img.paste(tile, (tilenum*16, 0))

    img = img.crop((0, 0, 16*8, 16))
    img=img.convert('P', palette=Image.ADAPTIVE, colors=4)
    palettevalues = img.getpalette()
    palette = [(r, g, b) for r, g, b in zip(palettevalues[0:16 * 3:3], palettevalues[1:16 * 3:3], palettevalues[2:16 * 3:3])]
    if (255, 255, 255) in palette:
        pc1 = palette.index((255, 255, 255))
        palette[pc1] = (255, 255, 0)
    if (0xea, 0x74, 0x6c) in palette:
        pc1 = palette.index((0xea, 0x74, 0x6c))
        palette[pc1] = (255, 0, 0)
    if (0x37, 0x39, 0xc4) in palette:
        pc1 = palette.index((0x37, 0x39, 0xc4))
        palette[pc1] = (255, 0, 255)
    assert all(p in [(255, 255, 0), (255, 0, 255), (255, 0, 0), (0, 0, 0)] for p in palette)
    palettevalues = []
    for rgb in palette:
        palettevalues.extend(rgb)
    img.putpalette(palettevalues)
    img.save("ss{}_crop.png".format(num))

# replace the tiles that have new versions
c64 = Image.open("bouldercaves/gfx/c64_gfx_orig.png")
diamonds = Image.open("ss1_crop.png")
c64.paste(diamonds, (0, 31*16))
butterfly = Image.open("ss5_crop.png")
c64.paste(butterfly, (0, 17*16))
firefly = Image.open("ss13_crop.png")
c64.paste(firefly, (0, 18*16))
left = Image.open("ss3_crop.png")
c64.paste(left, (0, 29*16))
right = Image.open("ss4_crop.png")
c64.paste(right, (0, 30*16))

assorted = Image.open("ss6_crop.png")
boulder = assorted.crop((0,0,16,16))
c64.paste(boulder, (16, 0))
dirt = assorted.crop((16,0,32,16))
c64.paste(dirt, (32, 0))
steelwall = assorted.crop((32,0,48,16))
c64.paste(steelwall, (4*16, 0))
c64.paste(steelwall, (6*16, 2*16))
brickwall = assorted.crop((48,0,64,16))
c64.paste(brickwall, (5*16, 0))
inbox = assorted.crop((5*16,0,6*16,16))
c64.paste(inbox, (7*16, 2*16))
explosion1 = assorted.crop((6*16,0, 7*16, 16))
explosion2 = assorted.crop((7*16,0, 8*16, 16))
c64.paste(explosion1, (3*16, 5*16))
c64.paste(explosion1, (7*16, 5*16))
c64.paste(explosion2, (4*16, 5*16))
c64.paste(explosion2, (6*16, 5*16))
rockfordface = Image.open("ss2_crop.png")
c64.paste(rockfordface, (0, 26*16))
c64.paste(rockfordface, (0, 27*16))
c64.paste(rockfordface, (0, 28*16))

assorted = Image.open("ss7_crop.png")
explosion3 = assorted.crop((0,0, 16,16))
c64.paste(explosion3, (5*16, 5*16))
diamondbirth1 = assorted.crop((1*16, 0, 2*16, 16))
diamondbirth2 = assorted.crop((2*16, 0, 3*16, 16))
diamondbirth3 = assorted.crop((3*16, 0, 4*16, 16))
diamondbirth4 = assorted.crop((4*16, 0, 5*16, 16))
diamondbirth5 = assorted.crop((5*16, 0, 6*16, 16))
c64.paste(diamondbirth1, (0*16, 7*16))
c64.paste(diamondbirth2, (1*16, 7*16))
c64.paste(diamondbirth3, (2*16, 7*16))
c64.paste(diamondbirth4, (3*16, 7*16))
c64.paste(diamondbirth5, (4*16, 7*16))

amoeba = Image.open("ss8_crop.png")
c64.paste(amoeba, (0, 24*16))
slime = Image.open("ss10_crop.png")
c64.paste(slime, (0, 25*16))

assorted = Image.open("ss9_crop.png")
magicwall1 = assorted.crop((0*16, 0, 1*16, 16))
magicwall2 = assorted.crop((1*16, 0, 2*16, 16))
magicwall3 = assorted.crop((2*16, 0, 3*16, 16))
magicwall4 = assorted.crop((3*16, 0, 4*16, 16))
c64.paste(magicwall1, (0, 23*16))
c64.paste(magicwall2, (1*16, 23*16))
c64.paste(magicwall3, (2*16, 23*16))
c64.paste(magicwall4, (3*16, 23*16))
c64.paste(magicwall1, (4*16, 23*16))
c64.paste(magicwall2, (5*16, 23*16))
c64.paste(magicwall3, (6*16, 23*16))
c64.paste(magicwall4, (7*16, 23*16))
rockford = assorted.crop((4*16,0, 5*16,16))
c64.paste(rockford, (3*16, 4*16))

assorted = Image.open("ss11_crop.png")
switch1 = assorted.crop((0*16, 0, 1*16, 16))
switch2 = assorted.crop((1*16, 0, 2*16, 16))
sokoban = assorted.crop((7*16, 0, 8*16, 16))
c64.paste(switch1, (2*16, 2*16))
c64.paste(switch2, (3*16, 2*16))
c64.paste(sokoban, (5*16, 2*16))

assorted = Image.open("ss12_crop.png")
bomb = assorted.crop((0*16, 0, 1*16, 16))
sweet = assorted.crop((1*16, 0, 2*16, 16))
acid = assorted.crop((2*16, 0, 3*16, 16))
gravestone = assorted.crop((3*16, 0, 4*16, 16))
diamondkey = assorted.crop((4*16, 0, 5*16, 16))
lockeddiamond = assorted.crop((5*16, 0, 6*16, 16))
mutantstone = assorted.crop((6*16, 0, 7*16, 16))
c64.paste(bomb, (0, 6*16))
c64.paste(acid, (4*16, 2*16))
c64.paste(diamondkey, (3*16,16))
c64.paste(lockeddiamond, (2*16,16))



c64.save("bouldercaves/gfx/c64_gfx.png")