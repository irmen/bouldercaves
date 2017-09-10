# Boulder Caves
A Boulder Dash (tm) clone in pure python.
Requires Python 3.5 + and the ``pillow`` (or ``pil``) library.
Want to hear sound? Install the ``sounddevice`` or ``pyaudio`` library as well, and
the ``oggdec`` tool has to be installed on your system.  Usually that is part of
the ``vorbis-tools`` package (Linux, Mac OS).  On Windows a version of the tool 
is provided for you, and the game *can* optionally use the built-in ``winsound`` module -
but the sound quality will suffer (no mixing possible) 

If you choose to use the built-in sound synthesizer, no sound files and oggdec tool are required at all.
  

Graphics and sounds are used from the MIT-licensed GDash 
https://bitbucket.org/czirkoszoltan/gdash

Inspired by the javascript version from Jake Gordon
http://codeincomplete.com/posts/javascript-boulderdash/

Much technical info about Boulder Dash can be found here https://www.elmerproductions.com/sp/peterb/
and here https://www.boulder-dash.nl/


There are a few command line options to control the graphics of the game, the zoom level,
and the graphics update speed (fps).
On Linux the game runs very well, on Windows and Mac OS it can have some troubles. 
If you experience graphics slowdown issues or the game prints that it cannot refresh
the screen fast enough, try adjusting the parameters on the command line.

## Screenshot

![Boulder Caves title screen](screenshots/screenshot.png?raw=true "Screenshot of the title screen")


## Objective and rules of the game

- Collect enough diamonds to open the exit to go to the next level!
- Extra diamonds grant bonus points, and time left is added to your score as well.
- Avoid monsters or use them to your advantage.
- Some brick walls are not simply what they seem. 
- Amoeba grows and grows but it is often worthwhile to contain it. 
- *Intermission* levels are bonus stages where you have one chance to complete them.
You won't lose a life here if you die.


## Controls

You control the game via the keyboard:

- Cursorkeys UP, DOWN, LEFT, RIGHT: move your hero.
- with SHIFT: grab or push something in adjacent place without moving yourself.
- ESC: lose a life and restart the level. When game over, returns to title screen.
- Space: pause/continue the game.
- F1: start a new game, or skip popup screen wait.
- F5: cheat and add an extra life.
- F6: cheat and add 10 seconds extra time.
- F7: cheat and skip to the next level.
- F8: randomize colors (only when using Commodore-64 colors)
- F9: replay prerecorded demo (from title screen)

## Sound

You can choose between *sampled sounds* and *synthesized sounds* via a command line option.

The sampled sounds require the 'oggdec' tool and the sound files. If you use the 
sound synthesizer however, both of these are not needed at all - all sounds are generated
by the program. For this I'm using a slightly tweaked version of my software FM-synthesizer
available here: https://github.com/irmen/synthesizer

The Python zip app script creates two versions of this game, one with the sound files included,
and another one ()that is much smaller) without the sound files because it uses the synthesizer.


## Screenshot of a level

![a level](screenshots/screenshot2.png?raw=true "Screenshot of a level in progress")


## Screenshot of 'authentic' C-64 mode

![a level](screenshots/screenshot3.png?raw=true "Screenshot of the game runnig in 'authentic' C-64 mode")

