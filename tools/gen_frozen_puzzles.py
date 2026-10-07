"""Загадки Ледяных Чертогов (волна 0.4, шаг 6): залы скользящего льда и Зеркальный лабиринт.

Блоки: ледяная плита пола, гнездо, ледяная колонна, рунная глыба, ледяной колокол (сброс и хранитель зала).
Шаблоны залов `celestial:glacier_hall/hall_1..3` строятся из ASCII-карт; каждая карта проверяется решателем
(`ice_solver.py`) — нерешаемый или слишком короткий расклад роняет генерацию. Решение пишется в
`tools/scenarios/puzzle_ice_solutions.txt` (для сценариев автопилота и подсказок).
"""
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, c, save_png, blockstate, model, item_def, write_json
from gen_story import lang_patch
from gen_structures import Template, reliquary
from ice_solver import Hall, DIR_NAMES
from beam_solver import Maze

ICE = T.pal('#3f86b8', '#4f9ccc', '#66b2dc', '#8fd0ef', '#b4e4f8')
DEEP = T.pal('#1c4a78', '#245a8c', '#2e6aa0', '#3a7db4', '#4b92c8')
FROST = T.hexrgb('#e9fbff')
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- залы (карты проверяет решатель)
# '#' стена, '.' плита, 'o' гнездо, 'G' глыба, 'P' колонна, 'E' вход из преддверия
HALLS = {
    'hall_1': ([
        '#########',
        '#o......#',
        '#...Po..#',
        '#.P.....#',
        '#.G..PG.#',
        '#.......#',
        '#......P#',
        '#..P....#',
        '####E####',
    ], 7),
    'hall_2': ([
        '##########',
        '#...o....#',
        '#..P.G...#',
        '#......P.#',
        '#P...Go.P#',
        '#o.......#',
        '#.G...P.P#',
        '#P.......#',
        '#P.......#',
        '#####E####',
    ], 9),
    'hall_3': ([
        '###########',
        '#....o....#',
        '#.PGP.G.P.#',
        '#P........#',
        '#.G.......#',
        '#.G......o#',
        '#.......oo#',
        '#.......PP#',
        '#....P.P.P#',
        '#..P......#',
        '#####E#####',
    ], 10),
}


def px(img, x, y, col, a=255):
    if 0 <= x < 16 and 0 <= y < 16:
        img.putpixel((x, y), (*col[:3], a))


def tile_tex(name):
    """Полированная ледяная плита: светлый лёд, тёмный шов по краю, блики-полосы."""
    img = T.noisy(name, ICE[1:], cell=4, grain=0.25)
    grout = T.hexrgb('#2f6c98')
    for i in range(16):
        px(img, i, 0, grout)
        px(img, 0, i, grout)
        px(img, i, 1, T.shade(img.getpixel((i, 1)), 1.12))
        px(img, 1, i, T.shade(img.getpixel((1, i)), 1.12))
    for k in range(9):  # две диагональные полосы-блика
        px(img, 3 + k, 12 - k, T.mix(img.getpixel((3 + k, 12 - k)), WHITE, 0.55))
        if k < 5:
            px(img, 9 + k, 14 - k, T.mix(img.getpixel((9 + k, 14 - k)), WHITE, 0.4))
    r = T.rng_for(name + '_specks')
    for _ in range(5):
        px(img, r.randrange(2, 15), r.randrange(2, 15), FROST)
    return img


def nest_tex(lit):
    """Гнездо: плита с вырезанным кольцом-руной; горит, когда занято глыбой."""
    img = tile_tex('glacier_nest')
    ring = T.hexrgb('#e8feff') if lit else T.hexrgb('#5aa2d2')
    edge = T.hexrgb('#6ff0ff') if lit else T.hexrgb('#2b5f8c')
    core = T.hexrgb('#ffffff') if lit else T.hexrgb('#3a77a8')
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if 4.6 <= d < 5.6:
                px(img, x, y, ring)
            elif 5.6 <= d < 6.4 or 3.8 <= d < 4.6:
                px(img, x, y, edge)
            elif lit and d < 3.8:
                px(img, x, y, T.mix(img.getpixel((x, y)), T.hexrgb('#a8f6ff'), 0.6 - d / 10))
    for x, y in ((7, 5), (8, 5), (7, 10), (8, 10), (5, 7), (5, 8), (10, 7), (10, 8), (7, 7), (8, 8), (7, 8), (8, 7)):
        px(img, x, y, core if (x, y) in ((7, 7), (8, 8), (7, 8), (8, 7)) else edge)
    return img


RUNE = [  # снежинка-руна 7×9, '#' — светящаяся черта, '+' — сердцевина
    '...#...',
    '.#.#.#.',
    '..###..',
    '#..+..#',
    '.##+##.',
    '#..+..#',
    '..###..',
    '.#.#.#.',
    '...#...',
]


