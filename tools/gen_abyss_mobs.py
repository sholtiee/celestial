"""Существа Бездны (волна 0.3, шаг 4): текстуры по развёртке своих моделей + светящиеся слои, яйца, лут, переводы.

Модели — client/render/AbyssModels.java (развёртки должны совпадать с texOffs там).
"""
import math
import os

from PIL import Image

import mob_textures as M
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, c, entity_loot, item_def, model, save_png, write_json
from gen_story import lang_patch
from textures import hexrgb, mix, rng_for, shade

CLEAR = None


def pick(r, pal):
    return r.choice(pal)


# ---------------------------------------------------------------- Слепой охотник
def blind_hunter():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('blind_hunter')
    skin = [hexrgb(h) for h in ('#a39c8f', '#b7b0a3', '#c9c3b8', '#bdb6a9')]
    dark, vein, gum, tooth = hexrgb('#5e5850'), hexrgb('#8a7f86'), hexrgb('#3a1418'), hexrgb('#efe6cf')
    cyan = (90, 255, 230, 255)

    def body(face, x, y, fw, fh):
        if face == 'front' and y % 3 == 1 and 1 < x < fw - 2 and 2 < y < 12:  # рёбра
            return shade(pick(r, skin), 0.78)
        if face == 'back' and x in (fw // 2 - 1, fw // 2):  # позвоночник
            return shade(pick(r, skin), 0.7 if y % 2 else 0.85)
        return shade(pick(r, skin), 0.92) if r.random() < 0.08 else pick(r, skin)

    def head(face, x, y, fw, fh):
        if face == 'front':
            if 3 <= x <= 4 and 2 <= y <= 7:  # вертикальная пасть
                return tooth if (y % 2 == 0 and x == 3) or (y % 2 == 1 and x == 4) else gum
            if y in (2, 3) and x in (1, 6):  # заросшие глазницы
                return shade(pick(r, skin), 0.75)
        if face == 'top' and (x + y) % 5 == 0:
            return vein
        return pick(r, skin)

    def frill(face, x, y, fw, fh):
        base = mix(hexrgb('#8a7f86'), hexrgb('#c9b4c0'), y / max(1, fh))
        return base

    def limb(face, x, y, fw, fh):
        if y >= fh - 4 and face != 'top':  # когти/ступни
            return shade(dark, 0.8 + 0.2 * r.random())
        return pick(r, skin)

    M.paint_box(img, 0, 0, 10, 16, 6, body)
    M.paint_box(img, 32, 0, 8, 8, 8, head)
    M.paint_box(img, 52, 16, 1, 7, 5, frill)
    M.paint_box(img, 32, 28, 3, 22, 3, limb)
    M.paint_box(img, 44, 28, 3, 22, 3, limb)
    M.paint_box(img, 0, 40, 4, 16, 4, limb)
    M.paint_box(img, 16, 40, 4, 16, 4, limb)
    # светятся «слуховые» жилки на гребнях
    M.paint_box(glow, 52, 16, 1, 7, 5, lambda f, x, y, fw, fh: cyan if f in ('right', 'left') and (x + y) % 3 == 0 else None)
    return img, glow


# ---------------------------------------------------------------- Светоед
def light_eater():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('light_eater')
    fur = [hexrgb(h) for h in ('#3e3150', '#4a3b5c', '#5b4a70', '#45375a')]
    wing_dark, wing_mid, ring = hexrgb('#3d2d5e'), hexrgb('#7a5fb0'), hexrgb('#e2d6ff')
    sac = hexrgb('#f5e6a8')

    def fuzz(face, x, y, fw, fh):
        return shade(pick(r, fur), 1.15) if r.random() < 0.12 else pick(r, fur)

    def head(face, x, y, fw, fh):
        if face == 'front' and y == 1 and x in (0, 3):
            return hexrgb('#1a1424')
        return pick(r, fur)

    def antenna(face, x, y, fw, fh):
        return hexrgb('#d8cfe8') if (x + y) % 2 == 0 else hexrgb('#a99cc0')

    def wing(cx, cy):
        def paint(face, x, y, fw, fh):
            if face not in ('top', 'bottom'):
                return (0, 0, 0, 0)  # торцы плоского крыла невидимы
            # силуэт крыла: эллипс, прижатый к телу (x = 0 у корня), прозрачные углы
            ex, ey = (x + 0.5) / fw, (y + 0.5) / fh - 0.5
            if (ex * 0.95) ** 2 + (ey * 2.1) ** 2 > 1.0 or (ex > 0.75 and abs(ey) > 0.32):
                return (0, 0, 0, 0)
            d = math.hypot(x - cx * fw, y - cy * fh)
            if d < 1.2:
                return hexrgb('#120c1c')
            if d < 2.4:
                return ring
            edge = x in (0, fw - 1) or y in (0, fh - 1)
            return shade(wing_mid, 0.75) if edge else mix(wing_dark, wing_mid, 0.4 + 0.3 * math.sin(x * 0.7 + y * 0.4))
        return paint

    M.paint_box(img, 0, 0, 4, 4, 8, fuzz)
    M.paint_box(img, 24, 0, 4, 4, 3, head)
    M.paint_box(img, 40, 0, 3, 6, 1, antenna)
    M.paint_box(img, 0, 12, 3, 3, 5, lambda f, x, y, fw, fh: mix(sac, hexrgb('#c9a24a'), 0.3 * r.random()))
    M.paint_box(img, 0, 24, 12, 1, 9, wing(0.55, 0.45))
    M.paint_box(img, 0, 34, 12, 1, 9, wing(0.45, 0.45))
    M.paint_box(img, 0, 44, 8, 1, 6, wing(0.5, 0.5))
    M.paint_box(img, 0, 51, 8, 1, 6, wing(0.5, 0.5))
    # светится брюшко (съеденный свет) и «глазки» на крыльях
    M.paint_box(glow, 0, 12, 3, 3, 5, lambda f, x, y, fw, fh: (255, 240, 170, 255))
    for v in (24, 34):
        M.paint_box(glow, 0, v, 12, 1, 9, lambda f, x, y, fw, fh: (210, 190, 255, 255)
                    if f in ('top', 'bottom') and 1.2 <= math.hypot(x - 0.5 * fw, y - 0.45 * fh) < 2.4 else None)
    return img, glow


# ---------------------------------------------------------------- Глубинный червь
def deep_worm():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    r = rng_for('deep_worm')
    plate = [hexrgb(h) for h in ('#3b3247', '#4a3f58', '#433852', '#544766')]
    seam, sheen = hexrgb('#1c1624'), hexrgb('#7a6a96')
    bone, bone_tip = hexrgb('#d8ccb0'), hexrgb('#5a4a3a')

    def chitin(face, x, y, fw, fh):
        if face in ('top', 'bottom'):
            return shade(pick(r, plate), 0.85)
        if y % 5 == 0:
            return seam
        if y % 5 == 1 and r.random() < 0.5:
            return sheen
        return pick(r, plate)

    def head(face, x, y, fw, fh):
        if face == 'top':
            d = math.hypot(x - 6.5, y - 6.5)
            if d < 3.0:
                return hexrgb('#120a10')  # пасть
            if d < 4.2:
                return bone if (x + y) % 2 == 0 else hexrgb('#2a1a20')  # кольцо зубов
        return chitin(face, x, y, fw, fh)

    def jaw(face, x, y, fw, fh):
        return bone_tip if y < 3 else bone

    def pores(cols):
        def paint(face, x, y, fw, fh):
            if face in ('front', 'back', 'left', 'right') and y % 5 == 3 and x % cols == 1:
                return (110, 255, 235, 255)
            return None
        return paint

    M.paint_box(img, 0, 0, 14, 28, 14, chitin)
    M.paint_box(img, 56, 0, 13, 11, 13, chitin)
    M.paint_box(img, 56, 24, 12, 10, 12, chitin)
    M.paint_box(img, 0, 46, 14, 10, 14, head)
    M.paint_box(img, 110, 0, 3, 10, 4, jaw)
    M.paint_box(img, 110, 14, 3, 10, 4, jaw)
    for u, v, w, h, d in ((0, 0, 14, 28, 14), (56, 0, 13, 11, 13), (56, 24, 12, 10, 12), (0, 46, 14, 10, 14)):
        M.paint_box(glow, u, v, w, h, d, pores(4))
    return img, glow


def frost_wraith():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('frost_wraith')
    robe = [hexrgb(h) for h in ('#b8d4e8', '#a6c6de', '#cfe4f2', '#94b8d4')]
    dark = hexrgb('#1c2a3a')

    def hood(face, x, y, fw, fh):
        if face == 'front' and 1 <= x <= 6 and 2 <= y <= 7:
            return dark  # пустота под капюшоном
        return r.choice(robe)

    def cloth(face, x, y, fw, fh):
        frost = (x * 3 + y * 5) % 11 == 0
        return hexrgb('#e8f6ff') if frost else r.choice(robe)

    M.paint_box(img, 0, 0, 8, 8, 8, hood)
    M.paint_box(img, 0, 16, 8, 10, 5, cloth)
    M.paint_box(img, 0, 32, 6, 8, 4, cloth)
    M.paint_box(img, 24, 32, 4, 6, 3, lambda f, x, y, fw, fh: (*r.choice(robe), 200 - y * 25))
    M.paint_box(img, 32, 16, 2, 12, 2, cloth)
    M.paint_box(img, 40, 16, 2, 12, 2, cloth)
    for x in (2, 5):  # глаза
        glow.putpixel((8 + x, 8 + 4), (140, 230, 255, 255))
    M.paint_box(glow, 0, 16, 8, 10, 5, lambda f, x, y, fw, fh: (170, 235, 255, 255) if (x * 3 + y * 5) % 11 == 0 else None)
    return img, glow


MOBS = {
    'blind_hunter': (blind_hunter, 'Слепой охотник', 'Blind Hunter', '#b7b0a3', '#5ae6d0',
                     'не видит, но слышит каждый шаг. Крадись или замри — и он пройдёт мимо.',
                     'cannot see, but hears every step. Sneak or stand still and it will pass you by.'),
    'light_eater': (light_eater, 'Светоед', 'Light Eater', '#4a3b5c', '#f5e6a8',
                    'моль Бездны. Ест факелы и фонари, высасывает Сияние у того, кто несёт огонь.',
                    'a moth of the Abyss. It eats torches and lanterns and drains Radiance from anyone carrying a flame.'),
    'frost_wraith': (frost_wraith, 'Морозный дух', 'Frost Wraith', '#b8d4e8', '#1c2a3a',
                     'призрак Чертогов, крадёт тепло касанием. Боится огня — держись у костра.',
                     'a ghost of the Halls that steals warmth with a touch. It fears fire: stay by a campfire.'),
    'deep_worm': (deep_worm, 'Глубинный червь', 'Deep Worm', '#4a3f58', '#6effeb',
                  'роет камень под ногами. Неуязвим под землёй — бей, пока он над поверхностью.',
                  'burrows through the stone beneath you. Invulnerable underground — strike while it is above the surface.'),
}


def fallen_guardian_extras():
    """Доп. детали Падшего стража (GuardianRenderer.Model) поверх базовой развёртки: плащ, наплечники, гребень, нимб."""
    img = M.fallen_guardian()
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('guardian_extras')
    cape = [hexrgb(h) for h in ('#3a2a55', '#43305f', '#2e2145')]
    metal = [hexrgb(h) for h in ('#5b6070', '#6c7284', '#4a4f5e')]
    gold = hexrgb('#b08a3c')
    M.paint_box(img, 0, 32, 10, 14, 1, lambda f, x, y, fw, fh: gold if y == fh - 1 or (f == 'front' and y == 0) else r.choice(cape))
    M.paint_box(img, 24, 32, 5, 3, 5, lambda f, x, y, fw, fh: gold if y == fh - 1 and f != 'top' else r.choice(metal))
    M.paint_box(img, 44, 32, 1, 4, 7, lambda f, x, y, fw, fh: hexrgb('#8a2f3a') if f in ('left', 'right') else gold)
    for v, (w, d) in ((48, (10, 1)), (50, (7, 1)), (52, (1, 8))):
        M.paint_box(img, 0, v, w, 1, d, lambda f, x, y, fw, fh: hexrgb('#d8c070'))
        M.paint_box(glow, 0, v, w, 1, d, lambda f, x, y, fw, fh: (255, 230, 150, 255) if (x + y) % 2 == 0 else None)
    # светятся только глаза в прорези капюшона (лицевая грань головы: x 8..15, y 8..15 развёртки)
    for x in (10, 13):
        glow.putpixel((x, 12), (95, 245, 255, 255))
    return img, glow


def main():
    names = {}
    tex, glow = fallen_guardian_extras()
    save_png(tex, 'entity/fallen_guardian')
    save_png(glow, 'entity/fallen_guardian_glow')
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
    names['item.celestial.worm_chitin'] = ('Хитин червя', 'Worm Chitin')
    chitin = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = rng_for('worm_chitin_item')
    for y in range(3, 13):
        for x in range(2 + abs(y - 8) // 2, 14 - abs(y - 8) // 2):
            col = '#1c1624' if y % 3 == 0 else ('#7a6a96' if x == 3 + abs(y - 8) // 2 else r.choice(['#3b3247', '#4a3f58', '#544766']))
            chitin.putpixel((x, y), (*hexrgb(col), 255))
    save_png(chitin, 'item/worm_chitin')
    model('item/worm_chitin', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/worm_chitin')}})
    item_def('worm_chitin', c('item/worm_chitin'))

    entity_loot('blind_hunter', [(c('shadow_essence'), 1, 2), ('minecraft:bone', 1, 3)])
    entity_loot('light_eater', [('minecraft:glowstone_dust', 1, 3), (c('shadow_essence'), 1, 1, 0.3)])
    entity_loot('frost_wraith', [('minecraft:snowball', 1, 3), ('minecraft:blue_ice', 1, 1, 0.25)])
    entity_loot('deep_worm', [(c('worm_chitin'), 2, 4), (c('shadow_essence'), 2, 4), (c('star_fragment'), 1, 1, 0.5)])

    append_tag('entity_type', 'celestial:repelled_by_wards', [c('blind_hunter'), c('light_eater')])
    opt = lambda i: {'id': i, 'required': False}  # noqa: E731
    write_json(os.path.join(DATA, 'tags/block/edible_lights.json'), {'values': [
        'minecraft:torch', 'minecraft:wall_torch', 'minecraft:soul_torch', 'minecraft:soul_wall_torch', 'minecraft:lantern',
        'minecraft:soul_lantern', 'minecraft:glowstone', 'minecraft:sea_lantern', 'minecraft:jack_o_lantern', 'minecraft:shroomlight',
        opt('minecraft:copper_torch'), opt('minecraft:copper_wall_torch'), opt('minecraft:copper_lantern')]})
    lang_patch(names)
    print('ok: существа Бездны')


if __name__ == '__main__':
    main()
