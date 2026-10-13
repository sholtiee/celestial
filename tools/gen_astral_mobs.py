"""Существа Астрала (волна 0.6, S5.2): звёздная рыба, Пустотный скат (ездовой, модель Небесного ската), Пожиратель звёзд.

Текстуры — по развёрткам client/render/AstralModels.java (скат — по SkyRayModel, как mob_textures.sky_ray), светящиеся слои,
яйца, лут (звёздная чешуя, Звёздные камни), упряжь для ската, переводы, Кодекс. Спавн — таблица SPAWNS → биомы gen_astral.
"""
from PIL import Image

import mob_textures as M
from gen_abyss import append_tag
from gen_assets import c, entity_loot, item_def, model, save_png
from gen_story import lang_patch
from textures import hexrgb, mix, rng_for, shade

H = hexrgb
WHITE = (255, 255, 255)


def star_fish():
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    glow = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    r = rng_for('star_fish')
    scales = [H(h) for h in ('#3a5ad8', '#4a6ae8', '#5a7cf0', '#6a8ef8')]

    def body(face, x, y, fw, fh):
        if face == 'bottom':
            return H('#c8d8ff')
        if face == 'front' and y == 1 and x in (0, fw - 1):
            return H('#fff4c0')  # глаза
        if (x + y * 2) % 5 == 0:
            return mix(r.choice(scales), WHITE, 0.5)  # чешуйки-искры
        return r.choice(scales)

    def fin(face, x, y, fw, fh):
        return (*mix(H('#8ab4ff'), WHITE, 0.3 + 0.1 * (x % 2)), 200)

    M.paint_box(img, 0, 0, 3, 4, 6, body)
    M.paint_box(img, 18, 0, 0, 2, 3, fin)
    M.paint_box(img, 0, 10, 0, 5, 4, fin)
    M.paint_box(img, 10, 10, 3, 0, 2, fin)
    M.paint_box(glow, 0, 0, 3, 4, 6, lambda f, x, y, fw, fh: (255, 244, 192, 255) if (f == 'front' and y == 1 and x in (0, fw - 1)) or (x + y * 2) % 5 == 0 and f != 'bottom' else None)
    M.paint_box(glow, 0, 10, 0, 5, 4, lambda f, x, y, fw, fh: (160, 200, 255, 180))
    return img, glow


def star_devourer():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('star_devourer')
    hide = [H(h) for h in ('#1a0e2e', '#22123a', '#2a1646', '#140a24')]
    for y in range(22, 56):  # сегменты: тёмная кожа с полосами-созвездиями
        for x in range(0, 26):
            col = r.choice(hide)
            if (x * 3 + y) % 11 == 0:
                col = H('#6a4ab8')
            img.putpixel((x, y), (*col, 255))
            if (x * 3 + y) % 11 == 0:
                glow.putpixel((x, y), (190, 150, 255, 255))

    def head(face, x, y, fw, fh):
        if face == 'front':
            if 1 <= x <= fw - 2 and y >= 2:
                return H('#0a0410')  # пасть-воронка
            if y == 1 and x in (1, fw - 2):
                return H('#d8b4ff')  # глаза
        if face == 'top' and (x + y) % 4 == 0:
            return H('#6a4ab8')
        return r.choice(hide)

    def jaw(face, x, y, fw, fh):
        if face == 'top':
            return H('#3a0a2a') if (x + y) % 3 else H('#e8e0ff')  # зубы-иглы в пасти
        return r.choice(hide)

    M.paint_box(img, 0, 0, 8, 5, 7, head)
    M.paint_box(img, 0, 12, 7, 2, 7, jaw)
    M.paint_box(img, 30, 0, 1, 1, 5, lambda f, x, y, fw, fh: H('#8a6ad8'))
    M.paint_box(img, 30, 8, 0, 8, 6, lambda f, x, y, fw, fh: (*mix(H('#4a2a8a'), H('#b48aff'), x / 6), 220))
    M.paint_box(glow, 0, 0, 8, 5, 7, lambda f, x, y, fw, fh: (230, 200, 255, 255) if f == 'front' and y == 1 and x in (1, fw - 2) else None)
    M.paint_box(glow, 0, 12, 7, 2, 7, lambda f, x, y, fw, fh: (240, 230, 255, 255) if f == 'top' and (x + y) % 3 == 0 else None)
    M.paint_box(glow, 30, 0, 1, 1, 5, lambda f, x, y, fw, fh: (180, 140, 255, 255))
    return img, glow


