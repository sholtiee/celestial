"""Свои модели старых существ (планка качества): текстуры по развёрткам client/render/HeavenModels.java + светящиеся слои.

Партия A: Тень (дым и тьма, светящиеся глаза), Грозовой дух и Грозовой элементаль (грозовое ядро, облака, молнии).
Партия B: Ангел (четыре профессии: одеяние, отделка, рукава, свой знак) и Херувим.
"""
from PIL import Image

import mob_textures as M
from gen_assets import save_png
from textures import hexrgb, mix, rng_for, shade

WHITE = (255, 255, 255)


def pick(r, pal):
    return r.choice(pal)


def shadow():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('shadow_model')
    dark = [hexrgb(h) for h in ('#0e0b16', '#151020', '#1c152b', '#120e1b')]
    smoke = [hexrgb(h) for h in ('#2a2140', '#342852', '#22192f')]
    eye = (190, 120, 255, 255)

    def skin(face, x, y, fw, fh):
        c = pick(r, dark)
        if (x * 5 + y * 3) % 13 == 0:
            c = mix(c, hexrgb('#5a3a8f'), 0.5)  # прожилки
        return c

    def head(face, x, y, fw, fh):
        if face == 'front':
            if y in (4, 5) and x in (1, 2, 5, 6):
                return eye[:3]
            if y >= 6:
                return hexrgb('#06050a')  # провал «рта»
        return skin(face, x, y, fw, fh)

    def hood(face, x, y, fw, fh):
        if face == 'front' and 1 <= x <= fw - 2 and y >= 1:
            return None  # лицо открыто
        if face == 'bottom':
            return None
        return pick(r, smoke) if (x + y) % 4 else shade(pick(r, smoke), 0.8)

    def tail(face, x, y, fw, fh):
        a = 255 if y < fh - 2 else 150
        return (*mix(pick(r, smoke), hexrgb('#5a3a8f'), y / fh * 0.4), a)

    def cloak(face, x, y, fw, fh):
        a = 255 if y < fh - 3 or (x + y) % 2 else 0  # рваный низ
        return (*pick(r, smoke), a)

    def claw(face, x, y, fw, fh):
        return hexrgb('#cfc3e6') if face in ('front', 'bottom') else hexrgb('#8a7aa8')

    M.paint_box(img, 0, 0, 8, 8, 8, head)
    M.paint_box(img, 0, 48, 9, 4, 9, hood)
    M.paint_box(img, 0, 16, 8, 12, 5, skin)
    M.paint_box(img, 26, 16, 6, 3, 4, skin)
    M.paint_box(img, 48, 16, 3, 15, 3, skin)
    M.paint_box(img, 26, 24, 3, 3, 1, claw)
    M.paint_box(img, 40, 34, 4, 16, 1, cloak)
    M.paint_box(img, 12, 34, 3, 6, 3, tail)
    M.paint_box(img, 24, 34, 2, 6, 2, tail)
    M.paint_box(glow, 0, 0, 8, 8, 8, lambda f, x, y, fw, fh: eye if f == 'front' and y in (4, 5) and x in (1, 2, 5, 6) else None)
    M.paint_box(glow, 0, 16, 8, 12, 5, lambda f, x, y, fw, fh: (120, 70, 200, 255) if f == 'front' and (x * 5 + y * 3) % 13 == 0 else None)
    return img, glow


