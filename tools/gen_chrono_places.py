"""Постройки Хронограда (волна 0.5): Часовая башня целиком (с ареной Часовщика), шестерни-памятники,
дома мастеров и литейня Тувалкаина. Шаблоны — на Template (gen_structures), размещение — jigsaw (gen_places); пол (слой y=0) встаёт вровень с землёй (смещение −1),
иначе к любому входу — ступень в целый блок.

Часовая башня: цоколь-барабан с нижним залом (вход с севера), парадная лестница с юга к двери арены,
арена Часовщика под куполом (вклеена из gen_clockmaker.arena_template), над куполом — шпиль с четырьмя циферблатами,
колоколом и медной кровлей. Карту к башне игрок получает при первом входе в Хроноград (награда главы «Часы мироздания»).
"""
import json
import math
import os

from gen_abyss import append_tag
from gen_assets import DATA, c, write_json
from gen_clockmaker import CX, CZ, R, SIZE, arena_template
from gen_places import jigsaw, structure_set
from gen_story import lang_patch
from gen_structures import Template, chest

MC = 'minecraft:'
WALL, TRIM, ACCENT = MC + 'deepslate_bricks', MC + 'waxed_cut_copper', MC + 'waxed_chiseled_copper'
ROOF = MC + 'waxed_oxidized_cut_copper'
OY = 10              # пол арены над землёй
TX, TZ, TY = SIZE, SIZE + 12, 64
SENTRY = {'id': c('clockwork_sentry'), 'PersistenceRequired': True}


# ---------------------------------------------------------------- Часовая башня
def dial(t, plane, fixed, cu, cv, r=4.4):
    """Циферблат на грани шпиля. plane 'x' — грань ⟂ x (u идёт по z), 'z' — грань ⟂ z (u по x)."""
    def put(u, v, block):
        if plane == 'x':
            t.set(fixed, cv + v, cu + u, block)
        else:
            t.set(cu + u, cv + v, fixed, block)
    for u in range(-5, 6):
        for v in range(-5, 6):
            d = math.hypot(u, v)
            if d <= 3.5:
                put(u, v, MC + 'smooth_quartz')
            elif d <= r:
                put(u, v, MC + 'waxed_copper_block')
    for u, v in ((3, 0), (0, -3), (-3, 0)):
        put(u, v, MC + 'black_concrete')
    put(0, 3, MC + 'sea_lantern')  # вместо «12» — звезда на рассвете (намёк на Денницу)
    for v in (1, 2):
        put(0, v, MC + 'gold_block')      # минутная — на «без одной минуты»
    put(-1, 1, MC + 'waxed_copper_block')  # часовая — почти на двенадцати
    put(0, 0, MC + 'gold_block')


