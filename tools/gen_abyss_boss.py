"""Акт II (волна 0.3, шаг 6): Пожиратель Света, жаровни, печать, Тёмное Ядро, Затонувший храм и Логово Пожирателя.

Развёртка босса совпадает с DevourerRenderer.Model (256×128). Постройки ставятся на абсолютной высоте в биомах Бездны,
вокруг них рельеф расчищается beardifier'ом (он есть в final_density Бездны).
"""
import math
import os
import random

from PIL import Image

import mob_textures as M
import textures as T
from gen_abyss import append_tag
from gen_assets import DATA, blockstate, c, item_def, model, save_png, self_drop, write_json
from gen_story import lang_patch
from gen_structures import Template, chest, reliquary

MC = lambda n: 'minecraft:' + n  # noqa: E731
F6 = ('north', 'south', 'east', 'west', 'up', 'down')

BOXES = {  # имя: (u, v, w, h, d) — как в DevourerRenderer.Model
    'body': (0, 0, 20, 6, 28), 'head': (96, 0, 12, 6, 8), 'jaw': (136, 0, 10, 2, 7),
    'lwing': (0, 34, 18, 2, 24), 'rwing': (0, 60, 18, 2, 24), 'ltip': (96, 34, 16, 1, 20), 'rtip': (96, 56, 16, 1, 20),
    'tail0': (0, 86, 6, 4, 12), 'tail1': (40, 86, 4, 3, 12), 'tail2': (76, 86, 2, 2, 10), 'sting': (104, 86, 4, 4, 4),
}


