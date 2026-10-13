"""Акт V «Звёздный путь» (волна 0.6, O5 шаг 4a): Безликий, вершина Звёздного алтаря, концовки «Возжечь» и «Поглотить».

Текстура Безликого рисуется по развёртке client/render/FacelessRenderer.java (texOffs совпадают). Вершина — `celestial:star_altar/summit`:
круглая площадка из звёздного камня, семь колонн-труб, кольцо погасших гнёзд, алтарь в центре (будит Безликого при 7+ хорах).
Весь Звёздный алтарь (4 яруса) и его место в Астрале — S5.1.
"""
import math
import os

from PIL import Image

import mob_textures as M
import textures as T
from gen_abyss import append_tag
from gen_assets import ASSETS, c, item_def, model, blockstate, save_png
from gen_story import advancement, lang_patch
from gen_structures import Template

H = T.hexrgb
WHITE = (255, 255, 255)
ROBE = [H(h) for h in ('#0a0814', '#100c1e', '#161028', '#0c0a18')]
VOID = H('#020104')


def faceless():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    r = T.rng_for('faceless')
    pick = lambda pal: r.choice(pal)  # noqa: E731

    def body(face, x, y, fw, fh):
        if face == 'front' and x in (fw // 2 - 1, fw // 2) and y > 2:
            return H('#2a1e44')  # шов балахона
        return pick(ROBE)

    def robe(face, x, y, fw, fh):
        k = y / max(1, fh)
        col = T.mix(pick(ROBE), H('#2a1440'), k * 0.5)
        if y >= fh - 3 and (x + y) % 3 == 0:
            return (*col, 0) if face != 'bottom' else col  # рваный подол
        return col

    def head(face, x, y, fw, fh):
        if face == 'front':
            # пустота под капюшоном: чёрный провал в лиловой кайме
            if 1 <= x <= fw - 2 and 1 <= y <= fh - 1:
                return VOID
            return H('#3a2458')
        return pick(ROBE)

    def tip(face, x, y, fw, fh):
        return pick(ROBE)

    def arm(face, x, y, fw, fh):
        if y >= fh - 3:
            return H('#1a1428') if (x + y) % 2 else H('#2e2448')  # когтистая кисть
        return pick(ROBE)

    def star(face, x, y, fw, fh):
        return T.mix(H('#fff6d0'), H('#ffd24a'), 0.3 if face == 'front' else 0.6)

    def dead_star(face, x, y, fw, fh):
        return T.mix(H('#4a4a5a'), H('#7a7a8a'), r.random() * 0.5)

    def wing(face, x, y, fw, fh):
        if face not in ('front', 'back'):
            return H('#1a1028')
        # силуэт пера-крыла: дуга сверху, рваные маховые перья снизу, заострённые концы (симметрично — развёртка зеркалится)
        u = (x + 0.5) / fw            # 0..1 вдоль крыла
        bulge = math.sin(math.pi * u)  # 0 на концах, 1 посередине
        top = (fh - 1) * (0.5 - 0.48 * bulge)
        feather = 2 if (x % 4) < 2 else 0
        bottom = (fh - 1) * (0.5 + 0.5 * bulge) - feather
        if y < top or y > bottom:
            return None
        if (x * 7 + y * 3) % 13 == 0 and y > (top + bottom) / 2:
            return None  # прорехи
        if y - top < 1 or bottom - y < 1:
            return H('#6a5420')  # тусклая золотая кайма — память о Серафиме
        if x % 4 == 0 and y > (top + bottom) / 2:
            return H('#2a1c40')  # стержни маховых перьев
        return T.shade(H('#1c1230') if (x // 3 + y // 4) % 2 else H('#24183a'), 0.9 + r.random() * 0.2)

    M.paint_box(img, 0, 0, 10, 14, 6, body)
    M.paint_box(img, 0, 20, 12, 22, 8, robe)
    M.paint_box(img, 40, 0, 9, 9, 9, head)
    M.paint_box(img, 76, 0, 6, 3, 6, tip)
    M.paint_box(img, 40, 20, 3, 18, 3, arm)
    M.paint_box(img, 56, 20, 3, 3, 1, star)
    M.paint_box(img, 64, 20, 2, 2, 2, dead_star)
    M.paint_box(img, 0, 64, 24, 16, 1, wing)
    # свечение: кайма пустого лица, утренняя звезда, тусклые погасшие звёзды, золотая кайма крыльев
    M.paint_box(glow, 40, 0, 9, 9, 9, lambda f, x, y, fw, fh: (120, 70, 200, 200) if f == 'front' and (x in (0, fw - 1) or y == 0) else None)
    M.paint_box(glow, 56, 20, 3, 3, 1, lambda f, x, y, fw, fh: (255, 248, 210, 255))
    M.paint_box(glow, 64, 20, 2, 2, 2, lambda f, x, y, fw, fh: (90, 90, 120, 120))
    wing_px = {}
    M.paint_box(Image.new('RGBA', (128, 128)), 0, 64, 24, 16, 1, lambda f, x, y, fw, fh: wing_px.__setitem__((f, x, y), wing(f, x, y, fw, fh)))
    M.paint_box(glow, 0, 64, 24, 16, 1, lambda f, x, y, fw, fh: (150, 120, 50, 150)
                if f in ('front', 'back') and wing_px.get((f, x, y)) == H('#6a5420') else None)
    return img, glow


def altar_blocks():
    for awakened in (False, True):
        img = T.noisy('star_altar', T.pal('#10142e', '#161c3c', '#1c244a'), cell=4, grain=0.2)
        col = H('#5a3a8a') if awakened else H('#d8c8ff')
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - 7.5, y - 7.5)
                a = math.atan2(y - 7.5, x - 7.5)
                if 6.2 <= d < 7.2:
                    img.putpixel((x, y), (*T.shade(col, 0.7), 255))
                ray = abs(math.cos(a * 4)) ** 8
                if d < 1.5 + ray * 4.5:
                    img.putpixel((x, y), (*T.mix(col, WHITE, 0.4 * (1 - d / 6)), 255))
        name = 'star_altar' + ('_awakened' if awakened else '')
        save_png(img, 'block/' + name)
        model('block/' + name, {'parent': 'minecraft:block/cube_bottom_top', 'textures': {
            'top': c('block/' + name), 'side': c('block/star_socket_side'), 'bottom': c('block/star_socket_side')}})
    blockstate('star_altar', {'variants': {'awakened=false': {'model': c('block/star_altar')},
                                           'awakened=true': {'model': c('block/star_altar_awakened')}}})
    item_def('star_altar', c('block/star_altar'))
    append_tag('block', 'minecraft:dragon_immune', [c('star_altar')])
    append_tag('block', 'minecraft:wither_immune', [c('star_altar')])


def summit():
    return summit_template().save('star_altar/summit')


def summit_template():
    """Вершина: площадка R=18 из звёздного камня, кольцо гнёзд, семь колонн-труб с огнями, алтарь в центре.
    Целый Звёздный алтарь (4 яруса + вершина) собирает gen_astral.altar_structure."""
    R = 18
    S = 2 * R + 3
    cx = cz = S // 2
    t = Template(S, 14, S)
    t.fill(0, 0, 0, S - 1, 13, S - 1, 'minecraft:air')
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - cx, z - cz)
            if d <= R + 0.5:
                t.set(x, 1, z, 'minecraft:polished_blackstone' if d > R - 2 or (int(d) % 5 == 0) else 'minecraft:blackstone')
                if d <= R - 3:
                    t.set(x, 0, z, 'minecraft:blackstone')
            if 11.5 <= d < 12.5:
                t.set(x, 2, z, c('star_socket'), filled=False)  # кольцо погасших гнёзд — хоры вокруг престола
    for k in range(7):
        a = k * math.tau / 7
        x, z = round(cx + math.sin(a) * 15), round(cz - math.cos(a) * 15)
        t.fill(x, 2, z, x, 7, z, 'minecraft:polished_blackstone_bricks')
        t.set(x, 8, z, 'minecraft:chiseled_polished_blackstone')
        t.set(x, 9, z, 'minecraft:sea_lantern')
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            t.set(cx + dx, 1, cz + dz, 'minecraft:gilded_blackstone')
    t.set(cx, 2, cz, c('star_altar'), awakened=False, nbt={'id': c('star_altar')})
    return t


REFLECT_R = 15


def reflection(name, floor, rim, deco):
    """Отражение мира для трубы: круглая площадка R=15 (пол на y=1, центр арены — (15, 2, 15)), обод, убранство по миру."""
    S = 2 * REFLECT_R + 1
    c0 = REFLECT_R
    t = Template(S, 16, S)
    t.fill(0, 0, 0, S - 1, 15, S - 1, 'minecraft:air')
    r = T.rng_for('faceless_' + name)
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - c0, z - c0)
            if d <= REFLECT_R + 0.3:
                t.set(x, 1, z, rim if d > REFLECT_R - 1.5 else floor(x, z, d, r))
                if d <= REFLECT_R - 4:
                    t.set(x, 0, z, rim)
    deco(t, c0, r)
    return t.save('faceless/' + name)


