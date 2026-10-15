"""Светящиеся слои старым мобам (планка качества): маска свечения выбирается по цвету готовой текстуры.

Звёздные скаты и облачная медуза — золотые и белые крапинки; Падший Серафим — красные глаза. Слой подхватывает рендер
(`CelestialRenderers.SimpleRenderer` — если есть `<текстура>_glow.png`; `SeraphRenderer` — явно). Запускать после текстур мобов.
"""
import os

from PIL import Image

from gen_assets import ASSETS


def specks(r, g, b):
    return r > 200 and g > 170 and b < 200 and r + g + b > 560  # золотистые и белые искры


def red_eyes(r, g, b):
    return r > 150 and g < 70 and b < 70


RULES = {'sky_ray': specks, 'void_ray': specks, 'cloud_jelly': specks, 'fallen_seraph': red_eyes}


def main():
    for name, rule in RULES.items():
        src = Image.open(os.path.join(ASSETS, 'textures/entity', name + '.png')).convert('RGBA')
        glow = Image.new('RGBA', src.size, (0, 0, 0, 0))
        n = 0
        for y in range(src.height):
            for x in range(src.width):
                r, g, b, a = src.getpixel((x, y))
                if a and rule(r, g, b):
                    glow.putpixel((x, y), (r, g, b, 255))
                    n += 1
        glow.save(os.path.join(ASSETS, 'textures/entity', name + '_glow.png'))
        print(f'  {name}: {n} светящихся точек')
    print('ok: светящиеся слои старых мобов')


if __name__ == '__main__':
    main()
