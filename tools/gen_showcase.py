#!/usr/bin/env python3
"""Карта-выставка «Celestial Showcase»: все блоки, предметы, существа и постройки мода в плоском мире.
Генерирует build/showcase_cmds.txt (команды для RCON). Запуск: tools/showcase.sh"""
import glob
import json
import os

import nbtlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RES = os.path.join(ROOT, 'src/main/resources')
Y = -60  # уровень пола (верх травы суперплоского мира -61)
lang = json.load(open(f'{RES}/assets/celestial/lang/ru_ru.json', encoding='utf-8'))


def keys(prefix):
    return sorted(k[len(prefix):] for k in lang if k.startswith(prefix) and '.' not in k[len(prefix):])


BLOCKS = keys('block.celestial.')
ITEMS = keys('item.celestial.')
PROJECTILES = {'frost_shard', 'ice_spike', 'light_spear', 'sling_stone', 'star_arrow', 'void_bolt', 'void_ray',
               'memory_human', 'memory_serpent', 'villager', 'sky_ray', 'clock_gear'}
MOBS = [e for e in keys('entity.celestial.') if e not in PROJECTILES]
templates = []
for f in sorted(glob.glob(f'{RES}/data/celestial/structure/*/*.nbt')):
    name = f.split('structure/')[1][:-4]
    size = [int(v) for v in nbtlib.load(f)['size']]
    templates.append((name, size))

out = []
def c(cmd): out.append(cmd)

HUB_TP = 'tp @s 0 %d 8 0 0' % Y
def sign(x, y, z, rot, lines, home=True):
    msgs = [lines[0], lines[1] if len(lines) > 1 else '{text:""}', lines[2] if len(lines) > 2 else '{text:""}',
            '{text:"[ В хаб ]",color:"blue",click_event:{action:"run_command",command:"%s"}}' % HUB_TP if home else '{text:""}']
    c(f'setblock {x} {y} {z} oak_sign[rotation={rot}]{{is_waxed:1b,front_text:{{messages:[{",".join(msgs)}]}}}}')

def tr(key): return '{translate:"%s"}' % key
def txt(t): return '{text:"%s"}' % t

regions = []
def region(x0, z0, x1, z1):
    regions.append((x0, z0, x1, z1))

# ---- настройки мира ----
for g in ('advance_time false', 'advance_weather false', 'spawn_mobs false', 'mob_griefing false', 'fire_spread_radius_around_player 0'):
    c(f'gamerule {g}')
c('time set 6000'); c('weather clear'); c('difficulty peaceful')

# ---- расположение ----
BX, BZ = 40, -100                      # блоки: 20 колонок, шаг 3, ряды через 4
IX, IZ = 130, -40                      # стена предметов
MX, MZ = 200, -100                     # существа
SX, SZ = -300, 100                     # постройки
cols = 20
brows = (len(BLOCKS) + cols - 1) // cols
region(-40, -40, 40, 40)
region(BX - 10, BZ - 10, BX + cols * 3 + 10, BZ + brows * 4 + 10)
region(IX - 10, IZ - 20, IX + 50, IZ + 20)
mrows = (len(MOBS) + 11) // 12
region(MX - 10, MZ - 10, MX + 12 * 9 + 10, MZ + mrows * 10 + 10)

# структуры: ряды шириной до 700
placed = []
x = z = 0; rowh = 0
for name, (sx, sy, sz) in templates:
    if x + sx > 700:
        x = 0; z += rowh + 20; rowh = 0
    placed.append((name, SX + x, SZ + z, sx, sy, sz))
    x += sx + 16; rowh = max(rowh, sz)
region(SX - 10, SZ - 10, SX + 740, SZ + z + rowh + 30)