def rune_side():
    img = T.noisy('glacier_rune', DEEP, cell=3, grain=0.3)
    for i in range(16):  # скос граней: светлый верх/лево, тёмный низ/право
        px(img, i, 0, T.shade(img.getpixel((i, 0)), 1.35))
        px(img, 0, i, T.shade(img.getpixel((0, i)), 1.25))
        px(img, i, 15, T.shade(img.getpixel((i, 15)), 0.7))
        px(img, 15, i, T.shade(img.getpixel((15, i)), 0.75))
    for y, row in enumerate(RUNE):
        for x, ch in enumerate(row):
            if ch == '#':
                px(img, 4 + x, 3 + y, T.hexrgb('#8ff3ff'))
            elif ch == '+':
                px(img, 4 + x, 3 + y, WHITE)
    # мягкий ореол вокруг руны
    for y in range(2, 14):
        for x in range(3, 13):
            col = img.getpixel((x, y))
            if col[:3] not in (T.hexrgb('#8ff3ff'), WHITE):
                near = any(0 <= y - 3 + dy < 9 and 0 <= x - 4 + dx < 7 and RUNE[y - 3 + dy][x - 4 + dx] != '.'
                           for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                if near:
                    px(img, x, y, T.mix(col, T.hexrgb('#4fd8f0'), 0.45))
    return img


def rune_top():
    img = T.noisy('glacier_rune_top', DEEP[1:], cell=3, grain=0.3)
    r = T.rng_for('glacier_rune_frost')
    for _ in range(26):  # иней шапкой
        px(img, r.randrange(16), r.randrange(16), T.mix(FROST, T.hexrgb('#9fd8f0'), r.random() * 0.5))
    for y in range(16):
        for x in range(16):
            d = max(abs(x - 7.5), abs(y - 7.5))
            if 3 <= d < 4:
                px(img, x, y, T.hexrgb('#8ff3ff'))
    return img


def pillar_side():
    img = Image.new('RGBA', (16, 16))
    r = T.rng_for('glacier_pillar')
    for x in range(16):
        edge = abs(x - 7.5) / 7.5
        base = T.mix(T.hexrgb('#9ad8f2'), T.hexrgb('#3a7fb0'), edge ** 1.5)
        for y in range(16):
            col = T.shade(base, 0.94 + r.random() * 0.12)
            if x in (5, 6) and r.random() < 0.85:  # вертикальный блик
                col = T.mix(col, WHITE, 0.5)
            px(img, x, y, col)
    for x in range(16):  # тонкие трещины-прожилки, бесшовно по вертикали (колонна выше блока)
        if x in (3, 11):
            for y in range(16):
                if r.random() < 0.4:
                    px(img, x, y, T.mix(img.getpixel((x, y)), T.hexrgb('#2a5f8a'), 0.5))
    for y in range(16):
        px(img, 0, y, T.hexrgb('#2f5a80'))
        px(img, 15, y, T.hexrgb('#2f5a80'))
    return img


def pillar_top():
    img = T.bricks('glacier_pillar_top', [T.hexrgb(h) for h in ('#5a6c84', '#667a92', '#7489a2')], '#2f3b4c')
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if d < 5.5:
                px(img, x, y, T.mix(T.hexrgb('#b4e4f8'), T.hexrgb('#4f9ccc'), d / 5.5))
            elif d < 6.3:
                px(img, x, y, T.hexrgb('#2f3b4c'))
    return img


def bell_tex():
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            t = y / 15
            col = T.mix(T.hexrgb('#d8f6ff'), T.hexrgb('#3f86b8'), t ** 0.8)
            if x in (3, 4):
                col = T.mix(col, WHITE, 0.45)
            if y in (12, 13):
                col = T.hexrgb('#8ff3ff')
            px(img, x, y, col)
    return img


def box(fr, to, tex, uv=None):
    faces = {}
    for d in ('north', 'south', 'east', 'west', 'up', 'down'):
        faces[d] = {'texture': tex, **({'uv': uv} if uv else {})}
    return {'from': fr, 'to': to, 'faces': faces}


def blocks():
    save_png(tile_tex('glacier_tile'), 'block/glacier_tile')
    save_png(nest_tex(False), 'block/glacier_nest')
    save_png(nest_tex(True), 'block/glacier_nest_lit')
    save_png(rune_side(), 'block/glacier_rune')
    save_png(rune_top(), 'block/glacier_rune_top')
    save_png(pillar_side(), 'block/glacier_pillar')
    save_png(pillar_top(), 'block/glacier_pillar_top')
    save_png(bell_tex(), 'block/ice_bell')

    blockstate('glacier_tile', {'variants': {'': [{'model': c('block/glacier_tile'), 'y': r} for r in (0, 90, 180, 270)]}})
    model('block/glacier_tile', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/glacier_tile')}})
    item_def('glacier_tile', c('block/glacier_tile'))
    for lit in (False, True):
        suffix = '_lit' if lit else ''
        model('block/glacier_nest' + suffix, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/glacier_nest' + suffix), 'side': c('block/glacier_tile'), 'bottom': c('block/glacier_tile')}})
    blockstate('glacier_nest', {'variants': {f'occupied={str(o).lower()}': {'model': c('block/glacier_nest' + ('_lit' if o else ''))}
                                             for o in (False, True)}})
    item_def('glacier_nest', c('block/glacier_nest'))
    model('block/glacier_pillar', {'parent': 'minecraft:block/cube_column', 'textures': {
        'end': c('block/glacier_pillar_top'), 'side': c('block/glacier_pillar')}})
    blockstate('glacier_pillar', {'variants': {'': {'model': c('block/glacier_pillar')}}})
    item_def('glacier_pillar', c('block/glacier_pillar'))
    model('block/glacier_rune', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/glacier_rune_top'), 'side': c('block/glacier_rune'), 'bottom': c('block/glacier_rune_top')}})
    blockstate('glacier_rune', {'variants': {'': {'model': c('block/glacier_rune')}}})
    item_def('glacier_rune', c('block/glacier_rune'))

    frame, bell = c('block/frost_stone_bricks'), c('block/ice_bell')
    model('block/ice_bell', {'parent': 'minecraft:block/block', 'textures': {'particle': bell, 'frame': frame, 'bell': bell}, 'elements': [
        box([1, 0, 4], [15, 2, 12], '#frame'),
        box([1, 2, 7], [3, 15, 9], '#frame'), box([13, 2, 7], [15, 15, 9], '#frame'),
        box([3, 13, 7], [13, 15, 9], '#frame'),
        box([7, 11, 7], [9, 13, 9], '#bell'),
        box([5.5, 6, 5.5], [10.5, 11, 10.5], '#bell'),
        box([4.5, 4, 4.5], [11.5, 6, 11.5], '#bell', uv=[0, 10, 16, 16]),
        box([7.5, 3, 7.5], [8.5, 4, 8.5], '#bell'),
    ]})
    blockstate('ice_bell', {'variants': {f'facing={f}': {'model': c('block/ice_bell'), 'y': y}
                                         for f, y in (('north', 0), ('east', 90), ('south', 180), ('west', 270))}})
    item_def('ice_bell', c('block/ice_bell'))
    append_tag('block', 'minecraft:dragon_immune', [c(n) for n in ('glacier_tile', 'glacier_nest', 'glacier_pillar', 'glacier_rune', 'ice_bell')])
    append_tag('block', 'minecraft:wither_immune', [c(n) for n in ('glacier_tile', 'glacier_nest', 'glacier_pillar', 'glacier_rune', 'ice_bell')])


# ---------------------------------------------------------------- шаблоны залов
BRICKS = c('frost_stone_bricks')


def hall_template(name, rows):
    """Зал по карте + преддверие с колоколом и запечатанной нишей Реликвария.

    Пол зала на y=0, глыбы и проходы на y=1, потолок на y=5. Преддверие примыкает к стороне входа 'E' (низ карты).
    """
    w, h = len(rows[0]), len(rows)
    depth = h + 4
    t = Template(w, 7, depth)
    ex = rows[-1].index('E')
    t.fill(0, 0, 0, w - 1, 6, depth - 1, 'minecraft:air')  # явный воздух: рельеф и лёд не затекают внутрь зала
    t.fill(0, 0, 0, w - 1, 0, depth - 1, BRICKS)
    t.fill(0, 6, 0, w - 1, 6, depth - 1, BRICKS)
    for z, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '#':
                t.fill(x, 0, z, x, 5, z, BRICKS)
                continue
            if ch == 'E':
                t.set(x, 0, z, BRICKS)
                t.fill(x, 3, z, x, 5, z, BRICKS)
                continue
            t.set(x, 0, z, c('glacier_nest') if ch in 'oQ' else c('glacier_tile'), **({'occupied': ch == 'Q'} if ch in 'oQ' else {}))
            t.set(x, 5, z, c('frost_stone_bricks'))
            if ch in 'GQ':
                t.set(x, 1, z, c('glacier_rune'))
            elif ch == 'P':
                t.fill(x, 1, z, x, 4, z, c('glacier_pillar'))
    # потолочные кристаллы сияния — свет без факелов
    for z in range(2, h - 2, 3):
        for x in range(2, w - 2, 3):
            if rows[z][x] != '#' and rows[z][x] != 'P':
                t.set(x, 4, z, c('aurora_crystal'), facing='down')
    # преддверие за стеной со входом 'E' (строка h-1): стены, вход снаружи посередине дальней стены
    z0, z1 = h - 1, depth - 1
    t.walls(0, 1, z0, w - 1, 5, z1, BRICKS)
    t.fill(1, 5, z0 + 1, w - 2, 5, z1 - 1, BRICKS)
    t.fill(ex, 1, z0, ex, 2, z0, 'minecraft:air')
    t.fill(ex, 1, z1, ex, 2, z1, 'minecraft:air')
    t.set(ex + 2, 1, z0 + 1, c('ice_bell'), facing='north')  # колокол в 2 клетках от пола зала — так он находит свой зал
    t.set(ex - 2, 4, z0 + 2, c('aurora_crystal'), facing='down')
    t.set(ex + 2, 4, z0 + 3, c('aurora_crystal'), facing='down')
    # ниша Реликвария в углу преддверия за печатью
    rx, rz = 1, z1 - 1
    reliquary(t, rx, 1, rz, 'celestial:chests/glacier_hall')
    for x, y, z in ((rx, 1, rz - 1), (rx + 1, 1, rz - 1), (rx + 1, 1, rz), (rx, 2, rz - 1), (rx + 1, 2, rz - 1), (rx + 1, 2, rz), (rx, 2, rz)):
        t.set(x, y, z, c('sealed_door'))
    return t.save('glacier_hall/' + name)


def solutions():
    lines = ['# Решения залов скользящего льда (генерирует tools/gen_frozen_puzzles.py, не править руками).',
             '# Координаты — в системе шаблона: x — столбец карты, z — строка карты, глыбы на y=1.',
             '# ход: глыба_x глыба_z направление игрок_x игрок_z']
    for name, (rows, min_moves) in HALLS.items():
        sol = Hall(rows).solve()
        assert sol is not None, f'{name}: расклад нерешаем'
        assert len(sol) >= min_moves, f'{name}: решение слишком короткое ({len(sol)} < {min_moves})'
        lines.append(f'[{name}] {len(sol)}')
        for (gx, gz), d, (sx, sz) in sol:
            lines.append(f'{gx} {gz} {DIR_NAMES[d]} {sx} {sz}')
        hall_template(name, rows)
    path = os.path.join(os.path.dirname(__file__), 'scenarios', 'puzzle_ice_solutions.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


OPPOSITE = {'east': 'west', 'west': 'east', 'north': 'south', 'south': 'north'}


def scenario():
    """Сценарий автопилота: обходы (все должны провалиться) и честное решение каждого зала по решателю."""
    X0, Y0, Z0 = 21000, 150, 21000
    out = ['# QA: залы скользящего льда (генерирует tools/gen_frozen_puzzles.py). Честно: решения решателя; обход: стройка, поршень, стопор, ломание',
           '/gamemode creative', '/effect clear @s', '/gamerule advance_time false', '/time set 6000', '/gamerule spawn_monsters false',
           f'/execute in minecraft:overworld run tp @s {X0} {Y0 + 20} {Z0}', 'fly', 'wait 100',
           *[f'/fill {X0 - 5 + i * 45} {Y0 - 3} {Z0 - 5} {X0 + 39 + i * 45} {Y0 - 1} {Z0 + 25} minecraft:stone' for i in range(3)],
           *[f'/fill {X0 - 5 + i * 45} {Y0} {Z0 - 5} {X0 + 39 + i * 45} {Y0 + 12} {Z0 + 25} minecraft:air' for i in range(3)]]
    for i, name in enumerate(HALLS):
        out.append(f'/place template celestial:glacier_hall/{name} {X0 + i * 40} {Y0} {Z0}')
    out += ['wait 60', '/clear @s', '/effect give @s minecraft:resistance 900 4 true', '/effect give @s minecraft:saturation 900 1 true']
    rows = HALLS['hall_1'][0]
    sol = Hall(rows).solve()
    glaciers = sorted(Hall(rows).glaciers)
    gx, gz = glaciers[0]
    X, Z = X0, Z0
    y = Y0 + 1
    out += [f'tp_note hall_1 glaciers {glaciers}',
            '# B1 своя стройка в зале: камень не ставится',
            '/say TEST B1 no_build_in_hall expect=pass',
            '/gamemode survival', '/give @s minecraft:stone 4',
            f'/tp @s {X + 1.5} {y} {Z + 7.5}', 'wait 10',
            f'use {X + 1} {Y0} {Z + 6} up', 'wait 10',
            f'/execute unless block {X + 1} {y} {Z + 6} minecraft:stone', '/clear @s',
            '# B2 сломать глыбу в выживании: остаётся',
            '/say TEST B2 break_glacier expect=pass',
            f'/tp @s {X + gx - 0.5} {y} {Z + gz + 0.5} facing {X + gx + 0.5} {y + 0.5} {Z + gz + 0.5}', 'wait 10',
            'hold attack 80',
            f'/execute if block {X + gx} {y} {Z + gz} celestial:glacier_rune',
            '# B3 поршень толкает глыбу: не двигается',
            '/say TEST B3 piston expect=pass',
            '/gamemode creative',
            f'/setblock {X + gx} {y} {Z + gz + 1} minecraft:piston[facing=north]',
            f'/setblock {X + gx} {y} {Z + gz + 2} minecraft:redstone_block', 'wait 10',
            f'/execute if block {X + gx} {y} {Z + gz} celestial:glacier_rune',
            f'/setblock {X + gx} {y} {Z + gz + 2} minecraft:air', f'/setblock {X + gx} {y} {Z + gz + 1} minecraft:air',
            'wait 5', '/gamemode survival',
            '# B4 толчок не с той стороны (по диагонали): глыба стоит',
            '/say TEST B4 push_from_diagonal expect=pass',
            f'/tp @s {X + gx - 0.5} {y} {Z + gz - 0.5}', 'wait 5',
            f'use {X + gx} {y} {Z + gz} west', 'wait 30',
            f'/execute if block {X + gx} {y} {Z + gz} celestial:glacier_rune']
    # B5 стопор: чужой камень на пути первого хода решения — глыба его сметает и встаёт туда же, куда и без него
    (g0x, g0z), d0, (s0x, s0z) = sol[0]
    hall = Hall(rows)
    dest = hall.slide((g0x, g0z), d0, hall.glaciers)
    mid = (g0x + d0[0], g0z + d0[1])
    out += ['# B5 свой блок-стопор на пути: глыба сметает его',
            '/say TEST B5 foreign_stopper expect=pass,pass',
            '/gamemode creative', f'/setblock {X + mid[0]} {y} {Z + mid[1]} minecraft:stone', '/gamemode survival',
            f'/tp @s {X + s0x + 0.5} {y} {Z + s0z + 0.5}', 'wait 5',
            f'use {X + g0x} {y} {Z + g0z} {OPPOSITE[DIR_NAMES[d0]]}', 'wait 40',
            f'/execute if block {X + dest[0]} {y} {Z + dest[1]} celestial:glacier_rune',
            f'/execute unless block {X + mid[0]} {y} {Z + mid[1]} minecraft:stone',
            'shot ice_after_sweep', '/kill @e[type=item]', '/clear @s',
            '# R2 колокол с блоком в руке всё равно звонит (охрана зоны не мешает), блок не ставится',
            '/give @s minecraft:stone 1',
            '# R колокол возвращает расклад',
            '/say TEST R bell_reset expect=pass',
            f'/tp @s {X + rows[-1].index("E") + 0.5} {y} {Z + len(rows) + 1.5}', 'wait 5',
            f'use {X + rows[-1].index("E") + 2} {y} {Z + len(rows)} north', 'wait 10',
            f'/execute if block {X + g0x} {y} {Z + g0z} celestial:glacier_rune', '/clear @s',
            '# B6 реликварий заперт до решения',
            '/say TEST B6 reliquary_sealed expect=pass(no items)',
            f'/tp @s {X + 3.5} {y} {Z + len(rows) + 2.5}', 'wait 5',
            f'use {X + 1} {y} {Z + len(rows) + 2} east', 'wait 10',
            '/execute unless items entity @s container.* *']
    for i, name in enumerate(HALLS):
        rows = HALLS[name][0]
        X = X0 + i * 40
        h = len(rows)
        out += [f'# S{i + 1} честное решение {name}', f'/say TEST S{i + 1} solve_{name} expect=pass,pass(items)']
        if i == 0:
            ex = rows[-1].index('E')
            out += [f'/tp @s {X + ex + 0.5} {y} {Z + h - 0.5} facing {X + ex + 0.5} {y} {Z + 1}', 'togglehud', 'wait 10', 'shot ice_hall_start', 'togglehud']
        for k, ((gx, gz), d, (sx, sz)) in enumerate(Hall(rows).solve()):
            out += [f'/tp @s {X + sx + 0.5} {y} {Z + sz + 0.5} facing {X + gx + 0.5 + d[0] * 3} {y + 0.3} {Z + gz + 0.5 + d[1] * 3}', 'wait 4',
                    f'use {X + gx} {y} {Z + gz} {OPPOSITE[DIR_NAMES[d]]}', 'wait 30']
            if i == 0 and k == 0:
                out.insert(-1, 'togglehud')
                out.insert(-1, 'wait 5')
                out.insert(-1, 'shot ice_sliding')
                out.insert(-1, 'togglehud')
        out += ['wait 20', f'/execute unless block {X + 2} {y} {Z + h + 1} celestial:sealed_door',
                f'/tp @s {X + 3.5} {y} {Z + h + 2.5}', 'wait 5', f'use {X + 1} {y} {Z + h + 2} east', 'wait 10',
                '/execute if items entity @s container.* *', '/clear @s']
        if i == 0:
            ex = rows[-1].index('E')
            out += [f'/tp @s {X + ex + 0.5} {y} {Z + h - 0.5} facing {X + ex + 0.5} {y} {Z + 1}', 'togglehud', 'wait 10', 'shot ice_hall_solved', 'togglehud']
    out += ['/gamemode creative', 'quit']
    out = [l for l in out if not l.startswith('tp_note')]
    with open(os.path.join(os.path.dirname(__file__), 'scenarios', 'puzzle_ice.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')


def loot():
    write_json(os.path.join(ASSETS.replace('assets', 'data'), 'loot_table/chests/glacier_hall.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/glacier_hall'), 'pools': [
            {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('frost_steel_ingot'),
                                      'functions': [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 2, 'max': 4}}]}]},
            {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('aurora_crystal'),
                                      'functions': [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 2, 'max': 5}}]}]},
            {'rolls': {'type': 'minecraft:uniform', 'min': 1, 'max': 2}, 'entries': [
                {'type': 'minecraft:item', 'name': c('star_fragment'), 'weight': 3},
                {'type': 'minecraft:item', 'name': c('starlight_flask'), 'weight': 2},
                {'type': 'minecraft:item', 'name': 'minecraft:diamond', 'weight': 1}]},
        ]})


