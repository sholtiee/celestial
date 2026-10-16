"""3D-модели предметов в руке (планка качества): в инвентаре, на земле и в рамке — плоская иконка, в руках — объёмная модель.

Предмет переключается по контексту отображения (`minecraft:select` по `minecraft:display_context`, как у ванильного трезубца).
Текстура объёмной модели — полоски-«материалы» 16×16 (`item/<имя>_3d`), рисуются здесь же.
Запускается после gen_assets (перезаписывает определение предмета).
"""
import os

from PIL import Image

import textures as T
from gen_assets import ASSETS, c, model, save_png, write_json

H = T.hexrgb


def strip_texture(name, columns):
    """Текстура из вертикальных полос по 4 пикселя: columns — список палитр (светлый → тёмный), шум по вертикали."""
    img = Image.new('RGBA', (16, 16))
    r = T.rng_for(name + '_3d')
    for i, pal in enumerate(columns):
        cols = [H(h) for h in pal]
        for x in range(i * 4, i * 4 + 4):
            for y in range(16):
                t = min(len(cols) - 1, int((x - i * 4) / 4 * len(cols)))  # грань светлее слева, темнее справа
                col = T.mix(cols[t], cols[min(len(cols) - 1, t + 1)], r.random() * 0.4)
                img.putpixel((x, y), (*col, 255))
    save_png(img, f'item/{name}_3d')


def box(frm, to, u, emissive=False):
    """Параллелепипед; u — номер полосы текстуры (0..3)."""
    uv = [u * 4, 0, u * 4 + 4, 16]
    e = {'from': frm, 'to': to, 'faces': {f: {'uv': uv, 'texture': '#all'} for f in ('north', 'south', 'east', 'west', 'up', 'down')}}
    if emissive:
        e['light_emission'] = 15
    return e


def held(name, elements, display):
    model(f'item/{name}_held', {'textures': {'all': c(f'item/{name}_3d'), 'particle': c(f'item/{name}')}, 'elements': elements,
                                'display': display})
    write_json(os.path.join(ASSETS, 'items', name + '.json'), {'model': {
        'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': ['gui', 'ground', 'fixed', 'on_shelf'], 'model': {'type': 'minecraft:model', 'model': c(f'item/{name}')}}],
        'fallback': {'type': 'minecraft:model', 'model': c(f'item/{name}_held')}}})


def light_spear():
    strip_texture('light_spear', [('#f3d27a', '#c08f1c', '#8a6410'), ('#ffffff', '#d8f2ff', '#9fd8ff'), ('#fff1b0', '#f0c040', '#b08020'),
                                  ('#e8e8f0', '#b0b0c0', '#808090')])
    elements = [
        box([7.5, -10, 7.5], [8.5, 19, 8.5], 0),          # древко (до перекладины)
        box([7.25, -11, 7.25], [8.75, -10, 8.75], 2),     # навершие
        box([7.25, 4, 7.25], [8.75, 6, 8.75], 3),         # обмотка под рукой
        box([5.5, 19, 7.25], [10.5, 20, 8.75], 2),        # перекладина
        box([7, 20, 7], [9, 24, 9], 1, emissive=True),    # наконечник — светится
        box([7.5, 24, 7.5], [8.5, 28, 8.5], 1, emissive=True),
    ]
    display = {
        'thirdperson_righthand': {'rotation': [90, 0, 0], 'translation': [0, 1, 3], 'scale': [0.85, 0.85, 0.85]},
        'thirdperson_lefthand': {'rotation': [90, 0, 0], 'translation': [0, 1, 3], 'scale': [0.85, 0.85, 0.85]},
        'firstperson_righthand': {'rotation': [0, -90, 20], 'translation': [1.5, -1, 1], 'scale': [0.68, 0.68, 0.68]},
        'firstperson_lefthand': {'rotation': [0, 90, -20], 'translation': [1.5, -1, 1], 'scale': [0.68, 0.68, 0.68]},
        'head': {'rotation': [0, 0, 0], 'translation': [0, 4, 0], 'scale': [0.6, 0.6, 0.6]},
    }
    held('light_spear', elements, display)