def storm(name, core_cols, bolt):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for(name + '_model')
    cloud = [hexrgb(h) for h in ('#9aa6b8', '#b4bfcd', '#cdd6e1', '#8a95a8')]
    core = [hexrgb(h) for h in core_cols]
    crack = hexrgb(bolt)

    def coref(face, x, y, fw, fh):
        if (x + 2 * y) % 7 == 0 or (2 * x - y) % 9 == 0:
            return crack  # трещины-разряды
        return pick(r, core)

    def eyes(face, x, y, fw, fh):
        return WHITE if face == 'front' else crack

    def puff(face, x, y, fw, fh):
        # мягкое облако: белая шапка, к низу — серо-голубая тень, без «каменного» шума
        if face == 'top':
            return mix(hexrgb('#f4f7fb'), WHITE, 0.4 * ((x + y) % 3 == 0))
        if face == 'bottom':
            return hexrgb('#8f9cb0')
        k = y / max(1, fh - 1)
        c = mix(hexrgb('#eef2f7'), hexrgb('#a9b5c6'), k ** 1.3)
        if (x * 3 + y) % 11 == 0:
            c = mix(c, WHITE, 0.4)
        return c

    M.paint_box(img, 0, 0, 8, 8, 8, coref)
    M.paint_box(img, 32, 0, 6, 2, 1, eyes)
    M.paint_box(img, 0, 16, 8, 6, 8, puff)
    M.paint_box(img, 0, 30, 7, 5, 7, puff)
    for u in (48, 52, 56):
        M.paint_box(img, u, 0, 1, 4, 1, lambda f, x, y, fw, fh: mix(crack, WHITE, 0.4))
        M.paint_box(glow, u, 0, 1, 4, 1, lambda f, x, y, fw, fh: (*mix(crack, WHITE, 0.4), 255))
    M.paint_box(glow, 0, 0, 8, 8, 8, lambda f, x, y, fw, fh: (*crack, 255) if (x + 2 * y) % 7 == 0 or (2 * x - y) % 9 == 0 else None)
    M.paint_box(glow, 32, 0, 6, 2, 1, lambda f, x, y, fw, fh: (255, 255, 255, 255))
    return img, glow


HALO = (255, 247, 200)
HALO_GLOW = (255, 250, 215, 255)


def halo_box(img, u, w, d, colour):
    """Планки нимба: передняя/задняя w×1×1 в (u,0), боковые 1×1×d в (u,4)."""
    M.paint_box(img, u, 0, w, 1, 1, lambda f, x, y, fw, fh: colour)
    M.paint_box(img, u, 4, 1, 1, d, lambda f, x, y, fw, fh: colour)


def angel(prof):
    robe, trim, sleeve = (hexrgb(h) for h in M.ANGEL_ROBES[prof])
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('angel_model_' + prof)
    skin, hair, eye = hexrgb('#f3d6bd'), hexrgb('#f4d27a'), hexrgb('#5ab8ff')

    def cloth(base, x, y, var=0.06):
        c = M.noise_color(r, base, var)
        return shade(c, 0.88) if x % 3 == 2 else c  # складки

    def mark(face, x, y, fw, fh, part):
        """Свой знак профессии на одеянии; None — нет знака в этой точке."""
        if prof == 'astronomer' and (x * 7 + y * 11 + part) % 23 == 0:
            return hexrgb('#fff3b0')  # звёзды на мантии
        if prof == 'gardener' and face in ('front', 'back') and part == 2 and fh - 5 <= y < fh - 2 and (x + y) % 3 == 0:
            return hexrgb('#5c8a2e')  # листья по подолу
        if prof == 'smith' and face == 'front' and 2 <= x <= fw - 3 and (part == 1 or (part == 2 and y < fh - 3)):
            return M.noise_color(r, hexrgb('#4a3020'), 0.08)  # кожаный фартук
        return None

    def head(face, x, y, fw, fh):
        if face == 'top' or face == 'back' or (face in ('left', 'right') and (y < 4 or x >= 5)):
            return M.noise_color(r, hair if (x + y) % 4 else shade(hair, 0.9), 0.06)
        if face == 'front':
            if y < 2:
                return M.noise_color(r, hair, 0.06)
            if y == 2 and x in (0, 7):
                return hair
            if y == 4 and x in (2, 5):
                return eye
            if y == 4 and x in (1, 6):
                return WHITE
            if y == 6 and 3 <= x <= 4:
                return hexrgb('#d9a08a')
        return M.noise_color(r, skin, 0.03)

    def body(face, x, y, fw, fh):
        m = mark(face, x, y, fw, fh, 1)
        if m:
            return m
        if y == 7:
            return trim  # пояс
        if face == 'front' and fw // 2 - 1 <= x <= fw // 2 and y < 7:
            return trim  # отделка по вороту
        if face == 'top' and 2 <= x <= 5:
            return skin
        return cloth(robe, x, y)

    def arm(face, x, y, fw, fh):
        if face == 'bottom' or (face != 'top' and y >= fh - 2):
            return M.noise_color(r, skin, 0.03)
        if face != 'top' and y == fh - 3:
            return trim  # обшлаг
        return cloth(sleeve, x, y)

    def skirt(face, x, y, fw, fh):
        if face == 'bottom':
            return shade(robe, 0.6)
        m = mark(face, x, y, fw, fh, 2)
        if m:
            return m
        if face != 'top' and y >= fh - 2:
            return trim  # кайма подола
        return cloth(robe, x, y)

    def wing(face, x, y, fw, fh):
        base = mix(WHITE, trim, 0.12)
        if face in ('left', 'right'):
            # перья: ряды сверху вниз, концы маховых темнее и с отделкой
            row = y // 3
            c = shade(base, 1.0 - 0.04 * row)
            if y % 3 == 2:
                c = shade(c, 0.86)
            if x >= fw - 2 and y >= fh - 6:
                c = mix(c, trim, 0.35)
            if fh - y <= (x % 3) + 1:
                return None  # зубчатый край
            return c
        return shade(base, 0.8)

    M.paint_box(img, 0, 0, 8, 8, 8, head)
    M.paint_box(img, 16, 16, 8, 10, 4, body)
    M.paint_box(img, 40, 16, 3, 11, 3, arm)
    M.paint_box(img, 0, 32, 10, 14, 6, skirt)
    M.paint_box(img, 32, 32, 1, 16, 10, wing)
    halo_box(img, 32, 9, 7, HALO)
    halo_box(glow, 32, 9, 7, HALO_GLOW)
    M.paint_box(glow, 0, 0, 8, 8, 8, lambda f, x, y, fw, fh: (*eye, 255) if f == 'front' and y == 4 and x in (2, 5) else None)
    return img, glow


