#!/usr/bin/env python3
"""Структуры Рая: шаблоны NBT строятся кодом (воксельный конструктор) + JSON структур/пулов/наборов.

Запуск: python3 tools/gen_structures.py
Структуры: небесная деревня, руины с запертыми хранилищами (ключи), Небесная Цитадель.
"""
import math
import os
import random

import nbtlib
from nbtlib import Byte, Compound, Double, Float, Int, List, String

from gen_assets import DATA, write_json, c

DATA_VERSION = 5023  # версия данных 26.3 (из ванильных шаблонов)


class Template:
    def __init__(self, sx, sy, sz):
        self.size = (sx, sy, sz)
        self.blocks = {}
        self.entities = []

    def set(self, x, y, z, block, nbt=None, **props):
        if 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]:
            self.blocks[(x, y, z)] = (block, tuple(sorted((k, str(v).lower()) for k, v in props.items())), nbt)

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0] if b else None

    def fill(self, x0, y0, z0, x1, y1, z1, block, **props):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, block, **props)

    def walls(self, x0, y0, z0, x1, y1, z1, block, **props):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or z in (z0, z1):
                        self.set(x, y, z, block, **props)

    def paste(self, other, ox, oy, oz):
        """Вклеить другой шаблон (блоки вместе с явным воздухом и сущности) со сдвигом."""
        for (x, y, z), (block, props, nbt) in other.blocks.items():
            if 0 <= x + ox < self.size[0] and 0 <= y + oy < self.size[1] and 0 <= z + oz < self.size[2]:
                self.blocks[(x + ox, y + oy, z + oz)] = (block, props, nbt)
        for e in other.entities:
            pos = [float(v) for v in e['pos']]
            bpos = [int(v) for v in e['blockPos']]
            self.entities.append(Compound({
                'pos': List[Double]([Double(pos[0] + ox), Double(pos[1] + oy), Double(pos[2] + oz)]),
                'blockPos': List[Int]([Int(bpos[0] + ox), Int(bpos[1] + oy), Int(bpos[2] + oz)]),
                'nbt': e['nbt']}))

    def entity(self, x, y, z, nbt):
        nbt = dict(nbt)
        self.entities.append(Compound({
            'pos': List[Double]([Double(x + 0.5), Double(y), Double(z + 0.5)]),
            'blockPos': List[Int]([Int(x), Int(y), Int(z)]),
            'nbt': to_nbt(nbt)}))

    def save(self, name):
        palette, index = [], {}
        blocks = []
        for (x, y, z), (block, props, nbt) in sorted(self.blocks.items()):
            key = (block, props)
            if key not in index:
                index[key] = len(palette)
                entry = {'id': String(block)}
                if props:
                    entry['properties'] = Compound({k: String(v) for k, v in props})
                palette.append(Compound(entry))
            b = {'pos': List[Int]([Int(x), Int(y), Int(z)]), 'state': Int(index[key])}
            if nbt is not None:
                b['nbt'] = to_nbt(nbt)
            blocks.append(Compound(b))
        root = nbtlib.File({
            'size': List[Int]([Int(v) for v in self.size]),
            'entities': List[Compound](self.entities),
            'blocks': List[Compound](blocks),
            'palette': List[Compound](palette),
            'DataVersion': Int(DATA_VERSION)})
        path = os.path.join(DATA, 'structure', name + '.nbt')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # gzip без времени создания — файл меняется только при реальных изменениях постройки
        import gzip
        with open(path, 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as f:
            root.write(f)
        return len(blocks)


def to_nbt(v):
    if isinstance(v, dict):
        return Compound({k: to_nbt(x) for k, x in v.items()})
    if isinstance(v, bool):
        return Byte(int(v))
    if isinstance(v, int):
        return Int(v)
    if isinstance(v, float):
        return Float(v)
    if isinstance(v, list):
        items = [to_nbt(x) for x in v]
        return List[type(items[0])](items) if items else List([])
    return String(v)


C = lambda n: f'celestial:{n}'  # noqa: E731
GRASS, DIRT, STONE, BRICKS = C('golden_grass'), C('heaven_dirt'), C('skystone'), C('skystone_bricks')
PLANKS, LOG, RADIANT, CLOUD = C('skywood_planks'), C('skywood_log'), C('radiant_stone'), C('cloud')
SLAB, FENCE, WALL = C('skywood_slab'), C('skywood_fence'), C('skystone_brick_wall')


def island_base(t, cx, cz, radius, top_y, depth, rng):
    """Собственный «островок» под постройкой: трава сверху, конус из камня книзу."""
    for x in range(t.size[0]):
        for z in range(t.size[2]):
            d = math.hypot(x - cx, z - cz)
            if d > radius:
                continue
            bottom = top_y - int(depth * (1 - (d / radius) ** 1.6)) - rng.randint(0, 1)
            for y in range(max(0, bottom), top_y + 1):
                t.set(x, y, z, GRASS if y == top_y else DIRT if y >= top_y - 2 else STONE)


def reliquary(t, x, y, z, loot):
    """Награда за загадку: неразрушимый Реликварий, открывается, только когда рядом не осталось печатей-дверей."""
    t.set(x, y, z, 'celestial:reliquary', nbt={'id': 'celestial:reliquary', 'LootTable': loot})


def chest(t, x, y, z, loot, facing='north', lock=None):
    nbt = {'id': 'minecraft:chest', 'LootTable': loot}
    if lock:
        nbt['lock'] = {'items': lock}
    t.set(x, y, z, 'minecraft:chest', nbt=nbt, facing=facing, type='single', waterlogged=False)


# ================================================================ небесная деревня
def house(t, x0, z0, y0, w, d, rng, door_side):
    h = 5
    t.fill(x0, y0, z0, x0 + w - 1, y0, z0 + d - 1, BRICKS)
    t.walls(x0, y0 + 1, z0, x0 + w - 1, y0 + h - 1, z0 + d - 1, PLANKS)
    for x, z in ((x0, z0), (x0 + w - 1, z0), (x0, z0 + d - 1), (x0 + w - 1, z0 + d - 1)):
        t.fill(x, y0 + 1, z, x, y0 + h - 1, z, LOG, axis='y')
    # окна
    for y in (y0 + 2, y0 + 3):
        for x in range(x0 + 2, x0 + w - 2, 2):
            t.set(x, y, z0, 'minecraft:white_stained_glass_pane', north=False, south=False, east=True, west=True, waterlogged=False)
            t.set(x, y, z0 + d - 1, 'minecraft:white_stained_glass_pane', north=False, south=False, east=True, west=True, waterlogged=False)
    # дверной проём
    mx, mz = x0 + w // 2, z0 + d // 2
    door = {'n': (mx, z0), 's': (mx, z0 + d - 1), 'w': (x0, mz), 'e': (x0 + w - 1, mz)}[door_side]
    t.fill(door[0], y0 + 1, door[1], door[0], y0 + 2, door[1], 'minecraft:air')
    # крыша-пирамида: каждый ярус сужается на блок, наверху — плиты
    layer = 0
    while True:
        xa, xb, za, zb = x0 - 1 + layer, x0 + w - layer, z0 - 1 + layer, z0 + d - layer
        if xa > xb or za > zb:
            break
        y = y0 + h + layer
        last = xb - xa <= 1 or zb - za <= 1
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                if last:
                    t.set(x, y, z, SLAB, type='bottom', waterlogged=False)
                elif x in (xa, xb) or z in (za, zb):
                    t.set(x, y, z, PLANKS)
        if last:
            break
        layer += 1
    # свет и уют
    t.set(mx, y0 + h - 1, mz, 'minecraft:lantern', hanging=True, waterlogged=False)
    t.fill(x0 + 1, y0 + 1, z0 + 1, x0 + w - 2, y0 + h - 2, z0 + d - 2, 'minecraft:air')
    t.set(mx, y0 + h - 1, mz, 'minecraft:lantern', hanging=True, waterlogged=False)
    return (mx, y0 + 1, mz)


def sky_village():
    rng = random.Random(7)
    t = Template(33, 16, 33)
    top = 6
    island_base(t, 16, 16, 16, top, 7, rng)
    # дорожки крестом
    for i in range(3, 30):
        for w in (15, 16, 17):
            t.set(i, top, w, BRICKS)
            t.set(w, top, i, BRICKS)
    # фонтан из светлого камня в центре
    t.fill(13, top, 13, 19, top, 19, BRICKS)
    t.walls(13, top + 1, 13, 19, top + 1, 19, RADIANT)
    t.fill(14, top + 1, 14, 18, top + 1, 18, 'minecraft:water', level=0)
    t.fill(16, top + 1, 16, 16, top + 3, 16, RADIANT)
    t.set(16, top + 4, 16, C('sky_crystal'), facing='up', waterlogged=False)
    # четыре дома
    inside = [
        house(t, 3, 3, top, 9, 8, rng, 's'),
        house(t, 21, 3, top, 9, 8, rng, 's'),
        house(t, 3, 22, top, 9, 8, rng, 'n'),
        house(t, 21, 22, top, 9, 8, rng, 'n'),
    ]
    chest(t, 5, top + 1, 5, 'celestial:chests/sky_village', facing='south')
    chest(t, 27, top + 1, 28, 'celestial:chests/sky_village', facing='north')
    t.set(23, top + 1, 5, 'minecraft:crafting_table')
    t.set(5, top + 1, 28, 'minecraft:white_bed', facing='east', part='foot', occupied=False)
    t.set(6, top + 1, 28, 'minecraft:white_bed', facing='east', part='head', occupied=False)
    t.set(16, top + 1, 12, C('quest_board'), facing='south')
    # фонари на столбах вдоль дорог
    for x, z in ((12, 12), (20, 12), (12, 20), (20, 20)):
        t.fill(x, top + 1, z, x, top + 2, z, FENCE, north=False, south=False, east=False, west=False, waterlogged=False)
        t.set(x, top + 3, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    # жители и пегасы
    for i, (x, y, z) in enumerate(inside[:3]):
        t.entity(x, y, z, {'id': C('angel'), 'PersistenceRequired': True, 'Profession': i})
    t.entity(16, top + 1, 9, {'id': C('pegasus'), 'PersistenceRequired': True})
    t.entity(9, top + 1, 16, {'id': C('pegasus'), 'PersistenceRequired': True})
    return t.save('sky_village/center')


# ================================================================ руины с хранилищами
def sky_ruins():
    rng = random.Random(11)
    t = Template(27, 14, 27)
    top = 5
    island_base(t, 13, 13, 13, top, 6, rng)
    t.fill(2, top, 2, 24, top, 24, BRICKS)
    # полуразрушенные стены и колонны
    t.walls(2, top + 1, 2, 24, top + 6, 24, BRICKS)
    for x in range(2, 25):
        for z in range(2, 25):
            if t.get(x, top + 3, z) == BRICKS:
                for y in range(top + 1 + rng.randint(1, 6), top + 7):
                    t.set(x, y, z, 'minecraft:air')
                if rng.random() < 0.15:
                    t.set(x, top + 1, z, STONE)
    for x, z in ((6, 6), (20, 6), (6, 20), (20, 20), (13, 4), (13, 22)):
        hgt = rng.randint(3, 8)
        t.fill(x, top + 1, z, x, top + hgt, z, WALL, up=True, north='none', south='none', east='none', west='none', waterlogged=False)
    # входы
    t.fill(12, top + 1, 2, 14, top + 3, 2, 'minecraft:air')
    t.fill(12, top + 1, 24, 14, top + 3, 24, 'minecraft:air')
    # три хранилища: бронзовое, серебряное, золотое
    vaults = [(5, 'bronze', 'celestial:bronze_key'), (13, 'silver', 'celestial:silver_key'), (21, 'gold', 'celestial:golden_key')]
    for vx, tier, key in vaults:
        t.walls(vx - 2, top + 1, 14, vx + 2, top + 4, 18, BRICKS)
        t.fill(vx - 2, top + 5, 14, vx + 2, top + 5, 18, BRICKS)
        t.fill(vx - 1, top + 1, 15, vx + 1, top + 4, 17, 'minecraft:air')
        t.set(vx, top + 1, 14, 'minecraft:air')
        t.set(vx, top + 2, 14, 'minecraft:air')
        chest(t, vx, top + 1, 17, f'celestial:chests/ruins_{tier}', facing='north', lock=key)
        t.set(vx, top + 4, 16, 'minecraft:lantern', hanging=True, waterlogged=False)
    # мимик притворяется сундуком у западной стены
    t.entity(4, top + 1, 8, {'id': C('mimic'), 'PersistenceRequired': True, 'Rotation': [90.0, 0.0]})
    # рассадник стражей в центре двора
    t.set(13, top + 1, 9, 'minecraft:spawner', nbt={
        'id': 'minecraft:mob_spawner', 'SpawnData': {'entity': {'id': C('fallen_guardian')}},
        'MinSpawnDelay': 300, 'MaxSpawnDelay': 900, 'SpawnCount': 2, 'MaxNearbyEntities': 4, 'RequiredPlayerRange': 16})
    return t.save('sky_ruins/main')


# ================================================================ Небесная Цитадель
def citadel():
    rng = random.Random(23)
    t = Template(45, 32, 45)
    cx = cz = 22
    top = 10
    island_base(t, cx, cz, 22, top, 11, rng)
    t.fill(3, top, 3, 41, top, 41, BRICKS)
    # внешняя стена с зубцами и четыре башни
    t.walls(4, top + 1, 4, 40, top + 9, 40, BRICKS)
    for i in range(4, 41, 2):
        for a, b in ((i, 4), (i, 40), (4, i), (40, i)):
            t.set(a, top + 10, b, BRICKS)
    for tx, tz in ((4, 4), (40, 4), (4, 40), (40, 40)):
        for x in range(tx - 3, tx + 4):
            for z in range(tz - 3, tz + 4):
                d = math.hypot(x - tx, z - tz)
                if d <= 3.2:
                    for y in range(top + 1, top + 16):
                        t.set(x, y, z, BRICKS if d > 2.2 else 'minecraft:air')
                    t.set(x, top + 16, z, RADIANT if d <= 1 else BRICKS)
        t.set(tx, top + 17, tz, C('sky_crystal'), facing='up', waterlogged=False)
    # ворота
    t.fill(20, top + 1, 4, 24, top + 6, 4, 'minecraft:air')
    # арена: круг из светлого камня и кирпича
    for x in range(5, 40):
        for z in range(5, 40):
            d = math.hypot(x - cx, z - cz)
            if d <= 14:
                ring = int(d) % 4 == 0
                t.set(x, top, z, RADIANT if ring else C('skystone_bricks'))
    # колонны вокруг арены
    for k in range(8):
        a = k * math.pi / 4
        x, z = round(cx + 14 * math.cos(a)), round(cz + 14 * math.sin(a))
        t.fill(x, top + 1, z, x, top + 8, z, BRICKS)
        t.set(x, top + 9, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    # центр: печать Серафима (заменяется на настоящий блок на этапе босса) и алтарь
    t.set(cx, top + 1, cz, C('seraph_seal'), nbt={'id': C('seraph_seal')}, awakened=False)
    t.fill(cx - 1, top + 1, cz + 10, cx + 1, top + 1, cz + 12, RADIANT)
    t.set(cx, top + 2, cz + 11, C('celestial_altar'))
    # сокровищница за аркой
    t.walls(16, top + 1, 34, 28, top + 5, 39, BRICKS)
    t.fill(17, top + 1, 35, 27, top + 4, 38, 'minecraft:air')
    t.fill(21, top + 1, 34, 23, top + 3, 34, 'minecraft:air')
    chest(t, 20, top + 1, 38, 'celestial:chests/citadel_treasure', facing='north')
    chest(t, 24, top + 1, 38, 'celestial:chests/citadel_treasure', facing='north')
    return t.save('citadel/main')


# ================================================================ большая деревня
def grand_village():
    rng = random.Random(77)
    t = Template(45, 22, 45)
    top = 7
    island_base(t, 22, 22, 22, top, 9, rng)
    for i in range(3, 42):
        for w in (21, 22, 23):
            t.set(i, top, w, BRICKS); t.set(w, top, i, BRICKS)
    # площадь с доской поручений и фонтаном
    t.fill(17, top, 17, 27, top, 27, BRICKS)
    t.walls(19, top + 1, 19, 25, top + 1, 25, RADIANT)
    t.fill(20, top + 1, 20, 24, top + 1, 24, 'minecraft:water', level=0)
    t.fill(22, top + 1, 22, 22, top + 4, 22, RADIANT)
    t.set(22, top + 5, 22, C('sky_crystal'), facing='up', waterlogged=False)
    t.set(22, top + 1, 17, C('quest_board'), facing='north')
    t.set(17, top + 1, 22, C('sky_beacon'))
    # храм на севере
    t.fill(16, top, 3, 28, top, 13, BRICKS)
    t.walls(16, top + 1, 3, 28, top + 8, 13, BRICKS)
    t.fill(17, top + 1, 4, 27, top + 7, 12, 'minecraft:air')
    t.fill(21, top + 1, 13, 23, top + 4, 13, 'minecraft:air')
    for x in (16, 28):
        for z in range(3, 14, 3):
            t.fill(x, top + 1, z, x, top + 8, z, RADIANT)
    for layer in range(5):
        t.fill(16 + layer, top + 9 + layer, 3, 28 - layer, top + 9 + layer, 13, BRICKS)
    t.set(22, top + 1, 5, C('celestial_altar'))
    for i, x in enumerate((18, 20, 24, 26, 22)):
        t.set(x, top + 1, 7 if i < 4 else 9, C('sky_bell'), note=i)
    t.set(22, top + 1, 9, C('sky_bell'), note=4)
    t.set(22, top + 7, 8, 'minecraft:lantern', hanging=True, waterlogged=False)
    # рынок на востоке: прилавки под навесами
    for k, z in enumerate((17, 21, 25)):
        x0 = 31
        t.fill(x0, top + 1, z, x0 + 3, top + 1, z, C('skywood_slab'), type='top', waterlogged=False)
        for x in (x0, x0 + 3):
            t.fill(x, top + 1, z + 1, x, top + 3, z + 1, FENCE, north=False, south=False, east=False, west=False, waterlogged=False)
        t.fill(x0, top + 4, z, x0 + 3, top + 4, z + 2, ['minecraft:yellow_wool', 'minecraft:white_wool', 'minecraft:light_blue_wool'][k])
        chest(t, x0 + 1, top + 2, z, 'celestial:chests/sky_village', facing='west')
    # сад на юге
    for x in range(16, 29):
        for z in range(31, 41):
            if (x + z) % 3 == 0:
                t.set(x, top + 1, z, C(rng.choice(['sky_lily', 'sunbell', 'cloudbloom', 'aether_rose', 'dawn_poppy'])))
            elif (x * z) % 7 == 0:
                t.set(x, top + 1, z, C('manna_bush'), age=3)
    t.set(22, top + 1, 36, C('cloud_willow_sapling'), stage=0)
    # шесть домов
    inside = [house(t, x, z, top, 8, 7, rng, d) for x, z, d in ((3, 3, 's'), (3, 16, 'e'), (3, 29, 'e'), (33, 3, 's'), (33, 33, 'n'), (3, 37, 'n'))]
    for i, (x, y, z) in enumerate(inside):
        t.entity(x, y, z, {'id': C('angel'), 'PersistenceRequired': True, 'Profession': i % 4})
    t.entity(22, top + 1, 15, {'id': C('angel'), 'PersistenceRequired': True, 'Profession': 2})
    t.entity(30, top + 1, 30, {'id': C('pegasus'), 'PersistenceRequired': True, 'Variant': 1})
    t.entity(14, top + 1, 30, {'id': C('pegasus'), 'PersistenceRequired': True})
    t.entity(25, top + 1, 38, {'id': C('golden_ram'), 'PersistenceRequired': True, 'Color': 4})
    for x, z in ((15, 15), (29, 15), (15, 29), (29, 29)):
        t.fill(x, top + 1, z, x, top + 2, z, FENCE, north=False, south=False, east=False, west=False, waterlogged=False)
        t.set(x, top + 3, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    return t.save('sky_village/grand')


# ================================================================ Храм Лучей
def beam_temple():
    """Луч с крыши (линза → перископ) надо довести до ЗЕЛЁНОГО приёмника у печати: повернуть перископ и зеркало Камертоном."""
    rng = random.Random(41)
    t = Template(27, 16, 27)
    top = 5
    island_base(t, 13, 13, 13, top, 7, rng)
    t.fill(2, top, 2, 24, top, 24, BRICKS)
    t.walls(2, top + 1, 2, 24, top + 7, 24, BRICKS)
    t.fill(2, top + 8, 2, 24, top + 8, 24, BRICKS)
    for x in range(2, 25, 4):
        for z in (2, 24):
            t.fill(x, top + 1, z, x, top + 7, z, RADIANT)
    t.fill(12, top + 1, 2, 14, top + 4, 2, 'minecraft:air')  # вход
    for x, z in ((6, 6), (20, 6), (6, 20), (20, 20)):
        t.set(x, top + 7, z, 'minecraft:lantern', hanging=True, waterlogged=False)
    # луч: линза на крыше светит вниз в перископ (стоит не туда — надо повернуть на юг)
    t.set(8, top + 9, 8, C('sun_lens'), nbt={'id': C('beam_source')}, facing='down', active=False, sealed=True)
    t.set(8, top + 8, 8, 'minecraft:glass')
    t.set(8, top + 1, 8, C('periscope'), facing='west', up=False)
    t.set(8, top + 1, 14, C('beam_prism'))
    t.set(8, top + 1, 18, C('beam_mirror'), flipped=False)  # стоит неверно: зелёный уйдёт на запад
    t.set(14, top + 1, 14, C('light_receiver'), color='red', powered=False, sealed=True)
    t.set(2 + 1, top + 1, 14, C('light_receiver'), color='blue', powered=False, sealed=True)
    t.set(16, top + 1, 18, C('light_receiver'), color='green', powered=False, sealed=True)
    t.fill(17, top + 1, 17, 17, top + 3, 19, C('sealed_door'))
    # сокровищница за печатью
    t.fill(18, top + 1, 16, 23, top + 4, 21, 'minecraft:air')
    reliquary(t, 22, top + 1, 18, 'celestial:chests/beam_temple')
    chest(t, 4, top + 1, 4, 'celestial:chests/trial_tools', facing='south')
    t.set(13, top + 1, 6, C('rune_pedestal'), riddle=3, solved=False)
    return t.save('beam_temple/main')


# ================================================================ Облачный замок
def cloud_castle():
    rng = random.Random(53)
    t = Template(35, 34, 35)
    top = 6
    island_base(t, 17, 17, 17, top, 9, rng)
    floors = [top, top + 9, top + 18]
    for f, y0 in enumerate(floors):
        inset = f * 3
        a, b = 3 + inset, 31 - inset
        t.fill(a, y0, a, b, y0, b, BRICKS if f == 0 else C('cloud'))
        t.walls(a, y0 + 1, a, b, y0 + 8, b, C('cloud') if f else BRICKS)
        for x, z in ((a, a), (b, a), (a, b), (b, b)):
            t.fill(x - 1, y0, z - 1, x + 1, y0 + 10, z + 1, BRICKS)
            t.set(x, y0 + 11, z, C('sky_crystal'), facing='up', waterlogged=False)
        for x in range(a + 2, b - 1, 4):
            t.set(x, y0 + 4, a, 'minecraft:white_stained_glass'); t.set(x, y0 + 4, b, 'minecraft:white_stained_glass')
        t.set(17, y0 + 7, 17, 'minecraft:lantern', hanging=True, waterlogged=False)
    t.fill(16, top + 1, 3, 18, top + 4, 3, 'minecraft:air')
    # 1 этаж: мимики и сундуки, плитки-звёзды открывают лестницу
    for x, z in ((6, 8), (28, 8), (6, 26)):
        chest(t, x, top + 1, z, 'celestial:chests/ruins_bronze', facing='east')
    for x, z in ((28, 26), (17, 28)):
        t.entity(x, top + 1, z, {'id': C('mimic'), 'PersistenceRequired': True, 'Rotation': [0.0, 0.0]})
    for x in range(15, 20):
        for z in range(15, 20):
            if abs(x - 17) <= 1 and abs(z - 17) <= 1:
                t.set(x, top, z, C('star_tile'), lit=(x + z) % 2 == 0, solved=False)
    t.fill(25, top + 1, 14, 27, top + 9, 14, 'minecraft:air')
    for k in range(9):
        t.set(26, top + 1 + k, 15 + k % 3, C('skystone_brick_stairs'), facing='south', half='bottom', shape='straight', waterlogged=False)
    t.fill(25, top + 9, 14, 27, top + 9, 18, C('sealed_door'))
    # 2 этаж: стражи и рунный пьедестал
    y1 = floors[1]
    t.set(17, y1 + 1, 17, C('rune_pedestal'), riddle=rng.randrange(8), solved=False)
    t.set(12, y1 + 1, 12, 'minecraft:spawner', nbt={'id': 'minecraft:mob_spawner', 'SpawnData': {'entity': {'id': C('fallen_guardian')}},
                                                    'MinSpawnDelay': 400, 'MaxSpawnDelay': 900, 'SpawnCount': 2, 'MaxNearbyEntities': 4,
                                                    'RequiredPlayerRange': 14})
    t.fill(16, y1 + 9, 22, 18, y1 + 9, 24, C('sealed_door'))
    t.set(17, y1 + 1, 19, C('sealed_door'))
    for k in range(9):
        t.set(17, y1 + 1 + k, 20 + k % 3, C('skystone_brick_stairs'), facing='south', half='bottom', shape='straight', waterlogged=False) if k > 0 else None
    # 3 этаж: кристалл испытания с Грозовым элементалем и сокровищница
    y2 = floors[2]
    t.set(17, y2 + 1, 17, C('trial_crystal'), nbt={'id': C('trial_crystal'), 'Trial': 'cloud_castle'}, state='idle')
    chest(t, 17, y2 + 1, 22, 'celestial:chests/cloud_castle', facing='north')
    chest(t, 15, y2 + 1, 22, 'celestial:chests/cloud_castle', facing='north')
    return t.save('cloud_castle/main')


# ================================================================ Небесный маяк
def sky_lighthouse():
    rng = random.Random(61)
    t = Template(15, 42, 15)
    top = 4
    island_base(t, 7, 7, 7, top, 6, rng)
    for y in range(top + 1, top + 32):
        for x in range(4, 11):
            for z in range(4, 11):
                d = math.hypot(x - 7, z - 7)
                if 2.2 < d <= 3.3:
                    stripe = ((y - top) // 4) % 2 == 0
                    t.set(x, y, z, 'minecraft:white_concrete' if stripe else C('skystone_bricks'))
    for y in range(top + 1, top + 31):
        t.set(7, y, 5, 'minecraft:ladder', facing='south', waterlogged=False)
    t.fill(6, top + 1, 4, 8, top + 3, 4, 'minecraft:air')
    t.set(7, top + 1, 5, 'minecraft:air'); t.set(7, top + 2, 5, 'minecraft:air')
    t.fill(3, top + 32, 3, 11, top + 32, 11, BRICKS)
    for x, z in ((3, 3), (11, 3), (3, 11), (11, 11)):
        t.fill(x, top + 33, z, x, top + 36, z, RADIANT)
    t.fill(3, top + 37, 3, 11, top + 37, 11, C('golden_cloud'))
    t.set(7, top + 33, 7, C('sky_beacon'))
    t.set(7, top + 36, 7, C('sun_lens'), nbt={'id': C('beam_source')}, facing='up', active=False)
    chest(t, 9, top + 33, 9, 'celestial:chests/sky_village', facing='west')
    return t.save('sky_lighthouse/main')


# ================================================================ Обломки воздушного галеона
def airship_wreck():
    rng = random.Random(97)
    t = Template(37, 22, 15)
    keel = 6
    for x in range(2, 35):
        half = int(5 * math.sin(math.pi * (x - 2) / 32)) + 1
        depth = int(4 * math.sin(math.pi * (x - 2) / 32)) + 1
        for z in range(7 - half, 8 + half):
            for y in range(keel - depth, keel + 1):
                edge = abs(z - 7) == half or y == keel - depth
                if edge and rng.random() > 0.08:  # пробоины
                    t.set(x, y, z, C('skywood_planks') if y > keel - depth else LOG, **({'axis': 'x'} if y == keel - depth else {}))
            if abs(z - 7) < half and rng.random() > 0.05:
                t.set(x, keel + 1, z, C('skywood_slab'), type='bottom', waterlogged=False)
        if abs(x - 18) > 8:
            for z in (7 - half, 7 + half):
                t.set(x, keel + 2, z, FENCE, north=False, south=False, east=True, west=True, waterlogged=False)
    # мачты и паруса (один порван)
    for mx, h in ((12, 12), (24, 10)):
        t.fill(mx, keel + 2, 7, mx, keel + 2 + h, 7, LOG, axis='y')
        for y in range(keel + 5, keel + 2 + h):
            for z in range(3, 12):
                if not (mx == 24 and rng.random() < 0.45):
                    t.set(mx + 1, y, z, 'minecraft:white_wool')
    # пушки и груз
    for x in (8, 16, 28):
        t.set(x, keel + 2, 3, 'minecraft:dispenser', facing='north', triggered=False)
        t.set(x, keel + 2, 11, 'minecraft:dispenser', facing='south', triggered=False)
    chest(t, 18, keel, 7, 'celestial:chests/airship_wreck', facing='east')
    chest(t, 30, keel + 2, 7, 'celestial:chests/airship_wreck', facing='west')
    t.set(4, keel + 2, 7, 'minecraft:barrel', facing='up', open=False)
    # облака держат обломки
    for _ in range(40):
        x, z = rng.randrange(4, 33), rng.randrange(2, 13)
        t.set(x, rng.randrange(0, 3), z, C(rng.choice(['cloud', 'cloud', 'golden_cloud'])))
    t.entity(14, keel + 2, 7, {'id': C('fallen_guardian'), 'PersistenceRequired': True})
    t.entity(26, keel + 2, 8, {'id': C('fallen_guardian'), 'PersistenceRequired': True})
    return t.save('airship_wreck/main')


# ================================================================ Башня Испытаний Рая
FLOOR_H = 7
TOWER = 21


def trial_tower():
    """7 этажей испытаний. Лестница в углу каждого этажа закрыта печатью — она растворяется после победы."""
    rng = random.Random(31)
    floors = 7
    t = Template(TOWER, FLOOR_H * floors + 8, TOWER)
    c0 = TOWER // 2
    island_base(t, c0, c0, 12, 4, 8, rng)
    base = 5
    for f in range(floors):
        y0 = base + f * FLOOR_H
        # пол, стены с окнами, колонны по углам
        t.fill(1, y0, 1, TOWER - 2, y0, TOWER - 2, BRICKS)
        t.walls(1, y0 + 1, 1, TOWER - 2, y0 + FLOOR_H - 1, TOWER - 2, BRICKS)
        for x, z in ((1, 1), (TOWER - 2, 1), (1, TOWER - 2), (TOWER - 2, TOWER - 2)):
            t.fill(x, y0 + 1, z, x, y0 + FLOOR_H - 1, z, RADIANT)
        for i in range(4, TOWER - 4, 4):
            for wall in ((i, 1), (i, TOWER - 2), (1, i), (TOWER - 2, i)):
                t.fill(wall[0], y0 + 3, wall[1], wall[0], y0 + 4, wall[1], 'minecraft:white_stained_glass')
        # свет
        for x, z in ((5, 5), (TOWER - 6, 5), (5, TOWER - 6), (TOWER - 6, TOWER - 6)):
            t.set(x, y0 + FLOOR_H - 1, z, 'minecraft:lantern', hanging=True, waterlogged=False)
        # лестница в северо-восточном углу на следующий этаж, проём закрыт печатью
        sx = TOWER - 4
        for k in range(FLOOR_H):
            t.set(sx, y0 + 1 + k, 3 + k % 3, 'minecraft:air')
        for k in range(FLOOR_H - 1):
            t.set(sx, y0 + 1 + k, 3 + (k % 3) if k < 3 else 5 - (k % 3), C('skystone_brick_stairs'), facing='south', half='bottom', shape='straight', waterlogged=False)
        if f < floors - 1:
            t.fill(sx - 1, y0 + FLOOR_H, 2, sx + 1, y0 + FLOOR_H, 6, C('sealed_door'))
        trial = f'heaven_{f + 1}'
        t.set(c0, y0 + 1, c0, C('trial_crystal'), nbt={'id': C('trial_crystal'), 'Trial': trial}, state='idle')
        decorate_floor(t, f + 1, y0, rng)
    # печати над лестницами ставим после всех этажей: пол следующего этажа (и пропасти 2-го и 5-го) лежит на том же уровне и стирал их,
    # из-за чего лестницы вели в потолок или были открыты с самого начала
    sx = TOWER - 4
    for f in range(floors - 1):
        t.fill(sx - 1, base + f * FLOOR_H + FLOOR_H, 2, sx + 1, base + f * FLOOR_H + FLOOR_H, 6, C('sealed_door'))
    # вход на первом этаже и крыша с сундуком наград
    t.fill(c0 - 1, base + 1, 1, c0 + 1, base + 3, 1, 'minecraft:air')
    roof = base + floors * FLOOR_H
    t.fill(1, roof, 1, TOWER - 2, roof, TOWER - 2, BRICKS)
    for i in range(1, TOWER - 1, 2):
        for a, b in ((i, 1), (i, TOWER - 2), (1, i), (TOWER - 2, i)):
            t.set(a, roof + 1, b, BRICKS)
    chest(t, c0, roof + 1, c0, 'celestial:chests/trial_tower_top', facing='south')
    t.set(c0, roof + 2, c0 + 2, C('sky_crystal'), facing='up', waterlogged=False)
    return t.save('trial_tower/main')


def decorate_floor(t, n, y0, rng):
    c0 = TOWER // 2
    if n in (1, 6, 7):
        for x, z in ((6, 6), (TOWER - 7, 6), (6, TOWER - 7), (TOWER - 7, TOWER - 7)):
            t.fill(x, y0 + 1, z, x, y0 + 3, z, WALL, up=True, north='none', south='none', east='none', west='none', waterlogged=False)
    if n in (2, 5):
        # пропасть с исчезающими облаками до финишного кристалла у западной стены
        t.fill(3, y0, 3, TOWER - 4, y0, TOWER - 4, 'minecraft:air')
        t.fill(3, y0 - 1, 3, TOWER - 4, y0 - 1, TOWER - 4, 'minecraft:air') if n == 5 else None
        t.fill(c0 - 1, y0, c0 - 1, c0 + 1, y0, c0 + 1, BRICKS)  # островок с кристаллом
        x, z = c0 + 2, c0
        path = []
        for step in range(14 if n == 2 else 22):
            path.append((x, z))
            if step % 3 == 2:
                z += rng.choice([-2, 2])
            else:
                x -= 1 if step % 2 == 0 else 0
                z += 0
            x = max(3, min(TOWER - 4, x - 1))
            z = max(3, min(TOWER - 4, z))
        if n == 5:
            # змейка с шагом в 2 клетки: все колонки разные (прежний случайный путь зажимался у стены и ставил облака друг над другом,
            # из-за чего над ними не оставалось места для игрока), подъём 1 блок каждые 5 шагов, потолок этажа на y0+7
            path = [(13, 10), (13, 12), (13, 14), (11, 14), (9, 14), (7, 14), (5, 14), (5, 12), (5, 10), (5, 8), (5, 6),
                    (7, 6), (9, 6), (11, 6), (13, 6), (15, 6), (15, 8), (15, 10), (15, 12), (15, 14), (15, 16), (13, 16)]
        for i, (x, z) in enumerate(path):
            yy = y0 + (i // 5 if n == 5 else 0)  # макс. подъём 4: потолок этажа на y0+7, над облаком нужно 2 блока воздуха
            t.set(x, yy, z, C('vanishing_cloud'), vanished=False)
        gx, gz = path[-1]
        t.set(gx - 1 if gx > 3 else gx, y0 + (len(path) // 5 if n == 5 else 0), gz, C('trial_goal'))
    if n == 3:
        # лучи: линза светит на восток, луч надо развернуть зеркалами (Камертон лежит в сундуке) на приёмник у южной стены
        t.set(2, y0 + 1, c0 - 3, C('sun_lens'), nbt={'id': C('beam_source')}, facing='east', active=False, sealed=True)
        t.set(c0 + 3, y0 + 1, c0 - 3, C('beam_mirror'), flipped=False)
        t.set(c0 + 3, y0 + 1, c0 + 4, C('beam_mirror'), flipped=False)
        t.set(c0 - 4, y0 + 1, c0 + 4, C('beam_mirror'), flipped=True)
        t.set(c0 - 4, y0 + 1, TOWER - 3, C('light_receiver'), color='white', powered=False, sealed=True)
        chest(t, 3, y0 + 1, TOWER - 4, 'celestial:chests/trial_tools', facing='east')
    if n == 4:
        # звёздный кодовый замок (PUZZLES C.1): четыре диска с оправами четырёх цветов, печать «сверить» и фрески-подсказки на стенах.
        # Замок стоит далеко от печатей лестницы (NE-угол), чтобы PuzzleRewards.solved не растворил их раньше победы в испытании.
        for i, x in enumerate((c0 - 3, c0 - 1, c0 + 1, c0 + 3)):
            t.set(x, y0 + 1, c0 + 5, C('star_disc'), color=i, symbol=(i * 3 + 1) % 8)
        t.set(c0, y0 + 1, c0 + 4, C('star_lock'), solved=False, nbt={'id': C('star_lock')})
        for col, (x, z) in enumerate(((6, 1), (TOWER - 2, 8), (14, TOWER - 2), (1, 12))):
            t.set(x, y0 + 5, z, C('star_fresco'), color=col, symbol=0, hidden=True)


# ================================================================ JSON: пулы, структуры, наборы
def pool(name, location, *more):
    """more — дополнительные варианты (местоположение, вес)."""
    elements = [{'weight': 2 if more else 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(location),
                                                         'processors': 'minecraft:empty', 'projection': 'rigid'}}]
    for loc, w in more:
        elements.append({'weight': w, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(loc),
                                                  'processors': 'minecraft:empty', 'projection': 'rigid'}})
    write_json(os.path.join(DATA, 'worldgen/template_pool', name + '.json'), {'fallback': 'minecraft:empty', 'elements': elements})


def structure(name, pool_name, biomes_tag, y, adaptation='beard_box'):
    write_json(os.path.join(DATA, 'worldgen/structure', name + '.json'), {
        'type': 'minecraft:jigsaw', 'biomes': '#' + c(f'has_structure/{biomes_tag}'), 'max_distance_from_center': 80,
        'size': 1, 'spawn_overrides': {}, 'start_height': {'absolute': y}, 'start_pool': c(pool_name),
        'step': 'surface_structures', 'terrain_adaptation': adaptation, 'use_expansion_hack': False})


def structure_set(name, structure_name, spacing, separation, salt):
    write_json(os.path.join(DATA, 'worldgen/structure_set', name + '.json'), {
        'placement': {'type': 'minecraft:random_spread', 'salt': salt, 'separation': separation, 'spacing': spacing},
        'structures': [{'structure': c(structure_name), 'weight': 1}]})


def landmark_sets():
    """Все крупные постройки Рая — один набор с весами: в одной ячейке сетки ровно одна постройка, наложений нет.
    Цитадель — отдельно и не ближе 4 чанков к достопримечательностям."""
    write_json(os.path.join(DATA, 'worldgen/structure_set/heaven_landmarks.json'), {
        'placement': {'type': 'minecraft:random_spread', 'salt': 731410, 'separation': 4, 'spacing': 11},
        'structures': [{'structure': c(n), 'weight': w} for n, w in (
            ('sky_village', 4), ('sky_ruins', 4), ('sky_lighthouse', 3), ('airship_wreck', 3), ('beam_temple', 3),
            ('cloud_castle', 2), ('trial_tower', 2), ('abyss_rift', 3), ('memory_shrine', 3), ('eden_garden', 3))]})
    write_json(os.path.join(DATA, 'worldgen/structure_set/citadels.json'), {
        'placement': {'type': 'minecraft:random_spread', 'salt': 731404, 'separation': 18, 'spacing': 48,
                      'exclusion_zone': {'other_set': c('heaven_landmarks'), 'chunk_count': 4}},
        'structures': [{'structure': c('citadel'), 'weight': 1}]})


def biome_tag(name, *biomes):
    write_json(os.path.join(DATA, 'tags/worldgen/biome/has_structure', name + '.json'), {'values': [c(b) for b in biomes]})


def loot():
    def chest_table(name, pools):
        write_json(os.path.join(DATA, 'loot_table/chests', name + '.json'),
                   {'type': 'minecraft:chest', 'pools': pools, 'random_sequence': c('chests/' + name)})

    def p(rolls, entries):
        return {'rolls': rolls if isinstance(rolls, int) else {'type': 'minecraft:uniform', 'min': rolls[0], 'max': rolls[1]},
                'entries': [{'type': 'minecraft:empty', 'weight': w} if n is None else
                            {'type': 'minecraft:item', 'name': n, 'weight': w,
                             **({'modifier': [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': a, 'max': b}}]} if b > 1 else {})}
                            for n, w, a, b in entries]}

    chest_table('sky_village', [
        p((3, 6), [(C('manna_berries'), 10, 2, 6), (C('cloud_fluff'), 8, 2, 8), (C('skywood_sapling'), 5, 1, 3),
                   (C('starquartz'), 5, 1, 3), ('minecraft:bread', 6, 1, 3), (C('cloud_parachute'), 3, 1, 2), ('minecraft:saddle', 2, 1, 1)]),
        p(1, [(C('bronze_key'), 1, 1, 1), (None, 3, 1, 1)])])
    chest_table('ruins_bronze', [
        p((3, 5), [(C('raw_etherite'), 10, 1, 4), (C('starquartz'), 8, 1, 4), ('minecraft:gold_ingot', 6, 1, 4), (C('cloud_parachute'), 4, 1, 2)]),
        p(1, [(C('silver_key'), 1, 1, 1), (None, 1, 1, 1)])])
    chest_table('ruins_silver', [
        p((3, 5), [(C('etherite_ingot'), 8, 1, 3), (C('starquartz'), 8, 2, 6), (C('seraph_feather'), 6, 1, 2),
                   ('minecraft:diamond', 4, 1, 2), (C('light_spear'), 1, 1, 1)]),
        p(1, [(C('golden_key'), 1, 1, 1), (None, 1, 1, 1)])])
    chest_table('ruins_gold', [
        p((3, 6), [(C('etherite_ingot'), 8, 2, 5), (C('seraph_feather'), 6, 2, 4), (C('starbow'), 2, 1, 1),
                   (C('light_spear'), 2, 1, 1), ('minecraft:enchanted_golden_apple', 1, 1, 1), (C('music_disc_heavenly_choir'), 2, 1, 1)])])
    for n in range(1, 8):
        chest_table(f'trial_heaven_{n}', [
            p((1 + n // 3, 2 + n // 2), [(C('starquartz'), 8, 1, 2 + n), (C('etherite_ingot'), 4, 1, 1 + n // 3), (C('seraph_feather'), 3, 1, 2),
                                        (C('cloud_parachute'), 2, 1, 2), (C('rune_of_wind'), 1, 1, 1), (C('rune_of_light'), 1, 1, 1),
                                        (C('rune_of_sky'), 1, 1, 1), (C('rune_of_stars'), 1, 1, 1)])])
    chest_table('trial_tools', [p(1, [(C('tuning_fork'), 1, 1, 1)])])
    chest_table('beam_temple', [
        p(1, [(C('beam_prism'), 1, 1, 1)]),
        p((3, 5), [(C('sun_lens'), 3, 1, 1), (C('beam_mirror'), 4, 2, 4), (C('rune_of_light'), 3, 1, 2), (C('etherite_ingot'), 3, 1, 3),
                   (C('starquartz'), 4, 3, 8), (C('light_receiver'), 2, 1, 1)])])
    chest_table('cloud_castle', [
        p((4, 6), [(C('etherite_ingot'), 6, 2, 5), (C('seraph_feather'), 4, 2, 4), (C('rune_of_sky'), 3, 1, 2), (C('rune_of_wind'), 3, 1, 2),
                   (C('cloud_lift'), 3, 2, 4), (C('golden_key'), 2, 1, 1), (C('halo'), 1, 1, 1), ('minecraft:diamond', 3, 2, 4)])])
    chest_table('airship_wreck', [
        p((4, 7), [(C('starquartz'), 6, 3, 8), (C('cloud_parachute'), 5, 1, 3), (C('golden_fleece'), 3, 1, 3), ('minecraft:gunpowder', 4, 2, 6),
                   ('minecraft:map', 2, 1, 1), (C('silver_key'), 2, 1, 1), (C('music_disc_heavenly_choir'), 1, 1, 1), (C('sky_beacon'), 1, 1, 1)])])
    chest_table('trial_tower_top', [
        p(1, [(C('seraph_wings'), 1, 1, 1)]),
        p((3, 5), [(C('etherite_ingot'), 6, 3, 6), (C('rune_of_light'), 3, 1, 2), (C('rune_of_wind'), 3, 1, 2), (C('starbow'), 1, 1, 1),
                   (C('light_spear'), 1, 1, 1), (C('golden_key'), 2, 1, 1)])])
    chest_table('citadel_treasure', [
        p((4, 7), [(C('etherite_ingot'), 8, 3, 6), (C('starquartz'), 8, 4, 10), ('minecraft:diamond', 6, 2, 5),
                   (C('seraph_feather'), 5, 2, 5), ('minecraft:golden_apple', 4, 1, 3), (C('music_disc_heavenly_choir'), 1, 1, 1)])])


def main():
    counts = {
        'деревня': sky_village(),
        'руины': sky_ruins(),
        'цитадель': citadel(),
        'башня': trial_tower(),
        'большая деревня': grand_village(),
        'храм лучей': beam_temple(),
        'облачный замок': cloud_castle(),
        'маяк': sky_lighthouse(),
        'галеон': airship_wreck(),
    }
    pool('sky_village/center', 'sky_village/center', ('sky_village/grand', 1))
    for n in ('beam_temple', 'cloud_castle', 'sky_lighthouse', 'airship_wreck'):
        pool(f'{n}/main', f'{n}/main')
    pool('sky_ruins/main', 'sky_ruins/main')
    pool('citadel/main', 'citadel/main')
    pool('trial_tower/main', 'trial_tower/main')
    structure('sky_village', 'sky_village/center', 'sky_village', 118)
    structure('sky_ruins', 'sky_ruins/main', 'sky_ruins', 66)
    structure('citadel', 'citadel/main', 'citadel', 168)
    structure('trial_tower', 'trial_tower/main', 'trial_tower', 96)
    structure('beam_temple', 'beam_temple/main', 'beam_temple', 110)
    structure('cloud_castle', 'cloud_castle/main', 'cloud_castle', 150)
    structure('sky_lighthouse', 'sky_lighthouse/main', 'sky_lighthouse', 90)
    structure('airship_wreck', 'airship_wreck/main', 'airship_wreck', 140)
    landmark_sets()
    biome_tag('beam_temple', 'golden_meadows', 'crystal_spires', 'heaven_gardens', 'rainbow_shoals')
    biome_tag('cloud_castle', 'cloud_forest', 'storm_peak', 'star_glade', 'golden_meadows')
    biome_tag('sky_lighthouse', 'golden_meadows', 'rainbow_shoals', 'cloud_forest', 'heaven_gardens', 'star_glade')
    biome_tag('airship_wreck', 'cloud_forest', 'rainbow_shoals', 'storm_peak', 'golden_meadows')
    biome_tag('sky_village', 'golden_meadows', 'rainbow_shoals', 'heaven_gardens')
    biome_tag('sky_ruins', 'golden_meadows', 'cloud_forest', 'crystal_spires', 'rainbow_shoals', 'storm_peak', 'star_glade')
    biome_tag('citadel', 'crystal_spires', 'golden_meadows', 'cloud_forest', 'rainbow_shoals', 'storm_peak', 'star_glade', 'heaven_gardens')
    biome_tag('trial_tower', 'golden_meadows', 'storm_peak', 'crystal_spires', 'star_glade')
    write_json(os.path.join(DATA, 'tags/worldgen/structure/wisp_guides_to.json'),
               {'values': [c('sky_village'), c('sky_ruins'), c('citadel'), c('trial_tower'), c('beam_temple'), c('cloud_castle'),
                           c('sky_lighthouse'), c('airship_wreck'), c('abyss_rift')]})
    write_json(os.path.join(DATA, 'tags/worldgen/structure/citadels.json'), {'values': [c('citadel')]})
    loot()
    print('ok: блоков в шаблонах', counts)


if __name__ == '__main__':
    main()
