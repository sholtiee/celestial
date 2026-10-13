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
    if choir == 'seraphim':  # Отблеск «Угль» (S5.6) — у края святилища Серафимов
        t.set(cx, 2, cz + 5, c('memory_anchor'), nbt={'id': c('memory_anchor'), 'Scene': 'seraph_coal'})
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


# ---------------------------------------------------------------- рисунки хоров (S5.4): иллюстрации 96×54 для Кодекса
def choir_art(choir):
    """Картина хора в духе Летописи: небо, свечение и символ чина. Без лиц и фигур — только знаки (крылья, колёса, венцы)."""
    import random as _r
    from PIL import ImageDraw
    from gen_lore import H as AH, W as AW, frame, glow, gradient, rgb, stars
    rng = _r.Random('choir_art_' + choir)
    sky = {'seraphim': ('#3a0a08', '#e0782a'), 'cherubim': ('#101a3a', '#c88a3a'), 'thrones': ('#0a1028', '#5a6ac8'),
           'dominions': ('#1a0e2e', '#8a5ad0'), 'virtues': ('#08142e', '#4ab0e0'), 'powers': ('#160a0a', '#a83a2a'),
           'principalities': ('#0e1430', '#c8a050'), 'archangels': ('#101a36', '#e8d080'), 'angels': ('#0c1430', '#8ab8f0')}[choir]
    img = gradient(*sky)
    stars(img, rng, 26, ymax=AH)
    cx, cy = AW // 2, AH // 2
    glow(img, cx, cy, 22, '#fff4c8', 0.8)
    d = ImageDraw.Draw(img)
    gold, white = rgb('#f2d68a'), rgb('#fffbe8')
    if choir == 'seraphim':  # шесть огненных крыльев вокруг света
        for k, (dx, dy) in enumerate(((16, -14), (20, -2), (14, 10))):
            for sgn in (-1, 1):
                d.polygon([(cx + sgn * 3, cy), (cx + sgn * dx, cy + dy), (cx + sgn * (dx - 4), cy + dy + 5)], fill=rgb('#ff9a3a'), outline=gold)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=white)
    elif choir == 'cherubim':  # крылья и пламенный меч
        for sgn in (-1, 1):
            d.polygon([(cx, cy - 2), (cx + sgn * 22, cy - 14), (cx + sgn * 18, cy + 6)], fill=rgb('#e8d8b0'), outline=gold)
        d.line([(cx, cy + 18), (cx, cy - 20)], fill=rgb('#ff7a2a'), width=2)
        d.line([(cx - 5, cy + 10), (cx + 5, cy + 10)], fill=gold, width=2)
    elif choir == 'thrones':  # колесо в колесе, полное очей
        d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=gold, width=2)
        d.ellipse([cx - 10, cy - 18, cx + 10, cy + 18], outline=rgb('#c9973a'), width=1)
        for k in range(10):
            a = k * 2 * math.pi / 10
            x, y = cx + math.cos(a) * 18, cy + math.sin(a) * 18
            d.ellipse([x - 2, y - 1, x + 2, y + 1], fill=white)
            d.point((round(x), round(y)), fill=rgb('#1a1a40'))
    elif choir == 'dominions':  # венец и скипетр
        d.polygon([(cx - 14, cy - 2), (cx - 14, cy - 12), (cx - 7, cy - 6), (cx, cy - 16), (cx + 7, cy - 6), (cx + 14, cy - 12), (cx + 14, cy - 2)],
                  fill=gold, outline=rgb('#8a6a1e'))
        d.line([(cx, cy + 2), (cx, cy + 22)], fill=gold, width=2)
        d.ellipse([cx - 3, cy - 1, cx + 3, cy + 5], fill=rgb('#d84a4a'))
    elif choir == 'virtues':  # сияние: лучи и малые звёзды
        for k in range(16):
            a = k * 2 * math.pi / 16
            r = 22 if k % 2 == 0 else 14
            d.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=gold)
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=white)
    elif choir == 'powers':  # меч и щит
        d.polygon([(cx - 12, cy - 12), (cx + 12, cy - 12), (cx + 12, cy + 2), (cx, cy + 16), (cx - 12, cy + 2)], fill=rgb('#5a6a8a'), outline=gold)
        d.line([(cx - 20, cy + 18), (cx + 20, cy - 22)], fill=white, width=2)
        d.line([(cx - 16, cy + 9), (cx - 9, cy + 16)], fill=gold, width=2)
    elif choir == 'principalities':  # град под венцом
        for x0, h in ((cx - 24, 10), (cx - 14, 16), (cx - 4, 22), (cx + 6, 14), (cx + 16, 18)):
            d.rectangle([x0, cy + 20 - h, x0 + 8, cy + 20], fill=rgb('#2a2440'), outline=rgb('#c9973a'))
        d.polygon([(cx - 10, cy - 12), (cx - 10, cy - 18), (cx - 5, cy - 14), (cx, cy - 20), (cx + 5, cy - 14), (cx + 10, cy - 18), (cx + 10, cy - 12)], fill=gold)
    elif choir == 'archangels':  # труба и волны звука
        d.polygon([(cx - 20, cy + 2), (cx + 8, cy - 2), (cx + 18, cy - 10), (cx + 18, cy + 10), (cx + 8, cy + 2)], fill=gold, outline=rgb('#8a6a1e'))
        for r in (8, 14, 20):
            d.arc([cx + 18 - r, cy - r, cx + 18 + r, cy + r], 300, 60, fill=white)
    else:  # angels: перо и путь звёзд
        d.line([(cx - 14, cy + 18), (cx + 10, cy - 18)], fill=white, width=1)
        for k in range(8):
            t = k / 7
            x, y = cx - 14 + 24 * t, cy + 18 - 36 * t
            d.line([(x, y), (x + 8 - 4 * t, y + 4)], fill=rgb('#e8f0ff'))
            d.line([(x, y), (x - 6 + 3 * t, y - 2)], fill=rgb('#e8f0ff'))
        for k in range(6):
            d.point((10 + k * 14, AH - 8 - (k % 2) * 3), fill=gold)
    return frame(img)


def main():
    blocks()
    for choir in CHOIRS:
        save_png(choir_art(choir), f'gui/choirs/{choir}')
        shrine(choir)
    lang()
    print('ok: хоры Астрала — диски, гнёзда, святилища', len(CHOIRS))


if __name__ == '__main__':
    main()
