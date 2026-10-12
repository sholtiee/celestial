"""Тайная концовка «Имя» (O5 шаг 4c): «следы Эдема» в Верхнем мире — сад с молодым Древом Жизни там, где упал свет.

Шаблон `celestial:eden_trace/garden` (23×20×23, центр (11, 1, 11) — уровень земли): луг, тропинки, ручей, Древо Жизни (ствол с корнями,
ветви, крона кластерами со светом внутри, лианы, плоды жизни), фиговые кусты и цветы. Ставит его код (`story/EdenTraces`) рядом с игроками.
"""
import math
import random

from gen_assets import c
from gen_story import lang_patch
from gen_structures import Template

S, H = 23, 20
CX = CZ = 11


def garden():
    rng = random.Random(9090)
    t = Template(S, H, S)
    t.fill(0, 2, 0, S - 1, H - 1, S - 1, 'minecraft:air')  # уровень земли по углам не трогаем — иначе дыры в рельефе
    for x in range(S):
        for z in range(S):
            d = math.hypot(x - CX, z - CZ)
            if d > 11.3:
                continue
            t.set(x, 0, z, 'minecraft:dirt')
            top = c('golden_grass') if d < 4 + rng.random() * 3 else 'minecraft:grass_block'
            t.set(x, 1, z, top, snowy=False) if top == 'minecraft:grass_block' else t.set(x, 1, z, top)
    for x in range(3, S - 3):  # ручей с востока на запад, тропинка к Древу
        z = round(CZ + 5 + math.sin(x * 0.5) * 1.2)
        if math.hypot(x - CX, z - CZ) < 10.5:
            t.set(x, 1, z, 'minecraft:water', level=0)
    for z in range(CZ + 1, S - 1):
        if t.get(CX, 1, z) != 'minecraft:water':
            t.set(CX, 1, z, 'minecraft:dirt_path')
    wood, leaves, blossom = c('skywood_wood'), c('skywood_leaves'), c('cloud_willow_leaves')

    def line(p0, p1, block):
        n = int(max(abs(p1[i] - p0[i]) for i in range(3)) * 2) + 1
        for i in range(n + 1):
            q = [p0[j] + (p1[j] - p0[j]) * i / n for j in range(3)]
            t.set(round(q[0]), round(q[1]), round(q[2]), block, axis='y')

    def cluster(x0, y0, z0, rx, ry):
        for x in range(int(x0 - rx) - 1, int(x0 + rx) + 2):
            for y in range(int(y0 - ry) - 1, int(y0 + ry) + 2):
                for z in range(int(z0 - rx) - 1, int(z0 + rx) + 2):
                    d = ((x - x0) / rx) ** 2 + ((y - y0) / ry) ** 2 + ((z - z0) / rx) ** 2
                    if d <= 1.0 and rng.random() > 0.08 * (1 + d * 2) and t.get(x, y, z) in (None, 'minecraft:air') and 0 <= y < H:
                        t.set(x, y, z, blossom if rng.random() < 0.2 else leaves, persistent=True, distance=1, waterlogged=False)

    trunk_top = 9
    for y in range(2, trunk_top + 1):  # молодой ствол: тоньше Древа в Саду Начала, тот же изгиб
        rad = 1.6 - 0.8 * (y - 2) / (trunk_top - 2)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if math.hypot(dx, dz) <= rad:
                    t.set(CX + dx, y, CZ + dz, wood, axis='y')
    for i in range(5):
        a = i / 5 * math.tau + 0.3
        line((CX + math.cos(a), 3, CZ + math.sin(a)), (CX + math.cos(a) * 4, 1, CZ + math.sin(a) * 4), wood)
    tips = []
    for i in range(5):
        a = i / 5 * math.tau + 0.8
        start = (CX, 6 + i % 2, CZ)
        tip = (CX + math.cos(a) * 5, 10 + rng.randint(0, 2), CZ + math.sin(a) * 5)
        line(start, tip, wood)
        tips.append(tip)
    cluster(CX, trunk_top + 4, CZ, 4.5, 3.2)
    for x0, y0, z0 in tips:
        cluster(x0, y0 + 1, z0, 3.0, 2.2)
    for x0, y0, z0 in tips + [(CX, trunk_top + 4, CZ)]:
        x, y, z = round(x0), round(y0) + 1, round(z0)
        if t.get(x, y, z) in (leaves, blossom):
            t.set(x, y, z, 'minecraft:light', level=12, waterlogged=False)
    fruits = vines = 0
    for _ in range(300):
        x, z = CX + rng.randint(-7, 7), CZ + rng.randint(-7, 7)
        for y in range(H - 2, 3, -1):
            if t.get(x, y, z) in (leaves, blossom) and t.get(x, y - 1, z) in (None, 'minecraft:air'):
                if fruits < 4 and rng.random() < 0.4:
                    t.set(x, y - 1, z, c('life_fruit'), ripe=True)
                    fruits += 1
                elif vines < 12:
                    n = rng.randint(1, 3)
                    for j in range(1, n + 1):
                        if t.get(x, y - j, z) not in (None, 'minecraft:air'):
                            break
                        t.set(x, y - j, z, c('lumivine'), tip=(j == n))
                    vines += 1
                break
    flowers = ['minecraft:lily_of_the_valley', 'minecraft:oxeye_daisy', 'minecraft:cornflower', 'minecraft:allium', c('fig_bush')]
    for _ in range(70):
        x, z = rng.randrange(1, S - 1), rng.randrange(1, S - 1)
        d = math.hypot(x - CX, z - CZ)
        if 3 < d < 10.8 and t.get(x, 1, z) in ('minecraft:grass_block', c('golden_grass')) and t.get(x, 2, z) in (None, 'minecraft:air'):
            t.set(x, 2, z, rng.choice(flowers))
    return t.save('eden_trace/garden')


def main():
    garden()
    lang_patch({
        'story.celestial.eden_trace': ('✦ Неподалёку, где упал свет, пророс след Эдема (%s, ~%s бл.)', '✦ Nearby, where the light fell, a trace of Eden has taken root (%s, ~%s blocks)'),
        'structure.celestial.eden_trace': ('След Эдема', 'Trace of Eden'),
        'codex.celestial.place.eden_trace': ('сад с молодым Древом Жизни там, куда упал свет после тайной концовки. Плоды жизни растут снова.',
                                             'a garden with a young Tree of Life where the light fell after the secret ending. The fruits of life grow again.'),
    })
    print('ok: следы Эдема')


if __name__ == '__main__':
    main()
