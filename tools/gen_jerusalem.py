"""Новый Иерусалим (волна 0.6, S5.5) — эпилог светлых концовок: город, сходящий с неба (Откр. 21–22).

Блоки: яспис («подобный кристаллу», стены), жемчуг (двенадцать ворот — «каждые ворота из одной жемчужины»), золотая мостовая
(«чистое золото, как прозрачное стекло»), камень основания — 12 самоцветов одним блоком со свойством `gem`, свет престола.

Шаблон `celestial:new_jerusalem/city` (75×34×75, центр (37, 12, 37) — уровень улицы; код — `story/NewJerusalem`, CENTER):
- под улицей 12 слоёв основания — перевёрнутая ступенчатая пирамида, сверху яспис, внизу аметист (Откр. 21:19–20);
- квадратная стена из ясписа (полуширина 33), по три ворот с каждой стороны, у каждых — ангел (21:12–13), ворота не затворяются (21:25);
- улицы — золото, сеткой от ворот к воротам; посередине главной улицы — река воды жизни от престола, по обе стороны — Древа Жизни
  с плодами (22:1–2); в кварталах — обители (Ин. 14:2) и сады;
- в центре — престол: ступени из жемчуга и золота и столб света без фигуры, радуга вокруг (4:3). Храма в городе нет (21:22).
"""
import math
import random

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import blockstate, c, item_def, model, save_png, self_drop
from gen_story import lang_patch
from gen_structures import Template

H = T.hexrgb
HALF, WALL, BELOW, TOP = 37, 33, 12, 22  # полуширина шаблона, стены; слоёв основания; высота над улицей
S = 2 * HALF + 1
C = HALF
Y0 = BELOW  # уровень улицы в шаблоне
GATES = (-16, 0, 16)
# двенадцать камней основания (Откр. 21:19–20): имя, светлый, основной, тёмный
GEMS = [
    ('jasper', '#e8fff0', '#9ee0b8', '#4a9a78'),
    ('sapphire', '#c8dcff', '#3a64d8', '#1a2a78'),
    ('chalcedony', '#f4f4ff', '#b8c4dc', '#6a7898'),
    ('emerald', '#c8ffd8', '#2ac070', '#0a6a38'),
    ('sardonyx', '#fff0e8', '#d0705a', '#6a2a20'),
    ('sardius', '#ffd0c0', '#d83a2a', '#701810'),
    ('chrysolite', '#f8ffc0', '#b8d83a', '#5a7a18'),
    ('beryl', '#d8fff8', '#4ad0c0', '#1a7068'),
    ('topaz', '#fff4c0', '#f0b830', '#8a5a10'),
    ('chrysoprase', '#e0ffd0', '#7ae070', '#2a7a30'),
    ('jacinth', '#ffe0c0', '#f07a30', '#8a3410'),
    ('amethyst', '#f0d8ff', '#a050e0', '#4a1a78'),
]


def put(img, x, y, col, a=255):
    if 0 <= x < 16 and 0 <= y < 16:
        img.putpixel((x, y), (*col, a))


# ---------------------------------------------------------------- текстуры
def jasper():
    img = T.noisy('jasper_block', [H(h) for h in ('#b8ecd0', '#c8f4dc', '#d8fae8', '#e8fff4')], cell=4, grain=0.25)
    r = T.rng_for('jasper_facets')
    for _ in range(4):  # кристальные грани — светлые диагонали
        x0, y0 = r.randrange(16), r.randrange(16)
        for i in range(r.randint(3, 6)):
            put(img, x0 + i, y0 - i, H('#ffffff'))
            put(img, x0 + i + 1, y0 - i, H('#f0fff8'))
    for i in range(16):
        put(img, i, 15, H('#8ccfb0'))
        put(img, 15, i, H('#8ccfb0'))
    return img


def pearl():
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            sheen = 0.5 + 0.5 * math.sin(d * 0.9 + x * 0.25)
            base = T.mix(H('#fbf6f0'), H('#f2e8f4'), sheen)
            tint = T.mix(H('#e8f4ff'), H('#ffe8f0'), 0.5 + 0.5 * math.sin((x - y) * 0.4))
            col = T.mix(base, tint, 0.35)
            if x in (0, 15) or y in (0, 15):
                col = T.mix(col, H('#d8ccd8'), 0.6)
            img.putpixel((x, y), (*col, 255))
    for x, y in ((4, 4), (5, 4), (4, 5), (11, 10)):
        put(img, x, y, H('#ffffff'))
    return img


