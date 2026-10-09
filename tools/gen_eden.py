"""Сад Начала (LORE §7, S2.4): постройка-ориентир Рая с Древом Жизни и Древом Познания, плоды, лист смоковницы, манна, эффект «Изгнание».

Блоки: life_fruit, knowledge_fruit (block/eden/FruitBlock), fig_bush (куст смоковницы), manna_dew (роса-манна, Manna).
Предметы: fig_leaf, manna. Эффект: exile. Постройка: eden_garden (в наборе heaven_landmarks, тег codex_places).
"""
import math
import os
import random

from PIL import Image, ImageDraw

import textures as T
from gen_abyss import append_tag
from gen_assets import DATA, ASSETS, blockstate, c, item_def, loot, model, save_png, write_json
from gen_story import lang_patch
from gen_structures import Template, island_base

rgb = T.hexrgb


# ------------------------------------------------------------------ текстуры и модели
def fruit(name, base, light, dark, glow_pts):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 14, 14], fill=rgb(base), outline=rgb(dark))
    d.ellipse([3, 3, 8, 7], fill=rgb(light))
    for x, y in glow_pts:
        img.putpixel((x, y), (255, 255, 255, 255))
    save_png(img, 'block/' + name)


def bud(name, base, dark):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 11, 11], fill=rgb(base), outline=rgb(dark))
    save_png(img, 'block/' + name)


