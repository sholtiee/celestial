"""Четыре архангела (LORE §4): текстуры 64×128 по развёртке HeavenModels.Archangel, общий светящийся слой, яйцо, переводы и беседы по актам.

Облик: 0 Гавриил (труба), 1 Уриил (пламя), 2 Михаил (меч), 3 Рафаил (посох с рыбой). Атрибуты лежат в нижней половине развёртки (y ≥ 70).
Светящийся слой общий: у каждой вещи свой участок развёртки, видна только вещь своего облика.
"""
from PIL import Image

import mob_textures as M
from gen_assets import c, item_def, model, save_png
from gen_heaven_mobs import HALO, HALO_GLOW, WHITE, halo_box
from gen_story import lang_patch
from textures import hexrgb, mix, rng_for, shade

# имя: (одеяние, отделка, рукава, волосы, ru, en, ru титул, en титул)
ARCHANGELS = {
    'gabriel': ('#eaf1ff', '#6fa6ff', '#cfdcf6', '#f1d27a', 'Гавриил', 'Gabriel', 'вестник', 'the Herald'),
    'uriel': ('#f2b650', '#c0522a', '#e6c070', '#c9632a', 'Уриил', 'Uriel', 'хранитель света', 'Keeper of Light'),
    'michael': ('#dde1ec', '#b8322a', '#a62b25', '#e8e0c8', 'Михаил', 'Michael', 'военачальник', 'the Captain'),
    'raphael': ('#d3ecca', '#4f9a4a', '#a8d0a0', '#8a5a34', 'Рафаил', 'Raphael', 'целитель', 'the Healer'),
}
ORDER = list(ARCHANGELS)
GOLD, SILVER, WOOD = hexrgb('#e8c25a'), hexrgb('#dfe6f2'), hexrgb('#7a5430')


