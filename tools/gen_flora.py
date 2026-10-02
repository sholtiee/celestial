#!/usr/bin/env python3
"""Флора Рая 0.2: цветы, травы, облачный мох, светолиана, кристальный блок, облачная ива и звёздная сосна.

Запуск: python3 tools/gen_flora.py (после gen_assets.py — дописывает переводы, теги, лут).
Золотая трава, пучки и высокая трава теперь окрашиваются цветом травы биома (tintindex).
"""
import json
import math
import os

from PIL import Image

import textures as T
from gen_assets import (ASSETS, DATA, VANILLA, blockstate, c, item_def, leaves_drop, model, save_png, self_drop,
                        shaped, tag, write_json, write_tags, TAGS)
from gen_story import lang_patch

GOLD = '#f0c94a'  # цвет травы в руке (в мире — из биома)


def gray(img):
    """Переводит текстуру в светлые оттенки серого — цвет придёт из биома."""
    out = Image.new('RGBA', img.size)
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = img.getpixel((x, y))
            v = int((r * 0.3 + g * 0.59 + b * 0.11) * 1.15)
            out.putpixel((x, y), (min(255, v), min(255, v), min(255, v), a))
    return out


def blades(name, height, density=0.55):
    r = T.rng_for(name)
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for x in range(1, 15):
        if r.random() > density:
            continue
        h = r.randint(height // 2, height)
        lean = r.choice([-1, 0, 0, 1])
        for i in range(h):
            y = 15 - i
            xx = min(15, max(0, x + (lean if i > h * 0.6 else 0)))
            v = 150 + int(90 * i / h) + r.randint(-10, 10)
            img.putpixel((xx, y), (v, v, v, 255))
    return img


def flower(petal, center, stem='#6f9a3a', shape='round'):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    p, cc, s = T.hexrgb(petal), T.hexrgb(center), T.hexrgb(stem)
    for y in range(8, 16):
        img.putpixel((8, y), (*s, 255))
    img.putpixel((7, 12), (*s, 255)); img.putpixel((6, 11), (*s, 255))
    img.putpixel((9, 13), (*s, 255)); img.putpixel((10, 12), (*s, 255))
    cx, cy = 8, 5
    if shape == 'round':
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            img.putpixel((cx + dx, cy + dy), (*p, 255))
    elif shape == 'bell':
        for y in range(3, 8):
            w = (y - 2) // 2
            for x in range(cx - w, cx + w + 1):
                img.putpixel((x, y), (*p, 255))
        img.putpixel((cx, 8), (*cc, 255))
    elif shape == 'star':
        for i in range(-3, 4):
            img.putpixel((cx + i, cy), (*p, 255)); img.putpixel((cx, cy + i), (*p, 255))
        for i in (-1, 1):
            img.putpixel((cx + i, cy + i), (*p, 255)); img.putpixel((cx + i, cy - i), (*p, 255))
    elif shape == 'tall':
        for y in range(1, 8):
            for x in (cx - 1, cx, cx + 1):
                if (x + y) % 2 == 0 or x == cx:
                    img.putpixel((x, y), (*p, 255))
    img.putpixel((cx, cy), (*cc, 255))
    return img


def lumivine(tip):
    r = T.rng_for('lumivine' + str(tip))
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    vine, glow = T.hexrgb('#4f8fb8'), T.hexrgb('#bff6ff')
    for x in (6, 9):
        for y in range(16 if not tip else 9):
            img.putpixel((x + (1 if (y // 4) % 2 else 0), y), (*vine, 255))
    for _ in range(6 if not tip else 3):
        img.putpixel((r.randrange(4, 12), r.randrange(0, 14)), (*glow, 255))
    if tip:
        for y in range(9, 15):
            w = 2 if 10 <= y <= 13 else 1
            for x in range(8 - w, 8 + w + 1):
                img.putpixel((x, y), (*glow, 255))
    return img


def leaves(name, palette, holes, sparkle=None):
    r = T.rng_for(name)
    img = T.noisy(name, palette, cell=2, grain=0.6)
    for y in range(16):
        for x in range(16):
            if r.random() < holes:
                img.putpixel((x, y), (0, 0, 0, 0))
            elif sparkle and r.random() < 0.05:
                img.putpixel((x, y), (*T.hexrgb(sparkle), 255))
    return img


def sapling(leaf, leaf2):
    rows = [
        '................',
        '................',
        '......LL........',
        '.....LllL.......',
        '....LlllLL......',
        '.....LlllL......',
        '...LL.LsL.LL....',
        '..LllL.s.LllL...',
        '...LlllsLlll....',
        '......lsl.......',
        '.......s........',
        '.......s........',
        '.......s........',
        '.......s........',
        '.......s........',
        '................']
    return T.sprite(rows, {'L': leaf2, 'l': leaf, 's': '#d8c9a8'})


def crystal_block():
    img = T.noisy('sky_crystal_block', [T.hexrgb(h) for h in ('#3b82c4', '#60a5e8', '#93c5fd', '#dbeafe')], cell=4, grain=0.3)
    for i in range(16):
        img.putpixel((i, (i * 3) % 16), (*T.hexrgb('#ffffff'), 255))
    return img


FLOWERS = {
    'sky_lily': ('Небесная лилия', 'Sky Lily', flower('#ffffff', '#f3c64a', shape='round')),
    'sunbell': ('Солнечный колокольчик', 'Sunbell', flower('#ffd64a', '#fff6c8', shape='bell')),
    'cloudbloom': ('Облакоцвет', 'Cloudbloom', flower('#e6eef8', '#9db4d6', shape='round')),
    'starflower': ('Звездоцвет', 'Starflower', flower('#bfe9ff', '#ffffff', shape='star')),
    'aether_rose': ('Эфирная роза', 'Aether Rose', flower('#52d3e3', '#1f8fa8', shape='round')),
    'dawn_poppy': ('Зорянка', 'Dawn Poppy', flower('#ff9a6b', '#ffe08a', shape='tall')),
}


def golden_grass_tinted():
    """Золотая трава: верх и «бахрома» сбоку — серые с tintindex, цвет берётся из биома."""
    save_png(gray(T.golden_grass_top()), 'block/golden_grass_top')
    side = T.dirt()
    overlay = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = T.rng_for('golden_grass_overlay')
    top = gray(T.golden_grass_top())
    for x in range(16):
        depth = 3 + r.choice([0, 0, 1, 1, 2])
        for y in range(depth):
            overlay.putpixel((x, y), top.getpixel((x, y)))
            side.putpixel((x, y), (0, 0, 0, 0))
    save_png(side, 'block/golden_grass_side')
    save_png(overlay, 'block/golden_grass_side_overlay')
    with open(os.path.join(VANILLA, 'models/block/grass_block.json')) as f:
        m = json.load(f)
    m['textures'] = {'particle': c('block/heaven_dirt'), 'bottom': c('block/heaven_dirt'), 'top': c('block/golden_grass_top'),
                     'side': c('block/golden_grass_side'), 'overlay': c('block/golden_grass_side_overlay')}
    model('block/golden_grass', m)
    write_json(os.path.join(ASSETS, 'items/golden_grass.json'), {'model': {
        'type': 'minecraft:model', 'model': c('block/golden_grass'), 'tints': [{'type': 'minecraft:constant', 'value': rgb_int(GOLD)}]}})


def rgb_int(h):
    r, g, b = T.hexrgb(h)
    return -16777216 | (r << 16) | (g << 8) | b


def cross_block(name, texture_name=None, tinted=False, item_tint=None):
    tex = c('block/' + (texture_name or name))
    blockstate(name, {'variants': {'': {'model': c('block/' + name)}}})
    model('block/' + name, {'parent': 'minecraft:block/tinted_cross' if tinted else 'minecraft:block/cross', 'textures': {'cross': tex}})
    model('item/' + name, {'parent': 'minecraft:item/generated', 'textures': {'layer0': tex}})
    item = {'type': 'minecraft:model', 'model': c('item/' + name)}
    if item_tint:
        item['tints'] = [{'type': 'minecraft:constant', 'value': rgb_int(item_tint)}]
    write_json(os.path.join(ASSETS, 'items', name + '.json'), {'model': item})


def main():
    names = {}
    golden_grass_tinted()

    for name, (ru, en, img) in FLOWERS.items():
        save_png(img, 'block/' + name)
        cross_block(name)
        self_drop(name)
        names[f'block.celestial.{name}'] = (ru, en)
        tag('block', 'minecraft:small_flowers', c(name))
        tag('item', 'minecraft:small_flowers', c(name))

    save_png(blades('golden_tuft', 11), 'block/golden_tuft')
    cross_block('golden_tuft', tinted=True, item_tint=GOLD)
    save_png(blades('tall_golden_grass_bottom', 16, 0.75), 'block/tall_golden_grass_bottom')
    save_png(blades('tall_golden_grass_top', 13, 0.6), 'block/tall_golden_grass_top')
    blockstate('tall_golden_grass', {'variants': {'half=lower': {'model': c('block/tall_golden_grass_bottom')},
                                                  'half=upper': {'model': c('block/tall_golden_grass_top')}}})
    for half in ('bottom', 'top'):
        model(f'block/tall_golden_grass_{half}', {'parent': 'minecraft:block/tinted_cross', 'textures': {'cross': c(f'block/tall_golden_grass_{half}')}})
    model('item/tall_golden_grass', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/tall_golden_grass_top')}})
    write_json(os.path.join(ASSETS, 'items/tall_golden_grass.json'), {'model': {
        'type': 'minecraft:model', 'model': c('item/tall_golden_grass'), 'tints': [{'type': 'minecraft:constant', 'value': rgb_int(GOLD)}]}})
    names['block.celestial.golden_tuft'] = ('Золотой пучок', 'Golden Tuft')
    names['block.celestial.tall_golden_grass'] = ('Высокая золотая трава', 'Tall Golden Grass')
    for n in ('golden_tuft', 'tall_golden_grass'):
        write_json(os.path.join(DATA, 'loot_table/blocks', n + '.json'), {
            'type': 'minecraft:block', 'pools': [{'rolls': 1, 'entries': [{'type': 'minecraft:alternatives', 'children': [
                {'type': 'minecraft:item', 'condition': 'minecraft:tool/can_shear', 'name': c('golden_tuft')},
                {'type': 'minecraft:item', 'condition': {'type': 'minecraft:random_chance', 'chance': 0.1}, 'name': c('manna_berries')}]}]}],
            'random_sequence': c('blocks/' + n)})
        tag('block', 'minecraft:replaceable_by_trees', c(n))
        tag('block', 'minecraft:sword_efficient', c(n))

    save_png(T.cloud('cloud_moss', T.CLOUD, 255), 'block/cloud_moss')
    blockstate('cloud_moss', {'variants': {'': {'model': c('block/cloud_moss')}}})
    model('block/cloud_moss', {'parent': 'minecraft:block/carpet', 'textures': {'wool': c('block/cloud_moss')}})
    item_def('cloud_moss', c('block/cloud_moss'))
    self_drop('cloud_moss')
    names['block.celestial.cloud_moss'] = ('Облачный мох', 'Cloud Moss')
    shaped('cloud_moss', c('cloud_moss'), ['##'], {'#': c('cloud')}, 3, 'building')

    save_png(lumivine(False), 'block/lumivine')
    save_png(lumivine(True), 'block/lumivine_tip')
    blockstate('lumivine', {'variants': {'tip=false': {'model': c('block/lumivine')}, 'tip=true': {'model': c('block/lumivine_tip')}}})
    model('block/lumivine', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/lumivine')}})
    model('block/lumivine_tip', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/lumivine_tip')}})
    model('item/lumivine', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/lumivine_tip')}})
    item_def('lumivine', c('item/lumivine'))
    write_json(os.path.join(DATA, 'loot_table/blocks/lumivine.json'), {'type': 'minecraft:block', 'pools': [{'rolls': 1, 'entries': [
        {'type': 'minecraft:item', 'condition': 'minecraft:tool/can_shear', 'name': c('lumivine')}]}], 'random_sequence': c('blocks/lumivine')})
    names['block.celestial.lumivine'] = ('Светолиана', 'Lumivine')

    save_png(crystal_block(), 'block/sky_crystal_block')
    blockstate('sky_crystal_block', {'variants': {'': {'model': c('block/sky_crystal_block')}}})
    model('block/sky_crystal_block', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/sky_crystal_block')}})
    item_def('sky_crystal_block', c('block/sky_crystal_block'))
    self_drop('sky_crystal_block')
    tag('block', 'minecraft:mineable/pickaxe', c('sky_crystal_block'))
    names['block.celestial.sky_crystal_block'] = ('Блок небесного кристалла', 'Sky Crystal Block')

    for tree, leaf_name, ru_leaves, en_leaves, ru_sap, en_sap, pal, holes, sparkle, sap_colors in (
            ('cloud_willow', 'cloud_willow_leaves', 'Листва облачной ивы', 'Cloud Willow Leaves', 'Саженец облачной ивы',
             'Cloud Willow Sapling', ('#cfd9e6', '#e0e8f2', '#eef3fa', '#ffffff'), 0.18, None, ('#e0e8f2', '#ffffff')),
            ('starpine', 'starpine_leaves', 'Хвоя звёздной сосны', 'Starpine Needles', 'Саженец звёздной сосны',
             'Starpine Sapling', ('#1e2f6b', '#2a4190', '#3a55b0', '#4d6bd0'), 0.08, '#ffe08a', ('#2a4190', '#4d6bd0'))):
        save_png(leaves(leaf_name, [T.hexrgb(h) for h in pal], holes, sparkle), 'block/' + leaf_name)
        blockstate(leaf_name, {'variants': {'': {'model': c('block/' + leaf_name)}}})
        model('block/' + leaf_name, {'parent': 'minecraft:block/leaves', 'textures': {'all': c('block/' + leaf_name)}})
        item_def(leaf_name, c('block/' + leaf_name))
        sap = tree + '_sapling'
        save_png(sapling(*sap_colors), 'block/' + sap)
        cross_block(sap)
        self_drop(sap)
        leaves_drop(leaf_name, c(sap))
        names[f'block.celestial.{leaf_name}'] = (ru_leaves, en_leaves)
        names[f'block.celestial.{sap}'] = (ru_sap, en_sap)
        tag('block', 'minecraft:leaves', c(leaf_name)); tag('item', 'minecraft:leaves', c(leaf_name))
        tag('block', 'minecraft:mineable/hoe', c(leaf_name))
        tag('block', 'minecraft:saplings', c(sap)); tag('item', 'minecraft:saplings', c(sap))

    # теги пишет gen_assets целиком; здесь дописываем только новые значения к существующим файлам
    for (kind, name), values in TAGS.items():
        ns, path = name.split(':')
        base = os.path.join(DATA if ns == 'celestial' else DATA.replace('celestial', 'minecraft'), 'tags', kind, path + '.json')
        existing = []
        if os.path.exists(base):
            with open(base) as f:
                existing = json.load(f)['values']
        write_json(base, {'replace': False, 'values': list(dict.fromkeys(existing + values))})
    lang_patch(names)
    print('ok: флора', len(names), 'названий')


if __name__ == '__main__':
    main()
