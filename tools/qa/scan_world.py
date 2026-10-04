#!/usr/bin/env python3
"""Сканер сгенерированного мира: ищет неестественную генерацию прямо в region-файлах сейва.

Запуск: python3 tools/qa/scan_world.py [путь_к_сейву] [--dim celestial/heaven ...]
По умолчанию: run/saves/test, все измерения мода + overworld.
Проверки (код — в отчёте):
  RAINBOW_EMBEDDED   радужная арка касается чужих блоков (врезана в остров/дерево/облако/постройку)
  RAINBOW_TRUNCATED  арка обрезана: компонент стекла заметно меньше полной арки
  RAINBOW_FLOATING   арка ни одной ногой не стоит на земле (висит в небе)
  PLANT_FLOATING     растение/цветок/саженец без опоры снизу
  VOID_FLUID         текущая вода/лава у дна мира (водопад в пустоту)
  STRUCTURE_OVERLAP  bbox двух разных построек пересекаются
  FEATURE_CHUNK_CUT  столб фичи обрывается ровно по границе чанка
  ICE_CHUNK_GRID     Чертоги: подземный объём чанка — синий лёд, у соседа камень (шов по сетке чанков)
"""
import io
import math
import os
import struct
import sys
import zlib
from collections import defaultdict, deque

import nbtlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAINBOW = {'minecraft:red_stained_glass', 'minecraft:orange_stained_glass', 'minecraft:yellow_stained_glass',
           'minecraft:lime_stained_glass', 'minecraft:light_blue_stained_glass', 'minecraft:purple_stained_glass'}
AIRS = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
PLANTS = {'celestial:sky_lily', 'celestial:sunbell', 'celestial:cloudbloom', 'celestial:starflower', 'celestial:aether_rose',
          'celestial:dawn_poppy', 'celestial:golden_tuft', 'celestial:tall_golden_grass', 'celestial:skywood_sapling',
          'celestial:cloud_willow_sapling', 'celestial:starpine_sapling', 'celestial:manna_bush', 'celestial:glowshroom',
          'minecraft:short_grass', 'minecraft:fern', 'minecraft:dandelion', 'minecraft:poppy', 'minecraft:sweet_berry_bush'}
FLUIDS = {'minecraft:water', 'minecraft:lava'}


def read_region(path):
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) < 8192:
        return
    for i in range(1024):
        off = struct.unpack('>I', b'\0' + data[i * 4:i * 4 + 3])[0]
        if not off:
            continue
        start = off * 4096
        length = struct.unpack('>I', data[start:start + 4])[0]
        ctype = data[start + 4]
        raw = data[start + 5:start + 4 + length]
        if ctype == 2:
            raw = zlib.decompress(raw)
        elif ctype == 1:
            import gzip
            raw = gzip.decompress(raw)
        else:
            continue
        try:
            yield nbtlib.File.parse(io.BytesIO(raw))
        except Exception:  # noqa: BLE001
            continue


def parse_state(p):
    """Элемент палитры: в 26.x — строка 'ns:name[k=v,...]', раньше — compound {Name, Properties}."""
    if isinstance(p, str):
        if '[' in p:
            name, rest = p.split('[', 1)
            props = dict(kv.split('=', 1) for kv in rest.rstrip(']').split(',') if '=' in kv)
            return name, props
        return str(p), {}
    # 26.x: {id, properties} | {'': id}; старые версии: {Name, Properties}
    name = p.get('id') or p.get('Name') or p.get('')
    props = p.get('properties') or p.get('Properties') or {}
    return str(name), {str(k): str(v) for k, v in props.items()}


def unpack(states, bits, count=4096):
    out = []
    per_long = 64 // bits
    mask = (1 << bits) - 1
    for long in states:
        v = int(long) & 0xFFFFFFFFFFFFFFFF
        for _ in range(per_long):
            out.append(v & mask)
            v >>= bits
            if len(out) == count:
                return out
    return out


import numpy as np

NAMES = ['minecraft:air']      # глобальная таблица id → имя
IDS = {'minecraft:air': 0}


def gid(name):
    if name not in IDS:
        IDS[name] = len(NAMES)
        NAMES.append(name)
    return IDS[name]


def ids_of(names):
    return np.array([gid(n) for n in names], dtype=np.uint16)


