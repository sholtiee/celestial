"""Хроноград (волна 0.5): сеть оборотов — вал, шестерня, маховик, часовая пружина, паровой котёл, приводной пресс, пластины.

Вращение показано анимацией текстур: у вращающейся детали (`spin=1` по часовой, `spin=2` против) лицевая грань — кадры
поворота рисунка (шестерня — на шаг зуба, маховик — на шаг спицы), у вала по боковым граням бегут насечки. Остановленная
деталь — первый кадр без анимации. Логика сети — `mech/Gears.java`.
"""
import json
import math
import os

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, c, save_png, blockstate, model, item_def, self_drop, shaped, shapeless
from gen_story import lang_patch

BRASS = T.pal('#6a4416', '#8a5a1c', '#a8722a', '#c48e3a', '#dcaa52', '#f0c86e')
IRON = T.pal('#2e323a', '#3e434d', '#50565f', '#646b75', '#7b828c', '#959ca5')
COPPER = T.pal('#6a2e1a', '#8a3e22', '#a8522c', '#c46a3a', '#d88452', '#eca070')
FRAMES = 8


def put(img, x, y, col, a=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), (*col[:3], a))


def disc_frame(shape, pal, angle, size=16, ss=4):
    """Рисует вращающийся диск: shape(r, a) → None (пусто) или яркость 0..1. Суперсэмплинг ss×ss, порог альфы 0.5."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    c0 = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            hits, light = 0, 0.0
            for sy in range(ss):
                for sx in range(ss):
                    dx = x + (sx + 0.5) / ss - 0.5 - c0
                    dy = y + (sy + 0.5) / ss - 0.5 - c0
                    r = math.hypot(dx, dy) / (size / 2)
                    a = math.atan2(dy, dx) - angle
                    v = shape(r, a)
                    if v is not None:
                        hits += 1
                        light += v
            if hits * 2 >= ss * ss:
                k = light / hits
                col = pal[min(len(pal) - 1, int(k * (len(pal) - 1) + 0.5))]
                put(img, x, y, col)
    return img


def gear_shape(r, a):
    """Шестерня: 8 крупных зубцов (глубина ~2 пикселя), тёмный кант по ободу, 4 окна, втулка с отверстием под вал."""
    tooth = math.cos(a * 8) > -0.1
    if r > 1.0 or (r > 0.74 and not tooth):
        return None
    if r < 0.17:
        return 0.05  # отверстие под вал
    if r < 0.32:
        return 0.95  # втулка
    if 0.42 < r < 0.62 and math.cos(a * 4) > 0.6:
        return None  # облегчающие окна
    if r > 0.92:
        return 0.4  # кант по силуэту зубцов
    if r > 0.74:
        return 0.78  # зубцы
    if r > 0.66:
        return 0.55  # обод
    return 0.68


def flywheel_shape(r, a):
    """Маховик: толстый обод, 6 спиц, крупная втулка."""
    if r > 1.0:
        return None
    if r > 0.66:
        return 0.25 if r > 0.92 or r < 0.72 else 0.7
    if r < 0.30:
        return 0.05 if r < 0.14 else 0.9
    return 0.5 if math.cos(a * 6) > 0.7 else None


def spiral_shape(r, a):
    """Заводная пружина: 2,5 витка широкой ленты на тёмном фоне."""
    if r > 1.0:
        return None
    if r > 0.9:
        return 0.3
    if r < 0.14:
        return 1.0
    turn = (r * 2.6 - (a % (2 * math.pi)) / (2 * math.pi)) % 1.0
    return 0.9 if turn < 0.45 else 0.0


angle_light = 0.0


def save_anim(frames, rel, frametime):
    sheet = Image.new('RGBA', (frames[0].width, frames[0].height * len(frames)))
    for i, f in enumerate(frames):
        sheet.paste(f, (0, f.height * i))
    save_png(sheet, rel)
    with open(os.path.join(ASSETS, 'textures', rel + '.png.mcmeta'), 'w') as f:
        json.dump({'animation': {'frametime': frametime, 'interpolate': False}}, f)


def rotating(name, shape, pal, period, frametime=1):
    """Три текстуры: статичная, по часовой и против — кадры поворота на period радиан."""
    save_png(disc_frame(shape, pal, 0.0), f'block/{name}')
    cw = [disc_frame(shape, pal, period * i / FRAMES) for i in range(FRAMES)]
    save_anim(cw, f'block/{name}_cw', frametime)
    save_anim(cw[:1] + cw[1:][::-1], f'block/{name}_ccw', frametime)


def shaft_side(shift):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            k = 0.65 + 0.25 * math.cos((x % 4 - 1.5) / 1.5)
            groove = (x + y + shift) % 4 == 0  # винтовая насечка
            col = T.shade(IRON[4], k * (0.7 if groove else 1.0))
            put(img, x, y, col)
    for y in (0, 15):
        for x in range(16):
            put(img, x, y, IRON[1])
    return img


def shaft():
    save_png(shaft_side(0), 'block/shaft_side')
    frames = [shaft_side(i) for i in range(4)]
    save_anim(frames, 'block/shaft_side_cw', 2)
    save_anim(frames[:1] + frames[1:][::-1], 'block/shaft_side_ccw', 2)
    end = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            put(end, x, y, IRON[5] if d < 1.2 else IRON[2] if d < 6 else IRON[1])
    save_png(end, 'block/shaft_end')
    for v in ('', '_cw', '_ccw'):
        model('block/shaft' + v, {'parent': 'minecraft:block/block', 'textures': {
            'side': c('block/shaft_side' + v), 'end': c('block/shaft_end'), 'particle': c('block/shaft_side')},
            'elements': [
                {'from': [6, 0, 6], 'to': [10, 16, 10], 'faces': {  # торцы закрывают муфты
                    f: {'uv': [6, 0, 10, 16], 'texture': '#side'} for f in ('north', 'south', 'east', 'west')}},
                {'from': [5, 0, 5], 'to': [11, 1, 11], 'faces': {  # муфты на концах
                    **{f: {'uv': [5, 0, 11, 1], 'texture': '#end'} for f in ('north', 'south', 'east', 'west')},
                    'down': {'uv': [5, 5, 11, 11], 'texture': '#end'}, 'up': {'uv': [5, 5, 11, 11], 'texture': '#end'}}},
                {'from': [5, 15, 5], 'to': [11, 16, 11], 'faces': {
                    **{f: {'uv': [5, 15, 11, 16], 'texture': '#end'} for f in ('north', 'south', 'east', 'west')},
                    'down': {'uv': [5, 5, 11, 11], 'texture': '#end'}, 'up': {'uv': [5, 5, 11, 11], 'texture': '#end'}}},
            ]})
    axis_state('shaft')


def disc_part(name, face_tex, thick, hub_tex, ring):
    """Диск по оси Y: две грани-картинки (верх/низ) толщиной thick, сплошное кольцо-тело и втулка вала."""
    lo, hi = 8 - thick / 2, 8 + thick / 2
    for v in ('', '_cw', '_ccw'):
        model(f'block/{name}{v}', {'parent': 'minecraft:block/block', 'textures': {
            'face': c(f'block/{face_tex}{v}'), 'hub': c(f'block/{hub_tex}'), 'particle': c(f'block/{face_tex}')},
            'elements': [
                {'from': [0.05, lo, 0.05], 'to': [15.95, hi, 15.95], 'faces': {  # ребро — центральная полоса рисунка (силуэт зубцов)
                    'up': {'uv': [0, 0, 16, 16], 'texture': '#face'}, 'down': {'uv': [0, 0, 16, 16], 'texture': '#face'},
                    **{f: {'uv': [0, 8 - thick / 2, 16, 8 + thick / 2], 'texture': '#face'} for f in ('north', 'south', 'east', 'west')}}},
                {'from': [8 - ring, lo + 0.25, 8 - ring], 'to': [8 + ring, hi - 0.25, 8 + ring], 'faces': {
                    f: {'uv': [0, 0, 2 * ring, hi - lo - 0.5], 'texture': '#hub'} for f in ('north', 'south', 'east', 'west')}},
                {'from': [6, 0, 6], 'to': [10, 16, 10], 'faces': {
                    **{f: {'uv': [6, 0, 10, 16], 'texture': '#hub'} for f in ('north', 'south', 'east', 'west')},
                    'up': {'uv': [6, 6, 10, 10], 'texture': '#hub'}, 'down': {'uv': [6, 6, 10, 10], 'texture': '#hub'}}},
            ]})
    axis_state(name)


def axis_state(name):
    rot = {'y': {}, 'x': {'x': 90, 'y': 90}, 'z': {'x': 90}}
    blockstate(name, {'variants': {
        f'axis={a},spin={s}': {'model': c(f'block/{name}' + ('', '_cw', '_ccw')[s]), **r}
        for a, r in rot.items() for s in range(3)}})
    item_def(name, c('block/' + name))
    self_drop(name)


def gear():
    rotating('gear_face', gear_shape, BRASS, math.pi / 4)
    disc_part('gear', 'gear_face', 3, 'shaft_end', 4.5)


def flywheel():
    rotating('flywheel_face', flywheel_shape, IRON, math.pi / 3)
    disc_part('flywheel', 'flywheel_face', 5, 'shaft_end', 2.5)


# ---------------------------------------------------------------- источники и пресс
def riveted(name, pal, rim):
    img = T.noisy(name, pal[1:5], cell=4, grain=0.18)
    for i in range(16):
        for x, y in ((i, 0), (i, 15), (0, i), (15, i)):
            put(img, x, y, rim)
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(img, x, y, pal[-1])
        put(img, x + 1, y + 1, rim)
    return img


def coupling(base):
    """Выходная грань: квадратная муфта под вал."""
    img = base.copy()
    for y in range(16):
        for x in range(16):
            d = max(abs(x - 7.5), abs(y - 7.5))
            if d < 2.5:
                put(img, x, y, IRON[4] if d < 1.5 else IRON[1])
            elif d < 3.5:
                put(img, x, y, IRON[0])
    return img


def spring():
    rim = T.hexrgb('#4a2c0c')
    side = riveted('clock_spring_side', BRASS, rim)
    save_png(side, 'block/clock_spring_side')
    save_png(coupling(side), 'block/clock_spring_front')
    # лицо пружины: спираль в латунной раме; заведённая — спираль раскручивается (поворот кадров)
    def face(angle):
        img = side.copy()
        sp = disc_frame(spiral_shape, [T.hexrgb('#3a2408'), BRASS[2], BRASS[3], BRASS[4], BRASS[5]], angle, 12)
        img.alpha_composite(sp, (2, 2))
        return img
    save_png(face(0.0), 'block/clock_spring_face')
    save_anim([face(-2 * math.pi * i / 16) for i in range(16)], 'block/clock_spring_face_active', 2)
    source_models('clock_spring', 'clock_spring_front', 'clock_spring_face', 'clock_spring_side', 'clock_spring_side')


def engine():
    rim = T.hexrgb('#4a1e0c')
    side = riveted('steam_engine_side', COPPER, rim)
    for x in range(16):  # заклёпочный пояс
        put(side, x, 8, T.shade(COPPER[2], 0.8))
    save_png(side, 'block/steam_engine_side')
    save_png(coupling(side), 'block/steam_engine_front')

    def firebox(lit, t=0):
        img = side.copy()
        for y in range(10, 15):  # топка с решёткой
            for x in range(4, 12):
                if lit:
                    k = 0.6 + 0.4 * math.sin(x * 1.7 + y * 0.9 + t * 1.3)
                    col = T.mix(T.hexrgb('#ff5a10'), T.hexrgb('#ffd060'), max(0, k))
                else:
                    col = T.hexrgb('#1a0e08')
                put(img, x, y, IRON[1] if x in (4, 11) or y == 10 or x % 3 == 0 else col)
        for x in range(3, 13):  # манометр
            pass
        for y in range(2, 7):
            for x in range(5, 10):
                d = math.hypot(x - 7, y - 4)
                if d < 2.6:
                    put(img, x, y, T.hexrgb('#f0e8d0') if d < 1.9 else IRON[1])
        put(img, 7, 4, T.hexrgb('#a01010'))
        put(img, 8 if lit else 6, 3, T.hexrgb('#a01010'))
        return img
    save_png(firebox(False), 'block/steam_engine_face')
    save_anim([firebox(True, i) for i in range(6)], 'block/steam_engine_face_active', 3)
    top = riveted('steam_engine_top', COPPER, rim)
    for y in range(16):
        for x in range(16):
            if math.hypot(x - 7.5, y - 7.5) < 3.0:
                put(top, x, y, T.hexrgb('#1a1008'))
    save_png(top, 'block/steam_engine_top')
    source_models('steam_engine', 'steam_engine_front', 'steam_engine_face', 'steam_engine_side', 'steam_engine_top', chimney=True)


def source_models(name, front, face, side, top, chimney=False):
    """Выход (front) — на север модели; «лицо» (face) — на юг (видно спереди, когда выход в стену); активная — анимированное лицо."""
    for active in (False, True):
        v = '_active' if active else ''
        elements = [{'from': [0, 0, 0], 'to': [16, 16, 16], 'faces': {
            'north': {'uv': [0, 0, 16, 16], 'texture': '#front'}, 'south': {'uv': [0, 0, 16, 16], 'texture': '#face'},
            'east': {'uv': [0, 0, 16, 16], 'texture': '#face'}, 'west': {'uv': [0, 0, 16, 16], 'texture': '#face'},
            'up': {'uv': [0, 0, 16, 16], 'texture': '#top'}, 'down': {'uv': [0, 0, 16, 16], 'texture': '#side'}}}]
        if chimney:
            elements.append({'from': [6, 16, 10], 'to': [10, 22, 14], 'faces': {
                **{f: {'uv': [6, 0, 10, 6], 'texture': '#side'} for f in ('north', 'south', 'east', 'west')},
                'up': {'uv': [6, 6, 10, 10], 'texture': '#top'}}})
        model(f'block/{name}{v}', {'parent': 'minecraft:block/block', 'textures': {
            'front': c('block/' + front), 'face': c(f'block/{face}{v}'), 'side': c('block/' + side), 'top': c('block/' + top),
            'particle': c('block/' + side)}, 'elements': elements})
    rot = {'north': {}, 'east': {'y': 90}, 'south': {'y': 180}, 'west': {'y': 270}, 'up': {'x': 270}, 'down': {'x': 90}}
    blockstate(name, {'variants': {
        f'active={str(a).lower()},facing={f}': {'model': c(f'block/{name}' + ('_active' if a else '')), **r}
        for f, r in rot.items() for a in (False, True)}})
    item_def(name, c('block/' + name))
    self_drop(name)


def press():
    rim = T.hexrgb('#22262e')
    base = riveted('drive_press_side', IRON, rim)
    for x in range(16):
        put(base, x, 7, T.hexrgb('#c8a040'))  # латунная полоса по станине
    save_png(base, 'block/drive_press_side')
    anvil = T.noisy('drive_press_top', IRON[2:], cell=4, grain=0.1)
    for i in range(16):
        put(anvil, i, 0, rim)
        put(anvil, i, 15, rim)
        put(anvil, 0, i, rim)
        put(anvil, 15, i, rim)
    for y in range(4, 12):
        for x in range(4, 12):
            put(anvil, x, y, T.shade(IRON[4], 1.1 if (x + y) % 2 else 1.0))
    save_png(anvil, 'block/drive_press_top')
    def box(f, t, tex, skip=()):
        return {'from': f, 'to': t, 'faces': {d: {'texture': tex} for d in ('north', 'south', 'east', 'west', 'up', 'down') if d not in skip}}
    for working in (False, True):
        head_y = 9.5 if working else 11
        model('block/drive_press' + ('_working' if working else ''), {'parent': 'minecraft:block/block', 'textures': {
            'side': c('block/drive_press_side'), 'top': c('block/drive_press_top'), 'shaft': c('block/shaft_side'),
            'particle': c('block/drive_press_side')},
            'elements': [
                box([0, 0, 0], [16, 9, 16], '#side') | {'faces': {
                    **{d: {'uv': [0, 7, 16, 16], 'texture': '#side'} for d in ('north', 'south', 'east', 'west')},
                    'up': {'texture': '#top'}, 'down': {'texture': '#side'}}},
                box([1, 9, 1], [3, 14, 3], '#side', ('up', 'down')), box([13, 9, 1], [15, 14, 3], '#side', ('up', 'down')),
                box([1, 9, 13], [3, 14, 15], '#side', ('up', 'down')), box([13, 9, 13], [15, 14, 15], '#side', ('up', 'down')),
                box([0, 14, 0], [16, 16, 16], '#side'),
                box([7, head_y + 3, 7], [9, 14, 9], '#shaft', ('up', 'down')),
                box([4, head_y, 4], [12, head_y + 3, 12], '#top'),
            ]})
    blockstate('drive_press', {'variants': {
        'working=false': {'model': c('block/drive_press')}, 'working=true': {'model': c('block/drive_press_working')}}})
    item_def('drive_press', c('block/drive_press'))
    self_drop('drive_press')


def plates():
    for name, pal in (('iron_plate', IRON), ('copper_plate', COPPER), ('gold_plate', BRASS)):
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        for y in range(4, 13):  # пластина в лёгкой перспективе
            off = (12 - y) // 3
            for x in range(2 + off, 14 + off - 2):
                k = 0.75 + 0.25 * ((x - y) % 7 == 0) + (0.15 if y == 4 else 0) - (0.2 if y == 12 else 0)
                put(img, x, y, T.shade(pal[3], k))
        save_png(img, 'item/' + name)
        model('item/' + name, {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/' + name)}})
        item_def(name, c('item/' + name))


def recipes():
    shaped('shaft', c('shaft'), ['I', 'I', 'I'], {'I': 'minecraft:iron_ingot'}, 6, 'redstone')
    shaped('gear', c('gear'), [' C ', 'CIC', ' C '], {'C': 'minecraft:copper_ingot', 'I': 'minecraft:iron_nugget'}, 2, 'redstone')
    shaped('flywheel', c('flywheel'), ['PPP', 'PSP', 'PPP'], {'P': c('iron_plate'), 'S': c('shaft')}, 1, 'redstone')
    shaped('clock_spring', c('clock_spring'), ['GPG', 'PKP', 'GSG'],
           {'G': c('gold_plate'), 'P': c('copper_plate'), 'K': 'minecraft:clock', 'S': c('shaft')}, 1, 'redstone')
    shaped('steam_engine', c('steam_engine'), ['PPP', 'PBP', 'PFP'],
           {'P': c('copper_plate'), 'B': 'minecraft:bucket', 'F': 'minecraft:furnace'}, 1, 'redstone')
    shaped('drive_press', c('drive_press'), ['PPP', 'ISI', 'XXX'],
           {'P': 'minecraft:iron_ingot', 'I': 'minecraft:iron_bars', 'S': 'minecraft:piston', 'X': 'minecraft:smooth_stone'}, 1, 'redstone')
    for name, ingot in (('iron_plate', 'minecraft:iron_ingot'), ('copper_plate', 'minecraft:copper_ingot'), ('gold_plate', 'minecraft:gold_ingot')):
        shapeless(name + '_by_hand', c(name), [ingot, ingot])  # вручную — вдвое дороже, чем прессом


def lang():
    lang_patch({
        'block.celestial.shaft': ('Вал', 'Shaft'),
        'block.celestial.shaft.lore1': ('Передаёт вращение вдоль своей оси', 'Carries rotation along its axis'),
        'block.celestial.gear': ('Шестерня', 'Gear'),
        'block.celestial.gear.lore1': ('Зацепляется с соседними шестернями — те крутятся в обратную сторону', 'Meshes with neighbouring gears — they turn the other way'),
        'block.celestial.gear.lore2': ('Два источника, что крутят навстречу, заклинят сеть', 'Two sources turning against each other jam the network'),
        'block.celestial.flywheel': ('Маховик', 'Flywheel'),
        'block.celestial.flywheel.lore1': ('Копит разгон: ещё 10 с крутит сеть без источника', 'Stores momentum: keeps the network turning for 10 s'),
        'block.celestial.clock_spring': ('Часовая пружина', 'Clock Spring'),
        'block.celestial.clock_spring.lore1': ('ПКМ пустой рукой — завести на 30 с (до 2 мин)', 'Use with an empty hand to wind for 30 s (up to 2 min)'),
        'block.celestial.clock_spring.lore2': ('Крутит вал или шестерню перед своей муфтой', 'Turns the shaft or gear facing its coupling'),
        'block.celestial.clock_spring.wound': ('Пружина заведена: %s с', 'Spring wound: %s s'),
        'block.celestial.steam_engine': ('Паровой котёл', 'Steam Engine'),
        'block.celestial.steam_engine.lore1': ('Работает, пока под ним огонь, лава или магма', 'Runs while fire, lava or magma burns beneath it'),
        'block.celestial.steam_engine.lore2': ('Крутит вал или шестерню перед своей муфтой', 'Turns the shaft or gear facing its coupling'),
        'block.celestial.drive_press': ('Приводной пресс', 'Drive Press'),
        'block.celestial.drive_press.lore1': ('ПКМ слитком — положить; пустой рукой — забрать', 'Use with an ingot to load; with an empty hand to take back'),
        'block.celestial.drive_press.lore2': ('Работает от вала или шестерни: слиток → пластина', 'Driven by a shaft or gear: ingot → plate'),
        'block.celestial.drive_press.busy': ('На прессе уже лежит другое', 'Something else is already on the press'),
        'block.celestial.drive_press.empty': ('Пресс пуст', 'The press is empty'),
        'block.celestial.drive_press.no_drive': ('Пресс пуст и стоит: нужен вращающийся вал', 'The press is empty and idle: it needs a turning shaft'),
        'item.celestial.iron_plate': ('Железная пластина', 'Iron Plate'),
        'item.celestial.iron_plate.lore1': ('Деталь механизмов', 'A part for mechanisms'),
        'item.celestial.copper_plate': ('Медная пластина', 'Copper Plate'),
        'item.celestial.copper_plate.lore1': ('Деталь механизмов', 'A part for mechanisms'),
        'item.celestial.gold_plate': ('Золотая пластина', 'Gold Plate'),
        'item.celestial.gold_plate.lore1': ('Деталь часовых механизмов', 'A part for clockwork'),
    })


def main():
    shaft()
    gear()
    flywheel()
    spring()
    engine()
    press()
    plates()
    recipes()
    append_tag('block', 'minecraft:mineable/pickaxe', [c(n) for n in ('shaft', 'gear', 'flywheel', 'clock_spring', 'steam_engine', 'drive_press')])
    lang()
    print('Сеть оборотов: вал, шестерня, маховик, пружина, котёл, пресс, пластины')


if __name__ == '__main__':
    main()