def golden_street():
    img = Image.new('RGBA', (16, 16))
    r = T.rng_for('golden_street')
    for y in range(16):
        for x in range(16):
            tile = (x // 8 + y // 8) % 2
            col = T.mix(H('#f8d050'), H('#ffe890'), 0.25 + 0.5 * r.random() * 0.4 + 0.2 * tile)
            if x % 8 == 0 or y % 8 == 0:
                col = H('#c89a28')
            img.putpixel((x, y), (*col, 255))
    for k in range(2):  # стеклянный отблеск
        for i in range(5):
            put(img, 2 + i + k * 8, 6 - i + (k * 8 if k else 0), H('#fffbe0'))
            put(img, 3 + i + k * 8, 6 - i + (k * 8 if k else 0), H('#fff2b0'))
    return img


def gem(name, light, base, dark):
    lc, bc, dc = H(light), H(base), H(dark)
    img = Image.new('RGBA', (16, 16))
    r = T.rng_for('gem_' + name)
    for y in range(16):
        for x in range(16):
            u, v = x - 7.5, y - 7.5
            if max(abs(u), abs(v)) > 6.5:  # оправа-ступень: свет слева сверху, тень справа снизу
                col = T.mix(bc, lc if (u < 0 and abs(u) >= abs(v)) or (v < 0 and abs(v) >= abs(u)) else dc, 0.55)
            elif abs(u) + abs(v) < 4.5:  # площадка огранки
                col = T.mix(bc, lc, 0.45 + 0.1 * r.random())
            else:  # грани
                q = (u > 0) * 1 + (v > 0) * 2
                col = T.mix(bc, (lc, bc, bc, dc)[q], 0.35 + 0.1 * r.random())
            img.putpixel((x, y), (*col, 255))
    put(img, 5, 5, H('#ffffff'))
    put(img, 6, 5, T.mix(lc, H('#ffffff'), 0.5))
    return img


def throne_light():
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            a = math.atan2(y - 7.5, x - 7.5)
            ray = 0.5 + 0.5 * math.cos(a * 8)
            col = T.mix(H('#fffef0'), H('#ffe080'), min(1.0, d / 10) * (1 - 0.5 * ray))
            img.putpixel((x, y), (*col, 255))
    return img


def blocks():
    for name, img in (('jasper_block', jasper()), ('pearl_block', pearl()), ('golden_street', golden_street()), ('throne_light', throne_light())):
        save_png(img, 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + name)}})
        blockstate(name, {'variants': {'': {'model': c('block/' + name)}}})
        item_def(name, c('block/' + name))
    for n in ('jasper_block', 'pearl_block', 'golden_street'):
        self_drop(n)
    variants = {}
    for i, g in enumerate(GEMS):
        save_png(gem(*g), f'block/foundation_stone_{i}')
        model(f'block/foundation_stone_{i}', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c(f'block/foundation_stone_{i}')}})
        variants[f'gem={i}'] = {'model': c(f'block/foundation_stone_{i}')}
    blockstate('foundation_stone', {'variants': variants})
    item_def('foundation_stone', c('block/foundation_stone_0'))
    self_drop('foundation_stone')
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in ('jasper_block', 'pearl_block', 'golden_street', 'foundation_stone')])
    append_tag('block', 'minecraft:needs_iron_tool', [c(n) for n in ('jasper_block', 'pearl_block', 'golden_street', 'foundation_stone')])


