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

    # --- названия
    names = {
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
    shaped('radiant_stone', c('radiant_stone'), ['GSG', 'QBQ', 'GSG'],
           {'G': 'minecraft:glowstone_dust', 'S': c('skystone'), 'Q': c('starquartz'), 'B': 'minecraft:gold_block'}, 4, 'building')
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


def main():
    gen_blocks()
    gen_items()
    write_tags()
    T.icon().save(os.path.join(ASSETS, 'icon.png'))
    for lang, entries in LANG.items():
        write_json(os.path.join(ASSETS, 'lang', lang + '.json'), dict(sorted(entries.items())))
    print('ok:', sum(len(v) for v in LANG.values()) // 2, 'переводов')


if __name__ == '__main__':
    main()