class World:
    """Готовые чанки как numpy-массивы [y, z, x] глобальных id (сплошные миры не раздувают память)."""

    def __init__(self):
        self.chunks = {}
        self.starts = []  # (structure_id, (minx,miny,minz,maxx,maxy,maxz), chunk)
        self.min_y = None
        self.height = None
        self.air = ids_of(AIRS)

    def load_dim(self, region_dir):
        for name in os.listdir(region_dir):
            if name.endswith('.mca'):
                for chunk in read_region(os.path.join(region_dir, name)):
                    self.add_chunk(chunk)

    def add_chunk(self, c):
        if not str(c.get('Status', '')).endswith('full'):
            return
        cx, cz = int(c['xPos']), int(c['zPos'])
        secs = [s for s in c.get('sections', []) if s.get('block_states')]
        if not secs:
            return
        ys = [int(s['Y']) for s in c.get('sections', [])]
        lo, hi = min(ys), max(ys)
        if self.min_y is None:
            self.min_y, self.height = lo * 16, (hi - lo + 1) * 16
        arr = np.zeros((self.height, 16, 16), dtype=np.uint16)
        for sec in secs:
            bs = sec['block_states']
            pal = ids_of([parse_state(p)[0] for p in bs['palette']])
            sy = int(sec['Y']) * 16 - self.min_y
            if not 0 <= sy < self.height:
                continue
            if len(pal) == 1:
                arr[sy:sy + 16] = pal[0]
            else:
                bits = max(4, math.ceil(math.log2(len(pal))))
                idx = np.array(unpack(bs['data'], bits), dtype=np.int64)
                arr[sy:sy + 16] = pal[idx].reshape(16, 16, 16)
        self.chunks[(cx, cz)] = arr
        for sid, start in (c.get('structures', {}).get('starts', {}) or {}).items():
            if str(start.get('id', 'INVALID')) == 'INVALID':
                continue
            for piece in start.get('Children', []):
                bb = [int(v) for v in piece.get('BB', [])]
                if len(bb) == 6:
                    self.starts.append((str(sid), tuple(bb), (cx, cz)))

    def loaded(self, x, z):
        return (x >> 4, z >> 4) in self.chunks

    def get(self, x, y, z):
        a = self.chunks.get((x >> 4, z >> 4))
        if a is None or self.min_y is None or not 0 <= y - self.min_y < self.height:
            return 'minecraft:air'
        return NAMES[a[y - self.min_y, z & 15, x & 15]]

    def find(self, names):
        """Все позиции блоков из набора имён: список (x, y, z)."""
        want = ids_of(names)
        out = []
        for (cx, cz), a in self.chunks.items():
            m = np.isin(a, want)
            if m.any():
                for y, z, x in zip(*np.nonzero(m)):
                    out.append((cx * 16 + int(x), int(y) + self.min_y, cz * 16 + int(z)))
        return out


def neighbors6(p):
    x, y, z = p
    return ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1))


def check_rainbows(w, dim, out):
    glass = set(w.find(RAINBOW))
    seen = set()
    for p in glass:
        if p in seen:
            continue
        comp = []
        q = deque([p])
        seen.add(p)
        while q:
            c = q.popleft()
            comp.append(c)
            x, y, z = c
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        n = (x + dx, y + dy, z + dz)
                        if n in glass and n not in seen:
                            seen.add(n)
                            q.append(n)
        xs = [c[0] for c in comp]
        ys = [c[1] for c in comp]
        zs = [c[2] for c in comp]
        # граница несгенерированных чанков — не судим
        if any(not w.loaded(x, z) for x in (min(xs) - 1, max(xs) + 1) for z in (min(zs) - 1, max(zs) + 1)):
            continue
        foreign = defaultdict(int)
        for c in comp:
            for n in neighbors6(c):
                b = w.get(*n)
                if b not in AIRS and b not in RAINBOW:
                    foreign[b] += 1
        where = f'{dim} {min(xs)},{min(ys)},{min(zs)}..{max(xs)},{max(ys)},{max(zs)}'
        if foreign:
            top = ', '.join(f'{k.split(":")[1]}×{v}' for k, v in sorted(foreign.items(), key=lambda kv: -kv[1])[:5])
            out['RAINBOW_EMBEDDED'].append(f'{where}: {len(comp)} стекла, касается: {top}')
        # полная арка радиуса 7..8, ширина 3 ≈ 400+ блоков стекла
        if len(comp) < 250:
            out['RAINBOW_TRUNCATED'].append(f'{where}: всего {len(comp)} стекла (полная 276–330)')
        base_y = min(ys)
        feet = [c for c in comp if c[1] == base_y]
        if all(w.get(c[0], c[1] - 1, c[2]) in AIRS for c in feet):
            out['RAINBOW_FLOATING'].append(f'{where}: опоры нет, под арками пусто')


def check_plants(w, dim, out):
    for (x, y, z) in w.find(PLANTS):
        n = w.get(x, y, z)
        if True:
            below = w.get(x, y - 1, z)
            if below in AIRS or below in FLUIDS:
                out['PLANT_FLOATING'].append(f'{dim} {x},{y},{z}: {n.split(":")[1]} над {below.split(":")[1]}')


def check_void_fluids(w, dim, out):
    per_chunk = defaultdict(int)
    fl = ids_of(FLUIDS)
    for (cx, cz), a in w.chunks.items():
        low = a[:9]
        for f in fl:
            cnt = int((low == f).sum())
            if cnt:
                per_chunk[(cx, cz, NAMES[f])] += cnt
    for (cx, cz, n), cnt in per_chunk.items():
        out['VOID_FLUID'].append(f'{dim} чанк {cx},{cz} (блок ~{cx * 16},{cz * 16}): {cnt}× {n.split(":")[1]} у дна мира — поток в пустоту')


