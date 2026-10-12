"""Вавилонская башня (волна 0.5, S4.6): загадка «Смешение языков», Глиняная табличка, эпизод «Вавилон» (Быт. 11:1–9).

Глифы: 12 слов × 4 письма (0 картинки — понятны глазу, 1 клинья, 2 руны, 3 вавилонское письмо). Рисунки писем 1–3 —
детерминированные штрихи от сида (слово, письмо); картинки — пиксель-арт ниже. Порядок слов совпадает с Glyphs.WORDS.

Загадка: над колёсами замка — фраза картинками (ответ, 4 слова). Колёса набираются вавилонским письмом. Ключ — билингвы
на стенах Зала языков: «картинка = вавилонское» напрямую или цепочкой через клинья/руны. Глиняная табличка читает знак сразу.
Башня — зиккурат из сырцового кирпича (Быт. 11:3 «кирпичи вместо камней»): 5 ярусов, внешняя спираль лестниц,
недостроенная вершина с лесами, краном и остановленными часами; у подножия — лагерь каменщика с якорем Отблеска «Вавилон».
"""
import math
import os
import random

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import DATA, blockstate, c, item_def, model, save_png, write_json
from gen_places import jigsaw
from gen_story import advancement, lang_patch
from gen_structures import Template, reliquary

H = T.hexrgb
MC = 'minecraft:'
WORDS = ['city', 'tower', 'heaven', 'name', 'brick', 'tongue', 'earth', 'people', 'one', 'scatter', 'top', 'build']
WORD_LANG = {
    'city': ('город', 'city'), 'tower': ('башня', 'tower'), 'heaven': ('небо', 'heaven'), 'name': ('имя', 'name'),
    'brick': ('кирпич', 'brick'), 'tongue': ('язык', 'tongue'), 'earth': ('земля', 'earth'), 'people': ('народ', 'people'),
    'one': ('один', 'one'), 'scatter': ('рассеять', 'scatter'), 'top': ('вершина', 'top'), 'build': ('строить', 'build'),
}
PICTO = {
    'city': ['.#....#...', '###..###..', '#.#..#.#..', '###..###..', '....#.....', '...###....', '...#.#....', '...###....', '##########', '..........'],
    'tower': ['....##....', '...####...', '...#..#...', '..######..', '..#....#..', '.########.', '.#......#.', '##########', '#........#', '##########'],
    'heaven': ['....#.....', '...###....', '....#.....', '..........', '...####...', '..#....#..', '.#......#.', '#........#', '.########.', '..........'],
    'name': ['..######..', '.#......#.', '#...##...#', '#..#..#..#', '#...##...#', '#...##...#', '#........#', '.#......#.', '..######..', '..........'],
    'brick': ['..........', '##########', '#...#....#', '##########', '#.....#..#', '##########', '#..#.....#', '##########', '..........', '..........'],
    'tongue': ['..........', '.#.#.#....', '#.#.#.#...', '..........', '..####....', '.#....#...', '#..##..#..', '.#....#...', '..####....', '..........'],
    'earth': ['..........', '.....#....', '....###...', '.....#....', '..........', '...####...', '.##....##.', '#........#', '##########', '..........'],
    'people': ['..........', '.#...#...#', '###.###.##', '.#...#...#', '.#...#...#', '#.#.#.#.#.', '..........', '##########', '..........', '..........'],
    'one': ['....#.....', '...##.....', '....#.....', '....#.....', '....#.....', '....#.....', '....#.....', '...###....', '..........', '..........'],
    'scatter': ['#...#...#.', '.#..#..#..', '..#.#.#...', '...###....', '####.####.', '...###....', '..#.#.#...', '.#..#..#..', '#...#...#.', '..........'],
    'top': ['.....##...', '.....#....', '.....#....', '....###...', '...#####..', '..#######.', '.#########', '##########', '..........', '..........'],
    'build': ['.######...', '.######...', '...##.....', '...##.....', '...##.....', '...##.....', '...##.....', '...##.....', '..........', '..........'],
}
INK = {0: H('#5a1e0e'), 1: H('#2a1a10'), 2: H('#1e1e2a'), 3: H('#3e1446')}


