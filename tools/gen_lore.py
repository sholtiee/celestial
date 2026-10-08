"""Летопись Небес: переводы, данные для игры и иллюстрации-кадры по tools/lore_data.py (docs/LORE.md).

Выход:
- `data/celestial/lore/lore.json` — структура (книги, узлы «Нити», листы, Глоссарий); читает `dev.celestial.lore.Lore` на сервере и клиенте;
- переводы `lore.celestial.*` (ru/en);
- `textures/gui/lore/<id>.png` — картинка листа 96×54 (рисуется кодом, ванильного арта нет), `lore_locked.png` — для закрытых листов.
Бог и Христос не изображаются: на картинках только свет, места, вещи и силуэты.
"""
import json
import math
import os

from PIL import Image, ImageDraw

import lore_data as L
import textures as T
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, write_json
from gen_story import advancement, lang_patch

W, H = 96, 54


# ------------------------------------------------------------------ рисование
def rgb(h):
    return T.hexrgb(h)


def gradient(top, bottom):
    """Вертикальный градиент с упорядоченным дизерингом 2×2 — как «пиксель-арт», без плавных полутонов."""
    img = Image.new('RGBA', (W, H))
    px = img.load()
    a, b = rgb(top), rgb(bottom)
    bayer = ((0, 2), (3, 1))
    for y in range(H):
        for x in range(W):
            t = y / (H - 1) + (bayer[y % 2][x % 2] - 1.5) / 14
            px[x, y] = (*T.mix(a, b, max(0.0, min(1.0, t))), 255)
    return img


def glow(img, cx, cy, r, color, power=1.0):
    px = img.load()
    c = rgb(color)
    for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
            d = math.hypot(x - cx, y - cy)
            if d < r:
                k = (1 - d / r) ** 2 * power
                px[x, y] = (*T.mix(px[x, y][:3], c, min(1.0, k)), 255)


def stars(img, rng, n, ymax=H, colors=('#ffffff', '#fff3c6', '#bfd8ff')):
    for _ in range(n):
        img.putpixel((rng.randrange(W), rng.randrange(ymax)), (*rgb(rng.choice(colors)), 255))


def hills(img, base, amp, color, seed, wavelength=22.0):
    r = T.rng_for('hills' + seed)
    ph = r.random() * 6.28
    d = ImageDraw.Draw(img)
    for x in range(W):
        y = int(base + amp * math.sin(x / wavelength * 6.28 + ph) + amp * 0.5 * math.sin(x / (wavelength * 0.45) + ph * 2))
        d.line([(x, y), (x, H)], fill=rgb(color))