def devourer():
    base = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    exposed = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    r = T.rng_for('light_devourer')
    ink = [T.hexrgb(h) for h in ('#07050c', '#0d0915', '#140e1f', '#1b1329')]
    edge = T.hexrgb('#2a1f3d')

    def skin(face, x, y, fw, fh):
        if face in ('top', 'bottom') and (x in (0, fw - 1) or y in (0, fh - 1)):
            return edge
        return r.choice(ink)

    def mouth(face, x, y, fw, fh):
        if face == 'top':
            return T.hexrgb('#000000')
        return skin(face, x, y, fw, fh)

    for name, (u, v, w, h, d) in BOXES.items():
        M.paint_box(base, u, v, w, h, d, mouth if name == 'jaw' else skin)

    # тёмные жилы (светятся всегда, тускло-фиолетовые) и золотые (только когда горят жаровни) — ветвистый узор по верху
    def veins(img, color, seed, density):
        rv = random.Random(seed)
        for name, (u, v, w, h, d) in BOXES.items():
            for x0, y0 in ((u + d, v), (u + d + w, v)):  # верхняя и нижняя грани (снизу босса видно чаще всего)
                for _ in range(max(1, w * d // density)):
                    x, y = rv.randrange(w), rv.randrange(d)
                    for _ in range(rv.randint(4, 12)):
                        if 0 <= x < w and 0 <= y < d:
                            img.putpixel((x0 + x, y0 + y), color)
                        x += rv.choice((-1, 0, 1))
                        y += rv.choice((-1, 0, 1))
    veins(glow, (120, 70, 200, 255), 7, 80)
    veins(exposed, (255, 210, 120, 255), 8, 45)
    # пасть и жало светятся всегда
    M.paint_box(glow, *BOXES['jaw'], lambda f, x, y, fw, fh: (190, 120, 255, 255) if f == 'top' else None)
    M.paint_box(glow, *BOXES['sting'], lambda f, x, y, fw, fh: (210, 150, 255, 255))
    M.paint_box(glow, *BOXES['head'], lambda f, x, y, fw, fh: (220, 180, 255, 255) if f == 'front' and y == 2 and x in (2, 3, 8, 9) else None)
    save_png(base, 'entity/light_devourer')
    save_png(glow, 'entity/light_devourer_glow')
    save_png(exposed, 'entity/light_devourer_exposed')


def brazier():
    save_png(T.noisy('brazier_metal', [T.hexrgb(h) for h in ('#14111a', '#1d1826', '#272033', '#3a2f4a')], cell=2, grain=0.4), 'block/brazier_metal')
    coal = T.noisy('brazier_coals', [T.hexrgb(h) for h in ('#120c0c', '#2a1410', '#3d1d12')], cell=2, grain=0.5)
    save_png(coal, 'block/brazier_coals')
    for lit in (False, True):
        els = [{'from': [4, 0, 4], 'to': [12, 2, 12], 'faces': {d: {'texture': '#metal'} for d in F6}},
               {'from': [6, 2, 6], 'to': [10, 9, 10], 'faces': {d: {'texture': '#bricks'} for d in F6}},
               {'from': [2, 9, 2], 'to': [14, 11, 14], 'faces': {d: {'texture': '#metal'} for d in F6}},
               {'from': [2, 11, 2], 'to': [14, 14, 3], 'faces': {d: {'texture': '#metal'} for d in F6}},
               {'from': [2, 11, 13], 'to': [14, 14, 14], 'faces': {d: {'texture': '#metal'} for d in F6}},
               {'from': [2, 11, 3], 'to': [3, 14, 13], 'faces': {d: {'texture': '#metal'} for d in F6}},
               {'from': [13, 11, 3], 'to': [14, 14, 13], 'faces': {d: {'texture': '#metal'} for d in F6}},
               {'from': [3, 11, 3], 'to': [13, 12, 13], 'faces': {'up': {'texture': '#coals'}}}]
        tex = {'metal': c('block/brazier_metal'), 'bricks': c('block/abyss_bricks'), 'coals': c('block/brazier_coals'),
               'particle': c('block/brazier_metal')}
        if lit:  # голубое «звёздное» пламя — ванильная текстура огня душ (анимированная), как в костре
            tex['fire'] = MC('block/soul_fire_0')
            for rot in (45, -45):
                els.append({'from': [3, 12, 8], 'to': [13, 26, 8], 'shade': False,
                            'rotation': {'origin': [8, 12, 8], 'axis': 'y', 'angle': rot, 'rescale': True},
                            'faces': {'north': {'texture': '#fire', 'uv': [0, 0, 16, 16]}, 'south': {'texture': '#fire', 'uv': [0, 0, 16, 16]}}})
        model('block/brazier' + ('_lit' if lit else ''), {'textures': tex, 'elements': els})
    blockstate('brazier', {'variants': {'lit=false': {'model': c('block/brazier')}, 'lit=true': {'model': c('block/brazier_lit')}}})
    item_def('brazier', c('block/brazier'))
    self_drop('brazier')


def seal():
    for awake in (False, True):
        img = T.noisy('devourer_seal' + str(awake), [T.hexrgb(h) for h in ('#120a1c', '#1c1029', '#251536')], cell=2, grain=0.4)
        for i in range(48):  # кольцо рун
            a = i * math.pi / 24
            x, y = int(7.5 + math.cos(a) * 6), int(7.5 + math.sin(a) * 6)
            img.putpixel((x, y), (*T.hexrgb('#4a2a6a' if awake else '#b48cff'), 255))
        for x, y in ((7, 7), (8, 7), (7, 8), (8, 8), (6, 7), (9, 8)):
            img.putpixel((x, y), (*T.hexrgb('#000000' if awake else '#e6d6ff'), 255))
        name = 'devourer_seal' + ('_awakened' if awake else '')
        save_png(img, 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_column', 'textures': {'end': c('block/' + name), 'side': c('block/abyss_bricks')}})
    blockstate('devourer_seal', {'variants': {'awakened=false': {'model': c('block/devourer_seal')},
                                              'awakened=true': {'model': c('block/devourer_seal_awakened')}}})
    item_def('devourer_seal', c('block/devourer_seal'))


def dark_core():
    rows = ['................',
            '.......11.......',
            '.....112211.....',
            '....12233221....',
            '...1233443321...',
            '...1234554321...',
            '..123455554321..',
            '..123456654321..',
            '..123456654321..',
            '..123455554321..',
            '...1234554321...',
            '...1233443321...',
            '....12233221....',
            '.....112211.....',
            '.......11.......',
            '................']
    img = T.sprite(rows, {'1': '#05030a', '2': '#140b24', '3': '#2a1450', '4': '#5b2a9c', '5': '#b48cff', '6': '#ffffff'})
    save_png(img, 'item/dark_core')
    model('item/dark_core', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/dark_core')}})
    item_def('dark_core', c('item/dark_core'))


# ---------------------------------------------------------------- постройки
def disc(t, cx, cz, r, y, block, **p):
    for x in range(t.size[0]):
        for z in range(t.size[2]):
            if math.hypot(x - cx, z - cz) <= r:
                t.set(x, y, z, block, **p)


def sunken_temple():
    """Храм у озёр тьмы: ров с водой, колонны со светогрибами, загадка луча (рычаг → фонарь → зеркало → приёмник)
    открывает хранилище с картой к Логову Пожирателя."""
    t = Template(23, 14, 23)
    B, S = c('abyss_bricks'), c('abyss_stone')
    t.fill(0, 0, 0, 22, 1, 22, S)
    t.fill(1, 2, 1, 21, 2, 21, MC('water'), level=0)  # ров
    t.fill(3, 0, 3, 19, 2, 19, B)
    t.walls(3, 3, 3, 19, 10, 19, B)
    t.fill(4, 3, 4, 18, 10, 18, MC('air'))
    t.fill(3, 11, 3, 19, 11, 19, B)
    t.fill(4, 12, 4, 18, 12, 18, c('gloom_moss'))
    t.fill(10, 3, 3, 12, 6, 3, MC('air'))  # вход с севера
    t.fill(10, 2, 0, 12, 2, 2, B)  # мостик через ров
    for x, z in ((6, 6), (16, 6), (6, 16), (16, 16)):
        t.fill(x, 3, z, x, 10, z, c('glowshroom_stem'))
        t.set(x, 11, z, c('glowshroom_cap'))
    # загадка: рычаг на фонаре, луч на восток в зеркало (стоит неверно), от него на юг — к приёмнику у печати
    t.set(5, 3, 11, c('beam_lantern'), nbt={'id': c('beam_source')}, facing='east', active=False, sealed=True)
    t.set(5, 4, 11, MC('lever'), face='floor', facing='east', powered=False)
    t.set(11, 3, 11, c('beam_mirror'), flipped=False)  # неверно: луч уходит на север, надо повернуть Камертоном
    t.set(11, 3, 15, c('light_receiver'), color='white', powered=False, sealed=True)
    t.fill(10, 3, 16, 12, 5, 16, c('sealed_door'))
    t.fill(5, 3, 17, 17, 6, 18, MC('air'))
    reliquary(t, 11, 3, 18, 'celestial:chests/sunken_temple')
    chest(t, 16, 3, 5, 'celestial:chests/trial_tools', facing='west')
    t.set(7, 3, 5, c('shadow_crystal'), facing='up', waterlogged=False)
    t.set(15, 3, 13, c('shadow_crystal'), facing='up', waterlogged=False)
    return t.save('sunken_temple/main')


def devourer_lair():
    """Логово: купол радиусом 15 из кирпичей Бездны, четыре жаровни на возвышениях, печать в центре, сокровищница сзади."""
    t = Template(33, 22, 33)
    cx = cz = 16
    B = c('abyss_bricks')
    disc(t, cx, cz, 15.5, 0, c('abyss_stone'))
    disc(t, cx, cz, 15.5, 1, B)
    for y in range(2, 21):
        for x in range(33):
            for z in range(33):
                d = math.sqrt((x - cx) ** 2 + ((y - 1) * 1.25) ** 2 + (z - cz) ** 2)
                if d <= 15.0:
                    t.set(x, y, z, MC('air'))
                elif d <= 16.2:
                    t.set(x, y, z, B)
    for i in range(12):  # кольцо колонн
        a = i * math.pi / 6
        x, z = round(cx + math.cos(a) * 10.5), round(cz + math.sin(a) * 10.5)
        t.fill(x, 2, z, x, 8, z, B)
        t.set(x, 9, z, c('shadow_crystal'), facing='up', waterlogged=False)
    for dx, dz in ((10, 0), (-10, 0), (0, 10), (0, -10)):
        x, z = cx + dx, cz + dz
        t.fill(x - 1, 1, z - 1, x + 1, 1, z + 1, MC('chiseled_polished_blackstone'))
        t.set(x, 2, z, c('brazier'), lit=False)
    t.set(cx, 1, cz, c('devourer_seal'), nbt={'id': c('devourer_seal')}, awakened=False)
    t.fill(cx - 1, 2, 31, cx + 1, 5, 32, MC('air'))  # проход
    t.fill(cx - 2, 1, 4, cx + 2, 1, 5, MC('chiseled_polished_blackstone'))  # сокровища у северной стены, внутри купола
    chest(t, cx - 1, 2, 4, 'celestial:chests/devourer_lair', facing='south')
    chest(t, cx + 1, 2, 4, 'celestial:chests/devourer_lair', facing='south')
    return t.save('devourer_lair/main')


def structures():
    # пол пещеры ищет свой тип постройки celestial:cave_floor (карта высот в мире с потолком указывает на крышу)
    # footprint/max_step: пол проверяется по углам и центру всей площади; clearance — по высоте шаблона (логово 22 — раньше 14, купол врезался в свод)
    for name, biomes, offset, clearance, spacing, sep, salt, footprint, step in (
            ('sunken_temple', ('dark_lakes', 'glowshroom_forest'), -2, 12, 22, 8, 7300201, 23, 6),
            ('devourer_lair', ('dark_wastes', 'crystal_hollows'), -1, 22, 40, 14, 7300202, 33, 6)):
        write_json(os.path.join(DATA, f'worldgen/template_pool/{name}/main.json'), {'fallback': 'minecraft:empty', 'elements': [
            {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(name + '/main'),
                                      'processors': 'minecraft:empty', 'projection': 'rigid'}}]})
        write_json(os.path.join(DATA, f'worldgen/structure/{name}.json'), {
            'type': c('cave_floor'), 'biomes': '#' + c('has_structure/' + name), 'spawn_overrides': {}, 'step': 'surface_structures',
            'terrain_adaptation': 'beard_box', 'start_pool': c(name + '/main'), 'min_y': 30, 'max_y': 110,
            'floor_offset': offset, 'clearance': clearance, 'max_distance_from_center': 80, 'footprint': footprint, 'max_step': step})
        write_json(os.path.join(DATA, f'tags/worldgen/biome/has_structure/{name}.json'), {'values': [c(b) for b in biomes]})
        write_json(os.path.join(DATA, f'worldgen/structure_set/{name}.json'), {
            'placement': {'type': 'minecraft:random_spread', 'salt': salt, 'separation': sep, 'spacing': spacing},
            'structures': [{'structure': c(name), 'weight': 1}]})
    write_json(os.path.join(DATA, 'tags/worldgen/structure/devourer_lairs.json'), {'values': [c('devourer_lair')]})
    append_tag('worldgen/structure', 'celestial:codex_places', [c('sunken_temple'), c('devourer_lair')])

    def table(name, pools):
        write_json(os.path.join(DATA, 'loot_table/chests', name + '.json'),
                   {'type': 'minecraft:chest', 'pools': pools, 'random_sequence': c('chests/' + name)})

    def item(n, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': n, 'weight': w}
        if hi > 1:
            e['modifier'] = [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e

    lair_map = {'type': 'minecraft:item', 'name': MC('filled_map'), 'modifier': [
        {'type': 'minecraft:exploration_map', 'decoration': 'minecraft:red_x', 'destination': '#' + c('devourer_lairs'),
         'search_radius': 50, 'skip_existing_chunks': False},
        {'type': 'minecraft:set_name', 'name': {'translate': 'filled_map.celestial.devourer_lair'}, 'target': 'item_name'}]}
    table('sunken_temple', [
        {'rolls': 1, 'entries': [lair_map]},
        {'rolls': {'type': 'minecraft:uniform', 'min': 3, 'max': 5}, 'entries': [
            item(c('abyssal_shard'), 6, 2, 5), item(c('starlight_flask'), 4, 1, 2), item(c('charged_crystal'), 2), item(c('star_fragment'), 3, 1, 2),
            item(c('starsteel_ingot'), 4, 1, 3), item(MC('glow_berries'), 4, 3, 8), item(c('shadow_essence'), 4, 1, 3)]}])
    table('devourer_lair', [
        {'rolls': {'type': 'minecraft:uniform', 'min': 4, 'max': 6}, 'entries': [
            item(c('abyssal_ingot'), 5, 1, 3), item(c('worm_chitin'), 3, 1, 2), item(c('starlight_flask'), 4, 1, 3),
            item(MC('diamond'), 3, 2, 4), item(c('charged_crystal'), 2), item(c('rune_of_stars'), 2), item(c('seraph_feather'), 2, 1, 2)]}])


def main():
    devourer()
    brazier()
    seal()
    dark_core()
    counts = {'храм': sunken_temple(), 'логово': devourer_lair()}
    structures()
    append_tag('block', 'minecraft:mineable/pickaxe', [c('brazier')])
    lang_patch({
        'entity.celestial.light_devourer': ('Пожиратель Света', 'Light Devourer'),
        'block.celestial.brazier': ('Жаровня', 'Brazier'),
        'block.celestial.devourer_seal': ('Печать Пожирателя', 'Devourer Seal'),
        'item.celestial.dark_core': ('Тёмное Ядро', 'Dark Core'),
        'filled_map.celestial.devourer_lair': ('Карта Логова Пожирателя', 'Map to the Devourer\'s Lair'),
        'structure.celestial.sunken_temple': ('Затонувший храм', 'Sunken Temple'),
        'structure.celestial.devourer_lair': ('Логово Пожирателя', 'Devourer\'s Lair'),
        'codex.celestial.place.sunken_temple': ('храм у озёр тьмы. Направь луч фонаря в приёмник — в хранилище карта к Логову.',
                                                'a temple by the dark lakes. Guide the lantern\'s beam into the receiver: the vault holds a map to the Lair.'),
        'codex.celestial.place.devourer_lair': ('купол в глубине Бездны. Зажги жаровни — иначе Пожирателя не ранить.',
                                                'a dome deep in the Abyss. Light the braziers, or the Devourer cannot be harmed.'),
        'codex.celestial.mob.light_devourer': ('страж Бездны. Уязвим, лишь пока горят хотя бы две жаровни; гасит их, налетая сверху.',
                                               'guardian of the Abyss. Vulnerable only while at least two braziers burn; it swoops down to put them out.'),
        'boss.celestial.light_devourer.awaken': ('§5Печать раскалывается. Из-под свода падает тьма — Пожиратель Света проснулся!',
                                                 '§5The seal cracks. Darkness pours from the vault: the Light Devourer awakens!'),
        'boss.celestial.light_devourer.subtitle': ('Зажги жаровни — тьма неуязвима', 'Light the braziers: darkness cannot be wounded'),
        'boss.celestial.light_devourer.absorbs': ('§8Тьма поглощает удар — зажги жаровни!', '§8The darkness swallows the blow: light the braziers!'),
        'boss.celestial.light_devourer.hunts_fire': ('§c⚠ Пожиратель летит гасить жаровню!', '§c⚠ The Devourer swoops to put out a brazier!'),
        'boss.celestial.light_devourer.phase2': ('§5Пожиратель ревёт — из тьмы лезут Светоеды!', '§5The Devourer roars: Light Eaters crawl from the dark!'),
        'boss.celestial.light_devourer.phase3': ('§4Пожиратель глотает весь свет вокруг! Зажигай жаровни снова и держись дальше от пасти!',
                                                 '§4The Devourer swallows all light around! Relight the braziers and keep away from its maw!'),
    })
    print('ok: Акт II', counts)


if __name__ == '__main__':
    main()
