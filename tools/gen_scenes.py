"""Отблески — воспоминания на ходу (docs/LORE.md §5c): измерение памяти, облики актёров, Отпечаток света, сцены и их данные.

Сцена = шаблон-остров в измерении `celestial:memory` + таймлайн шагов (Java: dev.celestial.memory.Memories). Координаты в сценах —
относительно угла шаблона. Первая (эталонная) сцена — «Плод» у Древа Познания; новые сцены добавляй по её образцу:
функция-шаблон `stage_<id>()` + запись в SCENES + переводы в LANG (см. AGENTS.md «Как сделать новую сцену»).
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

import mob_textures as M
import textures as T
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, write_json
from gen_story import lang_patch
from gen_structures import Template, island_base
from textures import hexrgb as rgb, mix, shade

AIR = 'minecraft:air'
WHITE = (255, 255, 255)


# ------------------------------------------------------------------ измерение памяти: пустота, вечный тёплый свет, без облаков и суток
def dimension():
    write_json(os.path.join(DATA, 'dimension_type/memory.json'), {
        'ambient_light': 0.55,
        'attributes': {
            'minecraft:visual/sky_color': '#f6dfae',
            'minecraft:visual/fog_color': '#fbe9c6',
            'minecraft:visual/cloud_height': 400.0,
            'minecraft:visual/ambient_light_color': '#3a3020',
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'never', 'can_sleep': 'never', 'destroy_on_use': False},
            'minecraft:gameplay/respawn_anchor_works': False,
        },
        'coordinate_scale': 1.0, 'default_clock': 'minecraft:overworld', 'has_ceiling': False, 'has_ender_dragon_fight': False,
        'has_fixed_time': True, 'has_skylight': True, 'height': 256, 'infiniburn': '#minecraft:infiniburn_overworld', 'logical_height': 256,
        'min_y': 0, 'monster_spawn_block_light_limit': 0, 'monster_spawn_light_level': 0, 'timelines': '#celestial:in_memory'})
    write_json(os.path.join(DATA, 'tags/timeline/in_memory.json'), {'values': []})
    write_json(os.path.join(DATA, 'worldgen/biome/memory.json'), {
        'attributes': {'minecraft:visual/sky_color': '#f6dfae', 'minecraft:visual/fog_color': '#fbe9c6', 'minecraft:visual/water_fog_color': '#a8d8f0'},
        'carvers': [], 'downfall': 0.0, 'effects': {'grass_color': '#c8d860', 'foliage_color': '#9ac850', 'water_color': '#7fc8ff'},
        'features': [], 'has_precipitation': False, 'temperature': 0.8})
    write_json(os.path.join(DATA, 'dimension/memory.json'), {
        'type': c('memory'),
        'generator': {'type': 'minecraft:flat', 'settings': {'biome': c('memory'), 'features': False, 'lakes': False, 'layers': []}}})


# ------------------------------------------------------------------ облики актёров (развёртка HeavenModels.Mortal 64×64)
PEOPLE = {
    # облик: кожа, волосы, одеяние, отделка, глаза, длинные волосы, борода
    'adam': ('#e2b48c', '#6a4426', '#efe6cf', '#c9a24a', '#5a8ac8', False, True),
    'eve': ('#ecc29e', '#a8642c', '#f4ecd8', '#9ac46a', '#4a9a6a', True, False),
    'morning_star': ('#fff1d8', '#fff8e6', '#fff6d0', '#f2c24a', '#ffd84a', True, False),  # Денница: сияющий, до падения
}


def mortal(skin, hair, robe, trim, eye, long_hair, beard, name):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = T.rng_for('memory_' + name)
    skin, hair, robe, trim, eye = map(rgb, (skin, hair, robe, trim, eye))

    def cloth(base, x, y):
        col = M.noise_color(r, base, 0.05)
        return shade(col, 0.9) if x % 3 == 2 else col

    def head(face, x, y, fw, fh):
        if face == 'top' or face == 'back' or (face in ('left', 'right') and (y < 3 or x >= 5)):
            return M.noise_color(r, hair if (x + y) % 4 else shade(hair, 0.85), 0.06)
        if face == 'front':
            if y < 2:
                return M.noise_color(r, hair, 0.06)
            if y == 4 and x in (2, 5):
                return eye
            if y == 4 and x in (1, 6):
                return WHITE
            if beard and y >= 6:
                return M.noise_color(r, hair, 0.08)  # борода
            if not beard and y == 6 and 3 <= x <= 4:
                return rgb('#c88a78')
        if beard and face in ('left', 'right') and y >= 6 and x <= 3:
            return M.noise_color(r, hair, 0.08)
        return M.noise_color(r, skin, 0.03)

    def hair_back(face, x, y, fw, fh):
        if not long_hair:
            return None
        if face in ('front', 'back') or y < fh - 1:
            return M.noise_color(r, hair if (x + y) % 3 else shade(hair, 0.85), 0.06)
        return None

    def body(face, x, y, fw, fh):
        if y == 7:
            return trim  # пояс
        if face == 'top' and 2 <= x <= 5:
            return skin
        return cloth(robe, x, y)

    def arm(face, x, y, fw, fh):
        if face == 'bottom' or (face != 'top' and y >= fh - 3):
            return M.noise_color(r, skin, 0.03)  # открытые кисти и запястья
        return cloth(robe, x, y)

    def skirt(face, x, y, fw, fh):
        if face == 'bottom':
            return shade(robe, 0.6)
        if face != 'top' and y >= fh - 1:
            return trim
        if face != 'top' and y >= fh - 3:
            return M.noise_color(r, skin, 0.03)  # босые ноги из-под подола
        return cloth(robe, x, y)

    M.paint_box(img, 0, 0, 8, 8, 8, head)
    M.paint_box(img, 32, 0, 8, 12, 1, hair_back)
    M.paint_box(img, 16, 16, 8, 10, 4, body)
    M.paint_box(img, 40, 16, 3, 11, 3, arm)
    M.paint_box(img, 0, 32, 10, 14, 6, skirt)
    return img


def serpent_texture():
    """Змей Сада: та же развёртка, что у Крылатого змея (HeavenModels.Serpent), но тёмно-зелёная чешуя с золотым узором и красные глаза."""
    import gen_heaven_mobs
    base, glow = gen_heaven_mobs.serpent()
    out = Image.new('RGBA', base.size, (0, 0, 0, 0))
    src, dst = base.load(), out.load()
    for y in range(base.height):
        for x in range(base.width):
            p = src[x, y]
            if p[3] == 0:
                continue
            rr, gg, bb = p[:3]
            if rr > 240 and gg < 120:
                dst[x, y] = p  # глаза
                continue
            lum = (rr * 0.3 + gg * 0.59 + bb * 0.11) / 255
            green = mix(rgb('#1f3a1c'), rgb('#5a8a2a'), lum)
            if (x + y) % 7 == 0 and lum > 0.55:
                green = mix(green, rgb('#d4a843'), 0.5)  # золотые искры по чешуе
            dst[x, y] = (*green, p[3])
    return out, glow


def actors():
    for name, args in PEOPLE.items():
        save_png(mortal(*args, name), 'entity/memory_' + name)
    save_png(Image.new('RGBA', (64, 64), (0, 0, 0, 0)), 'entity/memory_human_glow')
    tex, glow = serpent_texture()
    save_png(tex, 'entity/memory_serpent')
    save_png(glow, 'entity/memory_serpent_glow')


# ------------------------------------------------------------------ Отпечаток света: трещина света, мерцает
def anchor_block():
    frames = 10
    sheet = Image.new('RGBA', (16, 16 * frames), (0, 0, 0, 0))
    for f in range(frames):
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rf = random.Random(91 + f)
        pulse = 0.6 + 0.4 * math.sin(f / frames * 2 * math.pi)
        x = 8
        pts = []
        for y in range(1, 16):  # зигзаг трещины
            x = max(5, min(10, x + rf.choice([-1, 0, 0, 1])))
            pts.append((x, y))
        for (x, y) in pts:
            for dx in (-2, -1, 1, 2):
                a = int((90 if abs(dx) == 1 else 40) * pulse)
                img.putpixel((x + dx, y), (255, 226, 150, a))
        for (x, y) in pts:
            img.putpixel((x, y), (255, 250, 228, 255))
        for _ in range(4):  # искры
            px, py = rf.randrange(2, 14), rf.randrange(1, 15)
            img.putpixel((px, py), (255, 240, 190, int(200 * pulse)))
        sheet.paste(img, (0, 16 * f))
    save_png(sheet, 'block/memory_anchor')
    with open(os.path.join(ASSETS, 'textures/block/memory_anchor.png.mcmeta'), 'w') as fh:
        json.dump({'animation': {'frametime': 2, 'interpolate': True}}, fh)
    model('block/memory_anchor', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/memory_anchor')}})
    blockstate('memory_anchor', {'variants': {'': {'model': c('block/memory_anchor')}}})
    model('item/memory_anchor', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/memory_anchor')}})
    item_def('memory_anchor', c('item/memory_anchor'))


# ------------------------------------------------------------------ сцены-острова
def light_canopy(t, rng, cells, leaves_set, n):
    for _ in range(n):
        x, y, z = rng.choice(cells)
        if t.get(x, y, z) in leaves_set:
            t.set(x, y, z, 'minecraft:light', level=13, waterlogged=False)


def stage_fruit():
    """Сад до Изгнания: цветущая поляна, здоровое Древо Познания с плодами, Змей на ветви, Адам у пруда, смоковница, вдали — Восточные врата."""
    S, TOP = 41, 4
    rng = random.Random(5150)
    t = Template(S, 26, S)
    t.fill(0, 0, 0, S - 1, 25, S - 1, AIR)
    island_base(t, 20, 20, 19, TOP, 6, rng)
    flowers = ['sunbell', 'dawn_poppy', 'starflower', 'golden_tuft', 'golden_tuft', 'tall_golden_grass']
    for _ in range(420):
        x, z = rng.randrange(1, S - 1), rng.randrange(1, S - 1)
        if t.get(x, TOP, z) == c('golden_grass') and t.get(x, TOP + 1, z) in (None, AIR):
            f = rng.choice(flowers)
            if f == 'tall_golden_grass':
                continue
            t.set(x, TOP + 1, z, c(f))
    for x in range(28, 36):  # пруд Адама
        for z in range(15, 26):
            if math.hypot(x - 32, (z - 20) * 0.8) <= 3.6:
                t.set(x, TOP, z, 'minecraft:water', level=0)
    # Древо Познания — здоровое, раскидистое, с яркими плодами (в настоящем оно заросло терновником)
    tx, tz = 20, 16
    wood, leaves = 'minecraft:oak_wood', 'minecraft:oak_leaves'
    for y in range(TOP + 1, TOP + 8):
        for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
            t.set(tx + dx, y, tz + dz, wood, axis='y')
    crown = []
    for x in range(tx - 6, tx + 8):
        for y in range(TOP + 6, TOP + 13):
            for z in range(tz - 6, tz + 8):
                d = ((x - tx - 0.5) / 6.5) ** 2 + ((y - TOP - 9) / 3.4) ** 2 + ((z - tz - 0.5) / 6.5) ** 2
                if d <= 1.0 and rng.random() > 0.08 and t.get(x, y, z) in (None, AIR):
                    t.set(x, y, z, leaves, distance=1, persistent=True, waterlogged=False)
                    crown.append((x, y, z))
    for dx, dz in ((-1, 0), (2, 1), (0, -1), (1, 2)):  # толстые сучья под кроной
        for k in range(1, 4):
            t.set(tx + dx * k if dx else tx, TOP + 6 + k // 2, tz + dz * k if dz else tz, wood, axis='y')
    light_canopy(t, rng, crown, {leaves}, 10)
    placed = 0
    for _ in range(400):
        x, y, z = rng.choice(crown)
        if t.get(x, y, z) == leaves and t.get(x, y - 1, z) in (None, AIR) and y - 1 > TOP + 4:
            t.set(x, y - 1, z, c('knowledge_fruit'), ripe=True)
            placed += 1
        if placed >= 9:
            break
    # смоковница — там, где они спрячутся
    for x, z in ((30, 27), (32, 27), (31, 28), (29, 26), (33, 26), (31, 26)):
        t.set(x, TOP + 1, z, c('fig_bush'))
    # дорожка света к Восточным вратам и сами врата вдали
    for x in range(22, 39):
        t.set(x, TOP, 21, c('skystone_bricks') if x % 2 else c('radiant_stone'))
    for z in (17, 25):
        t.fill(38, TOP + 1, z, 38, TOP + 8, z, c('eden_wall'))
    t.fill(38, TOP + 8, 17, 38, TOP + 8, 25, c('eden_wall'))
    t.set(38, TOP + 9, 21, c('sky_crystal'), facing='up', waterlogged=False)
    return t.save('memory/fruit')


def stage_prologue_light():
    """Свет: пустота, девять колец хоров вокруг Престола под покровом (сияющая сфера; самого Престола не видно). Странник летит к свету."""
    S, C = 61, 30
    t = Template(S, S, S)
    t.fill(0, 0, 0, S - 1, S - 1, S - 1, AIR)
    mats = [c('radiant_stone'), 'minecraft:white_stained_glass', c('sky_crystal_block'), 'minecraft:gold_block']
    for k in range(9):  # девять хоров: кольца разной высоты, проём там, где летит странник (юг)
        r = 5 + 3 * k
        y = C + (2 if k % 2 else -2) * (k % 3)
        n = int(2 * math.pi * r * 1.2)
        for i in range(n):
            a = i / n * 2 * math.pi
            if abs(math.atan2(math.cos(a), math.sin(a))) < 0.18:  # проём на юге (направление +z)
                continue
            x, z = round(C + math.cos(a) * r), round(C + math.sin(a) * r)
            t.set(x, y, z, mats[k % len(mats)] if (i + k) % 5 else 'minecraft:light', **({'level': 15, 'waterlogged': False} if (i + k) % 5 == 0 else {}))
    for x in range(C - 4, C + 5):  # покров Престола: светящаяся сфера
        for y in range(C - 4, C + 5):
            for z in range(C - 4, C + 5):
                d = math.sqrt((x - C) ** 2 + (y - C) ** 2 + (z - C) ** 2)
                if d <= 3.6:
                    t.set(x, y, z, 'minecraft:white_stained_glass' if d > 2.6 else c('radiant_stone'))
    return t.save('memory/prologue_light')


def stage_prologue_exile():
    """Изгнание: голая земля за вратами, трещина, а впереди — малый остров Сада, который поднимут в небо (шаг lift)."""
    S, TOP = 41, 4
    rng = random.Random(5260)
    t = Template(S, 30, S)
    t.fill(0, 0, 0, S - 1, 29, S - 1, AIR)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 20, z - 24)
            if d <= 18 and not (abs(z - 15) <= 1 and d > 3):  # голая земля; трещина отделяет Сад
                for y in range(0, TOP + 1):
                    if y >= TOP - rng.randint(1, 3) or d < 14:
                        t.set(x, y, z, rng.choice(['minecraft:coarse_dirt', 'minecraft:gravel', 'minecraft:dirt', 'minecraft:coarse_dirt']) if y == TOP else 'minecraft:dirt')
    for _ in range(40):
        x, z = rng.randrange(4, 37), rng.randrange(17, 38)
        if t.get(x, TOP, z) not in (None, AIR) and t.get(x, TOP + 1, z) in (None, AIR):
            t.set(x, TOP + 1, z, 'minecraft:dead_bush')
    # малый Сад: остров золотой травы с деревцем и цветами (z 4..14)
    for x in range(12, 29):
        for z in range(3, 15):
            d = math.hypot(x - 20, (z - 9) * 1.1)
            if d <= 6.5:
                depth = max(1, int(5 - d * 0.6))
                for y in range(TOP - depth, TOP):
                    t.set(x, y, z, c('heaven_dirt'))
                t.set(x, TOP, z, c('golden_grass'))
                if rng.random() < 0.35:
                    t.set(x, TOP + 1, z, c(rng.choice(['sunbell', 'dawn_poppy', 'starflower', 'golden_tuft'])))
    for y in range(TOP + 1, TOP + 6):
        t.set(20, y, 9, c('skywood_log'), axis='y')
    for x in range(17, 24):
        for y in range(TOP + 5, TOP + 9):
            for z in range(6, 13):
                if (x - 20) ** 2 / 9 + (y - TOP - 7) ** 2 / 3 + (z - 9) ** 2 / 9 <= 1.0:
                    t.set(x, y, z, c('skywood_leaves'))
    t.set(20, TOP + 4, 10, 'minecraft:light', level=12, waterlogged=False)
    return t.save('memory/prologue_exile')


# ------------------------------------------------------------------ данные сцен
def step(t, **kw):
    return {'t': t, **kw}


PROLOGUE = {
    # 1. Свет: полёт сквозь хоры к Престолу; Денница смотрит на странника и уходит — падают звёзды
    'prologue_light': {
        'stage': c('memory/prologue_light'), 'center': [30, 30, 30], 'radius': 36, 'spawn': [30.5, 30, 60.0, 180],
        'sheet': 'light', 'thought': '', 'next': 'prologue_garden', 'skippable': True,
        'actors': [],
        'steps': [
            step('fly', on=True),
            step('caption', key='memory.celestial.prologue.light1', ticks=80),
            step('hint', key='memory.celestial.prologue.fly_hint'),
            step('near', pos=[30.5, 30, 37], r=6, timeout=900),
            step('caption', key='memory.celestial.prologue.light2', ticks=70),
            step('spawn', actor={'id': 'morning', 'type': 'human', 'skin': 'morning_star', 'pos': [30.5, 29, 34.5], 'yaw': 0}),
            step('particles', type='minecraft:end_rod', pos=[30.5, 30.5, 34.5], count=60, spread=0.8),
            step('face', actor='morning', to='player'),
            step('wait', ticks=40),
            step('say', actor='morning', key='memory.celestial.prologue.morning', ticks=70),
            step('dim', value=0.75),
            step('move', actor='morning', to=[30.5, 0, 6], speed=0.35, wait=False),
            step('caption', key='memory.celestial.prologue.fall', ticks=40),
            step('hint', key='memory.celestial.prologue.dodge_hint'),
            step('stars', ticks=320, every=9, r=6),
            step('despawn', actor='morning'),
            step('caption', key='memory.celestial.prologue.fall2', ticks=60),
            step('end', ticks=10),
        ],
    },
    # 2. Сад: имена зверям, Древа, выбор у Змея, Ева берёт плод, Херувим — бегство к вратам
    'prologue_garden': {
        'stage': c('memory/fruit'), 'center': [20, 5, 20], 'radius': 21, 'spawn': [12.5, 5, 33.5, 180],
        'sheet': 'eden', 'thought': '', 'next': 'prologue_exile', 'skippable': True,
        'actors': [
            {'id': 'adam', 'type': 'human', 'skin': 'adam', 'pos': [13.5, 5, 27.5], 'yaw': 0},
            {'id': 'eve', 'type': 'human', 'skin': 'eve', 'pos': [24.5, 5, 25.5], 'yaw': 150},
            {'id': 'serpent', 'type': 'serpent', 'skin': 'serpent', 'pos': [20.9, 7.6, 18.4], 'yaw': 20, 'pose': 3},
        ],
        'steps': [
            step('fly', on=False),
            step('caption', key='memory.celestial.prologue.garden1', ticks=70),
            step('entity', type=c('golden_ram'), pos=[10.5, 5, 30.5], yaw=90),
            step('entity', type=c('pegasus'), pos=[16.5, 5, 31.5], yaw=200),
            step('entity', type=c('light_wisp'), pos=[9.5, 6.5, 25.5], yaw=0, nogravity=True),
            step('entity', type=c('cherub'), pos=[15.5, 6.5, 24.5], yaw=160, nogravity=True),
            step('face', actor='adam', to='player'),
            step('say', actor='adam', key='memory.celestial.prologue.adam1', ticks=70),
            step('name', n=3, hint='memory.celestial.prologue.name_hint', timeout=1600),
            step('say', actor='adam', key='memory.celestial.prologue.adam2', ticks=60),
            step('move', actor='eve', to=[19.5, 5, 21.0], speed=0.08, wait=False),
            step('caption', key='memory.celestial.prologue.trees', ticks=70),
            step('near', pos=[20.5, 5, 22.5], r=7, timeout=900),
            step('face', actor='serpent', to='player'),
            step('say', actor='serpent', key='memory.celestial.prologue.serpent', ticks=60),
            step('choice', actor='serpent', key='fruit', hint='memory.celestial.prologue.choice_hint', timeout=900),
            step('face', actor='eve', to='serpent'),
            step('pose', actor='eve', pose=1),
            step('hold', actor='eve', item=c('knowledge_fruit')),
            step('wait', ticks=30),
            step('pose', actor='eve', pose=2),
            step('wait', ticks=30),
            step('hold', actor='eve', item=None),
            step('pose', actor='eve', pose=0),
            step('dim', value=0.5),
            step('particles', type='minecraft:white_ash', pos=[20, 12, 16], count=160, spread=5),
            step('wait', ticks=30),
            step('entity', type=c('gate_cherub'), pos=[32.5, 5, 21.5], yaw=90),
            step('caption', key='memory.celestial.prologue.run', ticks=20),
            step('hint', key='memory.celestial.prologue.run_hint'),
            step('reach', pos=[38.5, 5, 21.5], r=1.8, sweep={'center': [32.5, 5, 21.5], 'radius': 6.5}, timeout=1600),
            step('end', ticks=10),
        ],
    },
    # 3. Изгнание: голая земля, Сад поднимается в небо
    'prologue_exile': {
        'stage': c('memory/prologue_exile'), 'center': [20, 5, 26], 'radius': 15, 'spawn': [20.5, 5, 34.5, 180],
        'sheet': '', 'thought': '', 'on_complete': 'prologue_wake', 'skippable': True,
        'actors': [],
        'steps': [
            step('dim', value=0.35),
            step('caption', key='memory.celestial.prologue.exile1', ticks=70),
            step('wait', ticks=20),
            step('particles', type='minecraft:end_rod', pos=[20, 6, 9], count=80, spread=4),
            step('lift', **{'from': [11, 0, 2], 'to': [29, 14, 15]}, rise=45, ticks=240),
            step('caption', key='memory.celestial.prologue.exile2', ticks=80),
            step('caption', key='memory.celestial.prologue.exile3', ticks=80),
            step('end', ticks=20),
        ],
    },
}

SCENES = {
    'fruit': {
        'stage': c('memory/fruit'), 'center': [20, 5, 20], 'radius': 17.5, 'spawn': [20.5, 5, 35.5, 180],
        'sheet': 'fruit', 'thought': 'memory.celestial.fruit.thought', 'on_complete': 'part_thorns',
        'actors': [
            {'id': 'eve', 'type': 'human', 'skin': 'eve', 'pos': [11.5, 5, 24.5], 'yaw': 210},
            {'id': 'adam', 'type': 'human', 'skin': 'adam', 'pos': [27.5, 5, 23.5], 'yaw': 120},
            {'id': 'serpent', 'type': 'serpent', 'skin': 'serpent', 'pos': [20.9, 7.6, 18.4], 'yaw': 20, 'pose': 3},  # обвил ствол с южной стороны, на виду
        ],
        'steps': [
            step('wait', ticks=40),
            step('near', pos=[20.5, 5, 23], r=10, timeout=500),          # странник подошёл к Древу
            step('move', actor='eve', to=[18.5, 5, 19.5], speed=0.07),
            step('face', actor='eve', to='serpent'),
            step('face', actor='serpent', to='eve'),
            step('say', actor='serpent', key='memory.celestial.fruit.serpent', ticks=80),
            step('look', actor='eve', r=18, timeout=300),                 # Ева ждёт, пока странник посмотрит на неё
            step('pose', actor='eve', pose=1),
            step('hold', actor='eve', item=c('knowledge_fruit')),
            step('particles', type='minecraft:end_rod', pos=[19, 7, 18.5], count=14, spread=0.4),
            step('wait', ticks=40),
            step('move', actor='eve', to=[25.5, 5, 22.5], speed=0.08),
            step('face', actor='eve', to='adam'),
            step('face', actor='adam', to='eve'),
            step('pose', actor='adam', pose=1),
            step('hold', actor='adam', item=c('knowledge_fruit')),
            step('wait', ticks=25),
            step('pose', actor='eve', pose=2),
            step('pose', actor='adam', pose=2),
            step('wait', ticks=45),
            step('hold', actor='eve', item=None),
            step('hold', actor='adam', item=None),
            step('pose', actor='eve', pose=0),
            step('pose', actor='adam', pose=0),
            step('dim', value=0.55),                                       # свет меркнет
            step('particles', type='minecraft:white_ash', pos=[20, 12, 16], count=160, spread=5),
            step('wait', ticks=50),
            step('move', actor='eve', to=[30.5, 5, 25.5], speed=0.11, wait=False),
            step('move', actor='adam', to=[32.5, 5, 25.5], speed=0.11),
            step('pose', actor='eve', pose=3),
            step('pose', actor='adam', pose=3),
            step('wait', ticks=40),
            step('voice', key='memory.celestial.fruit.voice', pos=[25, 5, 21], ticks=90),
            step('pose', actor='eve', pose=0),
            step('pose', actor='adam', pose=0),
            step('entity', type=c('gate_cherub'), pos=[36.5, 5, 21.5], yaw=90),  # у врат вспыхивает пламенный меч
            step('wait', ticks=30),
            step('move', actor='eve', to=[35.0, 5, 23.0], speed=0.05, wait=False),
            step('move', actor='adam', to=[35.0, 5, 24.5], speed=0.05, wait=False),
            step('wait', ticks=110),
            step('despawn', actor='eve'),
            step('despawn', actor='adam'),
            step('end', ticks=30),
        ],
    },
}

LANG = {
    'block.celestial.memory_anchor': ('Отпечаток света', 'Imprint of Light'),
    'block.celestial.memory_anchor.lore1': ('Это место помнит. ПКМ — шагнуть в воспоминание.', 'This place remembers. Use to step into the memory.'),
    'entity.celestial.memory_human': ('Образ из памяти', 'Figure of Memory'),
    'entity.celestial.memory_serpent': ('Змей', 'The Serpent'),
    'lore.celestial.relive': ('✦ Пережить снова', '✦ Relive'),
    'memory.celestial.blank': ('Свет здесь ничего не помнит.', 'The light here remembers nothing.'),
    'memory.celestial.deny.already': ('Ты уже в воспоминании.', 'You are already within a memory.'),
    'memory.celestial.deny.combat': ('Память не открывается в бою.', 'Memory will not open in battle.'),
    'memory.celestial.deny.unsteady': ('Встань твёрдо на землю — память не держит на лету.', 'Stand firm on the ground: memory cannot hold you in flight.'),
    'memory.celestial.edge': ('Дальше память осыпается…', 'Beyond here the memory crumbles…'),
    'memory.celestial.who.serpent': ('Змей', 'The Serpent'),
    'memory.celestial.who.eve': ('Ева', 'Eve'),
    'memory.celestial.who.adam': ('Адам', 'Adam'),
    'memory.celestial.fruit.serpent': ('Нет, не умрёте…', 'Ye shall not surely die…'),
    'memory.celestial.fruit.voice': ('Где ты?', 'Where art thou?'),
    'memory.celestial.fruit.thought': ('Вот почему у врат стоит страж.', 'That is why a guardian stands at the gate.'),
    'memory.celestial.skipping': ('Сон уходит… (держи «красться»)', 'The dream fades… (keep sneaking)'),
    'memory.celestial.who.morning': ('Денница', 'The Morning Star'),
    'memory.celestial.prologue.light1': ('Прежде всех миров был Свет', 'Before all worlds there was Light'),
    'memory.celestial.prologue.fly_hint': ('Лети к свету (прыжок — вверх, красться — вниз)', 'Fly toward the light (jump to rise, sneak to descend)'),
    'memory.celestial.prologue.light2': ('Вокруг Престола пели хоры', 'Around the Throne the choirs sang'),
    'memory.celestial.prologue.morning': ('Свет будет моим.', 'The Light shall be mine.'),
    'memory.celestial.prologue.fall': ('Ярчайший пожелал Свет себе — и пал', 'The brightest wanted the Light for himself — and fell'),
    'memory.celestial.prologue.dodge_hint': ('Звёзды падают — уворачивайся!', 'Stars are falling — dodge!'),
    'memory.celestial.prologue.star_hit': ('Звезда опалила тебя светом', 'A star scorched you with light'),
    'memory.celestial.prologue.fall2': ('…и увлёк за собой звёзды', '…and drew the stars down with him'),
    'memory.celestial.prologue.garden1': ('Для первых людей был насажен Сад', 'For the first people a Garden was planted'),
    'memory.celestial.prologue.adam1': ('Назови их со мной.', 'Name them with me.'),
    'memory.celestial.prologue.name_hint': ('Присядь и коснись зверя пустой рукой — дай имя (%s из %s)', 'Sneak and touch a creature with an empty hand to name it (%s of %s)'),
    'memory.celestial.prologue.adam2': ('Так и будет имя им.', 'So shall their names be.'),
    'memory.celestial.prologue.trees': ('Посреди Сада росли два Древа', 'In the midst of the Garden grew two Trees'),
    'memory.celestial.prologue.serpent': ('Возьми. Не умрёшь…', 'Take it. You shall not die…'),
    'memory.celestial.prologue.choice_hint': ('Возьми плод у Змея — или отвернись', 'Take the fruit from the Serpent — or turn away'),
    'memory.celestial.choice.fruit.taken': ('Ты взял плод. Глаза открылись…', 'You took the fruit. Your eyes were opened…'),
    'memory.celestial.choice.fruit.refused': ('Ты отвернулся. Но Ева протянула руку…', 'You turned away. But Eve reached out…'),
    'memory.celestial.prologue.run': ('Беги!', 'Run!'),
    'memory.celestial.prologue.run_hint': ('Проскочи мимо пламенного меча к вратам', 'Slip past the flaming sword to the gate'),
    'memory.celestial.prologue.sword_hit': ('Пламенный меч отбросил тебя', 'The flaming sword threw you back'),
    'memory.celestial.prologue.exile1': ('Люди ушли из Сада…', 'The people left the Garden…'),
    'memory.celestial.prologue.exile2': ('…а Сад подняли над облаками', '…and the Garden was raised above the clouds'),
    'memory.celestial.prologue.exile3': ('Внизу люди со временем забыли дорогу', 'Below, in time, people forgot the way'),
    'memory.celestial.prologue.wake_title': ('Пробуждение', 'Awakening'),
    'memory.celestial.prologue.wake': ('Звёзды падают, свет уходит. Ты — дитя Адама: найди дорогу назад.', 'Stars fall and the light fades. You are a child of Adam: find the way back.'),
}


def main():
    dimension()
    actors()
    anchor_block()
    stage_fruit()
    stage_prologue_light()
    stage_prologue_exile()
    write_json(os.path.join(DATA, 'memory/scenes.json'), {**SCENES, **PROLOGUE})
    lang_patch(LANG)
    print('ok: Отблески —', len(SCENES) + len(PROLOGUE), 'сцен')


if __name__ == '__main__':
    main()
