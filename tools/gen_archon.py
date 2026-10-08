"""Акт III «Замёрзшие крылья» (волна 0.4, шаг 7): Морозный Архонт, Иния, Ледяная Корона, главы и дневник.

Текстуры Архонта и шипа рисуются по развёртке моделей client/render/ArchonRenderer.java (texOffs совпадают),
Иния — человеческая модель + крылья по альфа-маске развёртки элитр (рисунок свой), Корона — слой брони головы.
"""
import math
import os

from PIL import Image

import mob_textures as M
import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, c, item_def, model, blockstate, save_png, write_json
from gen_story import advancement, lang_patch

WHITE = (255, 255, 255)
H = T.hexrgb


def pick(r, pal):
    return r.choice(pal)


# ---------------------------------------------------------------- Морозный Архонт (128×128)
def frost_archon():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    r = T.rng_for('frost_archon')
    robe = [H(h) for h in ('#1d2f52', '#22375f', '#283f6b', '#1a2a4a')]
    silver = [H(h) for h in ('#b8c8dc', '#cfdcea', '#e2ecf6')]
    ice = [H(h) for h in ('#7fc6ec', '#9fd8f2', '#c4ecfb')]
    skin = H('#c9dbe8')
    rune = (110, 235, 255, 255)

    def torso(face, x, y, fw, fh):
        if face == 'front':
            if x in (fw // 2 - 1, fw // 2):  # серебряная застёжка
                return pick(r, silver)
            if 3 <= y <= 9 and abs(x - fw / 2 + 0.5) + abs(y - 6) == 3:  # руна-ромб на груди
                return rune[:3]
        if y == 0:
            return pick(r, silver)
        return pick(r, robe)

    def skirt(face, x, y, fw, fh):
        if y >= fh - 2:
            return pick(r, silver)  # серебряная кайма
        if face in ('front', 'back') and (x + y) % 9 == 0:
            return H('#3a5a8f')
        if face == 'front' and x in (fw // 2 - 1, fw // 2):
            return pick(r, silver)
        return pick(r, robe)

    def hem(face, x, y, fw, fh):
        k = y / max(1, fh)
        base = T.mix(pick(r, robe), H('#9fd8f2'), k * 0.8)  # подол растворяется инеем
        return (*base, 255 if k < 0.7 or (x + y) % 2 else 140)

    def head(face, x, y, fw, fh):
        if face == 'front':
            if y in (3, 4) and x in (1, 2, 5, 6):
                return rune[:3]  # глаза
            if y >= 6 and 2 <= x <= 5:
                return H('#a9bdd0')  # иней-борода
            return T.mix(skin, H('#9fb3c6'), r.random() * 0.2)
        if face == 'top':
            return pick(r, silver)
        return pick(r, silver) if y < 3 else T.mix(skin, H('#9fb3c6'), 0.3)

    def crown(face, x, y, fw, fh):
        if face in ('top', 'bottom'):
            return None if 1 <= x <= fw - 2 and 1 <= y <= fh - 2 else pick(r, ice)
        return pick(r, ice) if y == 0 else H('#5ab4e0') if (x % 3 == 1) else pick(r, ice)

    def crystal(face, x, y, fw, fh):
        return T.mix(H('#9fe8ff'), WHITE, (1 - y / max(1, fh)) * 0.7)

    def pauldron(face, x, y, fw, fh):
        if face == 'top':
            return pick(r, ice) if (x + y) % 3 else pick(r, silver)
        return pick(r, silver) if y == 0 else T.mix(pick(r, silver), H('#7fc6ec'), 0.3)

    def arm(face, x, y, fw, fh):
        if y >= fh - 3 and face != 'top':
            return T.mix(skin, H('#9fb3c6'), 0.2)  # кисть
        if y in (fh - 5, fh - 4):
            return pick(r, silver)  # манжета
        return pick(r, robe)

    def scepter(face, x, y, fw, fh):
        return pick(r, silver) if y % 6 else H('#5ab4e0')

    def cloak(face, x, y, fw, fh):
        if face in ('front', 'back'):
            k = y / max(1, fh)
            if x in (0, fw - 1):
                return pick(r, silver)
            col = T.mix(H('#16213a'), H('#3d6fa8'), k * 0.9)
            if (x * 3 + y) % 13 == 0:
                col = T.mix(col, H('#9fd8f2'), 0.5)  # снежинки на плаще
            return (*col, 255 if k < 0.85 or (x + y) % 2 else 120)
        return pick(r, silver)

    M.paint_box(img, 0, 0, 12, 14, 8, torso)
    M.paint_box(img, 0, 22, 14, 20, 10, skirt)
    M.paint_box(img, 48, 22, 10, 8, 8, hem)
    M.paint_box(img, 40, 0, 8, 8, 8, head)
    M.paint_box(img, 72, 0, 9, 2, 9, crown)
    M.paint_box(img, 108, 0, 1, 5, 1, crystal)
    M.paint_box(img, 84, 16, 6, 4, 10, pauldron)
    M.paint_box(img, 84, 30, 4, 16, 4, arm)
    M.paint_box(img, 100, 30, 1, 28, 1, scepter)
    M.paint_box(img, 104, 30, 3, 4, 3, crystal)
    M.paint_box(img, 0, 64, 14, 30, 1, cloak)
    M.paint_box(img, 116, 0, 2, 6, 2, crystal)
    # свечение: глаза, руна, корона, кристаллы скипетра и осколков
    M.paint_box(glow, 40, 0, 8, 8, 8, lambda f, x, y, fw, fh: rune if f == 'front' and y in (3, 4) and x in (1, 2, 5, 6) else None)
    M.paint_box(glow, 0, 0, 12, 14, 8, lambda f, x, y, fw, fh: rune if f == 'front' and 3 <= y <= 9 and abs(x - fw / 2 + 0.5) + abs(y - 6) == 3 else None)
    for u, v, w, h_, d in ((108, 0, 1, 5, 1), (104, 30, 3, 4, 3), (116, 0, 2, 6, 2)):
        M.paint_box(glow, u, v, w, h_, d, lambda f, x, y, fw, fh: (*T.mix(H('#7ff0ff'), WHITE, 0.4), 255))
    M.paint_box(glow, 72, 0, 9, 2, 9, lambda f, x, y, fw, fh: (120, 230, 255, 255) if f not in ('top', 'bottom') and x % 3 == 1 else None)
    return img, glow


def ice_spike():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = T.rng_for('ice_spike')

    def shard(face, x, y, fw, fh):
        k = y / max(1, fh)
        col = T.mix(H('#e9fbff'), H('#3f86b8'), k * 0.8)
        if x == 0 or (x + int(k * 7)) % 5 == 0:
            col = T.mix(col, WHITE, 0.4)
        return (*col, 200 + int(r.random() * 40))

    M.paint_box(img, 0, 0, 6, 36, 6, shard)
    M.paint_box(img, 24, 0, 4, 22, 4, shard)
    M.paint_box(img, 40, 0, 3, 16, 3, shard)
    return img


# ---------------------------------------------------------------- Иния
def inia():
    img = M.humanoid('inia', skin='#e8eef6', hair='#eef6ff', robe='#cfe4f6', trim='#7fc6ec', eyes='#5ab4e0', limbs='#e8f2fb')
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    for x in range(8, 16):  # тонкий светящийся обруч на лбу
        img.putpixel((x, 9), (*H('#9fe8ff'), 255))
        glow.putpixel((x, 9), (160, 240, 255, 255))
    for x, y in ((9, 12), (14, 12)):
        glow.putpixel((x, y), (140, 230, 255, 255))
    wings = M.from_mask('entity/equipment/wings/elytra.png', ['#cfe4f6', '#e4f1fb', '#ffffff', '#bfe9ff'], 'inia_wings', stripes=4)
    return img, glow, wings


# ---------------------------------------------------------------- Ледяная Корона
def crown_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    band = [H('#9fd8f2'), H('#c4ecfb'), H('#7fc6ec')]
    for x in range(2, 14):
        for y in range(10, 13):
            img.putpixel((x, y), (*band[(x + y) % 3], 255))
        img.putpixel((x, 13), (*H('#3f86b8'), 255))
    for cx, h in ((3, 4), (5, 5), (8, 8), (10, 5), (12, 4)):
        for y in range(10 - h, 10):
            w = 0 if y < 10 - h + 2 else 1
            for x in range(cx - w, cx + w + 1):
                if 0 <= x < 16:
                    img.putpixel((x, y), (*T.mix(WHITE, H('#7fc6ec'), (y - (10 - h)) / h), 255))
    for x in (5, 8, 11):
        img.putpixel((x, 11), (*H('#5ff0ff'), 255))
    return img


def crown_layer():
    """Слой брони 64×32: корона — зубчатый обруч в верхней части куба головы, остальное прозрачно."""
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    for face, (x0, y0, fw, fh) in M.box_faces(0, 0, 8, 8, 8).items():
        if face in ('top', 'bottom'):
            continue
        for x in range(fw):
            for y in range(4):
                if y == 0 and x % 2 == 1:
                    continue  # зубцы
                col = H('#c4ecfb') if y == 0 else H('#7fc6ec') if y == 1 else H('#9fd8f2') if y == 2 else H('#3f86b8')
                if y == 2 and x % 4 == 2:
                    col = H('#5ff0ff')  # самоцветы
                img.putpixel((x0 + x, y0 + y), (*col, 255))
    return img


def ice_shard_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for i in range(12):
        x, y = 2 + i, 13 - i
        for w in (-1, 0, 1):
            if 0 <= y + w < 16:
                img.putpixel((x, y + w), (*T.mix(WHITE, H('#3f86b8'), abs(w) * 0.5 + i / 30), 255))
    return img


# ---------------------------------------------------------------- блоки
def blocks():
    for awakened in (False, True):
        img = T.bricks('archon_seal', [H(h) for h in ('#3a4f6e', '#44597a', '#4e6588')], '#1a2334')
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                if 4.5 <= d < 6.3:
                    px_(img, x, y, '#5a7894' if awakened else '#bdf2ff')
        for x, y in ((5, 8), (6, 6), (7, 4), (8, 4), (9, 6), (10, 8), (5, 9), (10, 9), (6, 9), (7, 9), (8, 9), (9, 9)):  # знак короны
            px_(img, x, y, '#5a7894' if awakened else '#7ff0ff')
        save_png(img, 'block/archon_seal' + ('_awakened' if awakened else ''))
        name = 'archon_seal' + ('_awakened' if awakened else '')
        model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/' + name), 'side': c('block/everfrost_bricks'), 'bottom': c('block/everfrost_bricks')}})
    blockstate('archon_seal', {'variants': {'awakened=false': {'model': c('block/archon_seal')}, 'awakened=true': {'model': c('block/archon_seal_awakened')}}})
    item_def('archon_seal', c('block/archon_seal'))

    ice = Image.new('RGBA', (16, 16))
    r = T.rng_for('archon_ice')
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            col = T.mix(H('#bfe9ff'), WHITE, 0.6) if edge else T.mix(H('#9fd8f2'), WHITE, r.random() * 0.3)
            ice.putpixel((x, y), (*col, 230 if edge else 150))
    save_png(ice, 'block/archon_ice')
    model('block/archon_ice', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/archon_ice')}})
    blockstate('archon_ice', {'variants': {'': {'model': c('block/archon_ice')}}})

    # Иния во льду: прозрачный лёд с силуэтом ангела (нижняя и верхняя половины)
    sil_lower = ['....##....', '...####...', '...####...', '...####...', '..######..', '..######..', '...#..#...', '...#..#...']
    sil_upper = ['#.......#.', '##..##..##', '.##.##.##.', '..######..', '...####...', '...####...', '...####...', '....##....']
    for half, sil in (('lower', sil_lower), ('upper', sil_upper)):
        img = Image.new('RGBA', (16, 16))
        for y in range(16):
            for x in range(16):
                edge = x in (0, 15) or y in (0, 15)
                col = T.mix(H('#9fd8f2'), WHITE, 0.55 if edge else r.random() * 0.25)
                img.putpixel((x, y), (*col, 235 if edge else 170))
        for sy, row in enumerate(sil):
            for sx, ch in enumerate(row):
                if ch == '#':
                    for dy in (0, 1):
                        img.putpixel((3 + sx, sy * 2 + dy), (*T.mix(H('#e8f2fb'), H('#7fc6ec'), 0.3), 255))
        save_png(img, f'block/inia_ice_{half}')
        model(f'block/inia_ice_{half}', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c(f'block/inia_ice_{half}')}})
    blockstate('inia_ice', {'variants': {'half=lower': {'model': c('block/inia_ice_lower')}, 'half=upper': {'model': c('block/inia_ice_upper')}}})
    item_def('inia_ice', c('block/inia_ice_lower'))
    immune = [c('archon_seal'), c('inia_ice')]
    append_tag('block', 'minecraft:dragon_immune', immune)
    append_tag('block', 'minecraft:wither_immune', immune)


def px_(img, x, y, hexc):
    img.putpixel((x, y), (*H(hexc), 255))


# ---------------------------------------------------------------- сюжет
STORY = [
    ('frozen_wings', 'heart_of_darkness', c('frost_stone_bricks'),
     {'entered': {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': c('frozen_halls')}}}, 'goal',
     'Замёрзшие крылья', 'Сложи Ледяные врата, зажги их Тёмным Ядром и войди в Ледяные Чертоги',
     'Frozen Wings', 'Build the Frost Gate, light it with the Dark Core and enter the Frozen Halls'),
    ('crown_of_frost', 'frozen_wings', c('ice_crown'),
     {'killed': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                                         'predicate': {'minecraft:entity_type': c('frost_archon')}}}},
      'impossible': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Ледяная Корона', 'Одолей Морозного Архонта и освободи Инию', 'Crown of Frost', 'Defeat the Frost Archon and free Inia'),
]
SIDE = [
    ('glacier_master', 'frozen_wings', c('glacier_rune'), {'solved': {'trigger': 'minecraft:impossible'}}, 'goal',
     'Повелитель льдин', 'Реши зал скользящего льда', 'Master of the Floes', 'Solve a sliding-ice hall'),
    ('three_beams', 'frozen_wings', c('beam_lock'), {'solved': {'trigger': 'minecraft:impossible'}}, 'goal',
     'Три луча', 'Сведи три луча в Зеркальном лабиринте', 'Three Beams', 'Bring three beams together in the Mirror Labyrinth'),
    ('wolf_rider', 'frozen_wings', c('ice_wolf_spawn_egg'),
     {'tamed': {'trigger': 'minecraft:tame_animal', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                               'predicate': {'minecraft:entity_type': c('ice_wolf')}}}}}, 'task',
     'Ледяная упряжка', 'Приручи Ледяного волка', 'Ice Sled', 'Tame an Ice Wolf'),
    ('frost_forged', 'frozen_wings', c('frost_steel_chestplate'),
     {'armor': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('frost_steel_chestplate')}]}}}, 'task',
     'Закалённый стужей', 'Выкуй нагрудник из морозной стали', 'Frost-Forged', 'Forge a Frost Steel Chestplate'),
    ('guardian_breaker', 'frozen_wings', c('ice_core'),
     {'core': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('ice_core')}]}}}, 'goal',
     'Сердце изо льда', 'Добудь Ледяное ядро стража', 'Heart of Ice', 'Obtain an Ice Guardian\'s Ice Core'),
]