def blocks():
    fruit('life_fruit', '#f2c243', '#fff2a8', '#a8741c', [(4, 4), (9, 10)])
    bud('life_fruit_bud', '#7fae4a', '#3f6a24')
    fruit('knowledge_fruit', '#c8302a', '#f0705a', '#5a1410', [(4, 4)])
    bud('knowledge_fruit_bud', '#6a7a3a', '#3a4a1a')
    stem = Image.new('RGBA', (16, 16), rgb('#5a3f1c') + (255,))
    save_png(stem, 'block/fruit_stem')
    for name in ('life_fruit', 'knowledge_fruit'):
        for ripe in (True, False):
            tex = name if ripe else name + '_bud'
            fruit_el = ({'from': [4, 5, 4], 'to': [12, 13, 12]} if ripe else {'from': [6, 8, 6], 'to': [10, 12, 10]})
            faces = {d: {'texture': '#fruit', 'uv': [0, 0, 16, 16]} for d in ('north', 'south', 'east', 'west', 'up', 'down')}
            model(f'block/{name}{"" if ripe else "_unripe"}', {
                'textures': {'fruit': c('block/' + tex), 'stem': c('block/fruit_stem'), 'particle': c('block/' + tex)},
                'elements': [{**fruit_el, 'faces': faces},
                             {'from': [7.5, fruit_el['to'][1], 7.5], 'to': [8.5, 16, 8.5],
                              'faces': {d: {'texture': '#stem'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}}]})
        blockstate(name, {'variants': {'ripe=true': {'model': c(f'block/{name}')}, 'ripe=false': {'model': c(f'block/{name}_unripe')}}})
        item_def(name, c(f'block/{name}'))
    # куст смоковницы
    r = T.rng_for('fig_bush')
    bush = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = bush.load()
    for y in range(4, 16):
        for x in range(2, 14):
            if math.hypot(x - 8, (y - 10) * 1.3) < 5.5 and r.random() > 0.15:
                px[x, y] = (*T.shade(rgb('#4f8a3a'), 0.85 + r.random() * 0.4), 255)
    for x, y in ((6, 9), (10, 8), (8, 12), (5, 12)):
        px[x, y] = (*rgb('#8a4a7a'), 255)
    save_png(bush, 'block/fig_bush')
    model('block/fig_bush', {'parent': 'minecraft:block/cross', 'textures': {'cross': c('block/fig_bush')}})
    blockstate('fig_bush', {'variants': {'': {'model': c('block/fig_bush')}}})
    model('item/fig_bush', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('block/fig_bush')}})
    item_def('fig_bush', c('item/fig_bush'))
    loot('fig_bush', [{'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('fig_leaf'), 'modifier': [
        {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 1, 'max': 2}}]}]}])
    # роса-манна: плоская россыпь на траве и предмет
    dew = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = T.rng_for('manna_dew')
    for _ in range(46):
        x, y = r.randrange(1, 15), r.randrange(1, 15)
        dew.putpixel((x, y), (*rgb(r.choice(['#fffbe6', '#f6ecc0', '#ffffff'])), 255))
    save_png(dew, 'block/manna_dew')
    model('block/manna_dew', {'textures': {'dew': c('block/manna_dew'), 'particle': c('block/manna_dew')}, 'elements': [
        {'from': [0, 0, 0], 'to': [16, 0.5, 16], 'faces': {'up': {'texture': '#dew'}, 'down': {'texture': '#dew'}}}]})
    blockstate('manna_dew', {'variants': {'': {'model': c('block/manna_dew')}}})
    model('item/manna_dew', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/manna')}})
    item_def('manna_dew', c('item/manna_dew'))
    loot('manna_dew', [{'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('manna'), 'modifier': [
        {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 1, 'max': 2}}]}]}])
    # предметы
    leaf = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(leaf)
    d.polygon([(8, 1), (11, 4), (14, 5), (12, 8), (13, 11), (9, 11), (8, 15), (7, 11), (3, 11), (4, 8), (2, 5), (5, 4)], fill=rgb('#5a9a3a'), outline=rgb('#2f5a1c'))
    d.line([(8, 2), (8, 14)], fill=rgb('#a8d070'))
    for p in ((5, 6), (11, 6), (5, 9), (11, 9)):
        d.line([(8, 8), p], fill=rgb('#a8d070'))
    save_png(leaf, 'item/fig_leaf')
    model('item/fig_leaf', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/fig_leaf')}})
    item_def('fig_leaf', c('item/fig_leaf'))
    wafer = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(wafer)
    for cx, cy in ((5, 9), (10, 7), (8, 12)):
        d.ellipse([cx - 3, cy - 2, cx + 3, cy + 2], fill=rgb('#f6ecc0'), outline=rgb('#b89a50'))
        wafer.putpixel((cx - 1, cy - 1), (255, 255, 255, 255))
    save_png(wafer, 'item/manna')
    model('item/manna', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/manna')}})
    item_def('manna', c('item/manna'))
    # стена Эдема: крупные плиты белого мрамора с золотыми прожилками и золотым швом (раньше — песчаник)
    r = T.rng_for('eden_wall_marble')
    wall = T.noisy('eden_wall', [rgb(h) for h in ('#ece6d8', '#f4efe4', '#e2dccb', '#faf6ee')], cell=2, grain=0.3).convert('RGBA')
    px = wall.load()
    for y in range(16):
        for x in range(16):
            if y in (0, 8) or (x == 0 and y < 8) or (x == 8 and y >= 8):
                px[x, y] = (*rgb('#c9a24a'), 255)  # золотой шов плит
    for start in ((2, 2), (11, 10), (4, 12)):  # прожилки: короткие косые нити
        x, y = start
        for _ in range(6):
            if 0 < x < 16 and 0 < y < 16 and y not in (0, 8):
                px[x, y] = (*rgb(r.choice(['#d8b864', '#c9a24a', '#e8cf8a'])), 255)
            x += r.choice([1, 1, 0])
            y += r.choice([1, 0, -1])
    save_png(wall, 'block/eden_wall')
    model('block/eden_wall', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/eden_wall')}})
    blockstate('eden_wall', {'variants': {'': {'model': c('block/eden_wall')}}})
    item_def('eden_wall', c('block/eden_wall'))
    append_tag('block', 'minecraft:dragon_immune', [c('eden_wall')])
    append_tag('block', 'minecraft:wither_immune', [c('eden_wall')])
    # значок эффекта «Изгнание»: пламенный меч, повёрнутый остриём вниз
    icon = Image.new('RGBA', (18, 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(icon)
    d.polygon([(8, 15), (10, 15), (10, 4), (9, 2), (8, 4)], fill=rgb('#e8d8b0'), outline=rgb('#6a4a24'))
    d.rectangle([5, 4, 13, 5], fill=rgb('#c9a23a'))
    d.rectangle([8, 1, 9, 3], fill=rgb('#8a5a24'))
    for x, y in ((6, 11), (12, 9), (5, 8), (13, 12)):
        d.rectangle([x, y, x + 1, y + 1], fill=rgb('#ff9a3a'))
    save_png(icon, 'mob_effect/exile')
    append_tag('block', 'minecraft:dragon_immune', [c('life_fruit'), c('knowledge_fruit')])
    append_tag('block', 'minecraft:wither_immune', [c('life_fruit'), c('knowledge_fruit')])


# ------------------------------------------------------------------ постройка
TOP = 8
SIZE = 43
CX = CZ = 21


def garden():
    rng = random.Random(7700)
    t = Template(SIZE, 34, SIZE)
    t.fill(0, 0, 0, SIZE - 1, 33, SIZE - 1, 'minecraft:air')
    island_base(t, CX, CZ, 20, TOP, 9, rng)
    log, leaves = c('skywood_log'), c('skywood_leaves')
    # дорожки из светлых кирпичей: крест к Древу Жизни; пруд на востоке
    for i in range(2, SIZE - 2):
        for w in (CX - 1, CX, CX + 1):
            for x, z in ((i, w), (w, i)):
                if math.hypot(x - CX, z - CZ) <= 19.5:
                    t.set(x, TOP, z, c('skystone_bricks'))
    for x in range(26, 36):
        for z in range(4, 13):
            if math.hypot(x - 30, (z - 8) * 0.8) <= 3.6:
                t.set(x, TOP, z, 'minecraft:water', level=0)
    # Древо Жизни: могучий ствол из коры с корнями-контрфорсами, ветви во все стороны, многоярусная золото-белая крона
    # со светом внутри и светящимися лианами, плоды висят под кроной. Правка качества (приёмка K1): раньше — столб и шар.
    wood, leaves, blossom = c('skywood_wood'), c('skywood_leaves'), c('cloud_willow_leaves')

    def line(p0, p1, block, width=0):
        n = int(max(abs(p1[i] - p0[i]) for i in range(3)) * 2) + 1
        for i in range(n + 1):
            q = [p0[j] + (p1[j] - p0[j]) * i / n for j in range(3)]
            for dx in range(-width, width + 1):
                for dz in range(-width, width + 1):
                    if abs(dx) + abs(dz) <= width:
                        t.set(round(q[0]) + dx, round(q[1]), round(q[2]) + dz, block, axis='y')

    def cluster(x0, y0, z0, rx, ry, mix_rng):
        for x in range(int(x0 - rx) - 1, int(x0 + rx) + 2):
            for y in range(int(y0 - ry) - 1, int(y0 + ry) + 2):
                for z in range(int(z0 - rx) - 1, int(z0 + rx) + 2):
                    d = ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2 + ((z - z0) / rx) ** 2
                    if d <= 1.0 and mix_rng.random() > 0.06 * (1 + d * 2) and t.get(x, y, z) in (None, 'minecraft:air'):
                        t.set(x, y, z, blossom if mix_rng.random() < 0.18 else leaves)

    trunk_top = TOP + 13
    for y in range(TOP + 1, trunk_top + 1):
        k = (y - TOP) / (trunk_top - TOP)
        rad = 2.6 - 1.4 * k
        ox, oz = math.sin(y * 0.35) * 0.6, math.cos(y * 0.3) * 0.6  # лёгкий изгиб ствола
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if math.hypot(dx - ox, dz - oz) <= rad:
                    t.set(CX + dx, y, CZ + dz, wood, axis='y')
    for i in range(7):  # корни-контрфорсы расходятся и уходят в землю
        ang = i / 7 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        ln = rng.uniform(4.5, 7.0)
        line((CX + math.cos(ang) * 1.8, TOP + 3, CZ + math.sin(ang) * 1.8),
             (CX + math.cos(ang) * ln, TOP, CZ + math.sin(ang) * ln), wood)
    tips = []
    for i in range(7):  # ветви
        ang = i / 7 * 2 * math.pi + rng.uniform(-0.25, 0.25)
        y_start = TOP + rng.randint(8, 12)
        ln, rise = rng.uniform(6.5, 9.5), rng.uniform(4, 7)
        mid = (CX + math.cos(ang) * ln * 0.5, y_start + rise * 0.7, CZ + math.sin(ang) * ln * 0.5)
        tip = (CX + math.cos(ang) * ln, y_start + rise, CZ + math.sin(ang) * ln)
        line((CX, y_start, CZ), mid, wood)
        line(mid, tip, wood)
        tips.append(tip)
    line((CX, trunk_top, CZ), (CX, trunk_top + 4, CZ), wood)
    canopy_rng = random.Random(7701)
    cluster(CX, trunk_top + 6, CZ, 6.5, 4.2, canopy_rng)
    for x0, y0, z0 in tips:
        cluster(x0, y0 + 1, z0, rng.uniform(3.8, 4.8), rng.uniform(2.6, 3.2), canopy_rng)
    for _ in range(14):  # свет внутри кроны (невидимые источники) — Древо светится ночью
        x0, y0, z0 = rng.choice(tips + [(CX, trunk_top + 6, CZ)])
        x, y, z = round(x0 + rng.uniform(-2, 2)), round(y0 + rng.uniform(-1, 1)), round(z0 + rng.uniform(-2, 2))
        if t.get(x, y, z) in (leaves, blossom):
            t.set(x, y, z, 'minecraft:light', level=12, waterlogged=False)
    hang = 0
    for _ in range(400):  # светящиеся лианы свисают из-под кроны
        x, z = CX + rng.randint(-11, 11), CZ + rng.randint(-11, 11)
        for y in range(trunk_top + 12, TOP + 6, -1):
            if t.get(x, y, z) in (leaves, blossom) and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                n = rng.randint(1, 4)
                for j in range(1, n + 1):
                    if t.get(x, y - j, z) not in (None, 'minecraft:air'):
                        break
                    t.set(x, y - j, z, c('lumivine'), tip=(j == n))
                hang += 1
                break
        if hang >= 26:
            break
    placed = 0
    for k in range(200):
        x0, y0, z0 = rng.choice(tips)
        x, z = round(x0 + rng.uniform(-3, 3)), round(z0 + rng.uniform(-3, 3))
        for y in range(round(y0) + 3, round(y0) - 4, -1):
            if t.get(x, y, z) in (leaves, blossom) and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                t.set(x, y - 1, z, c('life_fruit'), ripe=True)
                placed += 1
                break
        if placed >= 8:
            break
    # Древо Познания: корявый ствол винтом (будто его обвил змей), голые сучья вниз, тёмная редкая крона; земля под ним голая
    kx, kz = 9, 31
    dark_wood, dark_leaves = 'minecraft:dark_oak_wood', 'minecraft:dark_oak_leaves'
    for x in range(kx - 2, kx + 3):
        for z in range(kz - 2, kz + 3):
            if math.hypot(x - kx, z - kz) <= 2.3 and t.get(x, TOP, z) == c('golden_grass'):
                t.set(x, TOP, z, c('heaven_dirt'))
    for y in range(TOP + 1, TOP + 10):
        a = (y - TOP) * 0.75
        ox, oz = round(math.cos(a) * 1.1), round(math.sin(a) * 1.1)
        t.set(kx + ox, y, kz + oz, dark_wood, axis='y')
        t.set(kx, y, kz, dark_wood, axis='y')
    k_tips = []
    for i in range(5):
        ang = i / 5 * 2 * math.pi + 0.4
        start = (kx, TOP + 7 + i % 2, kz)
        elbow = (kx + math.cos(ang) * 3, TOP + 10, kz + math.sin(ang) * 3)
        tip = (kx + math.cos(ang) * 5.5, TOP + 8, kz + math.sin(ang) * 5.5)  # сучья клонятся вниз
        line(start, elbow, dark_wood)
        line(elbow, tip, dark_wood)
        k_tips.append(elbow)
    k_rng = random.Random(7702)
    for x0, y0, z0 in k_tips:
        for x in range(round(x0) - 3, round(x0) + 4):
            for y in range(round(y0) - 1, round(y0) + 3):
                for z in range(round(z0) - 3, round(z0) + 4):
                    d = ((x - x0) / 2.8) ** 2 + ((y - y0 - 0.5) / 1.6) ** 2 + ((z - z0) / 2.8) ** 2
                    if d <= 1.0 and k_rng.random() > 0.35 and t.get(x, y, z) in (None, 'minecraft:air'):
                        t.set(x, y, z, dark_leaves, distance=1, persistent=True, waterlogged=False)
    placed = 0
    for k in range(200):
        x0, y0, z0 = k_tips[k % len(k_tips)]
        x, z = round(x0 + rng.uniform(-2, 2)), round(z0 + rng.uniform(-2, 2))
        for y in range(round(y0) + 2, round(y0) - 3, -1):
            if t.get(x, y, z) == dark_leaves and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                t.set(x, y - 1, z, c('knowledge_fruit'), ripe=True)
                placed += 1
                break
        if placed >= 4:
            break
    # Отпечаток света у ствола (Отблеск «Плод», docs/LORE.md §5c): коснись — и увидишь, как это было
    t.set(kx + 2, TOP + 1, kz, c('memory_anchor'), nbt={'id': c('memory_anchor'), 'Scene': 'fruit'})
    for x in range(kx - 5, kx + 6):  # терновник сплошным кольцом
        for z in range(kz - 5, kz + 6):
            if 2.4 <= math.hypot(x - kx, z - kz) <= 4.4 and t.get(x, TOP, z) not in (None, 'minecraft:air') and t.get(x, TOP + 1, z) in (None, 'minecraft:air'):
                t.set(x, TOP + 1, z, 'minecraft:sweet_berry_bush', age=3)
    # кусты смоковницы у входа в терновник; цветы и трава
    for x, z in ((14, 30), (13, 35), (6, 24), (17, 26)):
        t.set(x, TOP + 1, z, c('fig_bush'))
    for _ in range(260):
        x, z = rng.randrange(2, SIZE - 2), rng.randrange(2, SIZE - 2)
        if t.get(x, TOP, z) == c('golden_grass') and t.get(x, TOP + 1, z) in (None, 'minecraft:air') and math.hypot(x - kx, z - kz) > 5.5:
            t.set(x, TOP + 1, z, c(rng.choice(['sunbell', 'dawn_poppy', 'starflower', 'golden_tuft', 'golden_tuft'])))
    # Восточные врата: двор Херувима. Стены неразрушимы, внутри лезвие метёт круг радиусом 6,5 — обойти его нельзя, только перепрыгнуть в такт
    hx, hz = 34, 21
    for x in range(28, 41):
        for z in range(14, 29):
            t.set(x, TOP, z, c('skystone_bricks'))
            r = math.hypot(x - hx, z - hz)
            if 5.6 <= r <= 6.6 or r <= 1.6:
                t.set(x, TOP, z, c('radiant_stone'))
    for x in range(28, 41):
        for y in range(TOP + 1, TOP + 7):
            t.set(x, y, 14, c('eden_wall'))
            t.set(x, y, 28, c('eden_wall'))
    for z in range(14, 29):
        for y in range(TOP + 1, TOP + 7):
            t.set(28, y, z, c('eden_wall'))
            t.set(40, y, z, c('eden_wall'))
    for x in range(28, 41):  # зубцы поверху — тоже неразрушимые
        for z in (14, 28):
            if x % 2 == 0:
                t.set(x, TOP + 7, z, c('eden_wall'))
    for z in range(14, 29):
        for x in (28, 40):
            if z % 2 == 0:
                t.set(x, TOP + 7, z, c('eden_wall'))
    for x, z in [(x, 13) for x in range(28, 41, 3)] + [(x, 29) for x in range(28, 41, 3)] + \
                [(27, z) for z in range(14, 29, 3)] + [(41, z) for z in range(14, 29, 3) if not 17 <= z <= 25]:
        t.fill(x, TOP + 1, z, x, TOP + 6, z, c('radiant_stone'))  # пилястры снаружи стен
        t.set(x, TOP + 7, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    t.fill(28, TOP + 1, 19, 28, TOP + 4, 23, 'minecraft:air')  # западный вход
    t.fill(40, TOP + 1, 19, 40, TOP + 4, 23, 'minecraft:air')  # восточные врата
    t.fill(40, TOP + 5, 18, 40, TOP + 5, 24, c('radiant_stone'))
    # Восточные врата — высокая арка: столпы, перемычка, светильники и кристалл над проёмом
    for z in (17, 18, 24, 25):
        t.fill(41, TOP + 1, z, 41, TOP + 10, z, c('eden_wall'))
    t.fill(41, TOP + 10, 17, 41, TOP + 10, 25, c('eden_wall'))
    t.fill(41, TOP + 9, 19, 41, TOP + 9, 23, c('radiant_stone'))
    t.set(41, TOP + 11, 21, c('sky_crystal'), facing='up', waterlogged=False)
    for z in (17, 25):
        t.set(41, TOP + 11, z, 'minecraft:lantern', hanging=False, waterlogged=False)
    t.set(41, TOP, hz, c('trial_goal'))
    t.set(29, TOP + 1, 16, c('trial_crystal'), nbt={'id': c('trial_crystal'), 'Trial': 'eden_gate'}, state='idle')
    t.entity(hx, TOP + 1, hz, {'id': c('gate_cherub'), 'PersistenceRequired': True})
    fruits = {n: [(x, y, z) for (x, y, z), (b, *_r) in sorted(t.blocks.items()) if b == c(n)] for n in ('life_fruit', 'knowledge_fruit')}
    t.save('eden_garden/main')
    write_json(os.path.join(DATA, 'worldgen/template_pool/eden_garden/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c('eden_garden/main'),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}}]})
    write_json(os.path.join(DATA, 'worldgen/structure/eden_garden.json'), {
        'type': 'minecraft:jigsaw', 'biomes': '#' + c('has_structure/eden_garden'), 'max_distance_from_center': 80, 'size': 1,
        'spawn_overrides': {}, 'start_height': {'absolute': 120}, 'start_pool': c('eden_garden/main'), 'step': 'surface_structures',
        'terrain_adaptation': 'none', 'use_expansion_hack': False})
    write_json(os.path.join(DATA, 'tags/worldgen/biome/has_structure/eden_garden.json'),
               {'values': [c(b) for b in ('golden_meadows', 'heaven_gardens', 'star_glade', 'cloud_forest')]})
    append_tag('worldgen/structure', 'celestial:codex_places', [c('eden_garden')])
    return fruits


# ------------------------------------------------------------------ Херувим Восточных врат: текстура 64×128 по HeavenModels.GateCherub
def gate_cherub_textures():
    import mob_textures as M
    from gen_heaven_mobs import WHITE
    r = T.rng_for('gate_cherub')
    img = Image.new('RGBA', (64, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 128), (0, 0, 0, 0))

    def face_man():
        f = Image.new('RGBA', (10, 10), rgb('#e8c9a5') + (255,))
        d = ImageDraw.Draw(f)
        d.rectangle([0, 0, 9, 2], fill=rgb('#6a4a24'))
        d.rectangle([0, 0, 1, 6], fill=rgb('#6a4a24'))
        d.rectangle([8, 0, 9, 6], fill=rgb('#6a4a24'))
        for x in (3, 6):
            d.point((x, 4), fill=rgb('#2a4a8a'))
            d.point((x - 1, 4), fill=WHITE)
        d.line([(4, 7), (5, 7)], fill=rgb('#a86a5a'))
        return f

    def face_lion():
        f = Image.new('RGBA', (10, 10), rgb('#d9a441') + (255,))
        d = ImageDraw.Draw(f)
        d.rectangle([0, 0, 9, 9], outline=rgb('#8a5a1c'))
        d.rectangle([1, 1, 8, 1], fill=rgb('#a87028'))
        for x in (2, 6):
            d.rectangle([x, 3, x + 1, 4], fill=rgb('#3a2a10'))
        d.rectangle([4, 5, 5, 6], fill=rgb('#5a3a1a'))
        d.line([(3, 8), (6, 8)], fill=rgb('#8a5a1c'))
        return f

    def face_ox():
        f = Image.new('RGBA', (10, 10), rgb('#7a4a28') + (255,))
        d = ImageDraw.Draw(f)
        d.rectangle([0, 0, 1, 2], fill=rgb('#efe7cf'))
        d.rectangle([8, 0, 9, 2], fill=rgb('#efe7cf'))
        d.rectangle([2, 6, 7, 9], fill=rgb('#b88a62'))
        for x in (3, 6):
            d.point((x, 4), fill=rgb('#1a1008'))
            d.point((x, 8), fill=rgb('#4a2a14'))
        return f

    def face_eagle():
        f = Image.new('RGBA', (10, 10), rgb('#5a3f2a') + (255,))
        d = ImageDraw.Draw(f)
        d.rectangle([0, 0, 9, 5], fill=rgb('#f4f0e6'))
        for x in (2, 7):
            d.point((x, 3), fill=rgb('#ffcc33'))
        d.polygon([(4, 4), (5, 4), (6, 7), (4, 9), (3, 7)], fill=rgb('#f0b03a'))
        return f

    faces = {'front': face_man(), 'right': face_lion(), 'back': face_ox(), 'left': face_eagle()}

    def head(face, x, y, fw, fh):
        if face in faces:
            return faces[face].getpixel((x, y))
        return M.noise_color(r, rgb('#e6c46a'), 0.08)

    def head_glow(face, x, y, fw, fh):
        if face in faces:
            px = faces[face].getpixel((x, y))
            if px[:3] in (rgb('#ffcc33'), rgb('#3a2a10')) and face in ('left', 'right'):
                return (255, 214, 90, 255)
        return None

    def body(face, x, y, fw, fh):
        if y in (3, fh - 3):
            return rgb('#e0b54a')
        if face == 'front' and fw // 2 - 1 <= x <= fw // 2:
            return rgb('#e0b54a')
        return M.noise_color(r, rgb('#f2ecd6'), 0.05) if x % 3 else M.noise_color(r, rgb('#ddd5ba'), 0.05)

    eyes = {(c0, c1) for c0, c1 in ((3, 3), (7, 6), (4, 9), (8, 11), (2, 13), (6, 15), (9, 5), (5, 12))}

    def wing(face, x, y, fw, fh):
        if face in ('left', 'right'):
            if (x, y) in eyes:
                return rgb('#3a8ae0')  # крылья, «полные очей» (Иез. 1:18)
            row = y // 3
            c0 = T.shade(rgb('#f4efe0'), 1.0 - 0.04 * row)
            return T.shade(c0, 0.88) if y % 3 == 2 else c0
        return rgb('#cfc7ac')

    def wing_glow(face, x, y, fw, fh):
        return (120, 190, 255, 255) if face in ('left', 'right') and (x, y) in eyes else None

    def blade(face, x, y, fw, fh):
        t = (y % 12) / 12
        base = mix_col(rgb('#ff5a1a'), rgb('#ffe27a'), 0.5 + 0.5 * math.sin(y / 3.0)) if face != 'top' else rgb('#fff6c0')
        return M.noise_color(r, base, 0.04) if t else rgb('#fff6c0')

    def mix_col(a, b, k):
        return tuple(int(a[i] * (1 - k) + b[i] * k) for i in range(3))

    M.paint_box(img, 0, 0, 10, 10, 10, head)
    M.paint_box(glow, 0, 0, 10, 10, 10, head_glow)
    M.paint_box(img, 0, 20, 12, 24, 8, body)
    M.paint_box(img, 40, 0, 1, 16, 11, wing)
    M.paint_box(glow, 40, 0, 1, 16, 11, wing_glow)
    M.paint_box(img, 50, 36, 3, 65, 4, blade)
    M.paint_box(glow, 50, 36, 3, 65, 4, lambda f, x, y, fw, fh: (*blade(f, x, y, fw, fh), 255))
    save_png(img, 'entity/gate_cherub')
    save_png(glow, 'entity/gate_cherub_glow')
    save_png(M.spawn_egg('#f2ecd6', '#ff7a2a'), 'item/gate_cherub_spawn_egg')
    model('item/gate_cherub_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/gate_cherub_spawn_egg')}})
    item_def('gate_cherub_spawn_egg', c('item/gate_cherub_spawn_egg'))
    write_json(os.path.join(DATA, 'loot_table/chests/trial_eden_gate.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/trial_eden_gate'), 'pools': [
            {'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('fig_leaf'), 'modifier': [
                {'type': 'minecraft:set_count', 'count': 2}]}]},
            {'rolls': 2, 'entries': [
                {'type': 'minecraft:item', 'name': c('starquartz'), 'weight': 5, 'modifier': [
                    {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 2, 'max': 5}}]},
                {'type': 'minecraft:item', 'name': c('etherite_ingot'), 'weight': 3, 'modifier': [
                    {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 1, 'max': 2}}]},
                {'type': 'minecraft:item', 'name': c('manna'), 'weight': 4, 'modifier': [
                    {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 2, 'max': 4}}]}]}]})


