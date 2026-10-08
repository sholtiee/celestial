"""Переделка Серафима (волна 0.2, шаг 10): тёмные крылья, золотые кристаллы света, реплики боя, субтитры звуков."""
import colorsys
import os
import random

from PIL import Image

from gen_assets import ASSETS, save_png
from gen_story import lang_patch

VANILLA = os.path.join(os.path.dirname(__file__), '..', '.mcsrc', 'assets', 'assets', 'minecraft', 'textures')


def recolor(img, hue, light_mul, sat_add, keep_bright=0.0):
    img = img.convert('RGBA')
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if l > 1 - keep_bright:  # самые яркие пиксели (блики) оставляем светлыми
                nl = l
            else:
                nl = l * light_mul
            nr, ng, nb = colorsys.hls_to_rgb(hue, nl, min(1, s + sat_add))
            px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return img


def crystal_texture(mask):
    """Кристалл света: от ванильной развёртки — только форма, рисунок свой: золотое стекло с гранями и бликами."""
    rng = random.Random(91)
    img = Image.new('RGBA', mask.size, (0, 0, 0, 0))
    mp, px = mask.load(), img.load()
    golds = [(201, 162, 58), (239, 209, 120), (255, 243, 198), (176, 128, 40)]
    for y in range(mask.height):
        for x in range(mask.width):
            a = mp[x, y][3]
            if a == 0:
                continue
            facet = ((x // 4) + (y // 4)) % 3
            c = golds[facet] if rng.random() > 0.08 else golds[2]
            if x % 4 == 0 or y % 4 == 0:
                c = golds[3]
            px[x, y] = (*c, a)
    return img


def main():
    wings = Image.open(os.path.join(ASSETS, 'textures/entity/equipment/wings/seraph_wings.png'))
    dark = recolor(wings, 0.75, 0.3, 0.3)  # почти чёрные перья с фиолетовым отливом
    px = dark.load()
    for y in range(dark.height):  # золотая кромка по нижнему краю каждого пера
        for x in range(dark.width):
            if px[x, y][3] and (y + 1 >= dark.height or px[x, y + 1][3] == 0):
                px[x, y] = (201, 162, 58, 255)
    save_png(dark, 'entity/fallen_seraph_wings')
    src = os.path.join(VANILLA, 'entity', 'end_crystal', 'end_crystal.png')
    if os.path.exists(src):
        save_png(crystal_texture(Image.open(src).convert('RGBA')), 'entity/seraph_crystal')
    else:
        print('  нет', src, '— текстура кристалла не обновлена')
    lang_patch({
        'entity.celestial.seraph_crystal': ('Кристалл света', 'Light Crystal'),
        'boss.celestial.fallen_seraph.crystals': ('§eНад ареной вспыхивают Кристаллы света и питают Серафима! Разбей их — пока они целы, он почти неуязвим.',
                                                  '§eLight Crystals flare above the arena and feed the Seraph! Shatter them: while they stand he is nearly invulnerable.'),
        'boss.celestial.fallen_seraph.crystals_gone': ('§aПоследний кристалл разбит — Серафим больше не исцеляется!', '§aThe last crystal shatters: the Seraph no longer heals!'),
        'boss.celestial.fallen_seraph.shockwave': ('§c⚠ Свет собирается под Серафимом — прыгай!', '§c⚠ Light gathers beneath the Seraph — jump!'),
        'subtitles.celestial.wing_flap': ('Взмах крыльев', 'Wings flap'),
        'subtitles.celestial.spell_cast': ('Звучит заклинание', 'Spell cast'),
        'subtitles.celestial.light_bolt': ('Разряд света', 'Light bolt'),
        'subtitles.celestial.meteor_whoosh': ('Свист падающей звезды', 'Falling star whooshes'),
        'subtitles.celestial.meteor_impact': ('Удар метеорита', 'Meteorite impact'),
        'subtitles.celestial.shadow_ambient': ('Шёпот Тени', 'Shadow whispers'),
        'subtitles.celestial.shadow_blink': ('Тень перетекает', 'Shadow slips'),
        'subtitles.celestial.crystal_break': ('Кристалл разбит', 'Crystal shatters'),
        'subtitles.celestial.seraph_roar': ('Серафим ревёт', 'Seraph roars'),
        'subtitles.celestial.fading_grow': ('Свет мира тускнеет', 'The world\'s light dims'),
        'subtitles.celestial.trial_start': ('Испытание начинается', 'Trial begins'),
        'subtitles.celestial.devourer_roar': ('Пожиратель Света ревёт', 'Light Devourer roars'),
        'subtitles.celestial.hunter_screech': ('Слепой охотник визжит', 'Blind Hunter shrieks'),
        'subtitles.celestial.light_eater_feed': ('Светоед глотает свет', 'Light Eater devours light'),
        'subtitles.celestial.worm_bite': ('Глубинный червь кусает', 'Deep Worm bites'),
        # постановка битв (boss/BossIntro): титр при пробуждении и названия фаз
        'boss.celestial.phase': ('Фаза %s', 'Phase %s'),
        'boss.celestial.fallen_seraph.subtitle': ('Былой страж Небесного Престола', 'Once the Warden of the Heavenly Throne'),
        'boss.celestial.fallen_seraph.phase2.title': ('Дождь копий', 'Rain of Spears'),
        'boss.celestial.fallen_seraph.phase3.title': ('Ярость падшего', 'Wrath of the Fallen'),
        'boss.celestial.light_devourer.phase2.title': ('Голод тьмы', 'Hunger of the Dark'),
        'boss.celestial.light_devourer.phase3.title': ('Ни искры света', 'Not a Spark Left'),
        'boss.celestial.frost_archon.phase2.title': ('Метель', 'Blizzard'),
        'boss.celestial.frost_archon.phase3.title': ('Ледяная тюрьма', 'Ice Prison'),
    })
    print('ok: Серафим и звуки')


if __name__ == '__main__':
    main()
