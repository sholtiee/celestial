#!/usr/bin/env python3
"""Светотехника и загадки: текстуры, модели (с поворотами по blockstate), рецепты, лут, тексты загадок.

Запуск: python3 tools/gen_mechanics.py (после gen_assets.py).
"""
import json
import math
import os

from PIL import Image

import textures as T
from gen_assets import (ASSETS, DATA, blockstate, c, item_def, model, save_png, self_drop, shaped, shapeless, write_json, TAGS, tag)
from gen_story import lang_patch

FACING_ROT = {  # поворот модели «смотрит на север» под FACING
    'north': {}, 'south': {'y': 180}, 'east': {'y': 90}, 'west': {'y': 270},
    'up': {'x': 270}, 'down': {'x': 90},
}


def frame_texture(name, inner, rim='#c9a23a', glow=None):
    r = T.rng_for(name)
    img = Image.new('RGBA', (16, 16))
    rim_c, inner_c = T.hexrgb(rim), T.hexrgb(inner)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            if edge:
                img.putpixel((x, y), (*T.shade(rim_c, 0.85 + r.random() * 0.2), 255))
            else:
                d = math.hypot(x - 7.5, y - 7.5)
                c = T.mix(T.hexrgb(glow), inner_c, min(1, d / 6)) if glow else inner_c
                img.putpixel((x, y), (*T.shade(c, 0.9 + r.random() * 0.15), 255))
    return img


def side_texture(name, base='#b7b2a6'):
    return T.bricks(name, [T.hexrgb(h) for h in ('#cfd6e0', '#dce2ea', '#e7ecf2')], '#c9a23a')


def glass(color, alpha=150):
    img = Image.new('RGBA', (16, 16))
    c_ = T.hexrgb(color)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            img.putpixel((x, y), (*T.shade(c_, 0.7), 230) if edge else (*c_, alpha if (x + y) % 5 else alpha + 50))
    return img


def facing_block(name, front, side, states_extra=None, facing_values=('north', 'south', 'east', 'west', 'up', 'down')):
    """Блок с лицевой стороной: front_<суффикс> по состояниям."""
    variants = {}
    for f in facing_values:
        for suffix, props in (states_extra or {'': ''}).items():
            key = f'facing={f}' + (',' + props if props else '')
            variants[key] = {'model': c(f'block/{name}{suffix}'), **FACING_ROT[f]}
    blockstate(name, {'variants': variants})


