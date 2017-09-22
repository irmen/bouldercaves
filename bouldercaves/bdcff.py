"""
Boulder Caves - a Boulder Dash (tm) clone.

Parser for 'Boulder Dash Common File Format' BDCFF cave files.
Implementation info:
https://www.boulder-dash.nl/
http://www.emeraldmines.net/BDCFF/
http://www.gratissaugen.de/erbsen/bdcff.html

Written by Irmen de Jong (irmen@razorvine.net)
License: MIT open-source.
"""

import sys
import datetime
import getpass
from typing import Dict, List, Any, TextIO, Optional


class BdcffFormatError(Exception):
    pass


class BdcffCave:
    class Map:
        def __init__(self):
            self.maplines = []
            self.width = self.height = 0

        def postprocess(self):
            self.height = len(self.maplines)
            self.width = len(self.maplines[0])

    def __init__(self):
        # create a cave with the defaults from the Bdcff specification
        self.properties = {}
        self.map = self.Map()
        self.intermission = False
        self.cavetime = 200
        self.cavedelay = 8
        self.slimepermeability = 1.0
        self.amoebafactor = 0.2273
        self.amoebatime = 999
        self.magicwalltime = 999
        self.diamonds_required = 10
        self.diamondvalue_normal = self.diamondvalue_extra = 0
        self.width = self.map.width
        self.height = self.map.height
        self.color_screen, self.color_border, self.color_fg1, self.color_fg2, self.color_fg3, \
            self.color_amoeba, self.color_slime = [0, 0, 10, 12, 1, 5, 6]

    def postprocess(self):
        self.name = self.properties.pop("name")
        self.description = self.properties.pop("description", "")
        if not self.description:
            self.description = self.properties.pop("remark", "")
        if self.name.startswith(("Cave ", "Intermission ")):
            self.name = self.name.split(" ", maxsplit=1)[1]
        self.cavedelay = int(self.properties.pop("cavedelay").split()[0])
        self.cavetime = int(self.properties.pop("cavetime").split()[0])
        self.diamonds_required = int(self.properties.pop("diamondsrequired").split()[0])
        dvalue = self.properties.pop("diamondvalue")
        try:
            dv, dve = dvalue.split()
        except ValueError:
            dv = dve = dvalue
        self.diamondvalue_normal = int(dv)
        self.diamondvalue_extra = int(dve)
        self.amoebatime = int(self.properties.pop("amoebatime", str(self.amoebatime)).split()[0])
        self.amoebafactor = float(self.properties.pop("amoebathreshold", str(self.amoebafactor)))
        self.magicwalltime = int(self.properties.pop("magicwalltime", str(self.magicwalltime)).split()[0])
        self.slimepermeability = float(self.properties.pop("slimepermeability", str(self.slimepermeability)))
        colors = [BdcffParser.COLORNAMES.index(c) for c in self.properties.pop("colors").split()]
        self.color_border = 0
        self.color_screen = 0
        self.color_amoeba = 5
        self.color_slime = 6
        if len(colors) == 3:
            self.color_fg1, self.color_fg2, self.color_fg3 = colors
        elif len(colors) == 5:
            self.color_border, self.color_screen, self.color_fg1, self.color_fg2, self.color_fg3 = colors
        elif len(colors) == 7:
            self.color_border, self.color_screen, self.color_fg1, self.color_fg2, self.color_fg3, \
                self.color_amoeba, self.color_slime = colors
        else:
            raise BdcffFormatError("invalid color spec: " + str(colors))
        self.intermission = self.properties.pop("intermission", "false") == "true"
        self.map.postprocess()
        self.height = self.map.height
        self.width = self.map.width
        psize = self.properties.pop("size", None)
        if psize:
            pwidth, pheight = psize.split()[:2]
            pwidth = int(pwidth)
            pheight = int(pheight)
            if pwidth != self.width or pheight != self.height:
                raise BdcffFormatError("cave width or height doesn't match map, in cave "+self.name)
        if self.properties:
            print("\nWARNING: unrecognised cave properties in cave "+self.name+" :")
            print(self.properties, "\n")
        del self.properties

    def write(self, out: TextIO) -> None:
        out.write("[cave]\n")
        out.write("Name={:s} {:s}\n".format("Intermission" if self.intermission else "Cave", self.name))
        out.write("Description={:s}\n".format(self.description))
        out.write("Intermission={:s}\n".format("true" if self.intermission else "false"))
        out.write("CaveDelay={:d}\n".format(self.cavedelay))
        out.write("CaveTime={:d}\n".format(self.cavetime))
        out.write("DiamondsRequired={:d}\n".format(self.diamonds_required))
        out.write("DiamondValue={:d} {:d}\n".format(self.diamondvalue_normal, self.diamondvalue_extra))
        out.write("AmoebaTime={:d}\n".format(self.amoebatime))
        out.write("AmoebaThreshold={:f}\n".format(self.amoebafactor))
        out.write("MagicWallTime={:d}\n".format(self.magicwalltime))
        out.write("SlimePermeability={:.3f}\n".format(self.slimepermeability))
        out.write("Size={:d} {:d}\n".format(self.width, self.height))
        out.write("Colors={:s} {:s} {:s} {:s} {:s} {:s} {:s}\n".format(
            BdcffParser.COLORNAMES[self.color_border],
            BdcffParser.COLORNAMES[self.color_screen],
            BdcffParser.COLORNAMES[self.color_fg1],
            BdcffParser.COLORNAMES[self.color_fg2],
            BdcffParser.COLORNAMES[self.color_fg3],
            BdcffParser.COLORNAMES[self.color_amoeba],
            BdcffParser.COLORNAMES[self.color_slime]))
        out.write("\n[map]\n")
        if len(self.map.maplines) != self.height:
            raise BdcffFormatError("cave height differs from map")
        if len(self.map.maplines) == 0:
            raise BdcffFormatError("no map lines")
        for line in self.map.maplines:
            if len(line) != self.width:
                raise BdcffFormatError("cave width differs from map")
            out.write(line + "\n")
        out.write("[/map]\n")
        out.write("[/cave]\n")


