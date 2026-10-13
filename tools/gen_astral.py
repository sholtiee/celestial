"""Астрал (волна 0.6, S5.1): мир астероидов, туманностей и звёздной пыли; «Звёздные врата»; святилища хоров и Звёздный алтарь в мире.

Измерение: вечная звёздная ночь. Рельеф — астероиды из трёхмерного шума двух масштабов (крупные глыбы и россыпь мелочи) в полосе
высот 20–240, сверху — звёздная пыль, внутри — астральная порода. Биомы: Звёздный дрейф (россыпь астероидов), Туманность (кристаллы,
светящаяся дымка), Кристальные поля, Пыльные реки. Физика — профиль `CelestialDimensions.ASTRAL` (гравитация ×0.15, без урона от
падения, из пустоты выносит на остров).

Постройки: святилища девяти хоров (`star_shrine/<хор>`, gen_choirs) — набор «по одному на точку»; Звёздный алтарь — 4 яруса
(кольца-уступы) с вершиной `star_altar/summit` (gen_faceless), ставится кольцевым размещением у центра мира.
Врата: рамка из блоков звёздного камня (4 звёздных камня → блок), зажигается Шестернёй Вечности.
"""
import math
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, self_drop, shaped, write_json
from gen_places import jigsaw, structure_set
from gen_story import lang_patch
from gen_structures import Template

H = T.hexrgb
WG = os.path.join(DATA, 'worldgen')
MIN_Y, HEIGHT = -64, 384
BIOMES = ['star_drift', 'nebula', 'crystal_fields', 'dust_rivers']
CHOIRS = ['seraphim', 'cherubim', 'thrones', 'dominions', 'virtues', 'powers', 'principalities', 'archangels', 'angels']


def put(img, x, y, col, a=255):
    if 0 <= x < 16 and 0 <= y < 16:
        img.putpixel((x, y), (*col, a))


