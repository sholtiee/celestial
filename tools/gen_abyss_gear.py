"""Снаряжение из безднового обсидиана (волна 0.3, шаг 5): осколок, слиток, инструменты, броня, рецепты, лут руды.

Формы иконок — наши эфиритовые спрайты (textures.SPR), но в своей палитре: чёрно-фиолетовый обсидиан с сиреневыми гранями.
"""
import os

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, VANILLA, c, item_def, model, ore_drop, save_png, shaped, shapeless, write_json
from gen_story import lang_patch

ABY = {'1': '#0e0818', '2': '#24123a', '3': '#40216a', '4': '#6c3fae', '5': '#b48cff', '6': '#f0e6ff'}
TOOLS = ('sword', 'pickaxe', 'axe', 'shovel', 'hoe')
ARMOR = ('helmet', 'chestplate', 'leggings', 'boots')

SPRITES = {
    'abyssal_shard': ({'1': '#0e0818', '2': '#2a1442', '3': '#5b2a8c', '4': '#b48cff'}, [
        '................',
        '................',
        '.........1......',
        '........131.....',
        '.......1341.....',
        '......13441.....',
        '.....134431.....',
        '....1344321.....',
        '...13443221.....',
        '...1342221......',
        '....132221......',
        '.....1221.......',
        '......11........',
        '................',
        '................',
        '................']),
    'abyssal_ingot': ({'1': '#0e0818', '2': '#24123a', '3': '#40216a', '4': '#6c3fae', '5': '#b48cff', '6': '#f0e6ff'}, [
        '................',
        '................',
        '................',
        '................',
        '................',
        '......11111111..',
        '.....1345543321.',
        '....13456554321.',
        '...134555443221.',
        '..1233444332221.',
        '..111111111111..',
        '................',
        '................',
        '................',
        '................',
        '................']),
}

NAMES = {
    'abyssal_shard': ('Осколок безднового обсидиана', 'Abyssal Shard'),
    'abyssal_ingot': ('Слиток безднового обсидиана', 'Abyssal Ingot'),
    'abyssal_sword': ('Бездновый меч', 'Abyssal Sword'),
    'abyssal_pickaxe': ('Бездновая кирка', 'Abyssal Pickaxe'),
    'abyssal_axe': ('Бездновый топор', 'Abyssal Axe'),
    'abyssal_shovel': ('Бездновая лопата', 'Abyssal Shovel'),
    'abyssal_hoe': ('Бездновая мотыга', 'Abyssal Hoe'),
    'abyssal_helmet': ('Бездновый шлем', 'Abyssal Helmet'),
    'abyssal_chestplate': ('Бездновый нагрудник', 'Abyssal Chestplate'),
    'abyssal_leggings': ('Бездновые поножи', 'Abyssal Leggings'),
    'abyssal_boots': ('Бездновые сапоги', 'Abyssal Boots'),
}


