"""Места Отблесков S3 (LORE §5c): «Два алтаря» в Бездне (Каин и Авель), «Долина костей» в Ледяных Чертогах (Сухие кости, Иез. 37),
«Камень Иакова» в Раю (Лестница Иакова, Быт. 28). Небольшие постройки с Отпечатком света; ставятся в мир как обычные постройки мода.
"""
import math
import os
import random

from gen_abyss import append_tag
from gen_assets import DATA, c, write_json
from gen_places import jigsaw, structure_set, floor_place
from gen_story import lang_patch
from gen_structures import Template, island_base

MC = lambda n: 'minecraft:' + n  # noqa: E731
AIR = MC('air')


def anchor(t, x, y, z, scene):
    t.set(x, y, z, c('memory_anchor'), nbt={'id': c('memory_anchor'), 'Scene': scene})


def two_altars():
    """Бездна: тёмная поляна, два каменных алтаря — у Авеля дым столбом (костёр на сене), у Каина пепел; между ними алый цветок."""
    S = 21
    t = Template(S, 12, S)
    t.fill(0, 1, 0, S - 1, 11, S - 1, AIR)
    rng = random.Random(4101)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 10, z - 10)
            if d <= 10.3:
                t.set(x, 0, z, c('abyss_stone') if rng.random() < 0.7 else c('gloom_moss'))
    for ax, top in ((5, MC('hay_block')), (15, c('abyss_stone'))):  # алтари: ступень, кладка, верх
        t.fill(ax - 1, 1, 6, ax + 1, 1, 8, c('abyss_bricks'))
        t.fill(ax, 2, 7, ax, 2, 7, c('abyss_bricks'))
        t.set(ax, 3, 7, top) if ax == 5 else t.set(ax, 3, 7, c('abyss_bricks'))
        if ax == 5:
            t.set(ax, 4, 7, MC('campfire'), lit=True, signal_fire=True, facing='south', waterlogged=False)  # дым Авеля — столбом вверх
        else:
            t.set(ax, 4, 7, MC('campfire'), lit=False, signal_fire=False, facing='south', waterlogged=False)  # огонь Каина не принят
            for dx, dz in ((-1, 0), (1, 0), (0, 1)):
                t.set(ax + dx, 2, 7 + dz, MC('gray_carpet'))  # пепел, стелется у подножия
    t.set(10, 1, 11, MC('poppy'))  # алый цветок там, где упал Авель
    for x, z in ((8, 13), (9, 14), (11, 15), (12, 16), (14, 17)):  # следы Каина уводят прочь
        t.set(x, 0, z, c('gloom_moss'))
    for _ in range(10):
        x, z = rng.randrange(1, S - 1), rng.randrange(1, S - 1)
        if 7 < math.hypot(x - 10, z - 10) < 10 and t.get(x, 1, z) == AIR:
            t.set(x, 1, z, c('glowshroom'))
    anchor(t, 10, 1, 9, 'brothers')
    return t.save('two_altars/main')


def bone_valley():
    """Чертоги: лощина в снегу, рёбра и кости вмёрзли в наст, посередине — камень пророка."""
    S = 25
    t = Template(S, 10, S)
    t.fill(0, 1, 0, S - 1, 9, S - 1, AIR)
    rng = random.Random(4202)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 12, z - 12)
            if d <= 12.3:
                t.set(x, 0, z, MC('packed_ice') if rng.random() < 0.15 else MC('snow_block'))
    for _ in range(26):  # кости: блоки костей и черепа, иногда «ребро» аркой
        x, z = rng.randrange(2, S - 2), rng.randrange(2, S - 2)
        if 3 < math.hypot(x - 12, z - 12) < 11:
            r = rng.random()
            if r < 0.5:
                t.set(x, 1, z, MC('bone_block'), axis=rng.choice(['x', 'z']))
            elif r < 0.7:
                t.set(x, 1, z, MC('skeleton_skull'), rotation=rng.randint(0, 15))
            else:
                t.set(x, 1, z, MC('bone_block'), axis='y')
                t.set(x, 2, z, MC('bone_block'), axis='y')
                t.set(x + 1, 3, z, MC('bone_block'), axis='x')
    for x in range(S):
        for z in range(S):
            if math.hypot(x - 12, z - 12) <= 12 and t.get(x, 1, z) == AIR and rng.random() < 0.25:
                t.set(x, 1, z, MC('snow'), layers=1)
    t.fill(11, 1, 11, 13, 1, 13, MC('cobbled_deepslate'))  # камень пророка
    t.set(12, 2, 12, MC('polished_deepslate_slab'), type='bottom', waterlogged=False)
    anchor(t, 12, 1, 15, 'dry_bones')
    return t.save('bone_valley/main')