def tree(d, x, y, h, trunk, crown, r=None):
    r = r or max(4, h // 2)
    d.rectangle([x - 1, y - h // 2, x, y], fill=rgb(trunk))
    for dx, dy, rr in ((0, -h // 2 - r // 2, r), (-r // 2, -h // 2, r * 2 // 3), (r // 2, -h // 2, r * 2 // 3)):
        d.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill=rgb(crown))


def figure(d, x, y, h, robe, halo=None):
    """Силуэт человека в одежде до пят: без лица и черт (память — не портрет)."""
    d.ellipse([x - 1, y - h, x + 1, y - h + 2], fill=rgb('#e9cfa8'))
    d.polygon([(x - 1, y - h + 3), (x + 1, y - h + 3), (x + 3, y), (x - 3, y)], fill=rgb(robe))
    if halo:
        d.ellipse([x - 2, y - h - 2, x + 2, y - h], outline=rgb(halo))


def flame(d, x, y, h, w=2):
    for i, c in enumerate(('#ff7a2a', '#ffb347', '#fff1b8')):
        k = 1 - i * 0.28
        d.polygon([(x - w * k, y), (x, y - h * k), (x + w * k, y)], fill=rgb(c))


# ------------------------------------------------------------------ мотивы (ключ art → функция)
def art_light(rng):
    img = gradient('#10183a', '#2a3770')
    glow(img, 48, 27, 46, '#fff6d6', 1.15)
    d = ImageDraw.Draw(img)
    for i in range(16):
        a = i * math.pi / 8
        d.line([(48 + 6 * math.cos(a), 27 + 6 * math.sin(a)), (48 + 52 * math.cos(a), 27 + 52 * math.sin(a))], fill=rgb('#fff1b8'))
    glow(img, 48, 27, 9, '#ffffff', 1.5)
    return img


def art_garden(rng):
    img = gradient('#f6d98a', '#9fd6ff')
    d = ImageDraw.Draw(img)
    hills(img, 36, 3, '#6aa84f', 'g1')
    hills(img, 42, 2, '#4f8a3a', 'g2', 17.0)
    d.line([(10, 54), (40, 44), (60, 46), (90, 40)], fill=rgb('#7fc6f2'), width=2)
    tree(d, 22, 38, 14, '#6b4a24', '#3f7a2a')
    tree(d, 70, 36, 12, '#6b4a24', '#4f8a3a')
    return img


def art_names(rng):
    img = gradient('#ffe7b0', '#bfe3a0')
    d = ImageDraw.Draw(img)
    hills(img, 40, 2, '#79b455', 'n1')
    d.ellipse([14, 34, 26, 42], fill=rgb('#f4ecd2'))  # баран
    d.arc([10, 31, 18, 38], 90, 360, fill=rgb('#c9a23a'))
    d.rectangle([16, 41, 17, 46], fill=rgb('#f4ecd2'))
    d.rectangle([23, 41, 24, 46], fill=rgb('#f4ecd2'))
    d.line([(44, 20), (48, 24), (52, 20)], fill=rgb('#3a3a4a'))  # птицы
    d.line([(58, 14), (61, 17), (64, 14)], fill=rgb('#3a3a4a'))
    d.ellipse([60, 36, 76, 44], fill=rgb('#c98a4a'))  # зверь
    d.rectangle([62, 43, 63, 48], fill=rgb('#c98a4a'))
    d.rectangle([73, 43, 74, 48], fill=rgb('#c98a4a'))
    d.polygon([(76, 37), (82, 34), (80, 40)], fill=rgb('#c98a4a'))
    for x in (30, 52):
        d.ellipse([x, 30, x + 3, 33], fill=rgb('#ffd24a'))
    return img


def art_tree_life(rng):
    img = gradient('#1a2a4a', '#4a6a9a')
    glow(img, 48, 22, 34, '#ffd24a', 0.9)
    d = ImageDraw.Draw(img)
    hills(img, 46, 2, '#2f6a3a', 'tl')
    tree(d, 48, 46, 30, '#8a5a24', '#e0b54a', 16)
    for _ in range(14):
        x, y = rng.randrange(28, 68), rng.randrange(6, 30)
        d.point((x, y), fill=rgb('#fff3c6'))
    d.line([(0, 52), (96, 50)], fill=rgb('#7fc6f2'), width=2)
    return img


def art_fruit(rng):
    img = gradient('#2a1f3a', '#6a4a5a')
    d = ImageDraw.Draw(img)
    hills(img, 46, 2, '#1f2a24', 'fr')
    tree(d, 48, 48, 30, '#4a3220', '#355a2a', 15)
    d.ellipse([54, 24, 58, 28], fill=rgb('#d9342a'))  # плод
    d.point((56, 23), fill=rgb('#7fbf4a'))
    pts = [(46 + 3 * math.sin(i / 2.2), 48 - i * 1.4) for i in range(18)]  # змей на стволе
    d.line(pts, fill=rgb('#9fcf4a'), width=1)
    for x in (20, 26, 72, 80):  # терновник
        d.line([(x, 52), (x + 2, 46), (x + 5, 49)], fill=rgb('#5a4a2a'))
    return img


def art_exile(rng):
    img = gradient('#f6c26a', '#3a2a4a')
    glow(img, 48, 18, 30, '#fff1b8', 0.8)
    d = ImageDraw.Draw(img)
    d.rectangle([30, 14, 34, 44], fill=rgb('#e8dcb8'))
    d.rectangle([62, 14, 66, 44], fill=rgb('#e8dcb8'))
    d.arc([30, 6, 66, 30], 180, 360, fill=rgb('#e8dcb8'), width=3)
    d.polygon([(0, 54), (96, 54), (96, 46), (0, 46)], fill=rgb('#2a2236'))
    d.polygon([(40, 54), (56, 54), (50, 46), (46, 46)], fill=rgb('#7a6a5a'))
    figure(d, 12, 50, 9, '#9a8a7a')
    return img


def art_sword(rng):
    img = gradient('#0e1230', '#3a1f3a')
    stars(img, rng, 40, 40)
    glow(img, 48, 27, 24, '#ff7a2a', 0.8)
    d = ImageDraw.Draw(img)
    d.ellipse([28, 7, 68, 47], outline=rgb('#ffb347'), width=2)
    d.ellipse([34, 13, 62, 41], outline=rgb('#fff1b8'))
    d.polygon([(47, 4), (49, 4), (50, 36), (46, 36)], fill=rgb('#ffe08a'))
    d.rectangle([42, 36, 54, 38], fill=rgb('#c9a23a'))
    d.rectangle([47, 38, 49, 46], fill=rgb('#8a5a24'))
    flame(d, 48, 14, 8, 3)
    return img


def art_altars(rng):
    img = gradient('#3a2a3a', '#a86a4a')
    d = ImageDraw.Draw(img)
    d.polygon([(0, 54), (96, 54), (96, 44), (0, 44)], fill=rgb('#2a2230'))
    for x in (18, 66):
        d.rectangle([x, 38, x + 12, 46], fill=rgb('#8a8a9a'))
        d.rectangle([x + 1, 36, x + 11, 38], fill=rgb('#aaaaba'))
    for i in range(14):  # дым Авеля поднимается
        d.point((24 + int(2 * math.sin(i / 2)), 36 - i * 2), fill=rgb('#f4ecd2'))
    for i in range(14):  # дым Каина стелется по земле
        d.point((72 + i * 1.6, 36 + int(i * 0.6) % 6 - i // 3), fill=rgb('#6a5a5a'))
    d.ellipse([48, 46, 51, 49], fill=rgb('#c0342a'))  # алый цветок
    return img


def art_mark(rng):
    img = gradient('#10122a', '#2a1a2a')
    stars(img, rng, 30, 34)
    glow(img, 48, 14, 16, '#ff3a2a', 0.9)
    d = ImageDraw.Draw(img)
    d.ellipse([42, 8, 54, 20], outline=rgb('#ff6a4a'), width=2)
    d.line([(48, 9), (48, 19)], fill=rgb('#ffb0a0'))
    d.line([(43, 14), (53, 14)], fill=rgb('#ffb0a0'))
    d.polygon([(0, 54), (96, 54), (96, 46), (60, 44), (0, 48)], fill=rgb('#1a1626'))
    figure(d, 30, 48, 12, '#1a1626')
    d.rectangle([29, 36, 31, 49], outline=rgb('#3a3248'))
    return img


def art_watchers(rng):
    img = gradient('#0e1230', '#3a4a7a')
    stars(img, rng, 24, 20)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 54), (30, 30), (48, 22), (66, 30), (96, 54)], fill=rgb('#1a2236'))
    for i in range(22):  # светящиеся фигуры спускаются на гору
        x = 34 + (i * 7) % 30
        y = 4 + (i * 11) % 18
        d.line([(x, y), (x + 1, y + 3)], fill=rgb('#ffe9a0'))
        d.point((x, y), fill=rgb('#ffffff'))
    return img


def art_forge(rng):
    img = gradient('#1a1218', '#3a1f14')
    glow(img, 48, 40, 34, '#ff7a2a', 1.0)
    d = ImageDraw.Draw(img)
    d.rectangle([34, 38, 62, 42], fill=rgb('#3a3a46'))  # наковальня
    d.polygon([(30, 38), (34, 38), (34, 36), (28, 36)], fill=rgb('#3a3a46'))
    d.rectangle([42, 42, 54, 50], fill=rgb('#2a2a34'))
    d.line([(36, 35), (58, 33)], fill=rgb('#cfd8e8'), width=2)  # клинок на наковальне
    flame(d, 70, 48, 14, 4)
    flame(d, 24, 50, 9, 3)
    for _ in range(18):
        d.point((rng.randrange(30, 70), rng.randrange(10, 36)), fill=rgb('#ffb347'))
    return img


def art_giant(rng):
    img = gradient('#2a3a5a', '#8a9ab0')
    d = ImageDraw.Draw(img)
    hills(img, 44, 2, '#3a4a3a', 'gi')
    d.ellipse([54, 2, 66, 14], fill=rgb('#1a1f2a'))
    d.polygon([(52, 14), (68, 14), (74, 46), (46, 46)], fill=rgb('#1a1f2a'))
    d.rectangle([42, 20, 46, 46], fill=rgb('#1a1f2a'))  # дубина
    figure(d, 18, 50, 8, '#c9a23a')
    d.line([(18, 44), (26, 38)], fill=rgb('#e8e0d0'))  # праща
    d.point((28, 36), fill=rgb('#ffffff'))
    return img


def art_enoch(rng):
    img = gradient('#fff1b8', '#3a4a7a')
    glow(img, 48, 4, 30, '#ffffff', 1.0)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 54), (96, 54), (96, 46), (0, 46)], fill=rgb('#2a2a3a'))
    for i in range(10):  # дорога света вверх
        w = 3 + i * 2
        d.line([(48 - w, 46 - i * 4), (48 + w, 46 - i * 4)], fill=rgb('#fff6d6'))
    figure(d, 48, 46, 9, '#f4ecd2', '#ffd24a')
    return img


