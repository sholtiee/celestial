"""Бездна (волна 0.3): блоки, измерение celestial:abyss, рельеф, фичи и биомы.

Рельеф: пол ~30–55 с озёрами (уровень воды 32), потолок ~210, сталактиты с потолка, сталагмиты с пола
и средний ярус «перевёрнутых» островов ~112. Почти полная тьма (ambient_light 0) — на ней держится механика страха.
Запуск: python3 tools/gen_abyss.py (входит в build_assets.sh).
"""
import json
import os

from PIL import Image

import textures as T
from gen_assets import DATA, blockstate, c, item_def, loot, model, save_png, self_drop, silk_or, simple_cube, write_json
from gen_story import lang_patch
from gen_structures import Template, biome_tag, island_base, pool, structure

WG = os.path.join(DATA, 'worldgen')
MIN_Y, HEIGHT, SEA = 0, 256, 32
STONE_PAL = [T.hexrgb(h) for h in ('#15111c', '#1b1624', '#221b2d', '#2a2236')]


# ---------------------------------------------------------------- блоки
def textures():
    save_png(T.noisy('abyss_stone', STONE_PAL, cell=3, grain=0.45), 'block/abyss_stone')
    save_png(T.bricks('abyss_bricks', [T.hexrgb(h) for h in ('#1d1727', '#251e31', '#2d253b')], '#0c0912'), 'block/abyss_bricks')

    top = T.noisy('gloom_moss_top', [T.hexrgb(h) for h in ('#0b2226', '#0f2c31', '#14373c', '#19434a')], cell=2, grain=0.4)
    r = T.rng_for('gloom_moss_glow')
    for _ in range(9):  # светящиеся споры
        top.putpixel((r.randrange(16), r.randrange(16)), (*T.hexrgb(r.choice(['#3fe0c8', '#7af5e3'])), 255))
    save_png(top, 'block/gloom_moss_top')
    side = T.noisy('abyss_stone_moss_side', STONE_PAL, cell=3, grain=0.45)
    tp = top.load()
    for x in range(16):
        drop = 3 + r.randrange(3)
        for y in range(drop):
            side.putpixel((x, y), tp[x, y])
    save_png(side, 'block/gloom_moss_side')

    cap = T.noisy('glowshroom_cap', [T.hexrgb(h) for h in ('#1a5d78', '#1f78a0', '#2a97c4', '#38b4e0')], cell=3, grain=0.3)
    r = T.rng_for('glowshroom_spots')
    for _ in range(7):
        x, y = r.randrange(1, 15), r.randrange(1, 15)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            cap.putpixel((min(15, x + dx), min(15, y + dy)), (*T.hexrgb('#b8fbff'), 255))
    save_png(cap, 'block/glowshroom_cap')
    save_png(T.noisy('glowshroom_stem', [T.hexrgb(h) for h in ('#9fb3c2', '#b6c8d4', '#c9d8e2')], cell=2, grain=0.3), 'block/glowshroom_stem')

    plant = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(8, 16):  # ножка
        for x in (7, 8):
            plant.putpixel((x, y), (*T.hexrgb('#c9d8e2' if x == 7 else '#9fb3c2'), 255))
    for y, (x0, x1) in enumerate(((6, 9), (4, 11), (3, 12), (3, 12), (4, 11)), start=3):  # шляпка
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y == 7
            plant.putpixel((x, y), (*T.hexrgb('#1f78a0' if edge else ('#b8fbff' if (x + y) % 4 == 0 else '#38b4e0')), 255))
    save_png(plant, 'block/glowshroom')

    crystal = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for cx, h, w in ((7, 13, 2), (4, 8, 1), (11, 9, 1)):  # три грани-шипа
        for y in range(16 - h, 16):
            half = max(0, int(w * (y - (16 - h)) / h + 0.5))
            for x in range(cx - half, cx + half + 1):
                col = '#e0c8ff' if x == cx - half else '#6a3fb0' if x == cx + half else '#9b6be0'
                crystal.putpixel((x, y), (*T.hexrgb(col), 255))
    save_png(crystal, 'block/shadow_crystal')

    ore = T.noisy('abyssal_obsidian_ore', STONE_PAL, cell=3, grain=0.45)
    r = T.rng_for('abyssal_ore_specks')
    for _ in range(6):
        x, y = r.randrange(2, 14), r.randrange(2, 14)
        for i, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (-1, 0), (1, 1))):
            ore.putpixel((x + dx, y + dy), (*T.hexrgb(['#3a1b5c', '#5b2a8c', '#120a1f', '#7d45c2', '#2a1442'][i]), 255))
    save_png(ore, 'block/abyssal_obsidian_ore')


