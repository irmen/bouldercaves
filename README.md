# Boulder Caves
A Boulder Dash (tm) clone in pure python. Includes a cave editor so you can make your own game!

Requirements to run this:
- Python 3.5 +
- ``pillow`` (or ``pil``) python library
- ``sounddevice`` python library, if you want to play with sound.

*Detailed instructions how to run the game are [at the bottom of this text.](#how-to-install-and-run-this-game)*

This software is licensed under the [GNU GPL 3.0](https://www.gnu.org/licenses/gpl.html).
Graphics and sampled sounds are used from the MIT-licensed [GDash](https://bitbucket.org/czirkoszoltan/gdash). 


Inspired by the [javascript version from Jake Gordon](http://codeincomplete.com/posts/javascript-boulderdash/)


Much technical info about Boulder Dash can be found here https://www.elmerproductions.com/sp/peterb/
and here https://www.boulder-dash.nl/


There are a few command line options to control the graphics of the game, the zoom level,
and the graphics update speed (fps).
On Linux the game runs very well, on Windows and Mac OS it can have some troubles. 
If you experience graphics slowdown issues or the game prints that it cannot refresh
the screen fast enough, try adjusting the parameters on the command line.

## Screenshot

![a level](screenshots/screenshot2.png?raw=true "Screenshot of a level in progress")


## Objective and rules of the game

- Collect enough diamonds to open the exit to go to the next level!
- Extra diamonds grant bonus points, and time left is added to your score as well.
- Avoid monsters or use them to your advantage.
- Some brick walls are not simply what they seem. 
- Amoeba grows and grows but it is often worthwhile to contain it. Sometimes you have
  to set it free first.
- Slime is permeable to boulders and diamonds but you cannot go through it yourself.  
- *Intermission* levels are bonus stages where you have one chance to complete them.
You won't lose a life here if you die, but you only have one attempt at solving it.
- A small high score table is saved. 


## Controls

You control the game via the keyboard:

- Cursorkeys UP, DOWN, LEFT, RIGHT: move your hero.
- with SHIFT: grab or push something in adjacent place without moving yourself.
- ESC: lose a life and restart the level. When game over, returns to title screen.
- Space: pause/continue the game.
- F1: start a new game, or skip popup screen wait.
- F5: cheat and add an extra life.  No highscore will be recorded if you use this.
- F6: cheat and add 10 seconds extra time.   No highscore will be recorded if you use this.
- F7: cheat and skip to the next level.   No highscore will be recorded if you use this.
- F8: randomize colors (only when using Commodore-64 colors)
- F9: replay prerecorded demo (from title screen)
- F12: launch cave editor


## Sound

You can choose between *sampled sounds* and *synthesized sounds* via a command line option.

The sampled sounds require the 'oggdec' tool and the sound files. If you use the 
sound synthesizer however, both of these are not needed at all - all sounds are generated
by the program. For this I'm using a copy of [my software FM-synthesizer](https://github.com/irmen/synthesizer).

The Python zip app script creates two versions of this game, one with the sound files included,
and another one ()that is much smaller) without the sound files because it uses the synthesizer.


## The title screen

![Boulder Caves title screen](screenshots/screenshot.png?raw=true "Screenshot of the title screen")


## Screenshot of 'authentic' C-64 mode

![a level](screenshots/screenshot3.png?raw=true "Screenshot of the game runnig in 'authentic' C-64 mode")


## Screenshot of the Editor

![The editor in acation](screenshots/screenshot4.png?raw=true "Screenshot of the cave editor with a C-64 color palette")


## How to install and run this game

All platforms: if you just want to *play* the game and are not interested in the code,
you can simply download one of the Python zip apps (*.pyz) files that can be found
on the releases tab. The small one with 'synth' in the name uses synthesized sounds
while the larger one uses sampled sounds. 

If you run the game from a command prompt, you are able to tweak some command line settings.
To see what is available just use the ``-h`` (help) argument.

The original BD1 levels are built-in. With the ``-g`` (game) command line argument you can 
load external level files in BDCFF format. Hundreds of these can be found on 
https://www.boulder-dash.nl/  on the BDCFF format page.  A couple of them are included
in the 'caves' folder.


**Windows**

Did you download only a ```*.pyz``` file? Do this:
1. install Python 3.5 or newer from https://www.python.org/downloads/
1. open a command prompt and type:
   ``pip install --user pillow sounddevice``
1. double-click on the ``*.pyz`` file that you downloaded.

If you downloaded the source code, you can simply launch the game
by clicking on ``startgame-venv.py``  (that should take care of installing the
required libraries for you).  The other script, ``startgame.py`` also works, but
it requires you to have installed the libraries yourself (step 2 above).


**Mac OS, Linux, ...**

Make sure you have Python 3.5 or newer installed, with Tkinter (Python's default GUI toolkit).
On Linux it's probably easiest to install these via your distribution's package manager.
On Mac OS, personally I'm using [Homebrew](https://brew.sh) to install things
(I've used the "``brew install python3 --with-tcl-tk``" command to make sure it doesn't use Apple's
own version of the tcl/tk library, which is buggy, but a newer version).

If you don't want to bother with installing the required libraries yourself, 
just launch the ``startgame-venv.py`` script and it will take care of that for you.

Alternatively:

1. make sure you have the ``pillow`` (or ``pil``) and ``sounddevice`` python libraries 
   installed. You can often find them in your package manager or install them with pip.
1. if you want to play the version with synthesized sounds, you're all set.
1. if you want to play the version with sampled sounds, make sure you have the
   ``oggdec`` tool installed as well (usually available as part of the ``vorbis-tools`` package)
1. type ``python3 startgame.py``  or just execute the python zip app ``*.pyz`` file if you
   downloaded that.  If ``python3`` doesn't work just try ``python`` instead. 
