"""Текстуры существ Celestial. Цвета и рисунок — свои; для ванильных моделей берётся только форма развёртки (альфа)."""
import math
import os

from PIL import Image

from textures import hexrgb, mix, rng_for, shade

VANILLA_TEX = os.path.join(os.path.dirname(__file__), '..', '.mcsrc/assets/assets/minecraft/textures')


# ---------------------------------------------------------------- развёртка коробки
def box_faces(u, v, w, h, d):
    """Прямоугольники граней кубоида в развёртке Minecraft: имя -> (x0, y0, ширина, высота)."""
    return {
        'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d),
        'right': (u, v + d, d, h), 'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h), 'back': (u + d + w + d, v + d, w, h),
    }


def paint_box(img, u, v, w, h, d, painter):
    """painter(face, x, y, fw, fh) -> RGBA или None; x, y — координаты внутри грани."""
    for face, (x0, y0, fw, fh) in box_faces(u, v, w, h, d).items():
        for y in range(fh):
            for x in range(fw):
                c = painter(face, x, y, fw, fh)
                if c is not None:
                    img.putpixel((x0 + x, y0 + y), c if len(c) == 4 else (*c, 255))


def noise_color(r, base, var=0.08):
    return shade(base, 1 + (r.random() - 0.5) * 2 * var)