class BdcffParser:
    SECT_BDCFF = 1
    SECT_GAME = 2
    SECT_CAVE = 3
    SECT_MAP = 4
    COLORNAMES = ["Black", "White", "Red", "Cyan", "Purple", "Green", "Blue", "Yellow",
                  "Orange", "Brown", "LightRed", "Gray1", "Gray2", "LightGreen", "LightBlue", "Gray3"]

    def __init__(self, filename: Optional[str]=None) -> None:
        self.state = 0
        self.bdcff_version = ""
        self.game_properties = {}   # type: Dict[str, Any]
        self.caves = []     # type: List[BdcffCave]
        self.current_cave = None    # type: BdcffCave
        self.num_levels = 1
        self.num_caves = 0
        self.charset = self.fontset = "Original"
        self.author = getpass.getuser()
        self.www = ""
        self.date = str(datetime.datetime.now().date())
        self.name = "Unnamed"
        self.description = ""
        if filename:
            with open(filename, "rU") as f:
                for line in f:
                    line = line.rstrip('\n')
                    if line and not line.startswith(';'):
                        self.parse(line)
            self.postprocess()
            self.validate()

    def write(self, out: TextIO) -> None:
        if self.num_levels != 1:
            raise BdcffFormatError("only supports files with 1 difficulty level")
        if self.num_caves != len(self.caves):
            raise BdcffFormatError("number of caves differs from game property")
        out.write("; written by Bouldercaves.Bdcff by Irmen de Jong\n")
        out.write("; last modified {:s}\n".format(str(datetime.datetime.now().date())))
        out.write("\n[BDCFF]\n[game]\n")
        out.write("Name={:s}\n".format(self.name))
        if self.description:
            out.write("Description={:s}\n".format(self.name))
        out.write("Author={:s}\n".format(self.author))
        out.write("WWW={:s}\n".format(self.www))
        out.write("Date={:s}\n".format(self.date))
        out.write("Charset={:s}\n".format(self.charset))
        out.write("Fontset={:s}\n".format(self.fontset))
        out.write("Levels={:d}\n".format(self.num_levels))
        out.write("Caves={:d}\n".format(self.num_caves))
        out.write("\n")
        for cave in self.caves:
            cave.write(out)
            out.write("")
        out.write("\n[/game]\n[/BDCFF]\n")

    def postprocess(self) -> None:
        self.num_levels = int(self.game_properties.pop("levels"))
        self.num_caves = int(self.game_properties.pop("caves", 0))
        self.name = self.game_properties.pop("name")
        self.description = self.game_properties.pop("description", "")
        self.author = self.game_properties.pop("author", "")
        self.www = self.game_properties.pop("www", "")
        self.date = self.game_properties.pop("date", "")
        self.charset = self.game_properties.pop("charset", "Original")
        self.fontset = self.game_properties.pop("fontset", "Original")
        if self.game_properties:
            print("\nWARNING: unrecognised bdcff properties:")
            print(self.game_properties, "\n")
        del self.game_properties
        for cave in self.caves:
            cave.postprocess()
        self.num_caves = self.num_caves or len(self.caves)
        del self.current_cave
        del self.state

    def validate(self) -> None:
        if self.charset != "Original" or self.fontset != "Original":
            raise BdcffFormatError("invalid or unsupported cave data")
        if self.num_caves <= 0 or self.num_caves != len(self.caves):
            raise BdcffFormatError("invalid number of caves")
        if self.num_levels != 1:
            print("WARNING: only supports loading the first difficulty level")

    def parse(self, line: str) -> None:
        if line == '[BDCFF]' and self.state == 0:
            self.state = self.SECT_BDCFF
        elif line == '[game]' and self.state == self.SECT_BDCFF:
            self.state = self.SECT_GAME
        elif line == '[cave]' and self.state == self.SECT_GAME:
            self.current_cave = BdcffCave()
            self.caves.append(self.current_cave)
            self.state = self.SECT_CAVE
        elif line == '[map]' and self.state == self.SECT_CAVE:
            self.state = self.SECT_MAP
        elif line == '[/map]' and self.state == self.SECT_MAP:
            self.state = self.SECT_CAVE
        elif line == '[/cave]' and self.state == self.SECT_CAVE:
            self.current_cave = None
            self.state = self.SECT_GAME
        elif line == '[/game]' and self.state == self.SECT_GAME:
            self.state = self.SECT_BDCFF
        elif line == '[/BDCFF]' and self.state == self.SECT_BDCFF:
            pass
        elif line.startswith('[') and line.endswith(']'):
            raise BdcffFormatError("invalid tag: " + line)
        else:
            self.process_line(line)

    def process_line(self, line: str) -> None:
        if self.state == self.SECT_BDCFF:
            if line.startswith("Version="):
                self.bdcff_version = line.split("=")[1]
            else:
                raise BdcffFormatError("bdcff parse error, state=" + str(self.state) + " line=" + line)
        elif self.state == self.SECT_GAME:
            prop, value = line.split("=")
            self.game_properties[prop.lower()] = value
        elif self.state == self.SECT_CAVE:
            prop, value = line.split("=")
            self.current_cave.properties[prop.lower()] = value
        elif self.state == self.SECT_MAP:
            self.current_cave.map.maplines.append(line)
        else:
            raise BdcffFormatError("bdcff parse error, state=" + str(self.state) + " line=" + line)


if __name__ == "__main__":
    cave = BdcffParser(sys.argv[1])
    cave.write(sys.stdout)
