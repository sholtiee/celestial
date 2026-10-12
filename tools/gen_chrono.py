"""Хроноград (волна 0.5, S4.1–S4.2, сделано Opus): блоки и измерение celestial:chronograd, портал «Часовые врата».

Мир: вечный медный закат — солнце стоит низко на западе (атрибут sun_angle, без смены суток). Рельеф: медные равнины,
плато-«кварталы» с крутыми краями, каньоны («долина часов») с лавой на дне (жидкость по умолчанию — лава, уровень 46).
Биомы: Медные равнины, Город на шестернях, Долина часов, Литейные пустоши. Постройки — отдельно (Часовая башня, Вавилон и пр.).
"""
import colorsys
import json
import math
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, VANILLA, c, save_png, self_drop, simple_cube, write_json, blockstate, model, item_def, shaped, ore_drop
from gen_story import lang_patch

WG = os.path.join(DATA, 'worldgen')
H = T.hexrgb
LAVA_LEVEL = 46


def put(img, x, y, col, a=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), (*col[:3], a))


def blocks():
    stone_pal = [H(h) for h in ('#5a4a3c', '#66553f', '#735f46', '#7f6a4f')]
    stone = T.noisy('chronite_stone', stone_pal, cell=3, grain=0.3)
    r = T.rng_for('chronite_stone_veins')
    for _ in range(3):  # тонкие медные прожилки
        x, y = r.randrange(16), r.randrange(16)
        for _ in range(6):
            put(stone, x % 16, y % 16, T.mix(H('#c8743a'), H('#e89a5a'), r.random()))
            x += r.choice((-1, 0, 1))
            y += 1
    save_png(stone, 'block/chronite_stone')
    bricks = T.bricks('chronite_bricks', [H(h) for h in ('#6a5640', '#77614a', '#836c52')], '#b0642e')
    for x, y in ((3, 3), (11, 3), (7, 11), (15, 11)):
        put(bricks, x, y, H('#e8b860'))  # латунные заклёпки
    save_png(bricks, 'block/chronite_bricks')
    ore = stone.copy()
    r = T.rng_for('chronite_ore_gems')
    for _ in range(5):  # хронит: бирюзовые кристаллы с золотой искрой — застывшее время
        x, y = r.randrange(2, 14), r.randrange(2, 14)
        for dx, dy, col in ((0, 0, '#d8fff4'), (1, 0, '#5fe0c8'), (0, 1, '#3ab8a8'), (-1, 0, '#5fe0c8'), (0, -1, '#9ff4e0'), (1, 1, '#f0c860')):
            put(ore, x + dx, y + dy, H(col))
    save_png(ore, 'block/chronite_ore')
    soil = T.noisy('brass_soil', [H(h) for h in ('#7a4a26', '#8a5630', '#9a6238', '#a87040')], cell=2, grain=0.35)
    r = T.rng_for('brass_soil_flakes')
    for _ in range(9):
        put(soil, r.randrange(16), r.randrange(16), T.mix(H('#e0b050'), H('#fff0a0'), r.random() * 0.5))
    save_png(soil, 'block/brass_soil')
    slag = T.noisy('slag', [H(h) for h in ('#1a1614', '#221c18', '#2c241e', '#36302a')], cell=3, grain=0.4)
    r = T.rng_for('slag_glints')
    for _ in range(6):
        put(slag, r.randrange(16), r.randrange(16), T.mix(H('#ff7a2a'), H('#ffc060'), r.random()))
    save_png(slag, 'block/slag')
    for n in ('chronite_stone', 'chronite_bricks', 'brass_soil', 'slag', 'chronite_ore'):
        simple_cube(n)
    for n in ('chronite_stone', 'chronite_bricks', 'brass_soil', 'slag'):
        self_drop(n)
    ore_drop('chronite_ore', c('raw_chronite'), 1, 2)
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in ('chronite_stone', 'chronite_bricks', 'chronite_ore', 'slag')])
    append_tag('block', 'minecraft:mineable/shovel', [c('brass_soil')])
    append_tag('block', 'minecraft:needs_iron_tool', [c('chronite_ore')])
    append_tag('block', 'minecraft:supports_vegetation', [c('brass_soil')])
    # растения: проволочная трава и заводной цветок (крестом, как трава)
    grass = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = T.rng_for('wire_grass')
    for k in range(6):
        x = 2 + k * 2 + r.randrange(2)
        h = 6 + r.randrange(8)
        for i in range(h):
            xx = x + round(math.sin(i * 0.6 + k) * 1.2)
            put(grass, xx, 15 - i, T.mix(H('#c8743a'), H('#f0b060'), i / h))
        put(grass, x + round(math.sin(h * 0.6 + k) * 1.2), 15 - h, H('#fff0b0'))  # блестящий кончик
    save_png(grass, 'block/wire_grass')
    flower = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for i in range(9):
        put(flower, 7 + (i % 3 == 0), 15 - i, H('#a86a30'))  # стебель-проволока
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 4.5)
            a = math.atan2(y - 4.5, x - 7.5)
            if d < 1.4:
                put(flower, x, y, H('#5fe0c8'))  # бирюзовая сердцевина
            elif d < 3.2 or (d < 4.4 and math.cos(a * 6) > 0.2):
                put(flower, x, y, H('#f0c040') if d < 3.2 else H('#c88a20'))  # лепестки-зубцы
    save_png(flower, 'block/cog_flower')
    for n in ('wire_grass', 'cog_flower'):
        model('block/' + n, {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/' + n)}})
        blockstate(n, {'variants': {'': {'model': c('block/' + n)}}})
        model('item/' + n, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/' + n)}})
        item_def(n, c('item/' + n))
        self_drop(n)


def portal():
    src = Image.open(os.path.join(ASSETS, 'textures/block/heaven_portal.png')).convert('RGBA')
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            rr, g, b, a = px[x, y]
            h, l, sat = colorsys.rgb_to_hls(rr / 255, g / 255, b / 255)
            nr, ng, nb = colorsys.hls_to_rgb(0.09, min(1.0, l * 1.05), min(1.0, sat * 0.8 + 0.25))  # янтарь
            px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    save_png(src, 'block/chrono_portal')
    with open(os.path.join(ASSETS, 'textures/block/chrono_portal.png.mcmeta'), 'w') as f:
        json.dump({'animation': {'frametime': 2, 'interpolate': True}}, f)
    blockstate('chrono_portal', {'variants': {'axis=x': {'model': c('block/chrono_portal_ns')}, 'axis=z': {'model': c('block/chrono_portal_ew')}}})
    for suffix in ('ns', 'ew'):
        with open(os.path.join(VANILLA, f'models/block/nether_portal_{suffix}.json')) as f:
            m = json.load(f)
        m['textures'] = {'particle': c('block/chrono_portal'), 'portal': c('block/chrono_portal')}
        model(f'block/chrono_portal_{suffix}', m)
    # рамка: хронитовые кирпичи — делаются в Верхнем мире из меди и часов
    shaped('chronite_bricks_from_copper', c('chronite_bricks'), ['CCC', 'CKC', 'CCC'],
           {'C': 'minecraft:copper_ingot', 'K': 'minecraft:clock'}, 8, 'building')


def dimension():
    write_json(os.path.join(DATA, 'dimension_type/chronograd.json'), {
        'ambient_light': 0.12,
        'attributes': {
            'minecraft:visual/sky_color': '#e08848', 'minecraft:visual/fog_color': '#d89858', 'minecraft:visual/cloud_color': '#ffd8b0ff',
            'minecraft:visual/cloud_height': 260.0, 'minecraft:visual/sun_angle': 72.0, 'minecraft:visual/moon_angle': 252.0,
            'minecraft:visual/star_brightness': 0.15, 'minecraft:visual/sunrise_sunset_color': '#c0ff7a2a',
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'always', 'can_sleep': 'never', 'error_message': {'translate': 'dimension.celestial.chronograd.no_sleep'}},
            'minecraft:gameplay/respawn_anchor_works': False,
        },
        'coordinate_scale': 1.0, 'default_clock': 'minecraft:overworld', 'has_ceiling': False, 'has_ender_dragon_fight': False,
        'has_fixed_time': True, 'has_skylight': True, 'height': 256, 'infiniburn': '#minecraft:infiniburn_overworld', 'logical_height': 256,
        'min_y': 0, 'monster_spawn_block_light_limit': 0,
        'monster_spawn_light_level': {'type': 'minecraft:uniform', 'min_inclusive': 0, 'max_inclusive': 7}, 'timelines': '#celestial:in_chronograd'})
    write_json(os.path.join(DATA, 'tags/timeline/in_chronograd.json'), {'values': []})
    write_json(os.path.join(DATA, 'dimension/chronograd.json'), {
        'type': c('chronograd'),
        'generator': {'type': 'minecraft:noise', 'settings': c('chronograd'), 'biome_source': {'type': 'minecraft:multi_noise', 'biomes': [
            point('copper_plains', 0.0, 0.0), point('copper_plains', -0.4, 0.3), point('cog_city', 0.5, 0.4),
            point('clock_valley', -0.5, -0.5), point('foundry_wastes', 0.6, -0.5)]}}})


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
        write_json(os.path.join(WG, f'noise/chrono_{name}.json'),
                   {'base_amplitude': 1.0, 'base_octave': octave, 'octave_count': octaves, **({'amplitude_modifiers': amps} if amps else {})})
        return {'type': 'minecraft:noise', 'noise': c(f'chrono_{name}'), 'xz_scale': 1.0, 'y_scale': 0.0}

    for name in ('temperature', 'humidity'):
        write_json(os.path.join(WG, f'density_function/chrono/{name}.json'), noise(name, -8, 2))
    land = add(add(add(grad(58, 92, 1.0, -1.0), mul(noise('continent', -8, 3), 0.35)), mul(noise('rough', -4, 2), 0.05)), -0.05)  # ровные равнины ~66–72
    # плато-кварталы: плавная маска → плоская вершина на ~92 с крутыми краями
    mask = {'type': 'minecraft:clamp', 'input': mul(add(noise('city', -7, 2), -0.28), 7.0), 'min': 0.0, 'max': 1.0}  # плато реже и крупнее
    cap = add(grad(88, 100, 2.0, -2.0), mul(noise('city_top', -3, 2), 0.25))
    plateau = add(-1.0, mul(mask, add(cap, 1.0)))
    # каньоны «долины часов»: где шум у нуля — широкий глубокий разрез до лавы
    canyon = mul({'type': 'minecraft:max', 'left': add(0.06, mul({'type': 'minecraft:abs', 'input': noise('canyon', -6, 2)}, -1.0)), 'right': 0.0}, -26.0)
    terrain = add({'type': 'minecraft:max', 'left': land, 'right': plateau}, canyon)
    final = add({'type': 'minecraft:interpolated', 'cell_size_xz': 4, 'cell_size_y': 4, 'input': terrain}, {'type': 'minecraft:beardifier'})
    write_json(os.path.join(WG, 'density_function/chrono/final_density.json'), final)


def surface():
    def block(b):
        return {'type': 'minecraft:block', 'result_state': b}

    def biome_is(*names):
        return {'type': 'minecraft:biome', 'biome_is': [c(n) for n in names]}

    write_json(os.path.join(WG, 'material_rule/chronograd.json'), {'type': 'minecraft:sequence', 'sequence': [
        'minecraft:bedrock_floor',
        {'type': 'minecraft:condition', 'if_true': biome_is('foundry_wastes'), 'then_run': {'type': 'minecraft:condition',
            'if_true': 'minecraft:on_floor', 'then_run': block(c('slag'))}},
        {'type': 'minecraft:condition', 'if_true': {'type': 'minecraft:steep'}, 'then_run': {'type': 'minecraft:condition',
            'if_true': {'type': 'minecraft:stone_depth', 'offset': 3, 'surface_type': 'floor', 'add_surface_depth': False, 'secondary_depth_range': 0},
            'then_run': block(c('chronite_stone'))}},
        # у лавы — шлак, а не почва
        {'type': 'minecraft:condition', 'if_true': {'type': 'minecraft:y_above', 'anchor': {'absolute': LAVA_LEVEL + 2},
                                                    'surface_depth_multiplier': 0, 'add_stone_depth': False},
         'then_run': {'type': 'minecraft:sequence', 'sequence': [
             {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor', 'then_run': block(c('brass_soil'))},
             {'type': 'minecraft:condition', 'if_true': 'minecraft:under_floor', 'then_run': block(c('brass_soil'))}]}},
        {'type': 'minecraft:condition', 'if_true': 'minecraft:on_floor', 'then_run': block(c('slag'))},
    ]})
    write_json(os.path.join(WG, 'noise_settings/chronograd.json'), {
        'debug_functions': [], 'default_block': c('chronite_stone'), 'default_fluid': 'minecraft:lava', 'disable_mob_generation': False,
        'legacy_random_source': False, 'material_rule': c('chronograd'), 'noise': {'min_y': 0, 'height': 256},
        'noise_router': {'chunk_surface_level': 0.0, 'continents': 0.0, 'depth': 0.0, 'erosion': 0.0, 'ridges': 0.0,
                         'final_density': c('chrono/final_density'), 'temperature': c('chrono/temperature'), 'vegetation': c('chrono/humidity')},
        'sea_level': LAVA_LEVEL, 'spawn_target': []})


def features():
    def feature(name, obj):
        write_json(os.path.join(WG, 'feature', name + '.json'), obj)

    def placed(name, feat, placement):
        write_json(os.path.join(WG, 'placed_feature', name + '.json'), {'feature': feat, 'placement': placement})

    feature('ore_chronite', {'type': 'minecraft:ore', 'discard_chance_on_air_exposure': 0.1, 'size': 6,
                             'targets': [{'state': {'id': c('chronite_ore')}, 'target': {'predicate_type': 'minecraft:block_match', 'block': c('chronite_stone')}}]})
    for name, count in (('ore_chronite', 6), ('ore_chronite_rich', 14)):
        placed(name, c('ore_chronite'), [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                                         {'type': 'minecraft:height_range', 'height': {'type': 'minecraft:uniform', 'min_inclusive': {'absolute': 4},
                                                                                       'max_inclusive': {'absolute': 80}}}, {'type': 'minecraft:biome'}])
    # растения — простая фича пятном (в 26.3 нет random_patch): точка на поверхности, затем разброс, ставим только на латунную землю
    for plant in ('wire_grass', 'cog_flower'):
        feature(plant, {'type': 'minecraft:simple_block', 'to_place': {'id': c(plant)}})
    for name, plant, count, spread in (('wire_grass_dense', 'wire_grass', 5, 6), ('wire_grass_sparse', 'wire_grass', 1, 4),
                                       ('cog_flowers', 'cog_flower', 2, 3)):
        placed(name, c(plant), [{'type': 'minecraft:count', 'count': count}, {'type': 'minecraft:in_square'},
                                {'type': 'minecraft:heightmap', 'heightmap': 'WORLD_SURFACE_WG'}, {'type': 'minecraft:biome'},
                                {'type': 'minecraft:count', 'count': spread * 3},
                                {'type': 'minecraft:offset', 'x': {'type': 'minecraft:trapezoid', 'min': -spread, 'max': spread, 'plateau': 0},
                                 'y': {'type': 'minecraft:trapezoid', 'min': -1, 'max': 1, 'plateau': 0},
                                 'z': {'type': 'minecraft:trapezoid', 'min': -spread, 'max': spread, 'plateau': 0}},
                                {'type': 'minecraft:block_predicate_filter', 'predicate': {'type': 'minecraft:matching_block_tag', 'tag': 'minecraft:air'}}])
    # (почву проверяет сама фича: растение ставится, только если выживет — тег supports_vegetation)


def biomes():
    from gen_chrono_mobs import natural_spawns
    MC = 'minecraft:'
    steps = {
        'copper_plains': {6: [c('ore_chronite')], 9: [c('wire_grass_dense'), c('cog_flowers')]},
        'cog_city': {6: [c('ore_chronite')], 9: [c('wire_grass_sparse')]},
        'clock_valley': {6: [c('ore_chronite')], 9: [c('wire_grass_sparse'), c('cog_flowers')]},
        'foundry_wastes': {1: [MC + 'lake_lava_surface'], 6: [c('ore_chronite_rich')], 9: [MC + 'delta']},
    }
    colors = {'copper_plains': ('#e08848', '#d89858'), 'cog_city': ('#d87840', '#c88a50'), 'clock_valley': ('#e09858', '#d8a868'),
              'foundry_wastes': ('#b85a30', '#a05a38')}
    for name, by_step in steps.items():
        feats = [[] for _ in range(11)]
        for step, f in by_step.items():
            feats[step] = f
        sky, fog = colors[name]
        write_json(os.path.join(WG, 'biome', name + '.json'), {
            'attributes': {'minecraft:visual/sky_color': sky, 'minecraft:visual/fog_color': fog, 'minecraft:visual/water_fog_color': '#8a5a2a',
                           'minecraft:gameplay/natural_mob_spawns': natural_spawns(name),
                           'minecraft:visual/ambient_particles': {'argument': [{'particle': {'type': c('chrono_haste')}, 'probability': 0.004}],
                                                                  'modifier': 'append'}},
            'carvers': [], 'downfall': 0.0,
            'effects': {'grass_color': '#c8843a', 'foliage_color': '#b87430', 'water_color': '#b8743a'},
            'features': feats, 'has_precipitation': False, 'temperature': 1.2})


def chronite():
    """Хронит: руда → сырой хронит → слиток; инструменты и броня в бирюзово-латунной палитре (рисунок — свои спрайты проекта)."""
    from gen_assets import smelt
    CH = {'1': '#1c3a3a', '2': '#2f6a64', '3': '#46a090', '4': '#7fd8c4', '5': '#d8fff0', '6': '#fff4c0'}
    raw = ['................', '................', '................', '.....1111.......', '....124421......', '...12446421.....', '...12455431.....',
           '...1234443211...', '....12333321....', '.....122221.....', '......1111......', '................', '................',
           '................', '................', '................']
    save_png(T.sprite(raw, CH), 'item/raw_chronite')
    save_png(T.sprite(T.SPR['etherite_ingot'], CH), 'item/chronite_ingot')
    names = ['raw_chronite', 'chronite_ingot']
    for part in ('sword', 'pickaxe', 'axe', 'shovel', 'helmet', 'chestplate', 'leggings', 'boots'):
        save_png(T.sprite(T.SPR['etherite_' + part], {**CH, **T.WOOD}), f'item/chronite_{part}')
        names.append(f'chronite_{part}')
    for n in names:
        handheld = any(n.endswith(t) for t in ('sword', 'pickaxe', 'axe', 'shovel'))
        model('item/' + n, {'parent': 'minecraft:item/handheld' if handheld else 'minecraft:item/generated', 'textures': {'layer0': c('item/' + n)}})
        item_def(n, c('item/' + n))
    palette = T.pal('#1c3a3a', '#2f6a64', '#46a090', '#7fd8c4', '#d8fff0')
    for layer in ('humanoid', 'humanoid_leggings'):
        save_png(T.armor_layer(os.path.join(VANILLA, f'textures/entity/equipment/{layer}/iron.png'), palette), f'entity/equipment/{layer}/chronite')
    write_json(os.path.join(ASSETS, 'equipment/chronite.json'), {'layers': {'humanoid': [{'texture': c('chronite')}],
                                                                          'humanoid_leggings': [{'texture': c('chronite')}]}})
    smelt('chronite_ingot', c('chronite_ingot'), c('raw_chronite'), 1.2)
    X, S, I = '#celestial:chronite_tool_materials', 'minecraft:stick', c('chronite_ingot')
    shaped('chronite_sword', c('chronite_sword'), ['X', 'X', '#'], {'X': X, '#': S}, 1, 'equipment')
    shaped('chronite_pickaxe', c('chronite_pickaxe'), ['XXX', ' # ', ' # '], {'X': X, '#': S}, 1, 'equipment')
    shaped('chronite_axe', c('chronite_axe'), ['XX', 'X#', ' #'], {'X': X, '#': S}, 1, 'equipment')
    shaped('chronite_shovel', c('chronite_shovel'), ['X', '#', '#'], {'X': X, '#': S}, 1, 'equipment')
    shaped('chronite_helmet', c('chronite_helmet'), ['XXX', 'X X'], {'X': I}, 1, 'equipment')
    shaped('chronite_chestplate', c('chronite_chestplate'), ['X X', 'XXX', 'XXX'], {'X': I}, 1, 'equipment')
    shaped('chronite_leggings', c('chronite_leggings'), ['XXX', 'X X', 'X X'], {'X': I}, 1, 'equipment')
    shaped('chronite_boots', c('chronite_boots'), ['X X', 'X X'], {'X': I}, 1, 'equipment')
    append_tag('item', 'celestial:chronite_tool_materials', [I])
    append_tag('item', 'celestial:repairs_chronite_armor', [I])
    for t in ('sword', 'pickaxe', 'axe', 'shovel'):
        append_tag('item', f'minecraft:{t}s', [c('chronite_' + t)])
    for a, slot in (('helmet', 'head'), ('chestplate', 'chest'), ('leggings', 'leg'), ('boots', 'foot')):
        append_tag('item', f'minecraft:{slot}_armor', [c('chronite_' + a)])
    e = {'item.celestial.raw_chronite': ('Сырой хронит', 'Raw Chronite'), 'item.celestial.chronite_ingot': ('Слиток хронита', 'Chronite Ingot'),
         'item.celestial.chronite_ingot.lore1': ('Металл Тувалкаина: в нём застыло время', 'Tubal-cain\'s metal: time is frozen in it'),
         'item.celestial.chronite_set.lore1': ('Полный комплект: откат реликвий времени короче на четверть', 'Full set: time relics recharge a quarter faster')}
    ru = {'sword': 'Хронитовый меч', 'pickaxe': 'Хронитовая кирка', 'axe': 'Хронитовый топор', 'shovel': 'Хронитовая лопата',
          'helmet': 'Хронитовый шлем', 'chestplate': 'Хронитовый нагрудник', 'leggings': 'Хронитовые поножи', 'boots': 'Хронитовые сапоги'}
    for part, name in ru.items():
        e[f'item.celestial.chronite_{part}'] = (name, 'Chronite ' + part.capitalize())
    lang_patch(e)


def main():
    blocks()
    chronite()
    portal()
    dimension()
    noises()
    surface()
    features()
    biomes()
    lang_patch({
        'block.celestial.chronite_stone': ('Хронитовый камень', 'Chronite Stone'),
        'block.celestial.chronite_bricks': ('Хронитовые кирпичи', 'Chronite Bricks'),
        'block.celestial.chronite_ore': ('Хронитовая руда', 'Chronite Ore'),
        'block.celestial.brass_soil': ('Латунная земля', 'Brass Soil'),
        'block.celestial.slag': ('Шлак', 'Slag'),
        'block.celestial.wire_grass': ('Проволочная трава', 'Wire Grass'),
        'block.celestial.cog_flower': ('Заводной цветок', 'Cog Flower'),
        'block.celestial.chrono_portal': ('Часовые врата', 'Clock Gate'),
        'biome.celestial.copper_plains': ('Медные равнины', 'Copper Plains'),
        'biome.celestial.cog_city': ('Город на шестернях', 'City of Cogs'),
        'biome.celestial.clock_valley': ('Долина часов', 'Valley of Clocks'),
        'biome.celestial.foundry_wastes': ('Литейные пустоши', 'Foundry Wastes'),
        'dimension.celestial.chronograd.no_sleep': ('Здесь всегда закат — ночь не наступит', 'It is always sunset here — night never comes'),
    })
    print('ok: Хроноград — блоки, измерение, портал')


if __name__ == '__main__':
    main()
