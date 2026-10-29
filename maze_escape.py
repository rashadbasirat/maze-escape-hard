"""Maze Escape: a desktop Python game using only the standard library."""

import json
import math
import os
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk

from maze_logic import Game, LEVELS

BG = '#0b1220'
PANEL = '#141f32'
TEXT = '#ecf3ff'
MUTED = '#94a7c1'
MINT = '#67e8c3'
GOLD = '#ffd166'
WALL = '#25364f'
FLOOR = '#101b2c'
SCORE_FILE = Path(os.getenv('LOCALAPPDATA') or Path.home()) / 'MazeEscapeHard' / 'best_times.json'
STAR_FILE = SCORE_FILE.with_name('best_stars.json')


def load_records(path=SCORE_FILE):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return {k: v for k, v in data.items() if k in ('1', '2', '3', '4', '5')
                and isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) and v >= 0}
    except (OSError, ValueError, AttributeError):
        return {}


def load_stars(path=STAR_FILE):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return {key: value for key, value in data.items()
                if key in ('1', '2', '3', '4', '5') and type(value) is int
                and 1 <= value <= 3}
    except (OSError, ValueError, AttributeError):
        return {}


class MazeEscape:
    def __init__(self, root):
        self.root = root
        root.title('Maze Escape - Hard Edition')
        root.geometry('1080x790')
        root.minsize(900, 700)
        root.configure(bg=BG)
        self.records = load_records()
        self.star_records = load_stars()
        self.game = None
        self.started = None
        self.elapsed = 0
        self.pause_started = None
        self.paused = False
        self.hint_route = []
        self.hints = 0
        self.hint_generation = 0
        self.level = tk.StringVar(value=LEVELS[0][0])
        self.trail = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value='Find the golden key. Unlock the gate. Make your escape.')
        self.clock = tk.StringVar(value='00:00')
        self.move_text = tk.StringVar(value='0')
        self.key_text = tk.StringVar(value='NOT FOUND')
        self.best_text = tk.StringVar(value='—')
        self.targets = tk.StringVar()
        self.build_ui()
        root.bind('<KeyPress>', self.on_key)
        root.bind('<FocusOut>', self.focus_out)
        self.new_game()
        self.tick()

    def label(self, parent, text='', **kwargs):
        options = {'bg': parent.cget('bg'), 'fg': TEXT, 'font': ('Segoe UI', 11)}
        options.update(kwargs)
        return tk.Label(parent, text=text, **options)

    def button(self, parent, text, command, accent=False):
        return tk.Button(parent, text=text, command=command, relief='flat', bd=0,
                         bg=MINT if accent else '#26364e', fg=BG if accent else TEXT,
                         activebackground='#93f3d8' if accent else '#344b6c',
                         activeforeground=BG if accent else TEXT, cursor='hand2',
                         font=('Segoe UI Semibold', 10), padx=17, pady=10,
                         highlightthickness=0)

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill='x', padx=32, pady=(24, 18))
        self.label(header, 'FIVE LEVELS. NO EASY WAY OUT.', fg=MINT).pack(anchor='w')
        title = self.label(header, 'Maze Escape')
        title.configure(font=('Segoe UI Semibold', 31))
        title.pack(anchor='w', pady=(2, 1))
        self.label(header, 'Find the key. Remember the turns. Reach the gate.', fg=MUTED).pack(anchor='w')
        toolbar = tk.Frame(self.root, bg=BG)
        toolbar.pack(fill='x', padx=32, pady=(0, 16))
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', padding=8, fieldbackground=PANEL,
                        background=PANEL, foreground=TEXT, arrowcolor=MINT)
        style.map('TCombobox', fieldbackground=[('readonly', PANEL)],
                  foreground=[('readonly', TEXT)],
                  selectbackground=[('readonly', PANEL)],
                  selectforeground=[('readonly', TEXT)])
        self.selector = ttk.Combobox(toolbar, textvariable=self.level, width=24,
                                    state='readonly', values=[level[0] for level in LEVELS])
        self.selector.pack(side='left', padx=(0, 12))
        self.selector.bind('<<ComboboxSelected>>', lambda _: self.new_game())
        self.button(toolbar, 'New maze  [N]', self.new_game, True).pack(side='left', padx=(0, 8))
        self.pause_button = self.button(toolbar, 'Pause  [P]', self.toggle_pause)
        self.pause_button.pack(side='left', padx=(0, 8))
        self.hint_button = self.button(toolbar, 'Hint  [H]', self.show_hint)
        self.hint_button.pack(side='left')
        tk.Checkbutton(toolbar, text='Show trail', variable=self.trail, command=self.draw,
                       bg=BG, fg=MUTED, selectcolor=PANEL, activebackground=BG,
                       activeforeground=TEXT, font=('Segoe UI', 10)).pack(side='right')
        stats = tk.Frame(self.root, bg=PANEL)
        stats.pack(fill='x', padx=32)
        for name, variable in [('TIME', self.clock), ('MOVES', self.move_text),
                               ('KEY', self.key_text), ('LEVEL BEST · NO HINTS', self.best_text)]:
            section = tk.Frame(stats, bg=PANEL)
            section.pack(side='left', expand=True, fill='x', padx=20, pady=13)
            self.label(section, name, fg=MUTED).pack(anchor='w')
            item = self.label(section, textvariable=variable, fg=MINT if name == 'KEY' else TEXT)
            item.configure(font=('Segoe UI Semibold', 17))
            item.pack(anchor='w', pady=(3, 0))
        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0, takefocus=True)
        self.canvas.pack(fill='both', expand=True, padx=32, pady=(16, 8))
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.canvas.bind('<Button-1>', lambda _: self.canvas.focus_set())
        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill='x', padx=32, pady=(0, 20))
        self.label(bottom, textvariable=self.status, fg=GOLD, wraplength=980,
                   justify='left').pack(anchor='w')
        self.label(bottom, textvariable=self.targets, fg=MUTED).pack(anchor='w', pady=(5, 0))
        self.label(bottom, 'ARROWS / WASD  Move     •     H  Hint (+30s)     •     P  Pause     •     N  New maze',
                   fg=MUTED).pack(anchor='w', pady=(9, 0))
        self.label(bottom, 'YOU  ●     KEY  ◆     EXIT  ▣     Time starts on your first move.',
                   fg=MUTED).pack(anchor='w', pady=(4, 0))

    def new_game(self):
        self.game = Game(int(self.level.get()[0]))
        self.started = None
        self.elapsed = 0
        self.paused = False
        self.pause_started = None
        self.hint_route = []
        self.hints = 0
        self.hint_generation += 1
        self.pause_button.configure(text='Pause  [P]')
        self.status.set('Find the golden key, then reach the green gate. Click the maze to focus.')
        self.update_stats()
        self.draw()
        self.canvas.focus_set()

    def current_time(self):
        if self.started is None:
            return 0
        now = self.pause_started if self.paused else time.monotonic()
        return self.elapsed if self.game.won else now - self.started + self.hints * 30

    @staticmethod
    def format_time(seconds):
        seconds = int(seconds)
        return f'{seconds // 60:02}:{seconds % 60:02}'

    def update_stats(self):
        self.clock.set(self.format_time(self.current_time()))
        self.move_text.set(str(self.game.moves))
        self.key_text.set('COLLECTED' if self.game.has_key else 'NOT FOUND')
        best = self.records.get(str(self.game.level))
        stars = self.star_records.get(str(self.game.level), 0)
        self.best_text.set((self.format_time(best) if best is not None else '—')
                           + f'   {stars}/3 ★')
        three = math.ceil(self.game.par_moves * 1.2)
        two = math.ceil(self.game.par_moves * 1.6)
        self.targets.set(f'3★: at most {three} moves  |  2★: at most {two} moves OR 60 seconds  |  Hints: 1★ maximum')

    def tick(self):
        self.update_stats()
        self.root.after(100, self.tick)

    def focus_out(self, _):
        # Pause only when the whole app loses focus, not when clicking its controls.
        self.root.after_idle(self.pause_if_unfocused)

    def pause_if_unfocused(self):
        if self.root.focus_displayof() is None and self.started and not self.paused and not self.game.won:
            self.toggle_pause()

    def toggle_pause(self):
        if self.game.won:
            return
        if self.paused:
            if self.started is not None:
                self.started += time.monotonic() - self.pause_started
            self.paused = False
            self.pause_started = None
            self.pause_button.configure(text='Pause  [P]')
        else:
            self.pause_started = time.monotonic()
            self.paused = True
            self.pause_button.configure(text='Resume  [P]')
        self.draw()
        self.canvas.focus_set()

    def on_key(self, event):
        key = event.keysym.lower()
        if key == 'n':
            self.new_game()
        elif key in ('p', 'escape'):
            self.toggle_pause()
        elif key == 'h':
            self.show_hint()
        elif key in ('return', 'space') and self.game.won:
            self.advance()
        elif key in ('up', 'w', 'down', 's', 'left', 'a', 'right', 'd'):
            direction = {'up': (0, -1), 'w': (0, -1), 'down': (0, 1), 's': (0, 1),
                         'left': (-1, 0), 'a': (-1, 0), 'right': (1, 0), 'd': (1, 0)}[key]
            self.move(*direction)
            return 'break'

    def move(self, dx, dy):
        if self.paused or self.game.won:
            return
        result = self.game.move(dx, dy)
        if result == 'wall':
            return
        if result == 'locked':
            self.status.set('The gate is locked. Find the golden key first.')
        else:
            if self.started is None:
                self.started = time.monotonic()
            self.hint_route = []
            if result == 'key':
                self.status.set('Key collected! The green gate is now unlocked.')
            elif result == 'win':
                # Freeze elapsed time before rendering the victory panel.
                self.elapsed = time.monotonic() - self.started + self.hints * 30
                if not self.hints:
                    previous = self.records.get(str(self.game.level), float('inf'))
                    if self.elapsed < previous:
                        self.records[str(self.game.level)] = self.elapsed
                        try:
                            SCORE_FILE.parent.mkdir(parents=True, exist_ok=True)
                            SCORE_FILE.write_text(json.dumps(self.records, indent=2), encoding='utf-8')
                            self.status.set('New personal best! Your time has been saved.')
                        except OSError:
                            self.status.set('You escaped! Best time could not be saved on this computer.')
                else:
                    self.status.set('You escaped! Finish without hints to set a level best.')
                rating = self.game.stars(self.elapsed, self.hints)
                level = str(self.game.level)
                if rating > self.star_records.get(level, 0):
                    self.star_records[level] = rating
                    try:
                        STAR_FILE.parent.mkdir(parents=True, exist_ok=True)
                        STAR_FILE.write_text(json.dumps(self.star_records, indent=2), encoding='utf-8')
                    except OSError:
                        self.status.set('You escaped! Your star rating could not be saved on this computer.')
        self.update_stats()
        self.draw()

    def show_hint(self):
        if self.paused or self.game.won:
            return
        if self.started is None:
            self.started = time.monotonic()
        self.hints += 1
        goal = self.game.maze.exit if self.game.has_key else self.game.maze.key
        self.hint_route = self.game.maze.path(self.game.position, goal)[:4]
        self.hint_generation += 1
        generation = self.hint_generation
        self.status.set('Next 3 steps shown for 2 seconds. +30 seconds; assisted runs do not set best times.')
        self.draw()
        self.root.after(2000, lambda: self.clear_hint(generation))
        self.canvas.focus_set()

    def clear_hint(self, generation):
        if generation == self.hint_generation:
            self.hint_route = []
            self.draw()

    def advance(self):
        if self.game.level < 5:
            self.level.set(LEVELS[self.game.level][0])
        self.new_game()

    def draw(self):
        if not self.game:
            return
        c = self.canvas
        c.delete('all')
        maze = self.game.maze
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 10 or ch < 10:
            return
        size = max(5, min((cw - 12) / maze.width, (ch - 12) / maze.height))
        ox = (cw - size * maze.width) / 2
        oy = (ch - size * maze.height) / 2
        for y in range(maze.height):
            for x in range(maze.width):
                left, top = ox + x * size, oy + y * size
                color = FLOOR if (x, y) in maze.floor else WALL
                c.create_rectangle(left, top, left + size + 1, top + size + 1, fill=color, outline='')
        def center(position):
            return ox + (position[0] + .5) * size, oy + (position[1] + .5) * size
        if self.trail.get():
            for position in self.game.visited - {self.game.position}:
                x, y = center(position)
                r = max(1.5, size * .065)
                c.create_oval(x - r, y - r, x + r, y + r, fill='#416980', outline='')
        for position in self.hint_route:
            x, y = center(position)
            r = size * .12
            c.create_oval(x - r, y - r, x + r, y + r, fill=GOLD, outline='')
        x, y = center(maze.exit)
        r = size * .35
        c.create_rectangle(x-r, y-r, x+r, y+r, fill='#194d43', outline=MINT, width=2)
        if not self.game.has_key:
            for shift in (-.12, .12):
                c.create_line(x + size*shift, y-r, x + size*shift, y+r, fill=MINT, width=2)
            x, y = center(maze.key)
            r = size * .27
            c.create_polygon(x, y-r, x+r, y, x, y+r, x-r, y, fill=GOLD, outline='')
        x, y = center(self.game.position)
        r = size * .28
        c.create_oval(x-r-3, y-r-3, x+r+3, y+r+3, fill='#23566a', outline='')
        c.create_oval(x-r, y-r, x+r, y+r, fill=MINT, outline='')
        if self.paused or self.game.won:
            c.create_rectangle(ox, oy, ox+maze.width*size, oy+maze.height*size,
                               fill=BG, stipple='gray75', outline='')
            box_width = min(470, cw - 40)
            c.create_rectangle(cw/2-box_width/2, ch/2-115, cw/2+box_width/2, ch/2+115,
                               fill=PANEL, outline=MINT, width=1)
            title = ('LEVEL FIVE COMPLETE' if self.game.won and self.game.level == 5
                     else 'YOU ESCAPED' if self.game.won else 'TAKE A BREATHER')
            c.create_text(cw/2, ch/2-72, text=title, fill=MINT, font=('Segoe UI Semibold', 23))
            if self.game.won:
                rating = self.game.stars(self.elapsed, self.hints)
                for index in range(3):
                    c.create_text(cw/2 + (index-1)*52, ch/2-25, text='★',
                                  fill=GOLD if index < rating else '#42516a',
                                  font=('Segoe UI', 31))
            detail = (f'{self.format_time(self.elapsed)}  /  {self.game.moves} moves  /  {self.hints} hints'
                      if self.game.won else 'Your clock is paused.')
            c.create_text(cw/2, ch/2+24 if self.game.won else ch/2, text=detail, fill=TEXT, font=('Segoe UI', 13))
            action = ('Press ENTER for the next maze' if self.game.level < 5 else 'Press ENTER to replay level 5') if self.game.won else 'Press P or click Resume to continue'
            c.create_text(cw/2, ch/2+74, text=action, fill=MUTED, font=('Segoe UI', 11))


if __name__ == '__main__':
    window = tk.Tk()
    MazeEscape(window)
    window.mainloop()