def clock_tower():
    t = Template(TX, TY, TZ)
    t.fill(0, 1, 0, TX - 1, TY - 1, TZ - 1, MC + 'air')
    # цоколь-барабан: пол, стена кольцом, нижний зал
    for x in range(TX):
        for z in range(SIZE):
            d = math.hypot(x - CX, z - CZ)
            if d <= R + 2.8:
                t.set(x, 0, z, MC + 'polished_deepslate' if d > R + 1.8 else MC + 'deepslate_tiles')
            if R + 0.2 <= d <= R + 1.8:
                a = math.degrees(math.atan2(x - CX, -(z - CZ))) % 360
                for y in range(1, OY):
                    pil = round(a) % 30 in (0, 1, 29)
                    blk = TRIM if (pil or y in (1, OY - 1)) else WALL
                    if 4 <= y <= 6 and 12 <= round(a) % 30 <= 18:
                        blk = MC + 'yellow_stained_glass'
                    t.set(x, y, z, blk)
    # колонны нижнего зала с медными капителями, свет
    for k in range(6):
        a = math.radians(30 + 60 * k)
        x, z = round(CX + math.sin(a) * 8), round(CZ - math.cos(a) * 8)
        t.fill(x, 1, z, x, OY - 2, z, MC + 'polished_deepslate')
        t.set(x, OY - 1, z, ACCENT)
        t.set(x, 4, z + (1 if z < CZ else -1), MC + 'copper_lantern', hanging=False)
    for k in range(8):
        a = math.radians(45 * k)
        t.set(round(CX + math.sin(a) * 5), OY - 2, round(CZ - math.cos(a) * 5), MC + 'light', level=15)
        t.set(round(CX + math.sin(a) * 11), OY - 3, round(CZ - math.cos(a) * 11), MC + 'light', level=14)
    for k in range(12):  # медные фонари по кругу под потолком
        a = math.radians(15 + 30 * k)
        x, z = round(CX + math.sin(a) * 12), round(CZ - math.cos(a) * 12)
        t.set(x, OY - 1, z, MC + 'iron_chain', axis='y')
        t.set(x, OY - 2, z, MC + 'copper_lantern', hanging=True)
    # вход в нижний зал с севера (3×4) и утварь мастеров
    t.fill(CX - 1, 1, CZ - R - 2, CX + 1, 4, CZ - R + 1, MC + 'air')
    chest(t, CX - 4, 1, CZ - 6, c('chests/chrono_tower_hall'), facing='south')
    chest(t, CX + 4, 1, CZ + 6, c('chests/chrono_tower_hall'), facing='north')
    t.set(CX, 1, CZ, c('heavy_pendulum'), facing='north', swinging=True, nbt={'id': c('pendulum')})
    t.set(CX - 6, 1, CZ + 2, MC + 'anvil', facing='east')
    t.set(CX + 6, 1, CZ - 2, c('drive_press'), working=False, nbt={'id': c('drive_press')})
    # арена Часовщика сверху
    t.paste(arena_template(), 0, OY, 0)
    # парадная лестница с юга к двери арены: площадка на уровне пола арены, марш вниз к земле
    t.fill(CX - 2, OY, CZ + R + 1, CX + 2, OY, CZ + R + 5, MC + 'polished_deepslate')
    t.fill(CX - 2, 1, CZ + R + 2, CX + 2, OY - 1, CZ + R + 5, MC + 'deepslate_tiles')
    for k in range(1, OY + 1):  # ступень на высоте k, ближе к земле — дальше от башни; верхняя — край площадки
        z = CZ + R + 5 + (OY - k)
        t.fill(CX - 2, 0, z, CX + 2, k - 1, z, MC + 'deepslate_tiles')
        t.fill(CX - 2, k, z, CX + 2, k, z, MC + 'polished_deepslate_stairs', facing='north', half='bottom', shape='straight', waterlogged=False)
        for x in (CX - 3, CX + 3):  # щёки марша
            t.fill(x, 0, z, x, k, z, WALL)
    for x in (CX - 3, CX + 3):
        t.fill(x, 0, CZ + R + 2, x, OY + 1, CZ + R + 5, WALL)
        t.set(x, OY + 2, CZ + R + 5, MC + 'copper_lantern', hanging=False)
        t.set(x, 1, TZ - 1, ACCENT)
        t.set(x, 2, TZ - 1, MC + 'copper_lantern', hanging=False)
    t.entity(CX - 2, OY + 1, CZ + R + 4, SENTRY)
    t.entity(CX + 2, OY + 1, CZ + R + 4, SENTRY)
    # шпиль над куполом: стены, пояса, четыре циферблата, колокол, медная кровля
    s0, s1, base, top = CX - 5, CX + 5, OY + 23, OY + 45
    t.fill(s0, base, CZ - 5, s1, base, CZ + 5, MC + 'polished_deepslate')
    for y in range(base + 1, top + 1):
        for x in range(s0, s1 + 1):
            for z in range(CZ - 5, CZ + 6):
                if x in (s0, s1) or z in (CZ - 5, CZ + 5):
                    corner = x in (s0, s1) and z in (CZ - 5, CZ + 5)
                    band = (y - base) in (5, 19)
                    t.set(x, y, z, MC + 'waxed_copper_block' if corner else TRIM if band else WALL)
    cv = base + 12
    dial(t, 'x', s0, CZ, cv)
    dial(t, 'x', s1, CZ, cv)
    dial(t, 'z', CZ - 5, CX, cv)
    dial(t, 'z', CZ + 5, CX, cv)
    t.fill(CX, top - 3, CZ, CX, top, CZ, MC + 'iron_chain', axis='y')
    t.set(CX, top - 4, CZ, MC + 'bell', attachment='ceiling', facing='north', powered=False)
    t.set(CX, base + 3, CZ, MC + 'light', level=12)
    for i in range(7):  # кровля-пирамида с напуском
        half = 6 - i
        y = top + 1 + i
        for x in range(CX - half, CX + half + 1):
            for z in range(CZ - half, CZ + half + 1):
                if i == 6 or max(abs(x - CX), abs(z - CZ)) == half or i == 0:
                    t.set(x, y, z, ROOF if i < 6 else MC + 'gold_block')
    t.set(CX, top + 8, CZ, MC + 'waxed_lightning_rod', facing='up', powered=False, waterlogged=False)
    return t.save('clock_tower/main')


