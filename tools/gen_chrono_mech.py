"""Хроноград (волна 0.5), механика Времени: маятники (зоны иного хода) и Песочные часы.

Корпус маятника — латунный (Быстрый) или свинцово-железный (Тяжёлый) шкафчик с циферблатом на лицевой стороне;
стрелка циферблата бежит анимацией (у остановленного — стоит). Сам маятник (стержень, шарнир, груз) рисует
`client/chrono/PendulumRenderer` по текстуре `textures/entity/chrono/pendulum_<вид>.png` (развёртка 32×32 по texOffs модели).
"""
import json
import math
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, c, save_png, blockstate, model, item_def, self_drop, shaped
from gen_story import lang_patch

KINDS = {
    # имя: (пластины корпуса, кант/заклёпки, циферблат, стрелка, кадров на оборот, тиков на кадр)
    'swift_pendulum': (T.pal('#8a5a1c', '#a8722a', '#c48e3a', '#dcaa52', '#f0c86e'), '#5a3410', '#f4e6c0', '#7a1a10', 12, 1),
    'heavy_pendulum': (T.pal('#3a3f4a', '#4a505c', '#5a616e', '#6b7380', '#7d8592'), '#22262e', '#c8ccd4', '#1a2a5a', 12, 5),
}


def px(img, x, y, col, a=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), (*col[:3], a))


def plate(name, pal, rim):
    """Клёпаная пластина корпуса: шум металла, кант по краю, заклёпки в углах, горизонтальный шов."""
    img = T.noisy(name, pal[1:], cell=4, grain=0.18)
    rim = T.hexrgb(rim)
    for i in range(16):
        px(img, i, 0, rim)
        px(img, i, 15, rim)
        px(img, 0, i, rim)
        px(img, 15, i, rim)
        px(img, i, 1, T.shade(img.getpixel((i, 1)), 1.18))
        px(img, 1, i, T.shade(img.getpixel((1, i)), 1.12))
        px(img, i, 7, T.shade(img.getpixel((i, 7)), 0.78))
        px(img, i, 8, T.shade(img.getpixel((i, 8)), 1.1))
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13), (2, 5), (13, 10)):
        px(img, x, y, T.shade(pal[-1], 1.15))
        px(img, x + 1, y + 1, rim)
    return img


def dial(name, pal, rim, face, hand_col, angle, lit):
    """Лицевая сторона: пластина с круглым циферблатом, римские риски, стрелка под углом angle (радианы)."""
    img = plate(name, pal, rim)
    face, hand_col, rim_c = T.hexrgb(face), T.hexrgb(hand_col), T.hexrgb(rim)
    cx = cy = 7.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            if d < 5.6:
                glow = 0.12 if lit else 0.0
                px(img, x, y, T.mix(face, (255, 255, 255), glow) if d < 4.9 else T.shade(face, 0.82))
            elif d < 6.5:
                px(img, x, y, T.shade(pal[-1], 1.05))
            elif d < 7.2:
                px(img, x, y, rim_c)
    for i in range(12):
        t = i * math.pi / 6
        r = 4.2 if i % 3 else 3.8
        px(img, round(cx + math.sin(t) * r), round(cy - math.cos(t) * r), T.shade(face, 0.45 if i % 3 == 0 else 0.65))
    for k in range(5):  # длинная стрелка
        px(img, round(cx + math.sin(angle) * k * 0.95), round(cy - math.cos(angle) * k * 0.95), hand_col)
    for k in range(3):  # короткая — отстаёт вдвое
        a2 = angle / 12 + 1.0
        px(img, round(cx + math.sin(a2) * k), round(cy - math.cos(a2) * k), T.shade(hand_col, 0.7))
    px(img, 7, 7, T.shade(hand_col, 0.6))  # ось
    return img


def gear_top(name, pal, rim):
    """Крышка: шестерня с зубцами вокруг оси."""
    img = plate(name, pal, rim)
    rim_c = T.hexrgb(rim)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            a = math.atan2(y - 7.5, x - 7.5)
            tooth = (math.cos(a * 8) > 0.3)
            if d < 1.6:
                px(img, x, y, rim_c)
            elif d < 4.6 or (d < 6.2 and tooth):
                px(img, x, y, T.shade(pal[3], 1.0 + 0.15 * math.cos(a - 2.3)))
            elif d < 6.9 and tooth:
                px(img, x, y, rim_c)
    return img