def jacob_stone():
    """Рай: островок с камнем-изголовьем; над ним в небо уходит «лестница» света — столб светящихся ступеней."""
    S = 17
    t = Template(S, 30, S)
    t.fill(0, 0, 0, S - 1, 29, S - 1, AIR)
    rng = random.Random(4303)
    top = 6
    island_base(t, 8, 8, 7, top, 6, rng)
    t.set(8, top + 1, 8, c('skystone'))  # камень-изголовье
    t.set(9, top + 1, 8, MC('moss_carpet'))
    for i in range(18):  # ступени света: по спирали вверх, редкие
        a = i * 0.7
        x, z = round(8 + math.cos(a) * 2.2), round(8 + math.sin(a) * 2.2)
        t.set(x, top + 3 + i, z, c('radiant_stone') if i % 3 == 0 else MC('light'), **({} if i % 3 == 0 else {'level': 12, 'waterlogged': False}))
    anchor(t, 7, top + 1, 9, 'jacob_ladder')
    return t.save('jacob_stone/main')


def main():
    two_altars()
    bone_valley()
    jacob_stone()
    floor_place('two_altars', [c('dark_wastes'), c('glowshroom_forest')], 20, 110, 10, 21, 4, offset=-1)
    structure_set('two_altars', 40, 14, 4410011)
    jigsaw('bone_valley', [c('glacier'), c('aurora_fields')], 0, adaptation='beard_thin')
    structure_set('bone_valley', 44, 16, 4410022)
    jigsaw('jacob_stone', [c('golden_meadows'), c('heaven_gardens'), c('star_glade')], 0, adaptation='none')
    structure_set('jacob_stone', 48, 18, 4410033)
    append_tag('worldgen/structure', 'celestial:codex_places', [c('two_altars'), c('bone_valley'), c('jacob_stone')])
    lang_patch({
        'structure.celestial.two_altars': ('Два алтаря', 'The Two Altars'),
        'structure.celestial.bone_valley': ('Долина костей', 'Valley of Bones'),
        'structure.celestial.jacob_stone': ('Камень Иакова', 'Jacob\'s Stone'),
        'codex.celestial.place.two_altars': ('два алтаря во тьме Бездны: у одного дым идёт к небу, у другого стелется по земле. Между ними — алый цветок.',
                                             'two altars in the dark of the Abyss: from one the smoke rises to heaven, from the other it creeps along the ground. Between them, a red flower.'),
        'codex.celestial.place.bone_valley': ('лощина в снегах Чертогов, полная костей. В её середине — камень, на котором стоял пророк.',
                                              'a hollow in the snows of the Halls, full of bones. At its centre — the stone where the prophet stood.'),
        'codex.celestial.place.jacob_stone': ('островок с камнем-изголовьем; над ним в небо уходят ступени света.',
                                              'an islet with a stone for a pillow; above it, steps of light climb into the sky.'),
    })
    print('ok: места Отблесков — Два алтаря, Долина костей, Камень Иакова')


if __name__ == '__main__':
    main()
