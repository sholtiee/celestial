"""Головоломки этапа C (docs/PUZZLES.md): Звёздный кодовый замок (обсерватория), Плиты памяти (Святилище памяти в Раю).

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


# ---------------------------------------------------------------- Плиты памяти
def memory_textures():
    def plate(name, rim, core, alpha=255):
        img = T.noisy('memory_plate_' + name, [T.hexrgb(h) for h in ('#e8e2d2', '#efe9da', '#f6f1e4')], cell=4, grain=0.25)
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                if x in (0, 15) or y in (0, 15):
                    col = T.hexrgb('#c9a23a')
                elif 4.2 <= d < 5.4:
                    col = T.hexrgb(rim)
                elif d < 2.0:
                    col = T.hexrgb(core)
                else:
                    col = img.getpixel((x, y))[:3]
                img.putpixel((x, y), (*col, alpha))
        return img
    for name, rim, core, alpha in (('off', '#b8a77a', '#d9cfb3', 255), ('show', '#fff4c4', '#ffffff', 255),
                                   ('good', '#9fe8a8', '#e8ffe8', 255), ('gone', '#e8e2d2', '#e8e2d2', 70)):
        save_png(plate(name, rim, core, alpha), 'block/memory_plate_' + name)
        model('block/memory_plate_' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/memory_plate_' + name), 'side': c('block/skystone_bricks'), 'bottom': c('block/skystone_bricks')}})
    model('block/memory_plate_gone', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/memory_plate_gone')}})
    blockstate('memory_plate', {'variants': {f'glow={g}': {'model': c('block/memory_plate_' + g)} for g in ('off', 'show', 'good', 'gone')}})
    item_def('memory_plate', c('block/memory_plate_off'))
    for solved in (False, True):
        img = T.noisy('memory_altar', [T.hexrgb(h) for h in ('#e8e2d2', '#efe9da', '#f6f1e4')], cell=4, grain=0.25)
        for y in range(16):
            for x in range(16):
                d = math.hypot((x - 7.5) * 0.8, y - 7.5)
                if 4.0 <= d < 5.2:  # око-руна
                    img.putpixel((x, y), (*T.hexrgb('#fff4c4' if solved else '#c9a23a'), 255))
                elif d < 1.6:
                    img.putpixel((x, y), (*T.hexrgb('#ffffff' if solved else '#5aa8ff'), 255))
        name = 'memory_altar' + ('_solved' if solved else '')
        save_png(img, 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/' + name), 'side': c('block/radiant_stone'), 'bottom': c('block/skystone_bricks')}})
    blockstate('memory_altar', {'variants': {'solved=false': {'model': c('block/memory_altar')}, 'solved=true': {'model': c('block/memory_altar_solved')}}})
    item_def('memory_altar', c('block/memory_altar'))
    append_tag('block', 'minecraft:dragon_immune', [c('memory_plate'), c('memory_altar')])
    append_tag('block', 'minecraft:wither_immune', [c('memory_plate'), c('memory_altar')])


GRID = (10, 10)  # левый-верхний угол сетки плит 4×4 в шаблоне (y = TOP)
TOP = 8
ALTAR = (11, TOP + 1, 6)


def memory_shrine():
    """Парящий островок: сетка 4×4 плит памяти над ямой-ловушкой, алтарь с северной стороны, реликварий в клетке из печатей."""
    import random
    import os
    from gen_structures import Template, island_base, reliquary
    from gen_assets import DATA, write_json
    rng = random.Random(4100)
    t = Template(25, 16, 25)
    t.fill(0, 0, 0, 24, 15, 24, 'minecraft:air')
    island_base(t, 12, 12, 11, TOP, 7, rng)
    t.fill(5, TOP, 4, 19, TOP, 19, c('skystone_bricks'))
    gx, gz = GRID
    t.fill(gx - 1, TOP - 4, gz - 1, gx + 4, TOP - 4, gz + 4, c('skystone'))  # дно ямы
    t.fill(gx - 1, TOP - 3, gz - 1, gx + 4, TOP - 1, gz + 4, 'minecraft:air')
    for x in range(gx, gx + 4):
        for z in range(gz, gz + 4):
            t.set(x, TOP, z, c('memory_plate'), glow='off')
    for x in (gx - 1, gx + 4):  # кромка ямы вокруг сетки
        for z in range(gz - 1, gz + 5):
            t.set(x, TOP, z, c('skystone_bricks'))
    for z in (gz - 1, gz + 4):
        for x in range(gx - 1, gx + 5):
            t.set(x, TOP, z, c('skystone_bricks'))
    for x in range(gx - 1, gx + 5):  # стенки ямы
        for z in range(gz - 1, gz + 5):
            if x in (gx - 1, gx + 4) or z in (gz - 1, gz + 4):
                t.fill(x, TOP - 3, z, x, TOP - 1, z, c('skystone_bricks'))
    for i in range(5):  # выход из ямы: ступени на запад до поверхности острова
        x = gx - 1 - i
        t.set(x, TOP - 4 + i, gz + 1, c('skystone_bricks'))
        for yy in range(TOP - 3 + i, TOP - 1 + i):
            t.set(x, yy, gz + 1, 'minecraft:air')
    ax, ay, az = ALTAR
    t.set(ax, ay, az, c('memory_altar'), solved=False, nbt={'id': c('memory_altar')})
    for x in (ax - 2, ax + 2):  # арка над алтарём
        t.fill(x, TOP + 1, az, x, TOP + 4, az, c('skystone_bricks'))
        t.set(x, TOP + 5, az, c('radiant_stone'))
    t.fill(ax - 2, TOP + 5, az, ax + 2, TOP + 5, az, c('skystone_bricks'))
    t.set(ax, TOP + 5, az, c('radiant_stone'))
    # реликварий в клетке из печатей к востоку от сетки
    rx, rz = 17, 11
    t.set(rx, TOP, rz, c('radiant_stone'))
    reliquary(t, rx, TOP + 1, rz, 'celestial:chests/memory_shrine')
    for x, y, z in ((rx - 1, TOP + 1, rz), (rx + 1, TOP + 1, rz), (rx, TOP + 1, rz - 1), (rx, TOP + 1, rz + 1), (rx, TOP + 2, rz)):
        t.set(x, y, z, c('sealed_door'))
    for x, z in ((5, 4), (19, 4), (5, 19), (19, 19)):  # колонны по углам с сияющим камнем
        t.fill(x, TOP + 1, z, x, TOP + 3, z, c('skystone_bricks'))
        t.set(x, TOP + 4, z, c('radiant_stone'))
    t.save('memory_shrine/main')
    write_json(os.path.join(DATA, 'worldgen/template_pool/memory_shrine/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c('memory_shrine/main'),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}}]})
    write_json(os.path.join(DATA, 'worldgen/structure/memory_shrine.json'), {
        'type': 'minecraft:jigsaw', 'biomes': '#' + c('has_structure/memory_shrine'), 'max_distance_from_center': 80, 'size': 1,
        'spawn_overrides': {}, 'start_height': {'absolute': 120}, 'start_pool': c('memory_shrine/main'), 'step': 'surface_structures',
        'terrain_adaptation': 'none', 'use_expansion_hack': False})
    write_json(os.path.join(DATA, 'tags/worldgen/biome/has_structure/memory_shrine.json'),
               {'values': [c(b) for b in ('golden_meadows', 'heaven_gardens', 'star_glade', 'rainbow_shoals')]})
    append_tag('worldgen/structure', 'celestial:codex_places', [c('memory_shrine')])
    write_json(os.path.join(DATA, 'loot_table/chests/memory_shrine.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/memory_shrine'), 'pools': [
            {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('rune_of_wind')}, {'type': 'minecraft:item', 'name': c('rune_of_sky')}]},
            {'rolls': {'type': 'minecraft:uniform', 'min': 3, 'max': 5}, 'entries': [
                {'type': 'minecraft:item', 'name': c('starquartz'), 'weight': 6,
                 'functions': [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 3, 'max': 8}}]},
                {'type': 'minecraft:item', 'name': c('etherite_ingot'), 'weight': 4,
                 'functions': [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 1, 'max': 3}}]},
                {'type': 'minecraft:item', 'name': c('manna_berries'), 'weight': 4},
                {'type': 'minecraft:item', 'name': 'minecraft:golden_apple', 'weight': 2}]}]})


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
        'block.celestial.memory_plate': ('Плита памяти', 'Memory Plate'),
        'block.celestial.memory_plate.lore1': ('Вспыхивает по воле алтаря. Запомни путь и пройди его ногами.', 'Flashes at the altar\'s will. Remember the path and walk it.'),
        'block.celestial.memory_altar': ('Алтарь памяти', 'Memory Altar'),
        'block.celestial.memory_altar.lore1': ('ПКМ — показать путь по плитам.', 'Use to show the path across the plates.'),
        'puzzle.celestial.memory.watch': ('Смотри: плиты вспыхнут по порядку…', 'Watch: the plates will flash in order…'),
        'puzzle.celestial.memory.wrong': ('Память подвела — плиты ушли из-под ног.', 'Memory failed — the plates gave way.'),
        'puzzle.celestial.memory.solved': ('Путь уже пройден.', 'The path is already walked.'),
        'structure.celestial.memory_shrine': ('Святилище памяти', 'Shrine of Memory'),
        'codex.celestial.place.memory_shrine': ('островок с плитами над ямой: алтарь показывает путь, пройди его по порядку.',
                                                'an islet of plates over a pit: the altar shows a path, walk it in order.'),
        'codex.celestial.puzzle.memory': ('Плиты памяти', 'Memory Plates'),
        'codex.celestial.puzzle.memory.hint': ('Святилище памяти в Раю: запомни вспышки и пройди путь ногами — не верхом и не в полёте.',
                                               'a Shrine of Memory in Heaven: remember the flashes and walk the path on foot — no riding or flying.'),
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


def memory_route(X, Y0, Z):
    """Копия MemoryAltarBlockEntity.route для неповёрнутого шаблона в (X, Y0, Z)."""
    ax, ay, az = X + ALTAR[0], Y0 + ALTAR[1], Z + ALTAR[2]
    plates = [(X + GRID[0] + i, Y0 + TOP, Z + GRID[1] + k) for i in range(4) for k in range(4)]
    plates.sort(key=lambda p: ((p[0] - ax) ** 2 + (p[1] - ay) ** 2 + (p[2] - az) ** 2, p[0], p[2]))
    seed = as_long(ax, ay, az) ^ 0x4D454D4F5259
    if seed >= 1 << 63:
        seed -= 1 << 64
    r = JavaRandom(seed)
    out, prev = [], -1
    for _ in range(6):
        while True:
            k = r.next_int(len(plates))
            if k != prev:
                break
        out.append(plates[k])
        prev = k
    return out


def memory_scenario():
    import os
    X, Y0, Z = 26000, 150, 26000
    route = memory_route(X, Y0, Z)
    gx, gz = X + GRID[0], Z + GRID[1]
    wrong = next((gx + i, Y0 + TOP, gz + k) for i in range(4) for k in range(4) if (gx + i, Y0 + TOP, gz + k) != route[0])
    ax, ay, az = X + ALTAR[0], Y0 + ALTAR[1], Z + ALTAR[2]
    y = Y0 + TOP + 1
    out = ['# QA: Плиты памяти (генерирует tools/gen_puzzles_c.py; маршрут — копия Java-ГСЧ)',
           '/gamemode creative', '/effect clear @s', '/gamerule advance_time false', '/time set 6000', '/gamerule spawn_monsters false',
           f'/execute in minecraft:overworld run tp @s {X + 12} {Y0 + 25} {Z + 12}', 'fly', 'wait 80',
           f'/fill {X - 2} {Y0} {Z - 2} {X + 26} {Y0 + 16} {Z + 26} minecraft:air',
           f'/place template celestial:memory_shrine/main {X} {Y0} {Z}', 'wait 40',
           f'/tp @s {X + 12.5} {y + 8} {Z + 2} facing {X + 12} {y} {Z + 12}', 'togglehud', 'wait 20', 'shot memory_shrine', 'togglehud',
           '/gamemode survival', '/effect give @s minecraft:resistance 900 4 true', '/clear @s',
           '# B1 своя «доска» через яму: камень не ставится',
           '/say TEST B1 no_bridge expect=pass', '/give @s minecraft:stone 4',
           f'/tp @s {gx - 1.5} {y} {gz + 1.5} facing {gx + 0.5} {y - 1} {gz + 1.5}', 'wait 5',
           f'use {gx - 1} {Y0 + TOP} {gz + 1} east', 'wait 5', f'/execute unless block {gx} {Y0 + TOP} {gz + 1} minecraft:stone', '/clear @s',
           '# B2 неверный шаг: плиты уходят из-под ног, игрок в яме',
           '/say TEST B2 wrong_step expect=pass',
           f'/tp @s {wrong[0] + 0.5} {y} {wrong[2] + 0.5}', 'wait 30',
           f'/execute if entity @s[y={Y0},dy={TOP - 1}]',
           '# S показ и честный проход (после блокировки 20 с)',
           f'/tp @s {ax + 0.5} {y} {az + 2.5} facing {ax + 0.5} {ay + 0.5} {az + 0.5}', 'wait 420',
           f'use {ax} {ay} {az} south', 'wait 10', 'togglehud',
           f'/tp @s {ax + 0.5} {y + 3} {az + 1.5} facing {gx + 2} {Y0 + TOP} {gz + 2}', 'wait 20', 'shot memory_show', 'togglehud', 'wait 90',
           '/say TEST S solve expect=pass,pass(items)']
    for (px, py, pz) in route:
        out += [f'/tp @s {px + 0.5} {y} {pz + 0.5}', 'wait 8']
    out += ['wait 20', f'/execute if block {ax} {ay} {az} celestial:memory_altar[solved=true]',
            f'/tp @s {X + 15.5} {y} {Z + 11.5} facing {X + 17.5} {y + 0.5} {Z + 11.5}', 'wait 5', f'use {X + 17} {y} {Z + 11} west', 'wait 10',
            '/execute if items entity @s container.* *', '/gamemode creative', 'quit']
    with open(os.path.join(os.path.dirname(__file__), 'scenarios', 'puzzle_memory.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    return route


def main():
    blocks()
    memory_textures()
    memory_shrine()
    lang()
    print('маршрут тестового святилища:', memory_route(26000, 150, 26000))
    memory_scenario()
    print('комбинация тестового замка:', scenario())
    print('ok: головоломки C (звёздный замок)')


if __name__ == '__main__':
    main()
