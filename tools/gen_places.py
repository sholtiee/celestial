"""Сюжетные места Угасания в ванильных измерениях + Звездочёт (волна 0.2, шаг 9d–e).

Звёздная обсерватория (Верхний мир, загадка плиток-звёзд), Пылающее святилище (Ад, испытание огнём → Осколок Пламени),
Разлом Пустоты (Энд, испытание с Тенями). Телескоп и профессия Звездочёта: модель, рецепт, сделки, текстуры.
"""
import math
import os
import random

from PIL import Image

import textures as T
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, self_drop, shaped, write_json
from gen_story import lang_patch
from gen_structures import Template, chest, reliquary

MC = lambda n: 'minecraft:' + n  # noqa: E731
VANILLA = os.path.join(os.path.dirname(__file__), '..', '.mcsrc', 'assets', 'assets', 'minecraft', 'textures')


# ---------------------------------------------------------------- постройки
def disc(t, cx, cz, r, y, block, **props):
    for x in range(t.size[0]):
        for z in range(t.size[2]):
            if math.hypot(x - cx, z - cz) <= r:
                t.set(x, y, z, block, **props)


def observatory():
    """Башня со стеклянным куполом и телескопом наверху. Внизу — 3×3 плиток-звёзд: зажги все, и откроется хранилище."""
    t = Template(19, 22, 19)
    cx = cz = 9
    disc(t, cx, cz, 8.4, 0, MC('stone_bricks'))
    for y in range(1, 10):
        for x in range(19):
            for z in range(19):
                d = math.hypot(x - cx, z - cz)
                if d <= 6.3:
                    t.set(x, y, z, MC('air'))
                elif d <= 7.3:
                    window = y in (3, 4) and (x == cx or z == cz or abs(x - cx) == abs(z - cz))
                    t.set(x, y, z, MC('light_blue_stained_glass') if window else
                          MC('polished_andesite') if y in (1, 9) else MC('stone_bricks'))
    disc(t, cx, cz, 7.3, 10, MC('smooth_stone'))
    for y in range(11, 19):  # купол
        for x in range(19):
            for z in range(19):
                d = math.sqrt((x - cx) ** 2 + (y - 10) ** 2 * 1.0 + (z - cz) ** 2)
                if d <= 6.2:
                    t.set(x, y, z, MC('air'))
                elif d <= 7.2:
                    slot = z < cz and abs(x - cx) <= 1 and y >= 13  # щель для телескопа
                    rib = x == cx or z == cz
                    t.set(x, y, z, MC('air') if slot else MC('waxed_cut_copper') if rib else MC('light_blue_stained_glass'))
    # вход и лестница наверх
    t.fill(cx - 1, 1, 16, cx + 1, 3, 16, MC('air'))
    for y in range(1, 11):
        t.set(cx, y, 3, MC('ladder'), facing='south', waterlogged=False)
    t.set(cx, 10, 3, MC('air'))
    t.set(cx, 11, 4, C('telescope'), facing='north')
    t.set(cx, 11, 9, C('telescope'), facing='north')
    t.set(cx + 2, 11, 9, MC('lectern'), facing='west', has_book=False, powered=False)
    for x, z in ((4, 4), (14, 4), (4, 14), (14, 14)):
        t.set(x, 1, z, MC('bookshelf'))
        t.set(x, 2, z, MC('bookshelf'))
        t.set(x, 9, z, MC('lantern'), hanging=True, waterlogged=False)
    # загадка: плитки-звёзды (шахматный узор — уже не решено)
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            t.set(x, 1, z, C('star_tile'), lit=(x + z) % 2 == 1, solved=False)
    # хранилище за печатью у западной стены
    t.fill(3, 1, 7, 5, 3, 11, MC('chiseled_stone_bricks'))
    t.fill(3, 1, 8, 4, 2, 10, MC('air'))
    reliquary(t, 3, 1, 9, 'celestial:chests/observatory')
    t.fill(5, 1, 8, 5, 2, 10, C('sealed_door'))
    t.set(cx + 4, 1, cz, MC('cartography_table'))
    return t.save('observatory/main')


