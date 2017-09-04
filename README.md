# Boulder Caves
A Boulder Dash (tm) clone in pure python.
Requires Python 3.5 + and the ``pillow`` library.

Graphics and sounds are used from the MIT-licensed GDash https://bitbucket.org/czirkoszoltan/gdash

Inspired by the javascript version from Jake Gordon http://codeincomplete.com/posts/javascript-boulderdash/

There are a few command line options to control the graphics of the game, the zoom level,
and the graphics update speed (fps).
On Linux the game runs very well, on Windows and Mac OS it can have some troubles. 
If you experience graphics slowdown issues or the game prints that it cannot refresh
the screen fast enough, try adjusting the parameters on the command line.

## Screenshot

![Boulder Caves title screen](screenshot.png?raw=true "Screenshot of the title screen")


## Objective and rules of the game

Collect enough diamonds to open the exit to go to the next level!
Extra diamonds grant bonus points, and time left is added to your score as well.
Avoid monsters or use them to your advantage.
Some brick walls are not simply what they seem. 

'Intermission' levels are bonus stages where you have one chance to complete them.
You won't lose a life here if you die.


## Controls

The game is controlled via the keyboard.

- Cursorkeys UP, DOWN, LEFT, RIGHT: move the hero.
- with SHIFT: grab or push something in adjacent place without moving yourself.
- ESC: lose a life and restart the level. When game over, returns to title screen.
- F1: start a new game. Also skips waiting for popup screens.
- F5: cheat and add an extra life.
- F6: cheat and add 10 seconds extra time.
- F7: cheat and skip to the next level.
- F8: randomize colors (only when using Commodore-64 colors)