def blocks():
    for name, (pal, rim, face, hand, frames, ft) in KINDS.items():
        save_png(plate(name + '_side', pal, rim), 'block/' + name + '_side')
        save_png(gear_top(name + '_top', pal, rim), 'block/' + name + '_top')
        save_png(dial(name + '_front_still', pal, rim, face, hand, 0.0, False), 'block/' + name + '_front_still')
        sheet = Image.new('RGBA', (16, 16 * frames))
        for i in range(frames):
            sheet.paste(dial(name + '_front', pal, rim, face, hand, i * 2 * math.pi / frames, True), (0, 16 * i))
        save_png(sheet, 'block/' + name + '_front')
        with open(os.path.join(ASSETS, 'textures/block', name + '_front.png.mcmeta'), 'w') as f:
            json.dump({'animation': {'frametime': ft, 'interpolate': False}}, f)

        for still in (False, True):
            suffix = '_still' if still else ''
            tex = {k: c(f'block/{name}_{v}') for k, v in (('side', 'side'), ('top', 'top'))}
            tex['front'] = c(f'block/{name}_front' + suffix)
            tex['particle'] = tex['side']
            model('block/' + name + suffix, {
                'parent': 'minecraft:block/block',
                'textures': tex,
                'elements': [
                    {'from': [2, 2, 2], 'to': [14, 14, 14], 'faces': {
                        'north': {'uv': [2, 2, 14, 14], 'texture': '#front'},
                        'south': {'uv': [2, 2, 14, 14], 'texture': '#side'},
                        'east': {'uv': [2, 2, 14, 14], 'texture': '#side'},
                        'west': {'uv': [2, 2, 14, 14], 'texture': '#side'}}},
                    {'from': [1, 14, 1], 'to': [15, 16, 15], 'faces': {
                        'north': {'uv': [1, 0, 15, 2], 'texture': '#side'}, 'south': {'uv': [1, 0, 15, 2], 'texture': '#side'},
                        'east': {'uv': [1, 0, 15, 2], 'texture': '#side'}, 'west': {'uv': [1, 0, 15, 2], 'texture': '#side'},
                        'up': {'uv': [1, 1, 15, 15], 'texture': '#top'}, 'down': {'uv': [1, 1, 15, 15], 'texture': '#side'}}},
                    {'from': [1, 0, 1], 'to': [15, 2, 15], 'faces': {
                        'north': {'uv': [1, 14, 15, 16], 'texture': '#side'}, 'south': {'uv': [1, 14, 15, 16], 'texture': '#side'},
                        'east': {'uv': [1, 14, 15, 16], 'texture': '#side'}, 'west': {'uv': [1, 14, 15, 16], 'texture': '#side'},
                        'up': {'uv': [1, 1, 15, 15], 'texture': '#side'}, 'down': {'uv': [1, 1, 15, 15], 'texture': '#top'}}},
                ],
            })
        rot = {'north': 0, 'east': 90, 'south': 180, 'west': 270}
        blockstate(name, {'variants': {
            f'facing={f},swinging={str(s).lower()}': {'model': c('block/' + name + ('' if s else '_still')), **({'y': r} if r else {})}
            for f, r in rot.items() for s in (True, False)}})
        item_def(name, c('block/' + name))
        self_drop(name)
        pendulum_entity(name, pal, rim)
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in KINDS])
    shaped('swift_pendulum', c('swift_pendulum'), ['GCG', 'GKG', ' G '],
           {'G': 'minecraft:gold_ingot', 'C': 'minecraft:copper_ingot', 'K': 'minecraft:clock'}, 1, 'redstone')
    shaped('heavy_pendulum', c('heavy_pendulum'), ['III', 'IKI', ' B '],
           {'I': 'minecraft:iron_ingot', 'K': 'minecraft:clock', 'B': 'minecraft:iron_block'}, 1, 'redstone')


def pendulum_entity(name, pal, rim):
    """Развёртка 32×32: стержень (0,0), груз 7×7×2 (4,0), ободки (4,9)/(4,12), втулка (12,12), шарнир (0,24)."""
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    r = T.rng_for(name + '_ent')
    swift = name.startswith('swift')
    metal = pal
    def fill(x0, y0, x1, y1, base, var=0.08):
        for y in range(y0, y1):
            for x in range(x0, x1):
                px(img, x, y, T.shade(base, 1 - var + r.random() * var * 2))
    rod = T.hexrgb('#d8b060') if swift else T.hexrgb('#6a7280')
    fill(0, 0, 4, 19, rod)
    for y in range(0, 19, 4):  # риски на стержне
        for x in range(4):
            px(img, x, y, T.shade(rod, 0.7))
    fill(4, 0, 22, 9, metal[3])  # груз
    bob_face = T.hexrgb('#f0c86e') if swift else T.hexrgb('#8a92a0')
    engr = T.hexrgb('#8a5010') if swift else T.hexrgb('#2a3044')
    for ox in (6, 15):  # лицевая и тыльная грани 7×7
        for y in range(7):
            for x in range(7):
                d = math.hypot(x - 3, y - 3)
                col = T.mix(bob_face, (255, 255, 255), max(0, 0.35 - d / 10))
                if swift and (d < 1.5 or (2.4 < d < 3.4 and (x + y) % 2 == 0)):
                    col = engr  # солнце: диск и лучи
                if not swift and 1.2 < d < 3.2 and math.hypot(x - 4.3, y - 2.4) > 2.1:
                    col = engr  # месяц
                px(img, ox + x, 2 + y, col)
    fill(4, 9, 18, 12, T.hexrgb(rim))
    fill(4, 12, 10, 19, T.hexrgb(rim))
    fill(12, 12, 24, 18, metal[4])
    fill(0, 24, 12, 30, T.hexrgb(rim))
    save_png(img, 'entity/chrono/pendulum_' + name.split('_')[0])


