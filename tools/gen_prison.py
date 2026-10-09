"""Темница Стражей (LORE §7, S2.6): постройка Бездны на полу пещеры, Нефилим (мини-босс), прикованные Стражи, праща и камни для неё.

Модели: HeavenModels.Nephilim (128×64), узник — модель Ангела в тёмных лохмотьях (текстура chained_watcher).
"""
import math
import os

from PIL import Image, ImageDraw

import mob_textures as M
import textures as T
from gen_abyss import append_tag
from gen_assets import DATA, c, entity_loot, item_def, model, save_png, shapeless, write_json
from gen_story import lang_patch
from gen_structures import Template, chest

rgb = T.hexrgb
MC = lambda n: 'minecraft:' + n  # noqa: E731


# ------------------------------------------------------------------ текстуры
def nephilim():
    r = T.rng_for('nephilim')
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    skin, dark, hair = rgb('#8d7d6b'), rgb('#6a5a4c'), rgb('#2a1f1a')
    belt, wood = rgb('#4a3626'), rgb('#6b4a2b')

    def head(face, x, y, fw, fh):
        if face == 'top' or (face in ('back', 'left', 'right') and y < 3):
            return M.noise_color(r, hair, 0.1)
        if face == 'front':
            if y < 2:
                return M.noise_color(r, hair, 0.1)
            if y in (2, 3) and x in (0, 1, 2, 5, 6, 7):
                return T.shade(dark, 0.7)  # тяжёлая бровь
            if y == 4 and x in (2, 5):
                return rgb('#ff4a2a')
            if y == 6 and 2 <= x <= 5:
                return T.shade(dark, 0.6)  # рот
            if y == 7 and x in (2, 5):
                return rgb('#e8e0cc')  # клыки
        return M.noise_color(r, skin, 0.06)

    def head_glow(face, x, y, fw, fh):
        return (255, 74, 42, 255) if face == 'front' and y == 4 and x in (2, 5) else None

    def body(face, x, y, fw, fh):
        if y >= fh - 3:
            return M.noise_color(r, belt, 0.08)  # набедренная повязка
        if face in ('front', 'back') and x in (fw // 2, fw // 2 - 1) and y % 4 == 0:
            return T.shade(dark, 0.8)  # шрамы
        return M.noise_color(r, skin if (x + y) % 5 else dark, 0.06)

    def limb(face, x, y, fw, fh):
        if y == 2 and face != 'top':
            return M.noise_color(r, belt, 0.08)  # наручи
        return M.noise_color(r, skin, 0.06)

    def club(face, x, y, fw, fh):
        base = wood if (x + y // 3) % 3 else T.shade(wood, 0.8)
        if y < 8:
            base = T.shade(base, 1.1)
        return M.noise_color(r, base, 0.05)

    M.paint_box(img, 0, 0, 8, 8, 8, head)
    M.paint_box(glow, 0, 0, 8, 8, 8, head_glow)
    M.paint_box(img, 0, 16, 12, 14, 6, body)
    M.paint_box(img, 40, 16, 5, 16, 5, limb)
    M.paint_box(img, 64, 16, 6, 16, 6, limb)
    M.paint_box(img, 92, 16, 4, 22, 4, club)
    save_png(img, 'entity/nephilim')
    save_png(glow, 'entity/nephilim_glow')


def chained_watcher():
    import gen_heaven_mobs as H
    M.ANGEL_ROBES['watcher'] = ('#3a3a4a', '#8a8aa0', '#2a2a38')
    tex, glow = H.angel('watcher')
    del M.ANGEL_ROBES['watcher']
    px, gp = tex.load(), glow.load()
    for y in range(64):
        for x in range(64):
            if 32 <= x < 54 and 32 <= y < 58 and px[x, y][3]:  # крылья в лохмотьях: темнее и с дырами
                r_, g_, b_, a_ = px[x, y]
                px[x, y] = (int(r_ * 0.4), int(g_ * 0.4), int(b_ * 0.45), 0 if (x * 5 + y * 3) % 11 == 0 else a_)
            if y < 9 and x >= 32 and px[x, y][3]:  # нимб погашен
                px[x, y] = (0, 0, 0, 0)
                gp[x, y] = (0, 0, 0, 0)
    save_png(tex, 'entity/chained_watcher')
    save_png(glow, 'entity/chained_watcher_glow')


def items():
    sling = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(sling)
    d.line([(3, 13), (3, 5), (7, 2)], fill=rgb('#c9b27a'), width=1)
    d.line([(12, 13), (12, 5), (8, 2)], fill=rgb('#c9b27a'), width=1)
    d.polygon([(5, 6), (10, 6), (10, 9), (5, 9)], fill=rgb('#6b4a2b'), outline=rgb('#3a2814'))
    d.line([(3, 13), (6, 15)], fill=rgb('#8a6238'))
    d.line([(12, 13), (9, 15)], fill=rgb('#8a6238'))
    sling.putpixel((7, 7), (*rgb('#a89a86'), 255))
    save_png(sling, 'item/sling')
    stone = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(stone)
    d.ellipse([4, 5, 11, 12], fill=rgb('#8e8e98'), outline=rgb('#4a4a54'))
    d.ellipse([5, 6, 7, 8], fill=rgb('#b8b8c2'))
    save_png(stone, 'item/sling_stone')
    for n in ('sling', 'sling_stone'):
        model(f'item/{n}', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c(f'item/{n}')}})
        item_def(n, c(f'item/{n}'))
    shapeless('sling', c('sling'), [MC('leather'), MC('string'), MC('string')], 1, 'equipment')
    shapeless('sling_stone', c('sling_stone'), [MC('cobblestone')], 4, 'misc')
    for n, base, spots in (('nephilim', '#8d7d6b', '#ff4a2a'), ('chained_watcher', '#3a3a4a', '#8a8aa0')):
        save_png(M.spawn_egg(base, spots), f'item/{n}_spawn_egg')
        model(f'item/{n}_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c(f'item/{n}_spawn_egg')}})
        item_def(f'{n}_spawn_egg', c(f'item/{n}_spawn_egg'))
    entity_loot('nephilim', [(c('abyssal_shard'), 3, 6), (MC('bone'), 4, 10), (c('shadow_essence'), 2, 4), (c('sling_stone'), 8, 16)])


# ------------------------------------------------------------------ постройка
def prison():
    t = Template(33, 16, 33)
    B, S = c('abyss_bricks'), c('abyss_stone')
    t.fill(0, 0, 0, 32, 1, 32, S)
    t.fill(1, 1, 1, 31, 1, 31, B)
    t.fill(0, 2, 0, 32, 11, 32, MC('air'))
    t.walls(0, 2, 0, 32, 11, 32, B)
    t.fill(0, 12, 0, 32, 12, 32, B)
    t.fill(14, 2, 32, 18, 5, 32, MC('air'))  # вход с юга
    # камеры вдоль северной стены: 5 штук, решётки на z = 7; прикованные Стражи в 1-й, 3-й и 5-й
    for k in range(5):
        x0 = 2 + 6 * k
        for y in range(2, 6):
            for x in range(x0, x0 + 4):
                t.set(x, y, 7, MC('iron_bars'), north=False, south=False, east=True, west=True, waterlogged=False)
        for z in range(1, 7):  # перегородка справа
            t.fill(x0 + 4, 2, z, x0 + 4, 11, z, B)
        if k % 2 == 0:
            for x in (x0, x0 + 3):  # цепи свисают с потолка
                t.fill(x, 6, 3, x, 11, 3, MC('chain'), axis='y', waterlogged=False)
            t.entity(x0 + 1, 2, 4, {'id': c('chained_watcher'), 'PersistenceRequired': True})
        else:
            t.set(x0 + 1, 2, 4, MC('cobweb'))
            t.set(x0 + 2, 2, 5, MC('skeleton_skull'), rotation=4)
    # зал Нефилима: четыре колонны с теневыми кристаллами, светогрибы у стен
    for x, z in ((6, 13), (26, 13), (6, 27), (26, 27)):
        t.fill(x, 2, z, x, 9, z, B)
        t.set(x, 10, z, c('shadow_crystal'), facing='up', waterlogged=False)
    for x, z in ((2, 14), (30, 14), (2, 26), (30, 26)):
        t.set(x, 2, z, c('glowshroom'))
    # Убранство зала (приёмка K1: был голый куб). Пол — дорожки и круг печати под Нефилимом; колонны толще, с обвитыми цепями;
    # цепи свисают с потолка и лежат обрывками на полу; кости, черепа, мох; синее пламя душ в нишах стен.
    rng = __import__('random').Random(6600)
    for x in range(1, 32):
        for z in range(8, 32):
            if (x + z) % 6 == 0 or x in (15, 16, 17):
                t.set(x, 1, z, S)
    for x in range(8, 25):
        for z in range(12, 29):
            r = ((x - 16) ** 2 + (z - 20) ** 2) ** 0.5
            if 5.5 <= r <= 6.4:
                t.set(x, 1, z, c('abyss_stone'))
            if 6.4 < r <= 7.2:
                t.set(x, 1, z, B)
    for i in range(8):  # руны круга — теневые кристаллы в полу по кругу
        a = i / 8 * 6.2832
        t.set(round(16 + 6 * __import__('math').cos(a)), 2, round(20 + 6 * __import__('math').sin(a)), c('shadow_crystal'), facing='up', waterlogged=False)
    for x, z in ((6, 13), (26, 13), (6, 27), (26, 27)):
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t.fill(x + dx, 2, z + dz, x + dx, 3 + rng.randint(0, 5), z + dz, B)  # обломанная обкладка колонны
        t.fill(x + 1, 6, z - 1, x + 1, 11, z - 1, MC('chain'), axis='y', waterlogged=False)
    for _ in range(14):  # цепи с потолка разной длины
        x, z = rng.randint(3, 29), rng.randint(10, 30)
        if abs(x - 16) + abs(z - 20) > 4:
            t.fill(x, 12 - rng.randint(2, 6), z, x, 11, z, MC('chain'), axis='y', waterlogged=False)
    for _ in range(10):  # обрывки цепей на полу
        x, z = rng.randint(3, 29), rng.randint(10, 30)
        if t.get(x, 2, z) in (None, MC('air')):
            t.set(x, 2, z, MC('chain'), axis=rng.choice(['x', 'z']), waterlogged=False)
    for _ in range(16):  # кости и мох
        x, z = rng.randint(2, 30), rng.randint(9, 30)
        if t.get(x, 2, z) in (None, MC('air')):
            kind = rng.choice(['bone', 'moss', 'moss', 'skull'])
            if kind == 'bone':
                t.set(x, 2, z, MC('bone_block'), axis=rng.choice(['x', 'z']))
            elif kind == 'skull':
                t.set(x, 2, z, MC('skeleton_skull'), rotation=rng.randint(0, 15))
            else:
                t.set(x, 1, z, c('gloom_moss'))  # мох вместо плиты пола
    for z in (12, 18, 24, 30):  # синее пламя душ в нишах западной и восточной стен
        for x in (1, 31):
            t.set(x, 4, z, B)  # консоль в стене
            t.set(x, 5, z, MC('soul_lantern'), hanging=False, waterlogged=False)
    t.entity(16, 2, 20, {'id': c('nephilim'), 'PersistenceRequired': True})
    # склад у входа: праща и камни (на случай, если игрок пришёл без них)
    chest(t, 12, 2, 31, 'celestial:chests/watchers_prison', facing='north')
    chest(t, 20, 2, 31, 'celestial:chests/watchers_prison', facing='north')
    t.save('watchers_prison/main')


def structure():
    name = 'watchers_prison'
    write_json(os.path.join(DATA, f'worldgen/template_pool/{name}/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(name + '/main'),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}}]})
    write_json(os.path.join(DATA, f'worldgen/structure/{name}.json'), {
        'type': c('cave_floor'), 'biomes': '#' + c('has_structure/' + name), 'spawn_overrides': {}, 'step': 'surface_structures',
        'terrain_adaptation': 'beard_box', 'start_pool': c(name + '/main'), 'min_y': 30, 'max_y': 110,
        'floor_offset': -1, 'clearance': 14, 'max_distance_from_center': 80, 'footprint': 33, 'max_step': 6})
    write_json(os.path.join(DATA, f'tags/worldgen/biome/has_structure/{name}.json'), {'values': [c(b) for b in ('dark_wastes', 'crystal_hollows')]})
    write_json(os.path.join(DATA, f'worldgen/structure_set/{name}.json'), {
        'placement': {'type': 'minecraft:random_spread', 'salt': 7300203, 'separation': 12, 'spacing': 36},
        'structures': [{'structure': c(name), 'weight': 1}]})
    append_tag('worldgen/structure', 'celestial:codex_places', [c(name)])
    def item(n, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': n, 'weight': w}
        if hi > 1:
            e['modifier'] = [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e
    write_json(os.path.join(DATA, 'loot_table/chests/watchers_prison.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/watchers_prison'), 'pools': [
            {'rolls': 1, 'entries': [item(c('sling'), 3), {'type': 'minecraft:empty', 'weight': 1}]},
            {'rolls': 2, 'entries': [item(c('sling_stone'), 8, 8, 20), item(MC('leather'), 4, 1, 3), item(MC('string'), 4, 2, 5),
                                     item(c('abyssal_shard'), 3, 1, 3), item(c('starlight_flask'), 2)]}]})


def lang():
    e = {
        'entity.celestial.nephilim': ('Нефилим', 'Nephilim'),
        'entity.celestial.chained_watcher': ('Прикованный Страж', 'Chained Watcher'),
        'entity.celestial.chained_watcher.line1': ('Мы спустились на гору Ермон, поклялись, и клятва стала нам цепью.',
                                                  'We came down upon Hermon and swore an oath, and the oath became our chain.'),
        'entity.celestial.chained_watcher.line2': ('Мы хотели научить людей, а научили их воевать. Не повторяй нашей гордыни, странник.',
                                                  'We meant to teach men and taught them war instead. Do not repeat our pride, wanderer.'),
        'entity.celestial.chained_watcher.line3': ('Наши дети-великаны бродят по залу. Против великана не нужна сила, нужен меткий камень.',
                                                  'Our giant children prowl the hall. Against a giant strength is not needed; a well-aimed stone is.'),
        'item.celestial.sling': ('Праща', 'Sling'),
        'item.celestial.sling.lore1': ('ПКМ — метнуть камень для пращи.', 'Use to hurl a sling stone.'),
        'item.celestial.sling.lore2': ('По крупным целям — великанам, големам, боссам — урон ×3.', 'Against large targets (giants, golems, bosses) damage is tripled.'),
        'item.celestial.sling_stone': ('Камень для пращи', 'Sling Stone'),
        'entity.celestial.sling_stone': ('Камень для пращи', 'Sling Stone'),
        'item.celestial.nephilim_spawn_egg': ('Яйцо призыва: Нефилим', 'Nephilim Spawn Egg'),
        'item.celestial.chained_watcher_spawn_egg': ('Яйцо призыва: Прикованный Страж', 'Chained Watcher Spawn Egg'),
        'structure.celestial.watchers_prison': ('Темница Стражей', 'Prison of the Watchers'),
        'codex.celestial.place.watchers_prison': ('зал в глубине Бездны: прикованные Стражи в камерах и Нефилим в центре. У входа лежат праща и камни.',
                                                  'a hall deep in the Abyss: chained Watchers in cells and a Nephilim in the centre. A sling and stones lie by the entrance.'),
        'codex.celestial.mob.nephilim': ('великан, сын Стража и дочери человеческой. Бьёт дубиной и топочет — отбегай и бей камнями из пращи: по великанам они втрое сильнее.',
                                         'a giant, child of a Watcher and a daughter of men. Clubs and stomps: back away and use sling stones, which hit giants three times harder.'),
        'codex.celestial.mob.chained_watcher': ('узник Темницы. Не враг: расскажет, как Стражи пали.', 'a prisoner of the Prison. Not a foe: he will tell how the Watchers fell.'),
    }
    lang_patch(e)


def main():
    nephilim()
    chained_watcher()
    items()
    prison()
    structure()
    lang()
    print('ok: Темница Стражей, Нефилим, праща')


if __name__ == '__main__':
    main()