def line(img, x0, y0, x1, y1, col):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
        if 1 <= x <= 14 and 1 <= y <= 14:
            img.putpixel((x, y), (*col, 255))


def glyph_strokes(img, word, script, col):
    """Письма 1–3: штрихи от сида — клинья, руны, петли."""
    r = random.Random(1000 * script + WORDS.index(word) * 7 + 13)
    if script == 1:  # клинья: голова-треугольник и хвост
        for _ in range(r.randint(3, 4)):
            x, y = r.randint(3, 11), r.randint(3, 11)
            d = r.choice([(1, 0), (0, 1), (1, 1), (1, -1)])
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if abs(i) + abs(j) <= 1:
                        img.putpixel((x + i, y + j), (*col, 255))
            line(img, x, y, x + d[0] * r.randint(3, 4), y + d[1] * r.randint(3, 4), col)
    elif script == 2:  # руны: ствол и ветви
        sx = r.choice([5, 7, 9])
        line(img, sx, 2, sx, 13, col)
        for _ in range(r.randint(2, 3)):
            y = r.randint(3, 10)
            dx = r.choice([-1, 1]) * r.randint(3, 4)
            line(img, sx, y, sx + dx, y + r.choice([-3, 3]), col)
        if r.random() < 0.5:
            line(img, sx + r.choice([-4, 4]), 9, sx + r.choice([-4, 4]), 13, col)
    else:  # вавилонское: петли и дуги
        for _ in range(r.randint(2, 3)):
            cx, cy, rad = r.randint(4, 11), r.randint(4, 11), r.choice([2, 2.5, 3])
            a0 = r.uniform(0, math.tau)
            span = r.uniform(math.pi, math.tau)
            for k in range(24):
                a = a0 + span * k / 23
                x, y = round(cx + math.cos(a) * rad), round(cy + math.sin(a) * rad)
                if 1 <= x <= 14 and 1 <= y <= 14:
                    img.putpixel((x, y), (*col, 255))
        x, y = r.randint(5, 10), r.randint(11, 13)
        line(img, x - 2, y, x + 2, y, col)


def tile(seed, base, rim):
    r = T.rng_for(seed)
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            col = T.shade(base, 0.92 + r.random() * 0.14)
            if x in (0, 15) or y in (0, 15):
                col = rim
            img.putpixel((x, y), (*col, 255))
    return img


def glyph_tex(word, script, base=None, rim=None):
    img = tile(f'babel_{word}_{script}', base or H('#c07a4e'), rim or H('#7a4428'))
    col = INK[script]
    if script == 0:
        for y, row in enumerate(PICTO[word]):
            for x, ch in enumerate(row):
                if ch == '#':
                    img.putpixel((x + 3, y + 3), (*col, 255))
    else:
        glyph_strokes(img, word, script, col)
    return img


def tablet_item():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = T.rng_for('clay_tablet')
    for y in range(1, 15):
        for x in range(3, 13):
            if (x, y) in ((3, 1), (12, 1), (3, 14), (12, 14)):
                continue
            col = T.shade(H('#c07a4e'), 0.9 + r.random() * 0.15)
            if x in (3, 12) or y in (1, 14):
                col = H('#8a4e2e')
            img.putpixel((x, y), (*col, 255))
    for row, y in enumerate((3, 6, 9, 12)):  # четыре строки — четыре письма
        ink = INK[row]
        for x in range(5, 11):
            if r.random() < 0.6:
                img.putpixel((x, y), (*ink, 255))
    return img


