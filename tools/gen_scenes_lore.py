"""Отблески S3 (docs/LORE.md §5c, SONNET_PLAN S3): воспоминания по образцу «Плода» — Изгнание, Серафим до падения, Каин и Авель, Скованные,
Потоп, Иния в оковах, «Осколки падения» трёх боссов, Сухие кости, Лестница Иакова.

Подключается из gen_scenes.main(): PEOPLE (облики актёров), stages() (шаблоны сцен), SCENES (данные), LANG (переводы).
Якоря в постройках мира ставят их генераторы (gen_eden, gen_structures, gen_ark, gen_prison, gen_frozen_places) — здесь только `anchor()` для общих строк.
Правила тех же, что у «Плода»: Бог и Христос не изображаются (только `voice`), текст реплик 3–6 слов, люди в одеждах, шаблон заполняется воздухом.
"""
import math
import os
import random

from gen_assets import DATA, c, write_json
from gen_structures import Template, island_base

AIR = 'minecraft:air'

# облик: кожа, волосы, одеяние, отделка, глаза, длинные волосы, борода (см. gen_scenes.mortal)
PEOPLE = {
    'cain': ('#d9a97c', '#3a2616', '#8a6a44', '#5a4128', '#3a2a1a', False, True),
    'abel': ('#e6bc94', '#6a4a28', '#e8dcc0', '#b8a060', '#4a7ab0', False, False),
    'seraph': ('#fff0d0', '#ffe9a0', '#fff2c8', '#f2c24a', '#ffd84a', True, False),
    'chorister': ('#f1d6bd', '#d8c08a', '#f6f2e6', '#c9d8f0', '#5a8ac8', False, False),
    'watcher': ('#c9b8a8', '#2a2a32', '#3a3a4a', '#8a8aa0', '#9a5ac8', True, True),
    'host': ('#f3d6bd', '#f4d27a', '#e8f0ff', '#6fa6ff', '#5ab8ff', False, False),
    'archon': ('#d8e8f4', '#e8f6ff', '#9ac8e8', '#e8f6ff', '#7fe0ff', True, False),
    'inia': ('#e8eef6', '#eef6ff', '#cfe4f6', '#7fc6ec', '#5ab4e0', True, False),
    'noah': ('#dcb08a', '#c8c0b0', '#7a5a3a', '#a8864a', '#4a6a8a', False, True),
    'prophet': ('#d8b088', '#2a2018', '#5a6a8a', '#c9a24a', '#3a4a6a', False, True),
}


def step(t, **kw):
    return {'t': t, **kw}


def base(S, H):
    t = Template(S, H, S)
    t.fill(0, 0, 0, S - 1, H - 1, S - 1, AIR)
    return t


def tree(t, x, z, top, rng, h=5, r=3):
    for y in range(top + 1, top + 1 + h):
        t.set(x, y, z, c('skywood_log'), axis='y')
    for dx in range(-r, r + 1):
        for dy in range(0, r):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz + (dy * 1.4) ** 2 <= r * r + 1 and rng.random() > 0.1:
                    t.set(x + dx, top + h + dy - 1, z + dz, c('skywood_leaves'), distance=1, persistent=True, waterlogged=False)
    t.set(x, top + h, z, 'minecraft:light', level=13, waterlogged=False)


# ------------------------------------------------------------------ шаблоны сцен
def stage_exile():
    """Изгнание: Сад слева (золотая трава, деревья), у врат — высокая арка, справа — голая земля с терновником."""
    S, TOP = 49, 4
    rng = random.Random(6100)
    t = base(S, 26)
    island_base(t, 24, 20, 23, TOP, 7, rng)
    for x in range(S):
        for z in range(S):
            if x >= 37 and t.get(x, TOP, z) == c('golden_grass'):
                t.set(x, TOP, z, rng.choice(['minecraft:coarse_dirt', 'minecraft:gravel', 'minecraft:coarse_dirt', 'minecraft:dirt']))
    for _ in range(160):  # цветы Сада — только до врат
        x, z = rng.randrange(2, 34), rng.randrange(2, S - 2)
        if t.get(x, TOP, z) == c('golden_grass') and t.get(x, TOP + 1, z) in (None, AIR):
            t.set(x, TOP + 1, z, c(rng.choice(['sunbell', 'dawn_poppy', 'starflower', 'golden_tuft'])))
    for x, z in ((8, 10), (10, 31), (22, 6), (20, 36), (27, 34)):
        tree(t, x, z, TOP, rng)
    for _ in range(46):  # за вратами — сухие кусты и терновник
        x, z = rng.randrange(38, 46), rng.randrange(4, 38)
        if t.get(x, TOP, z) not in (None, AIR) and t.get(x, TOP + 1, z) in (None, AIR):
            t.set(x, TOP + 1, z, 'minecraft:dead_bush')
    # тропа через врата и сами врата (арка из стен Эдема)
    for x in range(26, 46):
        for z in (20, 21, 22):
            t.set(x, TOP, z, c('skystone_bricks') if x < 37 else 'minecraft:gravel')
    for z in (15, 16, 17, 25, 26, 27):
        t.fill(34, TOP + 1, z, 35, TOP + 9, z, c('eden_wall'))
    t.fill(34, TOP + 8, 15, 35, TOP + 9, 27, c('eden_wall'))
    t.fill(34, TOP + 7, 18, 35, TOP + 7, 24, c('radiant_stone'))
    t.set(34, TOP + 10, 21, c('sky_crystal'), facing='up', waterlogged=False)
    for z in (15, 27):
        t.set(34, TOP + 10, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    return t.save('memory/exile')


def stage_seraph_choir():
    """Зал хора: круглый пол, десять колонн со светом, у северного края — возвышение и Престол под покровом (светящаяся сфера; самого Престола не видно)."""
    S, TOP = 47, 4
    t = base(S, 24)
    cx = cz = 23
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - cx, z - cz)
            if d <= 20:
                t.fill(x, TOP - 2, z, x, TOP - 1, z, c('skystone'))
                ring = int(d) % 4 == 0
                t.set(x, TOP, z, c('radiant_stone') if ring else c('skystone_bricks'))
    for i in range(10):
        a = i / 10 * math.tau + 0.3
        x, z = round(cx + math.cos(a) * 17.5), round(cz + math.sin(a) * 17.5)
        t.fill(x, TOP + 1, z, x, TOP + 11, z, c('skystone_bricks'))
        t.set(x, TOP + 12, z, 'minecraft:light', level=15, waterlogged=False)
        t.set(x, TOP + 12, z, c('radiant_stone'))
    for k, z in enumerate((9, 8, 7)):  # возвышение к Престолу (север)
        t.fill(cx - 5 + k, TOP + 1 + k, z - 3, cx + 5 - k, TOP + 1 + k, z, c('radiant_stone'))
    for x in range(cx - 4, cx + 5):
        for y in range(TOP + 7, TOP + 15):
            for z in range(0, 9):
                d = math.sqrt((x - cx) ** 2 + (y - (TOP + 10)) ** 2 + (z - 4) ** 2)
                if d <= 3.5:
                    t.set(x, y, z, 'minecraft:white_stained_glass' if d > 2.4 else c('radiant_stone'))
    return t.save('memory/seraph_choir')


