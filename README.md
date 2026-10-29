# Maze Escape - Hard Edition

A Python maze game for my CIS 1051 project. The goal is to find the gold key and
then get to the green exit. Each time you start, the maze is different.

## Run it

You need Python 3.10 or newer with Tkinter. No extra pip packages are needed.

Download the repository ZIP, extract it, and double-click **Play Maze Escape.bat**
on Windows. You can also run this from the project folder:

```sh
python maze_escape.py
```

This is a desktop game. It does not run inside the GitHub website.

## Controls

- Arrow keys or WASD: move
- N: start a new maze
- P: pause/resume
- H: show the next three steps for two seconds
- Enter after winning: go to the next level
- Show trail: turn visited-cell dots on or off

Hints add 30 seconds. If you use a hint, the run cannot set a best time.
The timer starts when you first move or ask for a hint. It pauses when you switch
to another app. Best times save on your computer, not online.

## Five levels

| Level | Name | Maze size |
| --- | --- | --- |
| 1 | Hard | 25 x 17 |
| 2 | Brutal | 29 x 19 |
| 3 | Extreme | 33 x 21 |
| 4 | Nightmare | 37 x 23 |
| 5 | The Abyss | 41 x 25 |

All five are meant to be hard. The game looks for long routes when generating
a maze. The trail starts turned off, and each level has more passages to explore.
The exit is locked until you pick up the key. Walls cannot be crossed.

You can choose any level from the dropdown or play them in order. Winning level 5
finishes that maze; Enter creates another level-5 maze.

## Files

- `maze_escape.py`: window, drawing, controls, timer, hints, and saved times
- `maze_logic.py`: maze generation, paths, movement, key, and exit rules
- `Play Maze Escape.bat`: Windows launcher
- `README.md`: these instructions

The background is drawn with Tkinter colors and shapes. There is no background
image or downloaded artwork. The maze generator uses a stack to carve connected
passages; a queue is used to search for routes and choose key and exit locations.

Saved scores go in `%LOCALAPPDATA%\MazeEscapeHard\best_times.json` on Windows,
or a `MazeEscapeHard` folder in your home directory when LOCALAPPDATA is unavailable.
Each difficulty has its own best time. Layouts vary, so times are for casual play.

## Stars

Each completed maze earns 1, 2, or 3 stars. The move targets are shown below the
maze, and change with the random layout. The shortest route includes visiting
the key and then the exit; the player is not expected to know it in advance.

| Rating | Requirement |
| --- | --- |
| 3 stars | No hints, and no more than 120% of the shortest route's moves |
| 2 stars | No hints, and no more than 160% of the shortest route's moves, OR finish within 60 seconds without hints |
| 1 star | Finish the maze; a run using hints is capped at 1 star |

Move limits round up to whole moves. The highest matching rating wins, so an
efficient run still gets 3 stars even if it takes more than a minute. Time starts
on the first move and excludes pauses. Your best star rating per level is saved
in `best_stars.json` next to your saved times. The victory screen shows the stars.

## Credit and project status

Created for Rashad Basirat with OpenAI Codex assistance. This is a solo project.
The source and README should be reviewed and personalized before use as coursework.
The required demo video will be recorded later. Nothing has been submitted to Canvas.
