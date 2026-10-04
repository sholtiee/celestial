#!/usr/bin/env python3
"""Генератор датапака измерения Рая (celestial:heaven): тип измерения, шумы, биомы, фичи.

Запуск: python3 tools/gen_world.py
"""
import os

from gen_assets import DATA, write_json, c

WG = os.path.join(DATA, 'worldgen')

# Высоты Рая: мир от 0 до 256, острова живут в полосе ~40..210, ниже — бездна (падение в Верхний мир).
MIN_Y, HEIGHT = 0, 256


def dimension():
    write_json(os.path.join(DATA, 'dimension_type/heaven.json'), {
        'ambient_light': 0.12,
        'attributes': {
            'minecraft:audio/background_music': {
                'default': {'max_delay': 9000, 'min_delay': 2400, 'replace_current_music': True,
                            'sound': 'celestial:music.heaven'}},
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'always', 'can_sleep': 'when_dark',
                                            'error_message': {'translate': 'block.minecraft.bed.no_sleep'}},
            'minecraft:gameplay/respawn_anchor_works': False,
            'minecraft:visual/ambient_light_color': '#2a2618',
            'minecraft:visual/cloud_color': '#f2ffffff',
            # облака ванильного неба проплывают ПОД островами
            'minecraft:visual/cloud_height': 24.0,
            'minecraft:visual/fog_color': '#fdf3d4',
            'minecraft:visual/sky_color': '#8ec9ff',
        },
        'coordinate_scale': 1.0,
        'default_clock': 'minecraft:overworld',
        'has_ceiling': False,
        'has_ender_dragon_fight': False,
        'has_skylight': True,
        'height': HEIGHT,
        'infiniburn': '#minecraft:infiniburn_overworld',
        'logical_height': HEIGHT,
        'min_y': MIN_Y,
        'monster_spawn_block_light_limit': 0,
        'monster_spawn_light_level': {'type': 'minecraft:uniform', 'min_inclusive': 0, 'max_inclusive': 7},
        'timelines': '#minecraft:in_overworld',
    })

    write_json(os.path.join(DATA, 'dimension/heaven.json'), {
        'type': c('heaven'),
        'generator': {
            'type': 'minecraft:noise',
            'settings': c('heaven'),
            'biome_source': {'type': 'minecraft:multi_noise', 'biomes': [
                biome_point('golden_meadows', 0.0, -0.1),
                biome_point('golden_meadows', 0.3, 0.15),
                biome_point('cloud_forest', -0.2, 0.55),
                biome_point('heaven_gardens', 0.35, 0.6),
                biome_point('crystal_spires', 0.75, -0.6),
                biome_point('storm_peak', 0.8, 0.1),
                biome_point('rainbow_shoals', -0.65, -0.35),
                biome_point('star_glade', -0.7, 0.25),
            ]},
        },
    })


def biome_point(name, temperature, humidity):
    return {'biome': c(name), 'parameters': {
        'temperature': temperature, 'humidity': humidity, 'continentalness': 0.0,
        'erosion': 0.0, 'weirdness': 0.0, 'depth': 0.0, 'offset': 0.0}}


# Ярусы островов: (имя, высота основания H, глубина «сосульки» снизу D, высота холмов сверху T)
TIERS = [('low', 72, 38, 14), ('mid', 124, 34, 12), ('high', 176, 30, 10)]