# ---------------------------------------------------------------- город
def city():
    rng = random.Random(2122)
    t = Template(S, BELOW + TOP, S)
    t.fill(0, 0, 0, S - 1, BELOW + TOP - 1, S - 1, 'minecraft:air')  # астероиды в объёме города убрать
    for k in range(BELOW):  # основание: 12 слоёв, сверху вниз — от ясписа к аметисту, каждый на ступень уже
        y, r = Y0 - 1 - k, WALL + 1 - k
        t.fill(C - r, y, C - r, C + r, y, C + r, c('foundation_stone'), gem=k)

    jasper, pearl, gold = c('jasper_block'), c('pearl_block'), c('golden_street')
    grass = c('golden_grass')

    def street(x, z):
        dx, dz = abs(x - C), abs(z - C)
        if dx <= 6 or dz <= 2:  # главные улицы (север–юг шире: река и деревья)
            return True
        if any(abs(x - C - g) <= 1 for g in GATES[::2]) or any(abs(z - C - g) <= 1 for g in GATES[::2]):
            return True
        return max(dx, dz) >= WALL - 4  # кольцевая улица у стены

    for x in range(C - WALL + 2, C + WALL - 1):  # мостовая и сады
        for z in range(C - WALL + 2, C + WALL - 1):
            t.set(x, Y0, z, gold if street(x, z) else grass)

    # река воды жизни: от престола на север и юг посередине главной улицы, по берегам — Древа Жизни
    for z in list(range(C - WALL + 6, C - 6)) + list(range(C + 7, C + WALL - 5)):
        for x in range(C - 1, C + 2):
            t.set(x, Y0, z, 'minecraft:water', level=0)
        t.set(C - 2, Y0 + 1, z, pearl if z % 4 == 0 else 'minecraft:air')
        t.set(C + 2, Y0 + 1, z, pearl if z % 4 == 0 else 'minecraft:air')
    for z in list(range(C - WALL + 8, C - 8, 6)) + list(range(C + 10, C + WALL - 6, 6)):
        for side in (-4, 4):
            tree(t, rng, C + side, Y0 + 1, z)

    # стена: яспис, жемчужный пояс, зубцы, пилястры снаружи
    for x in range(C - WALL, C + WALL + 1):
        for z in range(C - WALL, C + WALL + 1):
            if max(abs(x - C), abs(z - C)) < WALL - 1:
                continue
            for y in range(Y0, Y0 + 13):
                t.set(x, y, z, pearl if y == Y0 + 7 else jasper)
            if (x + z) % 2 == 0:
                t.set(x, Y0 + 13, z, jasper)
            if (x + z) % 8 == 0:
                t.set(x, Y0 + 14, z, 'minecraft:light', level=15, waterlogged=False)
    for side in range(4):  # ворота
        for g in GATES:
            gate(t, side, g)

    # кварталы: обители и сады
    blocks_ = [(-24, -24), (-24, -8), (-24, 8), (-24, 24), (24, -24), (24, -8), (24, 8), (24, 24),
               (-12, -24), (12, -24), (-12, 24), (12, 24), (-12, -8), (12, -8), (-12, 8), (12, 8)]
    for i, (bx, bz) in enumerate(blocks_):
        if i % 3 == 1:
            garden(t, rng, C + bx, C + bz)
        else:
            mansion(t, rng, C + bx, C + bz, i)

    throne(t)
    for x in range(C - WALL + 3, C + WALL - 2, 5):  # «ночи там не будет» — невидимый свет над улицами
        for z in range(C - WALL + 3, C + WALL - 2, 5):
            if t.get(x, Y0, z) == gold and t.get(x, Y0 + 1, z) in (None, 'minecraft:air'):
                t.set(x, Y0 + 1, z, 'minecraft:light', level=15, waterlogged=False)
    return t.save('new_jerusalem/city')


def at(side, along, out):
    """Точка у стены: side 0 — юг (+Z), 1 — север, 2 — восток (+X), 3 — запад; along — вдоль стены, out — смещение от центра."""
    return [(C + along, C + out), (C - along, C - out), (C + out, C - along), (C - out, C + along)][side]