def deco_heaven(t, c0, r):
    # Рай: облачные островки, золотая трава, кольцо небесных деревьев-колонн с кронами
    for k in range(6):
        a = k * math.tau / 6
        x, z = round(c0 + math.cos(a) * 11), round(c0 + math.sin(a) * 11)
        t.fill(x, 2, z, x, 6, z, c('skywood_log'), axis='y')
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in (6, 7):
                    if abs(dx) + abs(dz) <= (3 if dy == 6 else 2) and not (dx == 0 and dz == 0 and dy == 6):
                        t.set(x + dx, dy, z + dz, c('skywood_leaves'), persistent=True, distance=1, waterlogged=False)
    for _ in range(14):
        x, z = r.randrange(3, 2 * REFLECT_R - 3), r.randrange(3, 2 * REFLECT_R - 3)
        if math.hypot(x - c0, z - c0) < REFLECT_R - 2:
            t.set(x, 2, z, 'minecraft:fire')  # «горят облака»


def deco_frozen(t, c0, r):
    for k in range(8):  # ледяные шпили по кругу
        a = k * math.tau / 8 + 0.3
        x, z = round(c0 + math.cos(a) * 12), round(c0 + math.sin(a) * 12)
        h = 4 + r.randrange(4)
        t.fill(x, 2, z, x, 1 + h, z, 'minecraft:packed_ice')
        t.set(x, 2 + h, z, 'minecraft:blue_ice')
    for _ in range(40):
        x, z = r.randrange(2 * REFLECT_R + 1), r.randrange(2 * REFLECT_R + 1)
        if math.hypot(x - c0, z - c0) < REFLECT_R - 2:
            t.set(x, 2, z, 'minecraft:snow', layers=1 + r.randrange(2))


