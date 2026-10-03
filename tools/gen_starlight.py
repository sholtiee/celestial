"""Звёздный свет (волна 0.3, идеи из Astral Sorcery): Звездоловка, Флакон, Звёздная купель, Оберег.

Модели с уровнями (заряд Звездоловки 0–4, уровень купели 0–3, состояния Оберега), текстуры, рецепты, переводы.
"""
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, self_drop, shaped, write_json
from gen_story import lang_patch

F6 = ('north', 'south', 'east', 'west', 'up', 'down')
NIGHT = [T.hexrgb(h) for h in ('#0b1030', '#121a45', '#1a2458', '#22306a')]


def box(fr, to, tex, faces=F6, uv=None, rot=None):
    e = {'from': fr, 'to': to, 'faces': {d: {'texture': tex, **({'uv': uv} if uv else {})} for d in faces}}
    if rot:
        e['rotation'] = rot
    return e


def starfield(name, stars, glow):
    """Тёмно-синее «звёздное» поле: чем больше заряд, тем больше звёзд и ярче свечение."""
    img = T.noisy(name, NIGHT, cell=3, grain=0.3)
    r = T.rng_for(name + '_stars')
    for _ in range(stars):
        x, y = r.randrange(16), r.randrange(16)
        img.putpixel((x, y), (*T.hexrgb(r.choice(['#ffffff', '#fff3c6', '#bfd8ff'])), 255))
    if glow:
        px = img.load()
        for y in range(16):
            for x in range(16):
                d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
                k = max(0.0, 1 - d / 8) * glow
                px[x, y] = (*T.mix(px[x, y][:3], T.hexrgb('#9fc4ff'), k), 255)
    return img


