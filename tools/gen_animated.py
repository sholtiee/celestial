"""Планка качества: анимированные текстуры блоков (.mcmeta) и иконки вкладок Кодекса.

Идёт после всех генераторов блоков: берёт готовую статичную текстуру как первый кадр и дорисовывает остальные
(блик бежит по граням кристаллов, пульс свечения, мерцание звёзд в купели). Кадры лежат стопкой друг под другом. Запускать в цепочке build_assets (звёзды купели мерцают от статичной картинки gen_starlight).
Разлом Бездны рисуется шейдером портала Энда (TheEndPortalRenderer) — он анимирован сам, своей текстуры у него нет.
"""
import json
import math
import os

from PIL import Image, ImageDraw

import textures as T
from gen_assets import ASSETS, save_png


def load(name):
    return Image.open(os.path.join(ASSETS, 'textures/block', name + '.png')).convert('RGBA').crop((0, 0, 16, 16))  # первый кадр


def save_anim(frames, name, frametime, interpolate=True):
    sheet = Image.new('RGBA', (16, 16 * len(frames)), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (0, 16 * i))
    save_png(sheet, 'block/' + name)
    with open(os.path.join(ASSETS, 'textures/block', name + '.png.mcmeta'), 'w') as f:
        json.dump({'animation': {'frametime': frametime, 'interpolate': interpolate}}, f)


def lighten(img, weight, white=(255, 255, 255)):
    """weight(x, y) → 0..1: подмешать белый только к непрозрачным пикселям."""
    out = img.copy()
    px = out.load()
    for y in range(16):
        for x in range(16):
            r, g, b, a = px[x, y]
            if a:
                k = max(0.0, min(1.0, weight(x, y)))
                px[x, y] = (*T.mix((r, g, b), white, k), a)
    return out


def glint_frames(src, n, strength=0.65, band=3.5):
    """Диагональный блик пробегает по кристаллу и затихает на паузе (последняя четверть кадров — без блика)."""
    frames = []
    for f in range(n):
        pos = (f / (n * 0.75)) * (32 + 2 * band) - band
        frames.append(lighten(src, lambda x, y, p=pos: strength * (1 - abs(x + y - p) / band) if f < n * 0.75 else 0.0))
    return frames


def pulse_frames(src, n, amount, center=(7.5, 7.5), radius=9.0, white=(255, 255, 255)):
    """Свечение у центра дышит: к белому подмешивается тем больше, чем ближе пиксель к центру и чем выше фаза пульса."""
    frames = []
    for f in range(n):
        phase = 0.5 - 0.5 * math.cos(2 * math.pi * f / n)
        frames.append(lighten(src, lambda x, y, p=phase: amount * p * max(0.0, 1 - math.hypot(x - center[0], y - center[1]) / radius), white))
    return frames