# ---------------------------------------------------------------- шестерня-памятник
def gear_monument(variant):
    """Огромная шестерня, на треть ушедшая в землю: обод с 16 зубьями, шесть спиц, ступица с осью. Три варианта старения меди."""
    rim = (MC + 'waxed_exposed_copper', MC + 'waxed_weathered_copper', MC + 'waxed_oxidized_copper')[variant]
    cut = (MC + 'waxed_exposed_cut_copper', MC + 'waxed_weathered_cut_copper', MC + 'waxed_oxidized_cut_copper')[variant]
    size, cx, cy = 23, 11, 10
    rad, teeth = 8.6, 16
    t = Template(size, 22, 4)
    for x in range(size):
        for y in range(22):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            frac = (a * teeth / (2 * math.pi)) % 1.0
            blk = None
            if rad - 2.0 < d <= rad:
                blk = rim
            elif rad < d <= rad + 1.6 and 0.2 < frac < 0.7:
                blk = rim  # зуб
            elif d <= 2.2:
                blk = MC + 'waxed_copper_block' if d > 1.0 else MC + 'iron_block'
            elif d <= rad - 2.0:
                for k in range(6):  # спица — расстояние до луча под углом k·60°
                    sa = k * math.pi / 3
                    along = dx * math.cos(sa) + dy * math.sin(sa)
                    across = abs(-dx * math.sin(sa) + dy * math.cos(sa))
                    if along > 0 and across < 0.75:
                        blk = cut
                        break
            if blk:
                t.set(x, y, 1, blk)
                t.set(x, y, 2, blk)
    t.set(cx, cy, 0, MC + 'iron_block')
    t.set(cx, cy, 3, MC + 'iron_block')
    # обломки у подножия (уровень земли — y = 3)
    for x, z, blk in ((3, 0, cut), (19, 3, rim), (20, 0, MC + 'iron_chain'), (2, 3, MC + 'iron_chain')):
        t.set(x, 3, z, blk, **({'axis': 'x'} if 'chain' in blk else {}))
    return t.save(f'gear_monument/main{variant}' if variant else 'gear_monument/main')


# ---------------------------------------------------------------- дом мастера
def master_house():
    t = Template(11, 12, 11)
    t.fill(0, 1, 0, 10, 11, 10, MC + 'air')
    t.fill(0, 0, 0, 10, 0, 10, MC + 'spruce_planks')
    t.walls(0, 0, 0, 10, 0, 10, TRIM)
    for y in range(1, 5):
        for x in range(11):
            for z in range(11):
                if x in (0, 10) or z in (0, 10):
                    corner = x in (0, 10) and z in (0, 10)
                    blk = MC + 'stripped_dark_oak_log' if corner else MC + 'polished_deepslate' if y == 1 else TRIM
                    if not corner and y in (2, 3) and ((x in (0, 10) and z in (3, 7)) or (z in (0, 10) and x in (2, 8))):
                        blk = MC + 'yellow_stained_glass'
                    t.set(x, y, z, blk, **({'axis': 'y'} if corner else {}))
    t.fill(5, 1, 10, 5, 2, 10, MC + 'air')  # дверной проём с юга
    t.set(5, 3, 10, ACCENT)
    # крыша-двускатка из зелёной меди, фронтоны кладкой
    for i in range(6):
        y = 5 + i
        for x in range(11):
            for z in (i, 10 - i):
                t.set(x, y, z, ROOF)
        for z in range(i + 1, 10 - i):
            for x in (0, 10):
                t.set(x, y, z, MC + 'deepslate_bricks')
    t.fill(8, 5, 7, 8, 10, 7, MC + 'bricks')  # труба с дымком
    t.set(8, 11, 7, MC + 'campfire', lit=True, signal_fire=False, facing='north', waterlogged=False)
    # мастерская: верстак, наковальня, пресс, пружина с валом, маятник-ходики, сундук
    t.set(1, 1, 1, MC + 'crafting_table')
    t.set(2, 1, 1, MC + 'anvil', facing='east')
    t.set(4, 1, 1, c('drive_press'), working=False, nbt={'id': c('drive_press')})
    t.set(6, 1, 1, c('clock_spring'), facing='east', active=False, nbt={'id': c('clock_spring')})
    t.set(7, 1, 1, c('shaft'), axis='x', spin=0)
    t.set(8, 1, 1, c('flywheel'), axis='x', spin=0, nbt={'id': c('flywheel')})
    t.set(9, 3, 5, c('heavy_pendulum'), facing='west', swinging=True, nbt={'id': c('pendulum')})
    chest(t, 1, 1, 8, c('chests/chrono_workshop'), facing='east')
    t.set(9, 1, 9, MC + 'barrel', facing='up', open=False)
    t.set(5, 4, 5, MC + 'copper_lantern', hanging=True)
    t.set(2, 1, 5, MC + 'lectern', facing='east', has_book=False, powered=False)
    t.entity(6, 1, 6, {'id': c('brass_doll'), 'PersistenceRequired': True})
    return t.save('master_house/main')


