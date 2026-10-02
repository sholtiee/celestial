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
        root.save(path, gzipped=True)
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
    # фонари на столбах вдоль дорог
    for x, z in ((12, 12), (20, 12), (12, 20), (20, 20)):
        t.fill(x, top + 1, z, x, top + 2, z, FENCE, north=False, south=False, east=False, west=False, waterlogged=False)
        t.set(x, top + 3, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    # жители и пегасы
    for x, y, z in inside[:3]:
        t.entity(x, y, z, {'id': C('angel'), 'PersistenceRequired': True})
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
    t.set(cx, top + 1, cz, C('seraph_seal'))
    t.fill(cx - 1, top + 1, cz + 10, cx + 1, top + 1, cz + 12, RADIANT)
    t.set(cx, top + 2, cz + 11, C('celestial_altar'))
    # сокровищница за аркой
    t.walls(16, top + 1, 34, 28, top + 5, 39, BRICKS)
    t.fill(17, top + 1, 35, 27, top + 4, 38, 'minecraft:air')
    t.fill(21, top + 1, 34, 23, top + 3, 34, 'minecraft:air')
    chest(t, 20, top + 1, 38, 'celestial:chests/citadel_treasure', facing='north')
    chest(t, 24, top + 1, 38, 'celestial:chests/citadel_treasure', facing='north')
    return t.save('citadel/main')


# ================================================================ JSON: пулы, структуры, наборы
def pool(name, location):
    write_json(os.path.join(DATA, 'worldgen/template_pool', name + '.json'), {
        'fallback': 'minecraft:empty',
        'elements': [{'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(location),
                                               'processors': 'minecraft:empty', 'projection': 'rigid'}}]})


def structure(name, pool_name, biomes_tag, y, adaptation='beard_box'):
    write_json(os.path.join(DATA, 'worldgen/structure', name + '.json'), {
        'type': 'minecraft:jigsaw', 'biomes': '#' + c(f'has_structure/{biomes_tag}'), 'max_distance_from_center': 80,
        'size': 1, 'spawn_overrides': {}, 'start_height': {'absolute': y}, 'start_pool': c(pool_name),
        'step': 'surface_structures', 'terrain_adaptation': adaptation, 'use_expansion_hack': False})


def structure_set(name, structure_name, spacing, separation, salt):
    write_json(os.path.join(DATA, 'worldgen/structure_set', name + '.json'), {
        'placement': {'type': 'minecraft:random_spread', 'salt': salt, 'separation': separation, 'spacing': spacing},
        'structures': [{'structure': c(structure_name), 'weight': 1}]})


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
    chest_table('citadel_treasure', [
        p((4, 7), [(C('etherite_ingot'), 8, 3, 6), (C('starquartz'), 8, 4, 10), ('minecraft:diamond', 6, 2, 5),
                   (C('seraph_feather'), 5, 2, 5), ('minecraft:golden_apple', 4, 1, 3), (C('music_disc_heavenly_choir'), 1, 1, 1)])])


def main():
    counts = {
        'деревня': sky_village(),
        'руины': sky_ruins(),
        'цитадель': citadel(),
    }
    pool('sky_village/center', 'sky_village/center')
    pool('sky_ruins/main', 'sky_ruins/main')
    pool('citadel/main', 'citadel/main')
    structure('sky_village', 'sky_village/center', 'sky_village', 118)
    structure('sky_ruins', 'sky_ruins/main', 'sky_ruins', 66)
    structure('citadel', 'citadel/main', 'citadel', 168)
    structure_set('sky_villages', 'sky_village', 28, 10, 731402)
    structure_set('sky_ruins', 'sky_ruins', 22, 8, 731403)
    structure_set('citadels', 'citadel', 48, 18, 731404)
    biome_tag('sky_village', 'golden_meadows', 'rainbow_shoals')
    biome_tag('sky_ruins', 'golden_meadows', 'cloud_forest', 'crystal_spires', 'rainbow_shoals')
    biome_tag('citadel', 'crystal_spires', 'golden_meadows', 'cloud_forest', 'rainbow_shoals')
    write_json(os.path.join(DATA, 'tags/worldgen/structure/wisp_guides_to.json'),
               {'values': [c('sky_village'), c('sky_ruins'), c('citadel')]})
    write_json(os.path.join(DATA, 'tags/worldgen/structure/citadels.json'), {'values': [c('citadel')]})
    loot()
    print('ok: блоков в шаблонах', counts)


if __name__ == '__main__':
    main()