def art_chains(rng):
    img = gradient('#0e0e1a', '#2a1f3a')
    d = ImageDraw.Draw(img)
    for x in (22, 40, 58, 76):
        y = 0
        while y < 40 + (x % 7):
            d.ellipse([x - 2, y, x + 2, y + 5], outline=rgb('#9aa0b0'))
            y += 4
        d.ellipse([x - 3, y, x + 3, y + 6], outline=rgb('#6a6a7a'), width=2)
    glow(img, 48, 48, 30, '#4a2a5a', 0.8)
    d.line([(0, 52), (96, 52)], fill=rgb('#3a2a4a'), width=2)
    return img


def art_abyss(rng):
    img = gradient('#0a0612', '#2a1040')
    d = ImageDraw.Draw(img)
    d.polygon([(48, 10), (92, 24), (48, 40), (4, 24)], fill=rgb('#140a22'))  # скат тьмы
    d.polygon([(48, 20), (60, 24), (48, 28), (36, 24)], fill=rgb('#2a1a3a'))
    d.ellipse([44, 22, 52, 26], fill=rgb('#ffd24a'))
    stars(img, rng, 14, 54, ('#7a5ab0', '#4a3a8a'))
    d.line([(0, 52), (96, 52)], fill=rgb('#1a0f2a'))
    return img