def check_structures(w, dim, out):
    # объединяем куски одной постройки (одинаковый id + чанк старта)
    groups = defaultdict(list)
    for sid, bb, chunk in w.starts:
        groups[(sid, chunk)].append(bb)
    items = list(groups.items())
    for i in range(len(items)):
        (sa, ca), ba = items[i]
        for j in range(i + 1, len(items)):
            (sb, cb), bbs = items[j]
            if ca == cb and sa == sb:
                continue
            for a in ba:
                hit = next((b for b in bbs if a[0] <= b[3] and b[0] <= a[3] and a[1] <= b[4] and b[1] <= a[4] and a[2] <= b[5] and b[2] <= a[5]), None)
                if hit:
                    out['STRUCTURE_OVERLAP'].append(f'{dim}: {sa} (старт {ca}) пересекается с {sb} (старт {cb}) в {a[:3]}')
                    break
            else:
                continue
            break


def check_ice_grid(w, dim, out):
    """Подземный объём чанка залит синим льдом, а у соседа — камень: сетка 16×16 видна сквозь лёд моря."""
    bi = gid('minecraft:blue_ice')
    frac = {k: float((a[5:55] == bi).mean()) for k, a in w.chunks.items()}
    for (cx, cz), f in frac.items():
        if f < 0.3:
            continue
        for d in ((1, 0), (0, 1)):
            n = frac.get((cx + d[0], cz + d[1]))
            if n is not None and n < 0.05:
                out['ICE_CHUNK_GRID'].append(f'{dim} чанк {cx},{cz} (~{cx * 16},{cz * 16}): {f:.0%} синего льда под землёй, сосед {n:.0%}')
                break


def check_chunk_cuts(w, dim, out):
    """Блоки-фичи мода, у которых соседний столб за границей чанка пуст, а внутри чанка — полон."""
    feature = {'celestial:sky_crystal', 'celestial:sky_crystal_block', 'celestial:radiant_stone', 'celestial:aurora_crystal',
               'celestial:shadow_crystal', 'celestial:glowshroom_cap', 'celestial:glowshroom_stem', 'minecraft:blue_ice', 'minecraft:packed_ice'}
    cols = defaultdict(int)
    for f in ids_of(feature):
        for (cx, cz), a in w.chunks.items():
            counts = (a == f).sum(axis=0)
            for z, x in zip(*np.nonzero(counts)):
                cols[(cx * 16 + int(x), cz * 16 + int(z), NAMES[f])] = int(counts[z, x])
    flagged = set()
    for (x, z, n), cnt in cols.items():
        if cnt < 4:
            continue
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if (nx >> 4, nz >> 4) == (x >> 4, z >> 4) or not w.loaded(nx, nz):
                continue
            inner = cols.get((x - dx, z - dz, n), 0)
            if cols.get((nx, nz, n), 0) == 0 and inner >= cnt * 0.8:
                key = (x >> 4, z >> 4, n)
                if key not in flagged:
                    flagged.add(key)
                    out['FEATURE_CHUNK_CUT'].append(f'{dim} {x},{z}: {n.split(":")[1]} столб {cnt} обрывается на границе чанка')


def main():
    args = sys.argv[1:]
    save = args[0] if args and not args[0].startswith('--') else os.path.join(ROOT, 'run/saves/test')
    dims = [a for i, a in enumerate(args) if i and args[i - 1] == '--dim'] or \
        ['celestial/heaven', 'celestial/abyss', 'celestial/frozen_halls', 'overworld']
    out = defaultdict(list)
    for dim in dims:
        region = os.path.join(save, 'region') if dim == 'overworld' else os.path.join(save, 'dimensions', dim, 'region')
        if not os.path.isdir(region):
            continue
        w = World()
        w.load_dim(region)
        print(f'{dim}: {len(w.chunks)} готовых чанков, {len(w.starts)} кусков построек', file=sys.stderr)
        if dim == 'celestial/heaven':
            check_rainbows(w, dim, out)
        check_plants(w, dim, out)
        if dim == 'celestial/heaven':  # под Небом пустота; в сплошных мирах вода у дна — водоносные слои
            check_void_fluids(w, dim, out)
        if dim == 'celestial/frozen_halls':
            check_ice_grid(w, dim, out)
        check_structures(w, dim, out)
        check_chunk_cuts(w, dim, out)
    total = 0
    for code in sorted(out):
        print(f'\n== {code} ({len(out[code])})')
        for m in out[code][:40]:
            print('  ' + m)
        if len(out[code]) > 40:
            print(f'  ... и ещё {len(out[code]) - 40}')
        total += len(out[code])
    print(f'\nИтого находок: {total}')


if __name__ == '__main__':
    main()
