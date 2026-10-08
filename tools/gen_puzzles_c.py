"""Головоломки этапа C (docs/PUZZLES.md): Звёздный кодовый замок — диски, фрески-подсказки, печать «сверить».

Созвездия — свои глифы (звёзды и линии), 8 штук; цвета оправ — красный, зелёный, синий, золотой.
Постройка — купол обсерватории (gen_places.observatory).
"""
import math

from PIL import Image, ImageDraw

import textures as T
from gen_abyss import append_tag
from gen_assets import c, save_png, blockstate, model, item_def
from gen_story import lang_patch

COLORS = ['#ff5a4a', '#5ae07a', '#5aa8ff', '#ffd24a']
COLOR_NAMES = [('красный', 'red'), ('зелёный', 'green'), ('синий', 'blue'), ('золотой', 'gold')]
# созвездия: звёзды (x, y в сетке 0..9) и линии между ними (индексы)
GLYPHS = [
    ('Корона', 'Crown', [(1, 6), (2, 2), (4, 5), (5, 1), (6, 5), (8, 2), (9, 6)], [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0)]),
    ('Крыло', 'Wing', [(1, 8), (3, 5), (5, 3), (8, 1), (6, 6), (9, 4)], [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (5, 3)]),
    ('Око', 'Eye', [(1, 5), (5, 2), (9, 5), (5, 8), (5, 5)], [(0, 1), (1, 2), (2, 3), (3, 0)]),
    ('Копьё', 'Spear', [(1, 9), (4, 6), (7, 3), (9, 1), (6, 2), (8, 4)], [(0, 1), (1, 2), (2, 3), (4, 3), (3, 5)]),
    ('Колокол', 'Bell', [(5, 1), (3, 3), (7, 3), (2, 7), (8, 7), (5, 9)], [(0, 1), (0, 2), (1, 3), (2, 4), (3, 4)]),
    ('Волк', 'Wolf', [(1, 3), (3, 2), (4, 4), (7, 4), (9, 2), (8, 7), (3, 7)], [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (2, 6)]),
    ('Луна', 'Moon', [(6, 1), (3, 2), (2, 5), (3, 8), (6, 9), (4, 5)], [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 4)]),
    ('Древо', 'Tree', [(5, 9), (5, 5), (2, 3), (8, 3), (5, 1), (3, 6), (7, 6)], [(0, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)]),
]


def glyph(img, sym, x0, y0, scale, star, line):
    """Нарисовать созвездие в квадрате 10×scale от (x0, y0)."""
    stars, edges = GLYPHS[sym][2], GLYPHS[sym][3]
    d = ImageDraw.Draw(img)
    pts = [(x0 + int(x * scale), y0 + int(y * scale)) for x, y in stars]
    for a, b in edges:
        d.line([pts[a], pts[b]], fill=(*line, 255), width=1)
    for (x, y) in pts:
        img.putpixel((x, y), (*star, 255))


def disc_tex(color, sym):
    """Диск: ночной камень, цветная оправа, созвездие белым по центру (32×32 — тоньше линии)."""
    img = Image.new('RGBA', (32, 32))
    base = T.noisy('star_disc_base', [T.hexrgb(h) for h in ('#151b3a', '#1b2347', '#212b55')], cell=4, grain=0.3).resize((32, 32), 0)
    img.paste(base)
    rim = T.hexrgb(COLORS[color])
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - 15.5, y - 15.5)
            if 13.2 <= d < 15.5:
                img.putpixel((x, y), (*T.shade(rim, 0.85 + 0.15 * ((x + y) % 3 == 0)), 255))
            elif 12.4 <= d < 13.2:
                img.putpixel((x, y), (*T.mix(rim, (255, 255, 255), 0.5), 255))
            elif d >= 15.5:
                img.putpixel((x, y), (*T.hexrgb('#2f3b4c'), 255))
    glyph(img, sym, 7, 7, 1.8, (255, 255, 255), T.mix(rim, (200, 220, 255), 0.6))
    return img


def fresco_tex(color, sym, hidden):
    img = T.noisy('star_fresco_base', [T.hexrgb(h) for h in ('#cfc6b0', '#d9d1bc', '#e3dcc9')], cell=4, grain=0.3).resize((32, 32), 0)
    rim = T.hexrgb(COLORS[color])
    for i in range(32):
        for k in (0, 1, 30, 31):
            img.putpixel((i, k), (*rim, 255))
            img.putpixel((k, i), (*rim, 255))
    if hidden:
        r = T.rng_for('fresco_dust')
        for _ in range(26):  # звёздная пыль — ещё не проявилось
            img.putpixel((r.randrange(4, 28), r.randrange(4, 28)), (*T.hexrgb('#b8ad94'), 255))
    else:
        glyph(img, sym, 6, 6, 2.0, T.hexrgb('#fff4c4'), T.hexrgb('#b8862a'))
    return img