# ---------------------------------------------------------------- человекоподобные (64×64, HumanoidModel)
def humanoid(name, skin, hair, robe, trim, eyes, limbs=None, hood=False, glow_eyes=False):
    """Голова 8³ (0,0), тело 8×12×4 (16,16), правая рука 4×12×4 (40,16), правая нога 4×12×4 (0,16).
    Левые конечности в модели зеркалят правые."""
    r = rng_for('mob_' + name)
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    skin, hair, robe, trim, eyes = map(hexrgb, (skin, hair, robe, trim, eyes))
    limbs = hexrgb(limbs) if limbs else robe

    def head(face, x, y, fw, fh):
        if face == 'top':
            return noise_color(r, robe if hood else hair, 0.1)
        if face == 'bottom':
            return noise_color(r, skin)
        if hood:
            if face == 'front' and 1 <= x <= 6 and 2 <= y <= 7:
                if y == 4 and x in (2, 5):
                    return eyes if glow_eyes else (30, 30, 40)
                return noise_color(r, shade(skin, 0.55 if glow_eyes else 1.0))
            return noise_color(r, robe if (y > 0 or face != 'front') else trim, 0.1)
        if face == 'front':
            if y < 2:
                return noise_color(r, hair, 0.12)
            if y == 4 and x in (1, 2, 5, 6):
                return (255, 255, 255) if x in (1, 6) else eyes
            if y == 6 and 3 <= x <= 4:
                return shade(skin, 0.8)
            return noise_color(r, skin, 0.04)
        if face == 'back':
            return noise_color(r, hair, 0.12)
        return noise_color(r, hair if y < 5 else skin, 0.1)

    def body(face, x, y, fw, fh):
        if face in ('top', 'bottom'):
            return noise_color(r, robe)
        if y in (8,) or (face == 'front' and x in (fw // 2 - 1, fw // 2) and y < 8):
            return trim
        if y == 0 and face == 'front':
            return trim
        return noise_color(r, robe, 0.07)

    def arm(face, x, y, fw, fh):
        if face == 'bottom' or (y >= 10 and face != 'top'):
            return noise_color(r, skin, 0.04)
        if y == 9:
            return trim
        return noise_color(r, limbs, 0.07)

    def leg(face, x, y, fw, fh):
        if y >= 10 and face != 'top':
            return noise_color(r, shade(trim, 0.8), 0.05)
        return noise_color(r, shade(robe, 0.92), 0.07)

    paint_box(img, 0, 0, 8, 8, 8, head)
    paint_box(img, 16, 16, 8, 12, 4, body)
    paint_box(img, 40, 16, 4, 12, 4, arm)
    paint_box(img, 0, 16, 4, 12, 4, leg)
    return img


def fallen_guardian():
    # потускневший доспех, капюшон, светящиеся голубые глаза
    img = humanoid('fallen_guardian', skin='#5b5f6e', hair='#2c2f3a', robe='#4a5263', trim='#b08a3c',
                   eyes='#5ff5ff', limbs='#3b4250', hood=True, glow_eyes=True)
    r = rng_for('guardian_cracks')
    for _ in range(40):  # трещины и ржавчина на доспехе
        x, y = r.randrange(16, 40), r.randrange(20, 32)
        if img.getpixel((x, y))[3]:
            img.putpixel((x, y), (*hexrgb('#2a2e38'), 255))
    return img


def angel():
    return humanoid('angel', skin='#f3d6bd', hair='#f4d27a', robe='#f7f4ec', trim='#e3b54a',
                    eyes='#3a8fd8', limbs='#ffffff')


def fallen_seraph():
    img = humanoid('fallen_seraph', skin='#d9c7b0', hair='#1f1a24', robe='#2a2230', trim='#d4a531',
                   eyes='#ff3b3b', limbs='#3a2f42', hood=False, glow_eyes=True)
    return img


# ---------------------------------------------------------------- по маске ванильной развёртки
def from_mask(rel, palette, name, stripes=None):
    """Берёт ТОЛЬКО форму развёртки (альфа-канал) и заливает своим рисунком."""
    mask = Image.open(os.path.join(VANILLA_TEX, rel)).convert('RGBA')
    w, h = mask.size
    r = rng_for(name)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pal = [hexrgb(c) for c in palette]
    for y in range(h):
        for x in range(w):
            a = mask.getpixel((x, y))[3]
            if not a:
                continue
            v = 0.5 + 0.25 * math.sin(x * 0.45 + y * 0.3) + (r.random() - 0.5) * 0.35
            if stripes and (x + y) % stripes == 0:
                v += 0.3
            c = pal[max(0, min(len(pal) - 1, int(v * len(pal))))]
            out.putpixel((x, y), (*c, a))
    return out


def pegasus(baby=False):
    rel = 'entity/horse/horse_white_baby.png' if baby else 'entity/horse/horse_white.png'
    base = from_mask(rel, ['#e6e2f0', '#f1eef8', '#faf8ff', '#ffffff'], 'pegasus' + str(baby))
    if baby:
        return base
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    img.paste(base, (0, 0))
    gold = [hexrgb(c) for c in ('#d9a62e', '#efc24f', '#ffe08a')]
    r = rng_for('pegasus_mane')
    # грива (UV 56,36 — коробка 2×16×2) и хвост — золотые
    for y in range(36, 56):
        for x in range(56, 64):
            if img.getpixel((x, y))[3]:
                img.putpixel((x, y), (*r.choice(gold), 255))
    # крылья: перья, белые с золотой кромкой (две коробки 16×1×12 в (64,0) и (64,16))
    for v0 in (0, 16):
        def wing(face, x, y, fw, fh):
            if face in ('top', 'bottom'):
                edge = y >= fh - 2
                feather = (x % 3 == 0)
                c = hexrgb('#f6e7b0') if edge else hexrgb('#ffffff') if not feather else hexrgb('#e8e4f2')
                return noise_color(r, c, 0.04)
            return hexrgb('#e9d9a6')
        paint_box(img, 64, v0, 16, 1, 12, wing)
    return img


def storm_spirit():
    # голова-тучка и молнии-стержни (развёртка ифрита 64×32)
    img = from_mask('entity/blaze/blaze.png', ['#3c4458', '#4d5770', '#5f6b88', '#7684a4'], 'storm_spirit')
    r = rng_for('storm_bolts')
    for y in range(16, 32):
        for x in range(0, 64):
            if img.getpixel((x, y))[3]:
                c = '#bfe9ff' if (x + y // 2) % 4 else '#ffffff'
                img.putpixel((x, y), (*noise_color(r, hexrgb(c), 0.05), 255))
    # глаза-разряды на лицевой стороне головы (8,8)-(16,16)
    for x in (9, 10, 13, 14):
        img.putpixel((x, 12), (*hexrgb('#e8fbff'), 255))
    return img


def winged_serpent():
    return from_mask('entity/phantom/phantom.png', ['#c79a3a', '#dcb252', '#efcb6e', '#f7e2a0'], 'winged_serpent', stripes=5)


def cloud_whale():
    img = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    r = rng_for('cloud_whale')
    top = [hexrgb(c) for c in ('#e4ecf6', '#eef3fa', '#f7faff', '#ffffff')]
    belly = [hexrgb(c) for c in ('#c9d6ea', '#d6e1f1')]

    def body(face, x, y, fw, fh):
        if face == 'bottom':
            return r.choice(belly)
        if face == 'front' and y == 7 and x in (4, 5, 18, 19):
            return hexrgb('#3a4a66')
        if face in ('left', 'right') and y == 7 and x in (6, 7):
            return hexrgb('#3a4a66')
        if face in ('left', 'right', 'front', 'back') and y > fh * 0.7:
            return r.choice(belly)
        return r.choice(top)

    paint_box(img, 0, 0, 24, 18, 40, body)
    paint_box(img, 0, 64, 12, 10, 16, lambda f, x, y, fw, fh: r.choice(belly if f == 'bottom' else top))
    paint_box(img, 64, 64, 28, 2, 10, lambda f, x, y, fw, fh: r.choice(top))
    paint_box(img, 160, 0, 12, 2, 8, lambda f, x, y, fw, fh: r.choice(top))
    paint_box(img, 160, 16, 12, 2, 8, lambda f, x, y, fw, fh: r.choice(top))
    return img


def light_wisp():
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    r = rng_for('wisp')
    paint_box(img, 0, 0, 4, 4, 4, lambda f, x, y, fw, fh: noise_color(r, hexrgb('#fff6c8'), 0.05))
    paint_box(img, 0, 8, 6, 6, 6, lambda f, x, y, fw, fh: (*hexrgb('#ffd75e'), 110 if (x + y) % 2 else 70))
    return img


def seraph_wings_layer():
    """Слой «крыльев» (развёртка элитр 64×32): белые перья с золотом."""
    return from_mask('entity/equipment/wings/elytra.png', ['#e9e4f4', '#f4f1fa', '#ffffff', '#fff3cf'], 'seraph_wings', stripes=4)


EGG = [
    '................',
    '................',
    '......1111......',
    '.....122221.....',
    '....12222221....',
    '....12232221....',
    '...1222222321...',
    '...1223222221...',
    '...1222222231...',
    '...1232222221...',
    '...1222223221...',
    '....12222221....',
    '....12322221....',
    '.....122221.....',
    '......1111......',
    '................']


def spawn_egg(base, spots):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    b, s = hexrgb(base), hexrgb(spots)
    for y, row in enumerate(EGG):
        for x, ch in enumerate(row):
            if ch == '1':
                img.putpixel((x, y), (*shade(b, 0.6), 255))
            elif ch == '2':
                img.putpixel((x, y), (*b, 255))
            elif ch == '3':
                img.putpixel((x, y), (*s, 255))
    return img