def noises():
    def gradient(a, b, va, vb):
        return {'type': 'minecraft:gradient', 'axis': 'y', 'from_coordinate': a, 'from_value': va, 'to_coordinate': b, 'to_value': vb}

    def add(a, b):
        return {'type': 'minecraft:add', 'left': a, 'right': b}

    def mul(a, b):
        return {'type': 'minecraft:mul', 'left': a, 'right': b}

    # рельеф поверхности и неровности краёв
    write_json(os.path.join(WG, 'noise/heaven_roughness.json'), {'base_amplitude': 1.0, 'base_octave': -4, 'octave_count': 3})
    rough = {'type': 'minecraft:noise', 'noise': c('heaven_roughness'), 'xz_scale': 1.0, 'y_scale': 1.0}
    write_json(os.path.join(WG, 'density_function/heaven/roughness.json'), rough)

    # свой «климат» Рая: биомы меняются каждые ~200-400 блоков (ванильный шум слишком крупный)
    for name in ('temperature', 'humidity'):
        write_json(os.path.join(WG, f'noise/heaven_{name}.json'), {'base_amplitude': 1.0, 'base_octave': -8, 'octave_count': 2})
        write_json(os.path.join(WG, f'density_function/heaven/{name}.json'),
                   {'type': 'minecraft:noise', 'noise': c(f'heaven_{name}'), 'xz_scale': 1.0, 'y_scale': 0.0})

    tiers = []
    for name, h, depth, top in TIERS:
        # 2D-маска яруса: где маска выше порога — там остров
        write_json(os.path.join(WG, f'noise/heaven_islands_{name}.json'),
                   {'base_amplitude': 1.0, 'base_octave': -6, 'octave_count': 3, 'amplitude_modifiers': [1.0, 0.5, 0.25]})
        mask = {'type': 'minecraft:noise', 'noise': c(f'heaven_islands_{name}'), 'xz_scale': 1.0, 'y_scale': 0.0}
        # внизу остров сужается в «сосульку», сверху плавно уходит в холмы
        bottom = gradient(h - depth, h, 1.0, 0.0)
        cap = gradient(h, h + top, 0.0, 1.0)
        density = add(add(add(mul(mask, 1.9), -0.62), mul(add(bottom, cap), -1.0)), mul(c('heaven/roughness'), 0.22))
        write_json(os.path.join(WG, f'density_function/heaven/tier_{name}.json'), density)
        tiers.append(c(f'heaven/tier_{name}'))

    islands = {'type': 'minecraft:max', 'left': tiers[0], 'right': {'type': 'minecraft:max', 'left': tiers[1], 'right': tiers[2]}}
    final = add({'type': 'minecraft:interpolated', 'cell_size_xz': 4, 'cell_size_y': 4, 'input': islands},
                {'type': 'minecraft:beardifier'})
    write_json(os.path.join(WG, 'density_function/heaven/final_density.json'), final)


def surface():
    write_json(os.path.join(WG, 'material_rule/heaven.json'), {'type': 'minecraft:sequence', 'sequence': [
        {'type': 'minecraft:condition', 'if_true': {'type': 'minecraft:biome', 'biome_is': c('crystal_spires')},
         'then_run': {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor',
                      'then_run': {'type': 'minecraft:block', 'result_state': c('skystone')}}},
        {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor',
         'then_run': {'type': 'minecraft:block', 'result_state': c('golden_grass')}},
        {'type': 'minecraft:condition', 'if_true': 'minecraft:under_floor',
         'then_run': {'type': 'minecraft:block', 'result_state': c('heaven_dirt')}},
    ]})

    write_json(os.path.join(WG, 'noise_settings/heaven.json'), {
        'debug_functions': [],
        'default_block': c('skystone'),
        'default_fluid': 'minecraft:water',
        'disable_mob_generation': False,
        'legacy_random_source': False,
        'material_rule': c('heaven'),
        'noise': {'min_y': MIN_Y, 'height': HEIGHT},
        'noise_router': {
            'chunk_surface_level': 0.0, 'continents': 0.0, 'depth': 0.0, 'erosion': 0.0, 'ridges': 0.0,
            'final_density': c('heaven/final_density'),
            'temperature': c('heaven/temperature'),
            'vegetation': c('heaven/humidity'),
        },
        'sea_level': -64,
        'spawn_target': [],
    })