# ---------------------------------------------------------------- блоки
def blocks():
    rock = T.noisy('astral_rock', [H(h) for h in ('#141634', '#1b1e44', '#232854', '#2c3264')], cell=3, grain=0.35)
    r = T.rng_for('astral_rock_stars')
    for _ in range(5):  # вкрапления звёзд
        x, y = r.randrange(16), r.randrange(16)
        put(rock, x, y, T.mix(H('#9fb4ff'), H('#ffffff'), r.random()))
    save_png(rock, 'block/astral_rock')
    dust = T.noisy('astral_dust', [H(h) for h in ('#5a5aa8', '#6a6ab8', '#7a7cc8', '#8c8ed8')], cell=2, grain=0.45)
    r = T.rng_for('astral_dust_sparks')
    for _ in range(10):
        put(dust, r.randrange(16), r.randrange(16), T.mix(H('#d8e4ff'), H('#fff4c0'), r.random()))
    save_png(dust, 'block/astral_dust')
    bricks = T.bricks('astral_bricks', [H(h) for h in ('#1e2250', '#262b60', '#2f356e')], '#0e1028')
    for x, y in ((2, 1), (10, 1), (6, 9), (14, 9)):
        put(bricks, x, y, H('#c8d8ff'))
    save_png(bricks, 'block/astral_bricks')
    crystal = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = T.rng_for('astral_crystal')
    for y in range(16):
        for x in range(16):
            d = abs(x - 7.5) + abs(y - 7.5) * 0.6
            col = T.mix(H('#e8d8ff'), H('#7a4ad8'), min(1.0, d / 9))
            a = 255 if (x in (0, 15) or y in (0, 15)) else 170 + int(60 * r.random())
            crystal.putpixel((x, y), (*col, a))
    save_png(crystal, 'block/astral_crystal')
    flower = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(8, 16):
        put(flower, 7 + (y % 3 == 0), y, H('#3a5aa8'))
    for dx, dy in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):  # звёздочка
        put(flower, 7 + dx, 5 + dy, H('#fff4c0') if (dx, dy) == (0, 0) else H('#a8c8ff'))
    put(flower, 4, 10, H('#6a8ad8'))
    put(flower, 10, 11, H('#6a8ad8'))
    save_png(flower, 'block/star_flower')
    block = T.noisy('star_stone_block', [H(h) for h in ('#4a6aa8', '#5a7cbc', '#6a8ed0', '#7aa0e0')], cell=3, grain=0.3)
    for k in range(5):  # пятиконечная звезда
        a = k * 2 * math.pi / 5 - math.pi / 2
        for i in range(6):
            put(block, round(7.5 + math.cos(a) * i), round(7.5 + math.sin(a) * i), H('#e8f0ff'))
    for x in range(16):
        put(block, x, 0, H('#2a3a68'))
        put(block, x, 15, H('#2a3a68'))
        put(block, 0, x, H('#2a3a68'))
        put(block, 15, x, H('#2a3a68'))
    save_png(block, 'block/star_stone_block')
    for n in ('astral_rock', 'astral_dust', 'astral_bricks', 'star_stone_block'):
        model('block/' + n, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + n)}})
        blockstate(n, {'variants': {'': {'model': c('block/' + n)}}})
        item_def(n, c('block/' + n))
        self_drop(n)
    model('block/astral_crystal', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/astral_crystal')}, 'render_type': 'minecraft:translucent'})
    blockstate('astral_crystal', {'variants': {'': {'model': c('block/astral_crystal')}}})
    item_def('astral_crystal', c('block/astral_crystal'))
    self_drop('astral_crystal')
    model('block/star_flower', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/star_flower')}, 'render_type': 'minecraft:cutout'})
    blockstate('star_flower', {'variants': {'': {'model': c('block/star_flower')}}})
    model('item/star_flower', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/star_flower')}})
    item_def('star_flower', c('item/star_flower'))
    self_drop('star_flower')
    portal()
    shaped('star_stone_block', c('star_stone_block'), ['SS', 'SS'], {'S': c('star_stone')}, 1, 'building')
    shaped('astral_bricks', c('astral_bricks'), ['RR', 'RR'], {'R': c('astral_rock')}, 4, 'building')
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in ('astral_rock', 'astral_bricks', 'astral_crystal', 'star_stone_block')])
    append_tag('block', 'minecraft:mineable/shovel', [c('astral_dust')])
    append_tag('block', 'minecraft:needs_iron_tool', [c('star_stone_block')])
    append_tag('block', 'minecraft:supports_vegetation', [c('astral_dust')])


def portal():
    """Завеса «Звёздных врат»: тёмная синь с кружащими искрами (анимация 8 кадров)."""
    frames = 8
    img = Image.new('RGBA', (16, 16 * frames))
    r = T.rng_for('star_portal')
    stars = [(r.random() * 16, r.random() * 16, r.random()) for _ in range(14)]
    for f in range(frames):
        for y in range(16):
            for x in range(16):
                v = 0.5 + 0.5 * math.sin((x * 0.6 + y * 0.4) + f * 0.8) * math.cos((x - y) * 0.3 - f * 0.5)
                col = T.mix(H('#0a0c30'), H('#4a3aa8'), v * 0.8)
                img.putpixel((x, f * 16 + y), (*col, 200))
        for sx, sy, ph in stars:
            a = (f / frames + ph) * 2 * math.pi
            x = int((sx + math.cos(a) * 1.5) % 16)
            y = int((sy + math.sin(a) * 1.5) % 16)
            img.putpixel((x, f * 16 + y), (230, 240, 255, 255))
    save_png(img, 'block/star_portal')
    with open(os.path.join(ASSETS, 'textures/block/star_portal.png.mcmeta'), 'w') as f:
        f.write('{"animation": {"frametime": 3}}\n')
    blockstate('star_portal', {'variants': {'axis=x': {'model': c('block/star_portal_ns')}, 'axis=z': {'model': c('block/star_portal_ew')}}})
    for suffix in ('ns', 'ew'):
        m = {'parent': f'minecraft:block/nether_portal_{suffix}', 'render_type': 'minecraft:translucent',
             'textures': {'particle': c('block/star_portal'), 'portal': c('block/star_portal')}}
        model(f'block/star_portal_{suffix}', m)


# ---------------------------------------------------------------- измерение
def dimension():
    write_json(os.path.join(DATA, 'dimension_type/astral.json'), {
        'ambient_light': 0.25,
        'attributes': {
            'minecraft:visual/sky_color': '#0b1030',
            'minecraft:visual/fog_color': '#141a3c',
            'minecraft:visual/star_brightness': 1.0,
            'minecraft:visual/cloud_height': 600.0,
            'minecraft:visual/ambient_light_color': '#202850',
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'never', 'can_sleep': 'never', 'destroy_on_use': False},
            'minecraft:gameplay/respawn_anchor_works': False,
        },
        'coordinate_scale': 1.0, 'default_clock': 'minecraft:overworld', 'has_ceiling': False, 'has_ender_dragon_fight': False,
        'has_fixed_time': True, 'has_skylight': True, 'height': HEIGHT, 'infiniburn': '#minecraft:infiniburn_end', 'logical_height': HEIGHT,
        'min_y': MIN_Y, 'monster_spawn_block_light_limit': 0, 'monster_spawn_light_level': 0, 'timelines': '#celestial:in_astral'})
    write_json(os.path.join(DATA, 'tags/timeline/in_astral.json'), {'values': []})
    points = {'star_drift': (0.0, 0.0), 'nebula': (0.6, 0.5), 'crystal_fields': (-0.6, 0.4), 'dust_rivers': (0.1, -0.6)}
    write_json(os.path.join(DATA, 'dimension/astral.json'), {
        'type': c('astral'),
        'generator': {'type': 'minecraft:noise', 'settings': c('astral'), 'biome_source': {'type': 'minecraft:multi_noise', 'biomes': [
            {'biome': c(b), 'parameters': {'temperature': t, 'humidity': h, 'continentalness': 0.0, 'erosion': 0.0, 'weirdness': 0.0,
                                            'depth': 0.0, 'offset': 0.0}} for b, (t, h) in points.items()]}}})
    old = os.path.join(WG, 'biome/astral_void.json')
    if os.path.exists(old):
        os.remove(old)