def flame_sanctuary():
    """Платформа над лавовым морем Ада: кристалл испытания огнём, жаровни, хранилище за печатью."""
    t = Template(23, 18, 23)
    cx = cz = 11
    for x, z in ((4, 4), (18, 4), (4, 18), (18, 18), (11, 2), (11, 20), (2, 11), (20, 11)):
        t.fill(x, 0, z, x, 4, z, MC('polished_blackstone_bricks'))
    disc(t, cx, cz, 10.4, 5, MC('polished_blackstone_bricks'))
    for x in range(23):
        for z in range(23):
            d = math.hypot(x - cx, z - cz)
            if d <= 10.4:
                for y in range(6, 16):
                    t.set(x, y, z, MC('air'))
                if 9.4 < d:
                    t.set(x, 5, z, MC('gilded_blackstone') if (x * 7 + z * 3) % 5 == 0 else MC('blackstone'))
                    t.set(x, 6, z, MC('polished_blackstone_brick_wall'), up=True, north='none', south='none', east='none', west='none',
                          waterlogged=False)
    for i in range(8):  # колонны с плачущим обсидианом
        a = i * math.pi / 4
        x, z = round(cx + math.cos(a) * 8), round(cz + math.sin(a) * 8)
        t.fill(x, 6, z, x, 11, z, MC('polished_blackstone_bricks'))
        t.set(x, 12, z, MC('crying_obsidian'))
    t.fill(cx - 1, 6, cz - 1, cx + 1, 6, cz + 1, MC('chiseled_polished_blackstone'))
    t.set(cx, 7, cz, C('trial_crystal'), nbt={'id': C('trial_crystal'), 'Trial': 'flame_sanctuary'}, state='idle')
    for dx, dz in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
        t.set(cx + dx, 6, cz + dz, MC('campfire'), facing='north', lit=True, signal_fire=False, waterlogged=False)
    # хранилище
    t.fill(cx - 2, 6, 1, cx + 2, 9, 4, MC('polished_blackstone_bricks'))
    t.fill(cx - 1, 6, 2, cx + 1, 8, 3, MC('air'))
    reliquary(t, cx, 6, 2, 'celestial:chests/flame_sanctuary')
    t.fill(cx - 1, 6, 4, cx + 1, 8, 4, C('sealed_door'))
    return t.save('flame_sanctuary/main')


def void_rift():
    """Святилище на внешних островах Энда: разлом из плачущего обсидиана, кристалл испытания, хранилище."""
    t = Template(17, 14, 17)
    cx = cz = 8
    disc(t, cx, cz, 7.4, 0, MC('end_stone_bricks'))
    for x in range(17):
        for z in range(17):
            if math.hypot(x - cx, z - cz) <= 7.4:
                for y in range(1, 12):
                    t.set(x, y, z, MC('air'))
    for x, z in ((2, 2), (14, 2), (2, 14), (14, 14)):
        t.fill(x, 1, z, x, 7, z, MC('purpur_pillar'), axis='y')
        t.set(x, 8, z, MC('end_rod'), facing='up')
    # разлом: кольцо плачущего обсидиана с аметистами
    for i in range(16):
        a = i * math.pi / 8
        x, z = round(cx + math.cos(a) * 4), round(cz + math.sin(a) * 4)
        t.set(x, 1, z, MC('crying_obsidian'))
        if i % 4 == 0:
            t.set(x, 2, z, MC('amethyst_cluster'), facing='up', waterlogged=False)
    t.fill(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, MC('obsidian'))
    t.set(cx, 1, cz, C('trial_crystal'), nbt={'id': C('trial_crystal'), 'Trial': 'void_rift'}, state='idle')
    t.fill(cx - 1, 1, 13, cx + 1, 3, 15, MC('purpur_block'))
    t.set(cx, 1, 14, MC('air'))
    reliquary(t, cx, 1, 14, 'celestial:chests/void_rift')
    t.set(cx, 1, 13, C('sealed_door'))
    t.set(cx, 2, 13, C('sealed_door'))
    return t.save('void_rift/main')


C = c