def stage_brothers():
    """Поле двух братьев: слева алтарь Авеля у стада, справа — алтарь Каина у пшеницы."""
    S, TOP = 41, 4
    rng = random.Random(6200)
    t = base(S, 20)
    island_base(t, 20, 22, 19, TOP, 5, rng)
    for x in range(S):
        for z in range(S):
            if t.get(x, TOP, z) == c('golden_grass') and rng.random() < 0.5:
                t.set(x, TOP, z, 'minecraft:grass_block')
    for ax, mat in ((11, 'minecraft:smooth_stone'), (29, 'minecraft:cobblestone')):
        t.fill(ax - 1, TOP + 1, 13, ax + 1, TOP + 1, 15, mat)
        t.set(ax, TOP + 2, 14, 'minecraft:stone_slab', type='bottom', waterlogged=False)
    for x in range(25, 35):  # пшеничное поле Каина
        for z in range(19, 27):
            t.set(x, TOP, z, 'minecraft:farmland', moisture=7)
            t.set(x, TOP + 1, z, 'minecraft:wheat', age=7)
    for x, z in ((6, 26), (5, 20), (15, 27)):
        t.set(x, TOP + 1, z, c(rng.choice(['sunbell', 'dawn_poppy'])))
    for x, z in ((20, 8), (36, 10), (4, 12)):
        tree(t, x, z, TOP, rng, h=4, r=2)
    return t.save('memory/brothers')


def stage_chains():
    """Сошествие во тьму: плато с цепью воинства, пологий спуск и чёрная арка Темницы внизу."""
    S, TOP = 49, 4
    rng = random.Random(6300)
    t = base(S, 26)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 24, z - 24)
            if d > 23:
                continue
            h = TOP + 5 if z < 13 else (TOP + 5 - (z - 12) if z < 18 else TOP)  # плато → спуск → низина
            for y in range(0, h + 1):
                t.set(x, y, z, 'minecraft:deepslate' if y < h else rng.choice(['minecraft:blackstone', 'minecraft:deepslate', 'minecraft:gravel']))
    for z in range(13, 19):  # ступени-спуск вдоль спуска
        pass
    for x in (18, 30):  # факелы вдоль пути
        for z in (8, 20, 30):
            hh = TOP + 5 if z < 13 else (TOP if z >= 18 else TOP + 5 - (z - 12))
            t.fill(x, hh + 1, z, x, hh + 2, z, 'minecraft:blackstone_wall', up=True, north='none', south='none', east='none', west='none', waterlogged=False)
            t.set(x, hh + 3, z, 'minecraft:soul_lantern', hanging=False, waterlogged=False)
    # арка Темницы в южной части: стены, проём, внутри — темно
    for x in range(21, 32):
        for y in range(TOP + 1, TOP + 8):
            for z in range(40, 46):
                if x in (21, 31) or y >= TOP + 6 or z == 45:
                    t.set(x, y, z, c('abyss_bricks'))
    t.fill(24, TOP + 1, 40, 28, TOP + 5, 40, AIR)
    t.fill(24, TOP + 6, 40, 28, TOP + 6, 40, c('abyss_bricks'))
    return t.save('memory/chains')