def lang():
    lang_patch({
        'block.celestial.glacier_tile': ('Ледяная плита', 'Glacier Tile'),
        'block.celestial.glacier_nest': ('Ледяное гнездо', 'Glacier Nest'),
        'block.celestial.glacier_nest.lore1': ('Загорается, когда на нём стоит рунная глыба.', 'Lights up when a rune glacier rests on it.'),
        'block.celestial.glacier_pillar': ('Ледяная колонна', 'Glacier Pillar'),
        'block.celestial.glacier_rune': ('Рунная глыба', 'Rune Glacier'),
        'block.celestial.glacier_rune.lore1': ('Встань вплотную и толкни (ПКМ) — заскользит до преграды.',
                                               'Stand right next to it and push (use) — it slides until it hits something.'),
        'block.celestial.ice_bell': ('Ледяной колокол', 'Ice Bell'),
        'block.celestial.ice_bell.lore1': ('Звон возвращает глыбы зала на прежние места.', 'Its chime returns the hall\'s glaciers to where they began.'),
        'puzzle.celestial.zone.no_build': ('Лёд святыни не принимает чужих камней', 'The sanctum\'s ice rejects foreign stones'),
        'puzzle.celestial.glacier.stand': ('Встань вплотную к глыбе с противоположной стороны', 'Stand right behind the glacier to push it'),
        'puzzle.celestial.glacier.reset': ('Колокол звенит — глыбы возвращаются на места', 'The bell rings — the glaciers return to their places'),
        'puzzle.celestial.glacier.solved': ('Зал уже покорён', 'This hall is already solved'),
    })