# ---------------------------------------------------------------- литейня Тувалкаина
def foundry():
    W, D, H = 21, 15, 14
    t = Template(W, H, D)
    t.fill(0, 1, 0, W - 1, H - 1, D - 1, MC + 'air')
    t.fill(0, 0, 0, W - 1, 0, D - 1, MC + 'polished_blackstone_bricks')
    for x in range(W):
        for z in range(D):
            for y in range(1, 8):
                if x in (0, W - 1) or z in (0, D - 1):
                    buttress = x % 5 == 0 and z in (0, D - 1) or z % 7 == 0 and x in (0, W - 1)
                    blk = MC + 'basalt' if buttress else MC + 'polished_blackstone_bricks'
                    if y == 7:
                        blk = TRIM
                    if 3 <= y <= 5 and not buttress and ((z in (0, D - 1) and x % 5 in (2, 3)) or (x in (0, W - 1) and z % 7 in (3, 4))):
                        blk = MC + 'orange_stained_glass'
                    t.set(x, y, z, blk, **({'axis': 'y'} if blk.endswith('basalt') else {}))
    # плоская кровля с двумя дымовыми трубами
    t.fill(0, 8, 0, W - 1, 8, D - 1, MC + 'blackstone')
    t.walls(0, 9, 0, W - 1, 9, D - 1, MC + 'polished_blackstone_brick_wall', up=True, north='none', south='none', east='none', west='none',
            waterlogged=False)
    for x in (4, 16):
        t.fill(x, 9, 3, x + 1, 12, 4, MC + 'bricks')
        t.set(x, 13, 3, MC + 'campfire', lit=True, signal_fire=True, facing='north', waterlogged=False)
        t.set(x + 1, 13, 4, MC + 'campfire', lit=True, signal_fire=True, facing='north', waterlogged=False)
    # ворота с юга 3×4
    t.fill(9, 1, D - 1, 11, 4, D - 1, MC + 'air')
    # жёлоб с магмой посередине, горны-тигли с лавой, наковальни, домны, пресс, цепи
    t.fill(2, 0, 7, W - 3, 0, 7, MC + 'magma_block')
    for x in (3, 8, 12, 17):
        t.set(x, 1, 2, MC + 'lava_cauldron')
        t.set(x, 1, 1, MC + 'blast_furnace', facing='south', lit=True)
    for x in (5, 15):
        t.set(x, 1, 10, MC + 'anvil', facing='east')
        t.set(x, 1, 11, MC + 'smithing_table')
    t.set(10, 1, 3, c('drive_press'), working=False, nbt={'id': c('drive_press')})
    t.set(10, 1, 4, c('steam_engine'), facing='north', active=False, nbt={'id': c('steam_engine')})
    for x in (4, 10, 16):
        t.fill(x, 4, 9, x, 7, 9, MC + 'iron_chain', axis='y')
        t.set(x, 3, 9, MC + 'lantern', hanging=True, waterlogged=False)
    for x in range(2, W - 2, 4):
        t.set(x, 6, 7, MC + 'light', level=13)
    # скрижаль Тувалкаина и запасы
    t.set(1, 1, 7, c('lore_tablet'), facing='east', nbt={'id': c('lore_tablet'), 'Sheet': 'tubal_cain'})
    chest(t, W - 2, 1, 2, c('chests/chrono_foundry'), facing='west')
    chest(t, W - 2, 1, 12, c('chests/chrono_foundry'), facing='west')
    t.entity(8, 1, 12, SENTRY)
    t.entity(13, 1, 12, SENTRY)
    t.set(6, 1, 5, c('memory_anchor'), nbt={'id': c('memory_anchor'), 'Scene': 'fiery_furnace'})  # Отблеск «Печь» (S5.6)
    return t.save('tubalcain_foundry/main')


