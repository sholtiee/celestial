"""После финала (волна 0.6, S5.7): камень Бесконечного испытания, тексты звёздных поручений и тёмный облик Рая после «Поглотить»
(пепельная трава, увядшая листва — их расползанием правит story/DarkHeaven).

Камень (`trial/EndlessTrialBlock`): ставится где угодно (рецепт — блоки звёздного камня, целестит, око офанима), ПКМ после финала —
волны врагов без конца; рекорд — таблица счёта `celestial_endless`, ранги на 5/10/15/20 волнах.
"""
import math

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import blockstate, c, item_def, model, save_png, self_drop, shaped
from gen_story import lang_patch

H = T.hexrgb


def put(img, x, y, col):
    if 0 <= x < 16 and 0 <= y < 16:
        img.putpixel((x, y), (*col, 255))


def side():
    img = T.bricks('endless_trial_side', [H(h) for h in ('#1e2250', '#262b60', '#2f356e')], '#0e1028')
    for y in range(3, 13):  # светящаяся бесконечность-лента по центру
        put(img, 7, y, H('#9fd0ff'))
        put(img, 8, y, H('#c8e8ff'))
    for x in range(16):
        put(img, x, 0, H('#c8a040'))
        put(img, x, 15, H('#c8a040'))
    return img


def top():
    img = T.noisy('endless_trial_top', [H(h) for h in ('#1a1e48', '#22285a', '#2a3268')], cell=3, grain=0.3)
    for i in range(64):  # знак бесконечности (лемниската)
        t = i / 64 * math.tau
        d = 1 + math.sin(t) ** 2
        x = 7.5 + 6 * math.cos(t) / d
        y = 7.5 + 6 * math.sin(t) * math.cos(t) / d
        put(img, round(x), round(y), H('#e8f4ff'))
    for x in range(16):
        put(img, x, 0, H('#c8a040'))
        put(img, x, 15, H('#c8a040'))
        put(img, 0, x, H('#c8a040'))
        put(img, 15, x, H('#c8a040'))
    return img


def ashen_top():
    img = T.noisy('ashen_grass_top', [H(h) for h in ('#4a4652', '#56525e', '#625e6a', '#3e3a46')], cell=4, grain=0.55)
    r = T.rng_for('ashen_embers')
    for _ in range(3):  # тлеющие искры
        put(img, r.randrange(16), r.randrange(16), H('#a04a5a'))
    return img


def ashen_side():
    img = T.dirt()
    top = ashen_top()
    r = T.rng_for('ashen_grass_side')
    for x in range(16):
        for y in range(3 + r.choice([0, 0, 1, 2])):
            img.putpixel((x, y), top.getpixel((x, y)))
    return img


def withered_leaves():
    img = T.noisy('withered_leaves', [H(h) for h in ('#3a2a44', '#4a3654', '#5a4262', '#2e2236')], cell=2, grain=0.6)
    r = T.rng_for('withered_leaves_holes')
    for y in range(16):
        for x in range(16):
            if r.random() < 0.22:
                img.putpixel((x, y), (0, 0, 0, 0))
    return img


def dark_heaven():
    save_png(ashen_top(), 'block/ashen_grass_top')
    save_png(ashen_side(), 'block/ashen_grass_side')
    model('block/ashen_grass', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'top': c('block/ashen_grass_top'), 'side': c('block/ashen_grass_side'), 'bottom': c('block/heaven_dirt')}})
    blockstate('ashen_grass', {'variants': {'': [{'model': c('block/ashen_grass')}, {'model': c('block/ashen_grass'), 'y': 90}]}})
    item_def('ashen_grass', c('block/ashen_grass'))
    self_drop('ashen_grass')
    save_png(withered_leaves(), 'block/withered_leaves')
    model('block/withered_leaves', {'parent': 'minecraft:block/leaves', 'textures': {'all': c('block/withered_leaves')}, 'render_type': 'minecraft:cutout_mipped'})
    blockstate('withered_leaves', {'variants': {'': {'model': c('block/withered_leaves')}}})
    item_def('withered_leaves', c('block/withered_leaves'))
    self_drop('withered_leaves')
    append_tag('block', 'minecraft:mineable/shovel', [c('ashen_grass')])
    append_tag('block', 'minecraft:mineable/hoe', [c('withered_leaves')])
    append_tag('block', 'minecraft:leaves', [c('withered_leaves')])
    lang_patch({
        'block.celestial.ashen_grass': ('Пепельная трава', 'Ashen Grass'),
        'block.celestial.withered_leaves': ('Увядшая листва', 'Withered Leaves'),
        'ending.celestial.consume.angel': ('Ангел отворачивается: «Ты взял свет себе».', 'The angel turns away: "You took the light for yourself."'),
    })


def main():
    dark_heaven()
    save_png(side(), 'block/endless_trial_side')
    save_png(top(), 'block/endless_trial_top')
    model('block/endless_trial', {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
        'side': c('block/endless_trial_side'), 'top': c('block/endless_trial_top'), 'bottom': c('block/endless_trial_side')}})
    blockstate('endless_trial', {'variants': {'': {'model': c('block/endless_trial')}}})
    item_def('endless_trial', c('block/endless_trial'))
    self_drop('endless_trial')
    shaped('endless_trial', c('endless_trial'), ['SCS', 'CEC', 'SCS'],
           {'S': c('star_stone_block'), 'C': c('celestite_ingot'), 'E': c('ophanim_eye')}, 1, 'misc')
    append_tag('block', 'minecraft:mineable/pickaxe', [c('endless_trial')])
    append_tag('block', 'minecraft:needs_diamond_tool', [c('endless_trial')])
    lang_patch({
        'block.celestial.endless_trial': ('Камень Бесконечного испытания', 'Stone of the Endless Trial'),
        'trial.celestial.endless.locked': ('Камень молчит: он проснётся после финала Саги.', 'The stone is silent: it wakes after the end of the Saga.'),
        'trial.celestial.endless.busy': ('Испытание уже идёт: волна %s.', 'A trial is already under way: wave %s.'),
        'trial.celestial.endless.start': ('Бесконечное испытание началось. Не отходите от камня дальше 24 блоков.',
                                          'The Endless Trial has begun. Stay within 24 blocks of the stone.'),
        'trial.celestial.endless.wave': ('Волна %s', 'Wave %s'),
        'trial.celestial.endless.foes': ('Врагов: %s', 'Foes: %s'),
        'trial.celestial.endless.champion': ('С ними — чемпион', 'A champion comes with them'),
        'trial.celestial.endless.champion_name': ('Чемпион: %s', 'Champion: %s'),
        'trial.celestial.endless.cleared': ('Волна %s пройдена.', 'Wave %s cleared.'),
        'trial.celestial.endless.over': ('Испытание окончено: пройдено волн — %s (рекорд %s).', 'The trial is over: %s waves cleared (record %s).'),
        'trial.celestial.endless.objective': ('Бесконечное испытание', 'Endless Trial'),
        'trial.celestial.endless.rank_sub': ('Пройдено волн: %s', 'Waves cleared: %s'),
        'trial.celestial.endless.rank.5': ('Бронзовый ранг', 'Bronze Rank'),
        'trial.celestial.endless.rank.10': ('Серебряный ранг', 'Silver Rank'),
        'trial.celestial.endless.rank.15': ('Золотой ранг', 'Gold Rank'),
        'trial.celestial.endless.rank.20': ('Звёздный ранг', 'Star Rank'),
    })
    print('ok: после финала — камень Бесконечного испытания')


if __name__ == '__main__':
    main()
