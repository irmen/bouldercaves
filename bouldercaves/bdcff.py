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
from typing import Dict, List, Any


class BdcffFormatError(Exception):
    pass


class BdcffParser:
    SECT_BDCFF = 1
    SECT_GAME = 2
    SECT_CAVE = 3
    SECT_MAP = 4

    class Cave:
        def __init__(self):
            self.properties = {}
            self.map = None
            self.intermission = False

        def postprocess(self):
            self.name = self.properties.pop("name")
            if self.name.startswith(("Cave ", "Intermission ")):
                self.name = self.name.split(" ", maxsplit=1)[1]
            self.cavedelay = int(self.properties.pop("cavedelay"))
            self.cavetime = int(self.properties.pop("cavetime"))
            self.diamonds_required = int(self.properties.pop("diamondsrequired"))
            dvalue = self.properties.pop("diamondvalue")
            try:
                dv, dve = dvalue.split()
            except ValueError:
                dv = dve = dvalue
            self.diamondvalue_normal = int(dv)
            self.diamondvalue_extra = int(dve)
            self.amoebatime = int(self.properties.pop("amoebatime", 200))
            self.magicwalltime = int(self.properties.pop("magicwalltime", 0))
            self.slimepermeability = float(self.properties.pop("slimepermeability", 0))  # @todo implement slime
            c64colors = ["black", "white", "red", "cyan", "purple", "green", "blue", "yellow",
                         "orange", "brown", "lightred", "gray1", "gray2", "lightgreen", "lightblue", "gray3"]
            colors = [c64colors.index(c.lower()) for c in self.properties.pop("colors").split()]
            self.color_border = 0
            self.color_screen = 0
            self.color_amoeba = 0   # @todo extra color ???
            self.color_slime = 0    # @todo extra color ???
            if len(colors) == 3:
                self.color_fg1, self.color_fg2, self.color_fg3 = colors
            elif len(colors) == 5:
                self.color_border, self.color_screen, self.color_fg1, self.color_fg2, self.color_fg3 = colors
            elif len(colors) == 7:
                self.color_border, self.color_screen, self.color_fg1, self.color_fg2, self.color_fg3,\
                    self.color_amoeba, self.color_slime = colors
            else:
                raise BdcffFormatError("invalid color spec: " + str(colors))
            self.intermission = self.properties.pop("intermission", "false") == "true"
            if self.properties:
                raise BdcffFormatError("unrecognised cave properties:" + str(self.properties))
            self.map.postprocess()
            self.height = self.map.height
            self.width = self.map.width
            del self.properties

    class Map:
        def __init__(self):
            self.maplines = []
            self.width = self.height = 0

        def postprocess(self):
            self.height = len(self.maplines)
            self.width = len(self.maplines[0])

    def __init__(self, filename: str) -> None:
        self.state = 0
        self.bdcff_version = ""
        self.game_properties = {}   # type: Dict[str, Any]
        self.caves = []     # type: List[BdcffParser.Cave]
        self.current_cave = None    # type: BdcffParser.Cave
        with open(filename, "rt") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(';'):
                    self.parse(line)
        self.postprocess()
        self.validate()

    def postprocess(self) -> None:
        self.game_properties["levels"] = int(self.game_properties["levels"])
        self.game_properties["caves"] = int(self.game_properties["caves"])
        for cave in self.caves:
            cave.postprocess()
        del self.current_cave
        del self.state

    def validate(self) -> None:
        if self.game_properties["charset"] != "Original" or \
                self.game_properties["fontset"] != "Original" or \
                self.game_properties["levels"] != 1 or \
                self.game_properties["caves"] != len(self.caves):
            raise BdcffFormatError("invalid or unsupported cave data")
        for cave in self.caves:
            if cave.color_slime != 0 or cave.color_amoeba != 0:
                raise BdcffFormatError("unsupported cave slime/amoeba color(s) in cave "+str(cave.name))

    def dump(self) -> None:
        print("BDCFF Cave set")
        print("version:", self.bdcff_version)
        print("name: ", self.game_properties["name"])
        print("author: ", self.game_properties["author"])
        print("www: ", self.game_properties["www"])
        print("date: ", self.game_properties["date"])
        print("caves: {:d}".format(len(self.caves)))

    def parse(self, line: str) -> None:
        if line == '[BDCFF]' and self.state == 0:
            self.state = self.SECT_BDCFF
        elif line == '[game]' and self.state == self.SECT_BDCFF:
            self.state = self.SECT_GAME
        elif line == '[cave]' and self.state == self.SECT_GAME:
            self.current_cave = self.Cave()
            self.caves.append(self.current_cave)
            self.state = self.SECT_CAVE
        elif line == '[map]' and self.state == self.SECT_CAVE:
            self.current_cave.map = self.Map()
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
    cave.dump()
