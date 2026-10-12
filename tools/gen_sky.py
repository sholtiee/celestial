"""Небо мода (волна 0.6, O5 шаг 5): спрайты небесных тел — в `textures/environment/celestial/` (атлас небесных тел ванилли
собирает эту папку из всех пространств имён; спрайт `celestial:<имя>`). Рисует `client/sky/CelestialSky` тем же конвейером, что солнце.
Ореол солнца и полярное сияние Рая, три туманности и звезда созвездий Астрала. Всё — своим шумом и формулами.
"""
import math
import os
import random

from PIL import Image

from gen_assets import ASSETS


def save(img, name):
    path = os.path.join(ASSETS, 'textures/environment/celestial', name + '.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def smooth_noise(rng, w, h, cell):
    gw, gh = w // cell + 2, h // cell + 2
    grid = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x / cell, y / cell
            x0, y0 = int(gx), int(gy)
            tx, ty = gx - x0, gy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0][x0] + (grid[y0][x0 + 1] - grid[y0][x0]) * tx
            b = grid[y0 + 1][x0] + (grid[y0 + 1][x0 + 1] - grid[y0 + 1][x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


def halo():
    """Венец вокруг солнца: тонкое яркое кольцо и мягкое свечение внутри, к краю — в ноль."""
    n = 128
    img = Image.new('RGBA', (n, n))
    for y in range(n):
        for x in range(n):
            r = math.hypot(x - n / 2 + 0.5, y - n / 2 + 0.5) / (n / 2)
            ring = math.exp(-((r - 0.74) / 0.035) ** 2)
            glow = max(0.0, 0.35 * (1 - r)) ** 1.5
            a = min(1.0, ring * 0.55 + glow * 0.6)
            img.putpixel((x, y), (255, 236, 190, int(255 * a)))
    return img


def aurora():
    """Занавесь сияния: вертикальные лучи, ярче у нижнего края, мягко гаснут вверх и по бокам."""
    w, h = 64, 32
    rng = random.Random(4242)
    nz = smooth_noise(rng, w, h, 6)
    img = Image.new('RGBA', (w, h))
    for y in range(h):
        for x in range(w):
            ray = 0.5 + 0.5 * math.sin(x * 0.9 + nz[y][x] * 6)
            k = y / (h - 1)  # 0 верх … 1 низ
            fade = (k ** 1.6) * (1 - k ** 8) * math.sin(math.pi * x / (w - 1))
            a = max(0.0, min(1.0, fade * (0.35 + 0.65 * ray) * (0.6 + 0.6 * nz[y][x])))
            g = int(200 + 55 * k)
            img.putpixel((x, y), (int(120 + 100 * (1 - k)), g, int(180 + 60 * (1 - k)), int(255 * a)))
    return img


def nebula(seed, c1, c2):
    """Туманность: облако из шума, два цвета, мягкий край, редкие звёзды внутри (128 — на полнеба не видно пикселей)."""
    n = 128
    rng = random.Random(seed)
    nz = smooth_noise(rng, n, n, 16)
    nz2 = smooth_noise(rng, n, n, 8)
    img = Image.new('RGBA', (n, n))
    for y in range(n):
        for x in range(n):
            r = math.hypot(x - n / 2 + 0.5, y - n / 2 + 0.5) / (n / 2)
            body = max(0.0, 1 - r) ** 1.3 * (0.5 * nz[y][x] + 0.5 * nz2[y][x])
            a = max(0.0, min(1.0, body * 1.6 - 0.15))
            t = nz2[y][x]
            col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            img.putpixel((x, y), (*col, int(255 * a)))
    for _ in range(24):
        x, y = rng.randrange(16, n - 16), rng.randrange(16, n - 16)
        img.putpixel((x, y), (255, 255, 255, 230))
    return img


def choir_star():
    """Звезда созвездия: яркая точка с крестом лучей и мягким ореолом."""
    n = 16
    img = Image.new('RGBA', (n, n))
    for y in range(n):
        for x in range(n):
            dx, dy = abs(x - 7.5), abs(y - 7.5)
            r = math.hypot(dx, dy)
            core = math.exp(-(r / 1.6) ** 2)
            rays = math.exp(-(min(dx, dy) / 0.6) ** 2) * max(0.0, 1 - max(dx, dy) / 8)
            a = min(1.0, core + rays * 0.8 + max(0.0, 0.25 * (1 - r / 8)))
            img.putpixel((x, y), (255, 248, 225, int(255 * a)))
    return img


def main():
    save(halo(), 'halo')
    save(aurora(), 'aurora')
    save(nebula(11, (90, 60, 200), (220, 90, 200)), 'nebula_1')
    save(nebula(23, (40, 120, 220), (120, 220, 255)), 'nebula_2')
    save(nebula(37, (200, 70, 120), (255, 180, 110)), 'nebula_3')
    save(choir_star(), 'choir_star')
    print('ok: небо — ореол, сияние, туманности, звезда хоров')


if __name__ == '__main__':
    main()
