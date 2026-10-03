"""Ледяные Чертоги (волна 0.4, шаг 1): блоки и измерение celestial:frozen_halls.

Рельеф: суша и замёрзшее море (уровень 62), ледники с узкими глубокими трещинами, редкие ледяные шпили.
Ванильные фичи льда (шипы, айсберги, синий лёд, ели в снегу) + заморозка воды и снег сверху.
"""
import os

import textures as T
from gen_abyss import append_tag
from gen_assets import DATA, c, save_png, self_drop, simple_cube, write_json, blockstate, model, item_def
from gen_story import lang_patch

WG = os.path.join(DATA, 'worldgen')
SEA = 62


def blocks():
    stone = [T.hexrgb(h) for h in ('#4a5a70', '#55677f', '#61748c', '#6f839a')]
    save_png(T.noisy('frost_stone', stone, cell=3, grain=0.35), 'block/frost_stone')
    save_png(T.bricks('frost_stone_bricks', [T.hexrgb(h) for h in ('#5a6c84', '#667a92', '#7489a2')], '#2f3b4c'), 'block/frost_stone_bricks')
    ore = T.noisy('frost_ore', stone, cell=3, grain=0.35)
    r = T.rng_for('frost_ore_specks')
    for _ in range(6):
        x, y = r.randrange(2, 14), r.randrange(2, 14)
        for i, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (-1, 0), (1, 1))):
            ore.putpixel((x + dx, y + dy), (*T.hexrgb(['#dff6ff', '#9fdcff', '#5fb8f0', '#ffffff', '#bfe9ff'][i]), 255))
    save_png(ore, 'block/frost_ore')
    from PIL import Image
    crystal = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for cx, h, w, cols in ((7, 13, 2, ('#d6fff0', '#5ff0b8', '#2fb58a')), (3, 8, 1, ('#ffe0f6', '#ff8ad8', '#c04a9a')),
                           (11, 10, 1, ('#e0ecff', '#7fb0ff', '#3a6ad0'))):
        for y in range(16 - h, 16):
            half = max(0, int(w * (y - (16 - h)) / h + 0.5))
            for x in range(cx - half, cx + half + 1):
                col = cols[0] if x == cx - half else cols[2] if x == cx + half else cols[1]
                crystal.putpixel((x, y), (*T.hexrgb(col), 255))
    save_png(crystal, 'block/aurora_crystal')
    for n in ('frost_stone', 'frost_stone_bricks', 'frost_ore'):
        simple_cube(n)
        self_drop(n)
    model('block/aurora_crystal', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/aurora_crystal')}})
    rot = {'up': {}, 'down': {'x': 180}, 'north': {'x': 90}, 'south': {'x': 90, 'y': 180}, 'east': {'x': 90, 'y': 90}, 'west': {'x': 90, 'y': 270}}
    blockstate('aurora_crystal', {'variants': {f'facing={f}': {'model': c('block/aurora_crystal'), **v} for f, v in rot.items()}})
    model('item/aurora_crystal', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/aurora_crystal')}})
    item_def('aurora_crystal', c('item/aurora_crystal'))
    self_drop('aurora_crystal')
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in ('frost_stone', 'frost_stone_bricks', 'frost_ore', 'aurora_crystal')])
    append_tag('block', 'minecraft:needs_iron_tool', [c('frost_ore')])
    append_tag('block', 'minecraft:needs_stone_tool', [c('frost_stone'), c('frost_stone_bricks')])