# ------------------------------------------------------------------ фичи
# Карта высот на парящих островах видит только верхний остров, поэтому растительность ставим так:
# случайная высота в полосе островов → ищем вниз первый воздух над твёрдой поверхностью.
ON_ANY_ISLAND = [
    {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform', 'min_inclusive': {'absolute': 40}, 'max_inclusive': {'absolute': 225}}},
    {'type': 'minecraft:environment_scan', 'direction_of_search': 'down', 'max_steps': 32,
     'allowed_search_condition': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
     'target_condition': {'type': 'minecraft:has_sturdy_face', 'direction': 'up'}},
    {'type': 'minecraft:offset', 'x': 0, 'y': 1, 'z': 0},
]


def on_islands(count, extra=None, spread=0):
    """Размещение на поверхности любого яруса; spread>0 — ещё и разброс пятном вокруг точки."""
    out = [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'}] + ON_ANY_ISLAND + [{'type': 'minecraft:biome'}]
    if spread:
        out += [{'type': 'minecraft:count', 'count': spread * 3},
                {'type': 'minecraft:offset', 'x': {'type': 'minecraft:trapezoid', 'min': -spread, 'max': spread, 'plateau': 0},
                 'y': {'type': 'minecraft:trapezoid', 'min': -1, 'max': 1, 'plateau': 0},
                 'z': {'type': 'minecraft:trapezoid', 'min': -spread, 'max': spread, 'plateau': 0}}]
    out.append({'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:all_of', 'predicates': [
        {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'}] + (extra or [])}})
    return out


ON_GRASS = [{'type': 'minecraft:matching_blocks', 'blocks': c('golden_grass'), 'offset': [0, -1, 0]}]


def feature(name, obj):
    write_json(os.path.join(WG, 'feature', name + '.json'), obj)


def placed(name, feat, placement):
    write_json(os.path.join(WG, 'placed_feature', name + '.json'), {'feature': feat, 'placement': placement})


def state(block, **props):
    s = {'id': block}
    if props:
        s['properties'] = {k: str(v).lower() for k, v in props.items()}
    return s


HEAVEN_SOIL = {'type': 'minecraft:rule_based', 'rules': [{
    'if_true': {'type': 'minecraft:not', 'predicate': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:cannot_replace_below_tree_trunk'}},
    'then': {'id': c('heaven_dirt')}}]}
LEAVES = state(c('skywood_leaves'), distance=7, persistent=False, waterlogged=False)
LOG = state(c('skywood_log'), axis='y')
SKYSTONE_RULE = {'predicate_type': 'minecraft:block_match', 'block': c('skystone')}
AIR_RULE = {'predicate_type': 'minecraft:block_match', 'block': 'minecraft:air'}


def features():
    feature('skywood_tree', {
        'type': 'minecraft:tree', 'below_trunk_provider': HEAVEN_SOIL, 'decorators': [], 'ignore_vines': True,
        'foliage_placer': {'type': 'minecraft:blob_foliage_placer', 'height': 4, 'offset': 0, 'radius': 3},
        'foliage_provider': LEAVES, 'minimum_size': {'type': 'minecraft:two_layers_feature_size', 'limit': 1, 'upper_size': 2},
        'trunk_placer': {'type': 'minecraft:straight_trunk_placer', 'base_height': 5, 'height_rand_a': 3, 'height_rand_b': 0},
        'trunk_provider': LOG})
    feature('fancy_skywood_tree', {
        'type': 'minecraft:tree', 'below_trunk_provider': HEAVEN_SOIL, 'decorators': [], 'ignore_vines': True,
        'foliage_placer': {'type': 'minecraft:cherry_foliage_placer', 'corner_hole_chance': 0.25, 'hanging_leaves_chance': 0.3,
                           'hanging_leaves_extension_chance': 0.4, 'height': 5, 'offset': 0, 'radius': 4,
                           'wide_bottom_layer_hole_chance': 0.25},
        'foliage_provider': LEAVES, 'minimum_size': {'type': 'minecraft:two_layers_feature_size', 'upper_size': 2},
        'trunk_placer': {'type': 'minecraft:cherry_trunk_placer', 'base_height': 7, 'height_rand_a': 2, 'height_rand_b': 0,
                         'branch_count': {'type': 'minecraft:weighted_list', 'distribution': [
                             {'data': 1, 'weight': 1}, {'data': 2, 'weight': 2}, {'data': 3, 'weight': 1}]},
                         'branch_end_offset_from_top': {'type': 'minecraft:uniform', 'min_inclusive': -1, 'max_inclusive': 0},
                         'branch_horizontal_length': {'type': 'minecraft:uniform', 'min_inclusive': 2, 'max_inclusive': 4},
                         'branch_start_offset_from_top': {'min_inclusive': -4, 'max_inclusive': -3}},
        'trunk_provider': LOG})
    feature('heaven_trees', {'type': 'minecraft:random_selector',
                             'default': {'feature': c('skywood_tree'), 'placement': []},
                             'features': [{'chance': 0.3, 'feature': {'feature': c('fancy_skywood_tree'), 'placement': []}}]})

    def tree_placement(count, sapling='skywood_sapling'):
        return [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'}] + ON_ANY_ISLAND + [
                {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:would_survive', 'state': state(c(sapling))}},
                {'type': 'minecraft:biome'}]

    placed('trees_golden_meadows', c('heaven_trees'), tree_placement(
        {'type': 'minecraft:weighted_list', 'distribution': [{'data': 2, 'weight': 3}, {'data': 4, 'weight': 2}, {'data': 6, 'weight': 1}]}))
    placed('trees_cloud_forest', c('heaven_trees'), tree_placement(
        {'type': 'minecraft:weighted_list', 'distribution': [{'data': 10, 'weight': 2}, {'data': 14, 'weight': 1}]}))

    def ore(name, block, size, count, lo, hi, discard=0.0):
        feature(name, {'type': 'minecraft:ore', 'discard_chance_on_air_exposure': discard, 'size': size,
                       'targets': [{'state': state(block), 'target': SKYSTONE_RULE}]})
        placed(name, c(name), [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                               {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform',
                                                                             'min_inclusive': {'absolute': lo}, 'max_inclusive': {'absolute': hi}}},
                               {'type': 'minecraft:biome'}])

    ore('ore_etherite', c('etherite_ore'), 6, 10, 30, 200, 0.3)
    ore('ore_etherite_rich', c('etherite_ore'), 9, 6, 30, 200, 0.0)
    ore('ore_starquartz', c('starquartz_ore'), 5, 8, 30, 200)
    ore('ore_radiant', c('radiant_stone'), 4, 2, 30, 200, 0.5)

    def sky_clouds(name, block, size, rarity, lo, hi):
        """Облачные «острова»: рудная фича, которая заменяет воздух на облако."""
        feature(name, {'type': 'minecraft:ore', 'discard_chance_on_air_exposure': 0.0, 'size': size,
                       'targets': [{'state': state(block), 'target': AIR_RULE}]})
        placed(name, c(name), [{'type': 'minecraft:rarity_filter', 'chance': rarity}, {'type': 'minecraft:in_square'},
                               {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform',
                                                                             'min_inclusive': {'absolute': lo}, 'max_inclusive': {'absolute': hi}}},
                               {'type': 'minecraft:biome'}])

    sky_clouds('sky_clouds', c('cloud'), 48, 3, 40, 200)
    sky_clouds('sky_golden_clouds', c('golden_cloud'), 32, 9, 60, 190)
    sky_clouds('sky_rain_clouds', c('rain_cloud'), 40, 2, 120, 210)

    feature('manna_bush', {'type': 'minecraft:simple_block', 'to_place': state(c('manna_bush'), age=3)})
    placed('patch_manna', c('manna_bush'), on_islands(1, ON_GRASS, spread=5))

    feature('sky_crystal', {'type': 'minecraft:simple_block', 'to_place': state(c('sky_crystal'), facing='up', waterlogged=False)})

    def crystals(name, count):
        placed(name, c('sky_crystal'), on_islands(count, [
            {'type': 'minecraft:matching_blocks', 'blocks': [c('skystone'), c('golden_grass')], 'offset': [0, -1, 0]}]))

    feature('rainbow_arc', {'type': c('rainbow_arc')})
    # арка встаёт «ногой» на остров: высота — по поверхности рельефа (heightmap), а не случайная 90–190
    placed('rainbow_arcs', c('rainbow_arc'), [
        {'type': 'minecraft:count', 'count': 2},  # попыток несколько: большинство отбраковывается проверкой «не врезаться»
        {'type': 'minecraft:in_square'},
        {'type': 'minecraft:heightmap', 'heightmap': 'WORLD_SURFACE_WG'},
        {'type': 'minecraft:offset', 'x': 0, 'y': 1, 'z': 0},
        {'type': 'minecraft:biome'}])

    # служебные блоки построек не заменяются фичами (жеоды, руды, облака)
    tag_dir = os.path.join(os.path.dirname(DATA), 'minecraft', 'tags', 'block')
    write_json(os.path.join(tag_dir, 'features_cannot_replace.json'), {'replace': False, 'values': [
        c(n) for n in ('sealed_door', 'trial_crystal', 'trial_goal', 'vanishing_cloud', 'seraph_seal', 'celestial_altar', 'bell_altar',
                       'rune_pedestal', 'star_tile', 'sky_bell', 'quest_board', 'sky_beacon', 'devourer_seal', 'brazier')]})

    flora_features()

    crystals('crystals_common', 12)
    crystals('crystals_rare', 1)

    # Шпили кристальных шпилей: столбы светлого камня (как ледяные шипы — своя фича вanilla «ice_spike» не подходит, берём колонну базальта)
    feature('radiant_spire', {'type': 'minecraft:block_column', 'allowed_placement': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                              'direction': 'up', 'prioritize_tip': True, 'layers': [
                                  {'height': {'type': 'minecraft:uniform', 'min_inclusive': 3, 'max_inclusive': 9}, 'provider': {'id': c('skystone')}},
                                  {'height': {'type': 'minecraft:uniform', 'min_inclusive': 1, 'max_inclusive': 3}, 'provider': {'id': c('radiant_stone')}},
                                  {'height': 1, 'provider': state(c('sky_crystal'), facing='up', waterlogged=False)}]})
    placed('radiant_spires', c('radiant_spire'), [
        {'type': 'minecraft:count', 'count': 3}, {'type': 'minecraft:in_square'},
        {'type': 'minecraft:heightmap', 'heightmap': 'WORLD_SURFACE_WG'}, {'type': 'minecraft:biome'},
        {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:matching_blocks', 'blocks': c('skystone'), 'offset': [0, -1, 0]}}])


def flora_features():
    def weighted_flowers(name, flowers):
        feature(name, {'type': 'minecraft:simple_block', 'to_place': {'type': 'minecraft:weighted', 'entries': [
            {'data': {'id': c(f)}, 'weight': w} for f, w in flowers]}})

    weighted_flowers('flowers_meadow', [('sky_lily', 3), ('sunbell', 3), ('dawn_poppy', 2), ('aether_rose', 1)])
    weighted_flowers('flowers_garden', [('sky_lily', 3), ('cloudbloom', 3), ('aether_rose', 2), ('sunbell', 2), ('dawn_poppy', 2)])
    weighted_flowers('flowers_star', [('starflower', 6), ('cloudbloom', 1)])
    placed('patch_flowers_meadow', c('flowers_meadow'), on_islands(2, ON_GRASS, spread=4))
    placed('patch_flowers_garden', c('flowers_garden'), on_islands(6, ON_GRASS, spread=5))
    placed('patch_flowers_star', c('flowers_star'), on_islands(4, ON_GRASS, spread=5))

    feature('golden_grass_patch', {'type': 'minecraft:simple_block', 'to_place': {'type': 'minecraft:weighted', 'entries': [
        {'data': {'id': c('golden_tuft')}, 'weight': 5}]}})
    feature('tall_golden_grass', {'type': 'minecraft:simple_block', 'to_place': {'id': c('tall_golden_grass'), 'properties': {'half': 'lower'}}})
    placed('patch_golden_grass', c('golden_grass_patch'), on_islands(4, ON_GRASS, spread=6))
    placed('patch_tall_golden_grass', c('tall_golden_grass'), on_islands(1, ON_GRASS + [
        {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air', 'offset': [0, 1, 0]}], spread=4))
    feature('cloud_moss', {'type': 'minecraft:simple_block', 'to_place': {'id': c('cloud_moss')}})
    placed('patch_cloud_moss', c('cloud_moss'), on_islands(2, ON_GRASS, spread=4))

    # светолиана свисает с нижней стороны островов
    feature('lumivine', {'type': 'minecraft:block_column', 'allowed_placement': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                         'direction': 'down', 'prioritize_tip': True, 'layers': [
                             {'height': {'type': 'minecraft:uniform', 'min_inclusive': 1, 'max_inclusive': 7}, 'provider': state(c('lumivine'), tip=False)},
                             {'height': 1, 'provider': state(c('lumivine'), tip=True)}]})
    feature('hanging_roots', {'type': 'minecraft:block_column', 'allowed_placement': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                              'direction': 'down', 'prioritize_tip': False, 'layers': [
                                  {'height': {'type': 'minecraft:uniform', 'min_inclusive': 1, 'max_inclusive': 2}, 'provider': state('minecraft:hanging_roots', waterlogged=False)}]})

    def under_islands(name, feat, count):
        placed(name, c(feat), [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                               {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform',
                                                                             'min_inclusive': {'absolute': 20}, 'max_inclusive': {'absolute': 210}}},
                               {'type': 'minecraft:environment_scan', 'direction_of_search': 'up', 'max_steps': 24,
                                'allowed_search_condition': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                                'target_condition': {'type': 'minecraft:has_sturdy_face', 'direction': 'down'}},
                               {'type': 'minecraft:offset', 'x': 0, 'y': -1, 'z': 0}, {'type': 'minecraft:biome'}])

    under_islands('lumivines', 'lumivine', 24)
    under_islands('island_roots', 'hanging_roots', 30)

    # водопады: источник в боку острова, вода срывается в бездну
    feature('heaven_spring', {'type': 'minecraft:spring_feature', 'state': {'id': 'minecraft:water', 'properties': {'falling': 'true'}},
                              'valid_blocks': [c('skystone'), c('heaven_dirt')], 'requires_block_below': True, 'rock_count': 3, 'hole_count': 1})
    placed('heaven_waterfalls', c('heaven_spring'), [{'type': 'minecraft:count', 'count': 6}, {'type': 'minecraft:in_square'},
                                                    {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform',
                                                                                                  'min_inclusive': {'absolute': 50},
                                                                                                  'max_inclusive': {'absolute': 210}}},
                                                    {'type': 'minecraft:biome'}])

    # кристальные жеоды внутри островов
    feature('sky_geode', {'type': 'minecraft:geode', 'blocks': {
        'alternate_inner_layer_provider': {'id': c('radiant_stone')}, 'cannot_replace': '#minecraft:features_cannot_replace',
        'filling_provider': {'id': 'minecraft:air'}, 'inner_layer_provider': {'id': c('sky_crystal_block')},
        'inner_placements': [state(c('sky_crystal'), facing='up', waterlogged=False)], 'invalid_blocks': ['minecraft:air', 'minecraft:cave_air', 'minecraft:void_air', 'minecraft:bedrock'],
        'middle_layer_provider': {'id': 'minecraft:calcite'}, 'outer_layer_provider': {'id': c('skystone_bricks')}},
        'crack': {'generate_crack_chance': 0.6}, 'invalid_blocks_threshold': 0, 'layers': {},
        'outer_wall_distance': {'type': 'minecraft:uniform', 'min_inclusive': 3, 'max_inclusive': 5}, 'use_alternate_layer0_chance': 0.06})
    placed('sky_geodes', c('sky_geode'), [{'type': 'minecraft:rarity_filter', 'chance': 10}, {'type': 'minecraft:in_square'},
                                          {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform',
                                                                                        'min_inclusive': {'absolute': 60}, 'max_inclusive': {'absolute': 200}}},
                                          {'type': 'minecraft:biome'}])

    # новые деревья
    leaves_state = lambda b: state(c(b), distance=7, persistent=False, waterlogged=False)  # noqa: E731
    feature('cloud_willow', {
        'type': 'minecraft:tree', 'below_trunk_provider': HEAVEN_SOIL, 'decorators': [], 'ignore_vines': True,
        'foliage_placer': {'type': 'minecraft:cherry_foliage_placer', 'corner_hole_chance': 0.2, 'hanging_leaves_chance': 0.75,
                           'hanging_leaves_extension_chance': 0.7, 'height': 5, 'offset': 0, 'radius': 4,
                           'wide_bottom_layer_hole_chance': 0.1},
        'foliage_provider': leaves_state('cloud_willow_leaves'), 'minimum_size': {'type': 'minecraft:two_layers_feature_size', 'upper_size': 2},
        'trunk_placer': {'type': 'minecraft:straight_trunk_placer', 'base_height': 5, 'height_rand_a': 2, 'height_rand_b': 0},
        'trunk_provider': LOG})
    feature('starpine', {
        'type': 'minecraft:tree', 'below_trunk_provider': HEAVEN_SOIL, 'decorators': [], 'ignore_vines': True,
        'foliage_placer': {'type': 'minecraft:spruce_foliage_placer', 'offset': {'type': 'minecraft:uniform', 'min_inclusive': 0, 'max_inclusive': 2},
                           'radius': {'type': 'minecraft:uniform', 'min_inclusive': 2, 'max_inclusive': 3},
                           'trunk_height': {'type': 'minecraft:uniform', 'min_inclusive': 1, 'max_inclusive': 2}},
        'foliage_provider': leaves_state('starpine_leaves'), 'minimum_size': {'type': 'minecraft:two_layers_feature_size', 'limit': 2, 'upper_size': 2},
        'trunk_placer': {'type': 'minecraft:straight_trunk_placer', 'base_height': 7, 'height_rand_a': 3, 'height_rand_b': 1},
        'trunk_provider': LOG})
    placed('trees_cloud_willow', c('cloud_willow'), [{'type': 'minecraft:count', 'count': 7}, {'type': 'minecraft:in_square'}] + ON_ANY_ISLAND + [
        {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:would_survive', 'state': state(c('cloud_willow_sapling'))}},
        {'type': 'minecraft:biome'}])
    placed('trees_starpine', c('starpine'), [{'type': 'minecraft:count', 'count': 9}, {'type': 'minecraft:in_square'}] + ON_ANY_ISLAND + [
        {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:would_survive', 'state': state(c('starpine_sapling'))}},
        {'type': 'minecraft:biome'}])


# ------------------------------------------------------------------ биомы
def biome(name, sky, fog, grass, features_by_step, music='celestial:music.heaven', creatures=None, monsters=None, ambient=None,
          particle=None, particle_chance=0.0):
    steps = [[] for _ in range(11)]
    for step, fs in features_by_step.items():
        # единый порядок фич во всех биомах, иначе игра падает с «Feature order cycle»
        for f in sorted(fs, key=FEATURE_ORDER.index):
            steps[BEFORE_STRUCTURES if f in EARLY_FEATURES else step].append(c(f))
    for step in steps:
        step.sort(key=lambda f: FEATURE_ORDER.index(f.split(':')[1]))
    spawns = {}
    if creatures:
        spawns['creature'] = creatures
    if monsters:
        spawns['monster'] = monsters
    if ambient:
        spawns['ambient'] = ambient
    attributes = {
        'minecraft:audio/background_music': {'default': {'max_delay': 9000, 'min_delay': 2400, 'sound': music}},
        'minecraft:visual/sky_color': sky,
        'minecraft:visual/fog_color': fog,
        'minecraft:visual/water_fog_color': '#c8f0ff',
    }
    if particle:
        attributes['minecraft:visual/ambient_particles'] = {'argument': [{'particle': {'type': particle}, 'probability': particle_chance}],
                                                           'modifier': 'append'}
    if spawns:
        attributes['minecraft:gameplay/natural_mob_spawns'] = {'argument': {'spawn_costs': {}, 'spawns_by_category': spawns}, 'modifier': 'overlay'}
    write_json(os.path.join(WG, 'biome', name + '.json'), {
        'attributes': attributes, 'carvers': [], 'downfall': 0.4,
        'effects': {'grass_color': grass, 'foliage_color': grass, 'water_color': '#8fe3ff'},
        'features': steps, 'has_precipitation': False, 'temperature': 0.7})


FEATURE_ORDER = ['sky_geodes', 'ore_etherite', 'ore_etherite_rich', 'ore_starquartz', 'ore_radiant', 'heaven_waterfalls',
                 'sky_clouds', 'sky_golden_clouds', 'sky_rain_clouds', 'radiant_spires', 'rainbow_arcs',
                 'trees_golden_meadows', 'trees_cloud_forest', 'trees_cloud_willow', 'trees_starpine',
                 'patch_manna', 'patch_flowers_meadow', 'patch_flowers_garden', 'patch_flowers_star',
                 'patch_tall_golden_grass', 'patch_golden_grass', 'patch_cloud_moss', 'crystals_common', 'crystals_rare',
                 'lumivines', 'island_roots']
ORES = ['sky_geodes', 'ore_etherite', 'ore_etherite_rich', 'ore_starquartz', 'ore_radiant']
UNDER = ['lumivines', 'island_roots']
GROUND = ['heaven_waterfalls']
LOCAL_MODS, UNDERGROUND_ORES, FLUID_SPRINGS, VEGETAL = 2, 6, 8, 9
# постройки идут на шаге 4 (surface_structures): облака и жеоды ставим раньше, чтобы здания перекрывали их, а не наоборот
BEFORE_STRUCTURES = 3
EARLY_FEATURES = {'sky_geodes', 'sky_clouds', 'sky_golden_clouds', 'sky_rain_clouds'}


def spawn(mob, weight, lo, hi):
    return {'type': c(mob), 'count': lo if lo == hi else {'type': 'minecraft:uniform', 'min_inclusive': lo, 'max_inclusive': hi}, 'weight': weight}


MONSTERS = [spawn('fallen_guardian', 100, 1, 3), spawn('winged_serpent', 40, 1, 2), spawn('storm_spirit', 25, 1, 1)]
WISPS = [spawn('light_wisp', 10, 1, 3)]


def biomes():
    common = [*UNDER]
    biome('golden_meadows', '#8ec9ff', '#fdf3d4', '#f0c94a', {
        UNDERGROUND_ORES: ORES, FLUID_SPRINGS: GROUND,
        VEGETAL: ['sky_clouds', 'sky_golden_clouds', 'trees_golden_meadows', 'patch_manna', 'patch_flowers_meadow',
                  'patch_golden_grass', 'patch_tall_golden_grass', 'crystals_rare', *common]},
        creatures=[spawn('pegasus', 8, 2, 4), spawn('cloud_whale', 3, 1, 1), spawn('angel', 1, 1, 1), spawn('golden_ram', 6, 2, 4)],
        monsters=MONSTERS, ambient=WISPS, particle='celestial:feather', particle_chance=0.0006)
    biome('cloud_forest', '#a9d4ff', '#ffffff', '#e8d070', {
        UNDERGROUND_ORES: ORES, FLUID_SPRINGS: GROUND,
        VEGETAL: ['sky_clouds', 'sky_rain_clouds', 'trees_cloud_forest', 'trees_cloud_willow', 'patch_manna', 'patch_golden_grass',
                  'patch_cloud_moss', *common]},
        music='minecraft:music.overworld.meadow',
        creatures=[spawn('cloud_whale', 6, 1, 2), spawn('pegasus', 3, 1, 2), spawn('sky_ray', 3, 1, 1)], monsters=MONSTERS,
        ambient=WISPS + [spawn('cloud_jelly', 8, 1, 3)], particle='minecraft:white_ash', particle_chance=0.004)
    biome('crystal_spires', '#9cc1ff', '#e6ecff', '#d8e2f0', {
        UNDERGROUND_ORES: ORES, VEGETAL: ['sky_clouds', 'radiant_spires', 'crystals_common', *common]},
        music='minecraft:music.overworld.grove',
        monsters=[spawn('storm_spirit', 60, 1, 2), spawn('fallen_guardian', 60, 1, 2), spawn('winged_serpent', 30, 1, 2)], ambient=WISPS,
        particle='minecraft:glow', particle_chance=0.002)
    biome('rainbow_shoals', '#b9b0ff', '#ffe9f6', '#ffd38a', {
        UNDERGROUND_ORES: ORES, FLUID_SPRINGS: GROUND,
        VEGETAL: ['sky_clouds', 'sky_golden_clouds', 'patch_manna', 'trees_golden_meadows', 'patch_flowers_meadow', 'rainbow_arcs',
                  'patch_golden_grass', *common]},
        creatures=[spawn('pegasus', 6, 2, 3), spawn('cloud_whale', 4, 1, 1), spawn('sky_ray', 4, 1, 2)], monsters=MONSTERS,
        ambient=WISPS + [spawn('cloud_jelly', 6, 1, 2)], particle='minecraft:end_rod', particle_chance=0.001)
    # новые биомы 0.2
    biome('heaven_gardens', '#97d0ff', '#f6ffe8', '#c9e06a', {
        UNDERGROUND_ORES: ORES, FLUID_SPRINGS: GROUND,
        VEGETAL: ['sky_clouds', 'trees_cloud_willow', 'trees_golden_meadows', 'patch_manna', 'patch_flowers_garden',
                  'patch_golden_grass', 'patch_tall_golden_grass', 'patch_cloud_moss', *common]},
        music='minecraft:music.overworld.flower_forest',
        creatures=[spawn('pegasus', 5, 2, 3), spawn('angel', 3, 1, 2), spawn('cherub', 4, 1, 2), spawn('golden_ram', 4, 2, 3)],
        monsters=[spawn('fallen_guardian', 40, 1, 2)], ambient=WISPS + [spawn('cloud_jelly', 4, 1, 2)],
        particle='minecraft:cherry_leaves', particle_chance=0.002)
    biome('storm_peak', '#6f7f99', '#9aa3b5', '#9aa3b5', {
        UNDERGROUND_ORES: ORES, VEGETAL: ['sky_rain_clouds', 'sky_clouds', 'radiant_spires', 'patch_golden_grass', *common]},
        music='minecraft:music.overworld.jagged_peaks',
        monsters=[spawn('storm_spirit', 100, 1, 3), spawn('winged_serpent', 40, 1, 2), spawn('storm_elemental', 4, 1, 1)], ambient=WISPS,
        particle='minecraft:electric_spark', particle_chance=0.006)
    biome('star_glade', '#5c62b8', '#c7c9ff', '#a9b9ff', {
        UNDERGROUND_ORES: ORES, FLUID_SPRINGS: GROUND,
        VEGETAL: ['sky_clouds', 'trees_starpine', 'patch_flowers_star', 'patch_golden_grass', 'crystals_rare', *common]},
        music='minecraft:music.overworld.grove',
        creatures=[spawn('cloud_whale', 2, 1, 1)], monsters=[spawn('winged_serpent', 30, 1, 2)], ambient=[spawn('light_wisp', 30, 2, 4)],
        particle='celestial:starlight', particle_chance=0.003)


def main():
    dimension()
    noises()
    surface()
    features()
    biomes()
    print('ok: Рай сгенерирован')


if __name__ == '__main__':
    main()