def jigsaw(name, biomes, height, project=True, step='surface_structures', adaptation='beard_thin'):
    write_json(os.path.join(DATA, 'worldgen/template_pool', name + '/main.json'), {'fallback': 'minecraft:empty', 'elements': [
        {'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': c(name + '/main'),
                                  'processors': 'minecraft:empty', 'projection': 'rigid'}}]})
    s = {'type': 'minecraft:jigsaw', 'biomes': '#' + c('has_structure/' + name), 'max_distance_from_center': 80, 'size': 1,
         'spawn_overrides': {}, 'start_height': {'absolute': height}, 'start_pool': c(name + '/main'), 'step': step,
         'terrain_adaptation': adaptation, 'use_expansion_hack': False}
    if project:
        s['project_start_to_heightmap'] = 'WORLD_SURFACE_WG'
    write_json(os.path.join(DATA, 'worldgen/structure', name + '.json'), s)
    write_json(os.path.join(DATA, 'tags/worldgen/biome/has_structure', name + '.json'), {'values': biomes})


def structure_set(name, spacing, separation, salt):
    write_json(os.path.join(DATA, 'worldgen/structure_set', name + '.json'), {
        'placement': {'type': 'minecraft:random_spread', 'salt': salt, 'separation': separation, 'spacing': spacing},
        'structures': [{'structure': c(name), 'weight': 1}]})


