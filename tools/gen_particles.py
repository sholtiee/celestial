"""Свои частицы Celestial: текстуры кадров (8×8) и описания assets/celestial/particles/*.json."""
import math
import os

from PIL import Image

from gen_assets import ASSETS, save_png, write_json
from textures import hexrgb, mix


def blank():
    return Image.new('RGBA', (8, 8), (0, 0, 0, 0))


def star(radius):
    """Четырёхлучевая звезда: белое ядро, золотые лучи; radius — длина лучей (кадры от большой к малой)."""
    img = blank()
    core, ray = hexrgb('#ffffff'), hexrgb('#ffe7a0')
    for i in range(-radius, radius + 1):
        a = int(255 * (1 - abs(i) / (radius + 1)))
        for x, y in ((3 + i, 3), (3, 3 + i), (4 + i, 4), (4, 4 + i)):
            if 0 <= x < 8 and 0 <= y < 8:
                img.putpixel((x, y), (*mix(core, ray, abs(i) / (radius + 0.01)), max(a, 90)))
    for x, y in ((3, 3), (4, 3), (3, 4), (4, 4)):
        img.putpixel((x, y), (*core, 255))
    return img


def blob(r, color, soft):
    img = blank()
    c = hexrgb(color)
    for y in range(8):
        for x in range(8):
            d = math.hypot(x - 3.5, y - 3.5)
            if d <= r:
                img.putpixel((x, y), (*c, int(255 * max(0.0, 1 - (d / r) ** soft))))
    return img


def feather():
    img = blank()
    for i in range(7):  # ствол пера по диагонали и опахало
        img.putpixel((1 + i, 6 - i), (*hexrgb('#d8d0c0'), 255))
        for side in (-1, 1):
            x, y = 1 + i + side, 6 - i
            if 0 <= x < 8 and 0 < i < 6:
                img.putpixel((x, y), (*hexrgb('#ffffff'), 230))
    return img


PARTICLES = {
    'starlight': [star(3), star(3), star(2), star(1)],
    'shadow': [blob(3.6, '#2a1c3a', 1.2), blob(3.4, '#22172f', 1.4), blob(3.0, '#1a1226', 1.6), blob(2.4, '#140e1f', 2.0)],
    'spore': [blob(1.6, '#7af5e3', 1.5), blob(1.2, '#3fe0c8', 2.0)],
    'feather': [feather()],
    'rift': [blob(1.8, '#c9a8ff', 1.2), blob(1.4, '#8a5cd0', 1.5), blob(1.0, '#5b2a8c', 2.0)],
}


def main():
    for name, frames in PARTICLES.items():
        ids = []
        for i, img in enumerate(frames):
            save_png(img, f'particle/{name}_{i}')
            ids.append(f'celestial:{name}_{i}')
        write_json(os.path.join(ASSETS, 'particles', name + '.json'), {'textures': ids})
    print('ok: частицы', len(PARTICLES))


if __name__ == '__main__':
    main()
