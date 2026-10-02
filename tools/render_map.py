#!/usr/bin/env python3
"""Рисует карту измерения из region-файлов без запуска игры.

python3 tools/render_map.py [измерение] [выход.png]
  измерение: путь от run/world/dimensions, по умолчанию celestial/heaven
Сверху — вид сверху (цвет верхнего блока + тень по высоте), снизу — вертикальный срез по z=0.
"""
import io
import math
import os
import struct
import sys
import zlib

import nbtlib
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), '..')

COLORS = {
    'celestial:golden_grass': (236, 196, 70), 'celestial:heaven_dirt': (190, 165, 120),
    'celestial:skystone': (196, 205, 220), 'celestial:skystone_bricks': (170, 180, 196),
    'celestial:cloud': (250, 252, 255), 'celestial:golden_cloud': (255, 226, 130), 'celestial:rain_cloud': (150, 160, 175),
    'celestial:skywood_log': (220, 214, 200), 'celestial:skywood_leaves': (245, 200, 60),
    'celestial:etherite_ore': (60, 200, 220), 'celestial:starquartz_ore': (255, 245, 200),
    'celestial:radiant_stone': (255, 210, 90), 'celestial:sky_crystal': (120, 180, 255),
    'celestial:manna_bush': (150, 190, 80), 'minecraft:water': (60, 120, 230),
}


def block_color(name):
    if name in COLORS:
        return COLORS[name]
    h = hash(name) & 0xffffff
    return (h >> 16 & 255, h >> 8 & 255, h & 255)


def read_chunks(path):
    with open(path, 'rb') as f:
        data = f.read()
    for i in range(1024):
        off = int.from_bytes(data[i * 4:i * 4 + 3], 'big')
        if off == 0:
            continue
        start = off * 4096
        length = struct.unpack('>I', data[start:start + 4])[0]
        comp = data[start + 4]
        raw = data[start + 5:start + 4 + length]
        if comp == 2:
            raw = zlib.decompress(raw)
        else:
            continue
        yield nbtlib.File.parse(io.BytesIO(raw))


def palette_name(p):
    if hasattr(p, 'keys'):
        return str(p.get('id', p.get('Name', p.get('', '?'))))
    return str(p).split('[')[0]


def section_blocks(section):
    bs = section.get('block_states')
    if not bs:
        return None
    palette = [palette_name(p) for p in bs['palette']]
    if len(palette) == 1:
        return [palette[0]] * 4096
    bits = max(4, math.ceil(math.log2(len(palette))))
    per_long = 64 // bits
    mask = (1 << bits) - 1
    out = []
    for long in bs['data']:
        v = int(long) & 0xFFFFFFFFFFFFFFFF
        for _ in range(per_long):
            out.append(palette[v & mask])
            v >>= bits
            if len(out) == 4096:
                return out
    return out


def main():
    dim = sys.argv[1] if len(sys.argv) > 1 else 'celestial/heaven'
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'build/heaven_map.png')
    region_dir = os.path.join(ROOT, 'run/world/dimensions', dim, 'region')
    columns = {}  # (x, z) -> (y, name)
    slice_ = {}   # (x, y) -> name, срез по z == 0
    for fn in os.listdir(region_dir):
        for chunk in read_chunks(os.path.join(region_dir, fn)):
            cx, cz = int(chunk['xPos']), int(chunk['zPos'])
            if str(chunk.get('Status', '')) not in ('minecraft:full', 'full'):
                continue
            for sec in chunk['sections']:
                blocks = section_blocks(sec)
                if not blocks:
                    continue
                sy = int(sec['Y'])
                for idx, name in enumerate(blocks):
                    if name == 'minecraft:air':
                        continue
                    lx, lz, ly = idx & 15, (idx >> 4) & 15, idx >> 8
                    x, z, y = cx * 16 + lx, cz * 16 + lz, sy * 16 + ly
                    cur = columns.get((x, z))
                    if cur is None or y > cur[0]:
                        columns[(x, z)] = (y, name)
                    if z == 0:
                        slice_[(x, y)] = name
    if not columns:
        sys.exit('нет сгенерированных чанков')
    xs = [k[0] for k in columns]
    zs = [k[1] for k in columns]
    x0, z0 = min(xs), min(zs)
    w, h = max(xs) - x0 + 1, max(zs) - z0 + 1
    img = Image.new('RGB', (w, h + 260), (130, 190, 255))
    for (x, z), (y, name) in columns.items():
        r, g, b = block_color(name)
        f = 0.55 + 0.45 * (y / 255)
        img.putpixel((x - x0, z - z0), (int(r * f), int(g * f), int(b * f)))
    for (x, y), name in slice_.items():
        if 0 <= y < 256:
            img.putpixel((x - x0, h + 259 - y), block_color(name))
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save(out)
    solid = len(columns) / (w * h)
    ys = sorted(y for y, _ in columns.values())
    tops = {}
    for _, name in columns.values():
        tops[name] = tops.get(name, 0) + 1
    print(f'{out}: {w}x{h}, заполнено колонок {solid:.0%}, высоты {ys[0]}..{ys[-1]} (медиана {ys[len(ys) // 2]})')
    print('верхние блоки:', sorted(tops.items(), key=lambda t: -t[1])[:8])


if __name__ == '__main__':
    main()
