"""Существа Хронограда (волна 0.5, S4.4): Часовой-механоид, Жук-заводняк, Кукла-латунь, Офаним, Заводной конь.

Текстуры рисуются по развёртке своих моделей (client/render/ChronoModels.java — texOffs должны совпадать) + светящиеся слои,
яйца призыва, лут, Заводной ключ и Око офанима, теги (седло для коня, неподвластность времени для офанима), переводы и Кодекс.
Спавн в биомах Хронограда прописывает gen_chrono.py (SPAWNS ниже).
"""
from PIL import Image

import mob_textures as M
from gen_abyss import append_tag
from gen_assets import c, entity_loot, item_def, model, save_png, shaped
from gen_story import lang_patch
from textures import hexrgb, mix, rng_for, shade

WHITE = (255, 255, 255)
BRASS = [hexrgb(h) for h in ('#b8862e', '#c9973a', '#d0a044', '#bf8f34')]
BRASS_DARK = hexrgb('#5e4016')
BRASS_LIGHT = hexrgb('#f2d68a')
VERDIGRIS = [hexrgb(h) for h in ('#4a9c86', '#3f8a76', '#58ad94')]
STEEL = [hexrgb(h) for h in ('#5d626c', '#686e79', '#535862')]
AMBER = (255, 196, 92, 255)


def pick(r, pal):
    return r.choice(pal)


def plated(r, face, x, y, fw, fh, pal=BRASS, rivets=4):
    """Латунные листы: светлая кромка сверху, тёмная снизу, заклёпки по углам, пятна патины."""
    base = pick(r, pal)
    if face == 'top':
        return mix(base, BRASS_LIGHT, 0.3)
    if face == 'bottom':
        return shade(base, 0.6)
    if y == 0:
        return mix(base, BRASS_LIGHT, 0.45)
    if y == fh - 1 or x == fw - 1:
        return shade(base, 0.68)
    if rivets and fw > 3 and fh > 3 and x in (1, fw - 2) and y in (1, fh - 2):
        return BRASS_LIGHT
    if r.random() < 0.05:
        return pick(r, VERDIGRIS)
    return base


def key_paint(r):
    def paint(face, x, y, fw, fh):
        return mix(pick(r, BRASS), BRASS_LIGHT, 0.4 if (x + y) % 2 else 0.1)
    return paint


