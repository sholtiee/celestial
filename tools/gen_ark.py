"""Воды и ковчег (LORE §7, S2.7): Ковчег во льдах, голубь-проводник, Масличная ветвь, Неопалимая купина.

Постройки Ледяных Чертогов: frozen_ark (руина корабля 61×26×21: вмёрзшие пары зверей, голубятня, скрижаль Сима, сундуки с Масличной ветвью),
burning_bush_shrine (купина среди тающего снега). Модели: HeavenModels.Dove (32×32).
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

import mob_textures as M
import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, write_json
from gen_places import jigsaw, structure_set
from gen_story import lang_patch
from gen_structures import Template, chest

rgb = T.hexrgb
MC = lambda n: 'minecraft:' + n  # noqa: E731
AIR = MC('air')


# ------------------------------------------------------------------ текстуры
def dove():
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    r = T.rng_for('dove')
    white, gray = rgb('#f6f6f2'), rgb('#cfd2d6')

    def body(face, x, y, fw, fh):
        return M.noise_color(r, white if y < fh - 1 else gray, 0.03)

    def head(face, x, y, fw, fh):
        if face == 'front' and (x, y) in ((0, 1), (2, 1)):
            return rgb('#1a1a22')
        return M.noise_color(r, white, 0.03)

    def wing(face, x, y, fw, fh):
        base = white if x < fw - 2 else gray  # кончики маховых серее
        return M.noise_color(r, T.shade(base, 1.0 - 0.03 * (y % 3)), 0.03)

    M.paint_box(img, 0, 0, 3, 3, 7, body)
    M.paint_box(img, 0, 10, 3, 3, 3, head)
    M.paint_box(img, 12, 10, 1, 1, 1, lambda f, x, y, fw, fh: rgb('#e0a030'))
    M.paint_box(img, 0, 16, 3, 1, 4, body)
    M.paint_box(img, 0, 22, 6, 1, 5, wing)
    save_png(img, 'entity/dove')
    save_png(Image.new('RGBA', (32, 32), (0, 0, 0, 0)), 'entity/dove_glow')
    save_png(M.spawn_egg('#f6f6f2', '#e0a030'), 'item/dove_spawn_egg')
    model('item/dove_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/dove_spawn_egg')}})
    item_def('dove_spawn_egg', c('item/dove_spawn_egg'))


def olive_branch():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(2, 14), (13, 3)], fill=rgb('#6b4a2b'), width=1)
    for x, y in ((4, 10), (6, 8), (8, 6), (10, 4), (12, 3)):
        d.ellipse([x - 1, y - 2, x + 2, y + 1], fill=rgb('#7a9a4a'), outline=rgb('#3f5a24'))
    for x, y in ((5, 12), (8, 10), (10, 8)):
        d.ellipse([x, y, x + 2, y + 2], fill=rgb('#5a6a2a'))
    save_png(img, 'item/olive_branch')
    model('item/olive_branch', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/olive_branch')}})
    item_def('olive_branch', c('item/olive_branch'))


def burning_bush():
    r = T.rng_for('burning_bush')
    frames = 8
    sheet = Image.new('RGBA', (16, 16 * frames), (0, 0, 0, 0))
    base = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = base.load()
    for y in range(6, 16):  # куст из тёмных ветвей и листьев
        for x in range(2, 14):
            if math.hypot(x - 8, (y - 11) * 1.2) < 5.5 and r.random() > 0.2:
                px[x, y] = (*T.shade(rgb('#4a6a2a'), 0.8 + r.random() * 0.4), 255)
    for y in range(11, 16):
        px[8, y] = (*rgb('#4a3220'), 255)
    for f in range(frames):
        img = base.copy()
        d = ImageDraw.Draw(img)
        rf = random.Random(f * 31 + 7)
        for _ in range(5):  # язычки пламени разной высоты, каждый кадр свои
            x = rf.randrange(3, 13)
            h = rf.randrange(4, 9)
            y0 = 12 - rf.randrange(0, 4)
            d.polygon([(x - 1, y0), (x, y0 - h), (x + 1, y0)], fill=rgb('#ff7a2a'))
            d.polygon([(x - 0, y0), (x, y0 - h + 2), (x + 1, y0)], fill=rgb('#ffd24a'))
            d.point((x, y0 - 1), fill=rgb('#fff6c0'))
        sheet.paste(img, (0, 16 * f))
    save_png(sheet, 'block/burning_bush')
    with open(os.path.join(ASSETS, 'textures/block/burning_bush.png.mcmeta'), 'w') as f:
        json.dump({'animation': {'frametime': 3, 'interpolate': True}}, f)
    # купина крупнее блока: два скрещённых полотна 24×24 и внутренний крест — куст выглядит объёмным пламенем (приёмка K1: был мелкий крест)
    def plane(x0, x1, y1, angle):
        f = {'texture': '#cross', 'uv': [0, 0, 16, 16]}
        return {'from': [x0, 0, 8], 'to': [x1, y1, 8], 'shade': False,
                'rotation': {'origin': [8, 8, 8], 'axis': 'y', 'angle': angle, 'rescale': False},
                'faces': {'north': f, 'south': f}}
    model('block/burning_bush', {'ambientocclusion': False, 'textures': {'cross': c('block/burning_bush'), 'particle': c('block/burning_bush')},
                                 'elements': [plane(-4, 20, 22, 45), plane(-4, 20, 22, -45), plane(1, 15, 16, 0),
                                              {**plane(1, 15, 16, 0), 'rotation': {'origin': [8, 8, 8], 'axis': 'y', 'angle': 0, 'rescale': False},
                                               'from': [8, 0, 1], 'to': [8, 16, 15], 'faces': {'east': {'texture': '#cross', 'uv': [0, 0, 16, 16]},
                                                                                              'west': {'texture': '#cross', 'uv': [0, 0, 16, 16]}}}]})
    blockstate('burning_bush', {'variants': {'': {'model': c('block/burning_bush')}}})
    model('item/burning_bush', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/burning_bush')}})
    item_def('burning_bush', c('item/burning_bush'))
    append_tag('block', 'minecraft:dragon_immune', [c('burning_bush')])
    append_tag('block', 'minecraft:wither_immune', [c('burning_bush')])


# ------------------------------------------------------------------ постройки
def ark():
    """Корабль на боку льдов: корпус 60 блоков вдоль x, палуба, каюта со скрижалью и сундуками, голубятня на корме, клетки изо льда с парами зверей."""
    t = Template(61, 26, 21)
    rng = random.Random(3000)
    t.fill(0, 0, 0, 60, 25, 20, AIR)
    PL, LG, DK = MC('spruce_planks'), MC('stripped_spruce_log'), MC('dark_oak_planks')
    cz = 10

    def half_width(x):
        u = abs(x - 28) / 32.5
        return 8.6 * max(0.0, 1 - u ** 3) ** 0.6

    for x in range(61):
        hw = half_width(x)
        if hw < 1.0:
            continue
        for z in range(21):
            dz = (z - cz) / hw
            if abs(dz) > 1.0:
                continue
            floor_y = 3 + round(dz * dz * 7)
            edge = abs(dz) > 1 - 1.2 / hw
            top = 11 if edge else 8
            t.set(x, floor_y, z, DK if (x + z) % 3 else LG)
            if edge:
                for y in range(floor_y + 1, top + 1):
                    t.set(x, y, z, PL if (x + y) % 4 else LG)
    # палуба с люком посередине
    for x in range(61):
        hw = half_width(x)
        for z in range(21):
            if hw >= 1.0 and abs((z - cz) / hw) < 1 - 1.2 / hw and not (18 <= x <= 22 and 8 <= z <= 12):
                t.set(x, 8, z, PL)
    # каюта на палубе: стены, двускатная крыша, дверь с кормы
    for x in range(21, 41):
        for z in range(5, 16):
            if x in (21, 40) or z in (5, 15):
                t.fill(x, 9, z, x, 12, z, PL)
    for x in range(20, 42):
        t.fill(x, 13, 5, x, 13, 15, DK)
        t.fill(x, 14, 7, x, 14, 13, DK)
        t.fill(x, 15, 9, x, 15, 11, DK)
    t.fill(21, 9, 9, 21, 11, 11, AIR)
    for x in (26, 30, 34):
        t.set(x, 11, 5, MC('glass_pane'), waterlogged=False)
        t.set(x, 11, 15, MC('glass_pane'), waterlogged=False)
    t.set(38, 9, 7, c('lore_tablet'), nbt={'id': c('lore_tablet'), 'Sheet': 'ark'}, facing='west')
    chest(t, 38, 9, 11, 'celestial:chests/frozen_ark', facing='west')
    chest(t, 38, 9, 13, 'celestial:chests/frozen_ark', facing='west')
    t.set(30, 9, 10, MC('campfire'), lit=False, facing='north', signal_fire=False, waterlogged=False)
    # клетки изо льда с парами зверей (вмёрзшие в потоп)
    pairs = [(8, MC('sheep')), (13, MC('cow')), (46, MC('pig')), (51, MC('horse'))]
    for x, kind in pairs:
        for side, z in ((0, 4), (1, 16)):
            for dx in range(-3, 4):
                for dy in range(0, 4):
                    for dz in (-1, 0, 1):
                        shell = abs(dx) == 3 or dy == 3 or dz in (-1, 1) and abs(dx) == 3
                        if abs(dx) == 3 or dy == 3 or abs(dz) == 1 and dy < 3 and False:
                            t.set(x + dx, 9 + dy, z + dz, MC('ice'))
            for dx in range(-2, 3):
                for dz in (-1, 0, 1):
                    t.set(x + dx, 9, z + dz, AIR) if False else None
            for dz in (-1, 1):
                t.fill(x - 3, 9, z + dz, x + 3, 12, z + dz, MC('ice'))
            t.fill(x - 2, 9, z, x + 2, 11, z, AIR)
            t.entity(x - 1, 9, z, {'id': kind, 'NoAI': True, 'Silent': True, 'Invulnerable': True, 'PersistenceRequired': True})
            t.entity(x + 1, 9, z, {'id': kind, 'NoAI': True, 'Silent': True, 'Invulnerable': True, 'PersistenceRequired': True})
    # голубятня на корме
    t.fill(3, 9, 8, 6, 9, 12, DK)
    t.fill(3, 10, 8, 6, 13, 8, PL)
    t.fill(3, 10, 12, 6, 13, 12, PL)
    t.fill(3, 14, 8, 6, 14, 12, DK)
    t.fill(3, 10, 9, 3, 13, 11, MC('iron_bars'), north=False, south=False, east=True, west=True, waterlogged=False)
    t.entity(5, 10, 10, {'id': c('dove'), 'NoAI': True, 'Silent': True, 'PersistenceRequired': True})
    t.entity(4, 10, 9, {'id': c('dove'), 'NoAI': True, 'Silent': True, 'PersistenceRequired': True})
    # мачта-обломок, снежные и ледяные наносы вокруг и на палубе
    t.fill(28, 9, 10, 28, 24, 10, LG)
    # Наносы (приёмка K1: раньше — частокол случайных столбов и случайные глыбы в трюме). Снег привален к корпусу гладким сугробом:
    # высота падает с расстоянием от борта, сверху — снег слоями; лёд затёк в трюм только через пробоину у носа.
    def hull_dist(x, z):
        best = 99.0
        for hx in range(61):
            hw = half_width(hx)
            if hw < 1.0:
                continue
            d = max(0.0, abs(z - cz) - hw)
            best = min(best, ((x - hx) ** 2 + d * d) ** 0.5)
        return best

    for x in range(61):
        for z in range(21):
            hw = half_width(x)
            if hw >= 1.0 and abs((z - cz) / hw) <= 1.0:
                continue
            d = hull_dist(x, z)
            wave = 0.8 * __import__('math').sin(x * 0.45) + 0.6 * __import__('math').cos(z * 0.7 + x * 0.2)
            h = 6.5 - d * 1.1 + wave
            if h <= 0.4:
                continue
            top = int(h)
            if top >= 1:
                t.fill(x, 0, z, x, top - 1, z, MC('packed_ice'))
                t.set(x, top - 1, z, MC('snow_block'))
            layers = max(1, min(7, round((h - top) * 8)))
            t.set(x, top, z, MC('snow'), layers=layers)
    for x in range(48, 58):  # пробоина у носа: лёд затёк в трюм языком
        for z in range(6, 15):
            hw = half_width(x)
            if hw >= 1.0 and abs((z - cz) / hw) < 0.9:
                floor_y = 3 + round(((z - cz) / hw) ** 2 * 7)
                depth = max(0, round((x - 47) * 0.45 - abs(z - cz) * 0.3))
                for y in range(floor_y + 1, min(8, floor_y + 1 + depth)):
                    t.set(x, y, z, MC('blue_ice') if (x + y + z) % 4 == 0 else MC('packed_ice'))
    # трюм: стойла с сеном, бочки, корыта; лестница из люка
    for x in range(8, 46, 6):
        if 16 <= x <= 24:
            continue
        for z in (8, 12):
            t.fill(x, 4, z, x, 5, z, MC('spruce_fence'), waterlogged=False)
        t.set(x + 1, 4, 10, MC('hay_block'), axis='y')
        t.set(x + 2, 4, 9, MC('barrel'), facing='up', open=False)
        if x % 12 == 2:
            t.set(x + 2, 4, 11, MC('cauldron'))
    for i, x in enumerate(range(19, 24)):
        t.set(x, 4 + i, 10, MC('spruce_stairs'), facing='east', half='bottom', shape='straight', waterlogged=False)
    for x in range(30, 38, 3):
        t.set(x, 7, 10, MC('lantern'), hanging=True, waterlogged=False)
    # каюта Ноя: постель (под будущий Отблеск-сон), стол, книги
    t.set(36, 9, 13, MC('white_bed'), facing='north', part='foot', occupied=False)
    t.set(36, 9, 12, MC('white_bed'), facing='north', part='head', occupied=False)
    t.set(33, 9, 7, MC('spruce_fence'), waterlogged=False)
    t.set(33, 10, 7, MC('spruce_pressure_plate'), powered=False)
    t.set(32, 9, 6, MC('chiseled_bookshelf'), facing='south', **{f'slot_{i}_occupied': i % 2 == 0 for i in range(6)})
    t.set(34, 12, 10, MC('lantern'), hanging=True, waterlogged=False)
    for _ in range(90):  # сугробы на палубе и снег на крыше
        x, z = rng.randrange(1, 60), rng.randrange(2, 19)
        if t.get(x, 8, z) == PL and t.get(x, 9, z) in (None, AIR):
            t.set(x, 9, z, MC('snow'), layers=rng.randrange(1, 4))
    t.save('frozen_ark/main')


def shrine():
    t = Template(15, 8, 15)
    rng = random.Random(3100)
    BR = c('frost_stone_bricks')
    t.fill(0, 0, 0, 14, 7, 14, AIR)
    for x in range(15):
        for z in range(15):
            d = math.hypot(x - 7, z - 7)
            if d <= 7.2:
                t.set(x, 0, z, MC('snow_block') if d > 4.5 else BR)
    for x in range(15):
        for z in range(15):
            d = math.hypot(x - 7, z - 7)
            if 2.5 < d < 4.4 and rng.random() < 0.7:
                t.set(x, 0, z, MC('coarse_dirt') if rng.random() < 0.5 else MC('gravel'))  # земля оттаяла вокруг куста
    t.set(7, 1, 7, c('burning_bush'))
    for dx, dz in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        t.fill(7 + dx, 1, 7 + dz, 7 + dx, 3, 7 + dz, BR)
        t.set(7 + dx, 4, 7 + dz, MC('lantern'), hanging=False, waterlogged=False)
    for dx, dz in ((0, -5), (0, 5), (-5, 0), (5, 0)):
        t.set(7 + dx, 1, 7 + dz, MC('stone_brick_slab'), type='bottom', waterlogged=False)  # камни, на которые садятся разуваться
    t.save('burning_bush_shrine/main')


def loot():
    def item(n, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': n, 'weight': w}
        if hi > 1:
            e['modifier'] = [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e
    write_json(os.path.join(DATA, 'loot_table/chests/frozen_ark.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/frozen_ark'), 'pools': [
            {'rolls': 1, 'entries': [item(c('olive_branch'), 3), {'type': 'minecraft:empty', 'weight': 2}]},
            {'rolls': {'type': 'minecraft:uniform', 'min': 3, 'max': 5}, 'entries': [
                item(c('fur'), 5, 1, 3), item(MC('cooked_cod'), 5, 2, 5), item(MC('wheat'), 4, 3, 8), item(c('hearth_stew'), 3), item(c('spiced_cider'), 3, 1, 2),
                item(c('frost_steel_ingot'), 2, 1, 2), item(c('aurora_crystal'), 3, 1, 3), item(c('starlight_flask'), 2), item(MC('torch'), 4, 4, 10)]}]})


def structures():
    jigsaw('frozen_ark', [c('glacier'), c('aurora_fields')], 0, adaptation='beard_box')
    structure_set('frozen_ark', 56, 22, 4400431)
    jigsaw('burning_bush_shrine', [c('glacier'), c('aurora_fields'), c('ice_spires')], 0, adaptation='beard_thin')
    structure_set('burning_bush_shrine', 26, 10, 4400433)
    write_json(os.path.join(DATA, 'tags/worldgen/structure/dove_guides_to.json'), {'values': ['#celestial:codex_places']})
    append_tag('worldgen/structure', 'celestial:codex_places', [c('frozen_ark'), c('burning_bush_shrine')])


def lang():
    lang_patch({
        'entity.celestial.dove': ('Голубь', 'Dove'),
        'entity.celestial.dove.nothing': ('Голубь не видит вблизи ни одной постройки.', 'The dove sees no building nearby.'),
        'entity.celestial.dove.arrived': ('Голубь привёл тебя: постройка рядом.', 'The dove has brought you: the building is near.'),
        'item.celestial.dove_spawn_egg': ('Яйцо призыва: Голубь', 'Dove Spawn Egg'),
        'item.celestial.olive_branch': ('Масличная ветвь', 'Olive Branch'),
        'item.celestial.olive_branch.lore1': ('ПКМ — призвать голубя-проводника к ближайшей постройке.', 'Use to summon a guiding dove to the nearest building.'),
        'item.celestial.olive_branch.lore2': ('Служит шесть раз. Один голубь на странника.', 'Lasts six uses. One dove per wanderer.'),
        'item.celestial.olive_branch.summoned': ('Голубь взлетел: иди за ним.', 'The dove takes wing: follow it.'),
        'item.celestial.olive_branch.already': ('Голубь уже ведёт тебя.', 'A dove already guides you.'),
        'block.celestial.burning_bush': ('Неопалимая купина', 'Burning Bush'),
        'block.celestial.burning_bush.lore1': ('Горит и не сгорает. Греет путника, как костёр.', 'Burns and is not consumed. Warms the wanderer like a campfire.'),
        'block.celestial.burning_bush.lore2': ('«Сними обувь твою»: босому — полное тепло.', '"Put off thy shoes": the barefoot are fully warmed.'),
        'block.celestial.burning_bush.shoes': ('Пламя отталкивает: сними обувь твою.', 'The flame turns you back: put off thy shoes.'),
        'block.celestial.burning_bush.warm': ('Святая земля. Холод отступил.', 'Holy ground. The cold withdraws.'),
        'structure.celestial.frozen_ark': ('Ковчег во льдах', 'Ark in the Ice'),
        'structure.celestial.burning_bush_shrine': ('Неопалимая купина', 'The Burning Bush'),
        'codex.celestial.place.frozen_ark': ('огромный корабль, вмёрзший в лёд: пары зверей в ледяных клетках, голубятня, скрижаль Сима и Масличная ветвь в каюте.',
                                             'a vast ship frozen in the ice: pairs of beasts in ice cages, a dovecote, Shem\'s tablet and an Olive Branch in the cabin.'),
        'codex.celestial.place.burning_bush_shrine': ('куст, который горит и не сгорает, среди оттаявшей земли. Тепло для путника; подойти нужно без обуви.',
                                                      'a bush that burns and is not consumed, amid thawed ground. Warmth for the wanderer; approach unshod.'),
        'codex.celestial.mob.dove': ('вестник суши. Призывается Масличной ветвью и ведёт к ближайшей постройке.', 'the herald of dry land. Summoned by an Olive Branch, it leads to the nearest building.'),
    })


def main():
    dove()
    olive_branch()
    burning_bush()
    ark()
    shrine()
    loot()
    structures()
    lang()
    print('ok: Ковчег во льдах, голубь, купина')


if __name__ == '__main__':
    main()