# forceload плитками по 16x16 чанков
tiles = set()
for x0, z0, x1, z1 in regions:
    for tx in range(x0 // 256, x1 // 256 + 1):
        for tz in range(z0 // 256, z1 // 256 + 1):
            tiles.add((tx, tz))
head = []
for tx, tz in sorted(tiles):
    head.append(f'forceload add {tx*256} {tz*256} {tx*256+255} {tz*256+255}')
head.append('#sleep 60')
out[:0] = []
cmds_setup = list(out); out.clear()

# ---- хаб ----
c(f'fill -20 {Y-1} -20 20 {Y-1} 20 smooth_quartz')
c(f'fill -20 {Y} -20 20 {Y+12} 20 air')
c(f'fill -20 {Y} -20 20 {Y} -20 quartz_bricks'); c(f'fill -20 {Y} 20 20 {Y} 20 quartz_bricks')
c(f'fill -20 {Y} -20 -20 {Y} 20 quartz_bricks'); c(f'fill 20 {Y} -20 20 {Y} 20 quartz_bricks')
c(f'setworldspawn 0 {Y} 0')
sign(0, Y, 3, 0, [txt('CELESTIAL'), txt('Выставка мода'), txt('ПКМ по табличкам')], home=False)
dest = [
    ('Блоки', f'tp @s {BX+30} {Y} {BZ+brows*4+4} 180 0', f'{len(BLOCKS)} шт.'),
    ('Предметы', f'tp @s {IX+20} {Y} {IZ-5} 0 0', f'{len(ITEMS)} шт.'),
    ('Существа', f'tp @s {MX+50} {Y} {MZ+mrows*10+4} 180 0', f'{len(MOBS)} шт.'),
    ('Постройки', f'tp @s {SX+5} {Y} {SZ-12} 0 0', f'{len(templates)} шт.'),
    ('Рай', 'execute in celestial:heaven run tp @s 0 200 0', 'измерение'),
    ('Бездна', 'execute in celestial:abyss run tp @s 600 80 600', 'измерение'),
    ('Ледяные Чертоги', 'execute in celestial:frozen_halls run tp @s 0 199 0', 'измерение'),
    ('Хроноград', 'execute in celestial:chronograd run tp @s 1001 121 992', 'измерение'),
    ('Астрал', 'execute in celestial:astral run tp @s 0.5 100 20.5', 'измерение'),
]
for i, (n, cmd, note) in enumerate(dest):
    sx = -16 + i * 4
    c(f'setblock {sx} {Y} 10 oak_sign[rotation=0]{{is_waxed:1b,front_text:{{messages:[{txt(n)},{txt(note)},{txt("")},'
      f'{{text:"[ Идти ]",color:"dark_green",click_event:{{action:"run_command",command:"{cmd}"}}}}]}}}}')
c('summon minecraft:text_display 0 %d 0 {text:{text:"CELESTIAL",color:"gold",bold:1b},billboard:"center",background:0,transformation:{scale:[3f,3f,3f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}' % (Y + 8))
c(f'summon minecraft:text_display 0 {Y+4} 0 {{text:{{text:"Вернуться из измерения: /execute in minecraft:overworld run tp @s 0 {Y} 8",color:"gray"}},billboard:"center"}}')

# ---- блоки ----
c(f'fill {BX-5} {Y-1} {BZ-5} {BX+cols*3+5} {Y-1} {BZ+brows*4+5} smooth_stone')
c(f'fill {BX-5} {Y} {BZ-5} {BX+cols*3+5} {Y+8} {BZ+brows*4+5} air')
for i, b in enumerate(BLOCKS):
    bx = BX + (i % cols) * 3; bz = BZ + (i // cols) * 4
    c(f'setblock {bx} {Y-1} {bz} celestial:golden_grass')
    c(f'setblock {bx} {Y} {bz} celestial:{b}')
    sign(bx, Y, bz + 1, 0, [tr('block.celestial.' + b), txt(b)], home=False)

# ---- предметы ----
Zw = IZ
c(f'fill {IX-2} {Y-1} {Zw-10} {IX+42} {Y-1} {Zw+10} smooth_stone')
c(f'fill {IX-2} {Y} {Zw-10} {IX+42} {Y+8} {Zw+10} air')
c(f'fill {IX-1} {Y-1} {Zw} {IX+40} {Y+5} {Zw} polished_blackstone_bricks')
for i, it in enumerate(ITEMS):
    face = i // 120                   # 0 - северная грань, 1 - южная
    j = i % 120
    fx = IX + j % 40; fy = Y + j // 40
    fz = Zw - 1 if face == 0 else Zw + 1
    fac = 2 if face == 0 else 3
    c(f'summon minecraft:item_frame {fx} {fy} {fz} {{Facing:{fac}b,Fixed:1b,Invulnerable:1b,Item:{{id:"celestial:{it}",count:1}},'
      f'CustomName:{tr("item.celestial." + it)}}}')
sign(IX + 20, Y, Zw - 5, 8, [txt('Предметы'), txt('наведи на рамку')])
sign(IX + 20, Y, Zw + 5, 0, [txt('Предметы'), txt('наведи на рамку')])

# ---- существа ----
c(f'fill {MX-6} {Y-1} {MZ-6} {MX+12*9+6} {Y-1} {MZ+mrows*10+6} smooth_stone')
c(f'fill {MX-6} {Y} {MZ-6} {MX+12*9+6} {Y+14} {MZ+mrows*10+6} air')
for i, m in enumerate(MOBS):
    mx = MX + (i % 12) * 9 + 4; mz = MZ + (i // 12) * 10 + 4
    c(f'fill {mx-2} {Y-1} {mz-2} {mx+2} {Y-1} {mz+2} polished_andesite')
    c(f'summon celestial:{m} {mx}.5 {Y} {mz}.5 {{NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[0f,0f],'
      f'CustomName:{tr("entity.celestial." + m)},CustomNameVisible:1b}}')

# ---- постройки ----
book_pages = []
for name, px, pz, sx, sy, sz in placed:
    c(f'place template celestial:{name} {px} {Y} {pz}')
    sign(px + sx // 2, Y, pz - 2, 8, [txt(name), txt(f'{sx}x{sy}x{sz}')])
# путеводитель (книга с кликабельными записями) на лекторе в хабе
def entry(name, px, pz, sx):
    return '{text:"%s\\n",click_event:{action:"run_command",command:"tp @s %d %d %d 0 20"}}' % (name, px + sx // 2, Y + 3, pz - 6)
pages = []
for k in range(0, len(placed), 8):
    ents = ','.join(entry(n, px, pz, sx) for n, px, pz, sx, sy, sz in placed[k:k + 8])
    pages.append('{raw:{text:"",extra:[%s]}}' % ents)
c(f'setblock 3 {Y} 3 lectern[facing=south,has_book=true]{{Book:{{id:"minecraft:written_book",count:1,components:{{"minecraft:written_book_content":{{title:{{raw:"Постройки"}},author:"Celestial",pages:[{pages[0]}]}}}}}}}}')
for pg in pages[1:]:  # RCON принимает пакеты до ~1400 байт, страницы добавляются по одной
    c(f'data modify block 3 {Y} 3 Book.components."minecraft:written_book_content".pages append value {pg}')

c('save-all flush')
final = head + cmds_setup + out
os.makedirs(f'{ROOT}/build', exist_ok=True)
open(f'{ROOT}/build/showcase_cmds.txt', 'w', encoding='utf-8').write('\n'.join(final) + '\n')
print(f'блоков {len(BLOCKS)}, предметов {len(ITEMS)}, существ {len(MOBS)}, построек {len(placed)}, команд {len(final)}, плиток {len(tiles)}')