def gate(t, side, g):
    pearl, gold = c('pearl_block'), c('golden_street')
    for d in range(-3, 4):
        for o in range(WALL - 2, WALL + 1):
            x, z = at(side, g + d, o)
            for y in range(Y0 + 1, Y0 + 15):
                h = y - Y0
                opening = abs(d) <= 2 and (h <= 6 or (h == 7 and abs(d) <= 1))
                t.set(x, y, z, 'minecraft:air' if opening else pearl)
            t.set(x, Y0, z, gold)
        for o in range(WALL + 1, HALF + 1):  # площадка за воротами — ворота открыты в звёзды
            if abs(d) <= 2:
                x, z = at(side, g + d, o)
                t.set(x, Y0, z, pearl)
                if abs(d) == 2 or o == HALF:
                    t.set(x, Y0 + 1, z, c('jasper_block') if (o + d) % 2 == 0 else 'minecraft:air')
    for d in (-1, 0, 1):  # маковка над воротами
        x, z = at(side, g + d, WALL - 1)
        t.set(x, Y0 + 15, z, pearl)
    x, z = at(side, g, WALL - 1)
    t.set(x, Y0 + 16, z, pearl)
    # ангел у ворот (Откр. 21:12) — внутри, сбоку от прохода
    x, z = at(side, g + 3, WALL - 4)
    t.entity(x, Y0 + 1, z, {'id': c('angel'), 'NoAI': True, 'Silent': True, 'Invulnerable': True, 'PersistenceRequired': True,
                            'DespawnDelay': 0, 'Rotation': [[0.0, 180.0, 90.0, 270.0][side], 0.0]})


def tree(t, rng, x0, y0, z0):
    wood, leaves, blossom = c('skywood_wood'), c('skywood_leaves'), c('cloud_willow_leaves')
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            t.set(x0 + dx, y0 - 1, z0 + dz, c('golden_grass'))
    top = y0 + 4
    for y in range(y0, top + 1):
        t.set(x0, y, z0, wood, axis='y')
    for x in range(x0 - 3, x0 + 4):
        for y in range(top - 1, top + 4):
            for z in range(z0 - 3, z0 + 4):
                d = ((x - x0) / 3.0) ** 2 + ((y - top - 1) / 2.2) ** 2 + ((z - z0) / 3.0) ** 2
                if d <= 1 and t.get(x, y, z) in (None, 'minecraft:air') and rng.random() > 0.12:
                    t.set(x, y, z, blossom if rng.random() < 0.25 else leaves, persistent=True, distance=1, waterlogged=False)
    t.set(x0, top + 1, z0, 'minecraft:light', level=13, waterlogged=False)
    n = 0
    for _ in range(40):  # двенадцать плодов в году (22:2) — по два-три на дереве
        x, z = x0 + rng.randint(-2, 2), z0 + rng.randint(-2, 2)
        if (x, z) == (x0, z0):
            continue
        for y in range(top + 3, top - 2, -1):
            if t.get(x, y, z) in (leaves, blossom) and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                t.set(x, y - 1, z, c('life_fruit'), ripe=True)
                n += 1
                break
        if n >= 3:
            break


def mansion(t, rng, x0, z0, i):
    """Обитель: дом 9×9 из ясписа и жемчуга, золотая ступенчатая крыша, окна, свет внутри."""
    jasper, pearl, gold = c('jasper_block'), c('pearl_block'), c('golden_street')
    r = 4
    face = [(0, 1), (0, -1), (1, 0), (-1, 0)][i % 4]
    for x in range(x0 - r, x0 + r + 1):
        for z in range(z0 - r, z0 + r + 1):
            t.set(x, Y0, z, pearl)
            edge = max(abs(x - x0), abs(z - z0)) == r
            for y in range(Y0 + 1, Y0 + 6):
                if edge:
                    corner = abs(x - x0) == r and abs(z - z0) == r
                    win = not corner and y in (Y0 + 2, Y0 + 3) and (x - x0 + z - z0) % 3 == 0
                    t.set(x, y, z, pearl if corner else 'minecraft:glass' if win else jasper)
                else:
                    t.set(x, y, z, 'minecraft:air')
    for k in range(4):  # крыша
        rr = r - k
        for x in range(x0 - rr, x0 + rr + 1):
            for z in range(z0 - rr, z0 + rr + 1):
                if max(abs(x - x0), abs(z - z0)) == rr or k == 3:
                    t.set(x, Y0 + 6 + k, z, gold)
    t.set(x0, Y0 + 10, z0, c('pearl_block'))
    dx, dz = face
    for y in (Y0 + 1, Y0 + 2, Y0 + 3):  # дверной проём к улице
        for s in (-1, 0, 1):
            if y == Y0 + 3 and s != 0:
                continue
            t.set(x0 + dx * r + dz * s, y, z0 + dz * r + dx * s, 'minecraft:air')
    t.set(x0, Y0 + 5, z0, 'minecraft:light', level=15, waterlogged=False)
    t.set(x0 - dx * 2, Y0 + 1, z0 - dz * 2, c('star_flower') if rng.random() < 0.5 else c('fig_bush'))