def void_ray():
    """По развёртке Небесного ската: спина — глубокая синь со звёздной россыпью, брюхо — лиловое, глаза светятся."""
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    r = rng_for('void_ray')
    top = [H(h) for h in ('#141a4a', '#1a2258', '#222c68', '#2a3678')]
    belly = [H(h) for h in ('#5a3a9a', '#6a4aa8')]

    def skin(face, x, y, fw, fh):
        if face == 'bottom':
            return r.choice(belly)
        if face == 'top' and (x * 7 + y * 3) % 13 == 0:
            return H('#fff4c0')  # звёзды
        if face == 'top' and (x * 5 + y * 11) % 29 == 0:
            return H('#9ab4ff')
        return r.choice(top)

    M.paint_box(img, 0, 0, 16, 4, 22, skin)
    M.paint_box(img, 0, 26, 20, 2, 16, skin)
    M.paint_box(img, 0, 44, 20, 2, 16, skin)
    M.paint_box(img, 76, 0, 2, 2, 22, skin)
    for x in (3, 12):
        img.putpixel((22 + x, 22 + 1), (*H('#d8e4ff'), 255))
    return img


def star_scale():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(3, 14):
        for x in range(3, 13):
            dx, dy = (x - 7.5) / 5, (y - 8) / 5.5
            if dx * dx + dy * dy <= 1:
                col = mix(H('#e8f0ff'), H('#4a6ae8'), min(1, (dx * dx + dy * dy) ** 0.5))
                if (x + y) % 4 == 0:
                    col = shade(col, 0.85)
                img.putpixel((x, y), (*col, 255))
    img.putpixel((6, 6), (255, 255, 255, 255))
    return img


MOBS = {
    'star_fish': (star_fish, 'Звёздная рыба', 'Star Fish', '#3a5ad8', '#fff4c0',
                  'мирная стайка Астрала: плывёт в пустоте за вожаком и шарахается от странника. С неё — звёздная чешуя.',
                  'a peaceful school of the Astral: it swims through the void after its leader and darts away from wanderers. Drops star scales.'),
    'void_ray': (None, 'Пустотный скат', 'Void Ray', '#1a2258', '#9ab4ff',
                 'ездовой планер Астрала. Надень упряжь — и перелетай между астероидами; падения не боится.',
                 'the riding glider of the Astral. Put a harness on it to fly between asteroids; it fears no fall.'),
    'star_devourer': (star_devourer, 'Пожиратель звёзд', 'Star Devourer', '#22123a', '#b48aff',
                      'угорь пустоты: кусает и выпивает Сияние, а у незажжённых дисков выдёргивает Звёздные камни. Свет его отпугивает.',
                      'an eel of the void: it bites and drinks your Radiance, and plucks Star Stones from unlit disks. Light drives it away.'),
}

SPAWNS = {
    'ambient': [('star_fish', 30, 4, 8, ('star_drift', 'nebula', 'dust_rivers', 'crystal_fields'))],
    'creature': [('void_ray', 6, 1, 2, ('star_drift', 'dust_rivers'))],
    'monster': [('star_devourer', 20, 1, 2, ('nebula', 'star_drift', 'crystal_fields', 'dust_rivers'))],
}


def natural_spawns(biome):
    out = {}
    for cat, rows in SPAWNS.items():
        e = [{'type': c(n), 'count': {'type': 'minecraft:uniform', 'min_inclusive': lo, 'max_inclusive': hi} if hi > lo else lo, 'weight': w}
             for n, w, lo, hi, where in rows if biome in where]
        if e:
            out[cat] = e
    return {'argument': {'spawn_costs': {}, 'spawns_by_category': out}, 'modifier': 'overlay'}


def main():
    names = {}
    for name, (fn, ru, en, base, spots, dru, den) in MOBS.items():
        if fn is not None:
            tex, glow = fn()
            save_png(tex, 'entity/' + name)
            save_png(glow, 'entity/' + name + '_glow')
        else:
            save_png(void_ray(), 'entity/' + name)
        save_png(M.spawn_egg(base, spots), 'item/' + name + '_spawn_egg')
        model('item/' + name + '_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + name + '_spawn_egg')}})
        item_def(name + '_spawn_egg', c('item/' + name + '_spawn_egg'))
        names[f'entity.celestial.{name}'] = (ru, en)
        names[f'item.celestial.{name}_spawn_egg'] = (f'Яйцо призыва: {ru}', f'{en} Spawn Egg')
        names[f'codex.celestial.mob.{name}'] = (dru, den)
    save_png(star_scale(), 'item/star_scale')
    model('item/star_scale', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/star_scale')}})
    item_def('star_scale', c('item/star_scale'))
    entity_loot('star_fish', [(c('star_scale'), 1, 2)])
    entity_loot('void_ray', [(c('star_scale'), 1, 3), ('minecraft:leather', 0, 2)])
    entity_loot('star_devourer', [(c('star_stone'), 1, 2), (c('star_scale'), 0, 2)])
    append_tag('entity_type', 'minecraft:can_equip_harness', [c('void_ray')])
    names.update({
        'item.celestial.star_scale': ('Звёздная чешуя', 'Star Scale'),
        'item.celestial.star_scale.lore1': ('Мерцает даже в темноте. Нужна целеститу и астролябии.', 'It shimmers even in the dark. Celestite and the astrolabe need it.'),
    })
    lang_patch(names)
    print('ok: существа Астрала')


if __name__ == '__main__':
    main()