def tuning_fork():
    strip_texture('tuning_fork', [('#e8eef8', '#b8c4d8', '#8090a8'), ('#c8a060', '#8a6430', '#5a3e1c'), ('#bfe9ff', '#7fc8f0', '#4a98c8'),
                                  ('#ffffff', '#e0e8f0', '#b0b8c8')])
    elements = [
        box([7.5, 0, 7.5], [8.5, 7, 8.5], 1),            # рукоять
        box([7.25, -1, 7.25], [8.75, 0, 8.75], 1),
        box([6, 7, 7.5], [10, 8, 8.5], 0),               # перемычка
        box([6, 8, 7.5], [7, 15, 8.5], 0),               # зубцы
        box([9, 8, 7.5], [10, 15, 8.5], 0),
        box([7.5, 11, 7.75], [8.5, 12, 8.25], 2, emissive=True),  # звучащая искра между зубцами
    ]
    display = {
        'thirdperson_righthand': {'rotation': [90, 0, 0], 'translation': [0, 1, 1], 'scale': [0.85, 0.85, 0.85]},
        'thirdperson_lefthand': {'rotation': [90, 0, 0], 'translation': [0, 1, 1], 'scale': [0.85, 0.85, 0.85]},
        'firstperson_righthand': {'rotation': [0, -90, 15], 'translation': [1.2, 2.5, 1], 'scale': [0.7, 0.7, 0.7]},
        'firstperson_lefthand': {'rotation': [0, 90, -15], 'translation': [1.2, 2.5, 1], 'scale': [0.7, 0.7, 0.7]},
    }
    held('tuning_fork', elements, display)


def hourglass():
    strip_texture('hourglass', [('#ffe9a0', '#d8a838', '#8a6018'), ('#e8f4ff', '#bcd8f0', '#8ab0d0'), ('#f8e0a0', '#e0b860', '#b08840'),
                                ('#a87848', '#7a5430', '#4a3018')])
    elements = [
        box([4, 0, 4], [12, 1.5, 12], 0),               # нижнее донце
        box([4, 13.5, 4], [12, 15, 12], 0),             # верхнее донце
        box([4.5, 1.5, 4.5], [5.5, 13.5, 5.5], 3),      # четыре стойки
        box([10.5, 1.5, 4.5], [11.5, 13.5, 5.5], 3),
        box([4.5, 1.5, 10.5], [5.5, 13.5, 11.5], 3),
        box([10.5, 1.5, 10.5], [11.5, 13.5, 11.5], 3),
        box([6, 3.5, 6], [10, 5, 10], 1),               # нижняя колба (снизу — песок)
        box([7, 5, 7], [9, 6, 9], 1),
        box([7.5, 6, 7.5], [8.5, 8, 8.5], 2, emissive=True),  # перешеек: светящаяся струйка песка
        box([7, 8, 7], [9, 9, 9], 1),
        box([6, 9, 6], [10, 13.5, 10], 1),              # верхняя колба
        box([6, 1.5, 6], [10, 3.5, 10], 2),             # песок внизу
    ]
    display = {
        'thirdperson_righthand': {'rotation': [90, 0, 0], 'translation': [0, 1.5, 1.5], 'scale': [0.4, 0.4, 0.4]},
        'thirdperson_lefthand': {'rotation': [90, 0, 0], 'translation': [0, 1.5, 1.5], 'scale': [0.4, 0.4, 0.4]},
        'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [1.5, 5.5, 0], 'scale': [0.3, 0.3, 0.3]},
        'firstperson_lefthand': {'rotation': [0, 45, 0], 'translation': [1.5, 5.5, 0], 'scale': [0.3, 0.3, 0.3]},
    }
    held('hourglass', elements, display)


def main():
    light_spear()
    tuning_fork()
    hourglass()
    print('ok: объёмные предметы в руке — копьё, Камертон, Песочные часы')


if __name__ == '__main__':
    main()