def loot():
    def table(name, pools):
        write_json(os.path.join(DATA, 'loot_table/chests', name + '.json'),
                   {'type': 'minecraft:chest', 'pools': pools, 'random_sequence': c('chests/' + name)})

    def p(rolls, entries):
        return {'rolls': rolls if isinstance(rolls, int) else {'type': 'minecraft:uniform', 'min': rolls[0], 'max': rolls[1]},
                'entries': [{'type': 'minecraft:empty', 'weight': w} if n is None else
                            {'type': 'minecraft:item', 'name': n, 'weight': w,
                             **({'modifier': [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': a, 'max': b}}]} if b > 1 else {})}
                            for n, w, a, b in entries]}

    table('observatory', [
        p(1, [(C('telescope'), 1, 1, 1)]),
        p((3, 5), [(C('star_fragment'), 6, 1, 3), (C('starquartz'), 8, 3, 8), (MC('spyglass'), 3, 1, 1), (C('rune_of_stars'), 3, 1, 1),
                   (MC('compass'), 3, 1, 1), (MC('amethyst_shard'), 5, 2, 6), (C('radiant_stone'), 4, 2, 6)])])
    table('trial_flame_sanctuary', [
        p(1, [(C('flame_shard'), 1, 1, 1)]),
        p((2, 4), [(MC('blaze_rod'), 6, 2, 5), (MC('gold_ingot'), 6, 3, 8), (MC('ancient_debris'), 1, 1, 1), (MC('magma_cream'), 4, 2, 4)])])
    table('flame_sanctuary', [
        p((3, 5), [(MC('gilded_blackstone'), 4, 2, 6), (MC('golden_apple'), 3, 1, 2), (C('rune_of_light'), 2, 1, 1),
                   (MC('netherite_scrap'), 1, 1, 1), (MC('fire_charge'), 5, 2, 6), (C('star_fragment'), 2, 1, 2)])])
    table('trial_void_rift', [
        p(1, [(C('void_heart'), 1, 1, 1), (None, 3, 1, 1)]),
        p((2, 4), [(MC('ender_pearl'), 6, 2, 6), (C('shadow_essence'), 6, 2, 5), (C('star_fragment'), 4, 1, 3), (MC('shulker_shell'), 2, 1, 2)])])
    table('void_rift', [
        p((3, 5), [(MC('chorus_fruit'), 5, 2, 8), (MC('ender_pearl'), 5, 1, 4), (C('shadow_essence'), 4, 1, 3), (MC('diamond'), 2, 1, 3),
                   (MC('end_crystal'), 1, 1, 1), (C('rune_of_wind'), 2, 1, 1)])])


# ---------------------------------------------------------------- Звездочёт
def trade(name, gives, gives_count, wants, wants_count, max_uses=12, xp=5, extra=None):
    obj = {'gives': {'id': gives, **({'count': gives_count} if gives_count > 1 else {})}, 'max_uses': max_uses,
           'reputation_discount': 0.05, 'wants': {'id': wants, **({'count': wants_count} if wants_count > 1 else {})}, 'xp': xp}
    obj.update(extra or {})
    write_json(os.path.join(DATA, 'villager_trade/stargazer', name + '.json'), obj)
    return c('stargazer/' + name)


def stargazer_trades():
    E = MC('emerald')
    levels = {
        1: [trade('starquartz_emerald', E, 1, C('starquartz'), 4, xp=2), trade('emerald_spyglass', MC('spyglass'), 1, E, 6),
            trade('star_fragment_emerald', E, 4, C('star_fragment'), 1, xp=4)],
        2: [trade('emerald_observatory_map', MC('filled_map'), 1, E, 10, max_uses=4, xp=10, extra={
                'additional_wants': {'id': MC('compass')},
                'given_item_modifier': [
                    {'type': 'minecraft:exploration_map', 'decoration': 'minecraft:target_x', 'destination': '#' + c('observatories'),
                     'search_radius': 100},
                    {'type': 'minecraft:set_name', 'name': {'translate': 'filled_map.celestial.observatory'}, 'target': 'item_name'},
                    {'type': 'minecraft:filtered', 'item_filter': {'predicates': {'minecraft:map_id': {}}}, 'on_fail': {'type': 'minecraft:discard'}}]}),
            trade('emerald_glowstone', MC('glowstone'), 4, E, 3)],
        3: [trade('emerald_radiant_stone', C('radiant_stone'), 4, E, 6), trade('emerald_star_fragment', C('star_fragment'), 1, E, 10, max_uses=4, xp=10)],
        4: [trade('emerald_rune_of_stars', C('rune_of_stars'), 1, E, 20, max_uses=3, xp=15, extra={'additional_wants': {'id': C('star_fragment'), 'count': 2}})],
        5: [trade('emerald_seraph_feather', C('seraph_feather'), 1, E, 30, max_uses=2, xp=20, extra={'additional_wants': {'id': C('star_fragment'), 'count': 4}})],
    }
    for lvl, trades in levels.items():
        write_json(os.path.join(DATA, 'tags/villager_trade/stargazer/level_' + str(lvl) + '.json'), {'values': trades})
        write_json(os.path.join(DATA, 'trade_set/stargazer/level_' + str(lvl) + '.json'), {
            'amount': 2, 'random_sequence': c(f'trade_set/stargazer/level_{lvl}'), 'trades': '#' + c(f'stargazer/level_{lvl}')})


def stargazer_textures():
    """Мантия Звездочёта: от ванильной развёртки берём только форму (альфа-канал), рисунок свой —
    тёмно-синяя ткань с шумом, золотая кайма по краям и редкие звёзды."""
    r = random.Random(77)
    navy = [T.hexrgb(h) for h in ('#1b2350', '#222c62', '#2a3674', '#1f2858')]
    gold, star = T.hexrgb('#c9a23a'), T.hexrgb('#ffe7a0')
    for kind in ('villager', 'zombie_villager'):
        src = os.path.join(VANILLA, 'entity', kind, 'profession', 'cartographer.png')
        if not os.path.exists(src):
            print('  нет', src, '— пропускаю текстуру', kind)
            continue
        mask = Image.open(src).convert('RGBA')
        img = Image.new('RGBA', mask.size, (0, 0, 0, 0))
        mp, px = mask.load(), img.load()
        for y in range(mask.height):
            for x in range(mask.width):
                if mp[x, y][3] == 0:
                    continue
                edge = any(0 <= x + dx < mask.width and 0 <= y + dy < mask.height and mp[x + dx, y + dy][3] == 0
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                c_ = gold if edge and y > 16 else star if r.random() < 0.03 else r.choice(navy)
                px[x, y] = (*c_, 255)
        save_png(img, f'entity/{kind}/profession/stargazer')


def telescope():
    brass, dark = '#c08a3e', '#3b4a6b'
    side = T.noisy('telescope_tube', [T.hexrgb(h) for h in ('#2f3c5a', '#3b4a6b', '#46577c')], cell=2, grain=0.2)
    for x in range(16):
        side.putpixel((x, 0), (*T.hexrgb(brass), 255))
        side.putpixel((x, 15), (*T.hexrgb(brass), 255))
        side.putpixel((x, 7), (*T.hexrgb('#e2b55e'), 255))
    save_png(side, 'block/telescope_tube')
    leg = T.noisy('telescope_leg', [T.hexrgb(h) for h in ('#7a5232', '#8a6238', '#6b4a2b')], cell=2, grain=0.3)
    save_png(leg, 'block/telescope_leg')
    lens = Image.new('RGBA', (16, 16), (*T.hexrgb(brass), 255))
    for y in range(3, 13):
        for x in range(3, 13):
            lens.putpixel((x, y), (*T.hexrgb('#bfe3ff' if (x + y) % 4 else '#ffffff'), 255))
    save_png(lens, 'block/telescope_lens')
    f6 = ('north', 'south', 'east', 'west', 'up', 'down')

    def box(fr, to, tex, rot=None, faces=f6):
        e = {'from': fr, 'to': to, 'faces': {d: {'texture': tex} for d in faces}}
        if rot:
            e['rotation'] = rot
        return e

    model('block/telescope', {'textures': {'tube': c('block/telescope_tube'), 'leg': c('block/telescope_leg'),
                                           'lens': c('block/telescope_lens'), 'particle': c('block/telescope_tube')},
                              'elements': [
                                  box([7, 0, 2], [9, 10, 4], '#leg', {'origin': [8, 10, 8], 'axis': 'x', 'angle': -22.5}),
                                  box([2, 0, 11], [4, 10, 13], '#leg', {'origin': [8, 10, 8], 'axis': 'z', 'angle': -22.5}),
                                  box([12, 0, 11], [14, 10, 13], '#leg', {'origin': [8, 10, 8], 'axis': 'z', 'angle': 22.5}),
                                  box([6, 9, 6], [10, 11, 10], '#leg'),
                                  {'from': [6, 10, 0], 'to': [10, 14, 16], 'rotation': {'origin': [8, 12, 8], 'axis': 'x', 'angle': 22.5},
                                   'faces': {'north': {'texture': '#lens'}, 'south': {'texture': '#lens'},
                                             'east': {'texture': '#tube'}, 'west': {'texture': '#tube'},
                                             'up': {'texture': '#tube'}, 'down': {'texture': '#tube'}}}]})
    blockstate('telescope', {'variants': {f'facing={f}': {'model': c('block/telescope'), **({'y': r} if r else {})}
                                          for f, r in (('north', 0), ('east', 90), ('south', 180), ('west', 270))}})
    item_def('telescope', c('block/telescope'))
    self_drop('telescope')
    shaped('telescope', c('telescope'), [' G ', 'CFC', 'S S'],
           {'G': MC('spyglass'), 'C': MC('copper_ingot'), 'F': c('star_fragment'), 'S': MC('stick')}, 1, 'misc')


def main():
    counts = {'обсерватория': observatory(), 'святилище': flame_sanctuary(), 'разлом': void_rift()}
    overworld = [MC(b) for b in ('plains', 'sunflower_plains', 'savanna', 'savanna_plateau', 'meadow', 'badlands', 'wooded_badlands',
                                 'desert', 'snowy_plains', 'windswept_hills', 'cherry_grove', 'forest', 'birch_forest')]
    jigsaw('observatory', overworld, 0)
    jigsaw('flame_sanctuary', [MC(b) for b in ('nether_wastes', 'basalt_deltas', 'crimson_forest', 'soul_sand_valley')], 28,
           project=False, adaptation='none')
    jigsaw('void_rift', [MC('end_highlands'), MC('end_midlands')], 0, adaptation='none')
    structure_set('observatory', 32, 10, 9120341)
    structure_set('flame_sanctuary', 22, 8, 9120342)
    structure_set('void_rift', 20, 6, 9120343)
    write_json(os.path.join(DATA, 'tags/worldgen/structure/observatories.json'), {'values': [c('observatory')]})
    write_json(os.path.join(DATA, 'tags/worldgen/structure/codex_places.json'), {'values': [
        c(n) for n in ('sky_village', 'sky_ruins', 'citadel', 'trial_tower', 'beam_temple', 'cloud_castle', 'sky_lighthouse',
                       'airship_wreck', 'observatory', 'flame_sanctuary', 'void_rift', 'abyss_rift')]})
    write_json(os.path.join(DATA.replace('celestial', 'minecraft'), 'tags/point_of_interest_type/acquirable_job_site.json'),
               {'replace': False, 'values': [c('stargazer')]})
    loot()
    stargazer_trades()
    stargazer_textures()
    telescope()
    names = {
        'block.celestial.telescope': ('Телескоп', 'Telescope'),
        'block.celestial.telescope.no_stars': ('Звёзд не видно: нужно ночное открытое небо', 'No stars visible: you need an open night sky'),
        'block.celestial.telescope.stage.0': ('Звёзды горят ярко. Угасания нет.', 'The stars shine bright. There is no Fading.'),
        'block.celestial.telescope.stage.1': ('Несколько звёзд погасли. Угасание: 1.', 'A few stars have gone out. Fading: 1.'),
        'block.celestial.telescope.stage.2': ('Созвездия тускнеют. Угасание: 2.', 'The constellations are dimming. Fading: 2.'),
        'block.celestial.telescope.stage.3': ('Половины звёзд уже нет. Угасание: 3.', 'Half the stars are gone. Fading: 3.'),
        'block.celestial.telescope.stage.4': ('Небо почти чёрное. Угасание: 4.', 'The sky is nearly black. Fading: 4.'),
        'block.celestial.telescope.stage.5': ('Остались считанные звёзды. Угасание: 5!', 'Only a handful of stars remain. Fading: 5!'),
        'block.celestial.telescope.observatory': ('Над горизонтом блестит купол обсерватории: %s, ~%s блоков.',
                                                  'An observatory dome glints on the horizon: %s, ~%s blocks.'),
        'direction.celestial.n': ('север', 'north'), 'direction.celestial.ne': ('северо-восток', 'north-east'),
        'direction.celestial.e': ('восток', 'east'), 'direction.celestial.se': ('юго-восток', 'south-east'),
        'direction.celestial.s': ('юг', 'south'), 'direction.celestial.sw': ('юго-запад', 'south-west'),
        'direction.celestial.w': ('запад', 'west'), 'direction.celestial.nw': ('северо-запад', 'north-west'),
        'entity.celestial.villager.stargazer': ('Звездочёт', 'Stargazer'),
        'filled_map.celestial.observatory': ('Карта Звёздной обсерватории', 'Star Observatory Map'),
        'structure.celestial.observatory': ('Звёздная обсерватория', 'Star Observatory'),
        'structure.celestial.flame_sanctuary': ('Пылающее святилище', 'Blazing Sanctuary'),
        'structure.celestial.void_rift': ('Разлом Пустоты', 'Void Rift'),
        'structure.celestial.telescope': ('Телескоп', 'Telescope'),
        'codex.celestial.place.observatory': ('башня звездочётов. Зажги все плитки-звёзды, чтобы открыть хранилище.',
                                              'the stargazers\' tower. Light every star tile to open the vault.'),
        'codex.celestial.place.flame_sanctuary': ('святилище над лавой Ада. Испытание огнём хранит Осколок Пламени.',
                                                  'a shrine above the Nether lava. Its trial of fire guards a Flame Shard.'),
        'codex.celestial.place.void_rift': ('разлом на окраинах Энда, откуда сочатся Тени.', 'a rift on the End\'s outskirts where Shadows seep through.'),
        'codex.celestial.place.telescope': ('через телескоп видно, сколько звёзд погасло.', 'a telescope shows how many stars have gone out.'),
        'trial.celestial.name.flame_sanctuary': ('Испытание огнём', 'Trial of Fire'),
        'trial.celestial.name.void_rift': ('Испытание Пустотой', 'Trial of the Void'),
    }
    lang_patch(names)
    print('ok: места Угасания', counts)


if __name__ == '__main__':
    main()