def crystal_tex(name, lit):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    pal = ['#bfe7ff', '#7fc6f2', '#3f8fd0', '#ffffff'] if lit else ['#8fb3cc', '#5f86a8', '#3a5a7a', '#cfe3f0']
    for y in range(16):
        for x in range(16):
            edge = min(x, 15 - x, y, 15 - y)
            img.putpixel((x, y), (*T.hexrgb(pal[3] if edge == 0 and (x + y) % 3 == 0 else pal[min(2, edge // 3)]), 255))
    return img


def collector():
    for n in range(5):
        save_png(starfield(f'star_collector_top_{n}', 2 + n * 5, 0.15 * n), f'block/star_collector_top_{n}')
        model(f'block/star_collector_{n}', {
            'textures': {'stone': c('block/skystone_bricks'), 'trim': c('block/radiant_stone'), 'top': c(f'block/star_collector_top_{n}'),
                         'particle': c('block/skystone_bricks')},
            'elements': [box([4, 0, 4], [12, 2, 12], '#trim'), box([5, 2, 5], [11, 9, 11], '#stone'),
                         box([1, 9, 1], [15, 11, 15], '#trim', faces=('north', 'south', 'east', 'west', 'down')),
                         {'from': [1, 9, 1], 'to': [15, 11, 15], 'faces': {'up': {'texture': '#top'}}},
                         box([0, 11, 0], [16, 13, 1], '#trim'), box([0, 11, 15], [16, 13, 16], '#trim'),
                         box([0, 11, 1], [1, 13, 15], '#trim'), box([15, 11, 1], [16, 13, 15], '#trim')]})
    blockstate('star_collector', {'variants': {f'charge={n}': {'model': c(f'block/star_collector_{n}')} for n in range(5)}})
    item_def('star_collector', c('block/star_collector_4'))
    self_drop('star_collector')


def basin():
    liquid = starfield('star_liquid', 14, 0.5)
    save_png(liquid, 'block/star_liquid')
    walls = [box([3, 0, 3], [13, 3, 13], '#stone'), box([1, 3, 1], [15, 12, 3], '#stone'), box([1, 3, 13], [15, 12, 15], '#stone'),
             box([1, 3, 3], [3, 12, 13], '#stone'), box([13, 3, 3], [15, 12, 13], '#stone'), box([3, 3, 3], [13, 4, 13], '#stone')]
    for n in range(4):
        elements = list(walls)
        if n:
            h = 4 + n * 2.5
            elements.append({'from': [3, 4, 3], 'to': [13, h, 13], 'faces': {'up': {'texture': '#liquid'}}})
        model(f'block/star_basin_{n}', {'textures': {'stone': c('block/skystone_bricks'), 'liquid': c('block/star_liquid'),
                                                     'particle': c('block/skystone_bricks')}, 'elements': elements})
    blockstate('star_basin', {'variants': {f'level={n}': {'model': c(f'block/star_basin_{n}')} for n in range(4)}})
    item_def('star_basin', c('block/star_basin_3'))
    self_drop('star_basin')


def ward():
    save_png(crystal_tex('ward_crystal', False), 'block/ward_crystal')
    save_png(crystal_tex('ward_crystal_lit', True), 'block/ward_crystal_lit')
    base = [box([3, 0, 3], [13, 3, 13], '#trim'), box([5, 3, 5], [11, 12, 11], '#stone'), box([3, 12, 3], [13, 13, 13], '#trim')]
    gem = lambda: {'from': [6, 13, 6], 'to': [10, 20, 10], 'rotation': {'origin': [8, 16, 8], 'axis': 'y', 'angle': 45},  # noqa: E731
                   'faces': {d: {'texture': '#crystal'} for d in F6}}
    for name, crystal in (('ward', None), ('ward_crystal', 'ward_crystal'), ('ward_lit', 'ward_crystal_lit')):
        tex = {'stone': c('block/skystone_bricks'), 'trim': c('block/radiant_stone'), 'particle': c('block/skystone_bricks')}
        elements = list(base)
        if crystal:
            tex['crystal'] = c('block/' + crystal)
            elements.append(gem())
        model('block/' + name, {'textures': tex, 'elements': elements})
    blockstate('ward', {'variants': {
        'crystal=false,lit=false': {'model': c('block/ward')}, 'crystal=false,lit=true': {'model': c('block/ward')},
        'crystal=true,lit=false': {'model': c('block/ward_crystal')}, 'crystal=true,lit=true': {'model': c('block/ward_lit')}}})
    item_def('ward', c('block/ward_crystal'))
    self_drop('ward')


SPRITES = {
    'starlight_flask': ({'g': '#d8ecff', 'G': '#9fc4e8', 'c': '#8a6238', 'l': '#bfd8ff', 'L': '#ffffff', 'b': '#3f6fd0'}, [
        '................',
        '................',
        '......cc........',
        '......cc........',
        '.....gGGg.......',
        '......gg........',
        '.....gllg.......',
        '....glLlbg......',
        '...gllLllbg.....',
        '...glLllLbg.....',
        '...gllllbbg.....',
        '...gbllbbbg.....',
        '....gbbbbg......',
        '.....gggg.......',
        '................',
        '................']),
    'starsteel_ingot': ({'1': '#3a4a6e', '2': '#5a74a8', '3': '#8fb0e0', '4': '#e6f0ff', 's': '#fff3c6'}, [
        '................',
        '................',
        '................',
        '................',
        '................',
        '......11111111..',
        '.....1233s3321..',
        '....12344443321.',
        '...1233s4433221.',
        '..1222333322221.',
        '..111111111111..',
        '................',
        '................',
        '................',
        '................',
        '................']),
    'charged_crystal': ({'1': '#1f4f8a', '2': '#3f8fd0', '3': '#9fd8ff', '4': '#ffffff'}, [
        '................',
        '.......4........',
        '......434.......',
        '......323.......',
        '.....32223......',
        '.....32123......',
        '....3221223.....',
        '....3211123..4..',
        '....3221123.434.',
        '....3221223..4..',
        '.....32123......',
        '.....32223......',
        '......323.......',
        '......434.......',
        '.......4........',
        '................']),
}


def main():
    collector()
    basin()
    ward()
    for name, (colors, rows) in SPRITES.items():
        save_png(T.sprite(rows, colors), 'item/' + name)
        model('item/' + name, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + name)}})
        item_def(name, c('item/' + name))
    shaped('star_collector', c('star_collector'), [' G ', 'SFS', 'BBB'],
           {'G': 'minecraft:glass', 'S': c('starquartz'), 'F': c('star_fragment'), 'B': c('skystone_bricks')}, 1, 'misc')
    shaped('star_basin', c('star_basin'), ['B B', 'BSB', 'BBB'], {'B': c('skystone_bricks'), 'S': c('starquartz')}, 1, 'misc')
    shaped('ward', c('ward'), [' R ', 'SFS', 'BBB'],
           {'R': c('radiant_stone'), 'S': c('starsteel_ingot'), 'F': c('star_fragment'), 'B': c('skystone_bricks')}, 1, 'misc')
    append_tag('block', 'minecraft:mineable/pickaxe', [c('star_collector'), c('star_basin'), c('ward')])
    append_tag('entity_type', 'celestial:repelled_by_wards', [c('shadow')])
    lang_patch({
        'block.celestial.star_collector': ('Звездоловка', 'Star Catcher'),
        'block.celestial.star_collector.charge': ('Звёздный свет: %s / %s (нужно 100 на флакон)', 'Starlight: %s / %s (100 per flask)'),
        'block.celestial.star_collector.empty': ('Мало звёздного света — дождись ночи под открытым небом', 'Not enough starlight — wait for a night under open sky'),
        'block.celestial.star_basin': ('Звёздная купель', 'Star Basin'),
        'block.celestial.ward': ('Оберег', 'Ward'),
        'block.celestial.ward.no_crystal': ('Оберегу нужен заряженный кристалл', 'The Ward needs a charged crystal'),
        'block.celestial.ward.fuel': ('Оберег горит ещё ~%s мин. Флакон звёздного света добавит 5 минут', 'The Ward burns for ~%s more min. A starlight flask adds 5 minutes'),
        'block.celestial.ward.full': ('Оберег заправлен до предела', 'The Ward is fully fuelled'),
        'item.celestial.starlight_flask': ('Флакон звёздного света', 'Flask of Starlight'),
        'item.celestial.starsteel_ingot': ('Слиток звёздной стали', 'Starsteel Ingot'),
        'item.celestial.charged_crystal': ('Заряженный кристалл', 'Charged Crystal'),
        'codex.celestial.guide.10': ('Звездоловка ночью копит звёздный свет — склянкой наберёшь Флакон. Он снимает страх тьмы.',
                                     'A Star Catcher gathers starlight at night — fill a bottle to get a Flask. It dispels fear of the dark.'),
        'codex.celestial.guide.11': ('Звёздная купель: влей флакон и брось предмет. Железо → звёздная сталь, небесный кристалл → заряженный.',
                                     'Star Basin: pour a flask, then toss items in. Iron → starsteel, sky crystal → charged crystal.'),
        'codex.celestial.guide.12': ('Оберег с заряженным кристаллом и флаконами отгоняет Теней и страх в радиусе 16 блоков.',
                                     'A Ward with a charged crystal and flasks keeps Shadows and fear away within 16 blocks.'),
    })
    print('ok: звёздный свет')


if __name__ == '__main__':
    main()