def assets():
    for w in WORDS:
        for s in range(4):
            name = f'babel_glyph_{w}_{s}'
            save_png(glyph_tex(w, s), 'block/' + name)
            model('block/' + name, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + name)}})
    blockstate('babel_glyph', {'variants': {f'glyph={g},script={s}': {'model': c(f'block/babel_glyph_{w}_{s}')}
                                            for g, w in enumerate(WORDS) for s in range(4)}})
    item_def('babel_glyph', c('block/babel_glyph_tower_0'))
    brass, brim = H('#c9973a'), H('#5e4016')
    save_png(tile('glyph_wheel_side', brass, brim), 'block/glyph_wheel_side')
    for g, w in enumerate(WORDS):
        save_png(glyph_tex(w, 3, brass, brim), f'block/glyph_wheel_{g}')
        model(f'block/glyph_wheel_{g}', {'parent': 'minecraft:block/orientable', 'textures': {
            'front': c(f'block/glyph_wheel_{g}'), 'side': c('block/glyph_wheel_side'), 'top': c('block/glyph_wheel_side')}})
    rot = {'north': 0, 'east': 90, 'south': 180, 'west': 270}
    blockstate('glyph_wheel', {'variants': {f'facing={f},glyph={g}': {'model': c(f'block/glyph_wheel_{g}'), 'y': y}
                                            for f, y in rot.items() for g in range(12)}})
    item_def('glyph_wheel', c('block/glyph_wheel_1'))
    for solved in (False, True):
        img = tile('glyph_seal', H('#e0b050') if solved else brass, brim)
        for k in range(4):  # четыре письма по кругу — печать смешения
            a = k * math.pi / 2 + math.pi / 4
            x, y = round(7.5 + math.cos(a) * 4), round(7.5 + math.sin(a) * 4)
            img.putpixel((x, y), (*INK[k], 255))
            img.putpixel((x, y + 1), (*INK[k], 255))
        for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):
            img.putpixel((x, y), (255, 240, 170, 255) if solved else (*brim, 255))
        n = 'glyph_seal' + ('_solved' if solved else '')
        save_png(img, 'block/' + n)
        model('block/' + n, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + n)}})
    blockstate('glyph_seal', {'variants': {f'solved={str(s).lower()}': {'model': c('block/glyph_seal' + ('_solved' if s else ''))} for s in (False, True)}})
    item_def('glyph_seal', c('block/glyph_seal'))
    save_png(tablet_item(), 'item/clay_tablet')
    model('item/clay_tablet', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/clay_tablet')}})
    item_def('clay_tablet', c('item/clay_tablet'))


# ---------------------------------------------------------------- башня
B = 37                    # сторона основания
TIER_H = 7
TIERS = [B - 6 * k for k in range(5)]   # 37 31 25 19 13
TOP_SIZE = 7
CAMP = 9                  # лагерь каменщика к югу от башни
TX, TY, TZ = B, 52, B + CAMP
MUD, BRICK, PACKED = MC + 'mud_bricks', MC + 'bricks', MC + 'packed_mud'
COPPER = MC + 'waxed_cut_copper'
HALL0, HALL1 = 4, B - 5   # внутренность нижнего яруса (x, z), высота 1..5


def gl(t, x, y, z, word, script):
    t.set(x, y, z, c('babel_glyph'), glyph=WORDS.index(word), script=script)


def tiers(t):
    for k, size in enumerate(TIERS):
        o = 3 * k
        y0 = k * TIER_H
        for y in range(y0, y0 + TIER_H):
            band = (y - y0) == TIER_H - 1
            for x in range(o, o + size):
                for z in range(o, o + size):
                    edge = x in (o, o + size - 1) or z in (o, o + size - 1)
                    blk = MUD
                    if edge and band:
                        blk = COPPER if (x + z) % 2 == 0 else BRICK
                    elif edge and (x - o) % 6 == 3 and y < y0 + TIER_H - 1:
                        blk = BRICK  # лопатки-пилястры
                    elif not edge:
                        blk = PACKED
                    t.set(x, y, z, blk)
    # недостроенная вершина: стены с проломами, леса, кран, остановленные часы
    o = 3 * len(TIERS)
    y0 = len(TIERS) * TIER_H
    rng = random.Random(5500701)
    for x in range(o, o + TOP_SIZE):
        for z in range(o, o + TOP_SIZE):
            t.set(x, y0, z, MUD)
            if x in (o, o + TOP_SIZE - 1) or z in (o, o + TOP_SIZE - 1):
                h = rng.randint(1, 5)
                for y in range(y0 + 1, y0 + 1 + h):
                    t.set(x, y, z, MUD if rng.random() < 0.8 else BRICK)
    for x, z in ((o - 1, o - 1), (o + TOP_SIZE, o - 1), (o - 1, o + TOP_SIZE), (o + TOP_SIZE, o + TOP_SIZE)):
        for y in range(y0 - 1, y0 + 7):
            t.set(x, y, z, MC + 'scaffolding', distance=0, bottom=False, waterlogged=False)
    cx = o + TOP_SIZE // 2
    t.fill(cx, y0 + 1, cx, cx, y0 + 12, cx, MC + 'stripped_dark_oak_log', axis='y')  # мачта крана
    t.fill(cx - 5, y0 + 12, cx, cx + 2, y0 + 12, cx, MC + 'stripped_dark_oak_log', axis='x')
    t.set(cx + 1, y0 + 13, cx, c('gear'), axis='z', spin=0)
    t.fill(cx - 5, y0 + 8, cx, cx - 5, y0 + 11, cx, MC + 'iron_chain', axis='y')
    t.set(cx - 5, y0 + 7, cx, BRICK)
    # часы на южной грани вершины: стрелки стоят
    for u in range(-1, 2):
        for v in range(-1, 2):
            t.set(cx + u, y0 + 3 + v, o + TOP_SIZE - 1, MC + 'smooth_quartz')
    t.set(cx, y0 + 3, o + TOP_SIZE - 1, MC + 'gold_block')
    t.set(cx, y0 + 4, o + TOP_SIZE - 1, MC + 'sea_lantern')


def spiral(t):
    """Лестницы по уступам: с уступа k вверх вдоль стены яруса k+1, по сторонам по кругу (юг→восток→север→запад)."""
    for k in range(len(TIERS) - 1):
        o, s = 3 * (k + 1), TIERS[k + 1]
        base = (k + 1) * TIER_H           # уровень уступа k (верх яруса k)
        side = k % 4
        for i in range(TIER_H):
            y = base + i
            for w in range(2):            # ширина марша 2, внешняя полоса уступа — проход
                if side == 0:   # юг, вверх на восток
                    x, z, facing = o + 1 + i, o + s + w, 'east'
                elif side == 1:  # восток, вверх на север
                    x, z, facing = o + s + w, o + s - 2 - i, 'north'
                elif side == 2:  # север, вверх на запад
                    x, z, facing = o + s - 2 - i, o - 1 - w, 'west'
                else:            # запад, вверх на юг
                    x, z, facing = o - 1 - w, o + 1 + i, 'south'
                if y > base:
                    t.fill(x, base, z, x, y - 1, z, MUD)
                t.set(x, y, z, MC + 'mud_brick_stairs', facing=facing, half='bottom', shape='straight', waterlogged=False)
    # подъём с земли на первый уступ: марш вдоль южной грани (в лагере), вверх на восток
    for i in range(TIER_H - 1):
        x = 3 + i
        for z in (B, B + 1):
            if i > 0:
                t.fill(x, 1, z, x, i, z, MUD)
            t.set(x, i + 1, z, MC + 'mud_brick_stairs', facing='east', half='bottom', shape='straight', waterlogged=False)
    t.fill(3 + TIER_H - 1, 1, B, 3 + TIER_H, TIER_H - 1, B + 1, MUD)  # площадка наверху марша: с разбега не слететь


def hall(t, rng):
    """Зал языков в нижнем ярусе: билингвы на стенах, замок у северной стены, реликварий в нише."""
    t.fill(HALL0, 1, HALL0, HALL1, 5, HALL1, MC + 'air')
    t.fill(HALL0, 0, HALL0, HALL1, 0, HALL1, MC + 'polished_tuff')
    for x, z in ((10, 10), (10, 26), (26, 10), (26, 26), (18, 10), (18, 26), (10, 18), (26, 18)):
        t.fill(x, 1, z, x, 5, z, BRICK)
    for x in range(HALL0 + 2, HALL1 - 1, 5):
        for z in range(HALL0 + 2, HALL1 - 1, 5):
            t.set(x, 5, z, MC + 'light', level=14)
    for x, z in ((10, 9), (26, 9), (10, 27), (26, 27), (9, 18), (27, 18)):
        t.set(x, 3, z, MC + 'copper_lantern', hanging=False)
    # вход с юга сквозь стену яруса
    t.fill(17, 1, HALL1 + 1, 19, 4, B - 1, MC + 'air')
    # ответ (4 слова) и маршруты к вавилонскому письму
    answer = rng.sample(range(12), 4)
    plaques = []
    for g, w in enumerate(WORDS):
        route = rng.choice(['direct', 'via1', 'via2'])
        if route == 'direct':
            plaques.append((w, 0, w, 3))
        else:
            mid = 1 if route == 'via1' else 2
            plaques.append((w, 0, w, mid))
            plaques.append((w, mid, w, 3))
    rng.shuffle(plaques)
    # места на стенах: два ряда (y 2 и 4); у северной стены — не над замком, у южной — не у входа
    spots = []
    for y in (2, 4):
        for k in range(HALL0 + 2, HALL1 - 2, 5):
            spots.append(('west', HALL0 - 1, y, k))
            spots.append(('east', HALL1 + 1, y, k))
            if not 13 <= k <= 23:
                spots.append(('south', k, y, HALL1 + 1))
                spots.append(('north', k, y, HALL0 - 1))
    assert len(spots) >= len(plaques), (len(spots), len(plaques))
    rng.shuffle(spots)
    for (w1, s1, w2, s2), (wall, a, y, b) in zip(plaques, spots):
        if wall in ('west', 'east'):
            gl(t, a, y, b, w1, s1)
            t.set(a, y, b + 1, COPPER)
            gl(t, a, y, b + 2, w2, s2)
        else:
            gl(t, a, y, b, w1, s1)
            t.set(a + 1, y, b, COPPER)
            gl(t, a + 2, y, b, w2, s2)
    # замок: подсказка картинками над колёсами, колёса, печать
    wx = 16
    for i, g in enumerate(answer):
        gl(t, wx + i, 4, HALL0 - 1, WORDS[g], 0)
        t.set(wx + i, 2, HALL0, c('glyph_wheel'), facing='south', glyph=(g + 5 + 3 * i) % 12)
        t.set(wx + i, 1, HALL0, MC + 'chiseled_tuff_bricks')
    t.set(wx + 5, 2, HALL0, c('glyph_seal'), solved=False, nbt={'id': c('glyph_seal'), 'Answer': tuple(answer)})
    t.set(wx + 5, 1, HALL0, MC + 'chiseled_tuff_bricks')
    # реликварий в северо-восточном углу за печатями (открытые стороны — запад, юг, верх)
    rx, rz = HALL1, HALL0
    reliquary(t, rx, 1, rz, c('chests/babel_hall'))
    for x, y, z in ((rx - 1, 1, rz), (rx - 1, 2, rz), (rx, 1, rz + 1), (rx, 2, rz + 1), (rx, 2, rz)):
        t.set(x, y, z, c('sealed_door'))
    return answer, plaques


def camp(t):
    """Лагерь каменщика у подножия: кирпичи, печь для обжига, глина, ведро смолы — и Отпечаток света «Вавилон»."""
    z0 = B
    for x in range(4, 14):
        for z in range(z0 + 1, z0 + 6):
            if (x + z) % 3 == 0:
                t.set(x, 1, z, BRICK)
                if (x + z) % 2 == 0:
                    t.set(x, 2, z, BRICK)
    t.set(20, 1, z0 + 3, MC + 'furnace', facing='south', lit=True)
    t.set(21, 1, z0 + 3, MC + 'furnace', facing='south', lit=True)
    t.fill(20, 2, z0 + 3, 21, 2, z0 + 3, BRICK)
    t.set(23, 1, z0 + 5, MC + 'clay')
    t.set(24, 1, z0 + 5, MC + 'clay')
    t.set(23, 1, z0 + 4, MC + 'water_cauldron', level=3)
    t.set(26, 1, z0 + 2, MC + 'barrel', facing='up', open=False)
    t.set(17, 1, z0 + 6, c('memory_anchor'), nbt={'id': c('memory_anchor'), 'Scene': 'babel'})
    t.set(17, 1, z0 + 7, MC + 'light', level=10)


def tower():
    rng = random.Random(5500703)
    t = Template(TX, TY, TZ)
    t.fill(0, 1, 0, TX - 1, TY - 1, TZ - 1, MC + 'air')
    t.fill(0, 0, B, TX - 1, 0, TZ - 1, MC + 'packed_mud')  # площадка лагеря
    tiers(t)
    spiral(t)
    answer, plaques = hall(t, rng)
    camp(t)
    t.save('babel_tower/main')
    return answer, plaques


def loot():
    def item(n, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': n, 'weight': w}
        if hi > 1:
            e['modifier'] = [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e
    write_json(os.path.join(DATA, 'loot_table/chests/babel_hall.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/babel_hall'), 'pools': [
            {'rolls': 1, 'entries': [item(c('chronite_helmet'), 1), item(c('chronite_leggings'), 1), item(c('hourglass'), 1)]},
            {'rolls': {'type': 'minecraft:uniform', 'min': 3, 'max': 5}, 'entries': [
                item(c('chronite_ingot'), 6, 2, 4), item(MC + 'emerald', 5, 3, 8), item(MC + 'diamond', 3, 1, 2), item(MC + 'brick', 4, 8, 16),
                item(MC + 'experience_bottle', 4, 3, 8), item(c('ophanim_eye'), 1), item(MC + 'name_tag', 3)]}]})


# ---------------------------------------------------------------- эпизод «Вавилон»
PEOPLE = {
    'mason': ('#c89a72', '#2a1e14', '#8a6a4a', '#c9a24a', '#3a2a1a', False, True),
    'builder': ('#b88a62', '#1a1410', '#a8865a', '#7a4a2a', '#2a2a2a', False, False),
}


def step(t, **kw):
    return {'t': t, **kw}


def stage():
    """Площадка стройки: основание башни 9×9 в три яруса, леса, кирпичи; вокруг — равнина."""
    S, TOP = 41, 3
    t = Template(S, 24, S)
    t.fill(0, 0, 0, S - 1, 23, S - 1, MC + 'air')
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - 20, z - 20)
            if d <= 19.5:
                t.fill(x, 0, z, x, TOP - 1, z, MC + 'packed_mud' if d > 18 else MC + 'mud')
                t.set(x, TOP, z, MC + 'mud' if (x * 7 + z * 3) % 11 else MC + 'coarse_dirt')
    for k, size in enumerate((9, 7, 5)):
        o = 16 + k
        for y in range(TOP + 1 + k * 3, TOP + 4 + k * 3):
            for x in range(o, o + size):
                for z in range(o, o + size):
                    if x in (o, o + size - 1) or z in (o, o + size - 1) or y == TOP + 3 + k * 3:
                        t.set(x, y, z, MC + 'mud_bricks' if (x + y + z) % 5 else MC + 'bricks')
    for x, z in ((15, 15), (25, 15), (15, 25), (25, 25)):
        t.fill(x, TOP + 1, z, x, TOP + 9, z, MC + 'scaffolding', distance=0, bottom=False, waterlogged=False)
    for x in range(8, 14):
        for z in (28, 29):
            t.set(x, TOP + 1, z, MC + 'bricks')
    t.set(27, TOP + 1, 27, MC + 'furnace', facing='west', lit=True)
    for x in range(4, 37, 6):
        for z in range(4, 37, 6):
            t.set(x, TOP + 6, z, MC + 'light', level=13)
    return t.save('memory/babel')


SCENES = {
    'babel': {
        'stage': c('memory/babel'), 'center': [20, 4, 20], 'radius': 19, 'spawn': [20.5, 4, 33.5, 180],
        'sheet': 'babel_tongues', 'thought': 'memory.celestial.babel.thought', 'on_complete': 'clay_tablet',
        'actors': [
            {'id': 'mason', 'type': 'human', 'skin': 'mason', 'pos': [20.5, 4, 27.5], 'yaw': 180},
            {'id': 'b1', 'type': 'human', 'skin': 'builder', 'pos': [15.5, 4, 23.5], 'yaw': 90},
            {'id': 'b2', 'type': 'human', 'skin': 'builder', 'pos': [25.5, 4, 23.5], 'yaw': 270},
            {'id': 'b3', 'type': 'human', 'skin': 'builder', 'pos': [17.5, 4, 14.5], 'yaw': 0},
        ],
        'steps': [
            step('dim', value=0.15),
            step('caption', key='memory.celestial.babel.1', ticks=80),
            step('say', actor='mason', key='memory.celestial.babel.mason1', ticks=70),
            step('near', pos=[20.5, 4, 28.5], r=3, timeout=900),
            step('pose', actor='b1', pose=1),
            step('pose', actor='b2', pose=1),
            step('say', actor='b1', key='memory.celestial.babel.b1', ticks=60),
            step('say', actor='mason', key='memory.celestial.babel.mason2', ticks=70),
            step('look', actor='mason', timeout=600),
            step('particles', type='minecraft:end_rod', pos=[20.5, 16, 20.5], count=60, spread=2.0),
            step('voice', key='memory.celestial.babel.voice', pos=[20.5, 14, 20.5], ticks=90),
            step('dim', value=0.4),
            step('pose', actor='b1', pose=0),
            step('pose', actor='b2', pose=0),
            step('say', actor='b1', key='memory.celestial.babel.g1', ticks=50),
            step('say', actor='mason', key='memory.celestial.babel.g2', ticks=50),
            step('say', actor='b2', key='memory.celestial.babel.g3', ticks=50),
            step('face', actor='b1', to=[2.5, 4, 20.5]),
            step('face', actor='b2', to=[38.5, 4, 20.5]),
            step('face', actor='b3', to=[20.5, 4, 2.5]),
            step('move', actor='b1', to=[4.5, 4, 20.5], speed=0.06, wait=False),
            step('move', actor='b2', to=[36.5, 4, 20.5], speed=0.06, wait=False),
            step('move', actor='b3', to=[20.5, 4, 4.5], speed=0.06, wait=False),
            step('say', actor='mason', key='memory.celestial.babel.g4', ticks=60),
            step('face', actor='mason', to=[36.5, 4, 36.5]),
            step('move', actor='mason', to=[34.5, 4, 34.5], speed=0.05, wait=False),
            step('wait', ticks=60),
            step('caption', key='memory.celestial.babel.2', ticks=90),
            step('dim', value=0.1),
            step('end', ticks=50),
        ],
    },
}
SCENE_LANG = {
    'memory.celestial.who.mason': ('Каменщик', 'Mason'),
    'memory.celestial.who.b1': ('Строитель', 'Builder'),
    'memory.celestial.who.b2': ('Строитель', 'Builder'),
    'memory.celestial.who.b3': ('Строитель', 'Builder'),
    'memory.celestial.babel.1': ('На всей земле был один язык', 'The whole earth had one language'),
    'memory.celestial.babel.mason1': ('Наделаем кирпичей!', 'Let us make brick!'),
    'memory.celestial.babel.b1': ('Ещё ряд — и до неба!', 'One more course — and up to heaven!'),
    'memory.celestial.babel.mason2': ('Сделаем себе имя!', 'Let us make us a name!'),
    'memory.celestial.babel.voice': ('Смешаем там язык их', 'Let us confound their language'),
    'memory.celestial.babel.g1': ('ᚦᚨᛗ ᛞᚢᚱ ᛁᛚ?', 'ᚦᚨᛗ ᛞᚢᚱ ᛁᛚ?'),
    'memory.celestial.babel.g2': ('ᚷᛟᚾ ᚨᚱ ᛏᛁ!', 'ᚷᛟᚾ ᚨᚱ ᛏᛁ!'),
    'memory.celestial.babel.g3': ('ᛖᛋ ᚢᛗ… ᚠᚱᛟ?', 'ᛖᛋ ᚢᛗ… ᚠᚱᛟ?'),
    'memory.celestial.babel.g4': ('ᛚᚨᛉ… ᛚᚨᛉ…', 'ᛚᚨᛉ… ᛚᚨᛉ…'),
    'memory.celestial.babel.2': ('Они перестали понимать друг друга — и рассеялись', 'They no longer understood one another — and scattered'),
    'memory.celestial.babel.thought': ('В руке — глиняная табличка: на ней все четыре письма рядом', 'In my hand, a clay tablet: all four scripts side by side'),
}


# ---------------------------------------------------------------- сюжет, переводы, размещение
def story_and_lang(answer):
    names = {}
    tk, dk = 'advancements.celestial.babel_tongues.title', 'advancements.celestial.babel_tongues.description'
    advancement('babel_tongues', 'clockwork', c('clay_tablet'), {'solved': {'trigger': 'minecraft:impossible'}}, 'goal', tk, dk)
    names[tk] = ('Смешение языков', 'Confusion of Tongues')
    names[dk] = ('Прочти надписи Вавилонской башни и открой её замок', 'Read the inscriptions of the Tower of Babel and open its lock')
    for w, (ru, en) in WORD_LANG.items():
        names[f'glyph.celestial.{w}'] = (ru, en)
    names.update({
        'block.celestial.babel_glyph': ('Глиф Вавилона', 'Babel Glyph'),
        'block.celestial.babel_glyph.lore1': ('Знак одного из четырёх писем', 'A sign in one of four scripts'),
        'block.celestial.glyph_wheel': ('Колесо глифов', 'Glyph Wheel'),
        'block.celestial.glyph_wheel.lore1': ('ПКМ — следующий знак, крадучись — предыдущий', 'Use: next sign, sneak: previous'),
        'block.celestial.glyph_seal': ('Печать смешения', 'Seal of Confusion'),
        'block.celestial.glyph_seal.lore1': ('ПКМ — сверить слова на колёсах', 'Use: check the words on the wheels'),
        'item.celestial.clay_tablet': ('Глиняная табличка', 'Clay Tablet'),
        'item.celestial.clay_tablet.lore1': ('ПКМ по глифу — прочесть знак', 'Use on a glyph to read the sign'),
        'item.celestial.clay_tablet.lore2': ('Все четыре письма Вавилона рядом', 'All four scripts of Babel side by side'),
        'item.celestial.clay_tablet.reads': ('Знак означает: %s', 'The sign means: %s'),
        'puzzle.celestial.babel.picture': ('Рисунок понятен и без слов.', 'The picture needs no words.'),
        'puzzle.celestial.babel.unknown': ('Знак незнаком. Где-то рядом он стоит рядом со знакомым…', 'An unknown sign. Somewhere nearby it stands beside a familiar one…'),
        'puzzle.celestial.babel.wrong': ('Слова не сложились: печать трескается.', 'The words do not fit: the seal cracks.'),
        'puzzle.celestial.babel.solved': ('Печать смешения снята.', 'The Seal of Confusion is lifted.'),
        'puzzle.celestial.babel.creative': ('Печать не отвечает творцу — только страннику.', 'The seal does not answer a creator — only a wanderer.'),
        'codex.celestial.puzzle.babel': ('Смешение языков', 'Confusion of Tongues'),
        'codex.celestial.puzzle.babel.hint': ('над колёсами — слова картинками; набери их вавилонским письмом. Ключ — пары знаков «=» на стенах (Вавилонская башня).',
                                              'above the wheels are words in pictures; spell them in the Babel script. The key is the "=" pairs on the walls (Tower of Babel).'),
        'structure.celestial.babel_tower': ('Вавилонская башня', 'Tower of Babel'),
        'codex.celestial.place.babel_tower': ('недостроенный зиккурат в сердце Хронограда. Внизу — Зал языков с замком глифов, у подножия — лагерь каменщика.',
                                              'an unfinished ziggurat at the heart of Chronograd. Below is the Hall of Tongues with its glyph lock; at its foot, the mason\'s camp.'),
    })
    lang_patch(names)


def structures():
    jigsaw('babel_tower', [c('cog_city')], -1, adaptation='beard_box')
    # размещение — в наборе chrono_landmarks (gen_chrono_places)
    append_tag('worldgen/structure', 'celestial:codex_places', [c('babel_tower')])


def main():
    assets()
    answer, plaques = tower()
    loot()
    structures()
    story_and_lang(answer)
    print('ok: Вавилонская башня; ответ:', [WORDS[g] for g in answer], 'табличек:', len(plaques))


if __name__ == '__main__':
    main()
