"""Ветка достижений, проход 1 планки качества: загадки, металлы, охота, Холод, испытания (до 40+ всего).

Загадки, «Мастер загадок» и «Испытанный» выдаются из кода (критерий impossible, Story.grant):
puzzle/PuzzleRewards (по виду загадки), trial/TrialControllerBlockEntity.succeed.
"""
from gen_assets import c
from gen_story import advancement, lang_patch

IMPOSSIBLE = {'granted': {'trigger': 'minecraft:impossible'}}


def has(*items):
    return {'items': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': i} for i in items]}}}


def killed(entity):
    return {'kill': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {
        'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:entity_type': entity}}}}}


def ate(*items):
    return {i.split(':')[1]: {'trigger': 'minecraft:consume_item', 'conditions': {'item': {'items': i}}} for i in items}


# (путь, родитель, значок, критерии, рамка, ru заголовок, ru описание, en заголовок, en описание)
ACHIEVEMENTS = [
    # загадки Рая и Бездны
    ('bell_ringer', 'gates_of_heaven', 'minecraft:bell', IMPOSSIBLE, 'task',
     'Звонарь', 'Сыграй мелодию колоколов святилища', 'Bell Ringer', 'Play the shrine bells\' melody'),
    ('star_walker', 'gates_of_heaven', c('star_fragment'), IMPOSSIBLE, 'task',
     'По звёздным плитам', 'Пройди звёздные плиты, не ошибившись', 'Star Walker', 'Cross the star tiles without a mistake'),
    ('riddle_solved', 'gates_of_heaven', c('rune_of_stars'), IMPOSSIBLE, 'task',
     'Отгадчик', 'Ответь на загадку рунного пьедестала', 'Riddle Solved', 'Answer the rune pedestal\'s riddle'),
    ('star_lock', 'gates_of_heaven', c('starquartz'), IMPOSSIBLE, 'goal',
     'Звёздный ключ', 'Открой звёздный кодовый замок обсерватории', 'Starry Key', 'Open the observatory\'s star lock'),
    ('memory_keeper', 'gates_of_heaven', c('cloud_fluff'), IMPOSSIBLE, 'goal',
     'Память облаков', 'Повтори путь вспышек на плитах памяти', 'Memory of Clouds', 'Repeat the path of flashes on the memory plates'),
    ('echo_listener', 'beneath_the_clouds', c('shadow_essence'), IMPOSSIBLE, 'goal',
     'Голос во тьме', 'Разгадай Святилище эха в Бездне', 'Voice in the Dark', 'Solve the Echo Sanctum in the Abyss'),
    ('puzzle_master', 'light_returns', c('tuning_fork'), IMPOSSIBLE, 'challenge',
     'Мастер загадок', 'Реши все восемь видов загадок Небес', 'Puzzle Master', 'Solve all eight kinds of Heaven\'s puzzles'),
    ('trial_champion', 'gates_of_heaven', c('halo'), IMPOSSIBLE, 'goal',
     'Испытанный', 'Пройди испытание у кристалла', 'Tried and True', 'Complete a crystal trial'),
    # металлы и снаряжение
    ('heavenly_metal', 'gates_of_heaven', c('etherite_ingot'), has(c('etherite_ingot')), 'task',
     'Небесный металл', 'Выплавь слиток эфирита', 'Heavenly Metal', 'Smelt an etherite ingot'),
    ('clad_in_ether', 'heavenly_metal', c('etherite_chestplate'),
     has(c('etherite_helmet'), c('etherite_chestplate'), c('etherite_leggings'), c('etherite_boots')), 'goal',
     'Облачённый в эфир', 'Собери полный комплект эфиритовой брони', 'Clad in Ether', 'Collect a full set of etherite armor'),
    ('abyssal_smith', 'beneath_the_clouds', c('abyssal_ingot'), has(c('abyssal_ingot')), 'task',
     'Кузнец Бездны', 'Получи слиток бездонной стали', 'Abyssal Smith', 'Obtain an abyssal ingot'),
    ('starbow', 'fall_of_the_seraph', c('starbow'), has(c('starbow')), 'goal',
     'Тетива из звёзд', 'Добудь звёздный лук', 'Strung with Stars', 'Obtain the Starbow'),
    ('haloed', 'fall_of_the_seraph', c('halo'), has(c('halo')), 'goal',
     'Венец света', 'Добудь нимб', 'Crowned with Light', 'Obtain a halo'),
    ('golden_fleece', 'gates_of_heaven', c('golden_fleece'), has(c('golden_fleece')), 'task',
     'Золотое руно', 'Остриги Златорунного барана', 'Golden Fleece', 'Shear a Golden Ram'),
    ('fallen_star', 'root', c('star_fragment'), has(c('star_fragment')), 'task',
     'Упавшая звезда', 'Подбери осколок упавшей звезды', 'Fallen Star', 'Pick up a fragment of a fallen star'),
    # охота
    ('shadow_hunter', 'root', c('shadow_essence'), killed(c('shadow')), 'task',
     'Гаситель теней', 'Изгони Тень, пришедшую с Угасанием', 'Shadow Hunter', 'Banish a Shadow brought by the Fading'),
    ('storm_breaker', 'gates_of_heaven', c('charged_crystal'), killed(c('storm_elemental')), 'goal',
     'Укротитель бури', 'Победи Грозового элементаля', 'Storm Breaker', 'Defeat a Storm Elemental'),
    ('serpent_slayer', 'gates_of_heaven', c('seraph_feather'), killed(c('winged_serpent')), 'task',
     'Змееборец', 'Сбей Крылатого змея', 'Serpent Slayer', 'Bring down a Winged Serpent'),
    ('wraith_banisher', 'frozen_wings', c('ice_shard'), killed(c('frost_wraith')), 'task',
     'Огонь против стужи', 'Изгони Морозного духа', 'Fire Against Frost', 'Banish a Frost Wraith'),
    ('hunter_blinded', 'beneath_the_clouds', c('worm_chitin'), killed(c('blind_hunter')), 'task',
     'Слепой против слепого', 'Победи Слепого охотника', 'Blind Against Blind', 'Defeat a Blind Hunter'),
    # Холод
    ('warm_heart', 'frozen_wings', c('spiced_cider'), {**ate(c('spiced_cider'), c('hearth_stew'))}, 'task',
     'Тепло у очага', 'Согрейся пряным глинтвейном или похлёбкой у очага', 'Hearth\'s Warmth', 'Warm up with spiced cider or hearth stew'),
    ('fur_clad', 'frozen_wings', c('fur_cloak'), has(c('fur_hood'), c('fur_cloak'), c('fur_leggings'), c('fur_boots')), 'task',
     'В меха с головы до пят', 'Собери полный комплект меховой одежды', 'Fur from Head to Toe', 'Collect a full set of fur clothing'),
]


def main():
    entries = {}
    for path, parent, icon, criteria, frame, ru_t, ru_d, en_t, en_d in ACHIEVEMENTS:
        tk, dk = f'advancements.celestial.{path}.title', f'advancements.celestial.{path}.description'
        advancement(path, parent, icon, criteria, frame, tk, dk)  # несколько критериев — любой из них
        entries[tk] = (ru_t, en_t)
        entries[dk] = (ru_d, en_d)
    lang_patch(entries)
    print('ok: достижения', len(ACHIEVEMENTS))


if __name__ == '__main__':
    main()
