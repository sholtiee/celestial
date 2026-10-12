#!/usr/bin/env python3
"""Просмотр шаблона постройки без игры: три ортогональных вида (сверху, спереди, сбоку) в один PNG.
   python3 tools/qa/preview_template.py celestial:memory/exile out.png [масштаб]
Цвета блоков — по имени (грубая палитра, остальное — хеш): достаточно, чтобы увидеть форму, проходы и расстановку."""
import colorsys
import hashlib
import os
import sys

import nbtlib
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAL = {'air': None, 'water': (60, 110, 200), 'grass': (110, 170, 70), 'golden_grass': (230, 190, 60), 'dirt': (120, 90, 60), 'stone': (130, 130, 130),
       'light': None, 'oak_leaves': (50, 120, 50), 'leaves': (60, 130, 60), 'skywood_leaves': (230, 200, 90), 'log': (100, 70, 40), 'wood': (100, 70, 40),
       'bricks': (150, 150, 160), 'radiant_stone': (255, 235, 150), 'snow_block': (240, 245, 250), 'ice': (160, 200, 240), 'chain': (90, 90, 100)}


def color(name):
    n = name.split(':')[-1]
    for k, v in PAL.items():
        if k in n:
            return v
    h = int(hashlib.md5(n.encode()).hexdigest()[:6], 16)
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, 0.35 + (h >> 8) % 40 / 100, 0.55 + (h >> 16) % 40 / 100)
    return int(r * 255), int(g * 255), int(b * 255)


def load(ref):
    ns, path = ref.split(':')
    p = os.path.join(ROOT, 'src/main/resources/data', ns, 'structure', path + '.nbt')
    n = nbtlib.load(p)
    pal = [str(e['id']) for e in n['palette']]
    size = tuple(int(v) for v in n['size'])
    blocks = {}
    for b in n['blocks']:
        x, y, z = (int(v) for v in b['pos'])
        blocks[(x, y, z)] = pal[int(b['state'])]
    return size, blocks, len(n['entities'])


def view(size, blocks, axis, s):
    sx, sy, sz = size
    if axis == 'top':
        w, h = sx, sz
    elif axis == 'front':
        w, h = sx, sy
    else:
        w, h = sz, sy
    img = Image.new('RGB', (w * s, h * s), (24, 24, 32))
    d = ImageDraw.Draw(img)
    depth = {}
    for (x, y, z), name in blocks.items():
        c = color(name)
        if c is None:
            continue
        if axis == 'top':
            key, dep, pos = (x, z), y, (x, z)
        elif axis == 'front':
            key, dep, pos = (x, y), z, (x, sy - 1 - y)
        else:
            key, dep, pos = (z, y), x, (z, sy - 1 - y)
        if key not in depth or dep > depth[key][0]:
            depth[key] = (dep, c, pos)
    for dep, c, (px, py) in depth.values():
        shade = 0.6 + 0.4 * (dep / max(1, (sy if axis == 'top' else (sz if axis == 'front' else sx))))
        d.rectangle([px * s, py * s, px * s + s - 1, py * s + s - 1], fill=tuple(int(v * shade) for v in c))
    return img


def main():
    ref, out = sys.argv[1], sys.argv[2]
    s = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    size, blocks, ents = load(ref)
    views = [view(size, blocks, a, s) for a in ('top', 'front', 'side')]
    W = sum(v.width for v in views) + 16 * 4
    H = max(v.height for v in views) + 32
    img = Image.new('RGB', (W, H), (10, 10, 14))
    x = 16
    for v in views:
        img.paste(v, (x, 16))
        x += v.width + 16
    img.save(out)
    print(ref, size, len(blocks), 'блоков,', ents, 'сущностей')


if __name__ == '__main__':
    main()
