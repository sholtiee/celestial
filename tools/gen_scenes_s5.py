"""Отблески S5.6 (книги Странников, Чинов и Откровения): Печь Даниила, Угль Исаии, Семь печатей.

Подключается из gen_scenes.main() так же, как gen_scenes_lore: PEOPLE, stages(), SCENES, LANG.
Якоря стоят в постройках мира: печь — в литейне Тувалкаина (gen_chrono_places.foundry), угль — в святилище Серафимов
(gen_choirs.shrine), печати — на первом ярусе Звёздного алтаря (gen_astral.altar_structure).
Правила: Бог не изображается (только `voice`), четвёртый в печи — ангел (Дан. 3:28: «послал Ангела Своего»), реплики 3–6 слов.
"""
import math
import random

from gen_assets import c
from gen_scenes_lore import AIR, base, step
from gen_structures import island_base

PEOPLE = {
    'youth': ('#d8b088', '#1a1410', '#4a6aa8', '#c8a040', '#3a2a1a', False, False),
    'king': ('#d0a070', '#2a1a10', '#6a2a7a', '#e8c040', '#3a2a1a', False, True),
}

# семь печатей по кругу: (угол, частица, ключ подписи)
SEALS = [
    ('minecraft:end_rod', 'seal1'),
    ('minecraft:flame', 'seal2'),
    ('minecraft:large_smoke', 'seal3'),
    ('minecraft:soul_fire_flame', 'seal4'),
    ('minecraft:soul', 'seal5'),
    ('minecraft:falling_lava', 'seal6'),
    ('minecraft:white_ash', 'seal7'),
]
SEAL_C, SEAL_R, SEAL_TOP = 16, 9, 4


def stage_furnace():
    """Равнина Деира: золотой истукан, возвышение царя, огромная печь из кирпича с жерлом к зрителю."""
    S, TOP = 41, 4
    rng = random.Random(5300)
    t = base(S, 22)
    island_base(t, 20, 20, 19, TOP, 5, rng)
    for x in range(S):
        for z in range(S):
            if t.get(x, TOP, z) == c('golden_grass'):
                t.set(x, TOP, z, 'minecraft:sand' if rng.random() < 0.7 else 'minecraft:sandstone')
    # печь 11×9×8, жерло 5×5 на юг; внутри — раскалённый пол и свет
    x0, z0 = 15, 6
    for x in range(x0, x0 + 11):
        for z in range(z0, z0 + 9):
            for y in range(TOP + 1, TOP + 9):
                shell = x in (x0, x0 + 10) or z in (z0, z0 + 8) or y == TOP + 8
                t.set(x, y, z, 'minecraft:bricks' if shell else AIR)
            t.set(x, TOP, z, 'minecraft:shroomlight' if (x + z) % 2 else 'minecraft:orange_terracotta')
    for x in range(x0 + 3, x0 + 8):
        for y in range(TOP + 1, TOP + 6):
            t.set(x, y, z0 + 8, AIR)
    for x in range(x0 + 2, x0 + 9, 3):
        t.set(x, TOP + 9, z0 + 4, 'minecraft:bricks')
        t.set(x, TOP + 10, z0 + 4, 'minecraft:campfire', lit=True, signal_fire=True, facing='north', waterlogged=False)
    for x in range(x0 + 2, x0 + 9, 2):
        t.set(x, TOP + 3, z0 + 4, 'minecraft:light', level=15, waterlogged=False)
    # золотой истукан (Дан. 3:1) — столп из золота на западе
    t.fill(4, TOP + 1, 10, 6, TOP + 1, 12, 'minecraft:sandstone')
    t.fill(5, TOP + 2, 11, 5, TOP + 14, 11, 'minecraft:gold_block')
    t.set(5, TOP + 15, 11, 'minecraft:gold_block')
    # возвышение царя — на востоке, под навесом
    t.fill(31, TOP + 1, 18, 35, TOP + 1, 22, 'minecraft:smooth_sandstone')
    t.set(33, TOP + 2, 20, 'minecraft:gold_block')
    for x, z in ((31, 18), (35, 18), (31, 22), (35, 22)):
        t.fill(x, TOP + 2, z, x, TOP + 5, z, 'minecraft:cut_sandstone')
    t.fill(31, TOP + 6, 18, 35, TOP + 6, 22, 'minecraft:purple_wool')
    return t.save('memory/furnace')