JOURNAL = {
    'task_frozen': ('Тёмное Ядро холодит ладонь и тянет на север, к вечной стуже.\n\nСложи врата из кирпичей морозного камня (синий лёд и звёздный обломок) и зажги их Ядром. За ними — Ледяные Чертоги.',
                    'The Dark Core chills my palm and pulls north, toward eternal frost.\n\nBuild a gate of frost-stone bricks (blue ice and a star fragment) and light it with the Core. Beyond lie the Frozen Halls.'),
    'frozen': ('Чертоги. Метель не стихает, и всюду во льду — ангелы, застывшие на лету.\n\nУцелевшие жгут костры в лагерях: тепло — это жизнь. Говорят, их предводительницу Инию сковал Морозный Архонт в своей цитадели на леднике.',
               'The Halls. The blizzard never stops, and everywhere angels are frozen mid-flight in the ice.\n\nThe survivors keep fires burning in their camps: warmth is life. They say their leader Inia was chained by the Frost Archon in his citadel on the glacier.'),
    'task_archon': ('Цитадель Архонта заперта Печатью трёх залов: покори залы скользящего льда, и путь на арену откроется.\n\nЛовушки Архонта: шипы из пола (смотри на иней под ногами), метель, ледяная тюрьма — разбивай лёд изнутри, не медли.',
                    'The Archon\'s citadel is locked by the Seal of Three Halls: conquer the sliding-ice halls and the arena opens.\n\nThe Archon\'s tricks: spikes from the floor (watch the frost at your feet), the blizzard, the ice prison — break the ice from within, do not wait.'),
    'archon': ('Архонт пал, и лёд Инии треснул. Она говорит, что Безликий не просто гасит свет — он останавливает время мира.\n\nВ Хронограде, городе часовщиков, часы мироздания стоят. Ледяная Корона теперь моя: холод мне больше не страшен.',
               'The Archon has fallen and Inia\'s ice has cracked. She says the Faceless does not merely quench the light: it stops the world\'s time.\n\nIn Chronograd, the city of clockmakers, the clocks of creation stand still. The Ice Crown is mine now: the cold no longer frightens me.'),
}


