"""Астрал (волна 0.6, O5 шаг 2): созвездия девяти хоров — Звёздный диск, гнёзда, Звёздный камень, святилища хоров, переводы.

Рисунки созвездий — в коде (`astral/Choir.java`, точки на поле 5×5); здесь они повторены для святилищ, чтобы сценарий и линтер могли
проверить решаемость. Святилище `celestial:star_shrine/<хор>` — парящий островок с диском и полем гнёзд (в мир Астрала их ставит S5.1).
"""
import math
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, c, save_png, blockstate, model, item_def, shaped
from gen_story import lang_patch
from gen_structures import Template

H = T.hexrgb

# id: (ru, en, благословение ru, en) — порядок от младшего к старшему, как в Choir.java
CHOIRS = {
    'angels': ('Ангелы', 'Angels', 'Скорость +10%, падение мягче', 'Speed +10%, softer falls'),
    'archangels': ('Архангелы', 'Archangels', '+2 сердца здоровья', '+2 hearts of health'),
    'principalities': ('Начала', 'Principalities', 'Добыча блоков быстрее на 25%', 'Mine blocks 25% faster'),
    'powers': ('Власти', 'Powers', 'Броня +3, прочность брони +2', 'Armor +3, armor toughness +2'),
    'virtues': ('Силы', 'Virtues', 'Урон +20%', 'Damage +20%'),
    'dominions': ('Господства', 'Dominions', 'Скорость атаки +15%, удача +1', 'Attack speed +15%, luck +1'),
    'thrones': ('Престолы', 'Thrones', 'При смерти время вокруг тянется', 'Near death, time drags around you'),
    'cherubim': ('Херувимы', 'Cherubim', 'Удары отбрасывают, тебя — вдвое меньше', 'Your blows knock back; you are knocked back half as much'),
    'seraphim': ('Серафимы', 'Seraphim', 'Огонь не жжёт, удары поджигают', 'Fire does not burn you; your blows ignite'),
}
PATTERNS = {  # те же точки, что в Choir.java (x вправо, z на юг)
    'angels': [(0, 0), (-1, -1), (-2, -1), (1, -1), (2, -1)],
    'archangels': [(0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-1, -1), (1, -1)],
    'principalities': [(0, 0), (-2, 1), (-2, -1), (-1, 0), (0, -2), (1, 0), (2, -1), (2, 1)],
    'powers': [(0, 0), (0, -2), (2, 0), (0, 2), (-2, 0)],
    'virtues': [(0, 0), (-2, -2), (-1, -1), (1, 1), (2, 2), (2, -2), (1, -1), (-1, 1), (-2, 2)],
    'dominions': [(0, 0), (0, 2), (0, 1), (0, -1), (-1, -2), (1, -2), (0, -2)],
    'thrones': [(0, 0), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)],
    'cherubim': [(0, 0), (-2, -2), (2, -2), (2, 2), (-2, 2), (0, -1)],
    'seraphim': [(0, 0), (-2, -2), (-2, 0), (-2, 2), (2, -2), (2, 0), (2, 2)],
}
RANKS = [('Ангел', 'Angel'), ('Архангел', 'Archangel'), ('Начало', 'Principality'), ('Власть', 'Power'), ('Сила', 'Virtue'),
         ('Господство', 'Dominion'), ('Престол', 'Throne'), ('Херувим', 'Cherub'), ('Серафим', 'Seraph')]
PHASES = [('полнолуние', 'full moon'), ('убывающая луна', 'waning gibbous'), ('последняя четверть', 'third quarter'),
          ('старый месяц', 'waning crescent'), ('новолуние', 'new moon'), ('молодой месяц', 'waxing crescent'),
          ('первая четверть', 'first quarter'), ('растущая луна', 'waxing gibbous')]


def put(img, x, y, col, a=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), (*col[:3], a))


def stone_bg(name):
    """Тёмно-синий звёздный камень: шум и редкие искры."""
    img = T.noisy(name, T.pal('#10142e', '#161c3c', '#1c244a', '#232c58'), cell=4, grain=0.2)
    r = T.rng_for(name + '_sparks')
    for _ in range(7):
        put(img, r.randrange(16), r.randrange(16), T.mix(H('#b8c8ff'), H('#ffffff'), r.random()))
    return img


