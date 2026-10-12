"""Загадки времени (волна 0.5, S4.7) и постройка «Хранилище времени» в Хронограде.

Три зала в ряд вдоль x, у каждого — свой Реликварий за печатью (радиусы наград не задевают соседей):
  A «Связанные часы» — три циферблата на северной стене сцеплены шестернями по кругу (поворот i двигает и i+1);
    над каждым — фреска: неподвижные часы в медной раме показывают час-цель. Начальные часы и цели выводятся из случайных
    нажатий (решение существует; записано в комментарии scenario-файла генератором).
  B «Ход маятника» — над ямой ряд платформ такта от стартового уступа к финишу; древний лёгкий маятник гонит такт (не успеть),
    тяжёлый (стоит) — замедляет. Камертон — в сундуке на старте.
  C «Комната-перемотка» — каждые 45 с комната возвращается к снимку; зажечь три якоря за один оборот: на столбе (строй вверх),
    на острове во рву (строй мост), в каменной клети (ломай). Бочка с припасами пополняется каждый оборот.
"""
import math
import os
import random

from PIL import Image

import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, blockstate, c, item_def, model, save_png, write_json
from gen_places import jigsaw
from gen_story import advancement, lang_patch
from gen_structures import Template, chest, reliquary

H = T.hexrgb
MC = 'minecraft:'
WALL, TRIM, ROOF = MC + 'deepslate_bricks', MC + 'waxed_cut_copper', MC + 'waxed_oxidized_cut_copper'
FLOOR = MC + 'polished_deepslate'
BRASS = [H(h) for h in ('#b8862e', '#c9973a', '#d0a044', '#bf8f34')]
DARK, LIGHT = H('#5e4016'), H('#f2d68a')

TX, TY, TZ = 79, 24, 19
FY = 4            # пол залов
HALLS = {'A': 0, 'B': 28, 'C': 56}
HW = 23           # ширина зала по x


# ---------------------------------------------------------------- текстуры и модели
def dial_face(hour):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d <= 7.4:
                col = H('#f4ead2') if d < 6.2 else (BRASS[(x + y) % 4] if d < 7.0 else DARK)
                img.putpixel((x, y), (*col, 255))
    for k in range(12):  # риски часов
        a = k * math.pi / 6
        px, py = 7.5 + math.sin(a) * 5.3, 7.5 - math.cos(a) * 5.3
        img.putpixel((round(px - 0.5), round(py - 0.5)), (*(H('#7a1a10') if k == 0 else H('#3a2a14')), 255))
    a = hour * math.pi / 6
    for i in range(1, 9):  # стрелка
        r = i * 0.6
        img.putpixel((round(7.5 + math.sin(a) * r - 0.5), round(7.5 - math.cos(a) * r - 0.5)), (*H('#1a1a22'), 255))
    for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):
        img.putpixel((x, y), (*LIGHT, 255))
    return img


def brass_plate(seed, ghost=False, pips=0):
    r = T.rng_for(seed)
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            if ghost:
                if edge or (x + y) % 6 == 0:
                    img.putpixel((x, y), (255, 214, 120, 120 if edge else 50))
                continue
            col = r.choice(BRASS)
            if edge:
                col = DARK
            elif x in (1, 14) or y in (1, 14):
                col = T.mix(col, LIGHT, 0.4)
            elif (x - 7.5) ** 2 + (y - 7.5) ** 2 < 9 and (x + y) % 2 == 0:
                col = T.shade(col, 0.8)  # шестерёнка в центре
            img.putpixel((x, y), (*col, 255))
    for k in range(pips):  # точки фазы: 1..4 — чтобы глаз видел волну
        x = 4 + k * 3
        img.putpixel((x, 3), (90, 255, 200, 255 if not ghost else 160))
        img.putpixel((x, 4), (90, 255, 200, 255 if not ghost else 160))
    return img


def anchor_tex(lit):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    r = T.rng_for('rewind_anchor')
    for y in range(16):
        for x in range(16):
            col = T.mix(r.choice([H('#2a3640'), H('#33424e')]), H('#1a2228'), 0.2)
            if x in (0, 15) or y in (0, 15):
                col = H('#c48e3a')
            img.putpixel((x, y), (*col, 255))
    shape = ['...########...', '....######....', '.....####.....', '......##......', '......##......', '.....####.....',
             '....######....', '...########...']
    for y, row in enumerate(shape):
        for x, ch in enumerate(row):
            if ch == '#':
                img.putpixel((x + 1, y + 4), (120, 255, 240, 255) if lit else (90, 140, 150, 255))
    return img