def art_star_fall(rng):
    img = gradient('#0a0f2a', '#4a1f3a')
    stars(img, rng, 40, 30)
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(((12, 4), (34, 2), (60, 6), (80, 10))):
        d.line([(x, y), (x + 14, y + 30)], fill=rgb('#ffb347' if i % 2 else '#ff7a5a'))
    glow(img, 48, 8, 12, '#fff6d6', 1.2)
    d.ellipse([46, 6, 50, 10], fill=rgb('#ffffff'))
    d.line([(48, 10), (66, 50)], fill=rgb('#ffe9a0'))
    d.polygon([(0, 54), (96, 54), (96, 50), (0, 50)], fill=rgb('#0a0612'))
    return img


def art_waters(rng):
    img = gradient('#cfe9ff', '#2a5a9a')
    d = ImageDraw.Draw(img)
    d.rectangle([0, 24, 96, 29], fill=rgb('#f4f9ff'))  # твердь
    for x in range(0, 96, 6):
        d.arc([x, 8, x + 6, 16], 0, 180, fill=rgb('#9fcdf0'))
        d.arc([x, 36, x + 6, 44], 0, 180, fill=rgb('#7fb0e0'))
        d.arc([x + 3, 44, x + 9, 52], 0, 180, fill=rgb('#4a7ac0'))
    return img


def art_flood(rng):
    img = gradient('#1a2236', '#3a5a7a')
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 96, 14], fill=rgb('#2a2f3f'))
    for _ in range(60):
        x, y = rng.randrange(W), rng.randrange(8, 44)
        d.line([(x, y), (x - 1, y + 4)], fill=rgb('#9fcdf0'))
    d.rectangle([0, 40, 96, 54], fill=rgb('#2a4a7a'))
    for x in range(0, 96, 6):
        d.arc([x, 38, x + 6, 44], 0, 180, fill=rgb('#7fb0e0'))
    d.polygon([(34, 38), (64, 38), (60, 44), (38, 44)], fill=rgb('#6a4a24'))  # ковчег в волнах
    d.rectangle([44, 32, 56, 38], fill=rgb('#8a6a34'))
    return img


