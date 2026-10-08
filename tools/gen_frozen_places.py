"""Постройки Ледяных Чертогов (волна 0.4, шаг 6): Ледяная цитадель Архонта, Зеркальный лабиринт, лагеря ангелов.

Цитадель — один составной шаблон 63×30×63: двор с жаровнями и стражами, пояс из трёх залов скользящего льда
(вклеиваются из gen_frozen_puzzles.build_hall), центральный коридор с Печатью трёх залов и купол арены Архонта из
вечной кладки (неразрушима: к арене только через залы). Лабиринт — шаблон из gen_frozen_puzzles.build_maze.
"""
import math
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import DATA, c, save_png, blockstate, model, item_def, write_json
from gen_frozen_puzzles import HALLS, build_hall, px
from gen_places import jigsaw, structure_set
from gen_story import lang_patch
from gen_structures import Template

BR, EV, PI, BI = c('frost_stone_bricks'), c('everfrost_bricks'), 'minecraft:packed_ice', 'minecraft:blue_ice'
AIR, SNOW = 'minecraft:air', 'minecraft:snow_block'
GUARDIAN = {'id': c('ice_guardian'), 'PersistenceRequired': True}


# ---------------------------------------------------------------- блоки
def blocks():
    ev = T.bricks('everfrost_bricks', [T.hexrgb(h) for h in ('#3a4f6e', '#44597a', '#4e6588')], '#1a2334')
    r = T.rng_for('everfrost_glints')
    for _ in range(7):
        px(ev, r.randrange(16), r.randrange(16), T.hexrgb('#bdf2ff'))
    for x in range(16):  # руническая нить по шву
        if x % 4 == 1:
            px(ev, x, 7, T.hexrgb('#6fd8f0'))
    save_png(ev, 'block/everfrost_bricks')
    model('block/everfrost_bricks', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/everfrost_bricks')}})
    blockstate('everfrost_bricks', {'variants': {'': {'model': c('block/everfrost_bricks')}}})
    item_def('everfrost_bricks', c('block/everfrost_bricks'))

    side = T.bricks('hall_seal_side', [T.hexrgb(h) for h in ('#5a6c84', '#667a92', '#7489a2')], '#2f3b4c')
    save_png(side, 'block/hall_seal_side')
    variants = {}
    for lit in range(4):
        img = T.bricks('hall_seal_top', [T.hexrgb(h) for h in ('#44597a', '#4e6588', '#587095')], '#1a2334')
        for i, (cx, cy) in enumerate(((4, 5), (11, 5), (7.5, 11))):
            on = i < lit
            for y in range(16):
                for x in range(16):
                    d = math.hypot(x - cx, y - cy)
                    if 1.6 <= d < 2.8:
                        px(img, x, y, T.hexrgb('#e8feff') if on else T.hexrgb('#5a7894'))
                    elif d < 1.6:
                        px(img, x, y, T.hexrgb('#7ff0ff') if on else T.hexrgb('#2a3a52'))
        save_png(img, f'block/hall_seal_{lit}')
        for opened in (False, True):
            name = f'hall_seal_{lit}'
            model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
                'top': c('block/' + name), 'side': c('block/hall_seal_side'), 'bottom': c('block/hall_seal_side')}})
            variants[f'lit={lit},open={str(opened).lower()}'] = {'model': c('block/' + name)}
    blockstate('hall_seal', {'variants': variants})
    item_def('hall_seal', c('block/hall_seal_0'))
    immune = [c('everfrost_bricks'), c('hall_seal')]
    append_tag('block', 'minecraft:dragon_immune', immune)
    append_tag('block', 'minecraft:wither_immune', immune)


# ---------------------------------------------------------------- Ледяная цитадель
SIZE, HEIGHT = 63, 30
CX = 31            # ось симметрии
ARENA_C = (31, 14)  # центр арены (x, z)
ARENA_R = 13


def spire(t, x0, z0, base_y, w, top_y):
    """Ледяной шпиль-конус над башней: плотный лёд с синими рёбрами."""
    cx, cz = x0 + (w - 1) / 2, z0 + (w - 1) / 2
    for y in range(base_y, top_y + 1):
        k = (y - base_y) / max(1, top_y - base_y)
        rad = (w / 2) * (1 - k) + 0.3
        for x in range(x0, x0 + w):
            for z in range(z0, z0 + w):
                if math.hypot(x - cx, z - cz) <= rad:
                    t.set(x, y, z, BI if (x == round(cx) or z == round(cz)) else PI)


