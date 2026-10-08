"""Угасание (волна 0.2, шаг 9): Тень, метеорит, звёздный обломок, сгусток тьмы — текстуры, лут, теги, переводы."""
import json
import os

from PIL import Image

import mob_textures as M
import textures as T
from gen_assets import SILK, ASSETS, DATA, c, entity_loot, item_def, loot, model, save_png, simple_cube, shaped, write_json
from gen_story import lang_patch

FRAGMENT = {'1': '#3b2f5c', '2': '#6c58b0', '3': '#b9a6ff', '4': '#fff6d0', '5': '#ffb347'}
SPR = {
    'star_fragment': [
        '................',
        '................',
        '.........1......',
        '........121.....',
        '.......12321....',
        '......1234321...',
        '.....123444321..',
        '....12345443 1..',
        '...1234454321...',
        '...123444321....',
        '....1233321.....',
        '.....12221......',
        '......111.......',
        '................',
        '................',
        '................'],
    'shadow_essence': [
        '................',
        '................',
        '.......11.......',
        '......1221......',
        '.....122221.....',
        '....12233221....',
        '....12344321....',
        '...1233443321...',
        '...1234554321...',
        '...1233443321...',
        '....12344321....',
        '....12233221....',
        '.....122221.....',
        '......1111......',
        '................',
        '................'],
}
ESSENCE = {'1': '#0d0b14', '2': '#1f1830', '3': '#33284f', '4': '#55457e', '5': '#c9b8ff'}


def meteorite_texture():
    img = T.noisy('meteorite', [T.hexrgb(h) for h in ('#1d1a22', '#2a2530', '#352d3b', '#4a3c45')], cell=3, grain=0.45)
    r = T.rng_for('meteorite_glow')
    for _ in range(14):  # раскалённые прожилки и звёздные искры
        x, y = r.randrange(1, 15), r.randrange(1, 15)
        img.putpixel((x, y), (*T.hexrgb(r.choice(['#ff8a2a', '#ffb347', '#c9b8ff', '#fff3c6'])), 255))
    return img


def main():
    names = {
        'entity.celestial.shadow': ('Тень', 'Shadow'),
        'item.celestial.shadow_spawn_egg': ('Яйцо призыва Тени', 'Shadow Spawn Egg'),
        'block.celestial.meteorite': ('Метеоритное ядро', 'Meteorite Core'),
        'item.celestial.star_fragment': ('Звёздный обломок', 'Star Fragment'),
        'item.celestial.shadow_essence': ('Сгусток тьмы', 'Shadow Essence'),
        'structure.celestial.meteor_crater': ('Кратер метеорита', 'Meteor Crater'),
        'codex.celestial.mob.shadow': ('порождение Угасания. Горит на солнце, боится света, «перетекает» за спину.',
                                       'spawn of the Fading. Burns in sunlight, fears light, slips behind you.'),
        'codex.celestial.place.meteor_crater': ('след звездопада: метеоритное ядро, звёздный кварц.',
                                                'a starfall scar: a meteorite core and starquartz.'),
        'fading.celestial.grow.1': ('Свет мира чуть потускнел…', 'The world\'s light dims a little…'),
        'fading.celestial.grow.2': ('Ночи стали длиннее. Монстры — злее.', 'Nights grow longer. Monsters grow fiercer.'),
        'fading.celestial.grow.3': ('Во тьме шевелятся Тени. Угасание достигло третьей ступени.', 'Shadows stir in the dark. The Fading reaches its third stage.'),
        'fading.celestial.grow.4': ('Звёзды гаснут одна за другой. Тени приходят стаями.', 'Stars go out one by one. Shadows come in packs.'),
        'fading.celestial.grow.5': ('Мир почти погрузился во тьму. Последняя ступень Угасания.', 'The world is almost lost to darkness. The final stage of the Fading.'),
        'fading.celestial.weaken': ('Свет возвращается! Угасание отступило до ступени %s.', 'The light returns! The Fading recedes to stage %s.'),
        'fading.celestial.meteor_seen': ('По небу прочертила огненная полоса — что-то упало неподалёку!', 'A fiery streak crosses the sky — something fell nearby!'),
        'fading.celestial.meteor_landed': ('Метеорит упал у %s %s %s.', 'A meteorite landed near %s %s %s.'),
    }

    save_png(M.spawn_egg('#1b1726', '#c9a8ff'), 'item/shadow_spawn_egg')
    model('item/shadow_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/shadow_spawn_egg')}})
    item_def('shadow_spawn_egg', c('item/shadow_spawn_egg'))
    for k, rows in SPR.items():
        save_png(T.sprite(rows, FRAGMENT if k == 'star_fragment' else ESSENCE), 'item/' + k)
        model('item/' + k, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + k)}})
        item_def(k, c('item/' + k))

    save_png(meteorite_texture(), 'block/meteorite')
    simple_cube('meteorite')
    silk = SILK
    loot('meteorite', [
        {'entries': [{'type': 'minecraft:alternatives', 'children': [
            {'type': 'minecraft:item', 'condition': silk, 'name': c('meteorite')},
            {'type': 'minecraft:item', 'name': c('starquartz'), 'modifier': [
                {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 3, 'max': 6}},
                {'type': 'minecraft:apply_bonus', 'enchantment': 'minecraft:fortune', 'formula': 'minecraft:ore_drops'}]}]}], 'rolls': 1},
        {'condition': {'type': 'minecraft:inverted', 'term': silk},
         'entries': [{'type': 'minecraft:item', 'name': c('star_fragment')}], 'rolls': 1},
        {'condition': {'type': 'minecraft:inverted', 'term': silk},
         'entries': [{'type': 'minecraft:item', 'name': 'minecraft:iron_nugget', 'modifier': [
             {'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': 4, 'max': 9}}]}], 'rolls': 1},
    ])
    entity_loot('shadow', [(c('shadow_essence'), 0, 1), ('minecraft:phantom_membrane', 1, 1, 0.1)])

    def add_tag(kind, ns_path, values):
        ns, path = ns_path.split(':')
        base = os.path.join(DATA.replace('celestial', ns), 'tags', kind, path + '.json')
        existing = []
        if os.path.exists(base):
            with open(base) as f:
                existing = json.load(f)['values']
        write_json(base, {'replace': False, 'values': list(dict.fromkeys(existing + values))})

    add_tag('entity_type', 'minecraft:undead', [c('shadow')])
    add_tag('entity_type', 'minecraft:burn_in_daylight', [c('shadow')])
    add_tag('block', 'minecraft:mineable/pickaxe', [c('meteorite')])
    add_tag('block', 'minecraft:needs_iron_tool', [c('meteorite')])
    lang_patch(names)
    print('ok: Угасание,', len(names), 'строк')


if __name__ == '__main__':
    main()