def art_ark(rng):
    img = gradient('#dff0ff', '#8ab0d0')
    d = ImageDraw.Draw(img)
    d.polygon([(0, 54), (96, 54), (96, 44), (0, 46)], fill=rgb('#e8f4ff'))
    d.polygon([(12, 40), (84, 40), (76, 52), (22, 52)], fill=rgb('#5a3a1a'))  # корпус вмёрз
    d.rectangle([30, 28, 66, 40], fill=rgb('#7a5a2a'))
    d.polygon([(28, 28), (68, 28), (62, 22), (34, 22)], fill=rgb('#5a3a1a'))
    for x in (36, 46, 56):
        d.rectangle([x, 31, x + 3, 35], fill=rgb('#f6d98a'))
    for _ in range(26):
        d.point((rng.randrange(W), rng.randrange(H)), fill=rgb('#ffffff'))
    return img


def art_dove(rng):
    img = gradient('#ffd9a0', '#9fd6ff')
    d = ImageDraw.Draw(img)
    d.rectangle([0, 44, 96, 54], fill=rgb('#6aa0d0'))
    glow(img, 20, 40, 20, '#fff1b8', 0.8)
    d.polygon([(26, 34), (38, 28), (40, 32), (32, 36)], fill=rgb('#e8f0ff'))  # хвост
    d.ellipse([34, 26, 56, 36], fill=rgb('#ffffff'))  # тело
    d.ellipse([54, 23, 62, 31], fill=rgb('#ffffff'))  # голова
    d.polygon([(62, 26), (67, 27), (62, 29)], fill=rgb('#e0b54a'))  # клюв
    d.point((59, 26), fill=rgb('#2a2a3a'))
    d.polygon([(38, 28), (44, 10), (54, 14), (52, 28)], fill=rgb('#f4f9ff'))  # поднятое крыло
    d.line([(44, 12), (50, 26)], fill=rgb('#c8d8f0'))
    d.line([(66, 28), (78, 24)], fill=rgb('#5a8a3a'))  # масличная ветвь
    for x, y in ((70, 26), (73, 24), (76, 23)):
        d.ellipse([x, y - 2, x + 3, y + 1], fill=rgb('#6aa84f'))
    return img


def art_rainbow(rng):
    img = gradient('#9fd6ff', '#e8f6ff')
    d = ImageDraw.Draw(img)
    for i, c in enumerate(('#ff5a4a', '#ff9a3a', '#ffd24a', '#5ae07a', '#5aa8ff', '#6a5ae0', '#b05ae0')):
        r = 42 - i * 2
        d.arc([48 - r, 54 - r, 48 + r, 54 + r + 20], 180, 360, fill=rgb(c), width=2)
    for x, y in ((8, 46), (84, 44), (24, 50), (70, 50)):
        d.ellipse([x - 8, y - 4, x + 8, y + 4], fill=rgb('#ffffff'))
    return img