# ---------------------------------------------------------------- колокольня Иувала
BELL_TOP = 26  # пол звонницы


def belltower():
    """Кампанила Иувала: ствол 7×7 с лестницей-стремянкой внутри, звонница с пятью колоколами и алтарём мелодии,
    медный шатёр; скрижаль Иувала внизу; реликварий на звоннице за печатями (загадка «колокола»)."""
    S = 11
    t = Template(S, 40, S)
    t.fill(0, 1, 0, S - 1, 39, S - 1, MC + 'air')
    t.fill(0, 0, 0, S - 1, 0, S - 1, MC + 'polished_deepslate')
    t.fill(1, 1, 1, 9, 2, 9, WALL)  # цоколь
    t.fill(2, 1, 2, 8, 2, 8, MC + 'air')
    for y in range(1, BELL_TOP):
        for x in range(2, 9):
            for z in range(2, 9):
                if x in (2, 8) or z in (2, 8):
                    corner = x in (2, 8) and z in (2, 8)
                    band = y % 8 == 0
                    blk = MC + 'waxed_copper_block' if corner else TRIM if band else WALL
                    if not corner and 4 <= x <= 6 and z in (2, 8) and y % 8 in (4, 5) or not corner and 4 <= z <= 6 and x in (2, 8) and y % 8 in (4, 5):
                        blk = MC + 'yellow_stained_glass'
                    t.set(x, y, z, blk)
    t.fill(5, 1, 8, 5, 3, 8, MC + 'air')  # дверь с юга
    t.fill(5, 1, 9, 5, 2, 9, MC + 'air')
    t.fill(5, 1, 3, 5, BELL_TOP, 3, MC + 'ladder', facing='south', waterlogged=False)  # стремянка по северной стене
    for y in range(4, BELL_TOP, 6):
        t.set(5, y, 5, MC + 'light', level=13)
    t.set(3, 2, 5, c('lore_tablet'), facing='east', nbt={'id': c('lore_tablet'), 'Sheet': 'jubal'})
    # звонница: пол с люком у лестницы, балкон 9×9, арки по углам, колокола по кругу, алтарь в центре
    t.fill(1, BELL_TOP, 1, 9, BELL_TOP, 9, MC + 'polished_deepslate')
    t.set(5, BELL_TOP, 3, MC + 'ladder', facing='south', waterlogged=False)
    for x, z in ((1, 1), (9, 1), (1, 9), (9, 9)):
        t.fill(x, BELL_TOP + 1, z, x, BELL_TOP + 5, z, MC + 'waxed_copper_block')
    for x in range(1, 10):
        for z in range(1, 10):
            if x in (1, 9) or z in (1, 9):
                t.set(x, BELL_TOP + 6, z, TRIM)
                if not (x in (1, 9) and z in (1, 9)):
                    t.set(x, BELL_TOP + 1, z, MC + 'waxed_copper_grate', waterlogged=False)  # перила: сквозные, но не перешагнуть
    t.set(5, BELL_TOP + 1, 5, c('bell_altar'), solved=False, nbt={'id': c('bell_altar')})
    for note, (x, z) in enumerate(((3, 5), (4, 3), (6, 3), (7, 5), (5, 7))):
        t.set(x, BELL_TOP + 1, z, c('sky_bell'), note=note)
    t.set(5, BELL_TOP + 5, 5, MC + 'copper_lantern', hanging=True)
    # реликварий в северо-восточном углу звонницы за печатями
    rx, rz = 8, 2
    t.set(rx, BELL_TOP + 1, rz, MC + 'air')
    from gen_structures import reliquary as _rel
    _rel(t, rx, BELL_TOP + 1, rz, c('chests/jubal_belfry'))
    for x, y, z in ((rx - 1, BELL_TOP + 1, rz), (rx, BELL_TOP + 1, rz + 1), (rx - 1, BELL_TOP + 2, rz), (rx, BELL_TOP + 2, rz + 1),
                    (rx, BELL_TOP + 2, rz), (rx + 1, BELL_TOP + 1, rz), (rx, BELL_TOP + 1, rz - 1)):
        t.set(x, y, z, c('sealed_door'))
    for i in range(6):  # шатёр
        half = 5 - i
        y = BELL_TOP + 7 + i
        for x in range(5 - half, 6 + half):
            for z in range(5 - half, 6 + half):
                if max(abs(x - 5), abs(z - 5)) == half or i == 0:
                    t.set(x, y, z, ROOF)
    t.set(5, BELL_TOP + 13, 5, MC + 'gold_block')
    t.set(5, BELL_TOP + 14, 5, MC + 'waxed_lightning_rod', facing='up', powered=False, waterlogged=False)
    return t.save('jubal_belltower/main')


