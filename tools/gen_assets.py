#!/usr/bin/env python3
"""Генератор ресурсов Celestial: текстуры, blockstates, модели, предметы, лут, рецепты, теги, переводы.

Запуск: python3 tools/gen_assets.py
Сложные blockstate (ступени, плиты, стены, заборы) берутся по образцу ванильных из .mcsrc/assets
(см. ./gradlew genSources и распаковку клиентского jar), с заменой имён и текстур.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import textures as T  # noqa: E402
import mob_textures as M  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), '..')
RES = os.path.join(ROOT, 'src/main/resources')
ASSETS = os.path.join(RES, 'assets/celestial')
DATA = os.path.join(RES, 'data/celestial')
MCDATA = os.path.join(RES, 'data/minecraft')
VANILLA = os.path.join(ROOT, '.mcsrc/assets/assets/minecraft')
NS = 'celestial'


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def save_png(img, rel):
    path = os.path.join(ASSETS, 'textures', rel + '.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def c(name):
    return f'{NS}:{name}'


def blockstate(name, obj):
    write_json(os.path.join(ASSETS, 'blockstates', name + '.json'), obj)


def model(path, obj):
    write_json(os.path.join(ASSETS, 'models', path + '.json'), obj)


def item_def(name, model_ref):
    write_json(os.path.join(ASSETS, 'items', name + '.json'), {'model': {'type': 'minecraft:model', 'model': model_ref}})


def simple_cube(name, tex=None):
    tex = tex or c('block/' + name)
    blockstate(name, {'variants': {'': {'model': c('block/' + name)}}})
    model('block/' + name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': tex}})
    item_def(name, c('block/' + name))


def clone_vanilla(vanilla_block, name, tex_map, model_suffixes, inventory_suffix=None):
    """Копирует blockstate и модели ванильного блока, заменяя имя и текстуры."""
    with open(os.path.join(VANILLA, 'blockstates', vanilla_block + '.json')) as f:
        bs = f.read()
    bs = bs.replace('minecraft:block/' + vanilla_block, c('block/' + name))
    for v, ours in tex_map.items():
        bs = bs.replace('minecraft:block/' + v + '"', ours + '"')
    blockstate(name, json.loads(bs))
    for suf in model_suffixes:
        with open(os.path.join(VANILLA, 'models/block', vanilla_block + suf + '.json')) as f:
            m = json.load(f)
        for k, v in m.get('textures', {}).items():
            key = v.replace('minecraft:block/', '')
            m['textures'][k] = tex_map.get(key, v)
        model('block/' + name + suf, m)
    item_def(name, c('block/' + name + (inventory_suffix or '')))


# ---------------------------------------------------------------- переводы
LANG = {'ru_ru': {}, 'en_us': {}}


def tr(key, ru, en):
    LANG['ru_ru'][key] = ru
    LANG['en_us'][key] = en


def block_name(name, ru, en):
    tr(f'block.{NS}.{name}', ru, en)


def item_name(name, ru, en):
    tr(f'item.{NS}.{name}', ru, en)


# ---------------------------------------------------------------- лут (формат 26.x: condition / modifier)
SILK = 'minecraft:tool/can_silk_touch'
SHEARS = {'type': 'minecraft:any_of', 'terms': ['minecraft:tool/can_shear', SILK]}
EXPLOSION = {'type': 'minecraft:survives_explosion'}


def loot(name, pools, **extra):
    write_json(os.path.join(DATA, 'loot_table/blocks', name + '.json'),
               {'type': 'minecraft:block', **extra, 'pools': pools, 'random_sequence': c('blocks/' + name)})


def self_drop(name):
    loot(name, [{'condition': EXPLOSION, 'entries': [{'type': 'minecraft:item', 'name': c(name)}], 'rolls': 1}])


def slab_drop(name):
    loot(name, [{'entries': [{'type': 'minecraft:item', 'name': c(name), 'modifier': [
        {'type': 'minecraft:set_count', 'count': 2,
         'condition': {'type': 'minecraft:match_block', 'blocks': c(name), 'state': {'type': 'double'}}},
        {'type': 'minecraft:explosion_decay'}]}], 'rolls': 1}])


def ore_drop(name, item, min_c=1, max_c=1):
    mods = []
    if max_c > 1:
        mods.append({'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': min_c, 'max': max_c}})
    mods += [{'type': 'minecraft:apply_bonus', 'enchantment': 'minecraft:fortune', 'formula': 'minecraft:ore_drops'},
             {'type': 'minecraft:explosion_decay'}]
    loot(name, [{'entries': [{'type': 'minecraft:alternatives', 'children': [
        {'type': 'minecraft:item', 'condition': SILK, 'name': c(name)},
        {'type': 'minecraft:item', 'modifier': mods, 'name': item}]}], 'rolls': 1}])


def silk_or(name, other):
    loot(name, [{'entries': [{'type': 'minecraft:alternatives', 'children': [
        {'type': 'minecraft:item', 'condition': SILK, 'name': c(name)},
        {'type': 'minecraft:item', 'condition': EXPLOSION, 'name': other}]}], 'rolls': 1}])


def leaves_drop(name, sapling):
    not_shears = {'type': 'minecraft:inverted', 'term': SHEARS}
    loot(name, [
        {'entries': [{'type': 'minecraft:alternatives', 'children': [
            {'type': 'minecraft:item', 'condition': SHEARS, 'name': c(name)},
            {'type': 'minecraft:item', 'condition': {'type': 'minecraft:all_of', 'terms': [
                EXPLOSION, {'type': 'minecraft:table_bonus', 'chances': [0.05, 0.0625, 0.083333336, 0.1], 'enchantment': 'minecraft:fortune'}]},
             'name': sapling}]}], 'rolls': 1},
        {'condition': not_shears, 'entries': [{'type': 'minecraft:item',
            'condition': {'type': 'minecraft:table_bonus', 'chances': [0.02, 0.022222223, 0.025, 0.033333335, 0.1], 'enchantment': 'minecraft:fortune'},
            'modifier': [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'max': 2, 'min': 1}}, {'type': 'minecraft:explosion_decay'}],
            'name': 'minecraft:stick'}], 'rolls': 1},
        {'condition': not_shears, 'entries': [{'type': 'minecraft:item',
            'condition': {'type': 'minecraft:table_bonus', 'chances': [0.02, 0.025, 0.03, 0.04, 0.08], 'enchantment': 'minecraft:fortune'},
            'name': c('manna_berries')}], 'rolls': 1}])


def manna_loot():
    def pool(age, lo, hi):
        return {'condition': {'type': 'minecraft:match_block', 'blocks': c('manna_bush'), 'state': {'age': str(age)}},
                'entries': [{'type': 'minecraft:item', 'name': c('manna_berries')}],
                'modifier': [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'max': hi, 'min': lo}},
                             {'type': 'minecraft:apply_bonus', 'enchantment': 'minecraft:fortune', 'formula': 'minecraft:uniform_bonus_count', 'parameters': {'bonusMultiplier': 1}}],
                'rolls': 1}
    pools = [pool(3, 2, 3), pool(2, 1, 2)]
    loot('manna_bush', pools, modifier={'type': 'minecraft:explosion_decay'})
    write_json(os.path.join(DATA, 'loot_table/harvest/manna_bush.json'),
               {'type': 'minecraft:block', 'modifier': {'type': 'minecraft:explosion_decay'}, 'pools': pools, 'random_sequence': c('harvest/manna_bush')})


# ---------------------------------------------------------------- рецепты
def recipe(name, obj):
    write_json(os.path.join(DATA, 'recipe', name + '.json'), obj)


def shaped(name, result, pattern, key, count=1, category='misc', group=None):
    r = {'type': 'minecraft:crafting_shaped', 'category': category, 'key': key, 'pattern': pattern,
         'result': {'id': result, **({'count': count} if count > 1 else {})}}
    if group:
        r['group'] = group
    recipe(name, r)


def shapeless(name, result, ingredients, count=1, category='misc'):
    recipe(name, {'type': 'minecraft:crafting_shapeless', 'category': category, 'ingredients': ingredients,
                  'result': {'id': result, **({'count': count} if count > 1 else {})}})


def smelt(name, result, ingredient, xp=0.7, blasting=True):
    recipe(name, {'type': 'minecraft:smelting', 'category': 'misc', 'cookingtime': 200, 'experience': xp,
                  'ingredient': ingredient, 'result': {'id': result}})
    if blasting:
        recipe(name + '_blasting', {'type': 'minecraft:blasting', 'category': 'misc', 'cookingtime': 100, 'experience': xp,
                                    'ingredient': ingredient, 'result': {'id': result}})


def stonecut(name, result, ingredient, count=1):
    recipe(name, {'type': 'minecraft:stonecutting', 'ingredient': ingredient, 'result': {'id': result, 'count': count}})


# ---------------------------------------------------------------- теги
TAGS = {}


def tag(kind, name, *values):
    TAGS.setdefault((kind, name), [])
    TAGS[(kind, name)] += list(values)


def write_tags():
    for (kind, name), values in TAGS.items():
        ns, path = name.split(':')
        base = MCDATA if ns == 'minecraft' else DATA
        write_json(os.path.join(base, 'tags', kind, path + '.json'), {'replace': False, 'values': values})


# ================================================================ содержимое
def gen_blocks():
    # --- текстуры блоков
    save_png(T.dirt(), 'block/heaven_dirt')
    save_png(T.golden_grass_top(), 'block/golden_grass_top')
    save_png(T.golden_grass_side(), 'block/golden_grass_side')
    save_png(T.skystone(), 'block/skystone')
    save_png(T.bricks('skystone_bricks', T.SKYSTONE[1:], '#8b97a9'), 'block/skystone_bricks')
    save_png(T.radiant_stone(), 'block/radiant_stone')
    save_png(T.log_side(), 'block/skywood_log')
    save_png(T.log_top(), 'block/skywood_log_top')
    save_png(T.planks(), 'block/skywood_planks')
    save_png(T.leaves(), 'block/skywood_leaves')
    save_png(T.cloud('cloud', T.CLOUD, 215), 'block/cloud')
    save_png(T.cloud('golden_cloud', T.GOLD_CLOUD, 225), 'block/golden_cloud')
    save_png(T.cloud('rain_cloud', T.RAIN_CLOUD, 190), 'block/rain_cloud')
    save_png(T.ore('etherite_ore', T.ETHERITE[1:]), 'block/etherite_ore')
    save_png(T.ore('starquartz_ore', T.STARQ, count=7), 'block/starquartz_ore')
    save_png(T.metal_block(T.ETHERITE), 'block/etherite_block')
    for k, (colors, rows) in T.SPR_MISC.items():
        if k in ('skywood_sapling', 'sky_crystal'):
            save_png(T.sprite(rows, colors), 'block/' + k)
    for s in range(4):
        save_png(T.manna_stage(s), f'block/manna_bush_stage{s}')

    # --- простые кубы
    for n in ['heaven_dirt', 'skystone', 'skystone_bricks', 'radiant_stone', 'skywood_planks',
              'cloud', 'golden_cloud', 'rain_cloud', 'etherite_ore', 'starquartz_ore', 'etherite_block']:
        simple_cube(n)

    # --- золотая трава
    blockstate('golden_grass', {'variants': {'': [{'model': c('block/golden_grass')}, {'model': c('block/golden_grass'), 'y': 90},
                                                   {'model': c('block/golden_grass'), 'y': 180}, {'model': c('block/golden_grass'), 'y': 270}]}})
    model('block/golden_grass', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/golden_grass_top'), 'bottom': c('block/heaven_dirt'), 'side': c('block/golden_grass_side')}})
    item_def('golden_grass', c('block/golden_grass'))

    # --- брёвна
    blockstate('skywood_log', {'variants': {
        'axis=x': {'model': c('block/skywood_log_horizontal'), 'x': 90, 'y': 90},
        'axis=y': {'model': c('block/skywood_log')},
        'axis=z': {'model': c('block/skywood_log_horizontal'), 'x': 90}}})
    model('block/skywood_log', {'parent': 'minecraft:block/cube_column', 'textures': {'end': c('block/skywood_log_top'), 'side': c('block/skywood_log')}})
    model('block/skywood_log_horizontal', {'parent': 'minecraft:block/cube_column_horizontal', 'textures': {'end': c('block/skywood_log_top'), 'side': c('block/skywood_log')}})
    item_def('skywood_log', c('block/skywood_log'))
    blockstate('skywood_wood', {'variants': {
        'axis=x': {'model': c('block/skywood_wood'), 'x': 90, 'y': 90},
        'axis=y': {'model': c('block/skywood_wood')},
        'axis=z': {'model': c('block/skywood_wood'), 'x': 90}}})
    model('block/skywood_wood', {'parent': 'minecraft:block/cube_column', 'textures': {'end': c('block/skywood_log'), 'side': c('block/skywood_log')}})
    item_def('skywood_wood', c('block/skywood_wood'))

    # --- листва, саженец, кристалл, куст
    simple_cube('skywood_leaves')
    model('block/skywood_leaves', {'parent': 'minecraft:block/leaves', 'textures': {'all': c('block/skywood_leaves')}})
    blockstate('skywood_sapling', {'variants': {'': {'model': c('block/skywood_sapling')}}})
    model('block/skywood_sapling', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/skywood_sapling')}})
    model('item/skywood_sapling', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/skywood_sapling')}})
    item_def('skywood_sapling', c('item/skywood_sapling'))

    with open(os.path.join(VANILLA, 'blockstates/amethyst_cluster.json')) as f:
        blockstate('sky_crystal', json.loads(f.read().replace('minecraft:block/amethyst_cluster', c('block/sky_crystal'))))
    model('block/sky_crystal', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/sky_crystal')}})
    model('item/sky_crystal', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/sky_crystal')}})
    item_def('sky_crystal', c('item/sky_crystal'))

    blockstate('manna_bush', {'variants': {f'age={a}': {'model': c(f'block/manna_bush_stage{a}')} for a in range(4)}})
    for a in range(4):
        model(f'block/manna_bush_stage{a}', {'parent': 'minecraft:block/cross', 'textures': {'cross': c(f'block/manna_bush_stage{a}')}})

    # --- строительные семейства
    planks = c('block/skywood_planks')
    bricks = c('block/skystone_bricks')
    clone_vanilla('oak_stairs', 'skywood_stairs', {'oak_planks': planks}, ['', '_inner', '_outer'])
    clone_vanilla('oak_slab', 'skywood_slab', {'oak_planks': planks}, ['', '_top'])
    clone_vanilla('oak_fence', 'skywood_fence', {'oak_planks': planks}, ['_post', '_side', '_inventory'], '_inventory')
    clone_vanilla('oak_fence_gate', 'skywood_fence_gate', {'oak_planks': planks}, ['', '_open', '_wall', '_wall_open'])
    clone_vanilla('stone_brick_stairs', 'skystone_brick_stairs', {'stone_bricks': bricks}, ['', '_inner', '_outer'])
    clone_vanilla('stone_brick_slab', 'skystone_brick_slab', {'stone_bricks': bricks}, ['', '_top'])
    clone_vanilla('stone_brick_wall', 'skystone_brick_wall', {'stone_bricks': bricks}, ['_post', '_side', '_side_tall', '_inventory'], '_inventory')
    # двойная плита ссылается на целый блок
    for slab, full in (('skywood_slab', 'skywood_planks'), ('skystone_brick_slab', 'skystone_bricks')):
        path = os.path.join(ASSETS, 'blockstates', slab + '.json')
        with open(path) as f:
            bs = json.load(f)
        bs['variants']['type=double'] = {'model': c('block/' + full)}
        write_json(path, bs)

    # --- портал в Рай
    save_png(T.heaven_portal(), 'block/heaven_portal')
    with open(os.path.join(ASSETS, 'textures/block/heaven_portal.png.mcmeta'), 'w') as f:
        json.dump({'animation': {'frametime': 2, 'interpolate': True}}, f)
    blockstate('heaven_portal', {'variants': {'axis=x': {'model': c('block/heaven_portal_ns')}, 'axis=z': {'model': c('block/heaven_portal_ew')}}})
    for suffix in ('ns', 'ew'):
        with open(os.path.join(VANILLA, f'models/block/nether_portal_{suffix}.json')) as f:
            m = json.load(f)
        m['textures'] = {'particle': c('block/heaven_portal'), 'portal': c('block/heaven_portal')}
        model(f'block/heaven_portal_{suffix}', m)

    # --- названия
    names = {
        'heaven_portal': ('Портал в Рай', 'Heaven Portal'),
        'heaven_dirt': ('Небесная земля', 'Heaven Dirt'),
        'golden_grass': ('Золотая трава', 'Golden Grass'),
        'skystone': ('Небесный камень', 'Skystone'),
        'skystone_bricks': ('Кирпичи из небесного камня', 'Skystone Bricks'),
        'skystone_brick_stairs': ('Ступени из небесного кирпича', 'Skystone Brick Stairs'),
        'skystone_brick_slab': ('Плита из небесного кирпича', 'Skystone Brick Slab'),
        'skystone_brick_wall': ('Ограда из небесного кирпича', 'Skystone Brick Wall'),
        'radiant_stone': ('Светлый камень', 'Radiant Stone'),
        'skywood_log': ('Бревно небесного дерева', 'Skywood Log'),
        'skywood_wood': ('Древесина небесного дерева', 'Skywood Wood'),
        'skywood_planks': ('Доски небесного дерева', 'Skywood Planks'),
        'skywood_stairs': ('Ступени из небесного дерева', 'Skywood Stairs'),
        'skywood_slab': ('Плита из небесного дерева', 'Skywood Slab'),
        'skywood_fence': ('Забор из небесного дерева', 'Skywood Fence'),
        'skywood_fence_gate': ('Калитка из небесного дерева', 'Skywood Fence Gate'),
        'skywood_leaves': ('Листва небесного дерева', 'Skywood Leaves'),
        'skywood_sapling': ('Саженец небесного дерева', 'Skywood Sapling'),
        'cloud': ('Облако', 'Cloud'),
        'golden_cloud': ('Золотое облако', 'Golden Cloud'),
        'rain_cloud': ('Дождевое облако', 'Rain Cloud'),
        'etherite_ore': ('Эфиритовая руда', 'Etherite Ore'),
        'starquartz_ore': ('Руда звёздного кварца', 'Starquartz Ore'),
        'etherite_block': ('Эфиритовый блок', 'Block of Etherite'),
        'sky_crystal': ('Небесный кристалл', 'Sky Crystal'),
        'manna_bush': ('Манна-куст', 'Manna Bush'),
    }
    for k, (ru, en) in names.items():
        block_name(k, ru, en)

    # --- лут
    for n in ['heaven_dirt', 'skystone_bricks', 'skystone_brick_stairs', 'skystone_brick_wall', 'radiant_stone',
              'skywood_log', 'skywood_wood', 'skywood_planks', 'skywood_stairs', 'skywood_fence', 'skywood_fence_gate',
              'skywood_sapling', 'cloud', 'golden_cloud', 'rain_cloud', 'etherite_block']:
        self_drop(n)
    slab_drop('skywood_slab')
    slab_drop('skystone_brick_slab')
    silk_or('golden_grass', c('heaven_dirt'))
    silk_or('skystone', c('skystone'))
    ore_drop('etherite_ore', c('raw_etherite'))
    ore_drop('starquartz_ore', c('starquartz'), 1, 2)
    ore_drop('sky_crystal', c('starquartz'), 1, 2)
    leaves_drop('skywood_leaves', c('skywood_sapling'))
    manna_loot()

    # --- теги блоков
    tag('block', 'minecraft:mineable/pickaxe', *map(c, ['skystone', 'skystone_bricks', 'skystone_brick_stairs', 'skystone_brick_slab',
                                                        'skystone_brick_wall', 'radiant_stone', 'etherite_ore', 'starquartz_ore',
                                                        'etherite_block', 'sky_crystal']))
    tag('block', 'minecraft:mineable/shovel', c('heaven_dirt'), c('golden_grass'), c('cloud'), c('golden_cloud'), c('rain_cloud'))
    tag('block', 'minecraft:mineable/axe', *map(c, ['skywood_log', 'skywood_wood', 'skywood_planks', 'skywood_stairs', 'skywood_slab',
                                                    'skywood_fence', 'skywood_fence_gate', 'manna_bush']))
    tag('block', 'minecraft:mineable/hoe', c('skywood_leaves'))
    tag('block', 'minecraft:needs_iron_tool', c('etherite_ore'), c('etherite_block'), c('radiant_stone'))
    tag('block', 'minecraft:needs_stone_tool', c('starquartz_ore'))
    tag('block', 'celestial:skywood_logs', c('skywood_log'), c('skywood_wood'))
    tag('block', 'minecraft:logs_that_burn', '#celestial:skywood_logs')
    tag('block', 'minecraft:planks', c('skywood_planks'))
    tag('block', 'minecraft:wooden_stairs', c('skywood_stairs'))
    tag('block', 'minecraft:wooden_slabs', c('skywood_slab'))
    tag('block', 'minecraft:wooden_fences', c('skywood_fence'))
    tag('block', 'minecraft:fence_gates', c('skywood_fence_gate'))
    tag('block', 'minecraft:stairs', c('skystone_brick_stairs'))
    tag('block', 'minecraft:slabs', c('skystone_brick_slab'))
    tag('block', 'minecraft:walls', c('skystone_brick_wall'))
    tag('block', 'minecraft:leaves', c('skywood_leaves'))
    tag('block', 'minecraft:saplings', c('skywood_sapling'))
    tag('block', 'minecraft:dirt', c('heaven_dirt'), c('golden_grass'))
    tag('block', 'minecraft:substrate_overworld', c('heaven_dirt'), c('golden_grass'))
    tag('block', 'minecraft:beacon_base_blocks', c('etherite_block'))
    tag('block', 'celestial:base_stone_heaven', c('skystone'))

    # --- теги предметов
    tag('item', 'celestial:skywood_logs', c('skywood_log'), c('skywood_wood'))
    tag('item', 'minecraft:logs_that_burn', '#celestial:skywood_logs')
    tag('item', 'minecraft:planks', c('skywood_planks'))
    tag('item', 'minecraft:wooden_stairs', c('skywood_stairs'))
    tag('item', 'minecraft:wooden_slabs', c('skywood_slab'))
    tag('item', 'minecraft:wooden_fences', c('skywood_fence'))
    tag('item', 'minecraft:fence_gates', c('skywood_fence_gate'))
    tag('item', 'minecraft:stairs', c('skystone_brick_stairs'))
    tag('item', 'minecraft:slabs', c('skystone_brick_slab'))
    tag('item', 'minecraft:walls', c('skystone_brick_wall'))
    tag('item', 'minecraft:leaves', c('skywood_leaves'))
    tag('item', 'minecraft:saplings', c('skywood_sapling'))
    tag('item', 'minecraft:dirt', c('heaven_dirt'), c('golden_grass'))
    tag('item', 'minecraft:stone_crafting_materials', c('skystone'))
    tag('item', 'minecraft:stone_tool_materials', c('skystone'))

    # --- рецепты блоков
    shapeless('skywood_planks', c('skywood_planks'), ['#celestial:skywood_logs'], 4, 'building')
    shaped('skywood_wood', c('skywood_wood'), ['##', '##'], {'#': c('skywood_log')}, 3, 'building')
    shaped('skywood_stairs', c('skywood_stairs'), ['#  ', '## ', '###'], {'#': c('skywood_planks')}, 4, 'building', 'wooden_stairs')
    shaped('skywood_slab', c('skywood_slab'), ['###'], {'#': c('skywood_planks')}, 6, 'building', 'wooden_slab')
    shaped('skywood_fence', c('skywood_fence'), ['W#W', 'W#W'], {'W': c('skywood_planks'), '#': 'minecraft:stick'}, 3, 'misc', 'wooden_fence')
    shaped('skywood_fence_gate', c('skywood_fence_gate'), ['#W#', '#W#'], {'W': c('skywood_planks'), '#': 'minecraft:stick'}, 1, 'redstone', 'wooden_fence_gate')
    shaped('skystone_bricks', c('skystone_bricks'), ['##', '##'], {'#': c('skystone')}, 4, 'building')
    shaped('skystone_brick_stairs', c('skystone_brick_stairs'), ['#  ', '## ', '###'], {'#': c('skystone_bricks')}, 4, 'building')
    shaped('skystone_brick_slab', c('skystone_brick_slab'), ['###'], {'#': c('skystone_bricks')}, 6, 'building')
    shaped('skystone_brick_wall', c('skystone_brick_wall'), ['###', '###'], {'#': c('skystone_bricks')}, 6, 'misc')
    stonecut('skystone_bricks_from_stonecutting', c('skystone_bricks'), c('skystone'))
    stonecut('skystone_brick_stairs_from_stonecutting', c('skystone_brick_stairs'), c('skystone_bricks'))
    stonecut('skystone_brick_slab_from_stonecutting', c('skystone_brick_slab'), c('skystone_bricks'), 2)
    stonecut('skystone_brick_wall_from_stonecutting', c('skystone_brick_wall'), c('skystone_bricks'))
    # светлый камень — рамка портала в Рай: свет Ада + кварц звёзд + небесный камень
    # светлый камень — рамка портала в Рай: только материалы Ада и Верхнего мира, иначе в Рай не попасть
    shaped('radiant_stone', c('radiant_stone'), ['GQG', 'QBQ', 'GQG'],
           {'G': 'minecraft:glowstone_dust', 'Q': 'minecraft:quartz', 'B': 'minecraft:gold_block'}, 4, 'building')
    shaped('cloud', c('cloud'), ['##', '##'], {'#': c('cloud_fluff')}, 1, 'building')
    shaped('golden_cloud', c('golden_cloud'), [' G ', 'GCG', ' G '], {'G': 'minecraft:gold_nugget', 'C': c('cloud')}, 1, 'building')
    shapeless('rain_cloud', c('rain_cloud'), [c('cloud'), 'minecraft:water_bucket'], 1, 'building')
    shaped('etherite_block', c('etherite_block'), ['###', '###', '###'], {'#': c('etherite_ingot')}, 1, 'building')
    shapeless('etherite_ingot_from_block', c('etherite_ingot'), [c('etherite_block')], 9)
    smelt('etherite_ingot', c('etherite_ingot'), c('raw_etherite'), 1.0)
    smelt('etherite_ingot_from_ore', c('etherite_ingot'), c('etherite_ore'), 1.0)
    smelt('skystone_smooth', c('skystone_bricks'), c('skystone'), 0.1, blasting=False)


def gen_items():
    flat = {}
    for k, rows in T.SPR.items():
        flat[k] = T.sprite(rows, {**T.ETH, **T.WOOD})
    for k, rows in T.SPR_STAR.items():
        flat[k] = T.sprite(rows, T.STAR)
    for k, (colors, rows) in T.SPR_MISC.items():
        if k not in ('skywood_sapling', 'sky_crystal'):
            flat[k] = T.sprite(rows, colors)
    handheld = {'etherite_sword', 'etherite_pickaxe', 'etherite_axe', 'etherite_shovel', 'etherite_hoe'}
    for k, img in flat.items():
        save_png(img, 'item/' + k)
        model('item/' + k, {'parent': 'minecraft:item/handheld' if k in handheld else 'minecraft:item/generated',
                            'textures': {'layer0': c('item/' + k)}})
        item_def(k, c('item/' + k))

    names = {
        'raw_etherite': ('Необработанный эфирит', 'Raw Etherite'),
        'etherite_ingot': ('Эфиритовый слиток', 'Etherite Ingot'),
        'starquartz': ('Звёздный кварц', 'Starquartz'),
        'cloud_fluff': ('Облачная вата', 'Cloud Fluff'),
        'manna_berries': ('Манна', 'Manna Berries'),
        'etherite_sword': ('Эфиритовый меч', 'Etherite Sword'),
        'etherite_pickaxe': ('Эфиритовая кирка', 'Etherite Pickaxe'),
        'etherite_axe': ('Эфиритовый топор', 'Etherite Axe'),
        'etherite_shovel': ('Эфиритовая лопата', 'Etherite Shovel'),
        'etherite_hoe': ('Эфиритовая мотыга', 'Etherite Hoe'),
        'etherite_helmet': ('Эфиритовый шлем', 'Etherite Helmet'),
        'etherite_chestplate': ('Эфиритовый нагрудник', 'Etherite Chestplate'),
        'etherite_leggings': ('Эфиритовые поножи', 'Etherite Leggings'),
        'etherite_boots': ('Эфиритовые ботинки', 'Etherite Boots'),
        'flame_shard': ('Осколок Пламени', 'Flame Shard'),
        'void_heart': ('Сердце Пустоты', 'Void Heart'),
    }
    for k, (ru, en) in names.items():
        item_name(k, ru, en)
    tr('itemGroup.celestial', 'Celestial: Рай', 'Celestial: Heaven')

    # броня: слои в textures/entity/equipment/*
    for layer in ('humanoid', 'humanoid_leggings'):
        img = T.armor_layer(os.path.join(VANILLA, f'textures/entity/equipment/{layer}/diamond.png'), T.ETHERITE)
        save_png(img, f'entity/equipment/{layer}/etherite')
    write_json(os.path.join(ASSETS, 'equipment/etherite.json'), {'layers': {
        'humanoid': [{'texture': c('etherite')}],
        'humanoid_leggings': [{'texture': c('etherite')}]}})

    tag('item', 'celestial:etherite_tool_materials', c('etherite_ingot'))
    tag('item', 'celestial:repairs_etherite_armor', c('etherite_ingot'))
    for t in ('sword', 'pickaxe', 'axe', 'shovel', 'hoe'):
        tag('item', f'minecraft:{t}s', c('etherite_' + t))
    for a in ('helmet', 'chestplate', 'leggings', 'boots'):
        tag('item', f'minecraft:{"foot" if a == "boots" else "leg" if a == "leggings" else "chest" if a == "chestplate" else "head"}_armor', c('etherite_' + a))
    tag('item', 'minecraft:trimmable_armor', *[c('etherite_' + a) for a in ('helmet', 'chestplate', 'leggings', 'boots')])

    # рецепты экипировки
    X, S = '#celestial:etherite_tool_materials', 'minecraft:stick'
    shaped('etherite_sword', c('etherite_sword'), ['X', 'X', '#'], {'X': X, '#': S}, 1, 'equipment')
    shaped('etherite_pickaxe', c('etherite_pickaxe'), ['XXX', ' # ', ' # '], {'X': X, '#': S}, 1, 'equipment')
    shaped('etherite_axe', c('etherite_axe'), ['XX', 'X#', ' #'], {'X': X, '#': S}, 1, 'equipment')
    shaped('etherite_shovel', c('etherite_shovel'), ['X', '#', '#'], {'X': X, '#': S}, 1, 'equipment')
    shaped('etherite_hoe', c('etherite_hoe'), ['XX', ' #', ' #'], {'X': X, '#': S}, 1, 'equipment')
    I = c('etherite_ingot')
    shaped('etherite_helmet', c('etherite_helmet'), ['XXX', 'X X'], {'X': I}, 1, 'equipment')
    shaped('etherite_chestplate', c('etherite_chestplate'), ['X X', 'XXX', 'XXX'], {'X': I}, 1, 'equipment')
    shaped('etherite_leggings', c('etherite_leggings'), ['XXX', 'X X', 'X X'], {'X': I}, 1, 'equipment')
    shaped('etherite_boots', c('etherite_boots'), ['X X', 'X X'], {'X': I}, 1, 'equipment')


def entity_loot(name, entries):
    """entries: список (предмет, мин, макс[, шанс_только_от_игрока])."""
    pools = []
    for e in entries:
        item, lo, hi = e[:3]
        pool = {'entries': [{'type': 'minecraft:item', 'name': item, 'modifier': [
            {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}},
            {'type': 'minecraft:enchanted_count_increase', 'count': {'type': 'minecraft:uniform', 'min': 0.0, 'max': 1.0}, 'enchantment': 'minecraft:looting'}]}],
            'rolls': 1}
        if len(e) > 3:
            pool['condition'] = {'type': 'minecraft:all_of', 'terms': [
                {'type': 'minecraft:killed_by_player'}, {'type': 'minecraft:random_chance', 'chance': e[3]}]}
        pools.append(pool)
    write_json(os.path.join(DATA, 'loot_table/entities', name + '.json'),
               {'type': 'minecraft:entity', 'pools': pools, 'random_sequence': c('entities/' + name)})


def trade(name, gives, gives_count, wants, wants_count, max_uses=12):
    write_json(os.path.join(DATA, 'villager_trade/angel', name + '.json'), {
        'gives': {'id': gives, **({'count': gives_count} if gives_count > 1 else {})},
        'max_uses': max_uses, 'reputation_discount': 0.0,
        'wants': {'id': wants, **({'count': wants_count} if wants_count > 1 else {})}})
    return c('angel/' + name)


def gen_mobs():
    textures = {
        'fallen_guardian': M.fallen_guardian(), 'fallen_seraph': M.fallen_seraph(),
        'winged_serpent': M.winged_serpent(), 'cloud_whale': M.cloud_whale(),
        'light_wisp': M.light_wisp(), 'pegasus': M.pegasus(), 'pegasus_baby': M.pegasus(baby=True),
        'pegasus_golden': M.pegasus(coat='golden'), 'pegasus_storm': M.pegasus(coat='storm'),
        'golden_ram': M.golden_ram(), 'sky_ray': M.sky_ray(), 'cloud_jelly': M.cloud_jelly(), 'mimic': M.mimic(),
    }
    for k, img in textures.items():
        save_png(img, 'entity/' + k)
    save_png(M.seraph_wings_layer(), 'entity/equipment/wings/seraph_wings')
    write_json(os.path.join(ASSETS, 'equipment/seraph_wings.json'), {'layers': {'wings': [{'texture': c('seraph_wings')}]}})

    mobs = {
        'fallen_guardian': ('Падший страж', 'Fallen Guardian', '#4a5263', '#5ff5ff'),
        'storm_spirit': ('Грозовой дух', 'Storm Spirit', '#4d5770', '#bfe9ff'),
        'winged_serpent': ('Крылатый змей', 'Winged Serpent', '#dcb252', '#7a5418'),
        'cloud_whale': ('Облачный кит', 'Cloud Whale', '#eef3fa', '#9db4d6'),
        'light_wisp': ('Светлячок-проводник', 'Light Wisp', '#fff6c8', '#ffb92e'),
        'angel': ('Небесный житель', 'Angel', '#f7f4ec', '#e3b54a'),
        'pegasus': ('Пегас', 'Pegasus', '#faf8ff', '#efc24f'),
        'fallen_seraph': ('Падший Серафим', 'Fallen Seraph', '#2a2230', '#d4a531'),
        'cherub': ('Херувим', 'Cherub', '#fff1d6', '#ffd78f'),
        'golden_ram': ('Златорунный баран', 'Golden Ram', '#f0e2c2', '#d9a62e'),
        'sky_ray': ('Небесный скат', 'Sky Ray', '#6aa0e2', '#ffe08a'),
        'cloud_jelly': ('Облачная медуза', 'Cloud Jelly', '#f4f8ff', '#bfd8ff'),
        'mimic': ('Мимик', 'Mimic', '#d8c9a8', '#5a1a2a'),
        'storm_elemental': ('Грозовой элементаль', 'Storm Elemental', '#3c4458', '#ffffff'),
    }
    for k, (ru, en, base, spots) in mobs.items():
        tr(f'entity.{NS}.{k}', ru, en)
        egg = k + '_spawn_egg'
        save_png(M.spawn_egg(base, spots), 'item/' + egg)
        model('item/' + egg, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + egg)}})
        item_def(egg, c('item/' + egg))
        item_name(egg, f'Яйцо призыва: {ru.lower() if k != "angel" else ru}', f'{en} Spawn Egg')

    # крылья Серафима — предмет
    wings_icon = T.sprite([
        '................',
        '.11..........11.',
        '.121........121.',
        '.1221......1221.',
        '.12221....12221.',
        '..12231..13221..',
        '..122231132221..',
        '...1222332221...',
        '...1222332221...',
        '....12233221....',
        '....1223.3221...',
        '.....12...21....',
        '......1....1....',
        '................',
        '................',
        '................'], {'1': '#c9b27a', '2': '#ffffff', '3': '#f3d27a'})
    save_png(wings_icon, 'item/seraph_wings')
    model('item/seraph_wings', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/seraph_wings')}})
    item_def('seraph_wings', c('item/seraph_wings'))
    item_name('seraph_wings', 'Крылья Серафима', 'Seraph Wings')

    # добыча
    entity_loot('fallen_guardian', [('minecraft:gold_nugget', 1, 4), (c('raw_etherite'), 0, 1), (c('starquartz'), 1, 1, 0.12), (c('seraph_feather'), 1, 1, 0.08), (c('bronze_key'), 1, 1, 0.1)])
    entity_loot('storm_spirit', [(c('starquartz'), 1, 2), ('minecraft:glowstone_dust', 0, 2), (c('silver_key'), 1, 1, 0.08)])
    entity_loot('winged_serpent', [('minecraft:phantom_membrane', 0, 1), (c('cloud_fluff'), 0, 2), (c('seraph_feather'), 1, 1, 0.15)])
    entity_loot('cloud_whale', [(c('cloud_fluff'), 3, 6)])
    entity_loot('light_wisp', [('minecraft:glowstone_dust', 1, 1)])
    entity_loot('pegasus', [('minecraft:leather', 0, 2)])
    entity_loot('angel', [])
    entity_loot('cherub', [])
    entity_loot('golden_ram', [('minecraft:mutton', 1, 2)])
    entity_loot('sky_ray', [(c('cloud_fluff'), 1, 3), ('minecraft:leather', 0, 2)])
    entity_loot('cloud_jelly', [(c('sky_jelly'), 0, 2)])
    entity_loot('mimic', [(c('starquartz'), 2, 5), (c('etherite_ingot'), 0, 2), (c('bronze_key'), 1, 1, 0.5), ('minecraft:gold_ingot', 1, 3)])
    entity_loot('storm_elemental', [(c('starquartz'), 4, 8), (c('silver_key'), 1, 1), (c('seraph_feather'), 1, 3)])
    write_json(os.path.join(DATA, 'loot_table/shearing/golden_ram.json'), {'type': 'minecraft:shearing', 'pools': [
        {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('golden_fleece'),
                                  'modifier': [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 1, 'max': 2}}]}]}],
        'random_sequence': c('shearing/golden_ram')})
    tag('entity_type', 'minecraft:can_equip_harness', c('sky_ray'))
    tag('item', 'minecraft:happy_ghast_food', c('manna_berries'))
    tag('item', 'minecraft:happy_ghast_tempt_items', c('manna_berries'))
    for k, (colors, rows) in {
        'sky_jelly': ({'1': '#9db4d6', '2': '#dbe7fb', '3': '#ffffff', '4': '#ffe9a8'}, [
            '................', '................', '.....111111.....', '....12222221....', '...1223332221...', '...1233443321...',
            '...1233333321...', '...1222222221...', '....11111111....', '.....1.1.1.1....', '....1.1.1.1.....', '.....1.1.1.1....',
            '................', '................', '................', '................']),
        'golden_fleece': ({'1': '#b9862a', '2': '#efc24f', '3': '#ffe08a'}, [
            '................', '................', '...1111111111...', '..122332233221..', '.12333223332221.', '.12322333222321.',
            '.12233322333221.', '..1223332233221.', '..12223322332211', '...122332222321.', '...12222333221..', '....1122222211..',
            '......111111....', '................', '................', '................'])}.items():
        save_png(T.sprite(rows, colors), 'item/' + k)
        model('item/' + k, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + k)}})
        item_def(k, c('item/' + k))
    item_name('sky_jelly', 'Небесное желе', 'Sky Jelly')
    item_name('golden_fleece', 'Золотое руно', 'Golden Fleece')
    write_json(os.path.join(DATA, 'loot_table/entities/fallen_seraph.json'), {'type': 'minecraft:entity', 'pools': [
        # Осколок Света не лутом (пропадал за 5 минут, а Печать будит Серафима один раз): StoryEvents.onSeraphDefeated выдаёт его напрямую
        {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('seraph_wings')}]},
        {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('halo')}]},
        {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('seraph_feather'), 'modifier': [
            {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 4, 'max': 8}}]}]},
        {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('etherite_ingot'), 'modifier': [
            {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 4, 'max': 8}}]}]}],
        'random_sequence': c('entities/fallen_seraph')})
    tr('boss.celestial.fallen_seraph.awaken', '§6Печать трескается. Падший Серафим пробуждается!', '§6The seal cracks. The Fallen Seraph awakens!')
    tr('boss.celestial.fallen_seraph.phase2', '§eСерафим взмывает ввысь: «Свет обрушится на тебя!»', '§eThe Seraph takes flight: "Light shall rain upon you!"')
    tr('boss.celestial.fallen_seraph.phase3', '§cСерафим в ярости: «Стражи, ко мне!»', '§cThe Seraph rages: "Guardians, to me!"')

    # пегас — «лошадь» для ванильных механик: седло, конская броня, следование за игроком
    for t in ('can_equip_saddle', 'can_wear_horse_armor', 'can_float_while_ridden', 'dismounts_underwater', 'followable_friendly_mobs'):
        tag('entity_type', 'minecraft:' + t, c('pegasus'))

    # торговля ангелов: валюта — звёздный кварц и эфирит
    S, E = c('starquartz'), c('etherite_ingot')
    common = [
        trade('manna', c('manna_berries'), 6, S, 1),
        trade('golden_cloud', c('golden_cloud'), 4, S, 2),
        trade('skywood_sapling', c('skywood_sapling'), 2, S, 1),
        trade('cloud_fluff', c('cloud_fluff'), 8, S, 1),
        trade('radiant_stone', c('radiant_stone'), 2, E, 1),
        trade('starquartz_for_raw', S, 2, c('raw_etherite'), 3, 16),
    ]
    rare = [
        trade('saddle', 'minecraft:saddle', 1, E, 2, 3),
        trade('fleece_for_quartz', S, 3, c('golden_fleece'), 2, 12),
        trade('golden_apple', 'minecraft:golden_apple', 1, E, 3, 4),
        trade('experience', 'minecraft:experience_bottle', 4, S, 3),
        trade('name_tag', 'minecraft:name_tag', 1, S, 4, 2),
    ]
    prof = {
        'keeper': [trade('k_parachute', c('cloud_parachute'), 2, S, 2), trade('k_bronze_key', c('bronze_key'), 1, E, 1, 3),
                   trade('k_feather', c('seraph_feather'), 1, S, 4, 6)],
        'smith': [trade('s_rune_wind', c('rune_of_wind'), 1, E, 2, 3), trade('s_rune_light', c('rune_of_light'), 1, E, 2, 3),
                  trade('s_fork', c('tuning_fork'), 1, S, 3, 2), trade('s_forge', c('celestial_forge'), 1, E, 6, 1)],
        'astronomer': [trade('a_rune_stars', c('rune_of_stars'), 1, E, 2, 3), trade('a_lens', c('sun_lens'), 1, S, 4, 3),
                       trade('a_beacon', c('sky_beacon'), 1, E, 3, 2), trade('a_prism', c('beam_prism'), 1, E, 3, 2)],
        'gardener': [trade('g_willow', c('cloud_willow_sapling'), 2, S, 1), trade('g_starpine', c('starpine_sapling'), 2, S, 1),
                     trade('g_flowers', c('sunbell'), 4, S, 1), trade('g_jelly', c('sky_jelly'), 2, S, 2)],
    }
    for name, trades in prof.items():
        write_json(os.path.join(DATA, f'tags/villager_trade/angel/{name}.json'), {'values': trades})
        write_json(os.path.join(DATA, f'trade_set/angel/{name}.json'),
                   {'amount': 3, 'random_sequence': c(f'trade_set/angel/{name}'), 'trades': f'#celestial:angel/{name}'})
    write_json(os.path.join(DATA, 'tags/villager_trade/angel/common.json'), {'values': common})
    write_json(os.path.join(DATA, 'tags/villager_trade/angel/rare.json'), {'values': rare})
    write_json(os.path.join(DATA, 'trade_set/angel/common.json'),
               {'amount': 4, 'random_sequence': c('trade_set/angel/common'), 'trades': '#celestial:angel/common'})
    write_json(os.path.join(DATA, 'trade_set/angel/rare.json'),
               {'amount': 2, 'random_sequence': c('trade_set/angel/rare'), 'trades': '#celestial:angel/rare'})


def gen_equipment():
    # звёздный лук: обычная модель + три стадии натяжения
    save_png(T.starbow(), 'item/starbow')
    with open(os.path.join(VANILLA, 'models/item/bow.json')) as f:
        bow = json.load(f)
    bow['textures'] = {'layer0': c('item/starbow')}
    bow['parent'] = 'minecraft:item/generated'
    model('item/starbow', bow)
    for st in range(3):
        save_png(T.starbow(st), f'item/starbow_pulling_{st}')
        model(f'item/starbow_pulling_{st}', {'parent': c('item/starbow'), 'textures': {'layer0': c(f'item/starbow_pulling_{st}')}})
    write_json(os.path.join(ASSETS, 'items/starbow.json'), {'model': {
        'type': 'minecraft:condition', 'property': 'minecraft:using_item',
        'on_false': {'type': 'minecraft:model', 'model': c('item/starbow')},
        'on_true': {'type': 'minecraft:range_dispatch', 'property': 'minecraft:use_duration', 'scale': 0.05,
                    'fallback': {'type': 'minecraft:model', 'model': c('item/starbow_pulling_0')},
                    'entries': [{'threshold': 0.65, 'model': {'type': 'minecraft:model', 'model': c('item/starbow_pulling_1')}},
                                {'threshold': 0.9, 'model': {'type': 'minecraft:model', 'model': c('item/starbow_pulling_2')}}]}}})
    save_png(T.star_arrow_entity(), 'entity/projectiles/star_arrow')

    # нимб: объёмное кольцо, на голове висит над макушкой (display.head)
    save_png(T.halo_texture(), 'item/halo_ring')
    ring = []
    for frm, to in (([3, 7, 3], [13, 8, 4]), ([3, 7, 12], [13, 8, 13]), ([3, 7, 4], [4, 8, 12]), ([12, 7, 4], [13, 8, 12])):
        ring.append({'from': frm, 'to': to, 'faces': {d: {'texture': '#ring', 'uv': [0, 0, 16, 1]} for d in
                                                     ('north', 'south', 'east', 'west', 'up', 'down')}})
    model('item/halo', {'textures': {'ring': c('item/halo_ring'), 'particle': c('item/halo_ring')}, 'elements': ring,
                        'gui_light': 'front',
                        'display': {
                            'head': {'translation': [0, 14.5, 0], 'scale': [1.1, 1.1, 1.1]},
                            'gui': {'rotation': [30, 45, 0], 'scale': [1.0, 1.0, 1.0]},
                            'ground': {'translation': [0, 3, 0], 'scale': [0.5, 0.5, 0.5]},
                            'fixed': {'rotation': [90, 0, 0]},
                            'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.5, 0.5, 0.5]},
                            'firstperson_righthand': {'rotation': [0, 45, 0], 'scale': [0.5, 0.5, 0.5]}}})
    item_def('halo', c('item/halo'))

    sprites = {
        'cloud_parachute': ({'1': '#c9d6e6', '2': '#ffffff', '3': '#e8b833', '4': '#8a6238'}, [
            '................',
            '.....111111.....',
            '...1122222211...',
            '..122222222221..',
            '.12222222222221.',
            '.13.3..33..3.31.',
            '..4..4....4..4..',
            '...4..4..4..4...',
            '....4..44..4....',
            '.....4.44.4.....',
            '......4444......',
            '.......33.......',
            '......3333......',
            '......3333......',
            '.......33.......',
            '................']),
        'light_spear': ({'1': '#c08f1c', '2': '#f3d27a', '3': '#ffffff', '4': '#bfe9ff'}, [
            '.............33.',
            '............3443',
            '...........34431',
            '..........3443..',
            '.........2441...',
            '........221.....',
            '.......221......',
            '......221.......',
            '.....221........',
            '....221.........',
            '...221..........',
            '..221...........',
            '.221............',
            '.21.............',
            '1...............',
            '................']),
        'seraph_feather': ({'1': '#c9b27a', '2': '#ffffff', '3': '#f3d27a'}, [
            '................',
            '...........22...',
            '..........2222..',
            '.........22222..',
            '........222232..',
            '.......2222322..',
            '......2222322...',
            '.....2222322....',
            '....2222322.....',
            '....222322......',
            '...222322.......',
            '...22322........',
            '...2132.........',
            '..1.............',
            '.1..............',
            '................']),
        'light_shard': ({'1': '#c9a23a', '2': '#fff3c6', '3': '#ffffff', '4': '#ffe08a'}, [
            '................',
            '.......1........',
            '......121.......',
            '......121.......',
            '.....12321......',
            '.....12321......',
            '....1243421.....',
            '....1233321.....',
            '...124333421....',
            '....1233321.....',
            '....1243421.....',
            '.....12321......',
            '.....12321......',
            '......121.......',
            '.......1........',
            '................']),
        'music_disc_heavenly_choir': ({'1': '#3a3446', '2': '#4d465c', '3': '#f3d27a', '4': '#ffffff'}, [
            '................',
            '.....111111.....',
            '...1122222211...',
            '..122211112221..',
            '..121133331121..',
            '.12213333331221.',
            '.12133344333121.',
            '.12133444433121.',
            '.12133444433121.',
            '.12133344333121.',
            '.12213333331221.',
            '..121133331121..',
            '..122211112221..',
            '...1122222211...',
            '.....111111.....',
            '................']),
    }
    for k, (colors, rows) in sprites.items():
        save_png(T.sprite(rows, colors), 'item/' + k)
        model('item/' + k, {'parent': 'minecraft:item/handheld' if k == 'light_spear' else 'minecraft:item/generated',
                            'textures': {'layer0': c('item/' + k)}})
        item_def(k, c('item/' + k))

    names = {
        'halo': ('Нимб', 'Halo'), 'cloud_parachute': ('Облачный парашют', 'Cloud Parachute'),
        'starbow': ('Звёздный лук', 'Starbow'), 'light_spear': ('Копьё Света', 'Spear of Light'),
        'seraph_feather': ('Перо серафима', 'Seraph Feather'),
        'light_shard': ('Осколок Света', 'Light Shard'),
        'music_disc_heavenly_choir': ('Музыкальная пластинка', 'Music Disc'),
    }
    for k, (ru, en) in names.items():
        item_name(k, ru, en)
    tr('jukebox_song.celestial.heavenly_choir', 'Celestial — Небесный хор', 'Celestial - Heavenly Choir')
    tr('entity.celestial.star_arrow', 'Звёздная стрела', 'Star Arrow')
    tr('entity.celestial.light_spear', 'Копьё Света', 'Spear of Light')
    write_json(os.path.join(DATA, 'jukebox_song/heavenly_choir.json'), {
        'comparator_output': 13, 'description': {'translate': 'jukebox_song.celestial.heavenly_choir'},
        'length_in_seconds': 106.0, 'sound_event': 'celestial:music_disc.heavenly_choir'})
    tag('item', 'minecraft:bow_enchantable', c('starbow'))
    tag('item', 'minecraft:durability_enchantable', c('starbow'), c('light_spear'), c('seraph_wings'))
    tag('item', 'minecraft:trident_enchantable', c('light_spear'))

    S, Q, F = c('etherite_ingot'), c('starquartz'), c('seraph_feather')
    shaped('cloud_parachute', c('cloud_parachute'), ['CCC', 'S S', ' L '],
           {'C': c('cloud_fluff'), 'S': 'minecraft:string', 'L': 'minecraft:leather'}, 2, 'equipment')
    shaped('starbow', c('starbow'), [' QS', 'F S', ' QS'], {'Q': Q, 'S': 'minecraft:string', 'F': F}, 1, 'equipment')
    shaped('light_spear', c('light_spear'), ['  Q', ' E ', 'E  '], {'Q': Q, 'E': S}, 1, 'equipment')


def gen_keys_and_story_blocks():
    key_rows = [
        '................',
        '................',
        '..111...........',
        '.12221..........',
        '.12.21..........',
        '.12221111111111.',
        '..11122222222221',
        '.....11111121121',
        '..........1.1.1.',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................']
    for name, ru, en, light, dark in (('bronze_key', 'Бронзовый ключ', 'Bronze Key', '#e0a15e', '#8a5a2b'),
                                      ('silver_key', 'Серебряный ключ', 'Silver Key', '#eef2f7', '#8e99a8'),
                                      ('golden_key', 'Золотой ключ', 'Golden Key', '#ffe08a', '#b9862a')):
        save_png(T.sprite(key_rows, {'1': dark, '2': light}), 'item/' + name)
        model('item/' + name, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + name)}})
        item_def(name, c('item/' + name))
        item_name(name, ru, en)

    # печать Серафима: светлый камень с выжженным знаком
    seal = T.radiant_stone()
    for x, y in [(7, 2), (8, 2), (7, 13), (8, 13), (2, 7), (2, 8), (13, 7), (13, 8)] + [(i, i) for i in range(4, 12)] + [(i, 15 - i) for i in range(4, 12)]:
        seal.putpixel((x, y), (*T.hexrgb('#8a1c1c'), 255))
    save_png(seal, 'block/seraph_seal')
    dim = seal.copy()
    for y in range(16):
        for x in range(16):
            r_, g_, b_, a_ = dim.getpixel((x, y))
            dim.putpixel((x, y), (int(r_ * 0.45), int(g_ * 0.45), int(b_ * 0.5), a_))
    save_png(dim, 'block/seraph_seal_awakened')
    simple_cube('seraph_seal')
    model('block/seraph_seal_awakened', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/seraph_seal_awakened')}})
    blockstate('seraph_seal', {'variants': {'awakened=false': {'model': c('block/seraph_seal')},
                                            'awakened=true': {'model': c('block/seraph_seal_awakened')}}})
    block_name('seraph_seal', 'Печать Серафима', 'Seraph Seal')
    # алтарь: постамент (нижняя часть шире), сверху чаша
    save_png(T.bricks('altar_side', T.SKYSTONE[2:], '#c9a23a'), 'block/celestial_altar_side')
    save_png(T.radiant_stone(), 'block/celestial_altar_top')
    variants = {}
    for f in ('false', 'true'):
        for v in ('false', 'true'):
            for l in ('false', 'true'):
                variants[f'flame={f},light={l},void={v}'] = {'model': c('block/celestial_altar' + ('_lit' if f == v == l == 'true' else ''))}
    blockstate('celestial_altar', {'variants': variants})
    model('block/celestial_altar', {'parent': 'minecraft:block/block', 'textures': {
        'particle': c('block/celestial_altar_side'), 'side': c('block/celestial_altar_side'), 'top': c('block/celestial_altar_top')},
        'elements': [
            {'from': [1, 0, 1], 'to': [15, 4, 15], 'faces': {d: {'texture': '#side'} for d in ('north', 'south', 'east', 'west', 'down')} | {'up': {'texture': '#top'}}},
            {'from': [4, 4, 4], 'to': [12, 11, 12], 'faces': {d: {'texture': '#side'} for d in ('north', 'south', 'east', 'west')}},
            {'from': [2, 11, 2], 'to': [14, 14, 14], 'faces': {d: {'texture': '#side'} for d in ('north', 'south', 'east', 'west', 'down')} | {'up': {'texture': '#top'}}}]})
    item_def('celestial_altar', c('block/celestial_altar'))
    with open(os.path.join(ASSETS, 'models/block/celestial_altar.json')) as f:
        lit = json.load(f)
    lit['textures']['top'] = c('block/seraph_seal')
    model('block/celestial_altar_lit', lit)
    journal = T.sprite([
        '................',
        '..1111111111....',
        '..1222222221....',
        '..12233332211...',
        '..12222222213...',
        '..12333333213...',
        '..12222222213...',
        '..12233322213...',
        '..12222222213...',
        '..12222442213...',
        '..12224444213...',
        '..12222442213...',
        '..1222222221 3..',
        '..11111111113...',
        '...3333333333...',
        '................'], {'1': '#5b3a1e', '2': '#e9dcb8', '3': '#c9a23a', '4': '#f3c64a'})
    save_png(journal, 'item/wanderer_journal')
    model('item/wanderer_journal', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/wanderer_journal')}})
    item_def('wanderer_journal', c('item/wanderer_journal'))
    icon = T.Image.new('RGBA', (18, 18), (0, 0, 0, 0))
    halo_icon = T.sprite([
        '................',
        '....11111111....',
        '...1222222221...',
        '...1211111121...',
        '...1222222221...',
        '....11111111....',
        '.......33.......',
        '......3443......',
        '.....344443.....',
        '....34444443....',
        '.....344443.....',
        '......3443......',
        '.......33.......',
        '................',
        '................',
        '................'], {'1': '#c9a23a', '2': '#fff3c6', '3': '#f3d27a', '4': '#ffffff'})
    icon.paste(halo_icon, (1, 1))
    path = os.path.join(ASSETS, 'textures/mob_effect/blessing.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    icon.save(path)
    block_name('celestial_altar', 'Небесный алтарь', 'Celestial Altar')
    tr('tag.item.celestial.etherite_tool_materials', 'Материалы эфиритовых инструментов', 'Etherite Tool Materials')
    tr('tag.item.celestial.repairs_etherite_armor', 'Чинит эфиритовую броню', 'Repairs Etherite Armor')
    tr('tag.item.celestial.skywood_logs', 'Брёвна небесного дерева', 'Skywood Logs')


def main():
    gen_keys_and_story_blocks()
    gen_blocks()
    gen_items()
    gen_mobs()
    gen_equipment()
    write_tags()
    T.icon().save(os.path.join(ASSETS, 'icon.png'))
    for lang, entries in LANG.items():
        write_json(os.path.join(ASSETS, 'lang', lang + '.json'), dict(sorted(entries.items())))
    print('ok:', sum(len(v) for v in LANG.values()) // 2, 'переводов')


if __name__ == '__main__':
    main()