def main():
    # иконки
    for k, (colors, rows) in SPRITES.items():
        save_png(T.sprite(rows, colors), 'item/' + k)
    for part in TOOLS + ARMOR:
        save_png(T.sprite(T.SPR['etherite_' + part], {**ABY, **T.WOOD}), f'item/abyssal_{part}')
    for name in list(SPRITES) + [f'abyssal_{p}' for p in TOOLS + ARMOR]:
        handheld = any(name.endswith(t) for t in TOOLS)
        model('item/' + name, {'parent': 'minecraft:item/handheld' if handheld else 'minecraft:item/generated',
                               'textures': {'layer0': c('item/' + name)}})
        item_def(name, c('item/' + name))
    # слои брони на теле: только форма ванильной развёртки, рисунок — обсидиан с сиреневыми прожилками
    palette = T.pal('#0e0818', '#24123a', '#40216a', '#5b2a8c', '#8a5cd0')
    for layer in ('humanoid', 'humanoid_leggings'):
        img = T.armor_layer(os.path.join(VANILLA, f'textures/entity/equipment/{layer}/diamond.png'), palette)
        px = img.load()
        r = T.rng_for('abyssal_veins_' + layer)
        for _ in range(60):  # светлые прожилки по пластинам
            x, y = r.randrange(img.width), r.randrange(img.height)
            if px[x, y][3]:
                px[x, y] = (*T.hexrgb('#c9a8ff'), px[x, y][3])
        save_png(img, f'entity/equipment/{layer}/abyssal')
    write_json(os.path.join(ASSETS, 'equipment/abyssal.json'), {'layers': {
        'humanoid': [{'texture': c('abyssal')}], 'humanoid_leggings': [{'texture': c('abyssal')}]}})

    # теги
    append_tag('item', 'celestial:abyssal_tool_materials', [c('abyssal_ingot')])
    append_tag('item', 'celestial:repairs_abyssal_armor', [c('abyssal_ingot')])
    for t in TOOLS:
        append_tag('item', f'minecraft:{t}s', [c('abyssal_' + t)])
    for a, slot in zip(ARMOR, ('head', 'chest', 'leg', 'foot')):
        append_tag('item', f'minecraft:{slot}_armor', [c('abyssal_' + a)])
    append_tag('item', 'minecraft:trimmable_armor', [c('abyssal_' + a) for a in ARMOR])

    # руда: осколки (удача работает), шёлковое касание — сама руда
    ore_drop('abyssal_obsidian_ore', c('abyssal_shard'), 1, 2)

    # рецепты: слиток = 3 осколка + звёздная сталь; нагрудник и шлем требуют хитин Глубинного червя
    shapeless('abyssal_ingot', c('abyssal_ingot'), [c('abyssal_shard')] * 3 + [c('starsteel_ingot')], 1, 'misc')
    X, S, C = '#celestial:abyssal_tool_materials', 'minecraft:stick', c('worm_chitin')
    shaped('abyssal_sword', c('abyssal_sword'), ['X', 'X', '#'], {'X': X, '#': S}, 1, 'equipment')
    shaped('abyssal_pickaxe', c('abyssal_pickaxe'), ['XXX', ' # ', ' # '], {'X': X, '#': S}, 1, 'equipment')
    shaped('abyssal_axe', c('abyssal_axe'), ['XX', 'X#', ' #'], {'X': X, '#': S}, 1, 'equipment')
    shaped('abyssal_shovel', c('abyssal_shovel'), ['X', '#', '#'], {'X': X, '#': S}, 1, 'equipment')
    shaped('abyssal_hoe', c('abyssal_hoe'), ['XX', ' #', ' #'], {'X': X, '#': S}, 1, 'equipment')
    I = c('abyssal_ingot')
    shaped('abyssal_helmet', c('abyssal_helmet'), ['XCX', 'X X'], {'X': I, 'C': C}, 1, 'equipment')
    shaped('abyssal_chestplate', c('abyssal_chestplate'), ['X X', 'XCX', 'XXX'], {'X': I, 'C': C}, 1, 'equipment')
    shaped('abyssal_leggings', c('abyssal_leggings'), ['XXX', 'X X', 'X X'], {'X': I}, 1, 'equipment')
    shaped('abyssal_boots', c('abyssal_boots'), ['X X', 'X X'], {'X': I}, 1, 'equipment')

    lang_patch({**{f'item.celestial.{k}': v for k, v in NAMES.items()},
                'codex.celestial.guide.13': ('Бездновый обсидиан: руда у пола Бездны (нужна алмазная кирка), 3 осколка + звёздная сталь = слиток. '
                                             'Полный комплект вдвое замедляет страх и снимает пульсы Тьмы.',
                                             'Abyssal obsidian: ore near the Abyss floor (diamond pickaxe), 3 shards + starsteel = ingot. '
                                             'The full set halves fear and stops the Darkness pulses.')})
    print('ok: снаряжение Бездны')


if __name__ == '__main__':
    main()
