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
    for x in range(30, 37):
        for z in range(16, 27):
            if math.hypot(x - 33, (z - 21) * 0.8) <= 3.6 and abs(z - CZ) > 1:
                t.set(x, TOP, z, 'minecraft:water', level=0)
    # Древо Жизни: толстый ствол, ветви, золотая крона, плоды
    for y in range(TOP + 1, TOP + 13):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) + abs(dz) <= 1 or y < TOP + 4:
                    t.set(CX + dx, y, CZ + dz, log, axis='y')
    cy = TOP + 15
    for x in range(CX - 10, CX + 11):
        for y in range(cy - 6, cy + 6):
            for z in range(CZ - 10, CZ + 11):
                d = math.sqrt(((x - CX) / 9.5) ** 2 + ((y - cy) / 5.2) ** 2 + ((z - CZ) / 9.5) ** 2)
                if d <= 1.0 and rng.random() > 0.08:
                    t.set(x, y, z, leaves, distance=1, persistent=True, waterlogged=False)
    for y in range(TOP + 13, cy + 1):
        t.set(CX, y, CZ, log, axis='y')
    placed = 0
    for k in range(40):
        a = rng.random() * 2 * math.pi
        rr = rng.uniform(2.5, 7.5)
        x, z = round(CX + math.cos(a) * rr), round(CZ + math.sin(a) * rr)
        for y in range(cy - 6, cy):
            if t.get(x, y, z) == leaves and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                t.set(x, y - 1, z, c('life_fruit'), ripe=True)
                placed += 1
                break
        if placed >= 8:
            break
    # Древо Познания: корявое тёмное дерево в терновнике (юго-запад)
    kx, kz = 9, 31
    dark_log, dark_leaves = 'minecraft:dark_oak_log', 'minecraft:dark_oak_leaves'
    for y in range(TOP + 1, TOP + 8):
        t.set(kx, y, kz, dark_log, axis='y')
        if y > TOP + 3:
            t.set(kx + (1 if y % 2 else -1), y, kz, dark_log, axis='x')
    for x in range(kx - 4, kx + 5):
        for y in range(TOP + 6, TOP + 12):
            for z in range(kz - 4, kz + 5):
                d = math.sqrt(((x - kx) / 4) ** 2 + ((y - (TOP + 8.5)) / 2.8) ** 2 + ((z - kz) / 4) ** 2)
                if d <= 1.0 and rng.random() > 0.2:
                    t.set(x, y, z, dark_leaves, distance=1, persistent=True, waterlogged=False)
    placed = 0
    for k in range(30):
        a = rng.random() * 2 * math.pi
        rr = rng.uniform(1.5, 3.2)
        x, z = round(kx + math.cos(a) * rr), round(kz + math.sin(a) * rr)
        for y in range(TOP + 6, TOP + 9):
            if t.get(x, y, z) == dark_leaves and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                t.set(x, y - 1, z, c('knowledge_fruit'), ripe=True)
                placed += 1
                break
        if placed >= 4:
            break
    for x in range(kx - 5, kx + 6):  # терновник сплошным кольцом
        for z in range(kz - 5, kz + 6):
            if 2.4 <= math.hypot(x - kx, z - kz) <= 4.4 and t.get(x, TOP, z) not in (None, 'minecraft:air') and t.get(x, TOP + 1, z) in (None, 'minecraft:air'):
                t.set(x, TOP + 1, z, 'minecraft:sweet_berry_bush', age=3)
    # кусты смоковницы у входа в терновник; цветы и трава
    for x, z in ((14, 30), (13, 35), (6, 24), (17, 26)):
        t.set(x, TOP + 1, z, c('fig_bush'))
    for _ in range(90):
        x, z = rng.randrange(2, SIZE - 2), rng.randrange(2, SIZE - 2)
        if t.get(x, TOP, z) == c('golden_grass') and t.get(x, TOP + 1, z) in (None, 'minecraft:air') and math.hypot(x - kx, z - kz) > 5.5:
            t.set(x, TOP + 1, z, c(rng.choice(['sunbell', 'dawn_poppy', 'starflower', 'golden_tuft', 'golden_tuft'])))
    # восточные врата: проём из светлого камня (Херувим и меч — отдельная задача S2.5)
    for z in (CZ - 3, CZ + 3):
        t.fill(39, TOP + 1, z, 39, TOP + 5, z, c('radiant_stone'))
    t.fill(39, TOP + 6, CZ - 3, 39, TOP + 6, CZ + 3, c('skystone_bricks'))
    t.fill(38, TOP + 7, CZ - 1, 40, TOP + 7, CZ + 1, c('radiant_stone'))
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
    fruits = garden()
    scenario(fruits)
    lang()
    print('ok: Сад Начала')


if __name__ == '__main__':
    main()