def noises():
    def gradient(a, b, va, vb):
        return {'type': 'minecraft:gradient', 'axis': 'y', 'from_coordinate': a, 'from_value': va, 'to_coordinate': b, 'to_value': vb}

    def add(a, b):
        return {'type': 'minecraft:add', 'left': a, 'right': b}

    def mul(a, b):
        return {'type': 'minecraft:mul', 'left': a, 'right': b}

    def noise(name, octave, octaves, amps=None, xz=1.0, y=1.0):
        spec = {'base_amplitude': 1.0, 'base_octave': octave, 'octave_count': octaves}
        if amps:
            spec['amplitude_modifiers'] = amps
        write_json(os.path.join(WG, f'noise/astral_{name}.json'), spec)
        return {'type': 'minecraft:noise', 'noise': c(f'astral_{name}'), 'xz_scale': xz, 'y_scale': y}

    for n in ('temperature', 'humidity'):
        write_json(os.path.join(WG, f'density_function/astral/{n}.json'), noise(n, -8, 2, y=0.0))
    big = noise('big', -6, 3, [1.0, 0.5, 0.25], y=1.6)        # крупные глыбы ~60–100 блоков
    small = noise('small', -4, 2, [1.0, 0.4], y=1.2)          # россыпь мелочи
    field = noise('field', -8, 1, y=0.0)                      # где гуще, где реже (по биомам)
    band = add(gradient(10, 70, 1.0, 0.0), gradient(180, 250, 0.0, 1.0))  # прочь от низа и верха полосы
    big_d = add(add(mul(big, 2.1), -0.78), mul(band, -2.0))
    small_d = add(add(add(mul(small, 2.4), -1.25), mul(field, 0.35)), mul(band, -2.0))
    rough = noise('rough', -3, 2, y=1.0)
    islands = add({'type': 'minecraft:max', 'left': big_d, 'right': small_d}, mul(rough, 0.12))
    final = add({'type': 'minecraft:interpolated', 'cell_size_xz': 4, 'cell_size_y': 4, 'input': islands}, {'type': 'minecraft:beardifier'})
    write_json(os.path.join(WG, 'density_function/astral/final_density.json'), final)


def surface():
    write_json(os.path.join(WG, 'material_rule/astral.json'), {'type': 'minecraft:sequence', 'sequence': [
        {'type': 'minecraft:condition', 'if_true': {'type': 'minecraft:biome', 'biome_is': [c('crystal_fields')]},
         'then_run': {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor',
                      'then_run': {'type': 'minecraft:block', 'result_state': c('astral_rock')}}},
        {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor',
         'then_run': {'type': 'minecraft:block', 'result_state': c('astral_dust')}},
        {'type': 'minecraft:condition', 'if_true': {'type': 'minecraft:biome', 'biome_is': [c('dust_rivers')]},
         'then_run': {'type': 'minecraft:condition', 'if_true': 'minecraft:under_floor',
                      'then_run': {'type': 'minecraft:block', 'result_state': c('astral_dust')}}},
    ]})
    write_json(os.path.join(WG, 'noise_settings/astral.json'), {
        'debug_functions': [], 'default_block': c('astral_rock'), 'default_fluid': 'minecraft:air', 'disable_mob_generation': False,
        'legacy_random_source': False, 'material_rule': c('astral'), 'noise': {'min_y': MIN_Y, 'height': HEIGHT},
        'noise_router': {'chunk_surface_level': 0.0, 'continents': 0.0, 'depth': 0.0, 'erosion': 0.0, 'ridges': 0.0,
                         'final_density': c('astral/final_density'), 'temperature': c('astral/temperature'), 'vegetation': c('astral/humidity')},
        'sea_level': -64, 'spawn_target': []})


