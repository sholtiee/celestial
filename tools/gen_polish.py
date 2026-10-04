"""Проход качества: подсказки-лор у предметов и блоков (что это и как работает) — ru/en."""
from gen_assets import blockstate, c, item_def, model, save_png
from gen_story import lang_patch
import mob_textures as M
import textures as T
from PIL import ImageDraw

LORE = {
    # предметы
    'item.celestial.star_fragment.lore1': ('Осколок упавшей звезды. Тёплый на ощупь.', 'A shard of a fallen star. Warm to the touch.'),
    'item.celestial.shadow_essence.lore1': ('Сгусток тьмы. В Звёздной купели очищается в звёздный обломок.',
                                            'A clot of darkness. A Star Basin purifies it into a star fragment.'),
    'item.celestial.starlight_flask.lore1': ('Выпей: страх тьмы исчезает, 3 минуты «Звёздного сияния».',
                                             'Drink: fear of the dark vanishes, 3 minutes of Starlight.'),
    'item.celestial.starlight_flask.lore2': ('Им же заправляют Оберег и наполняют Звёздную купель.', 'Also fuels a Ward and fills a Star Basin.'),
    'item.celestial.worm_chitin.lore1': ('Пластина Глубинного червя. Нужна для бездновых шлема и нагрудника.',
                                         'A Deep Worm plate. Needed for the abyssal helmet and chestplate.'),
    'item.celestial.starsteel_ingot.lore1': ('Железо, закалённое в звёздном свете.', 'Iron tempered in starlight.'),
    'item.celestial.charged_crystal.lore1': ('Сердце Оберега. Вставь в пьедестал.', 'The heart of a Ward. Set it into the pedestal.'),
    'item.celestial.dark_core.lore1': ('Свет, который Безликий успел проглотить.', 'Light the Faceless had already swallowed.'),
    'item.celestial.dark_core.lore2': ('§5Холодное. Тянет куда-то во льды…', '§5Cold. It pulls somewhere into the ice...'),
    'item.celestial.abyssal_shard.lore1': ('3 осколка + звёздная сталь = слиток.', '3 shards + starsteel = an ingot.'),
    'item.celestial.abyssal_ingot.lore1': ('Металл, что не боится тьмы.', 'A metal that does not fear the dark.'),
    'item.celestial.abyssal_sword.lore1': ('Выкован в Бездне из обсидиана, что не боится тьмы.', 'Forged in the Abyss from obsidian that fears no dark.'),
    'item.celestial.abyssal_pickaxe.lore1': ('Копает всё, что копает незеритовая.', 'Mines everything a netherite pickaxe can.'),
}
for part in ('helmet', 'chestplate', 'leggings', 'boots'):
    LORE[f'item.celestial.abyssal_{part}.lore1'] = ('§5Комплект: страх растёт вдвое медленнее, без пульсов Тьмы',
                                                    '§5Full set: fear grows half as fast, no Darkness pulses')
# блоки
LORE.update({
    'block.celestial.star_collector.lore1': ('Ночью под открытым небом копит звёздный свет.', 'Gathers starlight at night under an open sky.'),
    'block.celestial.star_collector.lore2': ('Склянкой по ней — Флакон звёздного света.', 'Use a glass bottle on it to fill a Flask of Starlight.'),
    'block.celestial.star_basin.lore1': ('Влей флакон и брось внутрь предмет.', 'Pour in a flask and toss an item inside.'),
    'block.celestial.star_basin.lore2': ('Железо → звёздная сталь, небесный кристалл → заряженный.', 'Iron → starsteel, sky crystal → charged crystal.'),
    'block.celestial.ward.lore1': ('С заряженным кристаллом и флаконами отгоняет Теней и страх.', 'With a charged crystal and flasks it repels Shadows and fear.'),
    'block.celestial.ward.lore2': ('Радиус 16 блоков, флакон = 5 минут.', 'Radius 16 blocks, one flask = 5 minutes.'),
    'block.celestial.brazier.lore1': ('Зажигается огнивом, факелом или флаконом.', 'Lit with flint and steel, a torch or a flask.'),
    'block.celestial.telescope.lore1': ('Ночью покажет стадию Угасания и путь к обсерватории.', 'At night it shows the Fading stage and the way to an observatory.'),
    'block.celestial.glowshroom.lore1': ('Светится в темноте. Костная мука вырастит гигантский гриб.', 'Glows in the dark. Bone meal grows a giant mushroom.'),
    'block.celestial.meteorite.lore1': ('Ядро упавшей звезды: звёздный кварц и обломки.', 'The core of a fallen star: starquartz and fragments.'),
})


def asset_fixes():
    # BUG-008: у разлома в Бездну не было blockstate → «missing model» в логе и пурпурные частицы (сам вид рисует рендерер портала)
    model('block/abyss_rift', {'textures': {'particle': c('block/abyss_stone')}})
    blockstate('abyss_rift', {'variants': {'': {'model': c('block/abyss_rift')}}})
    # BUG-009: у яйца призыва Пожирателя Света не было модели предмета
    save_png(M.spawn_egg('#1c1230', '#c9a8ff'), 'item/light_devourer_spawn_egg')
    model('item/light_devourer_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/light_devourer_spawn_egg')}})
    item_def('light_devourer_spawn_egg', c('item/light_devourer_spawn_egg'))
    lang_patch({'item.celestial.light_devourer_spawn_egg': ('Яйцо призыва: Пожиратель Света', 'Light Devourer Spawn Egg')})


def reliquary():
    """Реликварий: золотой ларец в тёмной оправе со знаком света (награда за загадку, открывается без печатей рядом)."""
    img = T.noisy('reliquary', [T.hexrgb(h) for h in ('#3b2f14', '#5a4720', '#7a6228', '#a2822f')], cell=2, grain=0.35).convert('RGBA')
    d = ImageDraw.Draw(img)
    gold, dark, glow = (232, 196, 90, 255), (28, 22, 12, 255), (255, 243, 198, 255)
    d.rectangle([0, 0, 15, 15], outline=dark)
    d.rectangle([1, 1, 14, 14], outline=gold)
    d.rectangle([4, 4, 11, 11], fill=dark)
    # знак: четыре луча и сердцевина
    for x, y in ((7, 5), (8, 5), (7, 10), (8, 10), (5, 7), (5, 8), (10, 7), (10, 8)):
        d.point((x, y), fill=gold)
    d.rectangle([7, 7, 8, 8], fill=glow)
    save_png(img, 'block/reliquary')
    model('block/reliquary', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/reliquary')}})
    blockstate('reliquary', {'variants': {'': {'model': c('block/reliquary')}}})
    lang_patch({
        'block.celestial.reliquary': ('Реликварий', 'Reliquary'),
        'puzzle.celestial.reliquary.sealed': ('Печать всё ещё держит сокровище.', 'The seal still holds the treasure.'),
        'puzzle.celestial.reliquary.empty': ('Ты уже забрал свою долю.', 'You already took your share.'),
    })


def main():
    asset_fixes()
    reliquary()
    lang_patch(LORE)
    print('ok: подсказки', len(LORE))


if __name__ == '__main__':
    main()
