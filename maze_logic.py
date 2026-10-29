"""Maze generation and game rules, independent of the graphical interface."""

from collections import deque
from itertools import permutations
import math
import random

LEVELS = [
    ('1 - Hard', 25, 17, 100),
    ('2 - Brutal', 29, 19, 150),
    ('3 - Extreme', 33, 21, 200),
    ('4 - Nightmare', 37, 23, 250),
    ('5 - The Abyss', 61, 35, 650),
]


class Maze:
    def __init__(self, width=21, height=15, seed=None):
        if width < 7 or height < 7 or width % 2 == 0 or height % 2 == 0:
            raise ValueError("Maze dimensions must be odd and at least 7.")
        self.width, self.height = width, height
        self.start = (1, 1)
        self.floor = {self.start}
        rng = random.Random(seed)
        stack = [self.start]
        # Depth-first search carves passages through a grid of solid walls.
        while stack:
            x, y = stack[-1]
            options = [(x + dx, y + dy) for dx, dy in
                       ((2, 0), (-2, 0), (0, 2), (0, -2))
                       if 0 < x + dx < width - 1 and 0 < y + dy < height - 1
                       and (x + dx, y + dy) not in self.floor]
            if options:
                nx, ny = rng.choice(options)
                self.floor.update({((x + nx) // 2, (y + ny) // 2), (nx, ny)})
                stack.append((nx, ny))
            else:
                stack.pop()
        distances = self.distances(self.start)
        self.exit = max(distances, key=distances.get)
        # Put the key far from the entrance while keeping it separate from the exit.
        candidates = [p for p in self.floor if p not in (self.start, self.exit)]
        exit_distances = self.distances(self.exit)
        self.key = max(candidates, key=lambda p: (
            distances[p] + exit_distances[p],
            min(distances[p], exit_distances[p])))

    def neighbors(self, position):
        x, y = position
        return [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if (x + dx, y + dy) in self.floor]

    def distances(self, start):
        result = {start: 0}
        queue = deque([start])
        while queue:
            position = queue.popleft()
            for neighbor in self.neighbors(position):
                if neighbor not in result:
                    result[neighbor] = result[position] + 1
                    queue.append(neighbor)
        return result

    def path(self, start, goal):
        parents = {start: None}
        queue = deque([start])
        while queue:
            position = queue.popleft()
            if position == goal:
                route = []
                while position is not None:
                    route.append(position)
                    position = parents[position]
                return route[::-1]
            for neighbor in self.neighbors(position):
                if neighbor not in parents:
                    parents[neighbor] = position
                    queue.append(neighbor)
        return []


class Game:
    def __init__(self, level=1, seed=None):
        if level not in range(1, 6):
            raise ValueError('Choose a level from 1 to 5.')
        self.level = level
        name, width, height, minimum_steps = LEVELS[level - 1]
        rng = random.Random(seed)
        # Try several layouts so even the first level has a long route.
        best_maze = None
        best_length = -1
        for attempt in range(40):
            maze = Maze(width, height, rng.getrandbits(64))
            length = (len(maze.path(maze.start, maze.key))
                      + len(maze.path(maze.key, maze.exit)) - 2)
            if length > best_length:
                best_maze, best_length = maze, length
            if length >= minimum_steps:
                break
        self.maze = best_maze
        self.par_moves = best_length
        self.keys = {self.maze.key}
        self.collected_keys = set()
        self.decoys = set()
        self.revealed_decoys = set()
        if level == 5:
            # Spread the keys across dead ends, forcing exploration and backtracking.
            ends = {p for p in self.maze.floor if len(self.maze.neighbors(p)) == 1
                    and p not in (self.maze.start, self.maze.exit)}
            distances = [self.maze.distances(p) for p in
                         (self.maze.start, self.maze.exit, self.maze.key)]
            while len(self.keys) < 3:
                choices = ends - self.keys
                key = max(choices, key=lambda p: min(d[p] for d in distances))
                self.keys.add(key)
                distances.append(self.maze.distances(key))
            choices = sorted(ends - self.keys)
            self.decoys = set(rng.sample(choices, min(6, len(choices))))
            # Only three keys: checking all six orders gives the exact move target.
            routes = {p: self.maze.distances(p) for p in self.keys | {self.maze.start}}
            self.par_moves = min(
                routes[self.maze.start][order[0]]
                + sum(routes[a][b] for a, b in zip(order, order[1:]))
                + routes[order[-1]][self.maze.exit]
                for order in permutations(self.keys))
        self.position = self.maze.start
        self.has_key = False
        self.won = False
        self.moves = 0
        self.visited = {self.position}

    def stars(self, seconds, hints=0):
        """Rate a finished run against this maze's shortest key-and-exit route."""
        if not self.won:
            return 0
        if hints:
            return 1
        if self.moves <= math.ceil(self.par_moves * 1.2):
            return 3
        if self.moves <= math.ceil(self.par_moves * 1.6) or seconds <= 60:
            return 2
        return 1

    def move(self, dx, dy):
        """Return 'wall', 'locked', 'key', 'decoy', 'win', or 'move'."""
        if self.won or (dx, dy) not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            return 'wall'
        target = self.position[0] + dx, self.position[1] + dy
        if target not in self.maze.floor:
            return 'wall'
        if target == self.maze.exit and not self.has_key:
            return 'locked'
        self.position = target
        self.moves += 1
        self.visited.add(target)
        if target in self.keys and target not in self.collected_keys:
            self.collected_keys.add(target)
            self.has_key = self.collected_keys == self.keys
            return 'key'
        if target == self.maze.exit:
            self.won = True
            return 'win'
        if target in self.decoys and target not in self.revealed_decoys:
            self.revealed_decoys.add(target)
            return 'decoy'
        return 'move'

    def visible_tiles(self):
        """Level 5's torch lights four passage steps and their bordering walls."""
        if self.level != 5:
            return None
        distances = {self.position: 0}
        queue = deque([self.position])
        while queue:
            current = queue.popleft()
            if distances[current] == 4:
                continue
            for neighbor in self.maze.neighbors(current):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        visible = set(distances)
        for x, y in distances:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = x + dx, y + dy
                if p not in self.maze.floor:
                    visible.add(p)
        return visible