def dimension():
    write_json(os.path.join(DATA, 'dimension_type/frozen_halls.json'), {
        'ambient_light': 0.05,
        'attributes': {
            'minecraft:audio/background_music': {'default': {'max_delay': 9000, 'min_delay': 2400, 'replace_current_music': True,
                                                             'sound': 'minecraft:music.overworld.frozen_peaks'}},
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'always', 'can_sleep': 'when_dark',
                                            'error_message': {'translate': 'block.minecraft.bed.no_sleep'}},
            'minecraft:gameplay/respawn_anchor_works': False,
            'minecraft:visual/cloud_color': '#ccd8e6ff',
            'minecraft:visual/fog_color': '#a8c4d8',
            'minecraft:visual/sky_color': '#3a5a7a',
        },
        'coordinate_scale': 1.0, 'default_clock': 'minecraft:overworld', 'has_ceiling': False, 'has_ender_dragon_fight': False,
        'has_skylight': True, 'height': 256, 'infiniburn': '#minecraft:infiniburn_overworld', 'logical_height': 256, 'min_y': 0,
        'monster_spawn_block_light_limit': 0,
        'monster_spawn_light_level': {'type': 'minecraft:uniform', 'min_inclusive': 0, 'max_inclusive': 7},
        'timelines': '#minecraft:in_overworld',
    })
    write_json(os.path.join(DATA, 'dimension/frozen_halls.json'), {
        'type': c('frozen_halls'),
        'generator': {'type': 'minecraft:noise', 'settings': c('frozen_halls'), 'biome_source': {'type': 'minecraft:multi_noise', 'biomes': [
            point('glacier', 0.0, 0.0), point('glacier', 0.4, -0.3),
            point('ice_spires', 0.6, 0.5), point('aurora_fields', -0.6, 0.4), point('frozen_sea', -0.5, -0.6)]}},
    })


def point(name, temperature, humidity):
    return {'biome': c(name), 'parameters': {'temperature': temperature, 'humidity': humidity, 'continentalness': 0.0,
                                             'erosion': 0.0, 'weirdness': 0.0, 'depth': 0.0, 'offset': 0.0}}


def noises():
    def grad(a, b, va, vb):
        return {'type': 'minecraft:gradient', 'axis': 'y', 'from_coordinate': a, 'from_value': va, 'to_coordinate': b, 'to_value': vb}

    def add(a, b):
        return {'type': 'minecraft:add', 'left': a, 'right': b}

    def mul(a, b):
        return {'type': 'minecraft:mul', 'left': a, 'right': b}

    def noise(name, octave, octaves=3, amps=None):
        write_json(os.path.join(WG, f'noise/frozen_{name}.json'),
                   {'base_amplitude': 1.0, 'base_octave': octave, 'octave_count': octaves, **({'amplitude_modifiers': amps} if amps else {})})
        return {'type': 'minecraft:noise', 'noise': c(f'frozen_{name}'), 'xz_scale': 1.0, 'y_scale': 0.0}

    for name in ('temperature', 'humidity'):
        write_json(os.path.join(WG, f'density_function/frozen/{name}.json'), noise(name, -8, 2))
    land = add(add(add(grad(30, 110, 1.0, -1.0), mul(noise('continent', -7, 3), 0.9)), mul(noise('rough', -4, 2), 0.12)), -0.22)
    # ледниковые щиты: плоские плато с отвесными стенами (двумерная маска → вертикальные края)
    glacier = {'type': 'minecraft:range_choice', 'input': noise('glacier', -6, 2), 'min_inclusive': 0.22, 'max_exclusive': 10.0,
               'when_in_range': grad(78, 96, 2.0, -2.0), 'when_out_of_range': -1.0}
    # трещины ледников: где шум близок к нулю — узкий глубокий разрез
    crevasse = mul({'type': 'minecraft:max', 'left': add(0.045, mul({'type': 'minecraft:abs', 'input': noise('crevasse', -5, 2)}, -1.0)),
                    'right': 0.0}, -45.0)
    spires = add(mul({'type': 'minecraft:max', 'left': add(noise('spires', -3, 2, [1.0, 0.4]), -0.36), 'right': 0.0}, 6.0),
                 grad(64, 150, 0.0, -5.0))
    terrain = {'type': 'minecraft:max', 'left': add({'type': 'minecraft:max', 'left': land, 'right': glacier}, crevasse), 'right': spires}
    final = add({'type': 'minecraft:interpolated', 'cell_size_xz': 4, 'cell_size_y': 4, 'input': terrain}, {'type': 'minecraft:beardifier'})
    write_json(os.path.join(WG, 'density_function/frozen/final_density.json'), final)


