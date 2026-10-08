"""Свои модели старых существ (планка качества): текстуры по развёрткам client/render/HeavenModels.java + светящиеся слои.

Партия A: Тень (дым и тьма, светящиеся глаза), Грозовой дух и Грозовой элементаль (грозовое ядро, облака, молнии).
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


def main():
    for name, (tex, glow) in (('shadow', shadow()),
                              ('storm_spirit', storm('storm_spirit', ('#2a3248', '#323c56', '#3a4664'), '#bfe9ff')),
                              ('storm_elemental', storm('storm_elemental', ('#1e2238', '#262c46', '#2e3654'), '#fff07a'))):
        save_png(tex, 'entity/' + name)
        save_png(glow, 'entity/' + name + '_glow')
    print('ok: модели существ, партия A')


if __name__ == '__main__':
    main()