def cherub():
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    r = rng_for('cherub_model')
    skin, curls, eye = hexrgb('#ffe2c4'), hexrgb('#ffd27a'), hexrgb('#6ac8ff')

    def head(face, x, y, fw, fh):
        if face == 'top' or face == 'back' or (face in ('left', 'right') and y < 2):
            return M.noise_color(r, curls if (x + y) % 2 else shade(curls, 0.88), 0.05)  # кудряшки
        if face == 'front':
            if y == 0 or (y == 1 and x in (0, 2, 3, 5)):
                return curls
            if y == 3 and x in (1, 4):
                return eye
            if y == 4 and x in (0, 5):
                return hexrgb('#ffb3a8')  # румянец
            if y == 4 and 2 <= x <= 3:
                return hexrgb('#e8957f')
        return M.noise_color(r, skin, 0.03)

    def body(face, x, y, fw, fh):
        if y >= 3:
            return M.noise_color(r, hexrgb('#fff8e8'), 0.04)  # набедренная повязка
        if y == 2:
            return hexrgb('#e3b54a')
        return M.noise_color(r, skin, 0.03)

    def wing(face, x, y, fw, fh):
        if fh - y <= (x % 2) and x > 2:
            return None
        c = mix(WHITE, hexrgb('#ffe6b8'), 0.1 + 0.05 * (y // 2))
        return shade(c, 0.88) if y % 2 else c

    M.paint_box(img, 0, 0, 6, 6, 6, head)
    M.paint_box(img, 0, 16, 4, 5, 3, body)
    M.paint_box(img, 14, 16, 1, 4, 2, lambda f, x, y, fw, fh: M.noise_color(r, skin, 0.03))
    M.paint_box(img, 20, 16, 3, 2, 2, lambda f, x, y, fw, fh: M.noise_color(r, skin, 0.03))
    M.paint_box(img, 24, 0, 0, 6, 8, wing)
    halo_box(img, 48, 7, 5, HALO)
    halo_box(glow, 48, 7, 5, HALO_GLOW)
    M.paint_box(glow, 0, 0, 6, 6, 6, lambda f, x, y, fw, fh: (*eye, 255) if f == 'front' and y == 3 and x in (1, 4) else None)
    return img, glow


def main():
    for name, (tex, glow) in (('shadow', shadow()),
                              ('storm_spirit', storm('storm_spirit', ('#2a3248', '#323c56', '#3a4664'), '#bfe9ff')),
                              ('storm_elemental', storm('storm_elemental', ('#1e2238', '#262c46', '#2e3654'), '#fff07a'))):
        save_png(tex, 'entity/' + name)
        save_png(glow, 'entity/' + name + '_glow')
    for prof in M.ANGEL_ROBES:
        tex, glow = angel(prof)
        save_png(tex, 'entity/angel_' + prof)
        if prof == 'keeper':
            save_png(tex, 'entity/angel')
            save_png(glow, 'entity/angel_glow')
    tex, glow = cherub()
    save_png(tex, 'entity/cherub')
    save_png(glow, 'entity/cherub_glow')
    print('ok: модели существ, партии A и B')


if __name__ == '__main__':
    main()