def surface():
    def block(b):
        return {'type': 'minecraft:block', 'result_state': b}

    def biome_is(*names):
        return {'type': 'minecraft:biome', 'biome_is': [c(n) for n in names]}

    write_json(os.path.join(WG, 'material_rule/frozen_halls.json'), {'type': 'minecraft:sequence', 'sequence': [
        'minecraft:bedrock_floor',
        {'type': 'minecraft:condition', 'if_true': biome_is('frozen_sea'), 'then_run': {'type': 'minecraft:condition',
                                                                                         'if_true': 'minecraft:on_floor', 'then_run': block('minecraft:gravel')}},
        {'type': 'minecraft:condition', 'if_true': biome_is('ice_spires'), 'then_run': {'type': 'minecraft:condition',
                                                                                         'if_true': 'minecraft:on_floor', 'then_run': block('minecraft:packed_ice')}},
        # отвесные стены ледников и шпилей — синий и плотный лёд, а не камень
        {'type': 'minecraft:condition', 'if_true': {'type': 'minecraft:steep'}, 'then_run': block('minecraft:blue_ice')},
        {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor', 'then_run': block('minecraft:snow_block')},
        {'type': 'minecraft:condition', 'if_true': 'minecraft:under_floor', 'then_run': block('minecraft:packed_ice')},
    ]})
    write_json(os.path.join(WG, 'noise_settings/frozen_halls.json'), {
        'debug_functions': [], 'default_block': c('frost_stone'), 'default_fluid': 'minecraft:water', 'disable_mob_generation': False,
        'legacy_random_source': False, 'material_rule': c('frozen_halls'), 'noise': {'min_y': 0, 'height': 256},
        'noise_router': {'chunk_surface_level': 0.0, 'continents': 0.0, 'depth': 0.0, 'erosion': 0.0, 'ridges': 0.0,
                         'final_density': c('frozen/final_density'), 'temperature': c('frozen/temperature'), 'vegetation': c('frozen/humidity')},
        'sea_level': SEA, 'spawn_target': []})


def features():
    def feature(name, obj):
        write_json(os.path.join(WG, 'feature', name + '.json'), obj)

    def placed(name, feat, placement):
        write_json(os.path.join(WG, 'placed_feature', name + '.json'), {'feature': feat, 'placement': placement})

    feature('ore_frost', {'type': 'minecraft:ore', 'discard_chance_on_air_exposure': 0.2, 'size': 6,
                          'targets': [{'state': {'id': c('frost_ore')}, 'target': {'predicate_type': 'minecraft:block_match', 'block': c('frost_stone')}}]})
    placed('ore_frost', c('ore_frost'), [{'type': 'minecraft:count', 'count': 8}, {'type': 'minecraft:in_square'},
                                         {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform', 'min_inclusive': {'absolute': 4},
                                                                                       'max_inclusive': {'absolute': 70}}}, {'type': 'minecraft:biome'}])
    feature('aurora_crystal', {'type': 'minecraft:simple_block', 'to_place': {'id': c('aurora_crystal'), 'properties': {'facing': 'up', 'waterlogged': 'false'}}})
    for name, count in (('aurora_crystals', 6), ('aurora_crystals_rare', 1)):
        placed(name, c('aurora_crystal'), [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                                          {'type': 'minecraft:heightmap', 'heightmap': 'MOTION_BLOCKING'}, {'type': 'minecraft:biome'},
                                          {'type': 'minecraft:count', 'count': 6},
                                          {'type': 'minecraft:offset', 'x': {'type': 'minecraft:uniform', 'min_inclusive': -3, 'max_inclusive': 3},
                                           'y': 0, 'z': {'type': 'minecraft:uniform', 'min_inclusive': -3, 'max_inclusive': 3}},
                                          {'type': 'minecraft:heightmap', 'heightmap': 'MOTION_BLOCKING'},
                                          {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:all_of', 'predicates': [
                                              {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                                              {'type': 'minecraft:has_sturdy_face', 'direction': 'up', 'offset': [0, -1, 0]}]}}])


