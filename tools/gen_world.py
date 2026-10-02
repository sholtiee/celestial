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
                            'sound': 'minecraft:music.overworld.cherry_grove'}},
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
                biome_point('golden_meadows', 0.3, 0.2),
                biome_point('cloud_forest', -0.1, 0.55),
                biome_point('crystal_spires', 0.75, -0.6),
                biome_point('rainbow_shoals', -0.65, -0.35),
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

    def tree_placement(count):
        return [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                {'type': 'minecraft:heightmap', 'heightmap': 'MOTION_BLOCKING_NO_LEAVES'},
                {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:would_survive', 'state': state(c('skywood_sapling'))}},
                {'type': 'minecraft:biome'}]

    placed('trees_golden_meadows', c('heaven_trees'), tree_placement(
        {'type': 'minecraft:weighted_list', 'distribution': [{'data': 0, 'weight': 3}, {'data': 1, 'weight': 2}, {'data': 2, 'weight': 1}]}))
    placed('trees_cloud_forest', c('heaven_trees'), tree_placement(
        {'type': 'minecraft:weighted_list', 'distribution': [{'data': 4, 'weight': 2}, {'data': 6, 'weight': 1}]}))

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
    placed('patch_manna', c('manna_bush'), [
        {'type': 'minecraft:rarity_filter', 'chance': 6}, {'type': 'minecraft:in_square'},
        {'type': 'minecraft:heightmap', 'heightmap': 'WORLD_SURFACE_WG'}, {'type': 'minecraft:biome'},
        {'type': 'minecraft:count', 'count': 24},
        {'type': 'minecraft:offset', 'x': {'type': 'minecraft:trapezoid', 'min': -6, 'max': 6, 'plateau': 0},
         'y': {'type': 'minecraft:trapezoid', 'min': -2, 'max': 2, 'plateau': 0},
         'z': {'type': 'minecraft:trapezoid', 'min': -6, 'max': 6, 'plateau': 0}},
        {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:all_of', 'predicates': [
            {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
            {'type': 'minecraft:matching_blocks', 'blocks': c('golden_grass'), 'offset': [0, -1, 0]}]}}])

    feature('sky_crystal', {'type': 'minecraft:simple_block', 'to_place': state(c('sky_crystal'), facing='up', waterlogged=False)})

    def crystals(name, count):
        placed(name, c('sky_crystal'), [
            {'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
            {'type': 'minecraft:heightmap', 'heightmap': 'WORLD_SURFACE_WG'}, {'type': 'minecraft:biome'},
            {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:all_of', 'predicates': [
                {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
                {'type': 'minecraft:matching_blocks', 'blocks': [c('skystone'), c('golden_grass')], 'offset': [0, -1, 0]}]}}])

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


# ------------------------------------------------------------------ биомы
def biome(name, sky, fog, grass, features_by_step, music='minecraft:music.overworld.cherry_grove', creatures=None, monsters=None):
    steps = [[] for _ in range(11)]
    for step, fs in features_by_step.items():
        # единый порядок фич во всех биомах, иначе игра падает с «Feature order cycle»
        steps[step] += [c(f) for f in sorted(fs, key=FEATURE_ORDER.index)]
    spawns = {}
    if creatures:
        spawns['creature'] = creatures
    if monsters:
        spawns['monster'] = monsters
    attributes = {
        'minecraft:audio/background_music': {'default': {'max_delay': 9000, 'min_delay': 2400, 'sound': music}},
        'minecraft:visual/sky_color': sky,
        'minecraft:visual/fog_color': fog,
        'minecraft:visual/water_fog_color': '#c8f0ff',
    }
    if spawns:
        attributes['minecraft:gameplay/natural_mob_spawns'] = {'argument': {'spawn_costs': {}, 'spawns_by_category': spawns}, 'modifier': 'overlay'}
    write_json(os.path.join(WG, 'biome', name + '.json'), {
        'attributes': attributes, 'carvers': [], 'downfall': 0.4,
        'effects': {'grass_color': grass, 'foliage_color': grass, 'water_color': '#8fe3ff'},
        'features': steps, 'has_precipitation': False, 'temperature': 0.7})


FEATURE_ORDER = ['ore_etherite', 'ore_etherite_rich', 'ore_starquartz', 'ore_radiant',
                 'sky_clouds', 'sky_golden_clouds', 'sky_rain_clouds', 'radiant_spires',
                 'trees_golden_meadows', 'trees_cloud_forest', 'patch_manna', 'crystals_common', 'crystals_rare']
ORES = ['ore_etherite', 'ore_etherite_rich', 'ore_starquartz', 'ore_radiant']
LOCAL_MODS, UNDERGROUND_ORES, VEGETAL = 2, 6, 9


def biomes():
    biome('golden_meadows', '#8ec9ff', '#fdf3d4', '#f0c94a', {
        UNDERGROUND_ORES: ORES, VEGETAL: ['sky_clouds', 'sky_golden_clouds', 'trees_golden_meadows', 'patch_manna', 'crystals_rare']})
    biome('cloud_forest', '#a9d4ff', '#ffffff', '#e8d070', {
        UNDERGROUND_ORES: ORES, VEGETAL: ['sky_clouds', 'sky_rain_clouds', 'trees_cloud_forest', 'patch_manna']},
        music='minecraft:music.overworld.meadow')
    biome('crystal_spires', '#9cc1ff', '#e6ecff', '#d8e2f0', {
        UNDERGROUND_ORES: ORES, VEGETAL: ['sky_clouds', 'radiant_spires', 'crystals_common']},
        music='minecraft:music.overworld.grove')
    biome('rainbow_shoals', '#b9b0ff', '#ffe9f6', '#ffd38a', {
        UNDERGROUND_ORES: ORES, VEGETAL: ['sky_clouds', 'sky_golden_clouds', 'patch_manna', 'trees_golden_meadows']})


def main():
    dimension()
    noises()
    surface()
    features()
    biomes()
    print('ok: Рай сгенерирован')


if __name__ == '__main__':
    main()