def disk_top(lit):
    img = stone_bg('star_disk')
    ring = H('#fff1b8') if lit else H('#5a6aa8')
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if 5.6 <= d < 6.6:
                put(img, x, y, ring)
            elif 6.6 <= d < 7.4:
                put(img, x, y, T.shade(ring, 0.6))
    for k in range(8):  # восемь лучей-фаз
        a = k * math.pi / 4
        for rr in (2.5, 3.5, 4.5):
            put(img, round(7.5 + math.cos(a) * rr), round(7.5 + math.sin(a) * rr), H('#ffe7a0') if lit else H('#3a4a88'))
    for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):
        put(img, x, y, H('#ffffff') if lit else H('#8a9ae0'))
    return img


def socket_tex(filled):
    img = stone_bg('star_socket')
    for i in range(16):
        for x, y in ((i, 0), (i, 15), (0, i), (15, i)):
            put(img, x, y, H('#2e3a78'))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d < 3.2:
                put(img, x, y, T.mix(H('#ffffff'), H('#9fb8ff'), d / 3.2) if filled else H('#070a18'))
            elif d < 4.2:
                put(img, x, y, H('#c9a23a') if filled else H('#3a4a88'))
    return img


def star_stone_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            dx, dy = abs(x - 7.5), abs(y - 7.5)
            if dx + dy < 6.5 and min(dx, dy) < 2.5 or dx + dy < 4:
                k = (dx + dy) / 6.5
                put(img, x, y, T.mix(H('#ffffff'), H('#5a7ae0'), k))
    for x, y in ((7, 7), (8, 8)):
        put(img, x, y, H('#fff8d0'))
    return img


def blocks():
    for lit in (False, True):
        name = 'star_disk' + ('_lit' if lit else '')
        save_png(disk_top(lit), 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/' + name), 'side': c('block/star_socket_side'), 'bottom': c('block/star_socket_side')}})
    blockstate('star_disk', {'variants': {'lit=false': {'model': c('block/star_disk')}, 'lit=true': {'model': c('block/star_disk_lit')}}})
    item_def('star_disk', c('block/star_disk'))
    side = stone_bg('star_socket_side')
    save_png(side, 'block/star_socket_side')
    for filled in (False, True):
        name = 'star_socket' + ('_filled' if filled else '')
        save_png(socket_tex(filled), 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/block', 'textures': {
            'top': c('block/' + name), 'side': c('block/star_socket_side'), 'particle': c('block/star_socket_side')},
            'elements': [{'from': [0, 0, 0], 'to': [16, 4, 16], 'faces': {
                'up': {'texture': '#top'}, 'down': {'texture': '#side', 'cullface': 'down'},
                **{f: {'uv': [0, 12, 16, 16], 'texture': '#side', 'cullface': f} for f in ('north', 'south', 'east', 'west')}}}]})
    blockstate('star_socket', {'variants': {'filled=false': {'model': c('block/star_socket')},
                                            'filled=true': {'model': c('block/star_socket_filled')}}})
    item_def('star_socket', c('block/star_socket'))
    save_png(star_stone_icon(), 'item/star_stone')
    model('item/star_stone', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/star_stone')}})
    item_def('star_stone', c('item/star_stone'))
    # пока Астрал не даёт камни лутом (S5.1/S5.3) — крафт из звёздного кварца и светокамня
    shaped('star_stone', c('star_stone'), [' Q ', 'QGQ', ' Q '], {'Q': c('starquartz'), 'G': 'minecraft:glowstone_dust'}, 2, 'misc')
    append_tag('block', 'minecraft:dragon_immune', [c('star_disk'), c('star_socket')])
    append_tag('block', 'minecraft:wither_immune', [c('star_disk'), c('star_socket')])


def shrine(choir):
    """Святилище хора: парящий островок звёздного камня 11×11 (скруглённый), поле 5×5 гнёзд вокруг диска, четыре колонны с огнями."""
    S = 13
    t = Template(S, 8, S)
    t.fill(0, 0, 0, S - 1, 7, S - 1, 'minecraft:air')
    cx = cz = S // 2
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - cx, z - cz)
            if d <= 6.2:
                t.set(x, 1, z, 'minecraft:polished_blackstone' if d > 4.2 else 'minecraft:blackstone')
                if d <= 4.5:
                    t.set(x, 0, z, 'minecraft:blackstone')
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if dx == 0 and dz == 0:
                t.set(cx, 2, cz, c('star_disk'), lit=False, nbt={'id': c('star_disk'), 'Choir': choir})
            else:
                t.set(cx + dx, 2, cz + dz, c('star_socket'), filled=False)
    for dx, dz in ((-4, -4), (4, -4), (4, 4), (-4, 4)):
        x, z = cx + dx, cz + dz
        t.fill(x, 2, z, x, 4, z, 'minecraft:polished_blackstone_bricks')
        t.set(x, 5, z, 'minecraft:sea_lantern')
    return t.save(f'star_shrine/{choir}')