def block_models():
    simple_cube('abyss_stone')
    simple_cube('abyss_bricks')
    simple_cube('abyssal_obsidian_ore')
    model('block/gloom_moss', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/gloom_moss_top'), 'side': c('block/gloom_moss_side'), 'bottom': c('block/abyss_stone')}})
    blockstate('gloom_moss', {'variants': {'': {'model': c('block/gloom_moss')}}})
    item_def('gloom_moss', c('block/gloom_moss'))
    # гигантский гриб: все состояния HugeMushroomBlock — один куб
    for name in ('glowshroom_cap', 'glowshroom_stem'):
        simple_cube(name)
    # светогриб и теневой кристалл — крест-модели
    model('block/glowshroom', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/glowshroom')}})
    blockstate('glowshroom', {'variants': {'': {'model': c('block/glowshroom')}}})
    model('item/glowshroom', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/glowshroom')}})
    item_def('glowshroom', c('item/glowshroom'))
    model('block/shadow_crystal', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/shadow_crystal')}})
    rot = {'up': {}, 'down': {'x': 180}, 'north': {'x': 90}, 'south': {'x': 90, 'y': 180}, 'east': {'x': 90, 'y': 90}, 'west': {'x': 90, 'y': 270}}
    blockstate('shadow_crystal', {'variants': {f'facing={f}': {'model': c('block/shadow_crystal'), **r} for f, r in rot.items()}})
    model('item/shadow_crystal', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/shadow_crystal')}})
    item_def('shadow_crystal', c('item/shadow_crystal'))

    for name in ('abyss_stone', 'abyss_bricks', 'glowshroom', 'shadow_crystal', 'abyssal_obsidian_ore'):
        self_drop(name)
    silk_or('gloom_moss', c('abyss_stone'))
    loot('glowshroom_cap', [{'entries': [{'type': 'minecraft:alternatives', 'children': [
        {'type': 'minecraft:item', 'condition': 'minecraft:tool/can_silk_touch', 'name': c('glowshroom_cap')},
        {'type': 'minecraft:item', 'name': c('glowshroom'), 'modifier': [
            {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': -1, 'max': 2}},
            {'type': 'minecraft:limit_count', 'limit': {'min': 0}}, {'type': 'minecraft:explosion_decay'}]}]}], 'rolls': 1}])
    loot('glowshroom_stem', [{'condition': 'minecraft:tool/can_silk_touch',
                              'entries': [{'type': 'minecraft:item', 'name': c('glowshroom_stem')}], 'rolls': 1}])


def append_tag(kind, name, values):
    ns, path = name.split(':')
    base = os.path.join(DATA.replace('celestial', ns), 'tags', kind, path + '.json')
    existing = []
    if os.path.exists(base):
        with open(base) as f:
            existing = json.load(f)['values']
    write_json(base, {'replace': False, 'values': list(dict.fromkeys(existing + values))})


def darkness_data():
    write_json(os.path.join(DATA, 'damage_type/darkness.json'), {'exhaustion': 0.0, 'message_id': 'celestial.darkness', 'scaling': 'never'})
    append_tag('damage_type', 'minecraft:bypasses_armor', [c('darkness')])
    opt = lambda i: {'id': i, 'required': False}  # noqa: E731
    write_json(os.path.join(DATA, 'tags/item/light_sources.json'), {'values': [
        'minecraft:torch', 'minecraft:soul_torch', 'minecraft:lantern', 'minecraft:soul_lantern', 'minecraft:glowstone',
        'minecraft:sea_lantern', 'minecraft:shroomlight', 'minecraft:jack_o_lantern', 'minecraft:glow_berries', 'minecraft:ochre_froglight',
        'minecraft:verdant_froglight', 'minecraft:pearlescent_froglight', 'minecraft:end_rod', 'minecraft:lava_bucket',
        opt('minecraft:copper_torch'), opt('minecraft:copper_lantern'),
        c('glowshroom'), c('radiant_stone'), c('beam_lantern'), c('sky_crystal'), c('light_spear')]})


def tags():
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in ('abyss_stone', 'abyss_bricks', 'gloom_moss', 'shadow_crystal',
                                                                      'abyssal_obsidian_ore')])
    append_tag('block', 'minecraft:mineable/axe', [c('glowshroom_cap'), c('glowshroom_stem')])
    append_tag('block', 'minecraft:needs_diamond_tool', [c('abyssal_obsidian_ore')])
    append_tag('block', 'minecraft:needs_stone_tool', [c('abyss_stone'), c('abyss_bricks'), c('gloom_moss')])


# ---------------------------------------------------------------- измерение
def dimension():
    write_json(os.path.join(DATA, 'dimension_type/abyss.json'), {
        'ambient_light': 0.0,
        'attributes': {
            'minecraft:audio/background_music': {'default': {'max_delay': 6000, 'min_delay': 1200, 'replace_current_music': True,
                                                             'sound': 'minecraft:music.overworld.deep_dark'}},
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'never', 'can_sleep': 'never', 'destroy_on_use': False,
                                            'error_message': {'translate': 'block.minecraft.bed.no_sleep'}},
            'minecraft:gameplay/respawn_anchor_works': False,
            'minecraft:gameplay/sky_light_level': 0.0,
            'minecraft:visual/ambient_light_color': '#0a0710',
            'minecraft:visual/fog_color': '#070a10',
            'minecraft:visual/fog_start_distance': 24.0,
            'minecraft:visual/fog_end_distance': 140.0,
            'minecraft:visual/sky_light_factor': 0.0,
        },
        'cardinal_light': 'nether',
        'coordinate_scale': 1.0,
        'has_ceiling': True,
        'has_ender_dragon_fight': False,
        'has_fixed_time': True,
        'has_skylight': False,
        'height': HEIGHT,
        'infiniburn': '#minecraft:infiniburn_overworld',
        'logical_height': HEIGHT,
        'min_y': MIN_Y,
        'monster_spawn_block_light_limit': 0,
        'monster_spawn_light_level': {'type': 'minecraft:uniform', 'min_inclusive': 0, 'max_inclusive': 7},
        'skybox': 'none',
        'timelines': '#minecraft:in_nether',
    })
    write_json(os.path.join(DATA, 'dimension/abyss.json'), {
        'type': c('abyss'),
        'generator': {'type': 'minecraft:noise', 'settings': c('abyss'), 'biome_source': {'type': 'minecraft:multi_noise', 'biomes': [
            point('glowshroom_forest', 0.0, 0.45), point('glowshroom_forest', 0.3, 0.7),
            point('dark_wastes', 0.55, -0.45), point('dark_wastes', 0.1, -0.1),
            point('crystal_hollows', -0.6, -0.4),
            point('dark_lakes', -0.45, 0.55),
        ]}},
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

    def noise(name, octave, octaves=3, y_scale=0.0, amps=None):
        write_json(os.path.join(WG, f'noise/abyss_{name}.json'),
                   {'base_amplitude': 1.0, 'base_octave': octave, 'octave_count': octaves,
                    **({'amplitude_modifiers': amps} if amps else {})})
        return {'type': 'minecraft:noise', 'noise': c(f'abyss_{name}'), 'xz_scale': 1.0, 'y_scale': y_scale}

    for name in ('temperature', 'humidity'):
        write_json(os.path.join(WG, f'density_function/abyss/{name}.json'), noise(name, -8, 2))

    floor = add(grad(18, 66, 1.0, -1.0), mul(noise('floor', -6), 0.75))
    ceiling = add(grad(188, 240, -1.0, 1.0), mul(noise('ceiling', -5), 0.6))
    # сталактиты: острый двумерный шум, вытянутый вниз градиентом — чем сильнее шум, тем длиннее «сосулька»
    def spike(n, threshold, strength):
        """Острый пик только там, где шум выше порога (иначе — 0): редкие, а не сплошной «лес»."""
        return mul({'type': 'minecraft:max', 'left': add(n, -threshold), 'right': 0.0}, strength)

    stalactites = add(spike(noise('stalactites', -3, 2, amps=[1.0, 0.4]), 0.22, 6.0), grad(86, 226, -5.0, 0.0))
    stalagmites = add(spike(noise('stalagmites', -3, 2, amps=[1.0, 0.4]), 0.32, 6.0), grad(36, 136, 0.0, -5.0))
    # средний ярус перевёрнутых островов: сверху плоско, снизу длинный шип
    mask = noise('islands', -6, 3, amps=[1.0, 0.5, 0.25])
    islands = add(add(mul(mask, 1.9), -0.8), mul(add(grad(84, 112, 1.0, 0.0), grad(112, 118, 0.0, 1.0)), -1.0))
    terrain = {'type': 'minecraft:max', 'left': floor, 'right': {'type': 'minecraft:max', 'left': ceiling, 'right': {
        'type': 'minecraft:max', 'left': islands, 'right': {'type': 'minecraft:max', 'left': stalactites, 'right': stalagmites}}}}
    final = add({'type': 'minecraft:interpolated', 'cell_size_xz': 4, 'cell_size_y': 4, 'input': terrain}, {'type': 'minecraft:beardifier'})
    write_json(os.path.join(WG, 'density_function/abyss/final_density.json'), final)


def surface():
    def on(cond, block):
        return {'type': 'minecraft:condition', 'if_true': cond, 'then_run': {'type': 'minecraft:block', 'result_state': block}}

    def biome_is(*names):
        return {'type': 'minecraft:biome', 'biome_is': [c(n) for n in names]}

    write_json(os.path.join(WG, 'material_rule/abyss.json'), {'type': 'minecraft:sequence', 'sequence': [
        'minecraft:bedrock_floor', 'minecraft:bedrock_roof',
        {'type': 'minecraft:condition', 'if_true': biome_is('glowshroom_forest', 'dark_lakes'),
         'then_run': on('minecraft:on_floor', c('gloom_moss'))},
    ]})
    write_json(os.path.join(WG, 'noise_settings/abyss.json'), {
        'debug_functions': [], 'default_block': c('abyss_stone'), 'default_fluid': 'minecraft:water',
        'disable_mob_generation': False, 'legacy_random_source': False, 'material_rule': c('abyss'),
        'noise': {'min_y': MIN_Y, 'height': HEIGHT},
        'noise_router': {'chunk_surface_level': 0.0, 'continents': 0.0, 'depth': 0.0, 'erosion': 0.0, 'ridges': 0.0,
                         'final_density': c('abyss/final_density'), 'temperature': c('abyss/temperature'),
                         'vegetation': c('abyss/humidity')},
        'sea_level': SEA, 'spawn_target': []})


# ---------------------------------------------------------------- фичи
def feature(name, obj):
    write_json(os.path.join(WG, 'feature', name + '.json'), obj)


def placed(name, feat, placement):
    write_json(os.path.join(WG, 'placed_feature', name + '.json'), {'feature': feat, 'placement': placement})


def scan(direction, lo, hi):
    """Случайная высота в полосе → ищем по направлению первый твёрдый блок (пол или потолок)."""
    face = 'up' if direction == 'down' else 'down'
    return [{'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform', 'min_inclusive': {'absolute': lo},
                                                          'max_inclusive': {'absolute': hi}}},
            {'type': 'minecraft:environment_scan', 'direction_of_search': direction, 'max_steps': 32,
             'allowed_search_condition': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
             'target_condition': {'type': 'minecraft:has_sturdy_face', 'direction': face}},
            {'type': 'minecraft:offset', 'x': 0, 'y': 1 if direction == 'down' else -1, 'z': 0}]


def on_floor(count, lo=SEA - 4, hi=200, spread=0):
    out = [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'}] + scan('down', lo, hi) + [{'type': 'minecraft:biome'}]
    if spread:
        out += [{'type': 'minecraft:count', 'count': spread * 3},
                {'type': 'minecraft:offset', 'x': {'type': 'minecraft:trapezoid', 'min': -spread, 'max': spread, 'plateau': 0},
                 'y': {'type': 'minecraft:trapezoid', 'min': -1, 'max': 1, 'plateau': 0},
                 'z': {'type': 'minecraft:trapezoid', 'min': -spread, 'max': spread, 'plateau': 0}}]
    out.append({'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:all_of', 'predicates': [
        {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'},
        {'type': 'minecraft:has_sturdy_face', 'direction': 'up', 'offset': [0, -1, 0]}]}})
    return out


def on_ceiling(count):
    return [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'}] + scan('up', 60, 200) + [
        {'type': 'minecraft:biome'},
        {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'}}]


def features():
    stone = {'predicate_type': 'minecraft:block_match', 'block': c('abyss_stone')}
    feature('huge_glowshroom', {
        'type': 'minecraft:huge_red_mushroom',
        'can_place_on': {'type': 'minecraft:matching_blocks', 'blocks': [c('gloom_moss'), c('abyss_stone')]},
        'cap_provider': {'id': c('glowshroom_cap'), 'properties': {
            'down': 'false', 'east': 'true', 'north': 'true', 'south': 'true', 'up': 'true', 'west': 'true'}},
        'stem_provider': {'id': c('glowshroom_stem'), 'properties': {
            'down': 'false', 'east': 'true', 'north': 'true', 'south': 'true', 'up': 'false', 'west': 'true'}},
        'foliage_radius': 3})
    placed('glowshroom_giants', c('huge_glowshroom'), on_floor(8))
    placed('glowshroom_giants_sparse', c('huge_glowshroom'), on_floor(1))
    feature('glowshroom_single', {'type': 'minecraft:simple_block', 'to_place': {'id': c('glowshroom')}})
    placed('patch_glowshroom', c('glowshroom_single'), on_floor(6, spread=3))
    placed('patch_glowshroom_sparse', c('glowshroom_single'), on_floor(2, spread=2))
    for name, facing, place in (('shadow_crystals_floor', 'up', on_floor), ('shadow_crystals_ceiling', 'down', on_ceiling)):
        feature(name, {'type': 'minecraft:simple_block', 'to_place': {
            'id': c('shadow_crystal'), 'properties': {'facing': facing, 'waterlogged': 'false'}}})
    placed('shadow_crystals_floor', c('shadow_crystals_floor'), on_floor(10, spread=2))
    placed('shadow_crystals_ceiling', c('shadow_crystals_ceiling'), on_ceiling(14))
    placed('shadow_crystals_few', c('shadow_crystals_ceiling'), on_ceiling(3))
    placed('abyss_cave_vines', 'minecraft:cave_vine', on_ceiling(30))
    feature('ore_abyssal_obsidian', {'type': 'minecraft:ore', 'discard_chance_on_air_exposure': 0.5, 'size': 4,
                                     'targets': [{'state': {'id': c('abyssal_obsidian_ore')}, 'target': stone}]})
    for name, count in (('ore_abyssal_obsidian', 5), ('ore_abyssal_obsidian_rich', 10)):
        placed(name, c('ore_abyssal_obsidian'), [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                                                 {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform',
                                                                                               'min_inclusive': {'absolute': 6},
                                                                                               'max_inclusive': {'absolute': 48}}},
                                                 {'type': 'minecraft:biome'}])
    


# Порядок фич одинаков во всех биомах (иначе «Feature order cycle»)
ORDER = ['ore_abyssal_obsidian', 'ore_abyssal_obsidian_rich', 'glowshroom_giants', 'glowshroom_giants_sparse', 'patch_glowshroom',
         'patch_glowshroom_sparse', 'shadow_crystals_floor', 'shadow_crystals_ceiling', 'shadow_crystals_few', 'abyss_cave_vines']
UNDERGROUND_ORES, VEGETAL = 6, 9


def spawn(mob, weight, lo, hi):
    return {'type': mob, 'count': lo if lo == hi else {'type': 'minecraft:uniform', 'min_inclusive': lo, 'max_inclusive': hi}, 'weight': weight}


def biome(name, fog, water, ores, vegetal, monsters, particle, chance):
    steps = [[] for _ in range(11)]
    steps[UNDERGROUND_ORES] = [c(f) for f in sorted(ores, key=ORDER.index)]
    steps[VEGETAL] = [c(f) for f in sorted(vegetal, key=ORDER.index)]
    write_json(os.path.join(WG, 'biome', name + '.json'), {
        'attributes': {
            'minecraft:visual/fog_color': fog,
            'minecraft:visual/water_fog_color': water,
            'minecraft:visual/ambient_particles': {'argument': [{'particle': {'type': particle}, 'probability': chance}], 'modifier': 'append'},
            'minecraft:gameplay/natural_mob_spawns': {'argument': {'spawn_costs': {}, 'spawns_by_category': {'monster': monsters}},
                                                      'modifier': 'overlay'},
        },
        'carvers': [], 'downfall': 0.0,
        'effects': {'grass_color': '#2a8c86', 'foliage_color': '#2a8c86', 'water_color': water},
        'features': steps, 'has_precipitation': False, 'temperature': 0.5})


def biomes():
    shadows = [spawn(c('shadow'), 100, 1, 2)]
    biome('glowshroom_forest', '#06100f', '#0d2a33', ['ore_abyssal_obsidian'],
          ['glowshroom_giants', 'patch_glowshroom', 'shadow_crystals_few', 'abyss_cave_vines'], shadows, 'minecraft:glow', 0.004)
    biome('dark_wastes', '#08080b', '#0a0612', ['ore_abyssal_obsidian'],
          ['patch_glowshroom_sparse', 'shadow_crystals_few'], shadows, 'minecraft:ash', 0.01)
    biome('crystal_hollows', '#0c0912', '#1a0d2b', ['ore_abyssal_obsidian', 'ore_abyssal_obsidian_rich'],
          ['shadow_crystals_floor', 'shadow_crystals_ceiling', 'patch_glowshroom_sparse'], shadows, 'minecraft:portal', 0.004)
    biome('dark_lakes', '#05080c', '#03070c', ['ore_abyssal_obsidian'],
          ['glowshroom_giants_sparse', 'patch_glowshroom_sparse', 'abyss_cave_vines'], shadows, 'minecraft:underwater', 0.006)


# ---------------------------------------------------------------- Разлом на дне Рая
def heaven_rift():
    """Треснувший остров нижнего яруса Рая: площадка из кирпичей, в центре — чёрный Разлом 3×3,
    от него по острову расходятся трещины камня Бездны и торчат теневые кристаллы."""
    import random
    rng = random.Random(303)
    t = Template(21, 20, 21)
    top = 12
    island_base(t, 10, 10, 9, top, 12, rng)
    for x in range(7, 14):
        for z in range(7, 14):
            t.set(x, top, z, c('skystone_bricks'))
    for x in range(9, 12):
        for z in range(9, 12):
            t.set(x, top, z, c('abyss_rift'), nbt={'id': c('abyss_rift')})
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):  # трещины
        x, z = 10 + dx * 4, 10 + dz * 4
        for _ in range(6):
            if not (7 <= x <= 13 and 7 <= z <= 13) and t.get(x, top, z):
                t.set(x, top, z, c('abyss_stone'))
                if rng.random() < 0.35:
                    t.set(x, top + 1, z, c('shadow_crystal'), facing='up', waterlogged=False)
            x += dx + rng.choice((-1, 0, 0, 1)) * (dz != 0)
            z += dz + rng.choice((-1, 0, 0, 1)) * (dx != 0)
    for x, z in ((7, 7), (13, 7), (7, 13)):  # обломки колонн
        for y in range(top + 1, top + 2 + rng.randint(0, 3)):
            t.set(x, y, z, c('skystone_bricks'))
    return t.save('abyss_rift/main')


def main():
    heaven_rift()
    pool('abyss_rift/main', 'abyss_rift/main')
    structure('abyss_rift', 'abyss_rift/main', 'abyss_rift', 60)
    biome_tag('abyss_rift', 'golden_meadows', 'cloud_forest', 'crystal_spires', 'rainbow_shoals', 'storm_peak', 'star_glade', 'heaven_gardens')
    textures()
    block_models()
    tags()
    darkness_data()
    dimension()
    noises()
    surface()
    features()
    biomes()
    lang_patch({
        'block.celestial.abyss_stone': ('Камень Бездны', 'Abyss Stone'),
        'block.celestial.abyss_bricks': ('Кирпичи Бездны', 'Abyss Bricks'),
        'block.celestial.gloom_moss': ('Мох сумрака', 'Gloom Moss'),
        'block.celestial.glowshroom': ('Светогриб', 'Glowshroom'),
        'block.celestial.glowshroom_cap': ('Шляпка светогриба', 'Glowshroom Cap'),
        'block.celestial.glowshroom_stem': ('Ножка светогриба', 'Glowshroom Stem'),
        'block.celestial.shadow_crystal': ('Теневой кристалл', 'Shadow Crystal'),
        'block.celestial.abyssal_obsidian_ore': ('Руда безднового обсидиана', 'Abyssal Obsidian Ore'),
        'biome.celestial.glowshroom_forest': ('Светящийся лес', 'Glowshroom Forest'),
        'biome.celestial.dark_wastes': ('Пустоши тьмы', 'Dark Wastes'),
        'biome.celestial.crystal_hollows': ('Кристальные гроты', 'Crystal Hollows'),
        'biome.celestial.dark_lakes': ('Озёра тьмы', 'Dark Lakes'),
        'block.celestial.abyss_rift': ('Разлом Бездны', 'Abyss Rift'),
        'hud.celestial.fear': ('Страх', 'Fear'),
        'abyss.celestial.fear_rising': ('§5Тьма подступает… Нужен свет!', '§5The dark closes in... You need light!'),
        'death.attack.celestial.darkness': ('%1$s поглотила тьма', '%1$s was consumed by the dark'),
        'death.attack.celestial.darkness.player': ('%1$s поглотила тьма, пока %2$s смотрел', '%1$s was consumed by the dark while %2$s watched'),
        'effect.celestial.starlight': ('Звёздное сияние', 'Starlight'),
        'block.celestial.abyss_rift.sealed': ('§5Разлом запечатан: свет Серафима ещё держит его закрытым', '§5The Rift is sealed: the Seraph\'s light still holds it shut'),
        'structure.celestial.abyss_rift': ('Разлом Бездны', 'Abyss Rift'),
        'structure.celestial.abyss': ('Бездна', 'The Abyss'),
        'codex.celestial.place.abyss_rift': ('треснувший остров на дне Рая. Чёрная воронка ведёт вниз, в Бездну.',
                                             'a cracked island at the bottom of Heaven. Its black funnel leads down into the Abyss.'),
        'codex.celestial.place.abyss': ('мир под облаками, где почти нет света. Без огня в руке растёт страх.',
                                        'the world beneath the clouds, almost without light. Without a flame in hand, fear grows.'),
        'story.celestial.abyss_enter': ('§5Ты падаешь сквозь тьму… Здесь свет — редкость. Держи огонь в руке, иначе тьма заберёт рассудок.',
                                        '§5You fall through darkness... Light is rare here. Keep a flame in hand or the dark will take your mind.'),
    })
    print('ok: Бездна сгенерирована')


if __name__ == '__main__':
    main()