# ---------------------------------------------------------------- Часовой-механоид (64×64)
def clockwork_sentry():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('clockwork_sentry')
    coat = [hexrgb(h) for h in ('#7a2a22', '#8a3028', '#6e241e')]  # мундир — красный лак по латуни

    def body(face, x, y, fw, fh):
        if face == 'front':
            if x in (fw // 2 - 1, fw // 2) and y % 3 == 1:
                return BRASS_LIGHT  # пуговицы
            if y in (fh - 3, fh - 2):
                return BRASS_DARK if x % 3 else BRASS_LIGHT  # ремень с пряжкой
            if 2 <= x <= fw - 3 and 1 <= y <= 3 and (x + y) % 2 == 0:
                return hexrgb('#e8c060')  # аксельбант
            return pick(r, coat) if 1 <= y < fh - 3 else plated(r, face, x, y, fw, fh)
        if face == 'back':
            if 3 <= x <= fw - 4 and 2 <= y <= 9:
                # окно механизма: шестерёнки на тёмном
                cx, cy = x - fw / 2 + 0.5, y - 5.5
                d = (cx * cx + cy * cy) ** 0.5
                if d < 1.2:
                    return BRASS_LIGHT
                if 2.2 < d < 3.4 and (int((cx + 4) * 3 + cy) % 2 == 0):
                    return pick(r, BRASS)
                return hexrgb('#2a1c10')
            return pick(r, coat)
        if face in ('left', 'right'):
            return pick(r, coat) if 1 <= y < fh - 3 else plated(r, face, x, y, fw, fh)
        return plated(r, face, x, y, fw, fh)

    def head(face, x, y, fw, fh):
        if face == 'front':
            if y == 1 and 1 <= x <= fw - 2:
                return BRASS_DARK  # козырёк
            if y in (5, 6) and 1 <= x <= fw - 2:
                return hexrgb('#3a2814') if x % 2 else hexrgb('#5e4016')  # решётка-рот
        return plated(r, face, x, y, fw, fh, rivets=0)

    def shako(face, x, y, fw, fh):
        if face == 'top':
            return hexrgb('#1e1a1a')
        if face == 'front' and 1 <= y <= 2 and 2 <= x <= 3:
            return BRASS_LIGHT  # кокарда-шестерёнка
        if y == fh - 1:
            return BRASS_LIGHT
        return hexrgb('#262020') if (x + y) % 5 else hexrgb('#302828')

    def lens(face, x, y, fw, fh):
        if face == 'front':
            return (255, 214, 120, 255) if (x, y) != (1, 1) else (255, 250, 220, 255)
        return BRASS_DARK

    def arm(face, x, y, fw, fh):
        if y >= fh - 3:
            return pick(r, STEEL) if face != 'bottom' else shade(pick(r, STEEL), 0.7)  # кисть
        if y in (5, 6):
            return BRASS_DARK if (x + y) % 2 else pick(r, STEEL)  # локтевой шарнир
        if y < 4:
            return pick(r, coat) if face != 'top' else mix(pick(r, BRASS), BRASS_LIGHT, 0.4)
        return plated(r, face, x, y, fw, fh, rivets=0)

    def leg(face, x, y, fw, fh):
        if y >= fh - 3:
            return hexrgb('#1e1a1a') if face != 'top' else hexrgb('#2c2424')  # сапоги
        if y in (6, 7):
            return BRASS_DARK if (x + y) % 2 else pick(r, STEEL)  # колено
        if face in ('left', 'right') and x == fw // 2:
            return hexrgb('#e8c060')  # лампас
        return hexrgb('#24242c') if (x * 3 + y) % 7 else hexrgb('#2e2e38')

    def shaft(face, x, y, fw, fh):
        return hexrgb('#5a3a1e') if y % 6 else BRASS_DARK

    def blade(face, x, y, fw, fh):
        if face in ('left', 'right'):
            steel = mix(pick(r, STEEL), WHITE, 0.25 + 0.1 * (x / max(1, fw)))
            return mix(steel, WHITE, 0.4) if x == 0 or y == 0 else steel
        return pick(r, STEEL)

    def epaulette(face, x, y, fw, fh):
        if face == 'top':
            return mix(hexrgb('#e8c060'), WHITE, 0.15 if (x + y) % 2 else 0)
        return hexrgb('#e8c060') if y == 0 else (hexrgb('#c09040') if x % 2 else hexrgb('#a07830'))  # бахрома

    M.paint_box(img, 0, 0, 10, 12, 6, body)
    M.paint_box(img, 0, 18, 7, 7, 7, head)
    M.paint_box(img, 28, 18, 6, 4, 6, shako)
    M.paint_box(img, 52, 18, 3, 3, 1, lens)
    M.paint_box(img, 46, 0, 1, 1, 2, key_paint(r))
    M.paint_box(img, 46, 4, 5, 2, 1, key_paint(r))
    M.paint_box(img, 32, 0, 3, 12, 4, arm)
    M.paint_box(img, 0, 32, 4, 13, 4, leg)
    M.paint_box(img, 16, 32, 1, 22, 1, shaft)
    M.paint_box(img, 20, 32, 1, 6, 5, blade)
    M.paint_box(img, 32, 32, 4, 2, 5, epaulette)
    M.paint_box(glow, 52, 18, 3, 3, 1, lambda f, x, y, fw, fh: AMBER if f == 'front' else None)
    return img, glow


# ---------------------------------------------------------------- Жук-заводняк (64×32)
def winder_beetle():
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    r = rng_for('winder_beetle')

    def shell(face, x, y, fw, fh):
        if face == 'top':
            if x == fw // 2 - 1 or x == fw // 2:
                return BRASS_DARK  # шов надкрылий
            cx = abs(x - fw / 2 + 0.5)
            return mix(pick(r, BRASS), BRASS_LIGHT, 0.5 if (cx < 2 and y % 3 == 0) else 0.1 + 0.05 * (y % 2))
        if face == 'bottom':
            return pick(r, STEEL)
        if y == 0:
            return BRASS_LIGHT
        return plated(r, face, x, y, fw, fh, pal=VERDIGRIS if r.random() < 0.15 else BRASS, rivets=0)

    def head(face, x, y, fw, fh):
        if face == 'front' and y == 0 and x in (0, fw - 1):
            return (120, 255, 200, 255)  # глазки-лампочки
        return plated(r, face, x, y, fw, fh, pal=STEEL, rivets=0)

    def leg(face, x, y, fw, fh):
        return BRASS_DARK if x % 2 else pick(r, STEEL)

    M.paint_box(img, 0, 0, 6, 4, 8, shell)
    M.paint_box(img, 0, 12, 4, 3, 3, head)
    M.paint_box(img, 14, 12, 1, 1, 2, lambda f, x, y, fw, fh: mix(pick(r, STEEL), WHITE, 0.3))
    M.paint_box(img, 28, 0, 4, 1, 1, leg)
    M.paint_box(img, 28, 4, 1, 2, 1, key_paint(r))
    M.paint_box(img, 28, 8, 4, 2, 1, key_paint(r))
    M.paint_box(glow, 0, 12, 4, 3, 3, lambda f, x, y, fw, fh: (120, 255, 200, 255) if f == 'front' and y == 0 and x in (0, fw - 1) else None)
    return img, glow


# ---------------------------------------------------------------- Кукла-латунь (64×64)
def brass_doll():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('brass_doll')
    porcelain = [hexrgb(h) for h in ('#efe4d4', '#f4ebde', '#e8dccb')]
    dress = [hexrgb(h) for h in ('#3d5a7a', '#45648a', '#365270')]
    lace = hexrgb('#f6f0e6')

    def head(face, x, y, fw, fh):
        if face == 'front':
            if y in (3, 4) and x in (1, 2, 5, 6):
                return hexrgb('#1a2a3a') if y == 3 else hexrgb('#7ad8ff')  # стеклянные глаза
            if y == 5 and x in (1, 6):
                return hexrgb('#e8a0a0')  # румянец
            if y == 6 and x in (3, 4):
                return hexrgb('#a83a3a')  # губы
            if y == 7 and x in (3, 4):
                return hexrgb('#5e4016')  # шов челюсти — кукла-щелкунчик
            if 0 < x < fw - 1 and y < 3 and (x + y) % 5 == 0:
                return mix(pick(r, porcelain), hexrgb('#8a7a6a'), 0.4)  # трещинки на фарфоре
            if y < 2:
                return hexrgb('#a86a2a')  # чёлка из медной проволоки
            return pick(r, porcelain)
        if face == 'top' or y < 3 or face == 'back':
            return hexrgb('#b8742e') if (x + y) % 3 else hexrgb('#9a5e22')  # волосы — медная проволока
        return pick(r, porcelain)

    def bonnet(face, x, y, fw, fh):
        if y == fh - 1 and face != 'top':
            return lace if x % 2 else hexrgb('#ded6c8')  # кружевная кайма
        return pick(r, dress) if face != 'bottom' else None

    def body(face, x, y, fw, fh):
        if y < 2:
            return lace  # воротник
        if face == 'front' and x in (fw // 2 - 1, fw // 2) and y % 3 == 0:
            return BRASS_LIGHT
        return pick(r, dress)

    def skirt(face, x, y, fw, fh):
        if face == 'bottom':
            return None
        if y == fh - 1:
            return lace if x % 2 else hexrgb('#ded6c8')
        return shade(pick(r, dress), 0.9 if x % 3 == 0 else 1.0)  # складки

    def arm(face, x, y, fw, fh):
        if y >= fh - 3:
            return pick(r, porcelain)  # фарфоровые кисти
        if y in (5, 6):
            return BRASS_DARK if (x + y) % 2 else pick(r, BRASS)  # шарнир локтя
        return pick(r, dress) if y < 5 else pick(r, porcelain)

    def leg(face, x, y, fw, fh):
        if y >= fh - 2:
            return hexrgb('#2a1e18')  # туфельки
        if y in (4, 5):
            return BRASS_DARK if (x + y) % 2 else pick(r, BRASS)  # колено-шарнир
        return lace if (x + y) % 4 else hexrgb('#ded6c8')  # чулки

    M.paint_box(img, 0, 0, 8, 8, 8, head)
    M.paint_box(img, 0, 32, 9, 3, 9, bonnet)
    M.paint_box(img, 0, 16, 8, 12, 4, body)
    M.paint_box(img, 24, 16, 10, 5, 6, skirt)
    M.paint_box(img, 56, 0, 1, 1, 2, key_paint(r))
    M.paint_box(img, 56, 4, 3, 2, 1, key_paint(r))
    M.paint_box(img, 32, 0, 3, 12, 3, arm)
    M.paint_box(img, 44, 0, 3, 10, 3, leg)
    M.paint_box(glow, 0, 0, 8, 8, 8, lambda f, x, y, fw, fh: (140, 225, 255, 255) if f == 'front' and y == 4 and x in (1, 2, 5, 6) else None)
    return img, glow


# ---------------------------------------------------------------- Офаним (64×64)
def ophanim():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    r = rng_for('ophanim')
    gold = [hexrgb(h) for h in ('#e8c050', '#f0cc60', '#d8b040', '#f6d878')]

    def eye(face, x, y, fw, fh):
        # каждая грань — око: белок, золотая радужка, тёмный зрачок
        cx, cy = x - fw / 2 + 0.5, y - fh / 2 + 0.5
        d = (cx * cx + cy * cy) ** 0.5
        if d < 1.0:
            return hexrgb('#101828')
        if d < 2.6:
            return hexrgb('#e8a830') if d > 1.9 else hexrgb('#ffd860')
        return mix(WHITE, hexrgb('#f0e6d0'), 0.3 if (x + y) % 3 == 0 else 0)

    # кольца: полосы по всей ширине, чтобы годились сегменты любой длины
    for v0, base in ((16, 0), (20, 1), (24, 2)):
        for y in range(4):
            for x in range(24):
                col = gold[(x + y + base) % 4]
                if y in (0, 3):
                    col = mix(col, WHITE, 0.35)
                elif x % 6 == 0:
                    col = shade(col, 0.75)  # насечки — «полные очей» и в узоре
                img.putpixel((x, v0 + y), (*col, 255))
    M.paint_box(img, 0, 0, 8, 8, 8, eye)

    def stud(face, x, y, fw, fh):
        if face in ('front', 'back'):
            return hexrgb('#101828') if (x, y) == (fw // 2, fh // 2) else (hexrgb('#ffd860') if y == fh // 2 else WHITE)
        return mix(gold[0], WHITE, 0.2)

    M.paint_box(img, 32, 0, 2, 3, 3, stud)
    M.paint_box(glow, 0, 0, 8, 8, 8, lambda f, x, y, fw, fh: (255, 230, 140, 255) if 1 <= x < fw - 1 and 1 <= y < fh - 1 else None)
    M.paint_box(glow, 32, 0, 2, 3, 3, lambda f, x, y, fw, fh: (255, 240, 180, 255) if f in ('front', 'back') else None)
    for v0 in (16, 20, 24):
        for x in range(24):
            if x % 6 == 3:
                glow.putpixel((x, v0 + 1), (255, 220, 120, 255))
                glow.putpixel((x, v0 + 2), (255, 220, 120, 255))
    return img, glow


# ---------------------------------------------------------------- Заводной конь (128×64)
def clockwork_horse():
    img = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    r = rng_for('clockwork_horse')

    def body(face, x, y, fw, fh):
        if face == 'front' and 2 <= x <= fw - 3 and 3 <= y <= fh - 3:
            return hexrgb('#ff9a3a') if y % 2 else hexrgb('#2a1a10')  # топка-решётка на груди
        if face in ('left', 'right'):
            # бок: шестерёнка-окно посередине
            cx, cy = x - fw / 2 + 0.5, y - fh / 2 + 0.5
            d = (cx * cx * 0.35 + cy * cy) ** 0.5
            if d < 3.4:
                return BRASS_LIGHT if d < 1 else (pick(r, BRASS) if int(d * 3 + x) % 2 else hexrgb('#2a1c10'))
            if y == fh - 1:
                return BRASS_DARK
        return shade(plated(r, face, x, y, fw, fh), 0.85 if face != 'top' else 0.8)

    def neck(face, x, y, fw, fh):
        if face == 'back' or face == 'top':
            return hexrgb('#3a2a20') if x % 2 else hexrgb('#2a1e18')  # грива-проволока
        return plated(r, face, x, y, fw, fh, rivets=0)

    def head(face, x, y, fw, fh):
        if face in ('left', 'right') and y == 1 and x in (2, 3):
            return (255, 196, 92, 255)  # глаза-лампы
        if face == 'front':
            return pick(r, STEEL) if y > 1 else BRASS_DARK  # стальная морда
        return plated(r, face, x, y, fw, fh, rivets=0)

    def piston(face, x, y, fw, fh):
        return mix(pick(r, STEEL), WHITE, 0.25 if x == 0 else 0)

    def hoof(face, x, y, fw, fh):
        return hexrgb('#2a2a30') if face != 'top' else pick(r, STEEL)

    def stack(face, x, y, fw, fh):
        if face == 'top':
            return hexrgb('#100c08')
        return hexrgb('#262428') if y else BRASS_LIGHT

    def saddle(face, x, y, fw, fh):
        leather = [hexrgb(h) for h in ('#5a2e1a', '#6a3820', '#4e2816')]
        if face == 'top' and (x in (0, fw - 1) or y in (0, fh - 1)):
            return BRASS_LIGHT
        return pick(r, leather)

    def tail(face, x, y, fw, fh):
        return hexrgb('#3a2a20') if (x + y) % 2 else hexrgb('#5a4430')

    M.paint_box(img, 0, 0, 10, 10, 22, body)
    M.paint_box(img, 64, 0, 5, 7, 5, neck)
    M.paint_box(img, 84, 0, 6, 5, 9, head)
    M.paint_box(img, 114, 0, 1, 3, 1, lambda f, x, y, fw, fh: pick(r, BRASS))
    M.paint_box(img, 64, 16, 3, 7, 3, lambda f, x, y, fw, fh: plated(r, f, x, y, fw, fh, rivets=0))
    M.paint_box(img, 76, 16, 2, 5, 2, piston)
    M.paint_box(img, 84, 16, 4, 2, 4, hoof)
    M.paint_box(img, 100, 16, 3, 1, 1, key_paint(r))
    M.paint_box(img, 100, 20, 1, 4, 4, key_paint(r))
    M.paint_box(img, 110, 16, 1, 1, 8, tail)
    M.paint_box(img, 0, 32, 3, 6, 3, stack)
    M.paint_box(img, 12, 32, 11, 1, 10, saddle)
    M.paint_box(img, 54, 32, 1, 8, 2, lambda f, x, y, fw, fh: BRASS_LIGHT if y == fh - 2 else hexrgb('#4e2816'))
    M.paint_box(glow, 0, 0, 10, 10, 22, lambda f, x, y, fw, fh: (255, 160, 70, 255)
                if f == 'front' and 2 <= x <= fw - 3 and 3 <= y <= fh - 3 and y % 2 else None)
    M.paint_box(glow, 84, 0, 6, 5, 9, lambda f, x, y, fw, fh: AMBER if f in ('left', 'right') and y == 1 and x in (2, 3) else None)
    return img, glow


# ---------------------------------------------------------------- предметы
def wind_key():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    pal = {'1': BRASS_DARK, '2': hexrgb('#b8862e'), '3': hexrgb('#d8aa4a'), '4': BRASS_LIGHT, '5': hexrgb('#4a9c86')}
    art = ['................', '..1111..........', '.123321.........', '.13..31.........', '.12..21.........', '.123321.........',
           '..1221..........', '...12...........', '....12..........', '.....121........', '......1321......', '.......1331.....',
           '........13431...', '.........1351...', '..........111...', '................']
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != '.':
                img.putpixel((x, y), (*pal[ch], 255))
    return img


def ophanim_eye():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, (y - 7.5) * 1.6
            d = (dx * dx + dy * dy) ** 0.5
            if d < 7:
                if d < 1.3:
                    col = hexrgb('#101828')
                elif d < 3.2:
                    col = mix(hexrgb('#ffd860'), hexrgb('#c88a20'), (d - 1.3) / 1.9)
                elif d < 6:
                    col = mix(WHITE, hexrgb('#e8dcc8'), (d - 3.2) / 2.8)
                else:
                    col = hexrgb('#d8b040')  # золотой ободок
                img.putpixel((x, y), (*col, 255))
    img.putpixel((6, 6), (255, 255, 255, 255))
    return img


MOBS = {
    'clockwork_sentry': (clockwork_sentry, 'Часовой-механоид', 'Clockwork Sentry', '#7a2a22', '#e8c060',
                         'латунный солдат с алебардой, страж улиц Хронограда. Когда завод кончается, встаёт и заводит себя сам — в эти 3 с бей: урон по нему почти вдвое выше.',
                         'a brass soldier with a halberd guarding the streets of Chronograd. When its spring runs down it stops to rewind itself — strike in those 3 s: it takes almost double damage.'),
    'winder_beetle': (winder_beetle, 'Жук-заводняк', 'Winder Beetle', '#b8862e', '#4a9c86',
                      'латунный жук-роевик. У качающегося маятника подзаводится: бегает и кусает злее. Останови маятник Камертоном — и рой сникнет.',
                      'a swarming brass beetle. Near a swinging pendulum it winds itself up and bites harder. Stop the pendulum with a Tuning Fork and the swarm calms down.'),
    'brass_doll': (brass_doll, 'Кукла-латунь', 'Brass Doll', '#3d5a7a', '#efe4d4',
                   'заводная кукла без своей воли: повторяет твои шаги, прыжки и замахи с задержкой в полторы секунды. Уводи её своим же путём.',
                   'a wind-up doll with no will of its own: it repeats your steps, jumps and swings a second and a half later. Lead it along your own path.'),
    'ophanim': (ophanim, 'Офаним', 'Ophanim', '#e8c050', '#ffffff',
                '«колёса, полные очей». Парит поодаль и наводит луч — нить света тянется к тебе 2,5 с. Уйди за укрытие до разряда. Время над ним не властно.',
                '"wheels full of eyes". Hovers at a distance and aims a beam — a thread of light reaches for you for 2.5 s. Get behind cover before it fires. Time has no power over it.'),
    'clockwork_horse': (clockwork_horse, 'Заводной конь', 'Clockwork Horse', '#c9973a', '#5d626c',
                        'ездовой автомат мастеров. Заведи Заводным ключом — станет твоим, 5 минут быстрого хода; кончится завод — плетётся. Чинится медью и хронитом, не горит.',
                        'the masters\' riding automaton. Wind it with a Wind Key to make it yours: 5 minutes of fast running; when the spring runs down it crawls. Repaired with copper and chronite, fireproof.'),
}

# спавн в биомах Хронограда: категория → [(моб, вес, мин, макс, биомы)]
SPAWNS = {
    'monster': [('clockwork_sentry', 40, 1, 2, ('cog_city', 'copper_plains', 'clock_valley')),
                ('winder_beetle', 60, 3, 5, ('copper_plains', 'foundry_wastes', 'cog_city')),
                ('brass_doll', 20, 1, 1, ('cog_city', 'clock_valley')),
                ('ophanim', 12, 1, 1, ('clock_valley',))],
    'creature': [('clockwork_horse', 8, 1, 2, ('copper_plains',))],
}


def natural_spawns(biome):
    """Атрибут natural_mob_spawns для биома Хронограда (зовёт gen_chrono.biomes)."""
    out = {}
    for cat, entries in SPAWNS.items():
        rows = [{'type': c(name), 'count': {'type': 'minecraft:uniform', 'min_inclusive': lo, 'max_inclusive': hi} if hi > lo else lo, 'weight': w}
                for name, w, lo, hi, where in entries if biome in where]
        if rows:
            out[cat] = rows
    return {'argument': {'spawn_costs': {}, 'spawns_by_category': out}, 'modifier': 'overlay'}


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
    save_png(wind_key(), 'item/wind_key')
    model('item/wind_key', {'parent': 'minecraft:item/handheld', 'textures': {'layer0': c('item/wind_key')}})
    item_def('wind_key', c('item/wind_key'))
    save_png(ophanim_eye(), 'item/ophanim_eye')
    model('item/ophanim_eye', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/ophanim_eye')}})
    item_def('ophanim_eye', c('item/ophanim_eye'))
    shaped('wind_key', c('wind_key'), [' C', 'X '], {'C': 'minecraft:copper_ingot', 'X': c('chronite_ingot')}, 1, 'equipment')
    entity_loot('clockwork_sentry', [('minecraft:copper_ingot', 1, 3), (c('raw_chronite'), 0, 1), (c('wind_key'), 1, 1, 0.08)])
    entity_loot('winder_beetle', [('minecraft:copper_nugget', 1, 4)])
    entity_loot('brass_doll', [('minecraft:copper_ingot', 0, 2), ('minecraft:string', 0, 2), (c('chronite_ingot'), 1, 1, 0.15)])
    entity_loot('ophanim', [(c('ophanim_eye'), 1, 1), ('minecraft:gold_ingot', 1, 3)])
    entity_loot('clockwork_horse', [('minecraft:copper_ingot', 2, 5)])
    append_tag('entity_type', 'minecraft:can_equip_saddle', [c('clockwork_horse')])
    append_tag('entity_type', 'celestial:time_immune', [c('ophanim')])
    names.update({
        'item.celestial.wind_key': ('Заводной ключ', 'Wind Key'),
        'item.celestial.wind_key.lore1': ('ПКМ по Заводному коню: завести (5 минут хода)', 'Use on a Clockwork Horse: wind it (5 minutes of running)'),
        'item.celestial.wind_key.lore2': ('Дикий конь станет твоим', 'A wild horse becomes yours'),
        'item.celestial.ophanim_eye': ('Око офанима', 'Ophanim Eye'),
        'item.celestial.ophanim_eye.lore1': ('Смотрит сквозь время. Говорят, нужно астролябии.', 'It sees through time. They say an astrolabe needs one.'),
        'entity.celestial.clockwork_horse.wound': ('Конь заведён: %s мин хода', 'Horse wound: %s min of running'),
        'entity.celestial.clockwork_horse.need_key': ('Завод кончился. Нужен Заводной ключ.', 'The spring has run down. You need a Wind Key.'),
        'subtitles.celestial.clock_tick': ('Тикают часы', 'Clock ticks'),
        'subtitles.celestial.gear_whir': ('Жужжат шестерни', 'Gears whir'),
        'subtitles.celestial.steam_hiss': ('Шипит пар', 'Steam hisses'),
        'subtitles.celestial.sentry_wind': ('Механизм заводится', 'A mechanism winds up'),
        'subtitles.celestial.beetle_chitter': ('Стрекочет жук-заводняк', 'Winder Beetle chitters'),
        'subtitles.celestial.doll_music_box': ('Играет музыкальная шкатулка', 'A music box plays'),
        'subtitles.celestial.ophanim_hum': ('Гудят колёса офанима', 'Ophanim wheels hum'),
        'subtitles.celestial.ophanim_charge': ('Офаним наводит луч', 'Ophanim takes aim'),
        'subtitles.celestial.ophanim_beam': ('Бьёт луч офанима', 'Ophanim beam strikes'),
        'subtitles.celestial.horse_whinny': ('Заводной конь ржёт', 'Clockwork Horse whinnies'),
        'subtitles.celestial.clockmaker_stop': ('Часовщик: «Стой!»', 'Clockmaker: "Stand still!"'),
        'subtitles.celestial.rewind': ('Время отматывается', 'Time rewinds'),
        'subtitles.celestial.glyph_click': ('Щёлкает колесо глифов', 'Glyph wheel clicks'),
        'entity.celestial.clockwork_horse.unwound': ('Завод кончился — конь едва плетётся', 'The spring has run down — the horse barely crawls'),
    })
    lang_patch(names)
    print('ok: существа Хронограда')


if __name__ == '__main__':
    main()