def garden(t, rng, x0, z0):
    """Сад: золотая трава, цветы, чаша-фонтан с водой."""
    flowers = ['minecraft:lily_of_the_valley', 'minecraft:oxeye_daisy', 'minecraft:cornflower', c('star_flower'), c('fig_bush')]
    for x in range(x0 - 5, x0 + 6):
        for z in range(z0 - 5, z0 + 6):
            if t.get(x, Y0, z) == c('golden_grass') and math.hypot(x - x0, z - z0) > 2.5 and rng.random() < 0.3:
                t.set(x, Y0 + 1, z, rng.choice(flowers))
    for x in range(x0 - 2, x0 + 3):
        for z in range(z0 - 2, z0 + 3):
            ring = max(abs(x - x0), abs(z - z0)) == 2
            t.set(x, Y0, z, c('pearl_block') if ring else 'minecraft:water', **({} if ring else {'level': 0}))
            if ring:
                t.set(x, Y0 + 1, z, 'minecraft:air')
    t.set(x0, Y0, z0, c('pearl_block'))
    t.set(x0, Y0 + 1, z0, c('pearl_block'))
    t.set(x0, Y0 + 2, z0, 'minecraft:light', level=15, waterlogged=False)


def throne(t):
    """Престол: площадь из жемчуга и золота, ступени, столб света. Без фигуры."""
    pearl, gold = c('pearl_block'), c('golden_street')
    for x in range(C - 6, C + 7):
        for z in range(C - 6, C + 7):
            d = math.hypot(x - C, z - C)
            if d <= 6.4:
                t.set(x, Y0, z, pearl if int(d) % 2 == 0 else gold)
                for y in range(Y0 + 1, Y0 + 8):
                    t.set(x, y, z, 'minecraft:air')
    for k, (r, block) in enumerate(((3, pearl), (2, gold), (1, pearl))):
        for x in range(C - r, C + r + 1):
            for z in range(C - r, C + r + 1):
                t.set(x, Y0 + 1 + k, z, block)
    t.set(C, Y0 + 4, C, c('throne_light'))


def main():
    blocks()
    city()
    lang_patch({
        'block.celestial.jasper_block': ('Яспис', 'Jasper'),
        'block.celestial.pearl_block': ('Жемчуг врат', 'Gate Pearl'),
        'block.celestial.golden_street': ('Золотая мостовая', 'Golden Street'),
        'block.celestial.foundation_stone': ('Камень основания', 'Foundation Stone'),
        'block.celestial.throne_light': ('Свет престола', 'Light of the Throne'),
        'jerusalem.celestial.title': ('Новый Иерусалим', 'New Jerusalem'),
        'jerusalem.celestial.subtitle': ('Ворота его не будут запираться', 'Its gates shall not be shut'),
        'jerusalem.celestial.welcome.1': ('Город сошёл с неба, сияя, как кристалл.', 'The city came down out of heaven, shining like crystal.'),
        'jerusalem.celestial.welcome.2': ('Посреди улицы — река и Древо Жизни.', 'In the midst of the street — the river and the Tree of Life.'),
        'jerusalem.celestial.welcome.3': ('Свет престола проводит тебя домой.', 'The light of the throne will lead you home.'),
        'jerusalem.celestial.leave': ('Свет мягко опускает тебя на землю.', 'The light gently sets you down on the earth.'),
        'structure.celestial.new_jerusalem': ('Новый Иерусалим', 'New Jerusalem'),
        'codex.celestial.place.new_jerusalem': (
            'город из ясписа и золота, сошедший в Астрал после светлой концовки: двенадцать жемчужных ворот, двенадцать камней основания, '
            'река воды жизни и Древа Жизни по её берегам. Попасть — ПКМ по Звёздному алтарю, домой — свет престола.',
            'a city of jasper and gold that came down into the Astral after a bright ending: twelve pearl gates, twelve foundation stones, '
            'the river of the water of life and Trees of Life on its banks. Reach it by using the Star Altar; the light of the throne leads home.'),
    })
    print('ok: Новый Иерусалим')


if __name__ == '__main__':
    main()