def main():
    names = {}

    # --- источники луча: линза и фонарь (facing × active)
    for name, glow in (('sun_lens', '#fff3b0'), ('beam_lantern', '#ffd6a8')):
        save_png(frame_texture(name + '_front', '#5f6b88', glow=None), f'block/{name}_front')
        save_png(frame_texture(name + '_front_on', '#fff6d8', glow=glow), f'block/{name}_front_on')
        save_png(side_texture(name + '_side'), f'block/{name}_side')
        for suffix, front in (('', f'block/{name}_front'), ('_on', f'block/{name}_front_on')):
            model(f'block/{name}{suffix}', {'parent': 'minecraft:block/orientable_with_bottom', 'textures': {
                'front': c(front), 'side': c(f'block/{name}_side'), 'top': c(f'block/{name}_side'), 'bottom': c(f'block/{name}_side')}})
        facing_block(name, None, None, {'': 'active=false', '_on': 'active=true'})
        item_def(name, c(f'block/{name}_on'))
        self_drop(name)
    names['block.celestial.sun_lens'] = ('Солнечная линза', 'Sun Lens')
    names['block.celestial.beam_lantern'] = ('Световой фонарь', 'Beam Lantern')

    # --- зеркало: диагональная пластина (элемент, повёрнутый на 45°)
    save_png(glass('#dfe9f5', 210), 'block/beam_mirror')
    save_png(side_texture('mirror_base'), 'block/beam_mirror_base')
    mirror_model = {'textures': {'mirror': c('block/beam_mirror'), 'base': c('block/beam_mirror_base'), 'particle': c('block/beam_mirror')},
                    'elements': [
                        {'from': [0, 0, 0], 'to': [16, 2, 16], 'faces': {d: {'texture': '#base'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
                        {'from': [7.5, 2, 0], 'to': [8.5, 16, 16], 'rotation': {'origin': [8, 8, 8], 'axis': 'y', 'angle': 45, 'rescale': True},
                         'faces': {d: {'texture': '#mirror', 'uv': [0, 0, 16, 16] if d in ('east', 'west') else [7, 0, 9, 16]}
                                   for d in ('east', 'west', 'north', 'south', 'up')}}]}
    model('block/beam_mirror', mirror_model)
    blockstate('beam_mirror', {'variants': {'flipped=false': {'model': c('block/beam_mirror')},
                                            'flipped=true': {'model': c('block/beam_mirror'), 'y': 90}}})
    item_def('beam_mirror', c('block/beam_mirror'))
    self_drop('beam_mirror')
    names['block.celestial.beam_mirror'] = ('Зеркало света', 'Light Mirror')

    # --- призма и фильтры (полупрозрачные)
    prism = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            hue = (x + y) / 30
            r_ = int(200 + 55 * math.sin(hue * 6.28)); g_ = int(200 + 55 * math.sin(hue * 6.28 + 2)); b_ = int(200 + 55 * math.sin(hue * 6.28 + 4))
            prism.putpixel((x, y), (min(255, r_), min(255, g_), min(255, b_), 200 if 0 < x < 15 and 0 < y < 15 else 255))
    save_png(prism, 'block/beam_prism')
    for name, color, ru, en in (('beam_prism', None, 'Призма', 'Prism'), ('red_filter', '#ff5a4a', 'Красный фильтр', 'Red Filter'),
                                ('green_filter', '#6cff7a', 'Зелёный фильтр', 'Green Filter'), ('blue_filter', '#5aa8ff', 'Синий фильтр', 'Blue Filter')):
        if color:
            save_png(glass(color), f'block/{name}')
        blockstate(name, {'variants': {'': {'model': c(f'block/{name}')}}})
        model(f'block/{name}', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c(f'block/{name}')}})
        item_def(name, c(f'block/{name}'))
        self_drop(name)
        names[f'block.celestial.{name}'] = (ru, en)

    # --- перископ (facing × up)
    save_png(frame_texture('periscope_front', '#dfe9f5', rim='#9aa6b8'), 'block/periscope_front')
    save_png(side_texture('periscope_side'), 'block/periscope_side')
    save_png(frame_texture('periscope_top', '#fff6d8', rim='#9aa6b8'), 'block/periscope_top')
    for suffix, top in (('_up', 'block/periscope_top'), ('_down', 'block/periscope_side')):
        model(f'block/periscope{suffix}', {'parent': 'minecraft:block/orientable_with_bottom', 'textures': {
            'front': c('block/periscope_front'), 'side': c('block/periscope_side'),
            'top': c(top), 'bottom': c('block/periscope_top' if suffix == '_down' else 'block/periscope_side')}})
    variants = {}
    for f in ('north', 'south', 'east', 'west'):
        for up in ('true', 'false'):
            variants[f'facing={f},up={up}'] = {'model': c('block/periscope_up' if up == 'true' else 'block/periscope_down'), **FACING_ROT[f]}
    blockstate('periscope', {'variants': variants})
    item_def('periscope', c('block/periscope_up'))
    self_drop('periscope')
    names['block.celestial.periscope'] = ('Перископ', 'Periscope')

    # --- приёмник света (color × powered)
    colors = {'white': '#fff6d8', 'red': '#ff5a4a', 'green': '#6cff7a', 'blue': '#5aa8ff'}
    variants = {}
    for col, hexc in colors.items():
        for powered in ('false', 'true'):
            tex = f'light_receiver_{col}' + ('_on' if powered == 'true' else '')
            dim = '#%02x%02x%02x' % T.mix(T.hexrgb(hexc), T.hexrgb('#3a3446'), 0.6)
            save_png(frame_texture(tex, hexc if powered == 'true' else dim, glow='#ffffff' if powered == 'true' else None), 'block/' + tex)
            model('block/' + tex, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + tex)}})
            variants[f'color={col},powered={powered}'] = {'model': c('block/' + tex)}
    blockstate('light_receiver', {'variants': variants})
    item_def('light_receiver', c('block/light_receiver_white'))
    self_drop('light_receiver')
    names['block.celestial.light_receiver'] = ('Приёмник света', 'Light Receiver')

    # --- печать-дверь
    door = T.radiant_stone()
    for i in range(3, 13):
        door.putpixel((i, 3), (*T.hexrgb('#8a5a1e'), 255)); door.putpixel((i, 12), (*T.hexrgb('#8a5a1e'), 255))
        door.putpixel((3, i), (*T.hexrgb('#8a5a1e'), 255)); door.putpixel((12, i), (*T.hexrgb('#8a5a1e'), 255))
    door.putpixel((7, 7), (*T.hexrgb('#ffffff'), 255)); door.putpixel((8, 8), (*T.hexrgb('#ffffff'), 255))
    save_png(door, 'block/sealed_door')
    blockstate('sealed_door', {'variants': {'': {'model': c('block/sealed_door')}}})
    model('block/sealed_door', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/sealed_door')}})
    item_def('sealed_door', c('block/sealed_door'))
    names['block.celestial.sealed_door'] = ('Печать-дверь', 'Sealed Door')

    # --- колокол (5 нот — разный цвет пояска)
    note_colors = ['#ff6b6b', '#ffb36b', '#ffe66b', '#6bffb3', '#6bb3ff']
    variants = {}
    for n, band in enumerate(note_colors):
        tex = Image.new('RGBA', (16, 16))
        for y in range(16):
            for x in range(16):
                base = T.hexrgb('#e8b84a') if y not in (10, 11) else T.hexrgb(band)
                tex.putpixel((x, y), (*T.shade(base, 0.85 + 0.15 * math.sin(x * 0.7)), 255))
        save_png(tex, f'block/sky_bell_{n}')
        model(f'block/sky_bell_{n}', {'textures': {'bell': c(f'block/sky_bell_{n}'), 'particle': c(f'block/sky_bell_{n}')}, 'elements': [
            {'from': [3, 2, 3], 'to': [13, 4, 13], 'faces': {d: {'texture': '#bell'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
            {'from': [4, 4, 4], 'to': [12, 12, 12], 'faces': {d: {'texture': '#bell'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
            {'from': [6, 12, 6], 'to': [10, 15, 10], 'faces': {d: {'texture': '#bell'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}}]})
        variants[f'note={n}'] = {'model': c(f'block/sky_bell_{n}')}
    blockstate('sky_bell', {'variants': variants})
    item_def('sky_bell', c('block/sky_bell_2'))
    write_json(os.path.join(DATA, 'loot_table/blocks/sky_bell.json'), {'type': 'minecraft:block', 'pools': [
        {'rolls': 1, 'condition': {'type': 'minecraft:survives_explosion'}, 'entries': [{'type': 'minecraft:item', 'name': c('sky_bell')}]}],
        'random_sequence': c('blocks/sky_bell')})
    names['block.celestial.sky_bell'] = ('Небесный колокол', 'Sky Bell')

    # --- колокольный алтарь, рунный пьедестал, плитка-звезда
    for name, base_tex, ru, en, prop, extra in (
            ('bell_altar', 'sky_bell_2', 'Колокольный алтарь', 'Bell Altar', 'solved', None),
            ('rune_pedestal', 'radiant_stone', 'Рунный пьедестал', 'Rune Pedestal', 'solved', 'riddle'),
            ('star_tile', None, 'Плитка-звезда', 'Star Tile', None, None)):
        names[f'block.celestial.{name}'] = (ru, en)
    with open(os.path.join(ASSETS, 'models/block/celestial_altar.json')) as f:
        altar = json.load(f)
    for solved in ('false', 'true'):
        m = json.loads(json.dumps(altar))
        m['textures']['top'] = c('block/sky_bell_4' if solved == 'true' else 'block/sky_bell_2')
        model(f'block/bell_altar{"_solved" if solved == "true" else ""}', m)
        m2 = json.loads(json.dumps(altar))
        m2['textures']['top'] = c('block/seraph_seal' if solved == 'true' else 'block/radiant_stone')
        model(f'block/rune_pedestal{"_solved" if solved == "true" else ""}', m2)
    blockstate('bell_altar', {'variants': {'solved=false': {'model': c('block/bell_altar')}, 'solved=true': {'model': c('block/bell_altar_solved')}}})
    blockstate('rune_pedestal', {'variants': {f'riddle={i},solved={s}': {'model': c('block/rune_pedestal' + ('_solved' if s == 'true' else ''))}
                                              for i in range(8) for s in ('false', 'true')}})
    item_def('bell_altar', c('block/bell_altar'))
    item_def('rune_pedestal', c('block/rune_pedestal'))
    tile_variants = {}
    for lit in ('false', 'true'):
        for solved in ('false', 'true'):
            tex_name = 'star_tile' + ('_lit' if lit == 'true' else '') + ('_solved' if solved == 'true' else '')
            img = Image.new('RGBA', (16, 16))
            base = '#ffe08a' if solved == 'true' else ('#bfe9ff' if lit == 'true' else '#2a3150')
            for y in range(16):
                for x in range(16):
                    edge = x in (0, 15) or y in (0, 15)
                    star = (x in (7, 8) and 3 <= y <= 12) or (y in (7, 8) and 3 <= x <= 12) or abs(x - y) <= 0 and 4 <= x <= 11
                    col = T.hexrgb('#141a30') if edge else (T.hexrgb('#ffffff') if star and lit == 'true' else T.hexrgb(base))
                    img.putpixel((x, y), (*col, 255))
            save_png(img, 'block/' + tex_name)
            model('block/' + tex_name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + tex_name)}})
            tile_variants[f'lit={lit},solved={solved}'] = {'model': c('block/' + tex_name)}
    blockstate('star_tile', {'variants': tile_variants})
    item_def('star_tile', c('block/star_tile'))

    # --- Камертон
    fork = T.sprite([
        '................', '...11.....11....', '...12.....21....', '...12.....21....', '...12.....21....', '...12.....21....',
        '...122...221....', '....1222221.....', '......121.......', '......121.......', '......121.......', '......131.......',
        '.....13331......', '.....13331......', '......111.......', '................'], {'1': '#8e99a8', '2': '#eef2f7', '3': '#c9a23a'})
    save_png(fork, 'item/tuning_fork')
    model('item/tuning_fork', {'parent': 'minecraft:item/handheld', 'textures': {'layer0': c('item/tuning_fork')}})
    item_def('tuning_fork', c('item/tuning_fork'))
    names['item.celestial.tuning_fork'] = ('Камертон', 'Tuning Fork')
    names['item.celestial.tuning_fork.lore1'] = ('ПКМ по линзе, зеркалу, перископу или приёмнику — повернуть / сменить цвет',
                                                 'Right-click a lens, mirror, periscope or receiver to rotate / recolor')

    for n in ('sun_lens', 'beam_lantern', 'beam_mirror', 'beam_prism', 'periscope', 'light_receiver', 'sky_bell', 'red_filter', 'green_filter', 'blue_filter'):
        tag('block', 'minecraft:mineable/pickaxe', c(n))

    # --- рецепты
    Q, G = c('starquartz'), 'minecraft:gold_ingot'
    shaped('sun_lens', c('sun_lens'), ['GQG', 'QLQ', 'GQG'], {'G': G, 'Q': Q, 'L': 'minecraft:glass'}, 1, 'redstone')
    shapeless('beam_lantern', c('beam_lantern'), [c('sun_lens'), 'minecraft:redstone_torch'], 1, 'redstone')
    shaped('beam_mirror', c('beam_mirror'), ['LI', 'IL'], {'L': 'minecraft:glass', 'I': 'minecraft:iron_ingot'}, 2, 'redstone')
    shaped('beam_prism', c('beam_prism'), ['LQL', 'QDQ', 'LQL'], {'L': 'minecraft:glass', 'Q': Q, 'D': 'minecraft:diamond'}, 1, 'redstone')
    for col, dye in (('red', 'minecraft:red_dye'), ('green', 'minecraft:lime_dye'), ('blue', 'minecraft:light_blue_dye')):
        shapeless(f'{col}_filter', c(f'{col}_filter'), ['minecraft:glass', dye, Q], 2, 'redstone')
    shaped('periscope', c('periscope'), ['I', 'M', 'I'], {'I': 'minecraft:iron_ingot', 'M': c('beam_mirror')}, 1, 'redstone')
    shaped('light_receiver', c('light_receiver'), ['GQG', 'QRQ', 'GQG'], {'G': G, 'Q': Q, 'R': 'minecraft:redstone_block'}, 1, 'redstone')
    shaped('sky_bell', c('sky_bell'), [' G ', 'GQG', 'G G'], {'G': G, 'Q': Q}, 1, 'redstone')
    shaped('tuning_fork', c('tuning_fork'), ['I I', ' I ', ' Q '], {'I': 'minecraft:iron_ingot', 'Q': Q}, 1, 'equipment')

    # --- тексты загадок
    riddles = [
        ('Падаю, но не разбиваюсь. Лечу, но крыльев у меня нет. Что я?', 'I fall but never break. I fly but have no wings. What am I?'),
        ('Мягче пуха, белее снега, держит тех, кто ходит по небу.', 'Softer than down, whiter than snow, it holds those who walk the sky.'),
        ('Без ног иду, без рук указываю, без глаз знаю, когда ночь.', 'Without legs I walk, without hands I point, without eyes I know the night.'),
        ('Рождена во тьме Ада, но несу свет.', 'Born in the darkness of the Nether, yet I carry light.'),
        ('Пища, что падает с неба.', 'Food that falls from the sky.'),
        ('Всегда смотрю в одну сторону, куда бы ты ни шёл.', 'I always look one way, wherever you go.'),
        ('Я — голос глубин, что повторяет за тобой.', 'I am the voice of the deep that repeats after you.'),
        ('Упал с неба, но не дождь. Светит, но не огонь.', 'Fell from the sky, but not rain. Shines, but not fire.'),
    ]
    for i, (ru, en) in enumerate(riddles):
        names[f'puzzle.celestial.riddle.{i}'] = ('§6Руны гласят: §f' + ru, '§6The runes read: §f' + en)
    names.update({
        'puzzle.celestial.riddle.solved': ('§aЗагадка разгадана — руны спокойно светятся.', '§aThe riddle is solved - the runes glow calmly.'),
        'puzzle.celestial.riddle.wrong': ('Руны остаются тёмными…', 'The runes stay dark...'),
        'puzzle.celestial.bells.listen': ('Слушай мелодию и повтори её на колоколах', 'Listen to the melody and repeat it on the bells'),
        'puzzle.celestial.bells.wrong': ('Фальшивая нота! Начни сначала', 'A false note! Start again'),
        'puzzle.celestial.bells.already': ('Колокола уже поют в унисон', 'The bells already sing in unison'),
        'puzzle.celestial.solved': ('✦ Загадка решена! +1 Благодать', '✦ Puzzle solved! +1 Grace'),
    })

    # теги дописываем к существующим файлам
    for (kind, name), values in TAGS.items():
        ns, path = name.split(':')
        base = os.path.join(DATA if ns == 'celestial' else DATA.replace('celestial', 'minecraft'), 'tags', kind, path + '.json')
        existing = []
        if os.path.exists(base):
            with open(base) as f:
                existing = json.load(f)['values']
        write_json(base, {'replace': False, 'values': list(dict.fromkeys(existing + values))})
    lang_patch(names)
    print('ok: механизмы и загадки,', len(names), 'строк')


if __name__ == '__main__':
    main()