def hourglass():
    """Песочные часы: золотые крышки и стойки, две стеклянные колбы, песок наполовину перетёк."""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    gold, dark, glass, sand = T.hexrgb('#e8b84a'), T.hexrgb('#7a5418'), T.hexrgb('#cfe8f4'), T.hexrgb('#e8c87a')
    for x in range(3, 13):
        for y in (1, 2, 13, 14):
            px(img, x, y, gold if y in (1, 13) else dark)
    for y in range(3, 13):
        w = abs(y - 7.5)  # колбы сужаются к середине
        half = 1 + int(w * 0.75)
        for x in range(8 - half, 8 + half):
            px(img, x, y, glass, 150)
        px(img, 8 - half - 1, y, T.shade(glass, 0.7))
        px(img, 8 + half, y, T.shade(glass, 0.7))
        if y >= 10 or (5 <= y <= 6 and w < 3):
            for x in range(8 - half, 8 + half):
                px(img, x, y, T.shade(sand, 0.9 + 0.1 * ((x + y) % 2)))
    for y in (7, 8, 9):
        px(img, 7, y, sand)
    for y in range(2, 14):  # стойки
        px(img, 3, y, gold)
        px(img, 12, y, dark)
    save_png(img, 'item/hourglass')
    model('item/hourglass', {'parent': 'minecraft:item/handheld', 'textures': {'layer0': c('item/hourglass')}})
    item_def('hourglass', c('item/hourglass'))
    shaped('hourglass', c('hourglass'), ['GGG', 'SIS', 'GGG'],
           {'G': 'minecraft:gold_ingot', 'S': 'minecraft:glass', 'I': c('ice_core')}, 1, 'equipment')


def tags():
    append_tag('entity_type', 'celestial:time_immune', [
        c('fallen_seraph'), c('light_devourer'), c('frost_archon'),
        'minecraft:ender_dragon', 'minecraft:wither', 'minecraft:warden', 'minecraft:elder_guardian'])


def lang():
    lang_patch({
        'block.celestial.swift_pendulum': ('Быстрый маятник', 'Swift Pendulum'),
        'block.celestial.swift_pendulum.lore1': ('Пока качается — в шести блоках время бежит вдвое быстрее', 'While it swings, time runs twice as fast within six blocks'),
        'block.celestial.swift_pendulum.lore2': ('ПКМ пустой рукой — остановить или пустить', 'Use with an empty hand to stop or start it'),
        'block.celestial.heavy_pendulum': ('Тяжёлый маятник', 'Heavy Pendulum'),
        'block.celestial.heavy_pendulum.lore1': ('Пока качается — в шести блоках время тянется вдвое медленнее', 'While it swings, time drags at half speed within six blocks'),
        'block.celestial.heavy_pendulum.lore2': ('ПКМ пустой рукой — остановить или пустить', 'Use with an empty hand to stop or start it'),
        'block.celestial.pendulum.sealed': ('Древний маятник не слушается руки', 'The ancient pendulum does not yield to a hand'),
        'item.celestial.hourglass': ('Песочные часы', 'Hourglass'),
        'item.celestial.hourglass.lore1': ('ПКМ: на 5 с останавливает время вокруг (10 блоков)', 'Use: stops time around you for 5 s (10 blocks)'),
        'item.celestial.hourglass.lore2': ('Мобы и снаряды замирают; сильных лишь замедляет', 'Mobs and projectiles freeze; the mighty only slow down'),
        'hud.celestial.time.stopped': ('Время стоит', 'Time stands still'),
        'hud.celestial.time.slow': ('Время тянется', 'Time drags'),
        'hud.celestial.time.fast': ('Время мчится', 'Time races'),
    })


def main():
    blocks()
    hourglass()
    tags()
    lang()
    print('Хроноград: маятники', ', '.join(KINDS), '+ Песочные часы')


if __name__ == '__main__':
    main()
