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
    codex_background()
    print('ok: частицы и фон Кодекса', len(PARTICLES))


# ---------------------------------------------------------------- фон Кодекса (проход качества)
def codex_background():
    """Книга-«ночное небо» 340×210 в текстуре 512×256: тёмно-синий градиент, звёзды, созвездия, золотая рамка и уголки."""
    import random
    W, H = 340, 210
    img = Image.new('RGBA', (512, 256), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(1717)
    top, bottom = hexrgb('#141a3a'), hexrgb('#0a0d22')
    for y in range(H):
        for x in range(W):
            c = mix(top, bottom, y / H)
            n = (rng.random() - 0.5) * 6
            px[x, y] = (int(max(0, c[0] + n)), int(max(0, c[1] + n)), int(max(0, c[2] + n * 1.3)), 245)
    for _ in range(160):  # звёзды
        x, y = rng.randrange(6, W - 6), rng.randrange(6, H - 6)
        b = rng.choice([90, 130, 180, 230])
        px[x, y] = (b, b, min(255, b + 25), 255)
    for _ in range(5):  # бледные созвездия: ломаные линии между звёздами
        x, y = rng.randrange(30, W - 30), rng.randrange(30, H - 30)
        for _ in range(4):
            nx, ny = x + rng.randint(-28, 28), y + rng.randint(-18, 18)
            steps = max(abs(nx - x), abs(ny - y), 1)
            for i in range(steps):
                ix, iy = int(x + (nx - x) * i / steps), int(y + (ny - y) * i / steps)
                if 4 < ix < W - 4 and 4 < iy < H - 4:
                    r, g, b, a = px[ix, iy]
                    px[ix, iy] = (min(255, r + 25), min(255, g + 25), min(255, b + 40), a)
            px[min(W - 5, max(4, nx)), min(H - 5, max(4, ny))] = (255, 240, 200, 255)
            x, y = min(W - 30, max(30, nx)), min(H - 30, max(30, ny))
    gold, gold_dark = hexrgb('#c9a23a'), hexrgb('#7a5a1a')
    for x in range(W):  # рамка
        for y in (0, 1, H - 2, H - 1):
            px[x, y] = (*(gold if y in (0, H - 1) else gold_dark), 255)
    for y in range(H):
        for x in (0, 1, W - 2, W - 1):
            px[x, y] = (*(gold if x in (0, W - 1) else gold_dark), 255)
    for x in range(5, W - 5):  # внутренняя тонкая линия
        px[x, 4] = px[x, H - 5] = (*gold_dark, 200)
    for y in range(5, H - 5):
        px[4, y] = px[W - 5, y] = (*gold_dark, 200)
    for cx, cy, sx, sy in ((2, 2, 1, 1), (W - 3, 2, -1, 1), (2, H - 3, 1, -1), (W - 3, H - 3, -1, -1)):  # уголки-завитки
        for i in range(10):
            for j in range(10 - i):
                if (i + j) % 3 == 0 or i == 0 or j == 0:
                    px[cx + sx * i, cy + sy * j] = (*gold, 255)
    save_png(img, 'gui/codex')


if __name__ == '__main__':
    main()