# ================================================================ Зеркальный лабиринт
# Карта проверяется beam_solver.Maze.check(): решение единственно по существенным зеркалам, старт не решён,
# к каждому зеркалу, которое надо повернуть, можно подойти. Зеркала, призма и фильтры вмурованы в стены из
# вечного льда (луч их пробивает, игрок нет) — проходы лабиринта они не перекрывают.
MAZE = [
    '###############',
    '#...~.........#',
    'X./~~.~.~~~.~.#',
    '#.....~.......#',
    '#.~.~./.~~~~~.#',
    '#.~...~.~...~.#',
    '#./~\\.~.~.~.\\.#',
    '#.g.....~.~./.#',
    '#~~.~r/~~.~~~.#',
    'S...*...../...#',
    '#.~.~~~.~.~.~~#',
    '#.../.../.....#',
    '#./~~.~.~.\\./.#',
    'Z.....~.\\.....#',
    '#######E####Y##',
]
MAZE_MIN_TURNS = 6
LOCK_DX = 2  # замок сбоку от прохода, чтобы не перегораживать его


def glass_tex(name, base, alpha, frost=True, rim=0.55, rim_alpha=235):
    """Полупрозрачный лёд: оттенок, морозные прожилки и рамка инея по краю (rim — насколько она белая)."""
    r = T.rng_for(name)
    img = Image.new('RGBA', (16, 16))
    col = T.hexrgb(base)
    nz = T.value_noise(r, 16, 4)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            c_ = T.mix(col, WHITE, rim) if edge else T.shade(col, 0.88 + nz[y][x] * 0.2)
            img.putpixel((x, y), (*c_, rim_alpha if edge else alpha + int(nz[y][x] * 40)))
    if frost:
        for _ in range(2):  # длинные трещины инея, бесшовно переходят через край тайла
            x, y = r.randrange(16), r.randrange(16)
            dx = r.choice((-1, 1))
            for _ in range(r.randint(10, 15)):
                px(img, x % 16, y % 16, T.mix(col, WHITE, 0.6), min(255, alpha + 70))
                if r.random() < 0.6:
                    x += dx
                y += 1
    return img


