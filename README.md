<img src="resources/icon.png" align="right" height="100"/>

# JParty
_A Jeopardy! simulator_

Homepage: https://www.stuartthomas.us/jparty/

Ever wanted to play the game show Jeopardy? This Python-based application aims to provide a full _Jeopardy!_ simulator complete with real questions from actual games. This game is perfect for parties and takes 3-4 players. For ideal usage, plug a TV into to a laptop, setting the laptop as the main monitor, instruct contestants to navigate to the local IP address on the screen. The person with the laptop is "Alex" and runs the game.

## How does it work?
JParty scrapes the J-Archive (https://j-archive.com) to download a previously-played game and then simulates that on the screen. JParty then uses PyQt6 to produce a GUI that simuates the motions of a full _Jeopardy!_ game. A `tornado` web server uses WebSockets to connect to the contestants' smartphones.

## Screenshots:

Welcome screen:

<img src="screenshots/welcome_screen.png" height="300"/>

The main game board:

<img src="screenshots/main_board.png" height="300"/>

The "Alex" player sees the answer on the laptop screen and can adjudicate with the arrow keys:

<img src="screenshots/alex_view.png" height="300"/>

## Features:
- WebSocket buzzer for use on mobile devices
- Complete access to all games on J-Archive
- Final Jeopardy, Daily Doubles, Double Jeopardy
 
## Download:
See <a href="https://github.com/stuartthomas25/JParty/releases">Releases</a> page.

## Requirements:
### For running binary
- macOS (for now)
- Two monitors
- A device with web access for each player

### For compiling from source code
- Python [>=3.8]
- PyQt6
- requests
- simpleaudio
- tornado
- BeautifulSoup4
- pyinstaller [>=5.0] (this is currently in development but is required for PyQt6)

To debug, run 

`
pip install -r requirements.txt;
cd jparty;
python ../cli.py
`

Too build from source, run

`
pyinstaller -y JParty.spec
`

Note that you may have to change the `target-arch` in the `spec` file.