def biomes():
    MC = 'minecraft:'
    steps = {
        'glacier': {6: [c('ore_frost')], 9: [MC + 'spruce_on_snow', c('aurora_crystals_rare')], 10: [MC + 'freeze_top_layer']},
        'ice_spires': {4: [MC + 'ice_spike'], 6: [c('ore_frost')], 9: [c('aurora_crystals_rare')], 10: [MC + 'freeze_top_layer']},
        'aurora_fields': {6: [c('ore_frost')], 9: [c('aurora_crystals')], 10: [MC + 'freeze_top_layer']},
        'frozen_sea': {2: [MC + 'iceberg_packed', MC + 'iceberg_blue'], 6: [c('ore_frost')], 7: [MC + 'blue_ice'], 10: [MC + 'freeze_top_layer']},
    }
    colors = {'glacier': ('#3a5a7a', '#a8c4d8'), 'ice_spires': ('#2f4d6e', '#9cbad6'), 'aurora_fields': ('#2a3f66', '#8fd8c0'),
              'frozen_sea': ('#3a5f80', '#b4cde0')}
    for name, by_step in steps.items():
        feats = [[] for _ in range(11)]
        for step, f in by_step.items():
            feats[step] = f
        sky, fog = colors[name]
        write_json(os.path.join(WG, 'biome', name + '.json'), {
            'attributes': {'minecraft:visual/sky_color': sky, 'minecraft:visual/fog_color': fog, 'minecraft:visual/water_fog_color': '#3d6a8a',
                           'minecraft:visual/ambient_particles': {'argument': [{'particle': {'type': 'minecraft:white_ash'}, 'probability': 0.006}],
                                                                  'modifier': 'append'}},
            'carvers': [], 'downfall': 0.6,
            'effects': {'grass_color': '#80b4a0', 'foliage_color': '#6a9a8a', 'water_color': '#3d6a8a'},
            'features': feats, 'has_precipitation': True, 'temperature': -0.7})


def portal():
    """Завеса портала: наша анимированная текстура портала Рая, перекрашенная в ледяные тона; форма модели — как у ванильного портала."""
    import colorsys
    import json
    from PIL import Image
    from gen_assets import ASSETS, VANILLA, shaped
    src = Image.open(os.path.join(ASSETS, 'textures/block/heaven_portal.png')).convert('RGBA')
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            nr, ng, nb = colorsys.hls_to_rgb(0.53, min(1.0, l * 1.05), min(1.0, sat * 0.8 + 0.2))
            px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    save_png(src, 'block/frozen_portal')
    with open(os.path.join(ASSETS, 'textures/block/frozen_portal.png.mcmeta'), 'w') as f:
        json.dump({'animation': {'frametime': 3, 'interpolate': True}}, f)
    blockstate('frozen_portal', {'variants': {'axis=x': {'model': c('block/frozen_portal_ns')}, 'axis=z': {'model': c('block/frozen_portal_ew')}}})
    for suffix in ('ns', 'ew'):
        with open(os.path.join(VANILLA, f'models/block/nether_portal_{suffix}.json')) as f:
            m = json.load(f)
        m['textures'] = {'particle': c('block/frozen_portal'), 'portal': c('block/frozen_portal')}
        model(f'block/frozen_portal_{suffix}', m)
    # рамка: 4 кирпича морозного камня из синего льда и звёздного обломка — делается в Верхнем мире
    shaped('frost_stone_bricks_from_ice', c('frost_stone_bricks'), [' B ', 'BSB', ' B '],
           {'B': 'minecraft:blue_ice', 'S': c('star_fragment')}, 4, 'building')


def main():
    blocks()
    portal()
    dimension()
    noises()
    surface()
    features()
    biomes()
    lang_patch({
        'block.celestial.frost_stone': ('Морозный камень', 'Frost Stone'),
        'block.celestial.frost_stone_bricks': ('Кирпичи из морозного камня', 'Frost Stone Bricks'),
        'block.celestial.aurora_crystal': ('Кристалл сияния', 'Aurora Crystal'),
        'block.celestial.frost_ore': ('Руда морозной стали', 'Frost Steel Ore'),
        'biome.celestial.glacier': ('Ледник', 'Glacier'),
        'biome.celestial.ice_spires': ('Ледяные шпили', 'Ice Spires'),
        'biome.celestial.aurora_fields': ('Поля сияния', 'Aurora Fields'),
        'biome.celestial.frozen_sea': ('Замёрзшее море', 'Frozen Sea'),
        'block.celestial.frozen_portal': ('Ледяные врата', 'Frozen Gate'),
        'story.celestial.frozen_portal_lit': ('§bЯдро вспыхивает холодом. Рамка затягивается льдом — Ледяные врата открыты!',
                                              '§bThe Core flares with cold. The frame frosts over: the Frozen Gate is open!'),
    })
    print('ok: Ледяные Чертоги')


if __name__ == '__main__':
    main()
