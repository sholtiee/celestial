#!/usr/bin/env python3
"""Светотехника и загадки: текстуры, модели (с поворотами по blockstate), рецепты, лут, тексты загадок.

Запуск: python3 tools/gen_mechanics.py (после gen_assets.py).
"""
import json
import math
import os

from PIL import Image

import textures as T
from gen_assets import (ASSETS, DATA, blockstate, c, item_def, model, save_png, self_drop, shaped, shapeless, write_json, TAGS, tag)
from gen_story import lang_patch

FACING_ROT = {  # поворот модели «смотрит на север» под FACING
    'north': {}, 'south': {'y': 180}, 'east': {'y': 90}, 'west': {'y': 270},
    'up': {'x': 270}, 'down': {'x': 90},
}


def frame_texture(name, inner, rim='#c9a23a', glow=None):
    r = T.rng_for(name)
    img = Image.new('RGBA', (16, 16))
    rim_c, inner_c = T.hexrgb(rim), T.hexrgb(inner)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            if edge:
                img.putpixel((x, y), (*T.shade(rim_c, 0.85 + r.random() * 0.2), 255))
            else:
                d = math.hypot(x - 7.5, y - 7.5)
                c = T.mix(T.hexrgb(glow), inner_c, min(1, d / 6)) if glow else inner_c
                img.putpixel((x, y), (*T.shade(c, 0.9 + r.random() * 0.15), 255))
    return img


def side_texture(name, base='#b7b2a6'):
    return T.bricks(name, [T.hexrgb(h) for h in ('#cfd6e0', '#dce2ea', '#e7ecf2')], '#c9a23a')


def glass(color, alpha=150):
    img = Image.new('RGBA', (16, 16))
    c_ = T.hexrgb(color)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            img.putpixel((x, y), (*T.shade(c_, 0.7), 230) if edge else (*c_, alpha if (x + y) % 5 else alpha + 50))
    return img


def facing_block(name, front, side, states_extra=None, facing_values=('north', 'south', 'east', 'west', 'up', 'down')):
    """Блок с лицевой стороной: front_<суффикс> по состояниям."""
    variants = {}
    for f in facing_values:
        for suffix, props in (states_extra or {'': ''}).items():
            key = f'facing={f}' + (',' + props if props else '')
            variants[key] = {'model': c(f'block/{name}{suffix}'), **FACING_ROT[f]}
    blockstate(name, {'variants': variants})


def enchantment(name, ru, en, slots, supported, max_level, effects, exclusive=None):
    """Небесное зачарование: только через Алтарь наделения (нет в тегах стола зачарований и добычи)."""
    e = {'anvil_cost': 4, 'description': {'translate': f'enchantment.celestial.{name}'}, 'effects': effects,
         'max_cost': {'base': 60, 'per_level_above_first': 20}, 'min_cost': {'base': 30, 'per_level_above_first': 20},
         'max_level': max_level, 'slots': slots, 'supported_items': supported, 'weight': 1}
    if exclusive:
        e['exclusive_set'] = exclusive
    write_json(os.path.join(DATA, 'enchantment', name + '.json'), e)
    return {f'enchantment.celestial.{name}': (ru, en)}


def lin(base, per):
    return {'type': 'minecraft:linear', 'base': base, 'per_level_above_first': per}