def stage_flood():
    """Берег и Ковчег под ливнем: слева море, посередине мокрый берег со зверями, справа — борт Ковчега с пандусом."""
    S, TOP = 45, 4
    rng = random.Random(6400)
    t = base(S, 22)
    for x in range(S):
        for z in range(S):
            if math.hypot(x - 24, z - 22) > 21:
                continue
            for y in range(0, TOP + 1):
                t.set(x, y, z, 'minecraft:mud' if y == TOP else 'minecraft:dirt')
            if x < 7:
                t.set(x, TOP, z, 'minecraft:water', level=0)
    # корпус Ковчега: борт, настил, палатка-каюта; пандус от берега
    for x in range(27, 44):
        for z in range(9, 25):
            t.set(x, TOP + 1, z, 'minecraft:spruce_planks')
            if x in (27, 43) or z in (9, 24):
                t.fill(x, TOP + 2, z, x, TOP + 5, z, 'minecraft:spruce_planks')
    t.fill(27, TOP + 2, 15, 27, TOP + 4, 19, AIR)  # проём борта
    for i in range(5):
        for z in range(14, 20):
            t.set(22 + i, TOP + (i // 2) + (0 if i < 2 else 0), z, 'minecraft:spruce_planks')
    for k in range(5):  # пандус: ступени по ходу к борту
        t.fill(22 + k, TOP + 1, 14, 22 + k, TOP + 1 + (k // 2), 19, 'minecraft:spruce_planks')
    t.fill(28, TOP + 6, 10, 42, TOP + 6, 23, 'minecraft:dark_oak_planks')
    t.set(30, TOP + 5, 12, 'minecraft:lantern', hanging=True, waterlogged=False)
    t.set(40, TOP + 5, 20, 'minecraft:lantern', hanging=True, waterlogged=False)
    for x, z in ((33, 12), (36, 20), (39, 14)):
        t.set(x, TOP + 2, z, 'minecraft:hay_block')
    return t.save('memory/flood')


def stage_ice_hall():
    """Ледяной зал: круглый пол, колонны, ниша у северной стены; под её устьем спрятана ледяная плита (шаг lift поднимает её и запирает нишу)."""
    S, TOP = 41, 8
    t = base(S, 26)
    cx = cz = 20
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - cx, z - cz)
            if d <= 17:
                t.fill(x, 0, z, x, TOP - 1, z, 'minecraft:blue_ice' if d > 15 else c('frost_stone'))
                t.set(x, TOP, z, c('glacier_tile') if 8 <= d < 9.5 or d < 1.5 else c('frost_stone_bricks'))
    for i in range(8):
        a = i / 8 * math.tau + 0.4
        x, z = round(cx + math.cos(a) * 12), round(cz + math.sin(a) * 12)
        t.fill(x, TOP + 1, z, x, TOP + 9, z, c('glacier_pillar'))
        t.set(x, TOP + 10, z, c('everfrost_bricks'))
    # ниша: свод из льда на севере (z 2..7), устье на z = 8; под полом перед устьем — плита, которая встанет на место
    for x in range(14, 27):
        for z in range(2, 9):
            for y in range(TOP + 1, TOP + 9):
                if x in (14, 26) or z == 2 or y == TOP + 8:
                    t.set(x, y, z, 'minecraft:packed_ice')
    t.fill(15, TOP + 1, 3, 25, TOP + 7, 7, AIR)
    for x in range(15, 26):
        for y in range(TOP - 8, TOP):
            t.set(x, y, 8, 'minecraft:blue_ice')  # плита: будет поднята на 8 и закроет устье ниши
    t.set(20, TOP + 8, 5, c('aurora_crystal'), facing='down')
    return t.save('memory/ice_hall')


def stage_void_star():
    """Пустота и малая площадка: падение звезды в Бездну (глазами Пожирателя)."""
    S, TOP = 41, 4
    rng = random.Random(6500)
    t = base(S, 16)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 20, z - 20)
            if d <= 6.5:
                t.fill(x, TOP - 2, z, x, TOP, z, 'minecraft:obsidian' if d > 3 else c('abyss_bricks'))
    for _ in range(60):
        a, r = rng.random() * math.tau, rng.uniform(8, 18)
        x, y, z = round(20 + math.cos(a) * r), rng.randrange(0, 12), round(20 + math.sin(a) * r)
        t.set(x, y, z, c('shadow_crystal'), facing='up', waterlogged=False) if y % 3 == 0 else None
    return t.save('memory/void_star')


def stage_dry_bones():
    """Долина сухих костей: снег, лёд, россыпи костяных блоков на отдельном слое (его поднимет шаг lift)."""
    S, TOP = 47, 4
    rng = random.Random(6600)
    t = base(S, 22)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 23, z - 23)
            if d > 22:
                continue
            for y in range(0, TOP):
                t.set(x, y, z, 'minecraft:packed_ice' if y < TOP - 2 else 'minecraft:snow_block')
            t.set(x, TOP, z, 'minecraft:snow_block')
    for _ in range(60):  # кости и черепа только вокруг пророка, слой TOP+1..TOP+2
        a, r = rng.random() * math.tau, rng.uniform(3, 15)
        x, z = round(23 + math.cos(a) * r), round(23 + math.sin(a) * r)
        t.set(x, TOP + 1, z, 'minecraft:bone_block', axis=rng.choice(['x', 'y', 'z']))
        if rng.random() < 0.4:
            t.set(x, TOP + 2, z, 'minecraft:bone_block', axis='y')
    for _ in range(14):
        a, r = rng.random() * math.tau, rng.uniform(4, 15)
        x, z = round(23 + math.cos(a) * r), round(23 + math.sin(a) * r)
        t.set(x, TOP + 1, z, 'minecraft:skeleton_skull', rotation=rng.randrange(16))
    for _ in range(18):  # застывший лёд по краям
        a, r = rng.random() * math.tau, rng.uniform(16, 21)
        x, z = round(23 + math.cos(a) * r), round(23 + math.sin(a) * r)
        t.fill(x, TOP + 1, z, x, TOP + rng.randrange(2, 6), z, 'minecraft:blue_ice')
    return t.save('memory/dry_bones')


def stage_jacob():
    """Ночное поле, камень-изголовье и лестница света, уходящая вверх и на восток (40 ступеней)."""
    S, H, TOP = 62, 56, 4
    rng = random.Random(6700)
    t = Template(S, H, 41)
    t.fill(0, 0, 0, S - 1, H - 1, 40, AIR)
    island_base(t, 12, 20, 18, TOP, 5, rng)
    t.fill(8, TOP + 1, 19, 10, TOP + 1, 21, 'minecraft:stone')  # камень-изголовье
    t.set(9, TOP + 2, 20, 'minecraft:stone_slab', type='bottom', waterlogged=False)
    for _ in range(40):
        x, z = rng.randrange(2, 24), rng.randrange(4, 36)
        if t.get(x, TOP, z) == c('golden_grass') and t.get(x, TOP + 1, z) in (None, AIR):
            t.set(x, TOP + 1, z, c(rng.choice(['starflower', 'golden_tuft'])))
    for i in range(40):  # ступень i: блок на высоте TOP+1+i
        x, y = 16 + i, TOP + 1 + i
        for z in (19, 20, 21):
            t.set(x, y, z, c('radiant_stone') if i % 4 == 0 else 'minecraft:white_stained_glass')
        if i % 3 == 0:
            for z in (18, 22):
                t.set(x, y + 1, z, 'minecraft:light', level=15, waterlogged=False)
    for x in range(54, 61):  # площадка на вершине
        for z in range(16, 25):
            if math.hypot(x - 57, z - 20) <= 4.2:
                t.set(x, TOP + 41, z, c('radiant_stone'))
    t.set(57, TOP + 42, 20, 'minecraft:light', level=15, waterlogged=False)
    return t.save('memory/jacob')


def stages():
    stage_exile()
    stage_seraph_choir()
    stage_brothers()
    stage_chains()
    stage_flood()
    stage_ice_hall()
    stage_void_star()
    stage_dry_bones()
    stage_jacob()


# ------------------------------------------------------------------ данные сцен
SCENES = {
    # S3.1 Изгнание: Адам и Ева выходят из Сада; за ними встаёт Херувим с мечом
    'exile': {
        'stage': c('memory/exile'), 'center': [24, 5, 21], 'radius': 26, 'spawn': [18.5, 5, 28.5, -70],
        'sheet': 'exile', 'thought': 'memory.celestial.exile.thought',
        'actors': [
            {'id': 'adam', 'type': 'human', 'skin': 'adam', 'pos': [27.5, 5, 20.5], 'yaw': 270, 'pose': 3},
            {'id': 'eve', 'type': 'human', 'skin': 'eve', 'pos': [27.5, 5, 22.5], 'yaw': 270, 'pose': 3},
        ],
        'steps': [
            step('wait', ticks=40),
            step('dim', value=0.25),
            step('voice', key='memory.celestial.exile.voice', pos=[27.5, 5, 21.5], ticks=100),
            step('pose', actor='adam', pose=0),
            step('pose', actor='eve', pose=0),
            step('move', actor='adam', to=[36.5, 5, 20.5], speed=0.06, wait=False),
            step('move', actor='eve', to=[36.5, 5, 22.5], speed=0.06),
            step('move', actor='adam', to=[43.5, 5, 20.5], speed=0.06, wait=False),
            step('move', actor='eve', to=[43.5, 5, 22.5], speed=0.06),
            step('entity', type=c('gate_cherub'), pos=[35.5, 5, 21.5], yaw=270),
            step('dim', value=0.5),
            step('wait', ticks=40),
            step('pose', actor='adam', pose=4),
            step('pose', actor='eve', pose=4),
            step('face', actor='eve', to=[34.5, 7, 21.5]),
            step('say', actor='eve', key='memory.celestial.exile.eve', ticks=80),
            step('wait', ticks=60),
            step('despawn', actor='adam'),
            step('despawn', actor='eve'),
            step('end', ticks=40),
        ],
    },
    # S3.2 Серафим до падения: светлый, поёт в хоре; Денница подходит и шепчет ему
    'seraph_choir': {
        'stage': c('memory/seraph_choir'), 'center': [23, 5, 23], 'radius': 22, 'spawn': [23.5, 5, 40.5, 180],
        'sheet': 'seraph_before', 'thought': 'memory.celestial.seraph.thought',
        'actors': [
            {'id': 'seraph', 'type': 'human', 'skin': 'seraph', 'pos': [23.5, 5, 15.5], 'yaw': 180},
            {'id': 'c1', 'type': 'human', 'skin': 'chorister', 'pos': [13.5, 5, 11.5], 'yaw': 270},
            {'id': 'c2', 'type': 'human', 'skin': 'chorister', 'pos': [12.5, 5, 15.5], 'yaw': 270},
            {'id': 'c3', 'type': 'human', 'skin': 'chorister', 'pos': [13.5, 5, 19.5], 'yaw': 270},
            {'id': 'c4', 'type': 'human', 'skin': 'chorister', 'pos': [33.5, 5, 11.5], 'yaw': 90},
            {'id': 'c5', 'type': 'human', 'skin': 'chorister', 'pos': [34.5, 5, 15.5], 'yaw': 90},
            {'id': 'c6', 'type': 'human', 'skin': 'chorister', 'pos': [33.5, 5, 19.5], 'yaw': 90},
        ],
        'steps': [
            step('wait', ticks=40),
            step('particles', type='minecraft:end_rod', pos=[23.5, 12, 6], count=60, spread=1.5),
            step('caption', key='memory.celestial.seraph.holy', ticks=90),
            step('near', pos=[23.5, 5, 25], r=9, timeout=700),
            step('say', actor='seraph', key='memory.celestial.seraph.sing', ticks=70),
            step('spawn', actor={'id': 'morning', 'type': 'human', 'skin': 'morning_star', 'pos': [39.5, 5, 21.5], 'yaw': 90}),
            step('particles', type='minecraft:end_rod', pos=[39.5, 7, 21.5], count=50, spread=0.8),
            step('move', actor='morning', to=[27.5, 5, 16.5], speed=0.05),
            step('face', actor='morning', to='seraph'),
            step('face', actor='seraph', to='morning'),
            step('wait', ticks=30),
            step('say', actor='morning', key='memory.celestial.seraph.morning', ticks=80),
            step('dim', value=0.55),
            step('particles', type='minecraft:white_ash', pos=[23.5, 9, 15.5], count=120, spread=3),
            step('wait', ticks=60),
            step('despawn', actor='morning'),
            step('end', ticks=40),
        ],
    },
    # S3.3 Каин и Авель: два алтаря, два дыма; сцена гаснет перед ударом
    'brothers': {
        'stage': c('memory/brothers'), 'center': [20, 5, 22], 'radius': 19, 'spawn': [20.5, 5, 35.5, 180],
        'sheet': 'cain_abel', 'thought': 'memory.celestial.brothers.thought',
        'actors': [
            {'id': 'abel', 'type': 'human', 'skin': 'abel', 'pos': [11.5, 5, 17.5], 'yaw': 180},
            {'id': 'cain', 'type': 'human', 'skin': 'cain', 'pos': [29.5, 5, 17.5], 'yaw': 180},
        ],
        'steps': [
            step('entity', type='minecraft:sheep', pos=[8.5, 5, 21.5], yaw=90),
            step('entity', type='minecraft:sheep', pos=[12.5, 5, 23.5], yaw=120),
            step('entity', type='minecraft:sheep', pos=[7.5, 5, 25.5], yaw=70),
            step('wait', ticks=40),
            step('near', pos=[20.5, 5, 24], r=11, timeout=600),
            step('pose', actor='abel', pose=1),
            step('hold', actor='abel', item='minecraft:white_wool'),
            step('pose', actor='cain', pose=1),
            step('hold', actor='cain', item='minecraft:wheat'),
            step('wait', ticks=50),
            step('particles', type='minecraft:campfire_signal_smoke', pos=[11.5, 6.5, 14.5], count=18, spread=0.1, speed=0.04),
            step('particles', type='minecraft:smoke', pos=[29.5, 6.2, 14.5], count=30, spread=0.7, speed=0.005),
            step('wait', ticks=40),
            step('particles', type='minecraft:campfire_signal_smoke', pos=[11.5, 6.5, 14.5], count=18, spread=0.1, speed=0.04),
            step('particles', type='minecraft:smoke', pos=[29.5, 6.2, 14.5], count=30, spread=0.7, speed=0.005),
            step('wait', ticks=40),
            step('voice', key='memory.celestial.brothers.voice', pos=[29.5, 5, 15.5], ticks=90),
            step('hold', actor='cain', item=None),
            step('pose', actor='cain', pose=0),
            step('face', actor='cain', to='abel'),
            step('dim', value=0.45),
            step('say', actor='cain', key='memory.celestial.brothers.cain', ticks=60),
            step('move', actor='cain', to=[17.5, 5, 18.5], speed=0.05),
            step('dim', value=0.85),
            step('particles', type='minecraft:crimson_spore', pos=[11.5, 5.5, 17.5], count=40, spread=0.6),
            step('wait', ticks=50),
            step('despawn', actor='cain'),
            step('despawn', actor='abel'),
            step('end', ticks=40),
        ],
    },
    # S3.4 Скованные: воинство ведёт Стражей в цепях вниз, к Темнице
    'chains': {
        'stage': c('memory/chains'), 'center': [24, 5, 24], 'radius': 23, 'spawn': [20.5, 5, 30.5, 180],
        'sheet': 'chains', 'thought': 'memory.celestial.chains.thought',
        'actors': [
            {'id': 'h1', 'type': 'human', 'skin': 'host', 'pos': [22.5, 10, 7.5], 'yaw': 0},
            {'id': 'w1', 'type': 'human', 'skin': 'watcher', 'pos': [24.5, 10, 8.5], 'yaw': 0},
            {'id': 'w2', 'type': 'human', 'skin': 'watcher', 'pos': [26.5, 10, 8.5], 'yaw': 0},
            {'id': 'w3', 'type': 'human', 'skin': 'watcher', 'pos': [28.5, 10, 8.5], 'yaw': 0},
            {'id': 'h2', 'type': 'human', 'skin': 'host', 'pos': [30.5, 10, 7.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.3),
            step('hold', actor='w1', item='minecraft:chain'),
            step('hold', actor='w2', item='minecraft:chain'),
            step('hold', actor='w3', item='minecraft:chain'),
            step('wait', ticks=40),
            step('caption', key='memory.celestial.chains.1', ticks=90),
            step('move', actor='h1', to=[22.5, 10, 12.5], speed=0.06, wait=False),
            step('move', actor='w1', to=[24.5, 10, 12.5], speed=0.06, wait=False),
            step('move', actor='w2', to=[26.5, 10, 12.5], speed=0.06, wait=False),
            step('move', actor='w3', to=[28.5, 10, 12.5], speed=0.06, wait=False),
            step('move', actor='h2', to=[30.5, 10, 12.5], speed=0.06),
            step('move', actor='h1', to=[22.5, 5, 18.0], speed=0.06, wait=False),
            step('move', actor='w1', to=[24.5, 5, 18.0], speed=0.06, wait=False),
            step('move', actor='w2', to=[26.5, 5, 18.0], speed=0.06, wait=False),
            step('move', actor='w3', to=[28.5, 5, 18.0], speed=0.06, wait=False),
            step('move', actor='h2', to=[30.5, 5, 18.0], speed=0.06),
            step('say', actor='h1', key='memory.celestial.chains.host', ticks=70),
            step('move', actor='h1', to=[26.5, 5, 40.5], speed=0.07, wait=False),
            step('move', actor='w1', to=[26.5, 5, 41.5], speed=0.07, wait=False),
            step('move', actor='w2', to=[26.5, 5, 42.5], speed=0.07, wait=False),
            step('move', actor='w3', to=[26.5, 5, 43.5], speed=0.07, wait=False),
            step('move', actor='h2', to=[27.5, 5, 40.5], speed=0.07),
            step('dim', value=0.6),
            step('face', actor='w3', to='player'),
            step('say', actor='w3', key='memory.celestial.chains.watcher', ticks=80),
            step('end', ticks=40),
        ],
    },
    # S3.5 Потоп: сон в каюте Ковчега; позвать пары зверей, пока открыта дверь; выпустить птицу
    'flood': {
        'stage': c('memory/flood'), 'center': [24, 5, 17], 'radius': 24, 'spawn': [14.5, 5, 17.5, -90],
        'sheet': 'flood', 'thought': 'memory.celestial.flood.thought',
        'actors': [
            {'id': 'noah', 'type': 'human', 'skin': 'noah', 'pos': [28.5, 6, 17.0], 'yaw': 270},
        ],
        'steps': [
            step('dim', value=0.3),
            step('entity', type='minecraft:sheep', pos=[17.5, 5, 9.5], yaw=0),
            step('entity', type='minecraft:sheep', pos=[19.5, 5, 9.5], yaw=0),
            step('entity', type='minecraft:cow', pos=[12.5, 5, 24.5], yaw=180),
            step('entity', type='minecraft:cow', pos=[14.5, 5, 25.5], yaw=180),
            step('entity', type='minecraft:pig', pos=[20.5, 5, 26.0], yaw=180),
            step('entity', type='minecraft:pig', pos=[22.5, 5, 25.0], yaw=180),
            step('entity', type='minecraft:horse', pos=[10.5, 5, 10.5], yaw=0),
            step('entity', type='minecraft:horse', pos=[12.5, 5, 9.5], yaw=0),
            step('particles', type='minecraft:rain', pos=[24, 18, 17], count=300, spread=14, speed=0.0),
            step('caption', key='memory.celestial.flood.1', ticks=80),
            step('say', actor='noah', key='memory.celestial.flood.noah1', ticks=80),
            step('name', n=4, hint='memory.celestial.flood.herd_hint', timeout=1800),
            step('particles', type='minecraft:rain', pos=[24, 18, 17], count=400, spread=14, speed=0.0),
            step('dim', value=0.55),
            step('say', actor='noah', key='memory.celestial.flood.noah2', ticks=70),
            step('hold', actor='noah', item='minecraft:feather'),
            step('choice', actor='noah', key='bird', hint='memory.celestial.flood.bird_hint', timeout=900),
            step('hold', actor='noah', item=None),
            step('particles', type='minecraft:end_rod', pos=[27.5, 8, 17.0], count=40, spread=1.0),
            step('caption', key='memory.celestial.flood.2', ticks=80),
            step('dim', value=0.1),
            step('end', ticks=40),
        ],
    },
    # S3.6 Иния в оковах: Архонт по приказу из темноты запирает её в ледяной нише
    'inia_chained': {
        'stage': c('memory/ice_hall'), 'center': [20, 9, 20], 'radius': 17, 'spawn': [20.5, 9, 34.5, 180],
        'sheet': 'inia', 'thought': 'memory.celestial.inia.thought',
        'actors': [
            {'id': 'archon', 'type': 'human', 'skin': 'archon', 'pos': [20.5, 9, 24.5], 'yaw': 180},
            {'id': 'inia', 'type': 'human', 'skin': 'inia', 'pos': [20.5, 9, 12.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.2),
            step('wait', ticks=50),
            step('near', pos=[20.5, 9, 27], r=9, timeout=700),
            step('face', actor='archon', to='inia'),
            step('say', actor='inia', key='memory.celestial.inia.inia1', ticks=70),
            step('voice', key='memory.celestial.inia.voice', pos=[20.5, 9, 18.0], ticks=90),
            step('pose', actor='archon', pose=1),
            step('particles', type='minecraft:snowflake', pos=[20.5, 10, 12.5], count=120, spread=1.2, speed=0.05),
            step('move', actor='inia', to=[20.5, 9, 6.5], speed=0.05, wait=False),
            step('wait', ticks=40),
            step('lift', **{'from': [15, 0, 8], 'to': [25, 8, 8]}, rise=8, ticks=70),
            step('pose', actor='archon', pose=0),
            step('say', actor='inia', key='memory.celestial.inia.inia2', ticks=80),
            step('dim', value=0.6),
            step('end', ticks=50),
        ],
    },
    # S3.7 Осколки падения: 15–20 секунд глазами побеждённого. Включаются сами после смерти босса (story/ShardsOfTheFall)
    'shard_seraph': {
        'stage': c('memory/seraph_choir'), 'center': [23, 5, 23], 'radius': 22, 'spawn': [23.5, 5, 18.5, 0],
        'sheet': '', 'thought': 'memory.celestial.shard.seraph.thought', 'skippable': True,
        'actors': [
            {'id': 'c1', 'type': 'human', 'skin': 'chorister', 'pos': [17.5, 5, 22.5], 'yaw': 270},
            {'id': 'c2', 'type': 'human', 'skin': 'chorister', 'pos': [29.5, 5, 22.5], 'yaw': 90},
            {'id': 'c3', 'type': 'human', 'skin': 'chorister', 'pos': [23.5, 5, 28.0], 'yaw': 180},
        ],
        'steps': [
            step('caption', key='memory.celestial.shard.seraph.1', ticks=80),
            step('spawn', actor={'id': 'morning', 'type': 'human', 'skin': 'morning_star', 'pos': [23.5, 5, 29.5], 'yaw': 180}),
            step('particles', type='minecraft:end_rod', pos=[23.5, 7, 29.5], count=50, spread=0.8),
            step('move', actor='morning', to=[23.5, 5, 20.5], speed=0.05),
            step('face', actor='morning', to='player'),
            step('say', actor='morning', key='memory.celestial.seraph.morning', ticks=80),
            step('dim', value=0.5),
            step('say', actor='morning', key='memory.celestial.shard.seraph.2', ticks=70),
            step('dim', value=0.8),
            step('end', ticks=30),
        ],
    },
    'shard_devourer': {
        'stage': c('memory/void_star'), 'center': [20, 3, 20], 'radius': 8, 'spawn': [20.5, 3, 20.5, 0],
        'sheet': '', 'thought': 'memory.celestial.shard.devourer.thought', 'skippable': True,
        'actors': [],
        'steps': [
            step('dim', value=0.35),
            step('caption', key='memory.celestial.shard.devourer.1', ticks=80),
            step('spawn', actor={'id': 'morning', 'type': 'human', 'skin': 'morning_star', 'pos': [20.5, 3, 11.5], 'yaw': 0}),
            step('face', actor='morning', to='player'),
            step('say', actor='morning', key='memory.celestial.shard.devourer.2', ticks=70),
            step('stars', ticks=100, every=40, r=3, warn=60),
            step('voice', key='memory.celestial.shard.devourer.voice', pos=[20.5, 3, 20.5], ticks=70),
            step('dim', value=0.9),
            step('end', ticks=30),
        ],
    },
    'shard_archon': {
        'stage': c('memory/ice_hall'), 'center': [20, 9, 20], 'radius': 17, 'spawn': [20.5, 9, 22.5, 180],
        'sheet': 'morning_star', 'thought': 'memory.celestial.shard.archon.thought', 'skippable': True,
        'actors': [
            {'id': 'inia', 'type': 'human', 'skin': 'inia', 'pos': [20.5, 9, 12.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.3),
            step('caption', key='memory.celestial.shard.archon.1', ticks=80),
            step('voice', key='memory.celestial.inia.voice', pos=[20.5, 9, 18.0], ticks=90),
            step('particles', type='minecraft:snowflake', pos=[20.5, 10, 12.5], count=120, spread=1.2, speed=0.05),
            step('move', actor='inia', to=[20.5, 9, 6.5], speed=0.05, wait=False),
            step('wait', ticks=40),
            step('lift', **{'from': [15, 0, 8], 'to': [25, 8, 8]}, rise=8, ticks=70),
            step('say', actor='inia', key='memory.celestial.shard.archon.2', ticks=80),
            step('dim', value=0.85),
            step('end', ticks=30),
        ],
    },
    # S3.8 Сухие кости: пророк говорит — кости поднимаются, и встают ангелы
    'dry_bones': {
        'stage': c('memory/dry_bones'), 'center': [23, 5, 23], 'radius': 21, 'spawn': [23.5, 5, 40.5, 180],
        'sheet': 'dry_bones', 'thought': 'memory.celestial.bones.thought',
        'actors': [
            {'id': 'prophet', 'type': 'human', 'skin': 'prophet', 'pos': [23.5, 5, 23.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.2),
            step('caption', key='memory.celestial.bones.1', ticks=80),
            step('near', pos=[23.5, 5, 30], r=9, timeout=700),
            step('pose', actor='prophet', pose=1),
            step('say', actor='prophet', key='memory.celestial.bones.prophet', ticks=90),
            step('particles', type='minecraft:end_rod', pos=[23.5, 7, 23.5], count=120, spread=10),
            step('lift', **{'from': [0, 5, 0], 'to': [46, 6, 46]}, rise=7, ticks=120),
            step('entity', type=c('angel'), pos=[17.5, 5, 18.5], yaw=0),
            step('entity', type=c('angel'), pos=[29.5, 5, 19.5], yaw=20),
            step('entity', type=c('angel'), pos=[20.5, 5, 29.5], yaw=180),
            step('entity', type=c('angel'), pos=[27.5, 5, 27.5], yaw=200),
            step('pose', actor='prophet', pose=0),
            step('dim', value=0.0),
            step('caption', key='memory.celestial.bones.2', ticks=90),
            step('end', ticks=40),
        ],
    },
    # S3.9 Лестница Иакова: сон на камне; по лестнице света идут ангелы; подняться до вершины
    'jacob_ladder': {
        'stage': c('memory/jacob'), 'center': [34, 5, 20], 'radius': 33, 'spawn': [11.5, 5, 20.5, -90],
        'sheet': 'jacob_ladder', 'thought': 'memory.celestial.jacob.thought',
        'actors': [
            {'id': 'a1', 'type': 'human', 'skin': 'host', 'pos': [26.5, 16, 19.5], 'yaw': 270},
            {'id': 'a2', 'type': 'human', 'skin': 'host', 'pos': [34.5, 24, 20.5], 'yaw': 270},
            {'id': 'a3', 'type': 'human', 'skin': 'host', 'pos': [42.5, 32, 20.5], 'yaw': 90},
            {'id': 'a4', 'type': 'human', 'skin': 'host', 'pos': [30.5, 20, 21.0], 'yaw': 90},
        ],
        'steps': [
            step('fly', on=False),
            step('dim', value=0.3),
            step('caption', key='memory.celestial.jacob.1', ticks=80),
            step('hint', key='memory.celestial.jacob.hint'),
            step('move', actor='a1', to=[44.5, 34, 19.5], speed=0.03, wait=False),
            step('move', actor='a2', to=[18.5, 6, 20.5], speed=0.03, wait=False),
            step('move', actor='a3', to=[22.5, 12, 20.5], speed=0.03, wait=False),
            step('move', actor='a4', to=[50.5, 40, 21.0], speed=0.03, wait=False),
            step('reach', pos=[57.5, 46, 20.5], r=2.5, timeout=3000),
            step('voice', key='memory.celestial.jacob.voice', pos=[57.5, 46, 20.5], ticks=100),
            step('dim', value=0.0),
            step('end', ticks=40),
        ],
    },
}

LANG = {
    'memory.celestial.who.cain': ('Каин', 'Cain'),
    'memory.celestial.who.seraph': ('Серафим', 'The Seraph'),
    'memory.celestial.who.noah': ('Ной', 'Noah'),
    'memory.celestial.who.prophet': ('Пророк', 'The Prophet'),
    'memory.celestial.who.inia': ('Иния', 'Inia'),
    'memory.celestial.who.h1': ('Воитель', 'The Warrior'),
    'memory.celestial.who.w3': ('Страж', 'The Watcher'),
    # Изгнание
    'memory.celestial.exile.voice': ('В поте лица твоего будешь есть хлеб…', 'In the sweat of thy face shalt thou eat bread…'),
    'memory.celestial.exile.eve': ('Там остался свет…', 'The light stayed behind…'),
    'memory.celestial.exile.thought': ('Путь назад — через меч.', 'The way back lies past the sword.'),
    # Серафим до падения
    'memory.celestial.seraph.holy': ('Свят, свят, свят Господь Саваоф!', 'Holy, holy, holy is the LORD of hosts!'),
    'memory.celestial.seraph.sing': ('Свят, свят, свят…', 'Holy, holy, holy…'),
    'memory.celestial.seraph.morning': ('Ты ярче всех.', 'You are brighter than all.'),
    'memory.celestial.seraph.thought': ('Он был одним из первых в хоре.', 'He was among the first of the choir.'),
    'memory.celestial.shard.seraph.1': ('Ты стоишь в хоре и поёшь…', 'You stand in the choir and sing…'),
    'memory.celestial.shard.seraph.2': ('Свет станет твоим.', 'The light shall be yours.'),
    'memory.celestial.shard.seraph.thought': ('Шёпот звучал совсем рядом.', 'The whisper sounded very near.'),
    # Каин и Авель
    'memory.celestial.brothers.voice': ('Отчего поникло лицо твоё?', 'Why is thy countenance fallen?'),
    'memory.celestial.brothers.cain': ('Он снова лучше меня.', 'He is better than I again.'),
    'memory.celestial.brothers.thought': ('От алтарей ведут следы.', 'Tracks lead away from the altars.'),
    # Скованные
    'memory.celestial.chains.1': ('Воинство вело Стражей вниз', 'The host led the Watchers down'),
    'memory.celestial.chains.host': ('Вниз. До великого суда.', 'Down. Until the great judgement.'),
    'memory.celestial.chains.watcher': ('Помни нас.', 'Remember us.'),
    'memory.celestial.chains.thought': ('Вот почему Падшие стражи враждебны.', 'That is why the Fallen Guardians are hostile.'),
    # Потоп
    'memory.celestial.flood.1': ('Дождь шёл, и звери шли к Ковчегу', 'The rain fell, and the beasts came to the Ark'),
    'memory.celestial.flood.noah1': ('Зовите их, пока открыта дверь.', 'Call them while the door is open.'),
    'memory.celestial.flood.herd_hint': ('Присядь и коснись зверя пустой рукой — он пойдёт в Ковчег (%s из %s)',
                                         'Sneak and touch a beast with an empty hand — it will go aboard (%s of %s)'),
    'memory.celestial.flood.noah2': ('Дверь затворена.', 'The door is shut.'),
    'memory.celestial.flood.bird_hint': ('Возьми у Ноя птицу — или отвернись', 'Take the bird from Noah — or turn away'),
    'memory.celestial.choice.bird.taken': ('Ты выпустил голубя. Он вернулся с веткой.', 'You loosed the dove. It returned with a branch.'),
    'memory.celestial.choice.bird.refused': ('Ной выпустил ворона. Он не вернулся.', 'Noah loosed the raven. It did not return.'),
    'memory.celestial.flood.2': ('Вода сошла.', 'The waters were gone.'),
    'memory.celestial.flood.thought': ('Под дождём у Ковчега память возвращается.', 'In the rain beside the Ark memory returns.'),
    # Иния
    'memory.celestial.inia.inia1': ('Я не склонюсь.', 'I will not bow.'),
    'memory.celestial.inia.voice': ('Скуй её.', 'Chain her.'),
    'memory.celestial.inia.inia2': ('Я дождусь.', 'I shall wait.'),
    'memory.celestial.inia.thought': ('Она дождалась.', 'She waited.'),
    'memory.celestial.shard.archon.1': ('Ты — тюремщик, и приказ пришёл из темноты…', 'You are the gaoler, and the order came out of the dark…'),
    'memory.celestial.shard.archon.2': ('Ты не спросил, зачем.', 'You did not ask why.'),
    'memory.celestial.shard.archon.thought': ('Приказы приходили из темноты.', 'The orders came out of the dark.'),
    # Пожиратель
    'memory.celestial.shard.devourer.1': ('Внизу — только голод…', 'Below there is only hunger…'),
    'memory.celestial.shard.devourer.2': ('Возьми первую звезду.', 'Take the first star.'),
    'memory.celestial.shard.devourer.voice': ('Голод.', 'Hunger.'),
    'memory.celestial.shard.devourer.thought': ('Он глотал свет, потому что не имел своего.', 'He swallowed light because he had none of his own.'),
    # Сухие кости
    'memory.celestial.bones.1': ('Долина была полна сухих костей', 'The valley was full of dry bones'),
    'memory.celestial.bones.prophet': ('Кости сухие! Слушайте слово.', 'O ye dry bones, hear the word.'),
    'memory.celestial.bones.2': ('И вошёл в них дух, и они ожили', 'And the breath entered into them, and they lived'),
    'memory.celestial.bones.thought': ('Дыхание света поднимает павших.', 'The breath of light raises the fallen.'),
    # Лестница Иакова
    'memory.celestial.jacob.1': ('Он уснул на камне — и увидел лестницу', 'He slept upon a stone and saw a ladder'),
    'memory.celestial.jacob.hint': ('Поднимись по лестнице света до вершины', 'Climb the ladder of light to the top'),
    'memory.celestial.jacob.voice': ('Вот, Я с тобою.', 'Behold, I am with thee.'),
    'memory.celestial.jacob.thought': ('Небо ближе, чем кажется.', 'The sky is nearer than it seems.'),
}