def art_archon(rng):
    img = gradient('#0e1e3a', '#3a6a9a')
    stars(img, rng, 20, 24)
    glow(img, 48, 30, 26, '#7fd6ff', 0.7)
    d = ImageDraw.Draw(img)
    d.polygon([(48, 8), (66, 22), (62, 46), (34, 46), (30, 22)], fill=rgb('#cfeaff'))  # ледяной трон-фигура
    d.polygon([(48, 14), (58, 24), (54, 44), (42, 44), (38, 24)], fill=rgb('#5a9ad0'))
    for x in (28, 36, 60, 68):
        d.polygon([(x, 46), (x + 2, 20 + abs(x - 48) // 3), (x + 4, 46)], fill=rgb('#e8f6ff'))
    d.ellipse([45, 24, 51, 30], fill=rgb('#ffffff'))
    d.polygon([(40, 12), (44, 6), (48, 11), (52, 6), (56, 12)], fill=rgb('#e8f6ff'))
    return img


def art_locked(rng):
    img = gradient('#1a1a24', '#2a2a38')
    d = ImageDraw.Draw(img)
    for p in ((44, 18), (46, 16), (50, 16), (52, 18), (52, 21), (50, 23), (48, 25), (48, 28)):
        d.rectangle([p[0], p[1], p[0] + 1, p[1] + 1], fill=rgb('#6a6a80'))
    d.rectangle([48, 32, 49, 33], fill=rgb('#6a6a80'))
    return img


ART = {
    'light': art_light, 'garden': art_garden, 'names': art_names, 'tree_life': art_tree_life, 'fruit': art_fruit, 'exile': art_exile,
    'sword': art_sword, 'altars': art_altars, 'mark': art_mark, 'watchers': art_watchers, 'forge': art_forge, 'giant': art_giant,
    'enoch': art_enoch, 'chains': art_chains, 'abyss': art_abyss, 'star_fall': art_star_fall, 'waters': art_waters, 'flood': art_flood,
    'ark': art_ark, 'dove': art_dove, 'rainbow': art_rainbow, 'archon': art_archon,
}


def frame(img):
    """Золотая рамка по краю кадра."""
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=rgb('#c9a23a'))
    d.rectangle([1, 1, W - 2, H - 2], outline=rgb('#6a4b14'))
    return img


def illustrations():
    for art, fn in ART.items():
        save_png(frame(fn(T.rng_for('lore_art_' + art))), f'gui/lore/{art}')
    save_png(frame(art_locked(T.rng_for('lore_art_locked'))), 'gui/lore/locked')


# ------------------------------------------------------------------ свиток и скрижаль
def scroll_item():
    """Свиток: скрученный пергамент с деревянными валиками и красной лентой."""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(2, 11), (11, 2), (14, 5), (5, 14)], fill=rgb('#f1e3b4'), outline=rgb('#6a4b14'))
    d.line([(4, 10), (10, 4)], fill=rgb('#d8c48a'))
    d.line([(5, 12), (12, 5)], fill=rgb('#d8c48a'))
    d.polygon([(10, 1), (13, 1), (15, 4), (12, 4)], fill=rgb('#8a5a24'), outline=rgb('#4a3014'))  # валик сверху
    d.polygon([(1, 12), (4, 12), (4, 15), (1, 14)], fill=rgb('#8a5a24'), outline=rgb('#4a3014'))  # валик снизу
    d.line([(7, 7), (9, 9)], fill=rgb('#b8322a'), width=2)  # лента
    d.point((8, 8), fill=rgb('#ffd24a'))
    save_png(img, 'item/lore_scroll')
    model('item/lore_scroll', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/lore_scroll')}})
    item_def('lore_scroll', c('item/lore_scroll'))


def tablet_block():
    """Скрижаль: тёмная плита на подставке; лицо с высеченными строками и знаком света."""
    stone = T.noisy('lore_tablet_stone', [rgb(h) for h in ('#4a4f5c', '#565c6a', '#646b7a')], cell=3, grain=0.3).convert('RGBA')
    save_png(stone, 'block/lore_tablet_stone')
    face = stone.copy()
    d = ImageDraw.Draw(face)
    d.rectangle([0, 0, 15, 15], outline=rgb('#2a2e38'))
    d.rectangle([1, 1, 14, 14], outline=rgb('#8a8f9c'))
    for y in (7, 9, 11, 13):  # строки
        for x in range(3, 13, 2):
            if (x * 7 + y * 3) % 5:
                d.point((x, y), fill=rgb('#1c1f26'))
                d.point((x + 1, y), fill=rgb('#1c1f26'))
    d.rectangle([7, 2, 8, 5], fill=rgb('#e0b54a'))  # знак света сверху
    d.rectangle([5, 3, 10, 4], fill=rgb('#e0b54a'))
    d.point((7, 3), fill=rgb('#fff6d6'))
    save_png(face, 'block/lore_tablet_face')
    side = {'texture': '#stone'}
    model('block/lore_tablet', {'textures': {'stone': c('block/lore_tablet_stone'), 'face': c('block/lore_tablet_face'),
                                              'particle': c('block/lore_tablet_stone')},
                                'elements': [
        {'from': [3, 0, 6], 'to': [13, 2, 10], 'faces': {k: side for k in ('north', 'south', 'east', 'west', 'up', 'down')}},
        {'from': [4, 2, 7], 'to': [12, 15, 9], 'faces': {'north': {'texture': '#face', 'uv': [4, 1, 12, 14]},
                                                         'south': {'texture': '#face', 'uv': [4, 1, 12, 14]},
                                                         'east': side, 'west': side, 'up': side, 'down': side}}]})
    blockstate('lore_tablet', {'variants': {f'facing={f}': {'model': c('block/lore_tablet'), 'y': y} for f, y in
                                            (('north', 0), ('east', 90), ('south', 180), ('west', 270))}})
    item_def('lore_tablet', c('block/lore_tablet'))


def loot_scrolls():
    """Свитки в добыче построек (дописываем пул в готовые таблицы): Азазель — в остове галеона (там пушки и оружие)."""
    path = os.path.join(DATA, 'loot_table/chests/airship_wreck.json')
    with open(path, encoding='utf-8') as f:
        table = json.load(f)
    if 'celestial:lore_scroll' in json.dumps(table):
        return
    table['pools'].append({'rolls': 1, 'entries': [
        {'type': 'minecraft:item', 'name': c('lore_scroll'), 'weight': 1,
         'modifier': [{'type': 'minecraft:set_custom_data', 'tag': '{sheet:"azazel"}'}]},
        {'type': 'minecraft:empty', 'weight': 3}]})
    write_json(path, table)


# ------------------------------------------------------------------ данные и переводы
def lore_json():
    sheets = [{'id': s['id'], 'book': s['book'], 'node': s['node'], 'art': s['art'], 'src': s['src'],
               'has_quote': bool(s['quote']), 'has_s': bool(s.get('s')), 'has_a': bool(s.get('a')), 'has_t': bool(s.get('t')),
               'gloss': s['gloss']} for s in L.SHEETS]
    data = {'books': sorted(L.BOOKS), 'nodes': [{'id': n[0], 'act': n[3]} for n in L.NODES], 'sheets': sheets, 'glossary': sorted(L.GLOSSARY)}
    write_json(os.path.join(DATA, 'lore/lore.json'), data)


def lang():
    e = {}
    for n, (ru, en) in L.BOOKS.items():
        e[f'lore.celestial.book.{n}'] = (ru, en)
    for nid, ru, en, _act in L.NODES:
        e[f'lore.celestial.node.{nid}'] = (ru, en)
    for s in L.SHEETS:
        p = f'lore.celestial.sheet.{s["id"]}'
        e[p + '.title'] = s['title']
        e[p + '.how'] = s['how']
        if s['ref']:
            e[p + '.ref'] = s['ref']
        if s['quote']:
            e[p + '.quote'] = s['quote']
        for k in ('s', 'a', 't'):
            if s.get(k):
                e[f'{p}.{k}'] = s[k]
    for gid, (ru, en, who_ru, who_en, here_ru, here_en) in L.GLOSSARY.items():
        e[f'lore.celestial.gloss.{gid}'] = (ru, en)
        e[f'lore.celestial.gloss.{gid}.who'] = (who_ru, who_en)
        e[f'lore.celestial.gloss.{gid}.here'] = (here_ru, here_en)
    e.update({
        'codex.celestial.tab.lore': ('Летопись', 'Chronicle'),
        'lore.celestial.view.thread': ('Нить', 'Thread'),
        'lore.celestial.view.books': ('Книги', 'Books'),
        'lore.celestial.view.glossary': ('Глоссарий', 'Glossary'),
        'lore.celestial.kind.s': ('Писание', 'Scripture'),
        'lore.celestial.kind.a': ('Апокриф Небес', 'Apocrypha of Heaven'),
        'lore.celestial.kind.t': ('Предание', 'Tradition'),
        'lore.celestial.progress': ('%s из %s листов', '%s of %s sheets'),
        'lore.celestial.soon': ('скоро', 'soon'),
        'lore.celestial.locked': ('Лист закрыт', 'Sheet sealed'),
        'lore.celestial.how': ('Как открыть: %s', 'How to open: %s'),
        'lore.celestial.back': ('← К книгам', '← To books'),
        'lore.celestial.thread.hint': ('Каждый узел загорается, когда открыт хоть один его лист.', 'A node lights up once any of its sheets is open.'),
        'lore.celestial.thread.node': ('%s: %s из %s', '%s: %s of %s'),
        'lore.celestial.thread.acts': ('Акты:', 'Acts:'),
        'lore.celestial.thread.here': ('здесь ты', 'you are here'),
        'lore.celestial.gloss.here': ('Здесь: ', 'Here: '),
        'lore.celestial.gloss.empty': ('Слова появятся, когда они встретятся в Летописи.', 'Words appear as they are met in the Chronicle.'),
        'lore.celestial.unlocked': ('Летопись: новый лист — «%s»', 'Chronicle: a new sheet — "%s"'),
        'lore.celestial.glossary_added': ('Глоссарий: %s', 'Glossary: %s'),
        'lore.celestial.unknown': ('Нет такого листа: %s', 'No such sheet: %s'),
        'lore.celestial.cmd.unlocked': ('Открыто листов: %s', 'Sheets opened: %s'),
        'item.celestial.lore_scroll': ('Свиток Летописи', 'Chronicle Scroll'),
        'item.celestial.lore_scroll.named': ('Свиток: «%s»', 'Scroll: "%s"'),
        'item.celestial.lore_scroll.lore1': ('ПКМ — прочесть: лист ляжет в твою Летопись.', 'Use to read: the sheet is added to your Chronicle.'),
        'block.celestial.lore_tablet': ('Скрижаль', 'Tablet'),
        'block.celestial.lore_tablet.lore1': ('ПКМ — прочесть высеченный лист Летописи.', 'Use to read the Chronicle sheet carved upon it.'),
        'lore.celestial.scroll.known': ('Этот лист уже в твоей Летописи.', 'This sheet is already in your Chronicle.'),
        'lore.celestial.scroll.blank': ('Свиток пуст: письмена стёрлись.', 'The scroll is blank: the script has faded.'),
        'lore.celestial.tablet.blank': ('Письмена на скрижали стёрлись.', 'The script on the tablet has worn away.'),
        'lore.celestial.cmd.gloss': ('Слов добавлено: %s', 'Words added: %s'),
        'lore.celestial.cmd.locked': ('Закрыто листов: %s', 'Sheets sealed: %s'),
    })
    lang_patch(e)


def achievements():
    """Ветка «Летопись» (под корнем саги): первая запись, по книге, Глоссарий, Нарёкший имена, Летописец. Выдаёт lore/Lore.check (критерий impossible)."""
    imp = {'granted': {'trigger': 'minecraft:impossible'}}
    scroll = c('lore_scroll')
    items = [('chronicle_first', scroll, 'task', 'Первая запись', 'Открой любой лист Летописи', 'The First Entry', 'Open any sheet of the Chronicle')]
    for n, (ru, en) in L.BOOKS.items():
        if any(s['book'] == n for s in L.SHEETS):
            items.append((f'chronicle_book_{n}', scroll, 'goal', ru, f'Открой все листы: «{ru}»', en, f'Open every sheet of {en}'))
    items.append(('chronicle_glossary', scroll, 'goal', 'Знаток слов', 'Узнай все слова Глоссария', 'Master of Words', 'Learn every word of the Glossary'))
    items.append(('chronicle_names', c('wanderer_journal'), 'goal', 'Нарёкший имена', 'Запиши в Бестиарий 24 существа, как Адам нарёк тварей',
                  'Namer of Creatures', 'Record 24 creatures in the Bestiary, as Adam named the beasts'))
    if all(any(s['book'] == n for s in L.SHEETS) for n in L.BOOKS):
        items.append(('chronicle_scribe', c('wanderer_journal'), 'challenge', 'Летописец', 'Открой каждый лист Летописи Небес', 'Chronicler', 'Open every sheet of the Chronicle of Heaven'))
    e = {}
    for path, icon, frame, ru_t, ru_d, en_t, en_d in items:
        advancement(path, 'root', icon, imp, frame, f'advancements.celestial.{path}.title', f'advancements.celestial.{path}.description')
        e[f'advancements.celestial.{path}.title'] = (ru_t, en_t)
        e[f'advancements.celestial.{path}.description'] = (ru_d, en_d)
    lang_patch(e)
    return len(items)


def main():
    scroll_item()
    tablet_block()
    loot_scrolls()
    lore_json()
    lang()
    illustrations()
    n_adv = achievements()
    print('ok: Летопись —', len(L.SHEETS), 'листов,', len(L.GLOSSARY), 'слов Глоссария,', len(ART), 'иллюстраций,', n_adv, 'достижений')


if __name__ == '__main__':
    main()