def lang():
    e = {
        'block.celestial.life_fruit': ('Плод Жизни', 'Fruit of Life'),
        'block.celestial.life_fruit.lore1': ('ПКМ — вкусить: полное исцеление и Благодать.', 'Use to taste: full healing and Grace.'),
        'block.celestial.life_fruit.lore2': ('Созревает снова через игровую неделю. Изгнанным недоступен.', 'Ripens again after a game week. Closed to the exiled.'),
        'block.celestial.knowledge_fruit': ('Плод Познания', 'Fruit of Knowledge'),
        'block.celestial.knowledge_fruit.lore1': ('ПКМ — вкусить: много опыта, но Изгнание на 10 минут.', 'Use to taste: great experience, but Exile for 10 minutes.'),
        'block.celestial.knowledge_fruit.lore2': ('Лист смоковницы в инвентаре принимает Изгнание на себя.', 'A fig leaf in your inventory takes the Exile in your stead.'),
        'block.celestial.fig_bush': ('Куст смоковницы', 'Fig Bush'),
        'block.celestial.manna_dew': ('Роса-манна', 'Manna Dew'),
        'block.celestial.manna_dew.lore1': ('Выпадает утром на траву Рая; к полудню тает.', 'Falls on the grass of Heaven at dawn; melts by noon.'),
        'item.celestial.fig_leaf': ('Лист смоковницы', 'Fig Leaf'),
        'item.celestial.fig_leaf.lore1': ('ПКМ — снять Изгнание.', 'Use to lift the Exile.'),
        'item.celestial.fig_leaf.lore2': ('В инвентаре принимает Изгнание вместо тебя.', 'In your inventory it takes the Exile instead of you.'),
        'item.celestial.manna': ('Манна', 'Manna'),
        'effect.celestial.exile': ('Изгнание', 'Exile'),
        'eden.celestial.fruit.unripe': ('Плод ещё не созрел.', 'The fruit is not ripe yet.'),
        'eden.celestial.fruit.exiled': ('Древо закрыто для изгнанных.', 'The Tree is closed to the exiled.'),
        'eden.celestial.fruit.life': ('Сила и свет вернулись к тебе.', 'Strength and light have returned to you.'),
        'eden.celestial.fruit.knowledge': ('Глаза открылись — и Сад отвернулся от тебя.', 'Your eyes are opened, and the Garden turns from you.'),
        'eden.celestial.fruit.leaf': ('Лист смоковницы прикрыл тебя: Изгнания нет.', 'The fig leaf covered you: no Exile.'),
        'eden.celestial.leaf.nothing': ('Тебе нечего скрывать.', 'You have nothing to hide.'),
        'eden.celestial.leaf.covered': ('Лист прикрыл тебя: Изгнание снято.', 'The leaf covers you: the Exile is lifted.'),
        'eden.celestial.cold': ('Ангел отводит взгляд: на тебе печать Изгнания.', 'The angel turns away: you bear the mark of Exile.'),
        'block.celestial.eden_wall': ('Стена Эдема', 'Wall of Eden'),
        'entity.celestial.gate_cherub': ('Херувим Восточных врат', 'Cherub of the East Gate'),
        'entity.celestial.gate_cherub.line': ('Херувим молчит. Меч обращается сам, и каждый шаг нужно сделать в такт.', 'The Cherub is silent. The sword turns by itself, and every step must keep its time.'),
        'entity.celestial.gate_cherub.hit': ('Пламенный меч отбросил тебя. Выжди его оборот и перепрыгни.', 'The flaming sword threw you back. Wait out its turn and leap over it.'),
        'entity.celestial.gate_cherub.spared': ('Меч не тронул тебя: в тебе достаточно Благодати.', 'The sword spared you: there is Grace enough in you.'),
        'item.celestial.gate_cherub_spawn_egg': ('Яйцо призыва: Херувим врат', 'Gate Cherub Spawn Egg'),
        'trial.celestial.name.eden_gate': ('Восточные врата', 'The East Gate'),
        'structure.celestial.eden_garden': ('Сад Начала', 'Garden of the Beginning'),
        'codex.celestial.place.eden_garden': ('поднятый в небо Сад: Древо Жизни, Древо Познания в терновнике, кусты смоковницы. Утром здесь выпадает манна.',
                                              'the Garden raised into the sky: the Tree of Life, the Tree of Knowledge in thorns, fig bushes. Manna falls here at dawn.'),
    }
    lang_patch(e)