ON_ANY = [
    {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform', 'min_inclusive': {'absolute': 20}, 'max_inclusive': {'absolute': 245}}},
    {'type': 'minecraft:environment_scan', 'direction_of_search': 'down', 'max_steps': 32,
     'allowed_search_condition': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
     'target_condition': {'type': 'minecraft:has_sturdy_face', 'direction': 'up'}},
    {'type': 'minecraft:offset', 'x': 0, 'y': 1, 'z': 0},
]


def features():
    def feature(name, obj):
        write_json(os.path.join(WG, 'feature', name + '.json'), obj)

    def placed(name, feat, count):
        place = [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'}] + ON_ANY + [
            {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'}},
            {'type': 'minecraft:biome'}]
        write_json(os.path.join(WG, 'placed_feature', name + '.json'), {'feature': c(feat), 'placement': place})

    feature('star_flower', {'type': 'minecraft:simple_block', 'to_place': {'id': c('star_flower')}})
    feature('astral_crystal_spike', {'type': 'minecraft:block_column', 'allowed_placement': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                                     'direction': 'up', 'prioritize_tip': True,
                                     'layers': [{'height': {'type': 'minecraft:uniform', 'min_inclusive': 1, 'max_inclusive': 4},
                                                 'provider': {'id': c('astral_crystal')}}]})
    placed('astral_flowers', 'star_flower', 14)
    placed('astral_flowers_sparse', 'star_flower', 4)
    placed('astral_crystals', 'astral_crystal_spike', 3)
    placed('astral_crystals_dense', 'astral_crystal_spike', 12)


def biomes():
    feats = {
        'star_drift': {9: [c('astral_crystals'), c('astral_flowers_sparse')]},
        'nebula': {9: [c('astral_crystals'), c('astral_flowers')]},
        'crystal_fields': {9: [c('astral_crystals_dense'), c('astral_flowers_sparse')]},
        'dust_rivers': {9: [c('astral_flowers')]},
    }
    look = {'star_drift': ('#0b1030', '#141a3c', 0.0015), 'nebula': ('#1a0e3a', '#3a1e5a', 0.008),
            'crystal_fields': ('#0e1438', '#1e2a5a', 0.003), 'dust_rivers': ('#0c1232', '#22285a', 0.004)}
    for name, by_step in feats.items():
        steps = [[] for _ in range(11)]
        for k, f in by_step.items():
            steps[k] = f
        sky, fog, p = look[name]
        write_json(os.path.join(WG, 'biome', name + '.json'), {
            'attributes': {'minecraft:visual/sky_color': sky, 'minecraft:visual/fog_color': fog, 'minecraft:visual/water_fog_color': '#1a2050',
                           'minecraft:visual/ambient_particles': {'argument': [{'particle': {'type': 'minecraft:end_rod'}, 'probability': p}],
                                                                  'modifier': 'append'}},
            'carvers': [], 'downfall': 0.0, 'effects': {'grass_color': '#6a7ac8', 'foliage_color': '#5a6ab8', 'water_color': '#3a4aa8'},
            'features': steps, 'has_precipitation': False, 'temperature': 0.5})
    write_json(os.path.join(DATA, 'tags/worldgen/biome/is_astral.json'), {'values': [c(b) for b in BIOMES]})


# ---------------------------------------------------------------- Звёздный алтарь
def altar_structure():
    """Звёздный алтарь: четыре яруса-кольца из астральной кладки (каждый уже предыдущего, по краю — огни), сверху — вершина
    star_altar/summit (gen_faceless.summit_template). Парит в пустоте у центра мира — без привязки к рельефу."""
    from gen_faceless import summit_template
    R0, STEP, TH = 33, 4, 5
    S = 2 * R0 + 3
    cx = S // 2
    top = 4 * TH
    t = Template(S, top + 14, S)
    t.fill(0, 0, 0, S - 1, top + 13, S - 1, 'minecraft:air')
    for k in range(4):
        R = R0 - STEP * k
        y0 = k * TH
        for x in range(S):
            for z in range(S):
                d = math.hypot(x - cx, z - cx)
                if d > R + 0.5:
                    continue
                for y in range(y0, y0 + TH):
                    if d < R - 2.5 and y < y0 + TH - 1:
                        continue  # ярус полый внутри
                    edge = d > R - 1.5
                    t.set(x, y, z, c('astral_bricks') if edge or y == y0 + TH - 1 else c('astral_rock'))
        n = 12 + 4 * (3 - k)
        for i in range(n):
            a = i * 2 * math.pi / n
            t.set(round(cx + math.sin(a) * (R - 0.5)), y0 + TH, round(cx - math.cos(a) * (R - 0.5)), 'minecraft:sea_lantern')
    summit = summit_template()
    off = (S - summit.size[0]) // 2
    t.paste(summit, off, top - 1, off)
    t.save('star_altar/main')
    write_json(os.path.join(DATA, 'worldgen/template_pool/star_altar/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c('star_altar/main'),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}}]})
    write_json(os.path.join(DATA, 'worldgen/structure/star_altar.json'), {
        'type': 'minecraft:jigsaw', 'biomes': '#' + c('is_astral'), 'max_distance_from_center': 80, 'size': 1, 'spawn_overrides': {},
        'start_height': {'absolute': 96}, 'start_pool': c('star_altar/main'), 'step': 'surface_structures', 'terrain_adaptation': 'none',
        'use_expansion_hack': False})
    write_json(os.path.join(DATA, 'worldgen/structure_set/star_altar.json'), {
        'placement': {'type': 'minecraft:concentric_rings', 'count': 1, 'distance': 4, 'spread': 1, 'preferred_biomes': '#' + c('is_astral'),
                      'salt': 0},
        'structures': [{'structure': c('star_altar'), 'weight': 1}]})


def shrines():
    """Святилища хоров парят в пустоте на высоте 100–200: набор «одно из девяти на точку»."""
    write_json(os.path.join(DATA, 'worldgen/template_pool/star_shrine/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(f'star_shrine/{ch}'),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}} for ch in CHOIRS]})
    write_json(os.path.join(DATA, 'worldgen/structure/star_shrine.json'), {
        'type': 'minecraft:jigsaw', 'biomes': '#' + c('is_astral'), 'max_distance_from_center': 80, 'size': 1, 'spawn_overrides': {},
        'start_height': {'type': 'minecraft:uniform', 'min_inclusive': {'absolute': 100}, 'max_inclusive': {'absolute': 190}},
        'start_pool': c('star_shrine/main'), 'step': 'surface_structures', 'terrain_adaptation': 'none', 'use_expansion_hack': False})
    structure_set('star_shrine', 14, 6, 6600601, exclusion=('star_altar', 4))
    write_json(os.path.join(DATA, 'tags/worldgen/structure/star_shrines.json'), {'values': [c('star_shrine')]})
    append_tag('worldgen/structure', 'celestial:codex_places', [c('star_shrine'), c('star_altar')])


def lang():
    lang_patch({
        'dimension.celestial.astral.drift': ('Звёздный ветер вынес тебя на остров', 'The star wind carried you back to an island'),
        'biome.celestial.star_drift': ('Звёздный дрейф', 'Star Drift'),
        'biome.celestial.nebula': ('Туманность', 'Nebula'),
        'biome.celestial.crystal_fields': ('Кристальные поля', 'Crystal Fields'),
        'biome.celestial.dust_rivers': ('Пыльные реки', 'Dust Rivers'),
        'block.celestial.astral_rock': ('Астральная порода', 'Astral Rock'),
        'block.celestial.astral_dust': ('Звёздная пыль', 'Star Dust'),
        'block.celestial.astral_bricks': ('Астральная кладка', 'Astral Bricks'),
        'block.celestial.astral_crystal': ('Астральный кристалл', 'Astral Crystal'),
        'block.celestial.star_flower': ('Звёздоцвет', 'Star Flower'),
        'block.celestial.star_stone_block': ('Блок звёздного камня', 'Block of Star Stone'),
        'block.celestial.star_portal': ('Звёздные врата', 'Star Gate'),
        'structure.celestial.star_shrine': ('Святилище хора', 'Choir Shrine'),
        'structure.celestial.star_altar': ('Звёздный алтарь', 'Star Altar'),
        'codex.celestial.place.star_shrine': ('парящий островок со Звёздным диском. Сложи созвездие хора Звёздными камнями.',
                                              'a floating islet with a Star Disk. Lay out the choir\'s constellation with Star Stones.'),
        'codex.celestial.place.star_altar': ('четыре яруса в центре Астрала; на вершине — престол Безликого. Откроется, когда соберёшь семь хоров.',
                                             'four tiers at the centre of the Astral; on top is the Faceless One\'s throne. It opens once seven choirs are gathered.'),
    })


def main():
    blocks()
    dimension()
    noises()
    surface()
    features()
    biomes()
    shrines()
    altar_structure()
    lang()
    print('ok: Астрал — мир, врата, святилища, алтарь')


if __name__ == '__main__':
    main()