def twinkle_frames(src, n):
    """Купель: звёзды мигают в разной фазе, ядро свечения медленно дышит."""
    px = src.load()
    stars = [(x, y) for y in range(16) for x in range(16) if sum(px[x, y][:3]) > 600]
    rng = T.rng_for('star_liquid_twinkle')
    phases = {s: rng.random() * 2 * math.pi for s in stars}
    frames = []
    for f in range(n):
        img = src.copy()
        out = img.load()
        for (x, y) in stars:
            near = [px[x + dx, y + dy][:3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < 16 and 0 <= y + dy < 16
                    and (x + dx, y + dy) not in phases]
            bg = tuple(sum(c[i] for c in near) // max(1, len(near)) for i in range(3)) if near else (20, 30, 70)
            k = 0.5 + 0.5 * math.sin(2 * math.pi * f / n + phases[(x, y)])
            out[x, y] = (*T.mix(bg, px[x, y][:3], 0.15 + 0.85 * k), 255)
        breathe = 0.5 - 0.5 * math.cos(2 * math.pi * f / n)
        frames.append(lighten(img, lambda x, y, b=breathe: 0.18 * b * max(0.0, 1 - math.hypot(x - 7.5, y - 7.5) / 8), (159, 196, 255)))
    return frames


def blocks():
    save_anim(glint_frames(load('sky_crystal'), 12), 'sky_crystal', 3)
    save_anim(glint_frames(load('sky_crystal_block'), 16, strength=0.45, band=4.5), 'sky_crystal_block', 3)
    save_anim(glint_frames(load('shadow_crystal'), 12, strength=0.5), 'shadow_crystal', 3)
    save_anim(pulse_frames(load('ward_crystal_lit'), 8, 0.55), 'ward_crystal_lit', 4)
    save_anim(pulse_frames(load('trial_crystal_running'), 8, 0.6, radius=10.0), 'trial_crystal_running', 3)
    save_anim(twinkle_frames(load('star_liquid'), 12), 'star_liquid', 5)


# ------------------------------------------------------------------ иконки вкладок Кодекса (16×16)
GOLD, DARK, CREAM, CYAN, RED = '#e0b54a', '#6a4b14', '#f4ecd2', '#7fd6ff', '#d9534a'


def icon(draw_fn, name):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(img), img)
    save_png(img, 'gui/codex_tab_' + name)


def saga(d, img):  # раскрытая книга
    d.polygon([(1, 3), (7, 5), (7, 13), (1, 11)], fill=CREAM, outline=DARK)
    d.polygon([(14, 3), (8, 5), (8, 13), (14, 11)], fill=CREAM, outline=DARK)
    d.line([(7, 4), (7, 13)], fill=DARK)
    d.line([(8, 4), (8, 13)], fill=GOLD)
    for y in (6, 8, 10):
        d.line([(2, y), (5, y + 1)], fill='#b9a779')
        d.line([(10, y + 1), (13, y)], fill='#b9a779')
    d.point([(7, 2), (8, 2)], fill=GOLD)


def grace(d, img):  # звезда Благодати и нимб
    d.ellipse([3, 1, 12, 4], outline=GOLD)
    for dx, dy in ((0, 0),):
        d.line([(7, 6), (7, 14)], fill=CYAN)
        d.line([(8, 6), (8, 14)], fill=CYAN)
        d.line([(3, 10), (12, 10)], fill=CYAN)
        d.line([(3, 9), (12, 9)], fill=CYAN)
    d.polygon([(7, 8), (8, 8), (8, 11), (7, 11)], fill='#ffffff')
    d.point([(5, 8), (10, 8), (5, 11), (10, 11), (7, 6), (8, 13)], fill='#ffffff')


def bestiary(d, img):  # лапа
    d.ellipse([4, 8, 11, 14], fill=GOLD, outline=DARK)
    for (x, y) in ((1, 5), (4, 2), (9, 2), (12, 5)):
        d.ellipse([x, y, x + 2, y + 3], fill=GOLD, outline=DARK)
    d.point([(7, 11), (8, 11)], fill=DARK)


def places(d, img):  # компас
    d.ellipse([1, 1, 14, 14], fill='#1d2a4a', outline=GOLD)
    d.polygon([(7, 3), (9, 8), (7, 8)], fill=RED)
    d.polygon([(8, 12), (6, 8), (8, 8)], fill=CREAM)
    d.polygon([(7, 3), (8, 3), (8, 12), (7, 12)], outline=None)
    d.point([(7, 7), (8, 7), (7, 8), (8, 8)], fill=GOLD)
    d.point([(2, 7), (13, 7), (7, 2), (7, 13)], fill=CREAM)


def guide(d, img):  # знак вопроса на свитке
    d.rectangle([3, 1, 12, 14], fill=CREAM, outline=DARK)
    d.line([(3, 2), (12, 2)], fill=GOLD)
    d.line([(3, 13), (12, 13)], fill=GOLD)
    for p in ((6, 5), (7, 4), (8, 4), (9, 5), (9, 6), (8, 7), (7, 8), (7, 9)):
        d.point(p, fill=DARK)
    d.point([(7, 11)], fill=DARK)
    d.point([(8, 11)], fill=DARK)


def lore(d, img):  # перо над свитком: Летопись
    d.rectangle([2, 10, 13, 14], fill=CREAM, outline=DARK)
    d.line([(4, 12), (11, 12)], fill='#b9a779')
    d.polygon([(12, 1), (14, 2), (9, 9), (7, 10), (7, 8)], fill=CYAN, outline=DARK)
    d.line([(7, 10), (4, 13)], fill=DARK)
    d.line([(11, 3), (8, 8)], fill='#ffffff')


def icons():
    for name, fn in (('saga', saga), ('grace', grace), ('bestiary', bestiary), ('places', places), ('guide', guide), ('lore', lore)):
        icon(fn, name)


def main():
    blocks()
    icons()
    print('ok: анимированные текстуры (6) и иконки вкладок Кодекса (6)')


if __name__ == '__main__':
    main()