def assets():
    for h in range(12):
        save_png(dial_face(h), f'block/clock_dial_{h}')
        model(f'block/clock_dial_{h}', {'parent': 'minecraft:block/block', 'textures': {'face': c(f'block/clock_dial_{h}'), 'side': c('block/clock_dial_side'),
                                                                                      'particle': c('block/clock_dial_side')},
                                        'elements': [{'from': [1, 1, 14], 'to': [15, 15, 16], 'faces': {
                                            'north': {'texture': '#face', 'uv': [1, 1, 15, 15]}, 'south': {'texture': '#side'},
                                            'east': {'texture': '#side'}, 'west': {'texture': '#side'}, 'up': {'texture': '#side'},
                                            'down': {'texture': '#side'}}}]})
    save_png(brass_plate('clock_dial_side'), 'block/clock_dial_side')
    rot = {'north': 0, 'east': 90, 'south': 180, 'west': 270}
    blockstate('clock_dial', {'variants': {f'facing={f},hour={h}': {'model': c(f'block/clock_dial_{h}'), 'y': y}
                                           for f, y in rot.items() for h in range(12)}})
    item_def('clock_dial', c('block/clock_dial_0'))
    # платформы такта: твёрдая плита и призрачный контур, точки фазы
    for p in range(4):
        save_png(brass_plate(f'tick_platform_{p}', pips=p + 1), f'block/tick_platform_{p}')
        save_png(brass_plate(f'tick_platform_{p}', ghost=True, pips=p + 1), f'block/tick_platform_ghost_{p}')
        for ghost in (False, True):
            name = f'tick_platform_{"ghost_" if ghost else ""}{p}'
            m = {'parent': 'minecraft:block/slab_top', 'textures': {'top': c('block/' + name), 'bottom': c('block/' + name),
                                                                  'side': c('block/' + name)}}
            if ghost:
                m['render_type'] = 'minecraft:translucent'
            model('block/' + name, m)
    blockstate('tick_platform', {'variants': {f'phase={p},solid={str(s).lower()}': {'model': c(f'block/tick_platform_{"" if s else "ghost_"}{p}')}
                                              for p in range(4) for s in (True, False)}})
    item_def('tick_platform', c('block/tick_platform_0'))
    save_png(dial_face(0), 'block/tick_goal_top')
    save_png(brass_plate('tick_goal_side'), 'block/tick_goal_side')
    model('block/tick_goal', {'parent': 'minecraft:block/block', 'textures': {'top': c('block/tick_goal_top'), 'side': c('block/tick_goal_side'),
                                                                            'particle': c('block/tick_goal_side')},
                              'elements': [{'from': [1, 0, 1], 'to': [15, 1, 15], 'faces': {
                                  'up': {'texture': '#top', 'uv': [1, 1, 15, 15]}, 'down': {'texture': '#side'}, 'north': {'texture': '#side', 'uv': [1, 15, 15, 16]},
                                  'south': {'texture': '#side', 'uv': [1, 15, 15, 16]}, 'east': {'texture': '#side', 'uv': [1, 15, 15, 16]},
                                  'west': {'texture': '#side', 'uv': [1, 15, 15, 16]}}}]})
    blockstate('tick_goal', {'variants': {'': {'model': c('block/tick_goal')}}})
    item_def('tick_goal', c('block/tick_goal'))
    for lit in (False, True):
        n = 'rewind_anchor' + ('_lit' if lit else '')
        save_png(anchor_tex(lit), 'block/' + n)
        model('block/' + n, {'parent': 'minecraft:block/cube_all', 'textures': {'all': c('block/' + n)}})
    blockstate('rewind_anchor', {'variants': {f'lit={str(l).lower()}': {'model': c('block/rewind_anchor' + ('_lit' if l else ''))} for l in (False, True)}})
    item_def('rewind_anchor', c('block/rewind_anchor'))
    for hidden in ('tick_conductor', 'rewind_core'):  # невидимые контроллеры
        model('block/' + hidden, {'textures': {'particle': c('block/clock_dial_side')}})
        blockstate(hidden, {'variants': {'': {'model': c('block/' + hidden)}}})


