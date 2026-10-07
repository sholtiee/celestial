"""Решатель залов скользящего льда (та же логика, что в GlacierHallBlockEntity).

Карта — строки символов:
  '#' стена (вне зала), '.' ледяная плита, 'o' гнездо, 'G' глыба на плите, 'Q' глыба на гнезде,
  'P' ледяная колонна (стоит на плите, останавливает глыбы), 'E' вход (игрок стоит здесь, глыбы сюда не едут).
Ход: игрок стоит вплотную с противоположной стороны глыбы (клетка достижима пешком, не занята) и толкает её —
глыба едет до колонны, другой глыбы или края пола. Цель: на каждом гнезде стоит глыба.
"""
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIR_NAMES = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}


class Hall:
    def __init__(self, rows):
        self.rows = rows
        self.floor, self.nests, self.pillars, self.glaciers = set(), set(), set(), set()
        self.entrance = None
        for z, row in enumerate(rows):
            for x, ch in enumerate(row):
                p = (x, z)
                if ch in '.oGQP':
                    self.floor.add(p)
                if ch in 'oQ':
                    self.nests.add(p)
                if ch in 'GQ':
                    self.glaciers.add(p)
                if ch == 'P':
                    self.pillars.add(p)
                if ch == 'E':
                    self.entrance = p
        self.walk = self.floor | {self.entrance}

    def reachable(self, start, glaciers):
        seen = {start}
        q = deque([start])
        while q:
            x, z = q.popleft()
            for dx, dz in DIRS:
                n = (x + dx, z + dz)
                if n in self.walk and n not in seen and n not in glaciers and n not in self.pillars:
                    seen.add(n)
                    q.append(n)
        return seen

    def slide(self, g, d, glaciers):
        x, z = g
        while True:
            n = (x + d[0], z + d[1])
            if n not in self.floor or n in self.pillars or n in glaciers:
                return (x, z)
            x, z = n

    def solve(self, limit=400000):
        """Кратчайшее решение (BFS). Возвращает список ходов [(глыба, направление, клетка игрока)] или None."""
        start = (frozenset(self.glaciers), self.entrance)
        key = lambda gl, pl: (gl, min(self.reachable(pl, gl)))  # noqa: E731
        seen = {key(*start): None}
        q = deque([start])
        parent = {}
        while q and len(seen) < limit:
            gl, pl = q.popleft()
            if self.nests <= gl:
                moves = []
                k = key(gl, pl)
                while parent.get(k):
                    prev, move = parent[k]
                    moves.append(move)
                    k = key(*prev)
                return moves[::-1]
            reach = self.reachable(pl, gl)
            for g in gl:
                for d in DIRS:
                    stand = (g[0] - d[0], g[1] - d[1])
                    if stand not in reach:
                        continue
                    dest = self.slide(g, d, gl)
                    if dest == g:
                        continue
                    ngl = frozenset((gl - {g}) | {dest})
                    nk = key(ngl, stand)
                    if nk in seen:
                        continue
                    seen[nk] = True
                    parent[nk] = ((gl, pl), (g, d, stand))
                    q.append((ngl, stand))
        return None