def deco_abyss(t, c0, r):
    for k in range(4):  # жаровни Пожирателя — единственный свет
        a = k * math.tau / 4 + math.pi / 4
        x, z = round(c0 + math.cos(a) * 9), round(c0 + math.sin(a) * 9)
        t.set(x, 2, z, 'minecraft:soul_campfire', lit=True, facing='north', signal_fire=False, waterlogged=False)
    for _ in range(18):
        x, z = r.randrange(2 * REFLECT_R + 1), r.randrange(2 * REFLECT_R + 1)
        if 5 < math.hypot(x - c0, z - c0) < REFLECT_R - 2:
            t.set(x, 2, z, c('shadow_crystal'), facing='up', waterlogged=False)


def deco_chrono(t, c0, r):
    for k in range(12):  # риски циферблата
        a = k * math.tau / 12
        for rr in (10, 11):
            t.set(round(c0 + math.sin(a) * rr), 1, round(c0 - math.cos(a) * rr), 'minecraft:gold_block')
    for i in range(2, 9):  # стрелки на «без одной минуты»
        t.set(c0, 1, c0 - i, 'minecraft:gold_block')
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        x, z = round(c0 + math.cos(a) * 12), round(c0 + math.sin(a) * 12)
        t.fill(x, 2, z, x, 3, z, 'minecraft:polished_deepslate')
        t.set(x, 4, z, c('heavy_pendulum'), facing='north', swinging=False, sealed=True, nbt={'id': c('pendulum')})  # стоят: время отражения мёртвое