def machines(names):
    # --- небесные зачарования
    names.update(enchantment('heavenly_step', 'Небесная поступь', 'Heavenly Step', ['feet'], '#minecraft:enchantable/foot_armor', 2, {
        'minecraft:attributes': [
            {'id': 'celestial:enchantment.heavenly_step_gravity', 'attribute': 'minecraft:gravity', 'amount': lin(-0.1, -0.1),
             'operation': 'add_multiplied_base'},
            {'id': 'celestial:enchantment.heavenly_step_fall', 'attribute': 'minecraft:safe_fall_distance', 'amount': lin(3.0, 3.0),
             'operation': 'add_value'}]}))
    names.update(enchantment('windstride', 'Попутный ветер', 'Windstride', ['legs'], '#minecraft:enchantable/leg_armor', 3, {
        'minecraft:attributes': [{'id': 'celestial:enchantment.windstride', 'attribute': 'minecraft:movement_speed', 'amount': lin(0.06, 0.06),
                                  'operation': 'add_multiplied_base'}]}))
    names.update(enchantment('radiance', 'Светоносность', 'Radiance', ['mainhand'], '#minecraft:enchantable/weapon', 3, {
        'minecraft:damage': [{'effect': {'type': 'minecraft:add', 'value': lin(3.0, 2.5)},
                              'requirements': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                               'predicate': {'minecraft:entity_type': '#minecraft:undead'}}}],
        'minecraft:post_attack': [{'affected': 'victim', 'enchanted': 'attacker', 'effect': {
            'type': 'minecraft:apply_mob_effect', 'to_apply': 'minecraft:glowing', 'min_duration': 3, 'max_duration': lin(4.0, 2.0),
            'min_amplifier': 0, 'max_amplifier': 0}}]}))
    names.update(enchantment('grace_strike', 'Удар благодати', 'Grace Strike', ['mainhand'], '#minecraft:enchantable/weapon', 1, {
        'minecraft:post_attack': [{'affected': 'attacker', 'enchanted': 'attacker', 'effect': {
            'type': 'minecraft:apply_mob_effect', 'to_apply': 'minecraft:regeneration', 'min_duration': 2, 'max_duration': 3,
            'min_amplifier': 0, 'max_amplifier': 0}}]}))
    names.update(enchantment('featherweight', 'Лёгкость пера', 'Featherweight', ['chest'], '#minecraft:enchantable/chest_armor', 1, {
        'minecraft:attributes': [{'id': 'celestial:enchantment.featherweight', 'attribute': 'minecraft:fall_damage_multiplier',
                                  'amount': -0.5, 'operation': 'add_multiplied_total'}]}))
    names.update(enchantment('farsight', 'Небесный взор', 'Farsight', ['head'], '#minecraft:enchantable/head_armor', 2, {
        'minecraft:attributes': [
            {'id': 'celestial:enchantment.farsight_block', 'attribute': 'minecraft:block_interaction_range', 'amount': lin(1.0, 1.0), 'operation': 'add_value'},
            {'id': 'celestial:enchantment.farsight_entity', 'attribute': 'minecraft:entity_interaction_range', 'amount': lin(0.5, 0.5), 'operation': 'add_value'}]}))
    names.update(enchantment('starbreaker', 'Звездолом', 'Starbreaker', ['mainhand'], '#minecraft:enchantable/mining', 3, {
        'minecraft:attributes': [{'id': 'celestial:enchantment.starbreaker', 'attribute': 'minecraft:block_break_speed', 'amount': lin(0.15, 0.15),
                                  'operation': 'add_multiplied_base'}]}))

    # --- машины: текстуры и модели
    save_png(T.cloud('cloud_lift', T.CLOUD, 255), 'block/cloud_lift')
    save_png(T.cloud('cloud_lift_on', T.GOLD_CLOUD, 255), 'block/cloud_lift_on')
    for suffix in ('', '_on'):
        model('block/cloud_lift' + suffix, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/cloud_lift' + suffix), 'side': c('block/cloud'), 'bottom': c('block/cloud')}})
    blockstate('cloud_lift', {'variants': {'lit=false': {'model': c('block/cloud_lift')}, 'lit=true': {'model': c('block/cloud_lift_on')}}})
    item_def('cloud_lift', c('block/cloud_lift'))
    self_drop('cloud_lift')
    names['block.celestial.cloud_lift'] = ('Облачный лифт', 'Cloud Lift')

    save_png(T.metal_block([T.hexrgb(h) for h in ('#8a5a1e', '#c9a23a', '#e8b84a', '#f3d27a', '#fff3c6')]), 'block/celestial_forge_side')
    save_png(frame_texture('forge_top', '#3a2f42', glow='#ff9a4a'), 'block/celestial_forge_top')
    model('block/celestial_forge', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/celestial_forge_top'), 'side': c('block/celestial_forge_side'), 'bottom': c('block/celestial_forge_side')}})
    save_png(crystal_like('infusion_side'), 'block/infusion_altar_side')
    save_png(frame_texture('infusion_top', '#2a4190', glow='#bff6ff'), 'block/infusion_altar_top')
    model('block/infusion_altar', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/infusion_altar_top'), 'side': c('block/infusion_altar_side'), 'bottom': c('block/infusion_altar_side')}})
    save_png(frame_texture('sky_beacon_top', '#fff6d8', glow='#ffffff'), 'block/sky_beacon_top')
    save_png(T.bricks('sky_beacon_side', [T.hexrgb(h) for h in ('#e8b84a', '#f3cf6a', '#fde48f')], '#fff6d8'), 'block/sky_beacon_side')
    model('block/sky_beacon', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/sky_beacon_top'), 'side': c('block/sky_beacon_side'), 'bottom': c('block/sky_beacon_side')}})
    for n, ru, en in (('celestial_forge', 'Небесная кузня', 'Celestial Forge'), ('infusion_altar', 'Алтарь наделения', 'Infusion Altar'),
                      ('sky_beacon', 'Небесный маяк', 'Sky Beacon')):
        blockstate(n, {'variants': {'': {'model': c('block/' + n)}}})
        item_def(n, c('block/' + n))
        self_drop(n)
        names[f'block.celestial.{n}'] = (ru, en)
        tag('block', 'minecraft:mineable/pickaxe', c(n))
        tag('block', 'minecraft:needs_iron_tool', c(n))

    # --- руны
    rune_rows = [
        '................', '....11111111....', '...1222222221...', '..122233332221..', '..122322223221..', '..122223322221..',
        '..122232222221..', '..122223322221..', '..122222232221..', '..122233332221..', '..122222222221..', '...1222222221...',
        '....11111111....', '................', '................', '................']
    for rune, (glyph, ru, en, desc_ru, desc_en) in {
        'rune_of_wind': ('#bfe9ff', 'Руна ветра', 'Rune of Wind', 'Ботинки: Небесная поступь, поножи: Попутный ветер', 'Boots: Heavenly Step, leggings: Windstride'),
        'rune_of_light': ('#ffe08a', 'Руна света', 'Rune of Light', 'Оружие: Светоносность, затем Удар благодати', 'Weapon: Radiance, then Grace Strike'),
        'rune_of_sky': ('#ffffff', 'Руна неба', 'Rune of Sky', 'Нагрудник: Лёгкость пера, шлем: Небесный взор', 'Chestplate: Featherweight, helmet: Farsight'),
        'rune_of_stars': ('#c7a8ff', 'Руна звёзд', 'Rune of Stars', 'Инструменты: Звездолом', 'Tools: Starbreaker')}.items():
        save_png(T.sprite(rune_rows, {'1': '#5f6b88', '2': '#adb8c8', '3': glyph}), 'item/' + rune)
        model('item/' + rune, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + rune)}})
        item_def(rune, c('item/' + rune))
        names[f'item.celestial.{rune}'] = (ru, en)
        names[f'item.celestial.{rune}.lore1'] = (desc_ru, desc_en)

    # --- рецепты машин и рун
    Q, E = c('starquartz'), c('etherite_ingot')
    shaped('cloud_lift', c('cloud_lift'), ['CCC', 'CQC', 'CCC'], {'C': c('cloud'), 'Q': Q}, 2, 'redstone')
    shaped('celestial_forge', c('celestial_forge'), ['EEE', 'QAQ', 'RRR'], {'E': E, 'Q': Q, 'A': 'minecraft:anvil', 'R': c('radiant_stone')}, 1, 'misc')
    shaped('infusion_altar', c('infusion_altar'), [' B ', 'QSQ', 'RRR'], {'B': 'minecraft:book', 'Q': Q, 'S': c('sky_crystal_block'),
                                                                        'R': c('radiant_stone')}, 1, 'misc')
    shaped('sky_beacon', c('sky_beacon'), ['QGQ', 'GEG', 'RRR'], {'Q': Q, 'G': 'minecraft:glass', 'E': 'minecraft:ender_pearl',
                                                                'R': c('radiant_stone')}, 1, 'misc')
    for rune, mat in (('rune_of_wind', c('cloud_fluff')), ('rune_of_light', 'minecraft:glowstone_dust'), ('rune_of_sky', c('seraph_feather')),
                      ('rune_of_stars', c('sky_crystal'))):
        shaped(rune, c(rune), [' Q ', 'QMQ', ' S '], {'Q': Q, 'M': mat, 'S': c('skystone')}, 1, 'misc')

    names.update({
        'machine.celestial.forge.incomplete': ('Кузня не собрана: нужны 4 блока светлого камня по сторонам ядра',
                                               'The forge is incomplete: place 4 Radiant Stone around the core'),
        'machine.celestial.forge.no_light': ('Нет света! Направь в машину луч Солнечной линзы (у кузни — сверху)', 'No light! Aim a Sun Lens beam at the machine (from above for the forge)'),
        'machine.celestial.forge.cost_upgrade': ('Нужно 2 эфиритовых слитка и звёздный кварц', 'Requires 2 etherite ingots and a starquartz'),
        'machine.celestial.forge.cost_repair': ('Для перековки нужен звёздный кварц', 'Reforging requires a starquartz'),
        'machine.celestial.forge.hint': ('Кузня принимает алмазное снаряжение (улучшение) и повреждённые вещи Рая (перековка)',
                                         'The forge takes diamond gear (upgrade) and damaged Heaven gear (reforge)'),
        'machine.celestial.forge.done': ('✦ Кузня сделала своё дело', '✦ The forge has done its work'),
        'machine.celestial.infusion.hint': ('Возьми руну в другую руку и нажми снаряжением по алтарю', 'Hold a rune in your other hand and use gear on the altar'),
        'machine.celestial.infusion.xp': ('Нужно 3 уровня опыта', 'Requires 3 experience levels'),
        'machine.celestial.infusion.max': ('Это зачарование уже на максимуме', 'That enchantment is already at max level'),
        'machine.celestial.infusion.unsuitable': ('Эта руна не подходит к этому предмету', 'This rune does not fit this item'),
        'machine.celestial.infusion.done': ('✦ Вплетено: %s', '✦ Infused: %s'),
        'machine.celestial.beacon.header': ('✦ Сеть Небесных маяков (нажми на строку, чтобы перенестись):', '✦ Sky Beacon network (click a line to travel):'),
        'machine.celestial.beacon.click': ('Перенестись сюда', 'Travel here'),
        'machine.celestial.beacon.too_far': ('Встань рядом с Небесным маяком', 'Stand next to a Sky Beacon'),
        'machine.celestial.beacon.lost': ('Этот маяк погас', 'That beacon has gone dark'),
    })


def trials(names):
    # кристалл испытания: тускло-голубой (ждёт), яркий (идёт), золотой (пройдено)
    for st, inner, glow in (('idle', '#3a55b0', '#93c5fd'), ('running', '#bfe9ff', '#ffffff'), ('done', '#f3c64a', '#fff6cf')):
        save_png(frame_texture('trial_crystal_' + st, inner, rim='#c9a23a', glow=glow), f'block/trial_crystal_{st}')
        model(f'block/trial_crystal_{st}', {'textures': {'t': c(f'block/trial_crystal_{st}'), 'b': c('block/skystone_bricks'),
                                                          'particle': c(f'block/trial_crystal_{st}')}, 'elements': [
            {'from': [1, 0, 1], 'to': [15, 3, 15], 'faces': {d: {'texture': '#b'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
            {'from': [4, 3, 4], 'to': [12, 15, 12], 'faces': {d: {'texture': '#t'} for d in ('north', 'south', 'east', 'west', 'up')}}]})
    blockstate('trial_crystal', {'variants': {f'state={st}': {'model': c(f'block/trial_crystal_{st}')} for st in ('idle', 'running', 'done')}})
    item_def('trial_crystal', c('block/trial_crystal_idle'))
    save_png(frame_texture('trial_goal', '#93c5fd', rim='#ffffff', glow='#ffffff'), 'block/trial_goal')
    blockstate('trial_goal', {'variants': {'': {'model': c('block/trial_goal')}}})
    model('block/trial_goal', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/trial_goal')}})
    item_def('trial_goal', c('block/trial_goal'))
    save_png(T.cloud('vanishing_cloud', [T.hexrgb(h) for h in ('#f0e6ff', '#f6efff', '#fbf7ff', '#ffffff')], 200), 'block/vanishing_cloud')
    model('block/vanishing_cloud', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/vanishing_cloud')}})
    model('block/vanishing_cloud_gone', {'textures': {'particle': c('block/vanishing_cloud')}, 'elements': []})
    blockstate('vanishing_cloud', {'variants': {'vanished=false': {'model': c('block/vanishing_cloud')},
                                                'vanished=true': {'model': c('block/vanishing_cloud_gone')}}})
    item_def('vanishing_cloud', c('block/vanishing_cloud'))
    trial_names = ['Врата испытаний', 'Тающие облака', 'Путь луча', 'Песнь колоколов', 'Лестница в небо', 'Без доспехов', 'Гнев бури']
    trial_names_en = ['Gate of Trials', 'Melting Clouds', 'Path of the Beam', 'Song of Bells', 'Stairway to the Sky', 'Unarmored', 'Wrath of the Storm']
    for i, (ru, en) in enumerate(zip(trial_names, trial_names_en), 1):
        names[f'trial.celestial.name.heaven_{i}'] = (f'Испытание {i}: {ru}', f'Trial {i}: {en}')
    names.update({
        'block.celestial.trial_crystal': ('Кристалл испытания', 'Trial Crystal'),
        'block.celestial.trial_goal': ('Финишный кристалл', 'Finish Crystal'),
        'block.celestial.vanishing_cloud': ('Исчезающее облако', 'Vanishing Cloud'),
        'trial.celestial.start.waves': ('§6Испытание началось: одолей все волны!', '§6The trial begins: defeat every wave!'),
        'trial.celestial.start.bare_waves': ('§6Испытание началось: сражайся без доспехов!', '§6The trial begins: fight without armor!'),
        'trial.celestial.start.parkour': ('§6Испытание началось: доберись до Финишного кристалла, пока не вышло время!',
                                          '§6The trial begins: reach the Finish Crystal before time runs out!'),
        'trial.celestial.start.puzzle': ('§6Испытание началось: разгадай загадку этажа!', '§6The trial begins: solve the floor puzzle!'),
        'trial.celestial.success': ('§a✦ %s пройдено! Благодать +%s', '§a✦ %s complete! Grace +%s'),
        'trial.celestial.done_already': ('Это испытание уже пройдено', 'This trial is already complete'),
        'trial.celestial.busy': ('Испытание уже идёт', 'The trial is already running'),
        'trial.celestial.remove_armor': ('§cСними доспехи, чтобы начать это испытание', '§cRemove your armor to begin this trial'),
        'trial.celestial.fail.left': ('§cИспытание провалено: ты покинул арену', '§cTrial failed: you left the arena'),
        'trial.celestial.fail.armor': ('§cИспытание провалено: ты надел доспехи', '§cTrial failed: you put on armor'),
        'trial.celestial.fail.time': ('§cИспытание провалено: время вышло', '§cTrial failed: time is up'),
    })


def crystal_like(name):
    img = T.noisy(name, [T.hexrgb(h) for h in ('#2a4190', '#3a55b0', '#4d6bd0', '#93c5fd')], cell=4, grain=0.4)
    return img


def main():
    names = {}

    # --- источники луча: линза и фонарь (facing × active)
    for name, glow in (('sun_lens', '#fff3b0'), ('beam_lantern', '#ffd6a8')):
        save_png(frame_texture(name + '_front', '#5f6b88', glow=None), f'block/{name}_front')
        save_png(frame_texture(name + '_front_on', '#fff6d8', glow=glow), f'block/{name}_front_on')
        save_png(side_texture(name + '_side'), f'block/{name}_side')
        for suffix, front in (('', f'block/{name}_front'), ('_on', f'block/{name}_front_on')):
            model(f'block/{name}{suffix}', {'parent': 'minecraft:block/orientable_with_bottom', 'textures': {
                'front': c(front), 'side': c(f'block/{name}_side'), 'top': c(f'block/{name}_side'), 'bottom': c(f'block/{name}_side')}})
        facing_block(name, None, None, {'': 'active=false', '_on': 'active=true'})
        item_def(name, c(f'block/{name}_on'))
        self_drop(name)
    names['block.celestial.sun_lens'] = ('Солнечная линза', 'Sun Lens')
    names['block.celestial.beam_lantern'] = ('Световой фонарь', 'Beam Lantern')

    # --- зеркало: диагональная пластина (элемент, повёрнутый на 45°)
    save_png(glass('#dfe9f5', 210), 'block/beam_mirror')
    save_png(side_texture('mirror_base'), 'block/beam_mirror_base')
    mirror_model = {'textures': {'mirror': c('block/beam_mirror'), 'base': c('block/beam_mirror_base'), 'particle': c('block/beam_mirror')},
                    'elements': [
                        {'from': [0, 0, 0], 'to': [16, 2, 16], 'faces': {d: {'texture': '#base'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
                        {'from': [7.5, 2, 0], 'to': [8.5, 16, 16], 'rotation': {'origin': [8, 8, 8], 'axis': 'y', 'angle': 45, 'rescale': True},
                         'faces': {d: {'texture': '#mirror', 'uv': [0, 0, 16, 16] if d in ('east', 'west') else [7, 0, 9, 16]}
                                   for d in ('east', 'west', 'north', 'south', 'up')}}]}
    model('block/beam_mirror', mirror_model)
    blockstate('beam_mirror', {'variants': {'flipped=false': {'model': c('block/beam_mirror')},
                                            'flipped=true': {'model': c('block/beam_mirror'), 'y': 90}}})
    item_def('beam_mirror', c('block/beam_mirror'))
    self_drop('beam_mirror')
    names['block.celestial.beam_mirror'] = ('Зеркало света', 'Light Mirror')

    # --- призма и фильтры (полупрозрачные)
    prism = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            hue = (x + y) / 30
            r_ = int(200 + 55 * math.sin(hue * 6.28)); g_ = int(200 + 55 * math.sin(hue * 6.28 + 2)); b_ = int(200 + 55 * math.sin(hue * 6.28 + 4))
            prism.putpixel((x, y), (min(255, r_), min(255, g_), min(255, b_), 200 if 0 < x < 15 and 0 < y < 15 else 255))
    save_png(prism, 'block/beam_prism')
    for name, color, ru, en in (('beam_prism', None, 'Призма', 'Prism'), ('red_filter', '#ff5a4a', 'Красный фильтр', 'Red Filter'),
                                ('green_filter', '#6cff7a', 'Зелёный фильтр', 'Green Filter'), ('blue_filter', '#5aa8ff', 'Синий фильтр', 'Blue Filter')):
        if color:
            save_png(glass(color), f'block/{name}')
        blockstate(name, {'variants': {'': {'model': c(f'block/{name}')}}})
        model(f'block/{name}', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c(f'block/{name}')}})
        item_def(name, c(f'block/{name}'))
        self_drop(name)
        names[f'block.celestial.{name}'] = (ru, en)

    # --- перископ (facing × up)
    save_png(frame_texture('periscope_front', '#dfe9f5', rim='#9aa6b8'), 'block/periscope_front')
    save_png(side_texture('periscope_side'), 'block/periscope_side')
    save_png(frame_texture('periscope_top', '#fff6d8', rim='#9aa6b8'), 'block/periscope_top')
    for suffix, top in (('_up', 'block/periscope_top'), ('_down', 'block/periscope_side')):
        model(f'block/periscope{suffix}', {'parent': 'minecraft:block/orientable_with_bottom', 'textures': {
            'front': c('block/periscope_front'), 'side': c('block/periscope_side'),
            'top': c(top), 'bottom': c('block/periscope_top' if suffix == '_down' else 'block/periscope_side')}})
    variants = {}
    for f in ('north', 'south', 'east', 'west'):
        for up in ('true', 'false'):
            variants[f'facing={f},up={up}'] = {'model': c('block/periscope_up' if up == 'true' else 'block/periscope_down'), **FACING_ROT[f]}
    blockstate('periscope', {'variants': variants})
    item_def('periscope', c('block/periscope_up'))
    self_drop('periscope')
    names['block.celestial.periscope'] = ('Перископ', 'Periscope')

    # --- приёмник света (color × powered)
    colors = {'white': '#fff6d8', 'red': '#ff5a4a', 'green': '#6cff7a', 'blue': '#5aa8ff'}
    variants = {}
    for col, hexc in colors.items():
        for powered in ('false', 'true'):
            tex = f'light_receiver_{col}' + ('_on' if powered == 'true' else '')
            dim = '#%02x%02x%02x' % T.mix(T.hexrgb(hexc), T.hexrgb('#3a3446'), 0.6)
            save_png(frame_texture(tex, hexc if powered == 'true' else dim, glow='#ffffff' if powered == 'true' else None), 'block/' + tex)
            model('block/' + tex, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + tex)}})
            variants[f'color={col},powered={powered}'] = {'model': c('block/' + tex)}
    blockstate('light_receiver', {'variants': variants})
    item_def('light_receiver', c('block/light_receiver_white'))
    self_drop('light_receiver')
    names['block.celestial.light_receiver'] = ('Приёмник света', 'Light Receiver')

    # --- печать-дверь
    door = T.radiant_stone()
    for i in range(3, 13):
        door.putpixel((i, 3), (*T.hexrgb('#8a5a1e'), 255)); door.putpixel((i, 12), (*T.hexrgb('#8a5a1e'), 255))
        door.putpixel((3, i), (*T.hexrgb('#8a5a1e'), 255)); door.putpixel((12, i), (*T.hexrgb('#8a5a1e'), 255))
    door.putpixel((7, 7), (*T.hexrgb('#ffffff'), 255)); door.putpixel((8, 8), (*T.hexrgb('#ffffff'), 255))
    save_png(door, 'block/sealed_door')
    blockstate('sealed_door', {'variants': {'': {'model': c('block/sealed_door')}}})
    model('block/sealed_door', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/sealed_door')}})
    item_def('sealed_door', c('block/sealed_door'))
    names['block.celestial.sealed_door'] = ('Печать-дверь', 'Sealed Door')

    # --- колокол (5 нот — разный цвет пояска)
    note_colors = ['#ff6b6b', '#ffb36b', '#ffe66b', '#6bffb3', '#6bb3ff']
    variants = {}
    for n, band in enumerate(note_colors):
        tex = Image.new('RGBA', (16, 16))
        for y in range(16):
            for x in range(16):
                base = T.hexrgb('#e8b84a') if y not in (10, 11) else T.hexrgb(band)
                tex.putpixel((x, y), (*T.shade(base, 0.85 + 0.15 * math.sin(x * 0.7)), 255))
        save_png(tex, f'block/sky_bell_{n}')
        model(f'block/sky_bell_{n}', {'textures': {'bell': c(f'block/sky_bell_{n}'), 'particle': c(f'block/sky_bell_{n}')}, 'elements': [
            {'from': [3, 2, 3], 'to': [13, 4, 13], 'faces': {d: {'texture': '#bell'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
            {'from': [4, 4, 4], 'to': [12, 12, 12], 'faces': {d: {'texture': '#bell'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}},
            {'from': [6, 12, 6], 'to': [10, 15, 10], 'faces': {d: {'texture': '#bell'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}}]})
        variants[f'note={n}'] = {'model': c(f'block/sky_bell_{n}')}
    blockstate('sky_bell', {'variants': variants})
    item_def('sky_bell', c('block/sky_bell_2'))
    write_json(os.path.join(DATA, 'loot_table/blocks/sky_bell.json'), {'type': 'minecraft:block', 'pools': [
        {'rolls': 1, 'condition': {'type': 'minecraft:survives_explosion'}, 'entries': [{'type': 'minecraft:item', 'name': c('sky_bell')}]}],
        'random_sequence': c('blocks/sky_bell')})
    names['block.celestial.sky_bell'] = ('Небесный колокол', 'Sky Bell')

    # --- колокольный алтарь, рунный пьедестал, плитка-звезда
    for name, base_tex, ru, en, prop, extra in (
            ('bell_altar', 'sky_bell_2', 'Колокольный алтарь', 'Bell Altar', 'solved', None),
            ('rune_pedestal', 'radiant_stone', 'Рунный пьедестал', 'Rune Pedestal', 'solved', 'riddle'),
            ('star_tile', None, 'Плитка-звезда', 'Star Tile', None, None)):
        names[f'block.celestial.{name}'] = (ru, en)
    with open(os.path.join(ASSETS, 'models/block/celestial_altar.json')) as f:
        altar = json.load(f)
    for solved in ('false', 'true'):
        m = json.loads(json.dumps(altar))
        m['textures']['top'] = c('block/sky_bell_4' if solved == 'true' else 'block/sky_bell_2')
        model(f'block/bell_altar{"_solved" if solved == "true" else ""}', m)
        m2 = json.loads(json.dumps(altar))
        m2['textures']['top'] = c('block/seraph_seal' if solved == 'true' else 'block/radiant_stone')
        model(f'block/rune_pedestal{"_solved" if solved == "true" else ""}', m2)
    blockstate('bell_altar', {'variants': {'solved=false': {'model': c('block/bell_altar')}, 'solved=true': {'model': c('block/bell_altar_solved')}}})
    blockstate('rune_pedestal', {'variants': {f'riddle={i},solved={s}': {'model': c('block/rune_pedestal' + ('_solved' if s == 'true' else ''))}
                                              for i in range(8) for s in ('false', 'true')}})
    item_def('bell_altar', c('block/bell_altar'))
    item_def('rune_pedestal', c('block/rune_pedestal'))
    tile_variants = {}
    for lit in ('false', 'true'):
        for solved in ('false', 'true'):
            tex_name = 'star_tile' + ('_lit' if lit == 'true' else '') + ('_solved' if solved == 'true' else '')
            img = Image.new('RGBA', (16, 16))
            base = '#ffe08a' if solved == 'true' else ('#bfe9ff' if lit == 'true' else '#2a3150')
            for y in range(16):
                for x in range(16):
                    edge = x in (0, 15) or y in (0, 15)
                    star = (x in (7, 8) and 3 <= y <= 12) or (y in (7, 8) and 3 <= x <= 12) or abs(x - y) <= 0 and 4 <= x <= 11
                    col = T.hexrgb('#141a30') if edge else (T.hexrgb('#ffffff') if star and lit == 'true' else T.hexrgb(base))
                    img.putpixel((x, y), (*col, 255))
            save_png(img, 'block/' + tex_name)
            model('block/' + tex_name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + tex_name)}})
            tile_variants[f'lit={lit},solved={solved}'] = {'model': c('block/' + tex_name)}
    blockstate('star_tile', {'variants': tile_variants})
    item_def('star_tile', c('block/star_tile'))

    # --- Камертон
    fork = T.sprite([
        '................', '...11.....11....', '...12.....21....', '...12.....21....', '...12.....21....', '...12.....21....',
        '...122...221....', '....1222221.....', '......121.......', '......121.......', '......121.......', '......131.......',
        '.....13331......', '.....13331......', '......111.......', '................'], {'1': '#8e99a8', '2': '#eef2f7', '3': '#c9a23a'})
    save_png(fork, 'item/tuning_fork')
    model('item/tuning_fork', {'parent': 'minecraft:item/handheld', 'textures': {'layer0': c('item/tuning_fork')}})
    item_def('tuning_fork', c('item/tuning_fork'))
    names['item.celestial.tuning_fork'] = ('Камертон', 'Tuning Fork')
    names['item.celestial.tuning_fork.lore1'] = ('ПКМ по линзе, зеркалу, перископу или приёмнику — повернуть / сменить цвет',
                                                 'Right-click a lens, mirror, periscope or receiver to rotate / recolor')

    for n in ('sun_lens', 'beam_lantern', 'beam_mirror', 'beam_prism', 'periscope', 'light_receiver', 'sky_bell', 'red_filter', 'green_filter', 'blue_filter'):
        tag('block', 'minecraft:mineable/pickaxe', c(n))

    # --- рецепты
    Q, G = c('starquartz'), 'minecraft:gold_ingot'
    shaped('sun_lens', c('sun_lens'), ['GQG', 'QLQ', 'GQG'], {'G': G, 'Q': Q, 'L': 'minecraft:glass'}, 1, 'redstone')
    shapeless('beam_lantern', c('beam_lantern'), [c('sun_lens'), 'minecraft:redstone_torch'], 1, 'redstone')
    shaped('beam_mirror', c('beam_mirror'), ['LI', 'IL'], {'L': 'minecraft:glass', 'I': 'minecraft:iron_ingot'}, 2, 'redstone')
    shaped('beam_prism', c('beam_prism'), ['LQL', 'QDQ', 'LQL'], {'L': 'minecraft:glass', 'Q': Q, 'D': 'minecraft:diamond'}, 1, 'redstone')
    for col, dye in (('red', 'minecraft:red_dye'), ('green', 'minecraft:lime_dye'), ('blue', 'minecraft:light_blue_dye')):
        shapeless(f'{col}_filter', c(f'{col}_filter'), ['minecraft:glass', dye, Q], 2, 'redstone')
    shaped('periscope', c('periscope'), ['I', 'M', 'I'], {'I': 'minecraft:iron_ingot', 'M': c('beam_mirror')}, 1, 'redstone')
    shaped('light_receiver', c('light_receiver'), ['GQG', 'QRQ', 'GQG'], {'G': G, 'Q': Q, 'R': 'minecraft:redstone_block'}, 1, 'redstone')
    shaped('sky_bell', c('sky_bell'), [' G ', 'GQG', 'G G'], {'G': G, 'Q': Q}, 1, 'redstone')
    shaped('tuning_fork', c('tuning_fork'), ['I I', ' I ', ' Q '], {'I': 'minecraft:iron_ingot', 'Q': Q}, 1, 'equipment')

    # --- тексты загадок
    riddles = [
        ('Падаю, но не разбиваюсь. Лечу, но крыльев у меня нет. Что я?', 'I fall but never break. I fly but have no wings. What am I?'),
        ('Мягче пуха, белее снега, держит тех, кто ходит по небу.', 'Softer than down, whiter than snow, it holds those who walk the sky.'),
        ('Без ног иду, без рук указываю, без глаз знаю, когда ночь.', 'Without legs I walk, without hands I point, without eyes I know the night.'),
        ('Рождена во тьме Ада, но несу свет.', 'Born in the darkness of the Nether, yet I carry light.'),
        ('Пища, что падает с неба.', 'Food that falls from the sky.'),
        ('Всегда смотрю в одну сторону, куда бы ты ни шёл.', 'I always look one way, wherever you go.'),
        ('Я — голос глубин, что повторяет за тобой.', 'I am the voice of the deep that repeats after you.'),
        ('Упал с неба, но не дождь. Светит, но не огонь.', 'Fell from the sky, but not rain. Shines, but not fire.'),
    ]
    for i, (ru, en) in enumerate(riddles):
        names[f'puzzle.celestial.riddle.{i}'] = ('§6Руны гласят: §f' + ru, '§6The runes read: §f' + en)
    names.update({
        'puzzle.celestial.riddle.solved': ('§aЗагадка разгадана — руны спокойно светятся.', '§aThe riddle is solved - the runes glow calmly.'),
        'puzzle.celestial.riddle.wrong': ('Руны остаются тёмными…', 'The runes stay dark...'),
        'puzzle.celestial.bells.listen': ('Слушай мелодию и повтори её на колоколах', 'Listen to the melody and repeat it on the bells'),
        'puzzle.celestial.bells.wrong': ('Фальшивая нота! Начни сначала', 'A false note! Start again'),
        'puzzle.celestial.bells.already': ('Колокола уже поют в унисон', 'The bells already sing in unison'),
        'puzzle.celestial.solved': ('✦ Загадка решена! +1 Благодать', '✦ Puzzle solved! +1 Grace'),
    })

    machines(names)
    trials(names)

    # теги дописываем к существующим файлам
    for (kind, name), values in TAGS.items():
        ns, path = name.split(':')
        base = os.path.join(DATA if ns == 'celestial' else DATA.replace('celestial', 'minecraft'), 'tags', kind, path + '.json')
        existing = []
        if os.path.exists(base):
            with open(base) as f:
                existing = json.load(f)['values']
        write_json(base, {'replace': False, 'values': list(dict.fromkeys(existing + values))})
    lang_patch(names)
    print('ok: механизмы и загадки,', len(names), 'строк')


if __name__ == '__main__':
    main()