def stage_temple_coal():
    """Храм, полный дыма: колонны, жертвенник с углями, у входа — коленопреклонённый пророк, над жертвенником — свет (Престол не виден)."""
    S, TOP = 33, 4
    t = base(S, 22)
    cx = 16
    for x in range(3, S - 3):
        for z in range(2, S - 2):
            t.fill(x, TOP - 2, z, x, TOP - 1, z, c('skystone'))
            t.set(x, TOP, z, c('radiant_stone') if (x + z) % 6 == 0 else c('skystone_bricks'))
    for z in range(5, S - 4, 5):
        for x in (6, S - 7):
            t.fill(x, TOP + 1, z, x, TOP + 12, z, c('skystone_bricks'))
            t.set(x, TOP + 13, z, c('radiant_stone'))
    t.fill(cx - 1, TOP + 1, 9, cx + 1, TOP + 2, 11, 'minecraft:polished_blackstone')  # жертвенник
    t.set(cx, TOP + 3, 10, 'minecraft:campfire', lit=True, signal_fire=True, facing='south', waterlogged=False)
    for k, z in enumerate((5, 4, 3)):  # ступени к свету
        t.fill(cx - 4 + k, TOP + 1 + k, z - 1, cx + 4 - k, TOP + 1 + k, z, c('radiant_stone'))
    for x in range(cx - 3, cx + 4):
        for y in range(TOP + 7, TOP + 14):
            for z in range(0, 7):
                d = math.sqrt((x - cx) ** 2 + (y - (TOP + 10)) ** 2 + (z - 3) ** 2)
                if d <= 3.2:
                    t.set(x, y, z, 'minecraft:white_stained_glass' if d > 2.2 else c('radiant_stone'))
    for x in range(5, S - 5, 4):
        for z in range(6, S - 4, 4):
            t.set(x, TOP + 4, z, 'minecraft:light', level=12, waterlogged=False)
    return t.save('memory/temple_coal')


def stage_seals():
    """Звёздная площадка: в центре — свиток на подставке, по кругу — семь печатей-столпов (к каждой надо подойти)."""
    S, TOP = 33, SEAL_TOP
    t = base(S, 16)
    cx = SEAL_C
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - cx, z - cx)
            if d <= 14:
                t.fill(x, TOP - 2, z, x, TOP - 1, z, c('astral_rock'))
                t.set(x, TOP, z, c('astral_bricks') if int(d) % 3 else c('star_stone_block'))
    t.set(cx, TOP + 1, cx, 'minecraft:lectern', facing='south', has_book=True, powered=False)
    for i, pos in enumerate(seal_points()):
        x, z = int(pos[0]), int(pos[2])
        t.fill(x, TOP + 1, z, x, TOP + 2, z, c('star_stone_block'))
        t.set(x, TOP + 3, z, 'minecraft:light', level=12, waterlogged=False)
    return t.save('memory/seals')


def seal_points():
    pts = []
    for i in range(7):
        a = -math.pi / 2 + i * 2 * math.pi / 7
        pts.append([SEAL_C + round(math.cos(a) * SEAL_R) + 0.5, SEAL_TOP + 1, SEAL_C + round(math.sin(a) * SEAL_R) + 0.5])
    return pts


def stages():
    stage_furnace()
    stage_temple_coal()
    stage_seals()


def seal_steps():
    out = [step('dim', value=0.4), step('caption', key='memory.celestial.seals.1', ticks=80), step('hint', key='memory.celestial.seals.hint')]
    for (particle, key), pos in zip(SEALS, seal_points()):
        out.append(step('near', pos=[pos[0], pos[1], pos[2] + (1.5 if pos[2] < SEAL_C else -1.5)], r=2.2, timeout=1600))
        out.append(step('particles', type=particle, pos=[pos[0], pos[1] + 2, pos[2]], count=60, spread=1.2, speed=0.03))
        if key == 'seal6':
            out.append(step('stars', ticks=80, every=40, r=3, warn=50))
        out.append(step('caption', key='memory.celestial.' + key, ticks=70))
    out += [step('dim', value=0.9), step('caption', key='memory.celestial.seals.silence', ticks=100), step('dim', value=0.0), step('end', ticks=40)]
    return out