def archangel(index, name):
    robe, trim, sleeve, hair = (hexrgb(h) for h in ARCHANGELS[name][:4])
    skin, eye = hexrgb('#f3d6bd'), hexrgb('#5ab8ff')
    img = Image.new('RGBA', (64, 128), (0, 0, 0, 0))
    glow = Image.new('RGBA', (64, 128), (0, 0, 0, 0))
    r = rng_for('archangel_' + name)

    def cloth(base, x):
        c0 = M.noise_color(r, base, 0.06)
        return shade(c0, 0.88) if x % 3 == 2 else c0

    def head(face, x, y, fw, fh):
        if face in ('top', 'back') or (face in ('left', 'right') and (y < 4 or x >= 5)):
            return M.noise_color(r, hair if (x + y) % 4 else shade(hair, 0.9), 0.06)
        if face == 'front':
            if y < 2 or (y == 2 and x in (0, 7)):
                return M.noise_color(r, hair, 0.06)
            if y == 4 and x in (2, 5):
                return eye
            if y == 4 and x in (1, 6):
                return WHITE
            if y == 6 and 3 <= x <= 4:
                return hexrgb('#d9a08a')
        return M.noise_color(r, skin, 0.03)

    def body(face, x, y, fw, fh):
        if y == 7:
            return trim
        if face == 'front' and fw // 2 - 1 <= x <= fw // 2 and y < 7:
            return trim
        if face == 'top' and 2 <= x <= 5:
            return skin
        return cloth(robe, x)

    def arm(face, x, y, fw, fh):
        if face == 'bottom' or (face != 'top' and y >= fh - 2):
            return M.noise_color(r, skin, 0.03)
        if face != 'top' and y == fh - 3:
            return trim
        return cloth(sleeve, x)

    def skirt(face, x, y, fw, fh):
        if face == 'bottom':
            return shade(robe, 0.6)
        if face != 'top' and y >= fh - 2:
            return trim
        return cloth(robe, x)

    def wing(face, x, y, fw, fh):
        base = mix(WHITE, trim, 0.1)
        if face in ('left', 'right'):
            row = y // 3
            c0 = shade(base, 1.0 - 0.035 * row)
            if y % 3 == 2:
                c0 = shade(c0, 0.86)
            if x >= fw - 3 and y >= fh - 8:
                c0 = mix(c0, trim, 0.4)
            if fh - y <= (x % 3) + 1:
                return None
            return c0
        return shade(base, 0.8)

    M.paint_box(img, 0, 0, 8, 8, 8, head)
    M.paint_box(img, 16, 16, 8, 10, 4, body)
    M.paint_box(img, 40, 16, 3, 11, 3, arm)
    M.paint_box(img, 0, 32, 10, 14, 6, skirt)
    M.paint_box(img, 32, 32, 1, 20, 14, wing)
    halo_box(img, 32, 9, 7, HALO)
    # атрибуты (текстуры всех четырёх — в каждой развёртке; видна вещь своего облика)
    metal = lambda base: (lambda f, x, y, fw, fh: M.noise_color(r, base, 0.05))  # noqa: E731
    M.paint_box(img, 0, 70, 2, 2, 9, metal(GOLD))                       # труба
    M.paint_box(img, 0, 82, 5, 5, 3, lambda f, x, y, fw, fh: shade(GOLD, 1.1 if (x + y) % 2 else 0.9))  # раструб
    M.paint_box(img, 24, 82, 1, 6, 1, metal(WOOD))                      # ручка светильника
    M.paint_box(img, 24, 70, 4, 5, 4, lambda f, x, y, fw, fh: mix(hexrgb('#ff7a2a'), hexrgb('#fff1b8'), 0.2 + 0.6 * (y / max(1, fh))))  # пламя
    M.paint_box(img, 42, 70, 1, 15, 2, lambda f, x, y, fw, fh: SILVER if f in ('front', 'back') and x == 0 else shade(SILVER, 0.82))  # клинок
    M.paint_box(img, 0, 92, 5, 1, 2, metal(GOLD))                       # гарда
    M.paint_box(img, 50, 70, 1, 22, 1, metal(WOOD))                     # посох
    M.paint_box(img, 0, 96, 5, 3, 1, lambda f, x, y, fw, fh: GOLD if (x + y) % 3 else shade(GOLD, 0.8))  # рыба
    # светящийся слой: глаза, нимб, пламя, острие клинка
    halo_box(glow, 32, 9, 7, HALO_GLOW)
    M.paint_box(glow, 0, 0, 8, 8, 8, lambda f, x, y, fw, fh: (*eye, 255) if f == 'front' and y == 4 and x in (2, 5) else None)
    M.paint_box(glow, 24, 70, 4, 5, 4, lambda f, x, y, fw, fh: (*mix(hexrgb('#ff7a2a'), hexrgb('#fff1b8'), 0.2 + 0.6 * (y / max(1, fh))), 255))
    M.paint_box(glow, 42, 70, 1, 15, 2, lambda f, x, y, fw, fh: (255, 255, 255, 255) if f in ('front', 'back') and x == 0 and y % 4 == 0 else None)
    return img, glow