def reflections():
    reflection('heaven', lambda x, z, d, r: c('golden_grass') if r.random() < 0.7 else c('cloud'), c('skystone_bricks'), deco_heaven)
    reflection('frozen', lambda x, z, d, r: 'minecraft:packed_ice' if r.random() < 0.5 else c('frost_stone'), c('frost_stone_bricks'), deco_frozen)
    reflection('abyss', lambda x, z, d, r: c('abyss_stone') if r.random() < 0.8 else c('abyss_bricks'), c('abyss_bricks'), deco_abyss)
    reflection('chrono', lambda x, z, d, r: 'minecraft:polished_deepslate' if int(d) % 3 else 'minecraft:waxed_cut_copper',
               'minecraft:waxed_cut_copper', deco_chrono)


STORY = [
    ('star_path', 'gear_of_eternity', c('star_stone'),
     {'entered': {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': c('astral')}}}, 'goal',
     'Звёздный путь', 'Войди в Астрал Звёздными вратами', 'The Starry Path', 'Enter the Astral through the Star Gate'),
    ('light_kindled', 'star_path', c('halo'), {'done': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Возжечь свет', 'Отдай свет миру: Угасание кончилось навсегда', 'Kindle the Light', 'Give the light to the world: the Fading is over for good'),
    ('light_consumed', 'star_path', c('seraph_wings'), {'done': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Поглотить свет', 'Возьми свет себе и стань новым Серафимом', 'Consume the Light', 'Take the light for yourself and become the new Seraph'),
]
IMPOSSIBLE = {'done': {'trigger': 'minecraft:impossible'}}
STORY.append(('true_name', 'star_path', c('star_disk'), IMPOSSIBLE, 'challenge',
              'Имя', 'Назови Безликого его прежним именем и выдержи, пока свет возвращается к нему',
              'The Name', 'Speak the Faceless\' former name and endure while the light returns to him'))
SIDE = [
    ('faceless_flawless', 'star_path', c('star_stone'), IMPOSSIBLE, 'challenge',
     'Свет без тени', 'Победи Безликого, ни разу не потеряв здоровья', 'Light Without Shadow', 'Defeat the Faceless without losing any health'),
    ('faceless_swift', 'star_path', c('gear_of_eternity'), IMPOSSIBLE, 'challenge',
     'Семь труб за миг', 'Победи Безликого за 12 минут', 'Seven Trumpets in a Breath', 'Defeat the Faceless within 12 minutes'),
]
JOURNAL = {
    'task_astral': ('Шестерня Вечности тёплая и тянет вверх, к звёздам. Сложи Звёздные врата и зажги их Шестернёй — там, в сердце неба, спит Безликий.',
                    'The Gear of Eternity is warm and pulls upward, toward the stars. Build the Star Gate and light it with the Gear — there, in the heart of the sky, the Faceless sleeps.'),
    'astral': ('Астрал. Тяжесть почти ушла: прыжок — и плывёшь. Созвездия здесь — не рисунки, а следы хоров, что пели когда-то.\n\nСобери хоры на Звёздных дисках. Когда соберёшь семь, Звёздный алтарь пропустит к нему.',
               'The Astral. Weight is nearly gone: one jump and you float. The constellations here are not pictures but traces of choirs that once sang.\n\nGather the choirs at the Star Disks. With seven, the Star Altar will let you through to him.'),
    'task_faceless': ('На вершине алтаря — Безликий. Говорят, он трубит семь раз, и с каждым разом берёт силу тех, кого я победил.\n\nОн не умрёт. Когда упадёт на колени, решать мне.',
                      'At the top of the altar is the Faceless. They say he sounds seven trumpets, and each time takes the strength of those I defeated.\n\nHe will not die. When he falls to his knees, the choice is mine.'),
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


TRUMPETS = [
    ('Град и огонь', 'Hail and Fire', 'Первая труба: с неба — град и огонь. Смотри на метки под ногами!',
     'The first trumpet: hail and fire from the sky. Watch the marks at your feet!'),
    ('Гора огненная в море', 'A Burning Mountain', 'Вторая труба: лёд Архонта рвётся из-под ног.', 'The second trumpet: the Archon\'s ice bursts from beneath you.'),
    ('Звезда Полынь', 'The Star Wormwood', 'Третья труба: падает звезда Полынь — где она упала, воздух горек.',
     'The third trumpet: the star Wormwood falls — where it lands, the air is bitter.'),
    ('Померкли светила', 'The Lights Darken', 'Четвёртая труба: треть светил померкла. Он прячется во тьме — жди, когда проступит.',
     'The fourth trumpet: a third of the lights go dark. He hides in the dark — wait for him to show.'),
    ('Саранча из бездны', 'Locusts from the Abyss', 'Пятая труба: из бездны выходит саранча — слепые охотники.',
     'The fifth trumpet: locusts come out of the abyss — blind hunters.'),
    ('Ангелы Евфрата', 'The Angels of the Euphrates', 'Шестая труба: «Тик… так…» — и время встанет. Не стой у него на пути.',
     'The sixth trumpet: "Tick… tock…" — and time will stop. Do not stand in his path.'),
    ('Седьмая труба', 'The Seventh Trumpet', 'Седьмая труба. Сквозь тьму на его груди проступает утренняя звезда…',
     'The seventh trumpet. Through the darkness on his chest a morning star appears…'),
]


def main():
    tex, glow = faceless()
    save_png(tex, 'entity/faceless')
    save_png(glow, 'entity/faceless_glow')
    save_png(M.spawn_egg('#0a0814', '#d8c8ff'), 'item/faceless_spawn_egg')
    model('item/faceless_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/faceless_spawn_egg')}})
    item_def('faceless_spawn_egg', c('item/faceless_spawn_egg'))
    altar_blocks()
    summit()
    reflections()
    append_tag('entity_type', 'celestial:time_immune', [c('faceless')])
    e = story()
    for i, (ru_t, en_t, ru, en) in enumerate(TRUMPETS, 1):
        e[f'boss.celestial.faceless.phase{i}.title'] = (ru_t, en_t)
        e[f'boss.celestial.faceless.trumpet{i}'] = ('§d' + ru, '§d' + en)
    e.update({
        'entity.celestial.faceless': ('Безликий', 'The Faceless'),
        'boss.celestial.faceless.reflection.heaven': ('§dМир вокруг становится отражением Рая — и облака горят.', '§dThe world around becomes a reflection of Heaven — and the clouds burn.'),
        'boss.celestial.faceless.reflection.frozen': ('§dВокруг — отражение Ледяных Чертогов: лёд помнит Архонта.', '§dAround you — a reflection of the Frozen Halls: the ice remembers the Archon.'),
        'boss.celestial.faceless.reflection.abyss': ('§dВокруг — отражение Бездны. Свет — только у жаровен.', '§dAround you — a reflection of the Abyss. The only light is at the braziers.'),
        'boss.celestial.faceless.reflection.chrono': ('§dВокруг — отражение Хронограда: часы стоят на последней минуте.', '§dAround you — a reflection of Chronograd: the clocks stand at the last minute.'),
        'entity.celestial.void_bolt': ('Сгусток пустоты', 'Void Bolt'),
        'item.celestial.faceless_spawn_egg': ('Яйцо призыва: Безликий', 'Faceless Spawn Egg'),
        'block.celestial.star_altar': ('Звёздный алтарь', 'Star Altar'),
        'block.celestial.star_altar.silent': ('Хоры молчат: собрано %s из %s', 'The choirs are silent: %s of %s gathered'),
        'codex.celestial.mob.faceless': ('тот, кто ест свет, потому что больше не может светить сам. Семь труб — семь бед: град, лёд, Полынь, тьма, саранча, остановленное время и всё сразу. Умереть он не может.',
                                         'the one who eats light because he can no longer shine himself. Seven trumpets, seven woes: hail, ice, Wormwood, darkness, locusts, stopped time and all at once. He cannot die.'),
        'codex.celestial.saga.text.5': ('Акт V пройден: Безликий повергнут, и выбор сделан. Сага Небес окончена — но звёзды помнят.',
                                        'Act V complete: the Faceless is laid low and the choice is made. The Saga of the Heavens is over — but the stars remember.'),
        'boss.celestial.faceless.awaken': ('§5Звёзды над алтарём гаснут одна за другой. Из темноты встаёт фигура без лица.',
                                           '§5The stars above the altar go out one by one. A faceless figure rises from the dark.'),
        'boss.celestial.faceless.subtitle': ('Тот, кто потерял имя', 'The One Who Lost His Name'),
        'boss.celestial.faceless.defeated': ('Безликий повержен', 'The Faceless, Laid Low'),
        'boss.celestial.faceless.kneels': ('§fБезликий опускается на колени у алтаря. Тьма стекает с него, и на груди горит утренняя звезда. Подойди и коснись его — выбор за тобой.',
                                           '§fThe Faceless sinks to his knees by the altar. The darkness runs off him, and a morning star burns on his chest. Approach and touch him — the choice is yours.'),
        'boss.celestial.faceless.kneels_title': ('Он на коленях', 'He Kneels'),
        'boss.celestial.faceless.kneels_sub': ('Коснись его и выбери', 'Touch him and choose'),
        'ending.celestial.screen.title': ('Свет в твоих руках', 'The Light Is in Your Hands'),
        'ending.celestial.screen.text': ('«Я светил ярче всех, — шепчет он. — Потом потерял имя и стал есть чужой свет. Теперь он у тебя. Что ты с ним сделаешь?»',
                                         '"I shone brighter than all," he whispers. "Then I lost my name and began to eat the light of others. Now it is yours. What will you do with it?"'),
        'ending.celestial.choice.kindle': ('Возжечь — отдать свет миру', 'Kindle — give the light to the world'),
        'ending.celestial.choice.kindle.desc': ('Угасание кончится навсегда, ты станешь Хранителем света.', 'The Fading ends for good; you become the Keeper of the light.'),
        'ending.celestial.choice.consume': ('Поглотить — взять свет себе', 'Consume — take the light for yourself'),
        'ending.celestial.choice.consume.desc': ('Ты станешь новым Серафимом, но над землёй встанет вечная ночь.', 'You become the new Seraph, but eternal night falls over the land.'),
        'ending.celestial.choice.name': ('Назвать его имя', 'Speak his name'),
        'ending.celestial.choice.name.desc': ('Ты знаешь, кем он был. Скажи ему.', 'You know who he was. Tell him.'),
        'lore.celestial.letter': ('✦ %s полна — в ней проступает буква: %s', '✦ %s is complete — a letter shows through it: %s'),
        **{f'letter.celestial.{i}': (ru, en) for i, (ru, en) in enumerate(zip('ДЕННИЦА', 'LUCIFER'), 1)},
        'ending.celestial.name.locked': ('Чтобы назвать его, нужна вся Летопись: по букве из каждой из семи книг.', 'To name him you need the whole Chronicle: a letter from each of the seven books.'),
        'ending.celestial.name.wrong': ('§7Он не откликается. Это не его имя.', '§7He does not answer. That is not his name.'),
        'ending.celestial.name.screen': ('Его прежнее имя', 'His Former Name'),
        'ending.celestial.name.screen_text': ('Семь книг Летописи — семь букв. Сложи их в имя того, кто светил ярче всех, пока не потерял себя.',
                                              'Seven books of the Chronicle — seven letters. Put them together into the name of the one who shone brightest before he lost himself.'),
        'ending.celestial.name.clear': ('Стереть', 'Clear'),
        'ending.celestial.name.speak': ('Назвать', 'Speak'),
        'ending.celestial.name.spoken': ('§6%s произносит имя. Безликий вздрагивает и медленно поднимает голову…', '§6%s speaks the name. The Faceless shudders and slowly lifts his head…'),
        'ending.celestial.name.hold': ('Выдержи', 'Endure'),
        'ending.celestial.name.hold_sub': ('Тьма отрывается от него. Свет возвращается — минуту', 'The darkness tears away from him. The light returns — for a minute'),
        'boss.celestial.faceless.naming': ('Свет возвращается к нему', 'The Light Returns to Him'),
        'ending.celestial.name.title': ('Денница', 'Lucifer'),
        'ending.celestial.name.subtitle': ('Он вспомнил своё имя', 'He remembers his name'),
        'ending.celestial.name.1': ('§f✦ Последняя тень падает с него, и под капюшоном — лицо. Свет, который он ел, снова его собственный.',
                                    '§f✦ The last shadow falls from him, and beneath the hood there is a face. The light he ate is his own again.'),
        'ending.celestial.name.2': ('§f✦ «Утренняя звезда, сын зари… Так меня звали, — говорит он. — Я забыл. Ты помнил за меня».',
                                    '§f✦ "Morning star, son of the dawn… That was my name," he says. "I forgot. You remembered for me."'),
        'ending.celestial.name.3': ('§f✦ Он поднимается выше алтаря и светит — не забирая, а отдавая. Угасание не просто кончилось: оно пошло вспять.',
                                    '§f✦ He rises above the altar and shines — not taking, but giving. The Fading has not merely ended: it has turned back.'),
        'ending.celestial.name.4': ('§f✦ Внизу, на земле, там, где упал свет, прорастают следы Эдема.', '§f✦ Down below, on the earth, where the light fell, traces of Eden take root.'),
        'ending.celestial.name.5': ('§6✦ Сага Небес окончена. Летопись полна — и в ней теперь есть и твоё имя.', '§6✦ The Saga of the Heavens is over. The Chronicle is full — and your name is in it now.'),
        'ending.celestial.kindle.title': ('Свет возжжён', 'The Light Is Kindled'),
        'ending.celestial.kindle.subtitle': ('Угасание кончилось', 'The Fading is over'),
        'ending.celestial.kindle.1': ('§6✦ Ты поднимаешь свет — и отпускаешь. Он уходит вниз, сквозь облака, к земле.', '§6✦ You raise the light — and let it go. It falls, through the clouds, to the earth.'),
        'ending.celestial.kindle.2': ('§6✦ Безликий растворяется в сиянии: его голод кончился вместе с Угасанием.', '§6✦ The Faceless dissolves into the radiance: his hunger ends with the Fading.'),
        'ending.celestial.kindle.3': ('§6✦ Ночи снова коротки, а Рай сияет. Ты — Хранитель света.', '§6✦ The nights are short again and Heaven shines. You are the Keeper of the light.'),
        'ending.celestial.kindle.4': ('§8✦ Сага Небес окончена. Но среди звёзд одна всё ещё ждёт своего имени…', '§8✦ The Saga of the Heavens is over. Yet among the stars one still waits for its name…'),
        'ending.celestial.consume.title': ('Свет поглощён', 'The Light Is Consumed'),
        'ending.celestial.consume.subtitle': ('Ты — новый Серафим', 'You are the new Seraph'),
        'ending.celestial.consume.1': ('§5✦ Свет входит в тебя, и за спиной раскрываются шесть крыльев.', '§5✦ The light enters you, and six wings open behind your back.'),
        'ending.celestial.consume.2': ('§5✦ Безликий смеётся тихо, как старый друг, и уходит во тьму.', '§5✦ The Faceless laughs softly, like an old friend, and goes into the dark.'),
        'ending.celestial.consume.3': ('§5✦ Над землёй встаёт ночь — и больше не кончается. Звёзды светят только тебе.', '§5✦ Night rises over the land — and never ends. The stars shine for you alone.'),
        'ending.celestial.consume.4': ('§8✦ Сага Небес окончена. Был ли он когда-то таким же, как ты?', '§8✦ The Saga of the Heavens is over. Was he once just like you?'),
    })
    lang_patch(e)
    print('ok: Акт V — Безликий, вершина алтаря, концовки')


if __name__ == '__main__':
    main()