def blocks():
    variants = {}
    for col in range(4):
        for sym in range(8):
            name = f'star_disc_{col}_{sym}'
            save_png(disc_tex(col, sym), 'block/' + name)
            model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
                'top': c('block/' + name), 'bottom': c('block/everfrost_bricks'), 'side': c('block/' + name)}})
            variants[f'color={col},symbol={sym}'] = {'model': c('block/' + name)}
    blockstate('star_disc', {'variants': variants})
    item_def('star_disc', c('block/star_disc_3_0'))

    variants = {}
    for col in range(4):
        save_png(fresco_tex(col, 0, True), f'block/star_fresco_{col}_hidden')
        model(f'block/star_fresco_{col}_hidden', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c(f'block/star_fresco_{col}_hidden')}})
        for sym in range(8):
            name = f'star_fresco_{col}_{sym}'
            save_png(fresco_tex(col, sym, False), 'block/' + name)
            model('block/' + name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + name)}})
            variants[f'color={col},hidden=false,symbol={sym}'] = {'model': c('block/' + name)}
            variants[f'color={col},hidden=true,symbol={sym}'] = {'model': c(f'block/star_fresco_{col}_hidden')}
    blockstate('star_fresco', {'variants': variants})
    item_def('star_fresco', c('block/star_fresco_3_4'))

    for solved in (False, True):
        img = T.bricks('star_lock', [T.hexrgb(h) for h in ('#151b3a', '#1b2347', '#212b55')], '#0b0f22')
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                if 4.4 <= d < 5.6:
                    img.putpixel((x, y), (*(T.hexrgb('#fff4c4') if solved else T.hexrgb('#c9a23a')), 255))
        for k, col in enumerate(COLORS):  # четыре цветные звезды по сторонам света
            x, y = ((7, 1), (14, 7), (8, 14), (1, 8))[k]
            img.putpixel((x, y), (*T.hexrgb(col), 255))
            img.putpixel((x + (1 if k in (0, 2) else 0), y + (1 if k in (1, 3) else 0)), (*T.hexrgb(col), 255))
        img.putpixel((7, 7), (255, 255, 255, 255))
        img.putpixel((8, 8), (255, 255, 255, 255) if solved else (*T.hexrgb('#c9a23a'), 255))
        name = 'star_lock' + ('_solved' if solved else '')
        save_png(img, 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/' + name), 'side': c('block/everfrost_bricks'), 'bottom': c('block/everfrost_bricks')}})
    blockstate('star_lock', {'variants': {'solved=false': {'model': c('block/star_lock')}, 'solved=true': {'model': c('block/star_lock_solved')}}})
    item_def('star_lock', c('block/star_lock'))
    immune = [c(n) for n in ('star_disc', 'star_fresco', 'star_lock')]
    append_tag('block', 'minecraft:dragon_immune', immune)
    append_tag('block', 'minecraft:wither_immune', immune)


def lang():
    names = {
        'block.celestial.star_disc': ('Звёздный диск', 'Star Disc'),
        'block.celestial.star_disc.lore1': ('ПКМ — следующее созвездие. Нужное для своего цвета покажет фреска.',
                                            'Use to turn to the next constellation. A fresco shows the right one for its colour.'),
        'block.celestial.star_fresco': ('Звёздная фреска', 'Star Fresco'),
        'block.celestial.star_lock': ('Звёздный замок', 'Star Lock'),
        'block.celestial.star_lock.lore1': ('Сверяет диски с тайной комбинацией обсерватории. За ошибку — стражи из звёздной пыли.',
                                            'Checks the discs against the observatory\'s secret combination. A mistake raises guardians of stardust.'),
        'puzzle.celestial.star_lock.wrong': ('Созвездия не сошлись.', 'The constellations do not align.'),
        'puzzle.celestial.star_lock.solved': ('Звёзды уже сошлись.', 'The stars have already aligned.'),
        'codex.celestial.puzzle.star_lock': ('Звёздный замок', 'Star Lock'),
        'codex.celestial.puzzle.star_lock.hint': ('под куполом обсерватории: найди фрески по цвету оправ и поверни диски. Ошибка зовёт стражей.',
                                                  'beneath an observatory dome: find the frescoes matching the rims and turn the discs. Mistakes summon guardians.'),
    }
    lang_patch(names)


class JavaRandom:
    """java.util.Random / LegacyRandomSource Minecraft — чтобы сценарий знал тайную комбинацию замка."""
    def __init__(self, seed):
        self.seed = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def next(self, bits):
        self.seed = (self.seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        r = self.seed >> (48 - bits)
        return r - (1 << bits) if r >= 1 << (bits - 1) and bits == 32 else r

    def next_int(self, bound):
        if bound & (bound - 1) == 0:
            return (bound * self.next(31)) >> 31
        while True:
            bits = self.next(31)
            val = bits % bound
            if bits - val + (bound - 1) < (1 << 31):
                return val


def as_long(x, y, z):
    return ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF)


def lock_targets(x, y, z):
    """Копия StarLockBlockEntity.target: перестановка 8 созвездий, сид от позиции замка."""
    seed = (as_long(x, y, z) * 0x9E3779B97F4A7C15 + 0x5741524C4F434B) & ((1 << 64) - 1)
    if seed >= 1 << 63:
        seed -= 1 << 64
    r = JavaRandom(seed)
    perm = list(range(8))
    for i in range(7, 0, -1):
        j = r.next_int(i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def scenario():
    import os
    X, Y0, Z = 25000, 150, 25000
    lock = (X + 9, Y0 + 11, Z + 12)
    targets = lock_targets(*lock)
    y = Y0 + 11
    out = ['# QA: Звёздный кодовый замок в обсерватории (генерирует tools/gen_puzzles_c.py; комбинация считается копией Java-ГСЧ)',
           '/gamemode creative', '/effect clear @s', '/gamerule advance_time false', '/time set 6000', '/gamerule spawn_monsters false',
           f'/execute in minecraft:overworld run tp @s {X + 9} {Y0 + 30} {Z + 9}', 'fly', 'wait 80',
           f'/fill {X - 2} {Y0 - 3} {Z - 2} {X + 20} {Y0 - 1} {Z + 20} minecraft:stone',
           f'/fill {X - 2} {Y0} {Z - 2} {X + 20} {Y0 + 22} {Z + 20} minecraft:air',
           f'/place template celestial:observatory/main {X} {Y0} {Z}', 'wait 60', '/kill @e[type=celestial:fallen_guardian]',
           '# F фрески проявились (замок осмотрелся при загрузке)',
           '/say TEST F frescoes_revealed expect=pass,pass',
           f'/execute if block {X + 6} {Y0 + 6} {Z + 3} celestial:star_fresco[hidden=false,symbol={targets[0]}]',
           f'/execute if block {X + 2} {Y0 + 6} {Z + 10} celestial:star_fresco[hidden=false,symbol={targets[3]}]',
           f'/tp @s {X + 9.5} {Y0 + 2} {Z + 9.5} facing {X + 6.5} {Y0 + 6.5} {Z + 3.5}', 'togglehud', 'wait 20', 'shot star_fresco', 'togglehud',
           '/gamemode survival', '/effect give @s minecraft:resistance 600 4 true', '/clear @s',
           f'/tp @s {X + 9.5} {y} {Z + 14.5} facing {X + 9.5} {y} {Z + 12.5}', 'wait 10',
           '# B1 неверная сверка: стражи и блокировка, реликварий заперт',
           '/say TEST B1 wrong_combo expect=pass,pass(no items)',
           f'use {lock[0]} {lock[1]} {lock[2]} up', 'wait 10',
           '/execute if entity @e[type=celestial:fallen_guardian,distance=..10]',
           '/kill @e[type=celestial:fallen_guardian]',
           f'/tp @s {X + 12.5} {y} {Z + 10.5} facing {X + 13.5} {y + 1.5} {Z + 9.5}', 'wait 5',
           f'use {X + 13} {y + 1} {Z + 9} south', 'wait 10', '/execute unless items entity @s container.* *',
           '# B2 повторная сверка сразу: замок ещё «остывает», стражей нет',
           '/say TEST B2 lockout expect=pass(no guardians)',
           f'/tp @s {X + 9.5} {y} {Z + 14.5} facing {X + 9.5} {y} {Z + 12.5}', 'wait 5',
           f'use {lock[0]} {lock[1]} {lock[2]} up', 'wait 10',
           '/execute unless entity @e[type=celestial:fallen_guardian,distance=..10]',
           '# S честно: повернуть диски на созвездия фресок, переждать блокировку, сверить',
           '/say TEST S solve expect=pass,pass(items)']
    for i, x in enumerate((6, 8, 10, 12)):
        start = (i * 3 + 1) % 8
        for _ in range((targets[i] - start) % 8):
            out += [f'use {X + x} {y} {Z + 13} up', 'wait 3']
    out += ['wait 800', f'use {lock[0]} {lock[1]} {lock[2]} up', 'wait 20',
            f'/execute if block {lock[0]} {lock[1]} {lock[2]} celestial:star_lock[solved=true]',
            f'/tp @s {X + 12.5} {y} {Z + 10.5} facing {X + 13.5} {y + 1.5} {Z + 9.5}', 'wait 5',
            f'use {X + 13} {y + 1} {Z + 9} south', 'wait 10', '/execute if items entity @s container.* celestial:rune_of_stars',
            f'/tp @s {X + 9.5} {y + 1.5} {Z + 15.5} facing {X + 9.5} {y} {Z + 11}', 'togglehud', 'wait 10', 'shot star_lock_solved', 'togglehud',
            '/gamemode creative', 'quit']
    with open(os.path.join(os.path.dirname(__file__), 'scenarios', 'puzzle_star_lock.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    return targets


def main():
    blocks()
    lang()
    print('комбинация тестового замка:', scenario())
    print('ok: головоломки C (звёздный замок)')


if __name__ == '__main__':
    main()
