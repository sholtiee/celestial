"""Варианты текстур природных блоков (планка качества: «варианты текстур»): против сетки одинаковых квадратов в рельефе.

Для каждого блока из BLOCKS к готовой текстуре (её рисует свой генератор) добавляются ещё две: зеркальная и зеркальная со сдвигом
с переносом (шов не появляется — текстуры бесшовные), модели `<блок>_v1`, `_v2` и blockstate из 3 моделей × 4 поворота по оси Y.
Запускается после всех генераторов текстур. Повторный запуск без изменений не даёт диффа.
"""
import json
import os

from PIL import Image, ImageOps

from gen_assets import ASSETS, blockstate, c, model

BLOCKS = ['skystone', 'heaven_dirt', 'abyss_stone', 'frost_stone', 'chronite_stone', 'brass_soil', 'slag', 'astral_rock', 'astral_dust',
          'etherite_ore', 'starquartz_ore', 'frost_ore', 'chronite_ore', 'celestite_ore', 'abyssal_obsidian_ore']


def shifted(img, dx, dy):
    w, h = img.size
    out = Image.new(img.mode, img.size)
    for y in range(h):
        for x in range(w):
            out.putpixel(((x + dx) % w, (y + dy) % h), img.getpixel((x, y)))
    return out


def main():
    done = 0
    for n in BLOCKS:
        tex = os.path.join(ASSETS, 'textures/block', n + '.png')
        if not os.path.exists(tex):
            print('нет текстуры', n)
            continue
        base = Image.open(tex).convert('RGBA')
        for i, img in ((1, ImageOps.mirror(base)), (2, shifted(ImageOps.flip(base), 5, 9))):
            img.save(os.path.join(ASSETS, 'textures/block', f'{n}_v{i}.png'))
            model(f'block/{n}_v{i}', {'parent': 'minecraft:block/cube_all', 'textures': {'all': c(f'block/{n}_v{i}')}})
        variants = []
        for m in (n, n + '_v1', n + '_v2'):
            for y in (0, 90, 180, 270):
                v = {'model': c('block/' + m)}
                if y:
                    v['y'] = y
                variants.append(v)
        blockstate(n, {'variants': {'': variants}})
        done += 1
    print('ok: варианты текстур', done, 'блоков')


if __name__ == '__main__':
    main()