def ancient_base():
    img = T.bricks('ancient_mirror_base', [T.hexrgb(h) for h in ('#5a6c84', '#667a92', '#7489a2')], '#2f3b4c')
    for x in range(3, 13):
        px(img, x, 7, T.hexrgb('#8ff3ff'))
    for x in (3, 12):
        for y in range(5, 10):
            px(img, x, y, T.hexrgb('#8ff3ff'))
    return img


def mirror_pane():
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            t = (x + y) / 30
            c_ = T.mix(T.hexrgb('#f4fbff'), T.hexrgb('#8fb8d8'), abs(0.5 - t) * 1.6)
            edge = x in (0, 15) or y in (0, 15)
            img.putpixel((x, y), (*(T.hexrgb('#b4e4f8') if edge else c_), 255 if edge else 225))
    for k in range(5):
        px(img, 3 + k, 11 - k, WHITE)
        px(img, 9 + k // 2, 14 - k, T.mix(T.hexrgb('#f4fbff'), WHITE, 0.5))
    return img


def gem_tex(color, lit):
    img = Image.new('RGBA', (16, 16))
    base = T.hexrgb(color)
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5 / 10.6
            c_ = T.mix(T.mix(base, WHITE, 0.6), base, d) if lit else T.mix(T.shade(base, 0.35), T.hexrgb('#1c2430'), d)
            img.putpixel((x, y), (*c_, 255))
    return img


def maze_blocks():
    save_png(glass_tex('rime_ice', '#8ccaec', 105, rim=0.18, rim_alpha=150), 'block/rime_ice')
    model('block/rime_ice', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/rime_ice')}})
    blockstate('rime_ice', {'variants': {'': {'model': c('block/rime_ice')}}})
    item_def('rime_ice', c('block/rime_ice'))
    from gen_assets import self_drop
    self_drop('rime_ice')
    append_tag('block', 'minecraft:mineable/pickaxe', [c('rime_ice')])

    save_png(ancient_base(), 'block/ancient_mirror_base')
    save_png(mirror_pane(), 'block/ancient_mirror')
    model('block/ancient_mirror', {'textures': {'mirror': c('block/ancient_mirror'), 'base': c('block/ancient_mirror_base'),
                                                'particle': c('block/ancient_mirror')}, 'elements': [
        {'from': [0, 0, 0], 'to': [16, 3, 16], 'faces': {d: {'texture': '#base'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
        {'from': [7.25, 3, 0], 'to': [8.75, 16, 16], 'rotation': {'origin': [8, 8, 8], 'axis': 'y', 'angle': 45, 'rescale': True},
         'faces': {d: {'texture': '#mirror', 'uv': [0, 0, 16, 16] if d in ('east', 'west') else [7, 0, 9, 16]}
                   for d in ('east', 'west', 'north', 'south', 'up')}}]})
    blockstate('ancient_mirror', {'variants': {'flipped=false': {'model': c('block/ancient_mirror')},
                                               'flipped=true': {'model': c('block/ancient_mirror'), 'y': 90}}})
    item_def('ancient_mirror', c('block/ancient_mirror'))

    prism = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            hue = (x - y + 16) / 32
            rgb = T.mix(T.mix((255, 120, 120), (120, 255, 150), min(1, hue * 2)), (120, 170, 255), max(0, hue * 2 - 1))
            edge = x in (0, 15) or y in (0, 15)
            prism.putpixel((x, y), (*(T.hexrgb('#e9fbff') if edge else T.mix(rgb, WHITE, 0.35)), 240 if edge else 190))
    save_png(prism, 'block/ancient_prism')
    for name, color in (('ancient_prism', None), ('ancient_red_filter', '#ff6a5a'), ('ancient_green_filter', '#6cff8a'),
                        ('ancient_blue_filter', '#5aa8ff')):
        if color:
            save_png(glass_tex(name, color, 160), 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + name)}})
        blockstate(name, {'variants': {'': {'model': c('block/' + name)}}})
        item_def(name, c('block/' + name))

    # Замок трёх лучей: постамент + три самоцвета (multipart по состояниям) + венец при решении
    lock_top = T.noisy('beam_lock_top', ICE[1:], cell=4, grain=0.25)
    for i in range(16):
        px(lock_top, i, 0, T.hexrgb('#2f3b4c')); px(lock_top, i, 15, T.hexrgb('#2f3b4c'))
        px(lock_top, 0, i, T.hexrgb('#2f3b4c')); px(lock_top, 15, i, T.hexrgb('#2f3b4c'))
    save_png(lock_top, 'block/beam_lock_top')
    bricks = c('block/frost_stone_bricks')
    model('block/beam_lock', {'parent': 'minecraft:block/block', 'textures': {'particle': bricks, 'b': bricks, 't': c('block/beam_lock_top')},
                              'elements': [box([1, 0, 1], [15, 3, 15], '#b'), box([3, 3, 3], [13, 10, 13], '#b'),
                                           {'from': [2, 10, 2], 'to': [14, 12, 14], 'faces': {
                                               **{d: {'texture': '#b'} for d in ('north', 'south', 'east', 'west', 'down')},
                                               'up': {'texture': '#t'}}}]})
    parts = [{'apply': {'model': c('block/beam_lock')}}]
    for (name, color), x0 in zip((('red', '#ff4a3a'), ('green', '#4aff6a'), ('blue', '#4a90ff')), (3, 6.5, 10)):
        for lit in (False, True):
            tex = f'beam_lock_{name}' + ('_on' if lit else '')
            save_png(gem_tex(color, lit), 'block/' + tex)
            model('block/' + tex, {'parent': 'minecraft:block/block', 'textures': {'particle': c('block/' + tex), 'g': c('block/' + tex)},
                                   'elements': [box([x0, 12, 6.5], [x0 + 3, 14.5, 9.5], '#g')]})
            parts.append({'when': {name: str(lit).lower()}, 'apply': {'model': c('block/' + tex)}})
    save_png(gem_tex('#e9fbff', True), 'block/beam_lock_halo')
    model('block/beam_lock_halo', {'parent': 'minecraft:block/block', 'textures': {'particle': c('block/beam_lock_halo'), 'h': c('block/beam_lock_halo')},
                                   'elements': [box([6.5, 15.5, 6.5], [9.5, 16, 9.5], '#h'), box([4, 14.5, 7.5], [12, 15, 8.5], '#h')]})
    parts.append({'when': {'solved': 'true'}, 'apply': {'model': c('block/beam_lock_halo')}})
    blockstate('beam_lock', {'multipart': parts})
    item_def('beam_lock', c('block/beam_lock'))
    immune = [c(n) for n in ('ancient_mirror', 'ancient_prism', 'ancient_red_filter', 'ancient_green_filter', 'ancient_blue_filter', 'beam_lock')]
    append_tag('block', 'minecraft:dragon_immune', immune)
    append_tag('block', 'minecraft:wither_immune', immune)


MAZE_BLOCKS = {'/': ('ancient_mirror', {'flipped': False}), '\\': ('ancient_mirror', {'flipped': True}), '*': ('ancient_prism', {}),
               'r': ('ancient_red_filter', {}), 'g': ('ancient_green_filter', {}), 'b': ('ancient_blue_filter', {})}
RECEIVERS = {'X': 'red', 'Y': 'green', 'Z': 'blue'}


def maze_template():
    """Лабиринт 15×15 (пол y=0, стены y=1..3, потолок из вечного льда y=4) + преддверие с Замком и нишей Реликвария."""
    size = len(MAZE)
    depth = size + 5
    t = Template(size, 6, depth)
    t.fill(0, 0, 0, size - 1, 5, depth - 1, 'minecraft:air')
    for z, row in enumerate(MAZE):
        for x, ch in enumerate(row):
            border = ch in '#SXYZE'
            t.set(x, 0, z, BRICKS if border else c('glacier_tile'))
            if ch == '#':
                t.fill(x, 1, z, x, 4, z, BRICKS)
            elif ch == 'S':
                facing = 'east' if x == 0 else 'west' if x == size - 1 else 'south' if z == 0 else 'north'
                t.set(x, 0, z, 'minecraft:redstone_block')  # родной фонарь горит всегда: сигнал из-под пола
                t.set(x, 1, z, c('beam_lantern'), facing=facing, active=True, sealed=True)
                t.fill(x, 2, z, x, 4, z, BRICKS)
            elif ch in RECEIVERS:
                t.set(x, 1, z, c('light_receiver'), color=RECEIVERS[ch], powered=False, sealed=True)
                t.fill(x, 2, z, x, 4, z, BRICKS)
            elif ch == 'E':
                t.fill(x, 3, z, x, 4, z, BRICKS)
            elif ch == '~':
                t.fill(x, 1, z, x, 3, z, c('rime_ice'))
                t.set(x, 4, z, c('rime_ice'))
            elif ch in MAZE_BLOCKS:
                block, props = MAZE_BLOCKS[ch]
                t.set(x, 1, z, c(block), **props)
                t.fill(x, 2, z, x, 3, z, c('rime_ice'))
                t.set(x, 4, z, c('rime_ice'))
            else:
                t.set(x, 4, z, c('rime_ice'))
    for x, z in ((3, 3), (11, 3), (7, 7), (3, 11), (11, 11)):  # кристаллы сияния под ледяным потолком
        if MAZE[z][x] == '.':
            t.set(x, 3, z, c('aurora_crystal'), facing='down')
    ex = MAZE[-1].index('E')
    z0, z1 = size - 1, depth - 1
    t.fill(0, 0, size, size - 1, 0, z1, BRICKS)
    t.walls(0, 1, size, size - 1, 4, z1, BRICKS)
    t.fill(1, 4, size, size - 2, 4, z1 - 1, BRICKS)
    t.fill(ex, 1, z1, ex, 2, z1, 'minecraft:air')
    t.fill(ex, 1, size, ex, 2, size, 'minecraft:air')  # проход из лабиринта в преддверие
    t.set(ex + LOCK_DX, 1, size + 1, c('beam_lock'))
    t.set(ex - 3, 3, size + 2, c('aurora_crystal'), facing='down')
    t.set(ex + 3, 3, size + 2, c('aurora_crystal'), facing='down')
    rx, rz = 1, z1 - 1
    reliquary(t, rx, 1, rz, 'celestial:chests/mirror_maze')
    for x, y, z in ((rx, 1, rz - 1), (rx + 1, 1, rz - 1), (rx + 1, 1, rz), (rx, 2, rz - 1), (rx + 1, 2, rz - 1), (rx + 1, 2, rz), (rx, 2, rz)):
        t.set(x, y, z, c('sealed_door'))
    return t.save('mirror_maze/main')


FACE = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}


def maze_scenario(best, turns):
    X, Y0, Z = 21000, 150, 21100
    y = Y0 + 1
    m = Maze(MAZE)
    reach = m.reachable()
    size = len(MAZE)
    ex = MAZE[-1].index('E')
    lock = (X + ex + LOCK_DX, y, Z + size + 1)
    first = turns[0]
    out = ['# QA: Зеркальный лабиринт (генерирует tools/gen_frozen_puzzles.py). Обходы: свой фонарь, своё зеркало, ломание, два цвета из трёх',
           '/gamemode creative', '/effect clear @s', '/gamerule advance_time false', '/time set 6000', '/gamerule spawn_monsters false',
           f'/execute in minecraft:overworld run tp @s {X} {Y0 + 20} {Z}', 'fly', 'wait 100',
           f'/fill {X - 3} {Y0 - 2} {Z - 3} {X + 18} {Y0 - 1} {Z + 23} minecraft:stone',
           f'/fill {X - 3} {Y0} {Z - 3} {X + 18} {Y0 + 8} {Z + 23} minecraft:air',
           f'/place template celestial:mirror_maze/main {X} {Y0} {Z}', 'wait 80', '/clear @s',
           '/effect give @s minecraft:resistance 900 4 true', '/effect give @s minecraft:night_vision 900 0 true',
           f'/tp @s {X + 7.5} {Y0 + 14} {Z + 7.5} 0 90', 'togglehud', 'wait 40', 'shot maze_start', 'togglehud',
           '# B1 свой фонарь светит прямо в родной красный приёмник: замок не горит',
           '/say TEST B1 own_lantern expect=pass']
    rx, rz = next((x, z) for z, row in enumerate(MAZE) for x, ch in enumerate(row) if ch == 'X')
    inward = (1, 0) if rx == 0 else (-1, 0) if rx == size - 1 else (0, 1) if rz == 0 else (0, -1)
    lx, lz = rx + inward[0], rz + inward[1]
    toward = {(1, 0): 'west', (-1, 0): 'east', (0, 1): 'north', (0, -1): 'south'}[inward]
    out += [f'/setblock {X + lx} {Y0 + 2} {Z + lz} minecraft:air',
            f'/setblock {X + lx} {Y0 + 1} {Z + lz} celestial:beam_lantern[facing={toward}]',
            f'/setblock {X + lx} {Y0 + 2} {Z + lz} minecraft:redstone_block', 'wait 40',
            f'/execute if block {lock[0]} {lock[1]} {lock[2]} celestial:beam_lock[red=false]',
            f'/setblock {X + lx} {Y0 + 2} {Z + lz} minecraft:air', f'/setblock {X + lx} {Y0 + 1} {Z + lz} minecraft:air']
    sx, sz = next(p for p in sorted(reach) if MAZE[p[1]][p[0]] == '.')
    out += ['# B2 своё зеркало в лабиринте (выживание): не ставится',
            '/say TEST B2 own_mirror expect=pass',
            '/gamemode survival', '/give @s celestial:beam_mirror 1',
            f'/tp @s {X + sx + 0.5} {y} {Z + sz + 0.5}', 'wait 5',
            f'use {X + sx} {Y0} {Z + sz} up', 'wait 10',
            f'/execute unless block {X + sx} {y} {Z + sz} celestial:beam_mirror', '/clear @s']
    adj = next((first[0] + dx, first[1] + dz) for dx, dz in FACE if (first[0] + dx, first[1] + dz) in reach)
    out += ['# B3 сломать древнее зеркало и стену вечного льда (выживание): стоят',
            '/say TEST B3 break_mirror_and_wall expect=pass,pass',
            f'/tp @s {X + adj[0] + 0.5} {y} {Z + adj[1] + 0.5} facing {X + first[0] + 0.5} {y + 0.5} {Z + first[1] + 0.5}', 'wait 10',
            'hold attack 80', f'/execute if block {X + first[0]} {y} {Z + first[1]} celestial:ancient_mirror',
            f'/tp @s {X + adj[0] + 0.5} {y} {Z + adj[1] + 0.5} facing {X + first[0] + 0.5} {y + 1.5} {Z + first[1] + 0.5}', 'wait 10',
            'hold attack 120', f'/execute if block {X + first[0]} {y + 1} {Z + first[1]} celestial:rime_ice',
            '# B4 реликварий заперт до решения',
            '/say TEST B4 reliquary_sealed expect=pass(no items)',
            f'/tp @s {X + 3.5} {y} {Z + size + 3.5}', 'wait 5', f'use {X + 1} {y} {Z + size + 3} east', 'wait 10',
            '/execute unless items entity @s container.* *',
            '# F замок дарит камертон',
            '/say TEST F lock_gives_fork expect=pass',
            f'/tp @s {X + ex + 0.5} {y} {Z + size + 2.5}', 'wait 5', f'use {lock[0]} {lock[1]} {lock[2]} south', 'wait 10',
            '/execute if items entity @s container.* celestial:tuning_fork']
    # B5: все повороты, кроме последнего — двух цветов мало (если последний поворот нужен одному цвету)
    out += ['# S честное решение: Камертоном повернуть нужные зеркала (по решателю)', '/say TEST S solve expect=pass,pass,pass(items)']
    for k, (mx, mz) in enumerate(turns):
        sxz = next((mx + dx, mz + dz) for dx, dz in FACE if (mx + dx, mz + dz) in reach)
        face = FACE[(sxz[0] - mx, sxz[1] - mz)]
        out += [f'/tp @s {X + sxz[0] + 0.5} {y} {Z + sxz[1] + 0.5} facing {X + mx + 0.5} {y + 0.5} {Z + mz + 0.5}', 'wait 4',
                f'use {X + mx} {y} {Z + mz} {face}', 'wait 6']
        if k == len(turns) - 2:
            out += ['wait 30', '/say TEST B5 not_all_colors expect=pass(lock unsolved)',
                    f'/execute if block {lock[0]} {lock[1]} {lock[2]} celestial:beam_lock[solved=false]']
    out += ['wait 40', f'/execute if block {lock[0]} {lock[1]} {lock[2]} celestial:beam_lock[solved=true]',
            f'/execute unless block {X + 2} {y} {Z + depth_of_maze() - 3} celestial:sealed_door',
            f'/tp @s {X + 3.5} {y} {Z + size + 3.5}', 'wait 5', f'use {X + 1} {y} {Z + size + 3} east', 'wait 10',
            '/execute if items entity @s container.* celestial:frost_steel_ingot',
            '/gamemode creative', 'fly',
            f'/tp @s {X + 7.5} {Y0 + 14} {Z + 7.5} 0 90', 'togglehud', 'wait 30', 'shot maze_solved', 'togglehud',
            *inside_shot(X, y, Z, reach),
            f'/tp @s {X + ex + 0.5} {y + 0.5} {Z + size + 3.5} facing {lock[0] + 0.5} {y + 0.5} {lock[2] + 0.5}', 'togglehud', 'wait 10',
            'shot maze_lock', 'togglehud', '/gamemode creative', 'quit']
    with open(os.path.join(os.path.dirname(__file__), 'scenarios', 'puzzle_mirror.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')


def inside_shot(X, y, Z, reach):
    """Кадр изнутри: из комнаты рядом с призмой вдоль луча."""
    m = Maze(MAZE)
    px_, pz_ = next((x, z) for z, row in enumerate(MAZE) for x, ch in enumerate(row) if ch == '*')
    stand = min(reach, key=lambda p: abs(p[0] - px_) + abs(p[1] - pz_) + (0 if p[1] != pz_ else 3))
    return [f'/tp @s {X + stand[0] + 0.5} {y} {Z + stand[1] + 0.5} facing {X + px_ + 0.5} {y + 0.5} {Z + pz_ + 0.5}',
            'togglehud', 'wait 20', 'shot maze_inside', 'togglehud']


def depth_of_maze():
    return len(MAZE) + 5


def maze():
    best, turns = Maze(MAZE).check(min_flips=MAZE_MIN_TURNS)
    maze_blocks()
    maze_template()
    maze_scenario(best, turns)
    write_json(os.path.join(ASSETS.replace('assets', 'data'), 'loot_table/chests/mirror_maze.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/mirror_maze'), 'pools': [
            {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('frost_steel_ingot'),
                                      'functions': [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 3, 'max': 6}}]}]},
            {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('rime_ice'),
                                      'functions': [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 8, 'max': 16}}]}]},
            {'rolls': {'type': 'minecraft:uniform', 'min': 1, 'max': 3}, 'entries': [
                {'type': 'minecraft:item', 'name': c('star_fragment'), 'weight': 3},
                {'type': 'minecraft:item', 'name': c('starlight_flask'), 'weight': 2},
                {'type': 'minecraft:item', 'name': 'minecraft:diamond', 'weight': 2}]},
        ]})
    lang_patch({
        'block.celestial.ancient_mirror': ('Древнее зеркало', 'Ancient Mirror'),
        'block.celestial.ancient_mirror.lore1': ('Вмёрзло навеки: не сдвинуть и не разбить. Повернуть можно только Камертоном.',
                                                 'Frozen in forever: cannot be moved or broken. Only a Tuning Fork turns it.'),
        'block.celestial.ancient_prism': ('Древняя призма', 'Ancient Prism'),
        'block.celestial.ancient_red_filter': ('Древний красный фильтр', 'Ancient Red Filter'),
        'block.celestial.ancient_green_filter': ('Древний зелёный фильтр', 'Ancient Green Filter'),
        'block.celestial.ancient_blue_filter': ('Древний синий фильтр', 'Ancient Blue Filter'),
        'block.celestial.rime_ice': ('Вечный лёд', 'Rime Ice'),
        'block.celestial.rime_ice.lore1': ('Не тает. Свет проходит насквозь, а путник — нет.', 'Never melts. Light passes through; travellers do not.'),
        'block.celestial.beam_lock': ('Замок трёх лучей', 'Lock of Three Beams'),
        'block.celestial.beam_lock.lore1': ('Откроется, когда красный, зелёный и синий лучи разом дойдут до своих приёмников.',
                                            'Opens when red, green and blue beams reach their receivers at once.'),
        'puzzle.celestial.zone.no_break': ('Святыня противится: её стены не поддаются', 'The sanctum resists: its walls will not yield'),
        'puzzle.celestial.beam_lock.status': ('Замок: %s  %s  %s', 'Lock: %s  %s  %s'),
        'puzzle.celestial.beam_lock.red': ('красный', 'red'),
        'puzzle.celestial.beam_lock.green': ('зелёный', 'green'),
        'puzzle.celestial.beam_lock.blue': ('синий', 'blue'),
        'puzzle.celestial.beam_lock.fork': ('У подножия замка лежит Камертон. Им поворачивают древние зеркала.',
                                            'A Tuning Fork lies at the foot of the lock. It turns the ancient mirrors.'),
        'puzzle.celestial.beam_lock.solved': ('Три луча сошлись — замок открыт', 'Three beams met — the lock is open'),
        'structure.celestial.mirror_maze': ('Зеркальный лабиринт', 'Mirror Labyrinth'),
    })


def main():
    blocks()
    solutions()
    scenario()
    loot()
    lang()
    maze()
    print('Ледяные загадки: залы', ', '.join(HALLS), '+ Зеркальный лабиринт')


if __name__ == '__main__':
    main()
