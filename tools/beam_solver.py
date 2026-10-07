"""Симулятор лучей (копия логики light/LightBeams.java) и решатель Зеркального лабиринта.

Карта — строки, x вправо (восток), z вниз (юг):
  '#' непрозрачная стена, '.' пол, '~' стена из вечного льда (луч проходит, игрок нет),
  '/' '\\' древнее зеркало (flipped=false / true), '*' призма, 'r' 'g' 'b' фильтры,
  'S' источник (светит внутрь зала от стены, на которой стоит), 'X' 'Y' 'Z' приёмники красный/зелёный/синий,
  'E' вход в лабиринт (проём во внешней стене).
Цель: одновременно красный луч в X, зелёный в Y, синий в Z.
"""
from collections import deque
from itertools import product

N, S, E, W = (0, -1), (0, 1), (1, 0), (-1, 0)
CW = {N: E, E: S, S: W, W: N}
CCW = {v: k for k, v in CW.items()}
MAX_LENGTH, MAX_SEGMENTS = 64, 24


def reflect(flipped, d):
    if d == N:
        return W if flipped else E
    if d == S:
        return E if flipped else W
    if d == E:
        return S if flipped else N
    return N if flipped else S


class Maze:
    def __init__(self, rows):
        self.rows = [list(r) for r in rows]
        self.w, self.h = len(rows[0]), len(rows)
        self.mirrors = [(x, z) for z in range(self.h) for x in range(self.w) if self.rows[z][x] in '/\\']
        self.source = next((x, z) for z in range(self.h) for x in range(self.w) if self.rows[z][x] == 'S')
        sx, sz = self.source
        self.source_dir = E if sx == 0 else W if sx == self.w - 1 else S if sz == 0 else N

    def at(self, x, z):
        if 0 <= x < self.w and 0 <= z < self.h:
            return self.rows[z][x]
        return '#'

    def trace(self, flips):
        """Куда попали лучи: {(x, z): set(цветов)} для приёмников. flips — dict зеркало -> flipped."""
        hits = {}
        queue = deque([(self.source, self.source_dir, 'w')])
        visited = set()
        segments, budget = 0, MAX_LENGTH
        while queue and segments < MAX_SEGMENTS and budget > 0:
            (x, z), d, col = queue.popleft()
            segments += 1
            while budget > 0:
                budget -= 1
                x, z = x + d[0], z + d[1]
                key = (x, z, d, col)
                if key in visited:
                    break
                visited.add(key)
                ch = self.at(x, z)
                if ch in '/\\':
                    queue.append(((x, z), reflect(flips[(x, z)], d), col))
                    break
                if ch == '*':
                    if col == 'w':
                        queue.append(((x, z), CCW[d], 'r'))
                        queue.append(((x, z), d, 'g'))
                        queue.append(((x, z), CW[d], 'b'))
                    else:
                        queue.append(((x, z), d, col))
                    break
                if ch in 'rgb':
                    if col in ('w', ch):
                        queue.append(((x, z), d, ch))
                    break
                if ch in 'XYZ':
                    hits.setdefault((x, z), set()).add(col)
                    break
                if ch in '#S':
                    break
        return hits

    def solved(self, flips):
        hits = self.trace(flips)
        want = {'X': 'r', 'Y': 'g', 'Z': 'b'}
        for z in range(self.h):
            for x in range(self.w):
                ch = self.rows[z][x]
                if ch in want and want[ch] not in hits.get((x, z), ()):
                    return False
        return True

    def initial(self):
        return {m: self.rows[m[1]][m[0]] == '\\' for m in self.mirrors}

    def solutions(self):
        out = []
        for bits in product((False, True), repeat=len(self.mirrors)):
            flips = dict(zip(self.mirrors, bits))
            if self.solved(flips):
                out.append(flips)
        return out

    def walkable(self):
        return {(x, z) for z in range(self.h) for x in range(self.w) if self.rows[z][x] in '.E'}

    def reachable(self):
        start = next((x, z) for z in range(self.h) for x in range(self.w) if self.rows[z][x] == 'E')
        floor = self.walkable()
        seen, q = {start}, deque([start])
        while q:
            x, z = q.popleft()
            for dx, dz in (N, S, E, W):
                n = (x + dx, z + dz)
                if n in floor and n not in seen:
                    seen.add(n)
                    q.append(n)
        return seen

    def check(self, min_flips=4):
        """Проверка для генератора: решение есть и единственно по существенным зеркалам, старт не решён,
        к каждому зеркалу, которое надо повернуть, можно подойти. Возвращает (решение, нужные повороты)."""
        sols = self.solutions()
        assert sols, 'лабиринт нерешаем'
        init = self.initial()
        assert not self.solved(init), 'лабиринт решён с самого начала'
        essential = [m for m in self.mirrors if len({s[m] for s in sols}) == 1]
        best = min(sols, key=lambda s: sum(s[m] != init[m] for m in self.mirrors))
        turns = [m for m in self.mirrors if best[m] != init[m]]
        assert all(m in essential for m in turns), 'решение неоднозначно'
        assert len(turns) >= min_flips, f'слишком мало поворотов: {len(turns)}'
        reach = self.reachable()
        for mx, mz in turns:
            assert any((mx + dx, mz + dz) in reach for dx, dz in (N, S, E, W)), f'к зеркалу {mx},{mz} не подойти'
        return best, turns
