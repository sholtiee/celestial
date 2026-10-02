"""Процедурные пиксель-арт текстуры Celestial (все рисуются кодом с нуля)."""
import hashlib
import math
import random

from PIL import Image


def rng_for(name):
    return random.Random(int(hashlib.md5(name.encode()).hexdigest()[:8], 16))


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def value_noise(r, size=16, cell=4):
    """Плавный периодический шум (тайлится без швов)."""
    n = size // cell
    grid = [[r.random() for _ in range(n)] for _ in range(n)]
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            gx, gy = x / cell, y / cell
            x0, y0 = int(gx) % n, int(gy) % n
            x1, y1 = (x0 + 1) % n, (y0 + 1) % n
            tx, ty = gx - int(gx), gy - int(gy)
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = grid[y0][x0] + (grid[y0][x1] - grid[y0][x0]) * tx
            b = grid[y1][x0] + (grid[y1][x1] - grid[y1][x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


def noisy(name, palette, cell=4, grain=0.35, alpha=255):
    """Текстура из палитры (от тёмного к светлому) по шуму + зерно."""
    r = rng_for(name)
    nz = value_noise(r, 16, cell)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            v = nz[y][x] * (1 - grain) + r.random() * grain
            idx = min(len(palette) - 1, int(v * len(palette)))
            img.putpixel((x, y), (*palette[idx], alpha))
    return img


def pal(*hexes):
    return [hexrgb(h) for h in hexes]


# ---------- Палитры ----------
DIRT = pal('#a08a63', '#b59d72', '#c7b083', '#d6c196')
GOLD_GRASS = pal('#c99a22', '#ddb233', '#ecc84a', '#f6dc70', '#fff09a')
SKYSTONE = pal('#9aa6b8', '#adb8c8', '#bfc9d6', '#d0d8e3', '#e1e7ef')
RADIANT = pal('#e8b94a', '#f3cf6a', '#fde48f', '#fff4c4', '#ffffff')
BARK = pal('#b7b2a6', '#cbc6ba', '#dcd8ce', '#ece9e2', '#f7f5f0')
PLANKS = pal('#d8c9a8', '#e3d6b8', '#ecdfc4', '#f4ead3')
LEAVES = pal('#d99a1a', '#eab52b', '#f5cb46', '#ffe073', '#fff2a8')
CLOUD = pal('#dfe8f2', '#eaf0f7', '#f3f7fb', '#ffffff')
GOLD_CLOUD = pal('#f2c94c', '#f7d76b', '#fbe590', '#fff3bf')
RAIN_CLOUD = pal('#7f8a99', '#8f9aa8', '#a1abb8', '#b4bdc8')
ETHERITE = pal('#1f8fa8', '#2fb5cc', '#52d3e3', '#8cecf3', '#d4fbff')
STARQ = pal('#f5e6a8', '#fff3c6', '#ffffff')


def dirt():
    return noisy('heaven_dirt', DIRT, cell=4, grain=0.5)


def golden_grass_top():
    return noisy('golden_grass_top', GOLD_GRASS, cell=4, grain=0.55)


def golden_grass_side():
    img = dirt()
    r = rng_for('golden_grass_side')
    top = golden_grass_top()
    for x in range(16):
        depth = 3 + r.choice([0, 0, 1, 1, 2])
        for y in range(depth):
            img.putpixel((x, y), top.getpixel((x, y)))
    return img


def skystone():
    img = noisy('skystone', SKYSTONE, cell=4, grain=0.4)
    r = rng_for('skystone_cracks')
    for _ in range(3):  # лёгкие трещинки
        x, y = r.randrange(16), r.randrange(16)
        for _ in range(r.randint(2, 4)):
            img.putpixel((x % 16, y % 16), (*SKYSTONE[0], 255))
            x += r.choice([-1, 0, 1]); y += 1
    return img


def bricks(base_name, palette, mortar):
    img = noisy(base_name, palette, cell=2, grain=0.5)
    m = hexrgb(mortar)
    for y in range(16):
        for x in range(16):
            row = y // 4
            off = 4 if row % 2 else 0
            if y % 4 == 3 or (x + off) % 8 == 7:
                img.putpixel((x, y), (*m, 255))
            elif y % 4 == 0:
                c = img.getpixel((x, y))
                img.putpixel((x, y), (*shade(c, 1.08), 255))
    return img


def radiant_stone():
    img = noisy('radiant', RADIANT[:3], cell=4, grain=0.3)
    r = rng_for('radiant_veins')
    for _ in range(5):
        x, y = r.randrange(16), r.randrange(16)
        for _ in range(r.randint(3, 6)):
            img.putpixel((x % 16, y % 16), (*RADIANT[4], 255))
            nx = (x + r.choice([-1, 1])) % 16
            img.putpixel((nx, y % 16), (*RADIANT[3], 255))
            x += r.choice([-1, 0, 1]); y += r.choice([0, 1])
    return img


def log_side():
    r = rng_for('skywood_log')
    img = Image.new('RGBA', (16, 16))
    cols = [r.random() for _ in range(16)]
    for y in range(16):
        for x in range(16):
            v = cols[x] * 0.6 + r.random() * 0.4
            if r.random() < 0.06:
                v = 0
            img.putpixel((x, y), (*BARK[min(4, int(v * 5))], 255))
    # золотые прожилки — отличительная черта небесного дерева
    for _ in range(3):
        x = r.randrange(16)
        y0 = r.randrange(16)
        for d in range(r.randint(3, 6)):
            img.putpixel((x, (y0 + d) % 16), (*hexrgb('#f0c85a'), 255))
    return img


def log_top():
    img = Image.new('RGBA', (16, 16))
    bark = log_side()
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            d = math.sqrt(dx * dx + dy * dy)
            if d > 6.8:
                img.putpixel((x, y), bark.getpixel((x, y)))
            else:
                ring = int(d) % 3
                img.putpixel((x, y), (*PLANKS[[3, 1, 2][ring]], 255))
    return img


def planks():
    r = rng_for('skywood_planks')
    img = noisy('skywood_planks', PLANKS, cell=2, grain=0.6)
    for y in range(16):
        for x in range(16):
            if y % 4 == 3:
                img.putpixel((x, y), (*shade(PLANKS[0], 0.9), 255))
    for row in range(4):
        x = r.randrange(16)
        for y in range(row * 4, row * 4 + 3):
            img.putpixel((x, y), (*shade(PLANKS[0], 0.92), 255))
    return img


def leaves():
    r = rng_for('skywood_leaves')
    img = noisy('skywood_leaves', LEAVES, cell=2, grain=0.6)
    for y in range(16):
        for x in range(16):
            if r.random() < 0.13:
                img.putpixel((x, y), (0, 0, 0, 0))
    return img


def cloud(name, palette, alpha):
    return noisy(name, palette, cell=8, grain=0.2, alpha=alpha)


def ore(name, specks, count=6):
    img = skystone()
    r = rng_for(name)
    for _ in range(count):
        cx, cy = r.randrange(2, 14), r.randrange(2, 14)
        shape = [(0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)]
        for i, (dx, dy) in enumerate(shape[:r.randint(3, 6)]):
            c = specks[min(len(specks) - 1, i % len(specks))]
            img.putpixel((cx + dx, cy + dy), (*c, 255))
    return img


def metal_block(palette):
    img = Image.new('RGBA', (16, 16))
    r = rng_for('etherite_block')
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                c = palette[0]
            elif x == 1 or y == 1:
                c = palette[4]
            else:
                v = 0.55 + 0.25 * math.sin((x + y) * 0.5) + r.random() * 0.15
                c = palette[min(4, max(1, int(v * 5)))]
            img.putpixel((x, y), (*c, 255))
    return img


# ---------- Спрайты по ASCII-маскам ----------
def sprite(rows, colors):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row.ljust(16, '.')[:16]):
            if ch in colors:
                img.putpixel((x, y), (*hexrgb(colors[ch]), 255))
    return img


ETH = {'1': '#126a80', '2': '#1f8fa8', '3': '#2fb5cc', '4': '#52d3e3', '5': '#a6f3f8', '6': '#ffffff'}
WOOD = {'h': '#6b4a2b', 'H': '#8a6238', 'g': '#f0c85a'}
CROSS_PLANT = {'s': '#b9a46c', 'l': '#e8b833', 'L': '#ffe073', 'd': '#c08f1c'}

SPR = {
    'etherite_sword': [
        '..............11',
        '.............153',
        '............1531',
        '...........1531.',
        '..........1531..',
        '.........1531...',
        '........1531....',
        '.......1531.....',
        '..1...1531......',
        '..21.1531.......',
        '...2131.........',
        '...hg2..........',
        '..hH.21.........',
        '.hH...2.........',
        'hH..............',
        'h...............'],
    'etherite_pickaxe': [
        '....111111......',
        '...14555531.....',
        '..1331..1553....',
        '..11.....hH51...',
        '........hH..31..',
        '.......hH....1..',
        '......hH........',
        '.....hH.........',
        '....hH..........',
        '...hH...........',
        '..hH............',
        '.hH.............',
        'hH..............',
        'h...............',
        '................',
        '................'],
    'etherite_axe': [
        '......111.......',
        '.....15531......',
        '....1555331.....',
        '....155hH31.....',
        '.....1hH331.....',
        '.....hH.11......',
        '....hH..........',
        '...hH...........',
        '..hH............',
        '.hH.............',
        'hH..............',
        'h...............',
        '................',
        '................',
        '................',
        '................'],
    'etherite_shovel': [
        '..........111...',
        '.........15531..',
        '........155531..',
        '........1553311.',
        '.........1331...',
        '........hH11....',
        '.......hH.......',
        '......hH........',
        '.....hH.........',
        '....hH..........',
        '...hH...........',
        '..hH............',
        '.hH.............',
        'hH..............',
        '................',
        '................'],
    'etherite_hoe': [
        '......11111.....',
        '.....155531.....',
        '.....11.hH3.....',
        '.......hH.1.....',
        '......hH........',
        '.....hH.........',
        '....hH..........',
        '...hH...........',
        '..hH............',
        '.hH.............',
        'hH..............',
        '................',
        '................',
        '................',
        '................',
        '................'],
    'etherite_helmet': [
        '................',
        '................',
        '................',
        '....11111111....',
        '...1555544331...',
        '..154433333321..',
        '..143322222231..',
        '..13311111133...',
        '..131......131..',
        '..121......121..',
        '..111......111..',
        '................',
        '................',
        '................',
        '................',
        '................'],
    'etherite_chestplate': [
        '................',
        '..1111....1111..',
        '.155311111135531',
        '.154333333334331',
        '.143322222223321',
        '..1332222222331.',
        '...13222222231..',
        '...13222222231..',
        '...13222222231..',
        '...13322222331..',
        '...12333333321..',
        '...11111111111..',
        '................',
        '................',
        '................',
        '................'],
    'etherite_leggings': [
        '................',
        '...1111111111...',
        '...1554444331...',
        '...1432222231...',
        '...1332111331...',
        '...133.1.1331...',
        '...133...1331...',
        '...132...1321...',
        '...132...1321...',
        '...132...1321...',
        '...121...1211...',
        '...111...111....',
        '................',
        '................',
        '................',
        '................'],
    'etherite_boots': [
        '................',
        '................',
        '................',
        '................',
        '................',
        '..1111....1111..',
        '..1551....1551..',
        '..1431....1431..',
        '..1331....1331..',
        '.13321...13321..',
        '1333321.1333321.',
        '1222221.1222221.',
        '1111111.1111111.',
        '................',
        '................',
        '................'],
    'etherite_ingot': [
        '................',
        '................',
        '................',
        '................',
        '.....11111111...',
        '....1555555431..',
        '...155444443331.',
        '..1544333333321.',
        '..1433333333221.',
        '..1222222222211.',
        '...11111111111..',
        '................',
        '................',
        '................',
        '................',
        '................'],
    'raw_etherite': [
        '................',
        '................',
        '................',
        '.......11.......',
        '.....11541......',
        '....1554331.....',
        '...15443321.....',
        '...1433332211...',
        '..14333222441...',
        '..13322225531...',
        '..1322224331....',
        '...12222221.....',
        '....111111......',
        '................',
        '................',
        '................'],
}

STAR = {'1': '#c9a23a', '2': '#efd178', '3': '#fff3c6', '4': '#ffffff'}
SPR_STAR = {
    'starquartz': [
        '................',
        '................',
        '.......1........',
        '.......2........',
        '......121.......',
        '......232.......',
        '..1222343222 1..',
        '...12334433 21..',
        '....123443221...',
        '.....12343 1....',
        '.....1233321....',
        '....12 2 1 21...',
        '....21.....12...',
        '...1.........1..',
        '................',
        '................'],
}

BERRY = {'s': '#7d8f3a', 'l': '#a8c24f', 'b': '#f2b84a', 'B': '#ffe28a', 'w': '#ffffff'}
SPR_MISC = {
    'manna_berries': ({'s': '#7d8f3a', 'l': '#a8c24f', 'b': '#e9a83a', 'B': '#ffe28a', 'w': '#ffffff'}, [
        '................',
        '.......ss.......',
        '......sll.......',
        '.....s..ls......',
        '....bb...bb.....',
        '...bBwb.bBwb....',
        '...bBBb.bBBb....',
        '....bb...bb.....',
        '......bb........',
        '.....bBwb.......',
        '.....bBBb.......',
        '......bb........',
        '................',
        '................',
        '................',
        '................']),
    'cloud_fluff': ({'1': '#c9d6e6', '2': '#e5edf6', '3': '#ffffff'}, [
        '................',
        '................',
        '................',
        '.....1111.......',
        '....122221......',
        '..11223332111...',
        '.1223333332221..',
        '12233333333321..',
        '12333333333331..',
        '.1223333333221..',
        '..11222222211...',
        '....1111111.....',
        '................',
        '................',
        '................',
        '................']),
    'flame_shard': ({'1': '#7a1a05', '2': '#c2410c', '3': '#f97316', '4': '#fbbf24', '5': '#fff3b0'}, [
        '................',
        '.........1......',
        '........12......',
        '.......1231.....',
        '......12341.....',
        '......13441.....',
        '.....124541.....',
        '.....135541.....',
        '....1245431.....',
        '....1345321.....',
        '....134431......',
        '....12431.......',
        '.....1221.......',
        '......11........',
        '................',
        '................']),
    'void_heart': ({'1': '#12051f', '2': '#3b0f5c', '3': '#6d28d9', '4': '#a78bfa', '5': '#f0e6ff'}, [
        '................',
        '................',
        '...111...111....',
        '..12221.12221...',
        '.1233321233321..',
        '.1234432344321..',
        '.1234543454321..',
        '.1233444443321..',
        '..12333433321...',
        '...123333321....',
        '....1233321.....',
        '.....12321......',
        '......121.......',
        '.......1........',
        '................',
        '................']),
    'skywood_sapling': ({'s': '#b9a46c', 'S': '#d8c9a8', 'l': '#e8b833', 'L': '#ffe073', 'd': '#c08f1c'}, [
        '................',
        '.....LL.........',
        '....LllL..LL....',
        '...dLlllLLllL...',
        '....ddlLlllld...',
        '......dlLld.....',
        '...LL..sS.......',
        '..LllL.sS.LL....',
        '..dllLLsSLllL...',
        '...ddlLsSllld...',
        '......dsS.d.....',
        '.......sS.......',
        '.......sS.......',
        '.......sS.......',
        '.......sS.......',
        '................']),
    'sky_crystal': ({'1': '#3b82c4', '2': '#60a5e8', '3': '#93c5fd', '4': '#dbeafe', '5': '#ffffff'}, [
        '................',
        '.......1........',
        '......135.......',
        '......1341......',
        '...1..1341......',
        '..135.1341..1...',
        '..1341234113....',
        '..13411234134...',
        '...1341234341...',
        '...1341224341...',
        '....134123341...',
        '....13412341....',
        '.....1312341....',
        '.....1212221....',
        '......11111.....',
        '................']),
}


def manna_stage(stage):
    r = rng_for('manna_stage')
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    leaf = [hexrgb('#7d8f3a'), hexrgb('#93a947'), hexrgb('#a8c24f'), hexrgb('#c3d96b')]
    h = [6, 9, 12, 13][stage]
    for x in range(1, 15):
        top = 16 - h + abs(x - 7.5) * 0.4 + r.random() * 2
        for y in range(int(top), 16):
            if r.random() < 0.72:
                img.putpixel((x, y), (*r.choice(leaf), 255))
    berries = [0, 0, 4, 9][stage]
    for _ in range(berries):
        x, y = r.randrange(2, 13), r.randrange(16 - h + 2, 15)
        img.putpixel((x, y), (*hexrgb('#f2b84a'), 255))
        img.putpixel((x + 1, y), (*hexrgb('#ffe28a'), 255))
    return img


def armor_layer(mask_path, palette):
    """Слой брони: берём только форму (альфу) развёртки, цвет рисуем сами."""
    mask = Image.open(mask_path).convert('RGBA')
    w, h = mask.size
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    r = rng_for('armor_' + mask_path)
    for y in range(h):
        for x in range(w):
            a = mask.getpixel((x, y))[3]
            if a == 0:
                continue
            # проверяем край детали — делаем тёмный контур
            edge = any(
                not (0 <= x + dx < w and 0 <= y + dy < h) or mask.getpixel((x + dx, y + dy))[3] == 0
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                c = palette[0]
            else:
                v = 0.5 + 0.3 * math.sin(x * 0.7 + y * 0.4) + r.random() * 0.2
                c = palette[min(len(palette) - 1, max(1, int(v * len(palette))))]
            out.putpixel((x, y), (*c, a))
    return out


def icon():
    img = Image.new('RGBA', (128, 128))
    for y in range(128):
        for x in range(128):
            t = y / 127
            img.putpixel((x, y), (*mix(hexrgb('#7dc4ff'), hexrgb('#fff3c6'), t), 255))
    cl = cloud('icon_cloud', CLOUD, 255).resize((64, 64), Image.NEAREST)
    gs = golden_grass_top().resize((64, 16), Image.NEAREST)
    img.paste(gs, (32, 48))
    img.paste(cl.crop((0, 0, 64, 24)), (32, 64))
    return img


def heaven_portal(frames=16):
    """Анимированная золотисто-белая завеса (кадры друг под другом)."""
    img = Image.new('RGBA', (16, 16 * frames))
    for f in range(frames):
        t = f / frames * 2 * math.pi
        for y in range(16):
            for x in range(16):
                dx, dy = x - 7.5, y - 7.5
                ang = math.atan2(dy, dx)
                d = math.sqrt(dx * dx + dy * dy)
                v = 0.5 + 0.5 * math.sin(ang * 3 + d * 0.9 - t)
                v = v * 0.7 + 0.3 * (0.5 + 0.5 * math.sin(y * 0.8 + t * 2))
                c = mix(hexrgb('#ffd56b'), hexrgb('#ffffff'), v)
                img.putpixel((x, y + 16 * f), (*c, int(150 + 80 * v)))
    return img