SCENES = {
    # S5.6 Печь: три отрока не поклонились истукану; в огне с ними ходит четвёртый
    'fiery_furnace': {
        'stage': c('memory/furnace'), 'center': [20, 5, 18], 'radius': 22, 'spawn': [20.5, 5, 32.5, 180],
        'sheet': 'fiery_furnace', 'thought': 'memory.celestial.furnace.thought',
        'actors': [
            {'id': 'king', 'type': 'human', 'skin': 'king', 'pos': [33.5, 6, 20.5], 'yaw': 90},
            {'id': 'y1', 'type': 'human', 'skin': 'youth', 'pos': [18.5, 5, 22.5], 'yaw': 0},
            {'id': 'y2', 'type': 'human', 'skin': 'youth', 'pos': [20.5, 5, 22.5], 'yaw': 0},
            {'id': 'y3', 'type': 'human', 'skin': 'youth', 'pos': [22.5, 5, 22.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.3),
            step('caption', key='memory.celestial.furnace.1', ticks=80),
            step('say', actor='king', key='memory.celestial.furnace.king1', ticks=80),
            step('face', actor='y1', to='king'),
            step('say', actor='y1', key='memory.celestial.furnace.youth', ticks=80),
            step('particles', type='minecraft:flame', pos=[20.5, 7, 10.5], count=200, spread=3, speed=0.05),
            step('caption', key='memory.celestial.furnace.2', ticks=60),
            step('move', actor='y1', to=[18.5, 5, 10.5], speed=0.06, wait=False),
            step('move', actor='y2', to=[20.5, 5, 9.5], speed=0.06, wait=False),
            step('move', actor='y3', to=[22.5, 5, 10.5], speed=0.06),
            step('particles', type='minecraft:flame', pos=[20.5, 6, 10.5], count=240, spread=3, speed=0.08),
            step('spawn', actor={'id': 'fourth', 'type': 'human', 'skin': 'host', 'pos': [19.5, 5, 12.5], 'yaw': 180}),
            step('particles', type='minecraft:end_rod', pos=[19.5, 6, 12.5], count=80, spread=1, speed=0.05),
            step('look', actor='fourth', r=26, timeout=900),
            step('say', actor='king', key='memory.celestial.furnace.king2', ticks=90),
            step('move', actor='y1', to=[18.5, 5, 19.5], speed=0.05, wait=False),
            step('move', actor='y2', to=[20.5, 5, 19.5], speed=0.05, wait=False),
            step('move', actor='y3', to=[22.5, 5, 19.5], speed=0.05),
            step('despawn', actor='fourth'),
            step('caption', key='memory.celestial.furnace.3', ticks=90),
            step('dim', value=0.0),
            step('end', ticks=40),
        ],
    },
    # S5.6 Угль: храм в дыму, «Свят, свят, свят»; серафим касается углём уст пророка; «Вот я, пошли меня»
    'seraph_coal': {
        'stage': c('memory/temple_coal'), 'center': [16, 5, 14], 'radius': 18, 'spawn': [16.5, 5, 27.5, 180],
        'sheet': 'seraph_coal', 'thought': 'memory.celestial.coal.thought',
        'actors': [
            {'id': 'prophet', 'type': 'human', 'skin': 'prophet', 'pos': [16.5, 5, 18.5], 'yaw': 180, 'pose': 4},
            {'id': 'seraph', 'type': 'human', 'skin': 'seraph', 'pos': [16.5, 8, 6.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.35),
            step('caption', key='memory.celestial.coal.1', ticks=80),
            step('particles', type='minecraft:campfire_cosy_smoke', pos=[16.5, 7, 12.5], count=60, spread=6, speed=0.01),
            step('say', actor='seraph', key='memory.celestial.seraph.holy', ticks=90),
            step('near', pos=[16.5, 5, 21.5], r=3.5, timeout=900),
            step('face', actor='prophet', to='seraph'),
            step('say', actor='prophet', key='memory.celestial.coal.woe', ticks=80),
            step('hold', actor='seraph', item='minecraft:fire_charge'),
            step('move', actor='seraph', to=[16.5, 5, 17.0], speed=0.05),
            step('face', actor='seraph', to='prophet'),
            step('particles', type='minecraft:flame', pos=[16.5, 6.6, 18.2], count=40, spread=0.2, speed=0.02),
            step('say', actor='seraph', key='memory.celestial.coal.touch', ticks=80),
            step('hold', actor='seraph', item=None),
            step('voice', key='memory.celestial.coal.voice', pos=[16.5, 13, 3.5], ticks=90),
            step('look', actor='prophet', timeout=600),
            step('pose', actor='prophet', pose=0),
            step('say', actor='prophet', key='memory.celestial.coal.send', ticks=90),
            step('dim', value=0.0),
            step('end', ticks=40),
        ],
    },
    # S5.6 Семь печатей: подойти к каждой печати по кругу; на седьмой — безмолвие
    'seven_seals': {
        'stage': c('memory/seals'), 'center': [SEAL_C, 5, SEAL_C], 'radius': 15, 'spawn': [SEAL_C + 0.5, 5, SEAL_C + 3.5, 180],
        'sheet': 'seven_seals', 'thought': 'memory.celestial.seals.thought',
        'actors': [],
        'steps': seal_steps(),
    },
}

LANG = {
    'memory.celestial.who.king': ('Царь', 'The King'),
    'memory.celestial.who.y1': ('Отрок', 'The Youth'),
    'memory.celestial.who.y2': ('Отрок', 'The Youth'),
    'memory.celestial.who.y3': ('Отрок', 'The Youth'),
    'memory.celestial.who.fourth': ('Четвёртый', 'The Fourth'),
    # Печь
    'memory.celestial.furnace.1': ('Царь велел поклониться золотому истукану', 'The king commanded all to bow to the golden image'),
    'memory.celestial.furnace.king1': ('Поклонитесь — или в печь!', 'Bow — or into the furnace!'),
    'memory.celestial.furnace.youth': ('Мы не поклонимся.', 'We will not bow.'),
    'memory.celestial.furnace.2': ('Печь раскалили всемеро', 'The furnace was heated seven times over'),
    'memory.celestial.furnace.king2': ('Я вижу в огне четверых!', 'I see four in the fire!'),
    'memory.celestial.furnace.3': ('Огонь не тронул даже их волос', 'The fire had not singed a single hair'),
    'memory.celestial.furnace.thought': ('Свет ходит и в огне.', 'Light walks in the fire too.'),
    # Угль
    'memory.celestial.coal.1': ('Храм наполнился дымом', 'The house was filled with smoke'),
    'memory.celestial.coal.woe': ('Горе мне! Я погиб.', 'Woe is me! I am undone.'),
    'memory.celestial.coal.touch': ('Вина твоя снята.', 'Thine iniquity is taken away.'),
    'memory.celestial.coal.voice': ('Кого Мне послать?', 'Whom shall I send?'),
    'memory.celestial.coal.send': ('Вот я, пошли меня.', 'Here am I; send me.'),
    'memory.celestial.coal.thought': ('Огонь серафимов не губит — очищает.', 'The fire of the seraphim does not destroy — it cleanses.'),
    # Печати
    'memory.celestial.seals.1': ('Книга, запечатанная семью печатями', 'A book sealed with seven seals'),
    'memory.celestial.seals.hint': ('Подойди к каждой печати по кругу', 'Go to each seal in turn around the circle'),
    'memory.celestial.seal1': ('Первая печать: белый свет — и победа', 'The first seal: a white light — and victory'),
    'memory.celestial.seal2': ('Вторая: огонь — и мира не стало', 'The second: fire — and peace was taken'),
    'memory.celestial.seal3': ('Третья: чёрный дым — и весы', 'The third: black smoke — and a balance'),
    'memory.celestial.seal4': ('Четвёртая: бледный огонь', 'The fourth: a pale fire'),
    'memory.celestial.seal5': ('Пятая: души под жертвенником', 'The fifth: souls beneath the altar'),
    'memory.celestial.seal6': ('Шестая: звёзды падают на землю', 'The sixth: the stars fall to the earth'),
    'memory.celestial.seal7': ('Седьмая…', 'The seventh…'),
    'memory.celestial.seals.silence': ('…и сделалось безмолвие на небе', '…and there was silence in heaven'),
    'memory.celestial.seals.thought': ('После безмолвия будут трубы.', 'After the silence come the trumpets.'),
}