# ---------------------------------------------------------------- беседы: по акту 0..4
TALKS = {
    'gabriel': [
        ('Я Гавриил, вестник. Вестей пока нет: Рай ждёт.', 'I am Gabriel, the herald. There is no word yet: Heaven waits.'),
        ('Свет вернулся в Цитадель, но лишь отчасти. Внизу, под облаками, растёт тьма: ищи Разлом на дне Рая.',
         'Light has returned to the Citadel, but only in part. Below the clouds darkness grows: seek the Rift at the bottom of Heaven.'),
        ('Ты вынес из Бездны Тёмное Ядро. Оно тянется к холоду: за Ледяными вратами замёрзли наши братья.',
         'You carried the Dark Core out of the Abyss. It yearns for cold: beyond the Frost Gate our brothers lie frozen.'),
        ('Иния свободна, Архонт пал. Но время встало в городе, где строили башню до небес. Ищи его.',
         'Inia is free and the Archon has fallen. Yet time has stopped in the city where a tower to heaven was raised. Find it.'),
        ('Остался последний путь, вверх, к звёздам. Там спит тот, кого мы когда-то звали братом.',
         'One road remains: upward, to the stars. There sleeps the one we once called brother.')],
    'uriel': [
        ('Я Уриил, «свет Божий». Огонь кузни честен, если его держат честные руки.',
         'I am Uriel, "light of God". The forge-fire is honest when honest hands hold it.'),
        ('Лучи и зеркала — язык света. Научись говорить на нём: храмы Рая хранят уроки.',
         'Beams and mirrors are the language of light. Learn to speak it: the temples of Heaven keep the lessons.'),
        ('Во тьме свет — это жизнь. Береги фонарь, странник: тьма голодна.',
         'In the dark, light is life. Guard your lantern, wanderer: the dark is hungry.'),
        ('Лёд преломляет свет иначе. Зеркальный лабиринт — моя загадка, и ответа я не дам.',
         'Ice bends light differently. The Mirror Maze is my riddle, and I will not give the answer.'),
        ('Время тоже можно ковать, но осторожно: мастера Хронограда уже обожглись.',
         'Even time can be forged, but carefully: the masters of Chronograd were burned before.')],
    'michael': [
        ('Я Михаил. «Кто как Бог?» — мой вопрос и мой клич.', 'I am Michael. "Who is like God?" is my question and my war-cry.'),
        ('Серафим пал, но он был лишь первым. Испытания Башни закалят тебя перед тем, что ждёт внизу.',
         'The Seraph has fallen, yet he was only the first. The Trials of the Tower will temper you for what waits below.'),
        ('Пожиратель побеждён светом, не силой одного удара. Береги спину, идя на Архонта.',
         'The Devourer was beaten by light, not by one strong blow. Guard your back when you go against the Archon.'),
        ('Ты выстоял против стужи. Против времени оружие бесполезно: нужна точность.',
         'You stood against the frost. Against time a weapon is useless: precision is needed.'),
        ('Последний бой не выиграть одним мечом. Выбирай, ради чего ты держишь клинок.',
         'The last battle is not won by a sword alone. Choose what you hold the blade for.')],
    'raphael': [
        ('Я Рафаил, «исцелил Бог». Я знаю дорогу, даже если ты о ней не спрашивал.',
         'I am Raphael, "God has healed". I know the road even if you did not ask for it.'),
        ('Маяки Рая отзовутся на твой шаг: зажигай их, и дорога станет короче.',
         'The beacons of Heaven will answer your step: kindle them and the road grows shorter.'),
        ('Раны Бездны лечатся светом, а страх — теплом. Флакон звёздного света — мой тебе совет.',
         'The wounds of the Abyss are healed by light and fear by warmth. A flask of starlight is my counsel.'),
        ('Мех и огонь — друзья в Чертогах. Не стыдись согреться: холод не знает гордости.',
         'Fur and fire are friends in the Halls. Be not ashamed to warm yourself: cold knows no pride.'),
        ('Созвездия укажут путь, когда небо станет близким. Я пойду рядом, пока смогу.',
         'The constellations will show the way when the sky draws near. I shall walk beside you for as long as I can.')],
}


def main():
    names = {'entity.celestial.archangel': ('Архангел', 'Archangel')}
    for i, name in enumerate(ORDER):
        tex, glow = archangel(i, name)
        save_png(tex, f'entity/archangel_{name}')
        if i == 0:
            save_png(glow, 'entity/archangel_glow')
            save_png(tex, 'entity/archangel')
        _, _, _, _, ru, en, ru_t, en_t = ARCHANGELS[name]
        names[f'entity.celestial.archangel.{name}'] = (ru, en)
        names[f'entity.celestial.archangel.{name}.title'] = (ru_t, en_t)
        for act, (tru, ten) in enumerate(TALKS[name]):
            names[f'entity.celestial.archangel.{name}.act{act}'] = (tru, ten)
    save_png(M.spawn_egg('#f4ecd2', '#e8c25a'), 'item/archangel_spawn_egg')
    model('item/archangel_spawn_egg', {'parent': 'minecraft:item/generated', 'textures': {'layer0': c('item/archangel_spawn_egg')}})
    item_def('archangel_spawn_egg', c('item/archangel_spawn_egg'))
    names['item.celestial.archangel_spawn_egg'] = ('Яйцо призыва: Архангел', 'Archangel Spawn Egg')
    names['codex.celestial.mob.archangel'] = ('Четыре стража света: Гавриил, Уриил, Михаил и Рафаил. Сходят к алтарю Цитадели, когда свет возвращается; говорят о том, что ждёт дальше.',
                                              'Four guardians of light: Gabriel, Uriel, Michael and Raphael. They descend to the Citadel altar when light returns and speak of what lies ahead.')
    lang_patch(names)
    print('ok: архангелы (4 облика)')


if __name__ == '__main__':
    main()
