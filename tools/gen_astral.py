"""Астрал (волна 0.6): **заготовка** измерения для механики невесомости (O5, шаг 1).

Тип измерения: вечная звёздная ночь (яркие звёзды, тёмно-синее небо, туманная дымка, искры звёздной пыли в воздухе), без смены суток.
Генератор пока — пустота (flat без слоёв): мир с астероидами, туманностями и биомами — задача S5.1 (заменит `dimension/astral.json`
и биомы, тип оставит). Физика — профиль `CelestialDimensions.ASTRAL` (гравитация ×0.15, без урона от падения, из пустоты выносит на остров).
"""
import os

from gen_assets import DATA, c, write_json
from gen_story import lang_patch


def dimension():
    write_json(os.path.join(DATA, 'dimension_type/astral.json'), {
        'ambient_light': 0.25,
        'attributes': {
            'minecraft:visual/sky_color': '#0b1030',
            'minecraft:visual/fog_color': '#141a3c',
            'minecraft:visual/star_brightness': 1.0,
            'minecraft:visual/cloud_height': 600.0,
            'minecraft:visual/ambient_light_color': '#202850',
            'minecraft:gameplay/bed_rule': {'can_set_spawn': 'never', 'can_sleep': 'never', 'destroy_on_use': False},
            'minecraft:gameplay/respawn_anchor_works': False,
        },
        'coordinate_scale': 1.0, 'default_clock': 'minecraft:overworld', 'has_ceiling': False, 'has_ender_dragon_fight': False,
        'has_fixed_time': True, 'has_skylight': True, 'height': 384, 'infiniburn': '#minecraft:infiniburn_end', 'logical_height': 384,
        'min_y': -64, 'monster_spawn_block_light_limit': 0, 'monster_spawn_light_level': 0, 'timelines': '#celestial:in_astral'})
    write_json(os.path.join(DATA, 'tags/timeline/in_astral.json'), {'values': []})
    write_json(os.path.join(DATA, 'worldgen/biome/astral_void.json'), {
        'attributes': {
            'minecraft:visual/sky_color': '#0b1030', 'minecraft:visual/fog_color': '#141a3c', 'minecraft:visual/water_fog_color': '#1a2050',
            'minecraft:visual/ambient_particles': [{'particle': {'type': 'minecraft:end_rod'}, 'probability': 0.0015}],
        },
        'carvers': [], 'downfall': 0.0, 'effects': {'grass_color': '#6a7ac8', 'foliage_color': '#5a6ab8', 'water_color': '#3a4aa8'},
        'features': [], 'has_precipitation': False, 'temperature': 0.5})
    path = os.path.join(DATA, 'dimension/astral.json')
    if not os.path.exists(path) or '"layers": []' in open(path).read():  # мир S5.1 не затираем
        write_json(path, {'type': c('astral'),
                          'generator': {'type': 'minecraft:flat', 'settings': {'biome': c('astral_void'), 'features': False, 'lakes': False, 'layers': []}}})


def main():
    dimension()
    lang_patch({
        'dimension.celestial.astral.drift': ('Звёздный ветер вынес тебя на остров', 'The star wind carried you back to an island'),
        'biome.celestial.astral_void': ('Звёздная пустота', 'Starry Void'),
    })
    print('ok: Астрал (заготовка измерения)')


if __name__ == '__main__':
    main()