# ---------------------------------------------------------------- постройка
def shell(t):
    """Корпус хранилища: три зала с коридорами, стены с медными пилястрами, кровля."""
    t.fill(0, 0, 0, TX - 1, FY, TZ - 1, FLOOR)
    t.fill(0, FY + 1, 0, TX - 1, TY - 1, TZ - 1, MC + 'air')
    for name, x0 in HALLS.items():
        x1 = x0 + HW - 1
        for y in range(FY + 1, 16):
            for x in range(x0, x1 + 1):
                for z in range(TZ):
                    if x in (x0, x1) or z in (0, TZ - 1):
                        pil = (x - x0) % 4 == 0 and z in (0, TZ - 1) or z % 4 == 1 and x in (x0, x1)
                        t.set(x, y, z, TRIM if pil or y in (FY + 1, 15) else WALL)
        t.fill(x0, 16, 0, x1, 16, TZ - 1, WALL)
        t.fill(x0, 17, 0, x1, 17, TZ - 1, ROOF)
        for x in range(x0, x1 + 1):  # зубцы парапета
            for z in (0, TZ - 1):
                if (x - x0) % 2 == 0:
                    t.set(x, 18, z, WALL)
        for z in range(TZ):
            for x in (x0, x1):
                if z % 2 == 0:
                    t.set(x, 18, z, WALL)
        for bx, bz in ((x0, 0), (x1 - 2, 0), (x0, TZ - 3), (x1 - 2, TZ - 3)):  # угловые башенки
            t.fill(bx, 17, bz, bx + 2, 20, bz + 2, WALL)
            t.fill(bx, 19, bz, bx + 2, 19, bz + 2, TRIM)
            t.fill(bx, 21, bz, bx + 2, 21, bz + 2, ROOF)
            t.set(bx + 1, 22, bz + 1, MC + 'copper_lantern', hanging=False)
        for x in range(x0 + 2, x1 - 1, 4):  # окна в длинных стенах
            for z in (0, TZ - 1):
                if name != 'A' or z != 0:
                    t.fill(x, 10, z, x + 1, 12, z, MC + 'yellow_stained_glass')
        for x in range(x0 + 3, x1 - 2, 4):  # свет: невидимый под потолком и пониже
            for z in (4, 9, 14):
                t.set(x, 15, z, MC + 'light', level=15)
                t.set(x, 11, z, MC + 'light', level=13)
        # проёмы в торцах (3×3, по центру)
        t.fill(x0, FY + 1, 8, x0, FY + 3, 10, MC + 'air')
        t.fill(x1, FY + 1, 8, x1, FY + 3, 10, MC + 'air')
    for x0, x1 in ((HW, HALLS['B'] - 1), (HALLS['B'] + HW, HALLS['C'] - 1)):  # коридоры
        t.fill(x0, FY + 1, 7, x1, FY + 4, 11, WALL)
        t.fill(x0, FY + 1, 8, x1, FY + 3, 10, MC + 'air')
        t.fill(x0, FY + 5, 7, x1, FY + 5, 11, ROOF)
        t.set((x0 + x1) // 2, FY + 3, 9, MC + 'copper_lantern', hanging=True)
    # фасад у входа: арка и фонари
    for z in (6, 12):
        t.fill(0, FY + 1, z, 0, FY + 6, z, TRIM)
        t.set(0, FY + 7, z, MC + 'copper_lantern', hanging=False)
    t.fill(0, FY + 5, 7, 0, FY + 5, 11, MC + 'waxed_chiseled_copper')
    t.fill(0, 17, 6, 4, 22, 12, WALL)  # надвратная башенка с циферблатом
    t.fill(0, 19, 6, 4, 19, 12, TRIM)
    t.fill(0, 23, 6, 4, 23, 12, ROOF)
    for v in range(-1, 2):
        for u in range(-1, 2):
            t.set(0, 21 + v, 9 + u, MC + 'smooth_quartz')
    t.set(0, 21, 9, MC + 'gold_block')
    t.set(0, 22, 9, MC + 'sea_lantern')


def niche(t, x, z, wall_axis):
    """Реликварий в нише стены за печатью-дверью (2 блока высотой)."""
    reliquary(t, x, FY + 1, z, c('chests/time_vault'))
    if wall_axis == 'z':  # стена на юге: печать к северу от ниши
        t.set(x, FY + 1, z - 1, c('sealed_door'))
        t.set(x, FY + 2, z - 1, c('sealed_door'))
    else:  # стена на востоке
        t.set(x - 1, FY + 1, z, c('sealed_door'))
        t.set(x - 1, FY + 2, z, c('sealed_door'))
    t.set(x, FY + 2, z, MC + 'light', level=10)


def hall_dials(t, rng):
    x0 = HALLS['A']
    presses = [rng.randint(1, 5) for _ in range(3)]
    start = [rng.randrange(12) for _ in range(3)]
    target = [(start[i] + presses[i] + presses[i - 1]) % 12 for i in range(3)]
    for i, dx in enumerate((4, 11, 18)):
        x = x0 + dx
        t.set(x, FY + 3, 1, c('clock_dial'), facing='south', hour=start[i], nbt={'id': c('clock_dial'), 'Index': i, 'Target': target[i]})
        t.set(x, FY + 2, 1, MC + 'waxed_chiseled_copper')
        # фреска: тёмная панель в медной раме, на ней неподвижные часы с нужным часом
        t.fill(x - 2, FY + 6, 0, x + 2, FY + 10, 0, MC + 'waxed_copper_block')
        t.fill(x - 1, FY + 7, 0, x + 1, FY + 9, 0, MC + 'polished_blackstone_bricks')
        t.fill(x - 1, FY + 7, 1, x + 1, FY + 9, 1, MC + 'air')
        t.set(x, FY + 8, 1, c('clock_dial'), facing='south', hour=target[i], nbt={'id': c('clock_dial'), 'Index': -1, 'Target': target[i]})
        t.set(x, FY + 11, 0, MC + 'sea_lantern')  # звезда над фреской
        t.set(x, FY + 6, 1, MC + 'light', level=12)
    for gx in (x0 + 7, x0 + 8, x0 + 14, x0 + 15):  # шестерни сцепления между циферблатами
        t.set(gx, FY + 3, 0, c('gear'), axis='z', spin=0)
    t.set(x0 + 21, FY + 3, 0, c('gear'), axis='z', spin=0)  # и от последнего — назад к первому (по кругу)
    t.set(x0 + 1, FY + 3, 0, c('gear'), axis='z', spin=0)
    niche(t, x0 + 11, TZ - 1, 'z')
    t.set(x0 + 11, FY + 1, 9, MC + 'lectern', facing='north', has_book=False, powered=False)
    return {'presses': presses, 'start': start, 'target': target}


def hall_ticks(t):
    x0 = HALLS['B']
    top = FY + 4  # уровень платформ (плита в верхней половине блока y=top)
    t.fill(x0 + 1, FY + 1, 1, x0 + 3, top, TZ - 2, FLOOR)            # стартовый уступ
    t.fill(x0 + 19, FY + 1, 1, x0 + 21, top, TZ - 2, FLOOR)          # финишный уступ
    t.fill(x0 + 1, FY + 1, 8, x0 + 3, FY + 3, 10, MC + 'air')        # проходы сквозь уступы к торцевым проёмам (низом, по дну ямы)
    t.fill(x0 + 19, FY + 1, 8, x0 + 21, FY + 3, 10, MC + 'air')
    path = list(range(x0 + 5, x0 + 18, 2))                           # 7 платформ через клетку
    for k, x in enumerate(path):
        t.set(x, top, 9, c('tick_platform'), solid=True, phase=(4 - k % 4) % 4)
    t.fill(x0 + 4, FY + 1, 13, x0 + 4, top, 13, MC + 'ladder', facing='east', waterlogged=False)  # выход из ямы на старт
    t.set(x0 + 20, top + 1, 9, c('tick_goal'))
    # реликварий в клети из печатей на финишном уступе
    rx, rz = x0 + 21, 14
    reliquary(t, rx, top + 1, rz, c('chests/time_vault'))
    for x, y, z in ((rx - 1, top + 1, rz), (rx, top + 1, rz - 1), (rx, top + 1, rz + 1), (rx, top + 2, rz), (rx - 1, top + 2, rz)):
        t.set(x, y, z, c('sealed_door'))
    # маятники на стартовом уступе: древний лёгкий качается, тяжёлый стоит (пустить рукой)
    t.set(x0 + 2, top + 1, 3, c('swift_pendulum'), facing='east', swinging=True, sealed=True, nbt={'id': c('pendulum')})
    t.set(x0 + 2, top + 1, 15, c('heavy_pendulum'), facing='east', swinging=False, nbt={'id': c('pendulum')})
    chest(t, x0 + 1, top + 1, 6, c('chests/tick_hall_fork'), facing='east')
    t.set(x0 + 11, 16, 9, c('tick_conductor'), nbt={'id': c('tick_conductor')})


def hall_rewind(t):
    x0 = HALLS['C']
    cx, cz = x0 + 11, 9
    t.fill(x0 + HW - 1, FY + 1, 8, x0 + HW - 1, FY + 3, 10, WALL)   # восточный торец глухой
    for x in range(x0 + 1, x0 + HW - 1):                             # ров вокруг острова
        for z in range(1, TZ - 1):
            d = max(abs(x - cx), abs(z - cz))
            if 3 <= d <= 6:
                t.fill(x, 1, z, x, FY, z, MC + 'air')
                t.set(x, 0, z, MC + 'magma_block' if (x + z) % 5 == 0 else FLOOR)
    t.fill(cx, 1, cz - 6, cx, FY, cz - 6, MC + 'ladder', facing='south', waterlogged=False)
    t.set(cx, FY + 1, cz, c('rewind_anchor'), lit=False)             # якорь на острове
    t.fill(x0 + 3, FY + 1, 3, x0 + 3, FY + 7, 3, MC + 'polished_deepslate')  # столб 7 блоков
    t.set(x0 + 3, FY + 8, 3, c('rewind_anchor'), lit=False)
    t.fill(x0 + 17, FY + 1, 13, x0 + 20, FY + 4, 16, WALL)           # клеть: внутри 2×2×2, якорь в углу
    t.fill(x0 + 18, FY + 1, 14, x0 + 19, FY + 2, 15, MC + 'air')
    t.set(x0 + 18, FY + 1, 14, c('rewind_anchor'), lit=False)
    t.set(x0 + 19, FY + 2, 15, MC + 'light', level=10)
    t.set(x0 + 2, FY + 1, 9, MC + 'barrel', facing='up', open=False, nbt={'id': MC + 'barrel'})
    t.set(cx, 16, cz, c('rewind_core'), nbt={'id': c('rewind_core'), 'From': (-11, -16, -9), 'To': (11, 0, 9)})
    niche(t, x0 + 11, TZ - 1, 'z')


def vault():
    rng = random.Random(5500601)
    t = Template(TX, TY, TZ)
    shell(t)
    sol = hall_dials(t, rng)
    hall_ticks(t)
    hall_rewind(t)
    t.save('time_vault/main')
    return sol


def loot():
    def item(n, w, lo=1, hi=1):
        e = {'type': 'minecraft:item', 'name': n, 'weight': w}
        if hi > 1:
            e['modifier'] = [{'type': 'minecraft:set_count', 'count': {'type': 'minecraft:uniform', 'min': lo, 'max': hi}}]
        return e
    write_json(os.path.join(DATA, 'loot_table/chests/time_vault.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/time_vault'), 'pools': [
            {'rolls': 1, 'entries': [item(c('hourglass'), 2), item(c('chronite_chestplate'), 1), item(c('chronite_sword'), 1)]},
            {'rolls': {'type': 'minecraft:uniform', 'min': 3, 'max': 5}, 'entries': [
                item(c('chronite_ingot'), 6, 2, 5), item(c('ophanim_eye'), 2), item(c('wind_key'), 3), item(MC + 'diamond', 3, 1, 3),
                item(MC + 'experience_bottle', 4, 3, 8), item(c('gear'), 3, 2, 6), item(MC + 'golden_apple', 2)]}]})
    write_json(os.path.join(DATA, 'loot_table/chests/tick_hall_fork.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/tick_hall_fork'),
        'pools': [{'rolls': 1, 'entries': [item(c('tuning_fork'), 1)]}]})