def lang():
    e = {
        'block.celestial.star_disk': ('Звёздный диск', 'Star Disk'),
        'block.celestial.star_socket': ('Звёздное гнездо', 'Star Socket'),
        'item.celestial.star_stone': ('Звёздный камень', 'Star Stone'),
        'item.celestial.star_stone.lore1': ('Вставь в гнездо Звёздного диска по рисунку созвездия', 'Set into a Star Disk socket following a constellation'),
        'block.celestial.star_disk.hint': ('Диск хора «%s»: вставь %s звёздных камней по рисунку созвездия (верх рисунка — север)',
                                           'Disk of the %s: set %s star stones following the constellation (top of the drawing is north)'),
        'block.celestial.star_disk.wrong': ('Звёзды не сложились в созвездие.', 'The stars do not form the constellation.'),
        'choir.celestial.remembers': ('Хор вспоминает', 'A Choir Remembers'),
        'choir.celestial.collected': ('✦ Хор «%s» собран (%s из 9). ПКМ по диску — сделать его покровителем.',
                                      '✦ The %s are gathered (%s of 9). Use the disk to take them as your patron.'),
        'choir.celestial.patron_set': ('✦ Твой небесный покровитель — %s: %s', '✦ Your heavenly patron: the %s — %s'),
        'block.celestial.telescope.constellation_new': ('✦ В разрыве облаков — новое созвездие: %s. Рисунок записан в Кодекс (вкладка «Созвездия»).',
                                                        '✦ Through a gap in the clouds, a new constellation: the %s. Its drawing is in the Codex (Constellations tab).'),
        'block.celestial.telescope.constellation': ('Этой ночью видно созвездие: %s.', 'Tonight the constellation of the %s is visible.'),
        'codex.celestial.tab.stars': ('Созвездия', 'Constellations'),
        'codex.celestial.stars.rank': ('Ранг: %s (хоров собрано: %s из 9)', 'Rank: %s (choirs gathered: %s of 9)'),
        'codex.celestial.stars.no_patron': ('Покровителя нет: собери хор на Звёздном диске Астрала.', 'No patron yet: gather a choir at a Star Disk in the Astral.'),
        'codex.celestial.stars.patron': ('Покровитель: %s — %s', 'Patron: the %s — %s'),
        'codex.celestial.stars.collected': ('Собран', 'Gathered'),
        'codex.celestial.stars.is_patron': ('Покровитель', 'Patron'),
        'codex.celestial.stars.seen': ('Видел. Диск — в Астрале', 'Seen. Its disk is in the Astral'),
        'codex.celestial.stars.astral_only': ('Только из Астрала', 'Only from the Astral'),
    }
    for cid, (ru, en, bru, ben) in CHOIRS.items():
        e[f'choir.celestial.{cid}'] = (ru, en)
        e[f'choir.celestial.{cid}.blessing'] = (bru, ben)
    for i, (ru, en) in enumerate(RANKS):
        e[f'rank.celestial.{i}'] = (ru, en)
    for i, (ru, en) in enumerate(PHASES):
        e[f'codex.celestial.stars.phase.{i}'] = (ru.capitalize(), en.capitalize())
    lang_patch(e)


def main():
    blocks()
    for choir in CHOIRS:
        shrine(choir)
    lang()
    print('ok: хоры Астрала — диски, гнёзда, святилища', len(CHOIRS))


if __name__ == '__main__':
    main()