def scenario(fruits):
    """Сценарий eden_test.txt: постройка, плоды (жизнь, познание, закрытое Древо), лист смоковницы, манна."""
    X, Y0, Z = 32000, 120, 32000
    life = [(X + x, Y0 + y, Z + z) for x, y, z in fruits['life_fruit']]
    know = [(X + x, Y0 + y, Z + z) for x, y, z in fruits['knowledge_fruit']]
    o = ['# S2.4: Сад Начала (генерирует tools/gen_eden.py)',
         '/gamemode creative', '/effect clear @s', '/gamerule spawn_monsters false', '/gamerule advance_time false', '/time set 6000', '/weather clear',
         f'/execute in minecraft:overworld run tp @s {X} 190 {Z}', 'fly', 'wait 60',
         f'/fill {X - 5} {Y0} {Z - 5} {X + 50} {Y0 + 12} {Z + 50} minecraft:air',
         f'/place template celestial:eden_garden/main {X} {Y0} {Z}', 'wait 80', '/kill @e[type=!minecraft:player,distance=..80]',
         '/celestial lore lock all',
         f'/tp @s {X + 21.5} {Y0 + 22} {Z + 44} 180 35', 'togglehud', 'wait 30', 'shot eden_garden_overview',
         f'/tp @s {X + 33} {Y0 + 12} {Z + 21} 90 15', 'wait 20', 'shot eden_tree_of_life',
         f'/tp @s {X + 9.5} {Y0 + 11} {Z + 40} 180 15', 'wait 20', 'shot eden_tree_of_knowledge',
         f'/tp @s {X + 21.5} {Y0 + 10} {Z + 31} 180 -40', 'wait 20', 'shot eden_life_canopy', 'togglehud',
         '/gamemode survival', '/effect give @s minecraft:resistance 900 4 true', '/effect give @s minecraft:slow_falling 900 0 true',
         '/clear @s', '/effect clear @s celestial:exile', '/scoreboard objectives add hp dummy', '/scoreboard objectives add maxhp dummy']
    lx, ly, lz = life[0]
    o += [f'/tp @s {lx + 0.5} {ly - 1} {lz + 0.5}', '/damage @s 12 minecraft:magic', 'wait 5',
          f'use {lx} {ly} {lz} down', 'wait 10',
          '/say TEST F1 life_fruit_heals_and_wilts expect=pass,pass',
          '/execute store result score @s hp run data get entity @s Health',
          '/execute store result score @s maxhp run attribute @s minecraft:max_health get', '/execute if score @s hp = @s maxhp',
          f'/execute if block {lx} {ly} {lz} celestial:life_fruit[ripe=false]']
    kx, ky, kz = know[0]
    o += [f'/tp @s {kx + 0.5} {ky - 1} {kz + 0.5}', 'wait 5', f'use {kx} {ky} {kz} down', 'wait 10',
          '/say TEST F2 knowledge_gives_exile_and_xp expect=pass,pass,pass',
          '/execute if entity @s[nbt={active_effects:[{id:"celestial:exile"}]}]', '/execute if entity @s[level=10..]',
          f'/execute if block {kx} {ky} {kz} celestial:knowledge_fruit[ripe=false]']
    l2 = life[1]
    o += [f'/tp @s {l2[0] + 0.5} {l2[1] - 1} {l2[2] + 0.5}', 'wait 5', f'use {l2[0]} {l2[1]} {l2[2]} down', 'wait 10',
          '/say TEST F3 exiled_cannot_eat_life expect=pass',
          f'/execute if block {l2[0]} {l2[1]} {l2[2]} celestial:life_fruit[ripe=true]',
          '/summon celestial:archangel ~ ~ ~2 {Variant:0,NoAI:1b}', 'wait 5', 'clearchat', 'interact celestial:archangel', 'wait 5',
          '# лист смоковницы снимает Изгнание',
          '/give @s celestial:fig_leaf', '/item replace entity @s weapon.mainhand with celestial:fig_leaf', 'wait 3', 'useitem', 'wait 10',
          '/say TEST F4 leaf_lifts_exile expect=pass',
          '/execute unless entity @s[nbt={active_effects:[{id:"celestial:exile"}]}]']
    if len(know) > 1:
        k2 = know[1]
        o += ['/clear @s', '/give @s celestial:fig_leaf',
              f'/tp @s {k2[0] + 0.5} {k2[1] - 1} {k2[2] + 0.5}', 'wait 5', f'use {k2[0]} {k2[1]} {k2[2]} down', 'wait 10',
              '/say TEST F5 leaf_in_inventory_takes_exile expect=pass,pass',
              '/execute unless entity @s[nbt={active_effects:[{id:"celestial:exile"}]}]',
              '/execute unless items entity @s container.* celestial:fig_leaf']
    o += ['# манна: утром выпадает на траву Рая около игрока, к полудню тает',
          '/gamemode creative', '/effect clear @s', '/time set 23500',
          '/execute in celestial:heaven run tp @s 5000 190 5000', 'wait 60',
          '/execute in celestial:heaven run fill 4970 169 4970 5030 169 5030 celestial:golden_grass',
          '/execute in celestial:heaven run fill 4970 170 4970 5030 190 5030 minecraft:air',
          '/execute in celestial:heaven run tp @s 5000.5 170 5000.5', '/gamemode survival', '/effect give @s minecraft:resistance 600 4 true', 'wait 300',
          '/say TEST M1 manna_fell_at_dawn expect=pass(Заполнено)',
          '/execute in celestial:heaven positioned 4975 170 4975 run fill ~ ~ ~ ~50 ~2 ~50 minecraft:air replace celestial:manna_dew',
          '/execute in celestial:heaven run setblock 5002 170 5002 celestial:manna_dew',
          '/gamerule random_tick_speed 4000', '/time set 8000', 'wait 100', '/gamerule random_tick_speed 3',
          '/say TEST M2 manna_melts_at_noon expect=pass',
          '/execute in celestial:heaven unless block 5002 170 5002 celestial:manna_dew',
          '/gamemode creative', 'quit']
    with open(os.path.join(os.path.dirname(__file__), 'scenarios', 'eden_test.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(o) + '\n')
    print('плоды:', len(life), 'жизни,', len(know), 'познания')


def main():
    blocks()
    gate_cherub_textures()
    fruits = garden()
    scenario(fruits)
    lang()
    print('ok: Сад Начала')


if __name__ == '__main__':
    main()