PUZZLE_STORY = [
    ('clock_dials', c('clock_dial'), 'Связанные часы', 'Выставь сцепленные циферблаты Хранилища времени', 'Linked Clocks',
     'Set the linked dials of the Time Vault'),
    ('tick_walker', c('tick_platform'), 'В такт маятнику', 'Пройди по платформам такта, укротив маятник', 'In Time with the Pendulum',
     'Cross the tick platforms by taming the pendulum'),
    ('rewind_room', c('rewind_anchor'), 'Один оборот', 'Зажги все якоря Комнаты-перемотки за один оборот', 'A Single Turn',
     'Light every anchor of the Rewind Room within one turn'),
]


def story_and_lang():
    names = {}
    for path, icon, ru_t, ru_d, en_t, en_d in PUZZLE_STORY:
        tk, dk = f'advancements.celestial.{path}.title', f'advancements.celestial.{path}.description'
        advancement(path, 'clockwork', icon, {'solved': {'trigger': 'minecraft:impossible'}}, 'goal', tk, dk)
        names[tk] = (ru_t, en_t)
        names[dk] = (ru_d, en_d)
    names.update({
        'block.celestial.clock_dial': ('Сцепленный циферблат', 'Linked Dial'),
        'block.celestial.clock_dial.lore1': ('ПКМ — вперёд на час, крадучись — назад; тянет соседа', 'Use: forward an hour, sneak: back; pulls its neighbour'),
        'block.celestial.tick_platform': ('Платформа такта', 'Tick Platform'),
        'block.celestial.tick_platform.lore1': ('Твёрдая полтакта; точки — фаза волны', 'Solid for half a beat; the dots show its phase'),
        'block.celestial.tick_goal': ('Финиш такта', 'Tick Goal'),
        'block.celestial.tick_goal.lore1': ('Дойди сюда по платформам', 'Reach it along the platforms'),
        'block.celestial.tick_conductor': ('Дирижёр такта', 'Tick Conductor'),
        'block.celestial.rewind_core': ('Ядро перемотки', 'Rewind Core'),
        'block.celestial.rewind_anchor': ('Якорь перемотки', 'Rewind Anchor'),
        'block.celestial.rewind_anchor.lore1': ('ПКМ — зажечь. Перемотка гасит все.', 'Use: light it. A rewind puts them all out.'),
        'puzzle.celestial.clock_dials.fresco': ('Это фреска: нарисованные часы показывают, какой час выставить внизу.', 'This is a fresco: the painted clock shows which hour to set below.'),
        'puzzle.celestial.clock_dials.solved': ('Часы выставлены — механизм стоит, как надо.', 'The clocks are set — the mechanism stands as it should.'),
        'puzzle.celestial.tick_platforms.walk': ('Финиш засчитывается, только если дойти по платформам.', 'The goal only counts if you walk the platforms.'),
        'puzzle.celestial.rewind_room.left': ('До перемотки: %s с', 'Rewind in: %s s'),
        'puzzle.celestial.rewind_room.rewound': ('Комната вернулась к началу оборота.', 'The room has returned to the start of the turn.'),
        'puzzle.celestial.rewind_room.anchors': ('Якорей горит: %s из %s', 'Anchors lit: %s of %s'),
        'puzzle.celestial.rewind_room.solved': ('Перемотка остановлена.', 'The rewind has stopped.'),
        'codex.celestial.puzzle.clock_dials': ('Связанные часы', 'Linked Clocks'),
        'codex.celestial.puzzle.clock_dials.hint': ('поворот циферблата тянет соседа справа (по кругу). Час — на нарисованных часах над каждым (Хранилище времени).',
                                                    'turning a dial pulls its right-hand neighbour (in a ring). The hour is on the fresco above each (Time Vault).'),
        'codex.celestial.puzzle.tick_platforms': ('Ход маятника', 'Pendulum Beat'),
        'codex.celestial.puzzle.tick_platforms.hint': ('платформы держат такт маятников: лёгкий гонит, тяжёлый тянет. Останови один, пусти другой.',
                                                       'the platforms keep the pendulums\' beat: the swift one hurries, the heavy one drags. Stop one, start the other.'),
        'codex.celestial.puzzle.rewind_room': ('Комната-перемотка', 'Rewind Room'),
        'codex.celestial.puzzle.rewind_room.hint': ('каждые 45 с всё возвращается. Три якоря — за один оборот: строй, ломай, спеши.',
                                                    'every 45 s everything returns. Three anchors within one turn: build, break, hurry.'),
        'structure.celestial.time_vault': ('Хранилище времени', 'Time Vault'),
        'codex.celestial.place.time_vault': ('три зала загадок времени: сцепленные часы, ход маятника, комната-перемотка. За каждую — реликварий.',
                                             'three halls of time puzzles: linked clocks, the pendulum beat, the rewind room. A reliquary for each.'),
    })
    lang_patch(names)


def structures():
    jigsaw('time_vault', [c('cog_city'), c('clock_valley')], -5, adaptation='beard_box')
    # размещение — в наборе chrono_minor (gen_chrono_places)
    append_tag('worldgen/structure', 'celestial:codex_places', [c('time_vault')])


def main():
    assets()
    sol = vault()
    loot()
    story_and_lang()
    structures()
    print('ok: загадки времени, Хранилище времени; циферблаты:', sol)


if __name__ == '__main__':
    main()
