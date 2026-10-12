"""Акт IV «Часы мироздания» (волна 0.5, O4): Часовщик-Механоид, арена Часовой башни, Шестерня Вечности, главы и дневник.

Текстура Часовщика рисуется по развёртке модели client/render/ClockmakerRenderer.java (texOffs совпадают).
Арена — `celestial:clock_tower/arena`: пол-циферблат со стрелками на «последней минуте», четыре древних маятника на постаментах,
печать-циферблат в центре, камертон у входа. В мир её встроит Часовая башня Хронограда (S4.1/S4.6), сейчас — `/place template`.
"""
import math
import os

from PIL import Image

import mob_textures as M
import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, DATA, c, item_def, model, blockstate, save_png, write_json
from gen_story import advancement, lang_patch
from gen_structures import Template

H = T.hexrgb
WHITE = (255, 255, 255)
BRASS = [H(h) for h in ('#8a5a1c', '#a8722a', '#c48e3a', '#dcaa52')]
DARK = [H(h) for h in ('#3a2a14', '#4a3418', '#2e2210')]
STEEL = [H(h) for h in ('#4a505c', '#5a616e', '#6b7380')]
GOLD_GLOW = (255, 214, 110, 255)


# ---------------------------------------------------------------- Часовщик (128×128)
def clockmaker():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    r = T.rng_for('clockmaker')
    pick = lambda pal: r.choice(pal)  # noqa: E731

    def torso(face, x, y, fw, fh):
        if face == 'front':
            if 4 <= y <= 9 and 3 <= x <= 8:  # окошко с механизмом на груди
                d = math.hypot(x - 5.5, y - 6.5)
                return H('#f0c86e') if d < 1.2 else DARK[0] if (x + y) % 2 else H('#c48e3a')
            if y in (2, 11) or x in (0, fw - 1):
                return H('#5a3410')  # кант
            if (x, y) in ((1, 1), (fw - 2, 1), (1, fh - 2), (fw - 2, fh - 2)):
                return H('#f0c86e')  # заклёпки
        if y == 0:
            return H('#dcaa52')
        return T.shade(pick(BRASS), 0.95 + 0.1 * ((x // 3 + y // 4) % 2))

    def hips(face, x, y, fw, fh):
        return H('#5a3410') if y == 0 else pick(STEEL) if (x + y) % 3 else pick(BRASS)

    def head(face, x, y, fw, fh):
        if face == 'front':
            d = math.hypot(x - 4.5, y - 4.5)
            if d < 4.2:
                if d > 3.4:
                    return H('#5a3410')
                a = math.atan2(y - 4.5, x - 4.5)
                for k in range(12):  # риски часов
                    ka = k * math.pi / 6 - math.pi / 2
                    if abs(math.atan2(math.sin(a - ka), math.cos(a - ka))) < 0.18 and d > 2.4:
                        return H('#3a2a14')
                return H('#f4e6c0')
            return pick(BRASS)
        if face == 'back':
            return pick(DARK)
        return pick(BRASS) if y % 3 else H('#5a3410')

    def hand(face, x, y, fw, fh):
        return H('#7a1a10') if face != 'top' else H('#a02a18')

    def halo(face, x, y, fw, fh):
        if face in ('front', 'back'):
            d = math.hypot(x - 6.5, y - 6.5)
            a = math.atan2(y - 6.5, x - 6.5)
            tooth = math.cos(a * 10) > 0
            if d > 7 or (d > 5.6 and not tooth):
                return None
            if d < 2.6:
                return None  # отверстие — сквозь него видно небо
            return H('#f0c86e') if d > 5.6 else T.shade(H('#dcaa52'), 0.85 if d < 3.4 else 1.0)
        return H('#c48e3a')

    def arm(face, x, y, fw, fh):
        if y in (0, fh - 1):
            return H('#dcaa52')
        return pick(STEEL) if x % 2 else pick(DARK)

    def blade(face, x, y, fw, fh):
        k = y / max(1, fh - 1)
        if k > 0.82:  # наконечник-стрелка
            return H('#f4d27a') if face in ('front', 'back') and abs(x - (fw - 1) / 2) <= (1 - k) * 6 else None
        return T.mix(H('#7a1a10'), H('#c04a28'), k) if face in ('front', 'back') else H('#5a120a')

    def segment(face, x, y, fw, fh):
        return T.shade(pick(BRASS), 1.1 if y == 0 else 0.9)

    def eye(face, x, y, fw, fh):
        if face in ('front', 'back'):
            return H('#1a2a6a') if (x, y) == (0, 0) or (x, y) == (1, 1) else WHITE
        return H('#e8e0c8')

    def rod(face, x, y, fw, fh):
        return H('#dcaa52')

    def bob(face, x, y, fw, fh):
        return H('#f0c86e') if math.hypot(x - 1.5, y - 1.5) < 1.6 else H('#a8722a')

    M.paint_box(img, 0, 0, 12, 14, 7, torso)
    M.paint_box(img, 0, 22, 10, 6, 6, hips)
    M.paint_box(img, 40, 0, 10, 10, 4, head)
    M.paint_box(img, 70, 0, 1, 4, 1, hand)
    M.paint_box(img, 76, 0, 1, 6, 1, hand)
    M.paint_box(img, 40, 16, 14, 14, 1, halo)
    M.paint_box(img, 0, 36, 3, 10, 3, arm)
    M.paint_box(img, 14, 36, 2, 16, 1, blade)
    M.paint_box(img, 0, 56, 3, 5, 3, segment)  # 5.2 → развёртка 5
    M.paint_box(img, 14, 56, 2, 2, 1, eye)
    M.paint_box(img, 24, 36, 1, 8, 1, rod)
    M.paint_box(img, 30, 36, 4, 4, 1, bob)
    # свечение: циферблат (слабо — светлые поля), окошко механизма, очи на ободьях, зубцы нимба
    M.paint_box(glow, 40, 0, 10, 10, 4, lambda f, x, y, fw, fh: (255, 236, 180, 150)
                if f == 'front' and math.hypot(x - 4.5, y - 4.5) < 3.4 else None)
    M.paint_box(glow, 0, 0, 12, 14, 7, lambda f, x, y, fw, fh: GOLD_GLOW if f == 'front' and math.hypot(x - 5.5, y - 6.5) < 1.2 else None)
    M.paint_box(glow, 14, 56, 2, 2, 1, lambda f, x, y, fw, fh: (220, 235, 255, 255) if f in ('front', 'back') else None)
    M.paint_box(glow, 40, 16, 14, 14, 1, lambda f, x, y, fw, fh: GOLD_GLOW
                if f in ('front', 'back') and 5.6 < math.hypot(x - 6.5, y - 6.5) <= 7 and math.cos(math.atan2(y - 6.5, x - 6.5) * 10) > 0 else None)
    return img, glow


def gear_of_eternity():
    """Иконка: золотая шестерня с синим камнем-циферблатом в центре."""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            a = math.atan2(y - 7.5, x - 7.5)
            tooth = math.cos(a * 8) > 0
            if d < 2.6:
                img.putpixel((x, y), (*T.mix(H('#9fd8ff'), H('#2a4aa0'), d / 2.6), 255))
            elif d < 5.0 or (d < 7.3 and tooth):
                light = 0.75 + 0.25 * math.cos(a + 2.3)
                col = T.shade(H('#f0c040'), light) if d < 6.4 else H('#9a6a18')
                img.putpixel((x, y), (*col, 255))
    img.putpixel((7, 5), (255, 255, 255, 255))
    img.putpixel((7, 6), (255, 255, 255, 255))
    return img


# ---------------------------------------------------------------- блоки
def blocks():
    for awakened in (False, True):
        img = Image.new('RGBA', (16, 16))
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                if d < 6.2:
                    col = H('#5a4a30') if awakened else H('#f4e6c0')
                elif d < 7.2:
                    col = H('#8a5a1c')
                else:
                    col = H('#3a2a14')
                img.putpixel((x, y), (*col, 255))
        for k in range(12):
            a = k * math.pi / 6
            img.putpixel((round(7.5 + math.sin(a) * 5.2), round(7.5 - math.cos(a) * 5.2)), (*H('#3a2a14'), 255))
        for i in range(5):  # стрелки на «без одной минуты»
            img.putpixel((7, 7 - i), (*H('#a01a10'), 255))
        for i in range(3):
            img.putpixel((7 - i // 2, 7 - i), (*H('#5a120a'), 255))
        name = 'clock_seal' + ('_awakened' if awakened else '')
        save_png(img, 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/' + name), 'side': c('block/swift_pendulum_side'), 'bottom': c('block/swift_pendulum_side')}})
    blockstate('clock_seal', {'variants': {'awakened=false': {'model': c('block/clock_seal')},
                                           'awakened=true': {'model': c('block/clock_seal_awakened')}}})
    item_def('clock_seal', c('block/clock_seal'))
    append_tag('block', 'minecraft:dragon_immune', [c('clock_seal')])
    append_tag('block', 'minecraft:wither_immune', [c('clock_seal')])


# ---------------------------------------------------------------- арена Часовой башни
R = 14
SIZE = 2 * R + 5
CX = CZ = SIZE // 2
HEIGHT = 24


def arena():
    return arena_template().save('clock_tower/arena')


def arena_template():
    """Зал под куполом Часовой башни (его же вклеивает целая башня — gen_chrono_places.clock_tower)."""
    t = Template(SIZE, HEIGHT, SIZE)
    t.fill(0, 0, 0, SIZE - 1, HEIGHT - 1, SIZE - 1, 'minecraft:air')
    wall, trim, accent = 'minecraft:deepslate_bricks', 'minecraft:waxed_cut_copper', 'minecraft:waxed_chiseled_copper'
    for x in range(SIZE):
        for z in range(SIZE):
            d = math.hypot(x - CX, z - CZ)
            if d > R + 1.8:
                continue
            # пол-циферблат: тёмная плитка, медное кольцо по краю, 12 золотых рисок
            a = math.degrees(math.atan2(x - CX, -(z - CZ))) % 360
            floor = 'minecraft:deepslate_tiles' if d > R - 1.5 else 'minecraft:polished_deepslate'
            if R - 3.2 < d <= R - 1.5:
                floor = trim
            k = round(a / 30) % 12
            near_mark = min(abs(a - k * 30), 360 - abs(a - k * 30))
            if R - 6 < d <= R - 3.2 and near_mark < (5 if k % 3 == 0 else 3) and (d > R - 5 or k % 3 == 0):
                floor = 'minecraft:gold_block'
            t.set(x, 0, z, floor)
            for y in range(1, HEIGHT):
                if y <= 12:
                    outer = R + 1.8
                else:  # купол
                    kq = (y - 12) / (HEIGHT - 12)
                    outer = (R + 1.8) * math.sqrt(max(0.0, 1 - kq * kq))
                inner = outer - 1.6
                if inner <= d <= outer:
                    pil = y <= 12 and round(a) % 30 in (0, 1, 29)
                    blk = trim if (pil or y in (1, 12)) else wall
                    if 5 <= y <= 9 and y <= 12 and 10 <= round(a) % 30 <= 20 and not (150 <= a <= 210):  # окна между пилястрами
                        blk = 'minecraft:yellow_stained_glass'
                    t.set(x, y, z, blk)
    # стрелки на полу: часовая почти на 12, минутная — без одной минуты
    for length, ang, blk in ((6, -2.5, 'minecraft:waxed_copper_block'), (10, -6.0, 'minecraft:gold_block')):
        for i in range(2, length + 1):
            x = round(CX + math.sin(math.radians(ang)) * i)
            z = round(CZ - math.cos(math.radians(ang)) * i)
            t.set(x, 0, z, blk)
    # четыре древних маятника на постаментах по диагоналям
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = round(CX + math.sin(a) * 9), round(CZ - math.cos(a) * 9)
        t.fill(x, 1, z, x, 2, z, 'minecraft:polished_deepslate')
        t.set(x, 3, z, accent)
        t.set(x, 4, z, c('swift_pendulum'), facing=('south', 'west', 'north', 'east')[k], swinging=True, sealed=True,
              nbt={'id': c('pendulum')})
    # стенные шестерни (вращаются всегда — декор вне сети): ряд у северной стены, зацепление чередует ход
    for i in range(-3, 4):
        x, y = CX + i, 8 + (i % 2)
        z = CZ - R + 1
        t.set(x, y, z, c('gear'), axis='z', spin=1 if (i + y) % 2 == 0 else 2)
    # свет: невидимые источники под куполом и фонари на цепях
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        x, z = round(CX + math.sin(a) * 11), round(CZ - math.cos(a) * 11)
        t.set(x, 10, z, 'minecraft:light', level=13)
    for k in range(4):
        a = math.radians(90 * k)
        x, z = round(CX + math.sin(a) * 6), round(CZ - math.cos(a) * 6)
        top = HEIGHT - 6
        t.fill(x, top - 3, z, x, top, z, 'minecraft:iron_chain', axis='y')
        t.set(x, top - 4, z, 'minecraft:copper_lantern', hanging=True)
    # вход с юга: проём 3×4, камертон в сундуке у входа
    for x in range(CX - 1, CX + 2):
        for y in range(1, 5):
            for z in range(CZ + R - 1, CZ + R + 3):
                t.set(x, y, z, 'minecraft:air')
    t.set(CX + 3, 1, CZ + R - 3, 'minecraft:chest', nbt={'id': 'minecraft:chest', 'LootTable': c('chests/clock_arena_fork')},
          facing='north', type='single', waterlogged=False)
    write_json(os.path.join(DATA, 'loot_table/chests/clock_arena_fork.json'), {
        'type': 'minecraft:chest', 'random_sequence': c('chests/clock_arena_fork'),
        'pools': [{'rolls': 1, 'entries': [{'type': 'minecraft:item', 'name': c('tuning_fork')}]}]})
    t.set(CX, 0, CZ, c('clock_seal'), awakened=False, nbt={'id': c('clock_seal')})
    return t


# ---------------------------------------------------------------- сюжет
STORY = [
    ('clockwork', 'crown_of_frost', c('swift_pendulum'),
     {'entered': {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': c('chronograd')}}}, 'goal',
     'Часы мироздания', 'Пройди Часовыми вратами в Хроноград', 'The Clocks of Creation', 'Pass through the Clock Gate into Chronograd'),
    ('gear_of_eternity', 'clockwork', c('gear_of_eternity'),
     {'killed': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                                         'predicate': {'minecraft:entity_type': c('clockmaker')}}}},
      'impossible': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Шестерня Вечности', 'Останови Часовщика-Механоида и запусти время мира', 'Gear of Eternity', 'Stop the Clockwork Mechanoid and set the world\'s time going'),
]
IMPOSSIBLE = {'done': {'trigger': 'minecraft:impossible'}}
SIDE = [
    ('clockmaker_flawless', 'gear_of_eternity', c('gear_of_eternity'), IMPOSSIBLE, 'challenge',
     'Ни секунды на ошибку', 'Победи Часовщика, ни разу не потеряв здоровья', 'Not a Second to Spare', 'Defeat the Clockmaker without losing any health'),
    ('clockmaker_swift', 'gear_of_eternity', c('hourglass'), IMPOSSIBLE, 'challenge',
     'Быстрее времени', 'Победи Часовщика за 9 минут', 'Faster Than Time', 'Defeat the Clockmaker within 9 minutes'),
]

JOURNAL = {
    'task_chrono': ('Иния сказала: часы мироздания стоят в Хронограде, городе Каина. Сложи Часовые врата из хронитовых кирпичей и зажги их осколком Ледяной Короны.',
                    'Inia said the clocks of creation stand still in Chronograd, the city of Cain. Build the Clock Gate from chronite bricks and light it with a shard of the Ice Crown.'),
    'chrono': ('Хроноград. Солнце не движется, медь горит закатом, и всюду тикает — но стрелки стоят.\n\nМастера Каина строили этот город, чтобы «сделать себе имя» и подчинить время. Где-то в сердце города — Часовая башня.',
               'Chronograd. The sun does not move, the copper burns with sunset, and everywhere there is ticking — yet the hands stand still.\n\nCain\'s craftsmen built this city to "make a name" and master time. Somewhere at its heart is the Clock Tower.'),
    'task_clockmaker': ('В Часовой башне на колесе-престоле сидит Часовщик. Говорят, он кричит «Стой!» — и время замирает для всех, кроме него.\n\nКамертон у входа: древние маятники встают от его звона. Пока они качаются, Часовщик переводит стрелки назад.',
                        'In the Clock Tower the Clockmaker sits upon a wheel-throne. They say he cries "Stand still!" and time freezes for all but him.\n\nThere is a tuning fork by the entrance: the ancient pendulums stop at its ring. While they swing, the Clockmaker turns his hands back.'),
    'clockmaker': ('Часовщик остановлен, и часы мира снова идут. На его циферблате было не время — там была звезда на рассвете.\n\nКто держал стрелки на последней минуте до падения? Шестерня Вечности тёплая в руке. Путь ведёт выше, к звёздам.',
                   'The Clockmaker is stopped and the world\'s clocks run again. His face did not show the time — it showed a star at dawn.\n\nWho held the hands at the last minute before the fall? The Gear of Eternity is warm in my hand. The road leads higher, to the stars.'),
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
    tex, glow = clockmaker()
    save_png(tex, 'entity/clockmaker')
    save_png(glow, 'entity/clockmaker_glow')
    save_png(gear_of_eternity(), 'item/gear_of_eternity')
    model('item/gear_of_eternity', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/gear_of_eternity')}})
    item_def('gear_of_eternity', c('item/gear_of_eternity'))
    save_png(M.spawn_egg('#a8722a', '#f4e6c0'), 'item/clockmaker_spawn_egg')
    model('item/clockmaker_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/clockmaker_spawn_egg')}})
    item_def('clockmaker_spawn_egg', c('item/clockmaker_spawn_egg'))
    blocks()
    arena()
    append_tag('entity_type', 'celestial:time_immune', [c('clockmaker')])
    names = story()
    names.update({
        'entity.celestial.clockmaker': ('Часовщик-Механоид', 'Clockwork Mechanoid'),
        'entity.celestial.clock_gear': ('Шестерня Часовщика', 'Clockmaker\'s Gear'),
        'item.celestial.clockmaker_spawn_egg': ('Яйцо призыва: Часовщик-Механоид', 'Clockwork Mechanoid Spawn Egg'),
        'item.celestial.gear_of_eternity': ('Шестерня Вечности', 'Gear of Eternity'),
        'item.celestial.gear_of_eternity.lore1': ('ПКМ: 8 с вокруг тебя время тянется, а ты быстр', 'Use: for 8 s time drags around you while you move swiftly'),
        'item.celestial.gear_of_eternity.lore2': ('Сердце часов Хронограда. Понадобится в конце пути.', 'The heart of Chronograd\'s clocks. It will be needed at the road\'s end.'),
        'block.celestial.clock_seal': ('Циферблат Часовщика', 'Clockmaker\'s Dial'),
        'codex.celestial.mob.clockmaker': ('хранитель хода Хронограда на колесе-престоле. На «Тик… так…» прячься: «Стой!» замораживает всех, кроме него. Древние маятники останавливай Камертоном — иначе он перематывает раны.',
                                           'Keeper of Chronograd\'s time upon a wheel-throne. At "Tick… tock…" take cover: "Stand still!" freezes all but him. Stop the ancient pendulums with a Tuning Fork, or he rewinds his wounds.'),
        'codex.celestial.saga.text.4': ('Акт IV пройден: Часовщик остановлен, время мира снова идёт. На его циферблате горела утренняя звезда.',
                                        'Act IV complete: the Clockmaker is stopped and the world\'s time runs again. A morning star burned on his dial.'),
        'boss.celestial.clockmaker.awaken': ('§6Бьют часы — трижды. Из циферблата поднимается колесо, полное очей: Часовщик проснулся!',
                                             '§6The clock strikes — thrice. A wheel full of eyes rises from the dial: the Clockmaker awakens!'),
        'boss.celestial.clockmaker.subtitle': ('Хранитель последней минуты', 'Keeper of the Last Minute'),
        'boss.celestial.clockmaker.phase1.title': ('Ход', 'The Movement'),
        'boss.celestial.clockmaker.phase2.title': ('Остановка', 'The Stop'),
        'boss.celestial.clockmaker.phase3.title': ('Перемотка', 'The Rewind'),
        'boss.celestial.clockmaker.phase2': ('§6Часовщик поднимает руки-стрелки: «Время принадлежит мне. Услышишь „тик-так“ — замри… или спрячься».',
                                             '§6The Clockmaker raises his hand-blades: "Time is mine. Hear the tick-tock — freeze… or hide."'),
        'boss.celestial.clockmaker.phase3': ('§cКолесо крутится назад, древние маятники снова качаются. «Последняя минута не кончится никогда!»',
                                             '§cThe wheel turns backwards and the ancient pendulums swing again. "The last minute will never end!"'),
        'boss.celestial.clockmaker.tick': ('Тик… так…', 'Tick… tock…'),
        'boss.celestial.clockmaker.stop': ('Стой!', 'Stand still!'),
        'boss.celestial.clockmaker.rewind': ('§6Часовщик переводит стрелки назад — раны затягиваются! Останови маятники Камертоном.',
                                             '§6The Clockmaker turns his hands back — his wounds close! Stop the pendulums with the Tuning Fork.'),
        'boss.celestial.clockmaker.held': ('Маятники держат его время', 'The pendulums hold his time'),
        'story.celestial.act4.title': ('§6Шестерня Вечности', '§6The Gear of Eternity'),
        'story.celestial.act4.subtitle': ('Акт IV «Часы мироздания» пройден', 'Act IV "The Clocks of Creation" complete'),
        'story.celestial.act4.1': ('§6✦ Колесо Часовщика рассыпается искрами, и над Хроноградом впервые за века сдвигается солнце.',
                                   '§6✦ The Clockmaker\'s wheel scatters into sparks, and for the first time in ages the sun moves over Chronograd.'),
        'story.celestial.act4.2': ('§6✦ В твоей руке тёплая Шестерня Вечности. Часы мира идут — и Угасание отступает.',
                                   '§6✦ The Gear of Eternity is warm in your hand. The world\'s clocks run — and the Fading recedes.'),
        'story.celestial.act4.3': ('§8✦ На погасшем циферблате ещё миг светится утренняя звезда… Сага Небес продолжается.',
                                   '§8✦ For a moment a morning star still glows on the dead dial… The Saga of the Heavens goes on.'),
    })
    lang_patch(names)
    print('ok: Акт IV — Часовщик, арена, Шестерня Вечности')


if __name__ == '__main__':
    main()