# ---------------------------------------------------------------- добыча, размещение, переводы
def loot():
    def item(n, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': n, 'weight': w}
        if hi > 1:
            e['modifier'] = [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e

    def table(name, pools):
        write_json(os.path.join(DATA, 'loot_table/chests', name + '.json'),
                   {'type': 'minecraft:chest', 'pools': pools, 'random_sequence': c('chests/' + name)})

    def rolls(lo, hi, entries):
        return {'rolls': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}, 'entries': entries}

    tower_map = {'type': 'minecraft:item', 'name': MC + 'filled_map', 'modifier': [
        {'type': 'minecraft:exploration_map', 'decoration': 'minecraft:target_x', 'destination': '#' + c('clock_towers'),
         'search_radius': 100, 'skip_existing_chunks': False},
        {'type': 'minecraft:set_name', 'name': {'translate': 'filled_map.celestial.clock_tower'}, 'target': 'item_name'}]}
    table('chrono_workshop', [
        rolls(3, 6, [item(c('chronite_ingot'), 4, 1, 2), item(MC + 'copper_ingot', 8, 2, 6), item(c('raw_chronite'), 5, 1, 3),
                     item(c('copper_plate'), 5, 1, 4), item(c('iron_plate'), 4, 1, 3), item(c('wind_key'), 2), item(MC + 'clock', 3),
                     item(MC + 'redstone', 4, 2, 6), item(MC + 'bread', 4, 1, 3), item(c('hourglass'), 1)]),
        {'rolls': 1, 'entries': [tower_map, {'type': 'minecraft:empty', 'weight': 2}]}])
    table('chrono_foundry', [
        rolls(4, 7, [item(c('chronite_ingot'), 6, 2, 4), item(c('raw_chronite'), 6, 2, 5), item(MC + 'copper_block', 3, 1, 2),
                     item(c('copper_plate'), 5, 2, 6), item(MC + 'iron_ingot', 5, 2, 5), item(c('wind_key'), 3), item(c('chronite_pickaxe'), 1),
                     item(c('chronite_chestplate'), 1), item(MC + 'blast_furnace', 2), item(MC + 'lava_bucket', 2)])])
    table('jubal_belfry', [
        rolls(3, 5, [item(c('chronite_ingot'), 5, 1, 3), item(MC + 'amethyst_shard', 5, 3, 8), item(MC + 'note_block', 3, 1, 2),
                     item(MC + 'jukebox', 1), item(c('tuning_fork'), 3), item(MC + 'golden_carrot', 4, 2, 5), item(c('wind_key'), 2)])])
    table('chrono_tower_hall', [
        rolls(3, 5, [item(c('chronite_ingot'), 5, 1, 3), item(MC + 'gold_ingot', 5, 2, 6), item(MC + 'golden_carrot', 4, 2, 5),
                     item(MC + 'experience_bottle', 4, 2, 6), item(c('hourglass'), 1), item(c('tuning_fork'), 2), item(c('gear'), 3, 2, 4),
                     item(MC + 'spectral_arrow', 3, 4, 12)])])
    write_json(os.path.join(DATA, 'loot_table/gameplay/clock_tower_map.json'), {
        'type': 'minecraft:advancement_reward', 'pools': [{'rolls': 1, 'entries': [tower_map]}],
        'random_sequence': c('gameplay/clock_tower_map')})


def structures():
    cities = [c('cog_city'), c('copper_plains'), c('clock_valley')]
    jigsaw('clock_tower', cities, -1, adaptation='beard_box')
    write_json(os.path.join(DATA, 'tags/worldgen/structure/clock_towers.json'), {'values': [c('clock_tower')]})
    # шестерни-памятники: три варианта старения в одном пуле, наполовину в земле
    jigsaw('gear_monument', [c('copper_plains'), c('cog_city'), c('clock_valley')], -3, adaptation='beard_thin')
    write_json(os.path.join(DATA, 'worldgen/template_pool/gear_monument/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c('gear_monument/' + n),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}} for n in ('main', 'main1', 'main2')]})
    jigsaw('master_house', [c('cog_city'), c('copper_plains')], -1, adaptation='beard_thin')
    jigsaw('tubalcain_foundry', [c('foundry_wastes')], -1, adaptation='beard_box')
    structure_set('tubalcain_foundry', 26, 10, 5500507)
    # карта к башне — наградой за главу «Часы мироздания» (первый вход в Хроноград)
    path = os.path.join(DATA, 'advancement/story/clockwork.json')
    with open(path, encoding='utf-8') as f:
        adv = json.load(f)
    adv['rewards'] = {'loot': [c('gameplay/clock_tower_map')]}
    write_json(path, adv)
    jigsaw('jubal_belltower', [c('cog_city'), c('clock_valley')], -1, adaptation='beard_box')
    # наборы: «ориентиры» (одна большая постройка на участок) и «малые» — в одной точке одна из них, и не ближе 5 чанков к ориентиру
    for old in ('clock_tower', 'gear_monument', 'master_house', 'jubal_belltower', 'time_vault', 'babel_tower'):
        path = os.path.join(DATA, 'worldgen/structure_set', old + '.json')
        if os.path.exists(path):
            os.remove(path)
    structure_set('chrono_landmarks', 34, 14, 5500500, structures={'clock_tower': 2, 'babel_tower': 1})
    structure_set('chrono_minor', 12, 4, 5500503, exclusion=('chrono_landmarks', 5),
                  structures={'gear_monument': 5, 'master_house': 4, 'jubal_belltower': 1, 'time_vault': 1})
    append_tag('worldgen/structure', 'celestial:codex_places', [c('clock_tower'), c('gear_monument'), c('master_house'), c('tubalcain_foundry'),
                                                                c('jubal_belltower')])


def lang():
    lang_patch({
        'structure.celestial.clock_tower': ('Часовая башня', 'Clock Tower'),
        'structure.celestial.gear_monument': ('Шестерня-памятник', 'Gear Monument'),
        'structure.celestial.master_house': ('Дом мастера', 'Craftsman\'s House'),
        'structure.celestial.tubalcain_foundry': ('Литейня Тувалкаина', 'Tubal-cain\'s Foundry'),
        'codex.celestial.place.clock_tower': ('сердце Хронограда. Под куполом на колесе-престоле ждёт Часовщик; парадная лестница — с юга, нижний зал — с севера.',
                                              'the heart of Chronograd. Under the dome the Clockmaker waits on his wheel-throne; the grand stair is on the south, the lower hall on the north.'),
        'codex.celestial.place.gear_monument': ('шестерня с городскую башню, ушедшая в землю. Такие стояли в механизме, что когда-то крутил время.',
                                                'a gear as tall as a city tower, sunk into the ground. Such gears turned in the mechanism that once drove time.'),
        'codex.celestial.place.master_house': ('мастерская латунщика: пресс, пружина, запасы меди. Хозяйка-кукла ещё на страже.',
                                               'a brass-smith\'s workshop: a press, a spring, stores of copper. Its doll is still on guard.'),
        'codex.celestial.place.tubalcain_foundry': ('литейня среди шлака и лавы. Здесь отлит хронит; на стене — скрижаль ковача.',
                                                    'a foundry amid slag and lava. Chronite was cast here; the smith\'s tablet hangs on the wall.'),
        'structure.celestial.jubal_belltower': ('Колокольня Иувала', 'Jubal\'s Belltower'),
        'codex.celestial.place.jubal_belltower': ('кампанила с пятью колоколами. Алтарь на звоннице сыграет мелодию — повтори её колоколами.',
                                                  'a campanile with five bells. The altar in the belfry plays a melody — repeat it on the bells.'),
        'filled_map.celestial.clock_tower': ('Карта к Часовой башне', 'Map to the Clock Tower'),
    })


def main():
    clock_tower()
    for v in range(3):
        gear_monument(v)
    master_house()
    foundry()
    belltower()
    loot()
    structures()
    lang()
    print('ok: постройки Хронограда')


if __name__ == '__main__':
    main()
