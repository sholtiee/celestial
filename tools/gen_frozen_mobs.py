"""Существа Ледяных Чертогов (волна 0.4, шаг 4): Ледяной страж и Ледяной волк.

Текстуры рисуются по развёртке своих моделей (client/render/FrozenModels.java — texOffs должны совпадать) + светящиеся слои,
яйца призыва, лут, Ледяное ядро, теги (седло для волка), переводы и описания для Кодекса.
"""
from PIL import Image

import mob_textures as M
from gen_abyss import append_tag
from gen_assets import c, entity_loot, item_def, model, save_png
from gen_story import lang_patch
from textures import hexrgb, mix, rng_for, shade

WHITE = (255, 255, 255)


def pick(r, pal):
    return r.choice(pal)


# ---------------------------------------------------------------- Ледяной страж (128×64)
def ice_guardian():
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    r = rng_for('ice_guardian')
    ice = [hexrgb(h) for h in ('#4380b0', '#4a88b8', '#5090c0', '#4684b4')]
    frost = [hexrgb(h) for h in ('#cfeefa', '#e4f7ff', '#b8e2f4')]
    seam = hexrgb('#1f3f62')
    cyan = (120, 250, 255, 255)
    core_c = (230, 255, 255, 255)

    def facet(face, x, y, fw, fh):
        """Гранёный лёд: светлые кромки сверху и слева, тёмные швы-трещины."""
        if face == 'top':
            return pick(r, frost)
        base = pick(r, ice)
        if y == 0 or x == 0:
            return mix(base, WHITE, 0.4)
        if y == fh - 1 or x == fw - 1:
            return shade(base, 0.7)
        if (x * 7 + y * 3) % 17 == 0:
            return seam
        if r.random() < 0.025:
            return pick(r, frost)
        return base

    def chest(face, x, y, fw, fh):
        if face == 'front':
            if 1 < y < fh - 1 and x in (2, 3, fw - 3, fw - 4) and y % 3 != 0:  # рёбра-кристаллы
                return hexrgb('#9fe8ff')
            if 6 <= x <= fw - 7 and 2 <= y <= 9 and abs(x - fw / 2 + 0.5) + abs(y - 5.5) < 6:
                return shade(pick(r, ice), 0.65)  # впадина вокруг ядра
        if face == 'back' and x in (fw // 2 - 1, fw // 2):
            return mix(pick(r, ice), WHITE, 0.3)
        return facet(face, x, y, fw, fh)

    def head(face, x, y, fw, fh):
        if face == 'front':
            if y in (3, 4) and x in (1, 2, 5, 6):  # глаза-щели
                return hexrgb('#0d2440')
            if y == 6 and 2 <= x <= 5:
                return seam
        if face == 'top':
            return pick(r, frost)
        return facet(face, x, y, fw, fh)

    def arm(face, x, y, fw, fh):
        if y >= fh - 8 and face != 'top':  # кулак-глыба: светлый спрессованный лёд
            return mix(pick(r, frost), pick(r, ice), 0.25 if (x + y) % 4 else 0.5)
        if y in (8, 9) and face != 'bottom':  # «браслет» из морозного камня
            return hexrgb('#5a6c84') if (x + y) % 3 else hexrgb('#2f3b4c')
        return facet(face, x, y, fw, fh)

    def crystal(face, x, y, fw, fh):
        return mix(hexrgb('#9fe8ff'), WHITE, y / max(1, fh) * 0.6 if face != 'top' else 0.8)

    def shard(face, x, y, fw, fh):
        edge = x in (0, fw - 1) or y in (0, fh - 1)
        if edge:
            return (*mix(hexrgb('#9fe8ff'), WHITE, 0.5), 255)
        return (*mix(hexrgb('#6cc8f0'), WHITE, (x + y) % 5 / 10), 170)

    M.paint_box(img, 0, 0, 20, 14, 12, chest)
    M.paint_box(img, 22, 26, 12, 6, 8, facet)
    M.paint_box(img, 0, 26, 10, 16, 1, shard)
    M.paint_box(img, 0, 44, 6, 14, 6, facet)
    M.paint_box(img, 64, 0, 5, 5, 1, lambda f, x, y, fw, fh: core_c)
    M.paint_box(img, 76, 0, 2, 6, 2, crystal)
    M.paint_box(img, 84, 0, 3, 8, 3, crystal)
    M.paint_box(img, 96, 0, 8, 8, 8, head)
    M.paint_box(img, 64, 16, 6, 26, 6, arm)
    M.paint_box(img, 88, 16, 6, 26, 6, arm)
    # свечение: ядро, глаза, кристаллы, рёбра, пластины щита
    M.paint_box(glow, 64, 0, 5, 5, 1, lambda f, x, y, fw, fh: core_c)
    M.paint_box(glow, 96, 0, 8, 8, 8, lambda f, x, y, fw, fh: cyan if f == 'front' and y in (3, 4) and x in (1, 2, 5, 6) else None)
    M.paint_box(glow, 76, 0, 2, 6, 2, lambda f, x, y, fw, fh: (*mix(hexrgb('#7ff0ff'), WHITE, y / fh * 0.5), 255) if f != 'bottom' else None)
    M.paint_box(glow, 84, 0, 3, 8, 3, lambda f, x, y, fw, fh: (*mix(hexrgb('#7ff0ff'), WHITE, y / fh * 0.5), 255) if f != 'bottom' else None)
    M.paint_box(glow, 0, 0, 20, 14, 12, lambda f, x, y, fw, fh: (110, 230, 255, 255)
                if f == 'front' and 1 < y < fh - 1 and x in (2, 3, fw - 3, fw - 4) and y % 3 != 0 else None)
    M.paint_box(glow, 0, 26, 10, 16, 1, lambda f, x, y, fw, fh: (160, 240, 255, 255) if x in (0, fw - 1) or y in (0, fh - 1) else None)
    return img, glow


# ---------------------------------------------------------------- Ледяной волк (128×64)
def ice_wolf():
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    r = rng_for('ice_wolf')
    fur = [hexrgb(h) for h in ('#d6e2ec', '#e4edf4', '#c7d6e3', '#eef4f8')]
    shadow_fur = [hexrgb(h) for h in ('#9fb3c6', '#aec0d1', '#8ea5bb')]
    mane = [hexrgb(h) for h in ('#f4f9fc', '#ffffff', '#e2eef6')]
    nose, eye = hexrgb('#1c2633'), (140, 230, 255, 255)

    def coat(face, x, y, fw, fh):
        if face == 'bottom':
            return pick(r, shadow_fur)
        if face in ('right', 'left', 'front', 'back') and y >= fh - 3:
            return pick(r, shadow_fur)  # брюхо темнее
        if face == 'top' and x in (fw // 2 - 1, fw // 2):
            return mix(pick(r, fur), hexrgb('#7d95ad'), 0.45)  # тёмная полоса по хребту
        if (x + 2 * y) % 7 == 0:
            return shade(pick(r, fur), 0.88)  # штрихи шерсти
        return pick(r, fur)

    def ruff(face, x, y, fw, fh):
        if (x + y) % 3 == 0:
            return shade(pick(r, mane), 0.9)
        return pick(r, mane)

    def head(face, x, y, fw, fh):
        if face == 'front':
            if y == 2 and x in (1, 6):
                return eye[:3]
            if y == 3 and x in (1, 6):
                return hexrgb('#5a7894')
        return coat(face, x, y, fw, fh)

    def snout(face, x, y, fw, fh):
        if face == 'front' and y <= 1:
            return nose
        if face == 'front' and y == 3 and x in (0, 3):
            return WHITE
        return pick(r, fur) if face != 'bottom' else pick(r, shadow_fur)

    def ear(face, x, y, fw, fh):
        return hexrgb('#9fb3c6') if face == 'front' and y > 0 else pick(r, fur)

    def leg(face, x, y, fw, fh):
        if y >= fh - 2 and face != 'top':
            return hexrgb('#5a6c84') if face != 'bottom' else hexrgb('#3a4658')  # лапы с когтями
        return coat(face, x, y, fw, fh)

    def tail(face, x, y, fw, fh):
        if face in ('front', 'back') or (face in ('right', 'left', 'top', 'bottom') and x >= fw - 3):
            return mix(pick(r, mane), hexrgb('#9fe8ff'), 0.3)  # заиндевевший кончик
        return pick(r, fur)

    def crest(face, x, y, fw, fh):
        return mix(hexrgb('#9fe8ff'), WHITE, 0.4 if y == 0 else 0.1)

    def saddle(face, x, y, fw, fh):
        leather = [hexrgb(h) for h in ('#3b4a63', '#46577a', '#33405a')]
        if face == 'top' and (x in (0, fw - 1) or y in (0, fh - 1)):
            return hexrgb('#9fd8f0')  # оторочка морозной сталью
        return pick(r, leather)

    def strap(face, x, y, fw, fh):
        return hexrgb('#9fd8f0') if y == fh - 2 else hexrgb('#33405a')

    M.paint_box(img, 0, 0, 10, 10, 20, coat)
    M.paint_box(img, 0, 30, 12, 12, 8, ruff)
    M.paint_box(img, 64, 0, 8, 8, 7, head)
    M.paint_box(img, 94, 0, 4, 4, 5, snout)
    M.paint_box(img, 112, 0, 2, 4, 1, ear)
    M.paint_box(img, 64, 16, 4, 12, 4, leg)
    M.paint_box(img, 80, 16, 3, 3, 12, tail)
    M.paint_box(img, 110, 16, 1, 3, 2, crest)
    M.paint_box(img, 40, 50, 11, 1, 9, saddle)
    M.paint_box(img, 80, 34, 1, 10, 2, strap)
    M.paint_box(glow, 64, 0, 8, 8, 7, lambda f, x, y, fw, fh: eye if f == 'front' and y == 2 and x in (1, 6) else None)
    M.paint_box(glow, 110, 16, 1, 3, 2, lambda f, x, y, fw, fh: (*mix(hexrgb('#7ff0ff'), WHITE, 0.3), 255) if f != 'bottom' else None)
    return img, glow


def ice_core():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            d = abs(dx) + abs(dy) * 0.8  # ромб-кристалл
            if d < 6.5:
                t = d / 6.5
                col = mix(WHITE, hexrgb('#3d8cc8'), t ** 0.8)
                if (x + y) % 5 == 0 and t > 0.4:
                    col = mix(col, hexrgb('#1f4f7e'), 0.5)
                img.putpixel((x, y), (*col, 255))
    for x, y in ((6, 5), (7, 5), (6, 6)):
        img.putpixel((x, y), (255, 255, 255, 255))
    return img


MOBS = {
    'ice_guardian': (ice_guardian, 'Ледяной страж', 'Ice Guardian', '#4a88b8', '#bdf2ff',
                     'голем из вечного льда, страж цитадели. Поднимает ледяной щит (бей после), сотрясает землю — держись на расстоянии. Боится огня.',
                     'a golem of everlasting ice guarding the citadel. Raises an ice shield (strike after it fades) and slams the ground — keep your distance. Fears fire.'),
    'ice_wolf': (ice_wolf, 'Ледяной волк', 'Ice Wolf', '#d6e2ec', '#7fc8f0',
                 'ездовой зверь Чертогов. Приручи сырой рыбой, оседлай: на льду быстрее, вода под лапами замерзает, шерсть греет седока.',
                 'the riding beast of the Halls. Tame it with raw fish and saddle it: faster on ice, freezes water underfoot, its fur keeps the rider warm.'),
}


def main():
    names = {}
    for name, (fn, ru, en, base, spots, dru, den) in MOBS.items():
        tex, glow = fn()
        save_png(tex, 'entity/' + name)
        save_png(glow, 'entity/' + name + '_glow')
        save_png(M.spawn_egg(base, spots), 'item/' + name + '_spawn_egg')
        model('item/' + name + '_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + name + '_spawn_egg')}})
        item_def(name + '_spawn_egg', c('item/' + name + '_spawn_egg'))
        names[f'entity.celestial.{name}'] = (ru, en)
        names[f'item.celestial.{name}_spawn_egg'] = (f'Яйцо призыва: {ru}', f'{en} Spawn Egg')
        names[f'codex.celestial.mob.{name}'] = (dru, den)
    save_png(ice_core(), 'item/ice_core')
    model('item/ice_core', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/ice_core')}})
    item_def('ice_core', c('item/ice_core'))
    names['item.celestial.ice_core'] = ('Ледяное ядро', 'Ice Core')
    names['item.celestial.ice_core.lore1'] = ('Сердце Ледяного стража. Не тает даже в огне.', 'The heart of an Ice Guardian. It does not melt even in fire.')
    entity_loot('ice_guardian', [(c('ice_core'), 1, 1), ('minecraft:packed_ice', 2, 5), (c('aurora_crystal'), 0, 2), (c('frost_steel_ingot'), 1, 1, 0.3)])
    entity_loot('ice_wolf', [(c('fur'), 0, 2)])
    append_tag('entity_type', 'minecraft:can_equip_saddle', [c('ice_wolf')])
    append_tag('entity_type', 'minecraft:dismounts_underwater', [c('ice_wolf')])
    append_tag('entity_type', 'minecraft:freeze_immune_entity_types', [c('ice_guardian'), c('ice_wolf')])
    lang_patch(names)
    print('ok: существа Ледяных Чертогов')


if __name__ == '__main__':
    main()