def story():
    entries = {}
    for path, parent, icon, criteria, frame, ru_t, ru_d, en_t, en_d in STORY + SIDE:
        tk, dk = f'advancements.celestial.{path}.title', f'advancements.celestial.{path}.description'
        advancement(path, parent, icon, criteria, frame, tk, dk)
        entries[tk] = (ru_t, en_t)
        entries[dk] = (ru_d, en_d)
    for k, (ru, en) in JOURNAL.items():
        entries['journal.celestial.' + k] = (ru, en)
    return entries


def main():
    tex, glow = frost_archon()
    save_png(tex, 'entity/frost_archon')
    save_png(glow, 'entity/frost_archon_glow')
    save_png(ice_spike(), 'entity/ice_spike')
    tex, glow, wings = inia()
    save_png(tex, 'entity/inia')
    save_png(glow, 'entity/inia_glow')
    save_png(wings, 'entity/inia_wings')
    save_png(crown_icon(), 'item/ice_crown')
    model('item/ice_crown', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/ice_crown')}})
    item_def('ice_crown', c('item/ice_crown'))
    save_png(crown_layer(), 'entity/equipment/humanoid/ice_crown')
    write_json(os.path.join(ASSETS, 'equipment/ice_crown.json'), {'layers': {'humanoid': [{'texture': c('ice_crown')}]}})
    write_json(os.path.join(DATA, 'tags/item/repairs_ice_crown.json'), {'values': [c('ice_core')]})
    save_png(ice_shard_icon(), 'item/ice_shard')
    model('item/ice_shard', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/ice_shard')}})
    item_def('ice_shard', c('item/ice_shard'))
    for name, base, spots in (('frost_archon', '#22375f', '#9fe8ff'), ('inia', '#e4f1fb', '#7fc6ec')):
        save_png(M.spawn_egg(base, spots), 'item/' + name + '_spawn_egg')
        model('item/' + name + '_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + name + '_spawn_egg')}})
        item_def(name + '_spawn_egg', c('item/' + name + '_spawn_egg'))
    blocks()
    names = story()
    names.update({
        'entity.celestial.frost_archon': ('Морозный Архонт', 'Frost Archon'),
        'entity.celestial.inia': ('Иния', 'Inia'),
        'entity.celestial.ice_spike': ('Ледяной шип', 'Ice Spike'),
        'entity.celestial.frost_shard': ('Ледяной осколок', 'Frost Shard'),
        'item.celestial.frost_archon_spawn_egg': ('Яйцо призыва: Морозный Архонт', 'Frost Archon Spawn Egg'),
        'item.celestial.inia_spawn_egg': ('Яйцо призыва: Иния', 'Inia Spawn Egg'),
        'item.celestial.ice_crown': ('Ледяная Корона', 'Ice Crown'),
        'item.celestial.ice_crown.lore1': ('Корона Морозного Архонта. Носящий её не мёрзнет.', 'The Frost Archon\'s crown. Its wearer never freezes.'),
        'item.celestial.ice_crown.lore2': ('Враги рядом с тобой коченеют.', 'Enemies near you grow numb with cold.'),
        'item.celestial.ice_shard': ('Осколок вечного льда', 'Shard of Everlasting Ice'),
        'item.celestial.ice_shard.lore1': ('Не тает. Им метал Архонт.', 'It never melts. The Archon hurled these.'),
        'block.celestial.archon_seal': ('Печать Архонта', 'Archon Seal'),
        'block.celestial.archon_ice': ('Лёд тюрьмы', 'Prison Ice'),
        'block.celestial.inia_ice': ('Иния во льду', 'Inia in the Ice'),
        'codex.celestial.mob.frost_archon': ('тюремщик Инии. Шипы растут из инея под ногами — отходи от меток; в метель зови огонь; из ледяной тюрьмы вырывайся сам.',
                                             'Inia\'s jailer. Spikes rise from the frost at your feet — step off the marks; in the blizzard keep warm; break out of the ice prison yourself.'),
        'codex.celestial.mob.inia': ('предводительница ангелов Чертогов, освобождённая из льда. Поговори с ней.',
                                     'leader of the Halls\' angels, freed from the ice. Talk to her.'),
        'codex.celestial.saga.text.3': ('Акт III пройден: Архонт повержен, Иния свободна. Безликий останавливает время мира — путь лежит в Хроноград.',
                                        'Act III complete: the Archon is slain and Inia is free. The Faceless stops the world\'s time — the road leads to Chronograd.'),
        'boss.celestial.frost_archon.awaken': ('§bПечать раскалывается. Иней поднимается столбом — Морозный Архонт пробудился!',
                                               '§bThe seal cracks. Frost rises in a pillar — the Frost Archon awakens!'),
        'boss.celestial.frost_archon.subtitle': ('Тюремщик Инии', 'Jailer of Inia'),
        'boss.celestial.frost_archon.phase2': ('§bАрхонт вскидывает скипетр — над ареной встаёт метель! Держись у огня и бей стражей.',
                                               '§bThe Archon raises his scepter — a blizzard sweeps the arena! Stay warm and fell his guardians.'),
        'boss.celestial.frost_archon.phase3': ('§fКорона Архонта вспыхивает белым. «Вы останетесь здесь навеки — во льду!»',
                                               '§fThe Archon\'s crown flares white. "You will stay here forever — in the ice!"'),
        'boss.celestial.frost_archon.prison': ('§bЛёд смыкается вокруг тебя!', '§bIce closes in around you!'),
        'boss.celestial.frost_archon.prison_hint': ('§fРазбей лёд — пока не поздно!', '§fBreak the ice — before it is too late!'),
        'entity.celestial.inia.blessing': ('✦ Иния касается твоего лба: «Свет помнит тебя». (+2 Благодати)', '✦ Inia touches your brow: "The light remembers you." (+2 Grace)'),
        'entity.celestial.inia.line1': ('Иния: «Ты разбил его лёд. Века я слышала, как бьются крылья моих сестёр — теперь они полетят».',
                                        'Inia: "You broke his ice. For ages I heard my sisters\' wings beat against it — now they will fly."'),
        'entity.celestial.inia.line2': ('Иния: «Архонт служил Безликому. Тот не просто гасит свет — он останавливает время мира».',
                                        'Inia: "The Archon served the Faceless. It does not merely quench light — it stops the world\'s time."'),
        'entity.celestial.inia.line3': ('Иния: «В Хронограде часы мироздания стоят. Найди Часовщика — пока стрелки не замёрзли навсегда».',
                                        'Inia: "In Chronograd the clocks of creation stand still. Find the Clockmaker — before the hands freeze forever."'),
        'entity.celestial.inia.line4': ('Иния: «Корона твоя по праву. Пусть холод склоняется перед тобой, как склонялся перед ним».',
                                        'Inia: "The crown is yours by right. Let the cold bow to you as it bowed to him."'),
        'story.celestial.act3.title': ('§bЛедяная Корона', '§bThe Ice Crown'),
        'story.celestial.act3.subtitle': ('Акт III «Замёрзшие крылья» пройден', 'Act III "Frozen Wings" complete'),
        'story.celestial.act3.1': ('§b✦ Архонт рассыпается снежной бурей, и по цитадели проходит треск — лёд отпускает пленников.',
                                   '§b✦ The Archon scatters into a snowstorm and a crack runs through the citadel — the ice releases its prisoners.'),
        'story.celestial.act3.2': ('§b✦ Ледяная Корона холодит голову, но тебе тепло. Иния свободна — поговори с ней.',
                                   '§b✦ The Ice Crown is cold on your head, yet you are warm. Inia is free — talk to her.'),
        'story.celestial.act3.3': ('§8✦ Где-то далеко замирает ход огромных часов… Сага Небес продолжается.',
                                   '§8✦ Somewhere far away a vast clock falls silent… The Saga of the Heavens goes on.'),
    })
    lang_patch(names)
    print('ok: Акт III')


if __name__ == '__main__':
    main()