def tower(t, x0, z0, w=9, top=16):
    t.fill(x0, 1, z0, x0 + w - 1, top, z0 + w - 1, BR)
    t.fill(x0 + 1, 1, z0 + 1, x0 + w - 2, top - 1, z0 + w - 2, AIR)
    for y in (5, 11):  # бойницы
        for x in range(x0 + 2, x0 + w - 2, 2):
            t.set(x, y, z0, c('rime_ice'))
            t.set(x, y, z0 + w - 1, c('rime_ice'))
    for x in range(x0, x0 + w, 2):  # зубцы
        t.set(x, top + 1, z0, BR)
        t.set(x, top + 1, z0 + w - 1, BR)
    spire(t, x0 + 1, z0 + 1, top + 1, w - 2, top + 8)
    t.set(x0 + w // 2, top - 2, z0 + w // 2, c('aurora_crystal'), facing='down')


def arena(t):
    """Купол арены Архонта из вечной кладки: пол с кольцом ледяных плит, колонны, ниша Инии, свет кристаллов."""
    ax, az = ARENA_C
    for x in range(ax - ARENA_R - 1, ax + ARENA_R + 2):
        for z in range(az - ARENA_R - 1, az + ARENA_R + 2):
            d = math.hypot(x - ax, z - az)
            if d > ARENA_R + 1.2:
                continue
            t.set(x, 0, z, c('glacier_tile') if 6.5 <= d < 8 or d < 1.5 else EV)
            for y in range(1, 21):
                # стена — цилиндр до y=10, выше купол (эллипсоид), толщина ~1.5
                if y <= 10:
                    outer = ARENA_R + 1.2
                else:
                    k = (y - 10) / 11.0
                    outer = (ARENA_R + 1.2) * math.sqrt(max(0.0, 1 - k * k))
                inner = outer - 1.6
                if inner <= d <= outer:
                    t.set(x, y, z, EV)
                elif d < inner:
                    t.set(x, y, z, AIR)
    for i in range(6):  # колонны из ледяных колонн по кругу
        a = i / 6 * math.tau  # 0°, 60° … — ни одна колонна не загораживает нишу Инии (север) и вход (юг)
        x, z = round(ax + math.cos(a) * 9), round(az + math.sin(a) * 9)
        t.fill(x, 1, z, x, 9, z, c('glacier_pillar'))
        t.set(x, 10, z, EV)
        t.set(x, 9, z + (1 if z < az else -1), c('aurora_crystal'), facing='down')
    # ниша Инии у северной стены: пьедестал и ангел во льду
    t.fill(ax - 2, 1, az - ARENA_R + 1, ax + 2, 1, az - ARENA_R + 3, EV)
    t.set(ax, 2, az - ARENA_R + 2, c('inia_ice'), half='lower')
    t.set(ax, 3, az - ARENA_R + 2, c('inia_ice'), half='upper')
    t.set(ax, 0, az, c('archon_seal'), awakened=False, nbt={'id': c('archon_seal')})  # печать в полу центра арены будит Архонта
    for x in range(ax - 5, ax + 6):  # замок купола
        for z in range(az - 5, az + 6):
            if math.hypot(x - ax, z - az) <= 5:
                t.set(x, 21, z, EV)
    t.set(ax, 20, az, c('aurora_crystal'), facing='down')


def citadel():
    t = Template(SIZE, HEIGHT, SIZE)
    t.fill(0, 0, 0, SIZE - 1, HEIGHT - 1, SIZE - 1, AIR)
    t.fill(0, 0, 0, SIZE - 1, 0, SIZE - 1, BR)
    # внешняя стена в два блока с зубцами
    for x in range(SIZE):
        for z in range(SIZE):
            if x < 2 or z < 2 or x >= SIZE - 2 or z >= SIZE - 2:
                t.fill(x, 1, z, x, 10, z, BR)
                if (x + z) % 2 == 0 and (x in (0, SIZE - 1) or z in (0, SIZE - 1)):
                    t.set(x, 11, z, BR)
    for x0, z0 in ((0, 0), (SIZE - 9, 0), (0, SIZE - 9), (SIZE - 9, SIZE - 9)):
        tower(t, x0, z0)
    # ворота на юге: арка из синего льда
    t.fill(CX - 2, 1, SIZE - 2, CX + 2, 6, SIZE - 1, AIR)
    for x in range(CX - 3, CX + 4):
        t.set(x, 7, SIZE - 1, BI)
    t.set(CX - 3, 6, SIZE - 1, BI)
    t.set(CX + 3, 6, SIZE - 1, BI)
    # двор: дорога из кирпича, жаровни (тепло), статуи — вмёрзшие ангелы, снег
    for z in range(44, SIZE - 2):
        for x in range(2, SIZE - 2):
            t.set(x, 0, z, BR if abs(x - CX) <= 2 else SNOW)
    for x in (CX - 7, CX + 7):
        t.set(x, 1, 52, c('brazier'), lit=True)
    for x in (9, SIZE - 10):
        t.set(x, 1, 50, c('frozen_angel'))
        t.set(x, 0, 50, BR)
    for x, z in ((12, 57), (50, 57), (20, 47), (42, 47)):
        t.set(x, 1, z, c('aurora_crystal'), facing='up')
    t.entity(CX - 10, 1, 54, GUARDIAN)
    t.entity(CX + 10, 1, 54, GUARDIAN)
    # пояс залов: внутренняя стена двора (z=43), крыша y=8
    t.fill(2, 1, 27, SIZE - 3, 8, 43, BR)
    halls = [('hall_1', 3), ('hall_2', 14), ('hall_3', 48)]
    for name, ox in halls:
        rows = HALLS[name][0]
        hall = build_hall(rows)
        ex = rows[-1].index('E')
        depth = hall.size[2]
        oz = 43 - (depth - 1)
        t.paste(hall, ox, 0, oz)
        t.fill(ox + ex, 1, 43, ox + ex, 2, 43, AIR)  # выход из преддверия во двор (сквозь внутреннюю стену)
    # центральный коридор к арене + Печать трёх залов
    t.fill(27, 1, 28, 35, 6, 43, AIR)
    for z in range(28, 44):
        for x in range(27, 36):
            t.set(x, 0, z, c('glacier_tile') if (x + z) % 2 == 0 else BR)
    t.set(CX, 1, 31, c('hall_seal'), nbt={'id': c('hall_seal'), 'Halls': len(halls)})
    for z in (32, 37, 42):
        t.set(27, 4, z, c('aurora_crystal'), facing='east')
        t.set(35, 4, z, c('aurora_crystal'), facing='west')
    # восточное крыло: заиндевевший сад (комната отдыха с костром)
    t.fill(37, 1, 30, 46, 6, 42, AIR)
    t.fill(37, 1, 43, 39, 2, 43, AIR)
    t.set(41, 1, 36, 'minecraft:campfire', lit=True, facing='north', signal_fire=False, waterlogged=False)
    for x, z in ((38, 31), (45, 31), (38, 41), (45, 41)):
        t.set(x, 1, z, c('frozen_angel'))
    t.set(41, 5, 36, c('aurora_crystal'), facing='down')
    # арена на севере и «заснеженные сады» по бокам от неё
    for z in range(2, 27):
        for x in range(2, SIZE - 2):
            t.set(x, 0, z, SNOW)
    arena(t)
    # проход сквозь стену арены: кольцо кладки на z=28 вскрыто, на z=27 — печать-дверь (откроет Печать трёх залов)
    t.fill(29, 1, 28, 33, 5, 28, AIR)
    t.fill(29, 1, 27, 33, 5, 27, c('sealed_door'))
    t.entity(8, 1, 18, GUARDIAN)
    t.entity(SIZE - 9, 1, 18, GUARDIAN)
    decorate(t)
    return t.save('frozen_citadel/main')


def decorate(t):
    """Детали: снег и ледяные шипы на крыше пояса залов, световые окна из вечного льда над коридором,
    колонны у ворот, шпиль-корона над куполом, контрфорсы внешней стены."""
    r = __import__('random').Random(4400417)
    for x in range(2, SIZE - 2):
        for z in range(27, 44):
            if t.get(x, 8, z) == BR and t.get(x, 9, z) in (None, AIR):
                t.set(x, 9, z, 'minecraft:snow', layers=r.choice((1, 1, 2, 3)))
    for x in range(4, SIZE - 4, 6):  # ледяные шипы по краю крыши со стороны двора
        t.set(x, 9, 43, BI)
        t.set(x, 10, 43, PI)
        t.set(x, 11, 43, c('aurora_crystal'), facing='up')
    for z in range(30, 43, 3):  # световые окна над коридором
        for x in range(29, 34):
            t.set(x, 8, z, c('rime_ice'))
            t.set(x, 9, z, AIR)
    for x in (CX - 4, CX + 4):  # колонны у ворот
        t.fill(x, 1, SIZE - 3, x, 8, SIZE - 3, c('glacier_pillar'))
        t.set(x, 9, SIZE - 3, c('aurora_crystal'), facing='up')
    ax, az = ARENA_C
    t.fill(ax, 22, az, ax, 26, az, c('glacier_pillar'))
    spire(t, ax - 1, az - 1, 27, 3, 29)
    for i in range(8):  # рёбра купола из вечной кладки — рельеф снаружи
        a = i / 8 * math.tau
        for y in range(11, 21):
            k = (y - 10) / 11.0
            rad = (ARENA_R + 1.2) * math.sqrt(max(0.0, 1 - k * k)) + 0.6
            x, z = round(ax + math.cos(a) * rad), round(az + math.sin(a) * rad)
            if 0 <= z < 27:
                t.set(x, y, z, EV)
    for x in range(10, SIZE - 10, 8):  # контрфорсы внутрь двора и садов
        for z0, dz in ((2, 1), (SIZE - 3, -1)):
            for k, h in enumerate((8, 6, 4)):
                if t.get(x, 1, z0 + dz * (k + 1)) in (AIR, None):
                    t.fill(x, 1, z0 + dz * (k + 1), x, h, z0 + dz * (k + 1), BR)


# ---------------------------------------------------------------- лагерь ангелов
def tent(t, x0, z0, along_x=True):
    """Шатёр-«домик» из белой шерсти на еловом каркасе, внутри — лежанка и сундук."""
    w, d = (5, 4) if along_x else (4, 5)
    for i in range(w):
        for j in range(d):
            x, z = x0 + i, z0 + j
            t.set(x, 0, z, 'minecraft:spruce_planks')
            edge = j if along_x else i
            span = d if along_x else w
            h = min(edge, span - 1 - edge) + 1
            t.set(x, h, z, 'minecraft:white_wool')
            if h > 1:
                for y in range(1, h):
                    t.set(x, y, z, AIR)
    t.set(x0 + 1, 1, z0 + 1, 'minecraft:white_carpet')


def angel_camp():
    t = Template(17, 8, 17)
    t.fill(0, 0, 0, 16, 7, 16, AIR)
    for x in range(17):
        for z in range(17):
            d = math.hypot(x - 8, z - 8)
            if d <= 8.4:
                t.set(x, 0, z, 'minecraft:snow_block' if d > 3 else BR)
    t.set(8, 1, 8, 'minecraft:campfire', lit=True, facing='north', signal_fire=False, waterlogged=False)
    for x, z in ((6, 8), (10, 8)):
        t.set(x, 1, z, 'minecraft:stripped_spruce_log', axis='z')
    tent(t, 1, 2, along_x=True)
    tent(t, 11, 2, along_x=False)
    tent(t, 2, 11, along_x=True)
    t.set(2, 1, 13, 'minecraft:chest', nbt={'id': 'minecraft:chest', 'LootTable': c('chests/angel_camp')}, facing='north',
          type='single', waterlogged=False)
    t.set(12, 1, 4, 'minecraft:chest', nbt={'id': 'minecraft:chest', 'LootTable': c('chests/angel_camp')}, facing='west',
          type='single', waterlogged=False)
    t.set(13, 1, 12, c('quest_board'))
    for x, z in ((15, 14), (1, 8)):
        t.set(x, 1, z, c('frozen_angel'))
    for x, z in ((5, 13), (13, 9)):  # фонари на столбах
        t.set(x, 1, z, 'minecraft:spruce_fence', north=False, south=False, east=False, west=False, waterlogged=False)
        t.set(x, 2, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    t.entity(7, 1, 10, {'id': c('angel'), 'PersistenceRequired': True})
    t.entity(10, 1, 6, {'id': c('angel'), 'PersistenceRequired': True})
    return t.save('angel_camp/main')


def loot():
    def item(name, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': name, 'weight': w}
        if hi > 1:
            e['functions'] = [{'function': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e
    write_json(os.path.join(DATA, 'loot_table/chests/angel_camp.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/angel_camp'), 'pools': [
            {'rolls': {'type': 'minecraft:uniform', 'min': 3, 'max': 6}, 'entries': [
                item(c('fur'), 6, 1, 3), item('minecraft:rabbit_stew', 3), item(c('hearth_stew'), 4), item(c('spiced_cider'), 4, 1, 3),
                item('minecraft:cooked_cod', 5, 2, 5), item('minecraft:bread', 5, 2, 4), item('minecraft:torch', 4, 4, 12),
                item(c('starlight_flask'), 2), item(c('frost_steel_ingot'), 2, 1, 2), item('minecraft:campfire', 2),
                item(c('aurora_crystal'), 3, 1, 3)]}]})


def structures():
    jigsaw('frozen_citadel', [c('glacier')], 0, adaptation='beard_box')
    structure_set('frozen_citadel', 44, 18, 4400417)
    jigsaw('mirror_maze', [c('ice_spires')], 0, adaptation='beard_box')
    structure_set('mirror_maze', 30, 12, 4400419)
    jigsaw('angel_camp', [c('glacier'), c('aurora_fields')], 0, adaptation='beard_thin')
    structure_set('angel_camp', 18, 7, 4400421)
    append_tag('worldgen/structure', 'celestial:codex_places', [c('frozen_citadel'), c('mirror_maze'), c('angel_camp')])


def lang():
    lang_patch({
        'block.celestial.everfrost_bricks': ('Вечная морозная кладка', 'Everfrost Bricks'),
        'block.celestial.everfrost_bricks.lore1': ('Кладка Архонта: её не берут ни кирка, ни взрыв.', 'The Archon\'s masonry: neither pick nor blast can harm it.'),
        'block.celestial.hall_seal': ('Печать трёх залов', 'Seal of Three Halls'),
        'block.celestial.hall_seal.lore1': ('Руна загорается за каждый покорённый зал цитадели. Все три — и путь к Архонту открыт.',
                                            'A rune lights for every conquered hall of the citadel. All three open the way to the Archon.'),
        'puzzle.celestial.hall_seal.status': ('Покорено залов: %s из %s', 'Halls conquered: %s of %s'),
        'puzzle.celestial.hall_seal.open': ('Печать трёх залов рассыпалась инеем — путь к Архонту открыт.',
                                            'The Seal of Three Halls crumbles into frost — the way to the Archon is open.'),
        'structure.celestial.frozen_citadel': ('Ледяная цитадель', 'Frozen Citadel'),
        'structure.celestial.angel_camp': ('Лагерь ангелов', 'Angel Camp'),
        'codex.celestial.place.frozen_citadel': ('твердыня Морозного Архонта на леднике. Покори три зала скользящего льда — Печать откроет арену.',
                                                 'the Frost Archon\'s stronghold on a glacier. Conquer three sliding-ice halls — the Seal opens the arena.'),
        'codex.celestial.place.mirror_maze': ('лабиринт из вечного льда среди шпилей. Сведи три цветных луча одновременно.',
                                              'a maze of rime ice among the spires. Bring three coloured beams together at once.'),
        'codex.celestial.place.angel_camp': ('стоянка уцелевших ангелов: костёр, припасы, поручения. Освободи вмёрзших товарищей.',
                                             'a camp of surviving angels: fire, supplies, errands. Free their frozen comrades.'),
    })


OPPOSITE = {'east': 'west', 'west': 'east', 'north': 'south', 'south': 'north'}


def citadel_scenario():
    """Сценарий: цитадель на тестовой площадке, обходы и честное прохождение трёх залов до открытия арены."""
    from ice_solver import Hall, DIR_NAMES
    X, Y0, Z = 23000, 150, 23000
    y = Y0 + 1
    out = ['# QA: Ледяная цитадель (генерирует tools/gen_frozen_places.py): вид, обходы арены, три зала → Печать открывает арену',
           '/gamemode spectator', '/effect clear @s', '/gamerule advance_time false', '/time set 6000', '/gamerule spawn_monsters false',
           '/weather clear', f'/execute in minecraft:overworld run tp @s {X + 31} {Y0 + 40} {Z + 31}', 'wait 120',
           *[f'/fill {X - 4 + i * 18} {Y0 - 3} {Z - 4} {X + 13 + i * 18} {Y0 - 1} {Z + 66} minecraft:stone' for i in range(4)],
           *[f'/fill {X - 4 + i * 18} {Y0 + h} {Z - 4} {X + 13 + i * 18} {Y0 + h + 14} {Z + 66} minecraft:air' for i in range(4) for h in (0, 15)],
           f'/place template celestial:frozen_citadel/main {X} {Y0} {Z}', 'wait 100',
           '/kill @e[type=celestial:ice_guardian]', '/kill @e[type=item]',
           'togglehud', f'/tp @s {X + 31} {Y0 + 45} {Z + 95} 180 30', 'wait 40', 'shot citadel_outside',
           f'/tp @s {X + 31} {Y0 + 60} {Z + 31} 0 90', 'wait 30', 'shot citadel_top',
           f'/tp @s {X + 31} {y + 2} {Z + 60} 180 5', 'wait 20', 'shot citadel_court',
           f'/tp @s {X + 31} {y + 1} {Z + 40} 180 10', 'wait 20', 'shot citadel_corridor',
           f'/tp @s {X + 31} {y + 3} {Z + 22} 180 15', 'wait 20', 'shot citadel_arena', 'togglehud',
           '/gamemode survival', '/effect give @s minecraft:resistance 900 4 true', '/effect give @s minecraft:saturation 900 1 true',
           '# A1 вечная кладка арены не ломается (выживание)',
           '/say TEST A1 break_everfrost expect=pass',
           f'/tp @s {X + 19.5} {y} {Z + 24.5} facing {X + 21.5} {y + 0.5} {Z + 22.5}', 'wait 10', 'hold attack 100',
           f'/execute if block {X + 21} {y} {Z + 22} celestial:everfrost_bricks',
           '# A2 печать-дверь арены на месте, пока залы не решены',
           '/say TEST A2 gate_closed expect=pass',
           f'/execute if block {X + 31} {y} {Z + 27} celestial:sealed_door']
    halls = [('hall_1', 3), ('hall_2', 14), ('hall_3', 48)]
    for i, (name, ox) in enumerate(halls):
        rows = HALLS[name][0]
        depth = len(rows) + 4
        oz = 43 - (depth - 1)
        out += [f'# S{i + 1} {name} в цитадели', f'/say TEST S{i + 1} citadel_{name} expect=pass(seal lit={i + 1})']
        for (gx, gz), d, (sx, sz) in Hall(rows).solve():
            out += [f'/tp @s {X + ox + sx + 0.5} {y} {Z + oz + sz + 0.5}', 'wait 4',
                    f'use {X + ox + gx} {y} {Z + oz + gz} {OPPOSITE[DIR_NAMES[d]]}', 'wait 30']
        out += ['wait 60', f'/execute if block {X + 31} {y} {Z + 31} celestial:hall_seal[lit={i + 1}]']
        if i == 1:
            out += ['/say TEST A3 two_halls_not_enough expect=pass', f'/execute if block {X + 31} {y} {Z + 27} celestial:sealed_door']
    out += ['/say TEST A4 gate_open expect=pass', f'/execute unless block {X + 31} {y} {Z + 27} celestial:sealed_door',
            f'/tp @s {X + 31.5} {y} {Z + 33.5} facing {X + 31.5} {y + 1} {Z + 20}', 'togglehud', 'wait 10', 'shot citadel_gate_open', 'togglehud',
            '/gamemode creative', 'quit']
    with open(os.path.join(os.path.dirname(__file__), 'scenarios', 'structures_frozen.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')


def main():
    blocks()
    n = citadel()
    angel_camp()
    loot()
    structures()
    lang()
    citadel_scenario()
    print('Постройки Чертогов: цитадель', n, 'блоков, лабиринт, лагерь')


if __name__ == '__main__':
    main()
