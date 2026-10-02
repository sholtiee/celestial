#!/usr/bin/env python3
"""Сюжет «Угасающий свет»: достижения-главы, тексты дневника, сообщения. Запуск: python3 tools/gen_story.py"""
import json
import os

from gen_assets import ASSETS, DATA, c, write_json

STORY = [
    # (путь, родитель, иконка, критерий, рамка, ru-заголовок, ru-описание, en-заголовок, en-описание)
    ('root', None, c('wanderer_journal'),
     {'journal': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('wanderer_journal')}]}}}, 'task',
     'Угасающий свет', 'Небесный свет гаснет. Прочти Дневник Странника', 'The Fading Light', 'The light of the heavens is fading. Read the Wanderer\'s Journal'),
    ('flame_of_the_deep', 'root', c('flame_shard'),
     {'shard': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('flame_shard')}]}}}, 'task',
     'Пламя глубин', 'Найди Осколок Пламени в крепости Ада или бастионе', 'Flame of the Deep', 'Find a Flame Shard in a Nether fortress or bastion'),
    ('heart_of_the_void', 'flame_of_the_deep', c('void_heart'),
     {'heart': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('void_heart')}]}}}, 'goal',
     'Сердце Пустоты', 'Победи дракона Энда и забери Сердце Пустоты', 'Heart of the Void', 'Defeat the Ender Dragon and claim the Void Heart'),
    ('gates_of_heaven', 'heart_of_the_void', c('radiant_stone'),
     {'entered': {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': c('heaven')}}}, 'goal',
     'Врата Небес', 'Сложи рамку из светлого камня, зажги её Сердцем Пустоты и войди в Рай', 'Gates of Heaven',
     'Build a Radiant Stone frame, light it with the Void Heart and enter Heaven'),
    ('fall_of_the_seraph', 'gates_of_heaven', c('halo'),
     {'killed': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                                         'predicate': {'minecraft:entity_type': c('fallen_seraph')}}}},
      'impossible': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Падение Серафима', 'Одолей Падшего Серафима в Небесной Цитадели', 'Fall of the Seraph', 'Defeat the Fallen Seraph in the Celestial Citadel'),
    ('light_returns', 'fall_of_the_seraph', c('light_shard'),
     {'altar': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Свет возвращается', 'Положи три осколка на Небесный алтарь', 'The Light Returns', 'Place the three shards on the Celestial Altar'),
]

SIDE = [
    ('pegasus_rider', 'gates_of_heaven', c('pegasus_spawn_egg'),
     {'tamed': {'trigger': 'minecraft:tame_animal', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                               'predicate': {'minecraft:entity_type': c('pegasus')}}}}}, 'task',
     'Небесный наездник', 'Приручи пегаса манной', 'Sky Rider', 'Tame a pegasus with manna berries'),
    ('golden_vault', 'gates_of_heaven', c('golden_key'),
     {'key': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('golden_key')}]}}}, 'goal',
     'Ключ от всех дверей', 'Добудь золотой ключ от хранилища руин', 'Key to Every Door', 'Obtain a golden vault key'),
    ('wings_of_light', 'fall_of_the_seraph', c('seraph_wings'),
     {'wings': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('seraph_wings')}]}}}, 'goal',
     'Крылья света', 'Заполучи Крылья Серафима', 'Wings of Light', 'Obtain the Seraph Wings'),
]

JOURNAL_RU = {
    'intro': 'Странник,\n\nесли ты читаешь это — свет небес гаснет. Ночи становятся длиннее, звёзды падают одна за другой.\n\nТри осколка держали свет: Пламя, Пустота и Свет. Их разбросали по трём мирам.',
    'task_flame': '§lПервый осколок§r\n\nОсколок Пламени скрыт в глубинах Ада: ищи его в сундуках адских крепостей и бастионов. Говорят, им владеют и ифриты.',
    'flame': 'Пламя у тебя. Оно тёплое, но не обжигает — словно помнит, каким было небо.',
    'task_void': '§lВторой осколок§r\n\nСердце Пустоты бьётся внутри дракона Энда. Победи его — и Сердце упадёт к твоим ногам. Ещё его находили в сундуках городов Энда.',
    'void': 'Сердце Пустоты пульсирует в руке. Оно открывает то, что закрыто для смертных.',
    'task_gates': '§lВрата§r\n\nСветлый камень куётся из светокаменной пыли, кварца Ада и золота. Сложи из него рамку (как портал в Ад) и коснись её Сердцем Пустоты.',
    'gates': 'Рай! Острова парят над облаками, а гравитация тут мягче. Осторожно у края: упадёшь — окажешься высоко над Верхним миром.\n\nСветлячки укажут путь к святыням.',
    'task_seraph': '§lТретий осколок§r\n\nОсколок Света украл Падший Серафим. Он спит в Небесной Цитадели под печатью. Подготовься: эфиритовая броня, звёздный лук и запас манны.',
    'seraph': 'Серафим пал. Его крылья и нимб теперь твои — как и Осколок Света.',
    'task_altar': '§lПоследний шаг§r\n\nВ Цитадели стоит Небесный алтарь. Положи на него все три осколка.',
    'finale': 'Свет вернулся.\n\nНебо снова сияет, и Рай открыт для всех, кто осмелится подняться.\n\nСпасибо, Странник.\n\n§o— Celestial§r',
}
JOURNAL_EN = {
    'intro': 'Wanderer,\n\nif you are reading this, the light of the heavens is fading. Nights grow longer and stars fall one by one.\n\nThree shards held the light: Flame, Void and Light. They were scattered across three worlds.',
    'task_flame': '§lThe first shard§r\n\nThe Flame Shard hides in the depths of the Nether: search the chests of Nether fortresses and bastions. Blazes are said to carry them too.',
    'flame': 'The Flame is yours. It is warm but does not burn, as if it remembers the sky.',
    'task_void': '§lThe second shard§r\n\nThe Void Heart beats inside the Ender Dragon. Defeat it and the Heart will fall at your feet. It has also been found in End city chests.',
    'void': 'The Void Heart pulses in your hand. It opens what is closed to mortals.',
    'task_gates': '§lThe Gates§r\n\nRadiant Stone is forged from glowstone dust, Nether quartz and gold. Build a frame of it (like a Nether portal) and touch it with the Void Heart.',
    'gates': 'Heaven! Islands float above the clouds and gravity is gentle here. Mind the edge: fall off and you will find yourself high above the Overworld.\n\nThe wisps will guide you to the shrines.',
    'task_seraph': '§lThe third shard§r\n\nThe Light Shard was stolen by the Fallen Seraph. He sleeps sealed in the Celestial Citadel. Prepare well: etherite armor, a starbow and plenty of manna.',
    'seraph': 'The Seraph has fallen. His wings and halo are yours now, and so is the Light Shard.',
    'task_altar': '§lThe last step§r\n\nThe Celestial Altar stands in the Citadel. Place all three shards upon it.',
    'finale': 'The light has returned.\n\nThe sky shines again, and Heaven is open to all who dare to rise.\n\nThank you, Wanderer.\n\n§o— Celestial§r',
}
MESSAGES = {
    'story.celestial.dream': ('§eТебе снится сон: небо гаснет, а чей-то голос просит о помощи. Проснувшись, ты находишь в сумке старый дневник.',
                              '§eYou dream of a darkening sky and a voice asking for help. When you wake, an old journal is in your bag.'),
    'story.celestial.void_heart_drop': ('§5Из тела дракона выпадает пульсирующее Сердце Пустоты…', '§5A pulsing Void Heart falls from the dragon...'),
    'story.celestial.portal_lit': ('§6Рамка вспыхивает золотым светом. Врата Небес открыты!', '§6The frame flares with golden light. The Gates of Heaven are open!'),
    'story.celestial.seraph_defeated': ('§6Серафим рассыпается светом. Осколок Света свободен! Отнеси все три осколка на алтарь Цитадели.',
                                        '§6The Seraph dissolves into light. The Light Shard is free! Bring all three shards to the Citadel altar.'),
    'story.celestial.finale.title': ('§6Свет возвращается', '§6The Light Returns'),
    'story.celestial.finale.subtitle': ('Небеса снова сияют', 'The heavens shine again'),
    'story.celestial.epilogue.1': ('§e✦ Осколки сливаются в столп света, и он пронзает облака.', '§e✦ The shards merge into a pillar of light that pierces the clouds.'),
    'story.celestial.epilogue.2': ('§e✦ Над Верхним миром снова загораются звёзды.', '§e✦ Stars light up above the Overworld again.'),
    'story.celestial.epilogue.3': ('§e✦ Ангелы выходят из домов и поют — впервые за много лет.', '§e✦ The angels step out of their homes and sing for the first time in years.'),
    'story.celestial.epilogue.4': ('§e✦ Тебя коснулось Благословение небес: +2 сердца, навсегда.', '§e✦ The Blessing of the heavens is upon you: +2 hearts, forever.'),
    'story.celestial.epilogue.5': ('§7Конец. Рай остаётся открытым — исследуй его дальше.', '§7The End. Heaven remains open - keep exploring.'),
    'block.celestial.celestial_altar.hint': ('Алтарь ждёт: Осколок Пламени, Сердце Пустоты и Осколок Света', 'The altar awaits: Flame Shard, Void Heart and Light Shard'),
    'effect.celestial.blessing': ('Благословение небес', 'Blessing of the Heavens'),
    'item.celestial.wanderer_journal': ('Дневник Странника', 'Wanderer\'s Journal'),
    'entity.celestial.fallen_seraph': ('Падший Серафим', 'Fallen Seraph'),
    'biome.celestial.golden_meadows': ('Золотые луга', 'Golden Meadows'),
    'biome.celestial.cloud_forest': ('Облачный лес', 'Cloud Forest'),
    'biome.celestial.crystal_spires': ('Кристальные шпили', 'Crystal Spires'),
    'biome.celestial.rainbow_shoals': ('Радужные отмели', 'Rainbow Shoals'),
    'biome.celestial.heaven_gardens': ('Небесные сады', 'Heaven Gardens'),
    'biome.celestial.storm_peak': ('Грозовой пик', 'Storm Peak'),
    'biome.celestial.star_glade': ('Звёздная поляна', 'Star Glade'),
    'gamerule.celestial.fading': ('Celestial: Угасание мира', 'Celestial: World Fading'),
    'block.celestial.quest_board': ('Доска поручений', 'Quest Board'),
    'quest.celestial.board.header': ('✦ Поручения ангелов (репутация: %s). Нажми [Взять] или [Сдать]:', '✦ Angel quests (reputation: %s). Click [Take] or [Turn in]:'),
    'quest.celestial.kill': ('Одолеть: %s — %3$s/%2$s', 'Defeat: %s - %3$s/%2$s'),
    'quest.celestial.bring': ('Принести: %s — %3$s/%2$s', 'Bring: %s - %3$s/%2$s'),
    'quest.celestial.explore': ('Найти и посетить: %s', 'Find and visit: %s'),
    'quest.celestial.reward': ('Награда: %s × %s, репутация +%s', 'Reward: %s x %s, reputation +%s'),
    'quest.celestial.take': ('[Взять]', '[Take]'),
    'quest.celestial.take_hint': ('Взять поручение (не больше трёх сразу)', 'Take the quest (three at most)'),
    'quest.celestial.turn_in': ('[Сдать]', '[Turn in]'),
    'quest.celestial.taken': ('Поручение принято', 'Quest accepted'),
    'quest.celestial.too_many': ('Не больше трёх поручений одновременно', 'No more than three quests at once'),
    'quest.celestial.nothing': ('Нечего сдавать', 'Nothing to turn in'),
    'quest.celestial.done': ('✦ Поручение выполнено!', '✦ Quest complete!'),
    'structure.celestial.sky_ruins': ('Руины Рая', 'Heaven Ruins'),
    'structure.celestial.trial_tower': ('Башня Испытаний', 'Trial Tower'),
    'structure.celestial.beam_temple': ('Храм Лучей', 'Temple of Beams'),
    'structure.celestial.cloud_castle': ('Облачный замок', 'Cloud Castle'),
    'structure.celestial.airship_wreck': ('Обломки воздушного галеона', 'Airship Wreck'),
    'structure.celestial.citadel': ('Небесная Цитадель', 'Celestial Citadel'),
    'structure.celestial.sky_lighthouse': ('Небесный маяк', 'Sky Lighthouse'),
    'structure.celestial.sky_village': ('Небесная деревня', 'Sky Village'),
    'trial.celestial.name.cloud_castle': ('Гнев Облачного замка', 'Wrath of the Cloud Castle'),
    'gamerule.celestial.meteors': ('Celestial: звездопады', 'Celestial: Meteor Showers'),
    'gamerule.celestial.fading_days': ('Celestial: дней на стадию Угасания', 'Celestial: Days per Fading Stage'),
    'item.celestial.halo.lore1': ('Наденьте на голову: регенерация и ночное зрение', 'Wear on your head: regeneration and night vision'),
    'item.celestial.seraph_wings.lore1': ('Планируйте как на элитрах', 'Glide like elytra'),
    'item.celestial.seraph_wings.lore2': ('В полёте жмите прыжок — взмах крыльями (до 5 подряд)', 'Press jump while gliding to flap (up to 5 in a row)'),
    'item.celestial.cloud_parachute.lore1': ('Раскроется сам, если вы падаете слишком долго', 'Opens by itself when you fall for too long'),
    'item.celestial.starbow.lore1': ('Стрелы сами находят ближайшего врага', 'Arrows seek the nearest enemy'),
    'item.celestial.light_spear.lore1': ('Бросок по ПКМ — копьё вернётся в руку', 'Right-click to throw; the spear returns to you'),
    'item.celestial.void_heart.lore1': ('Коснитесь рамки из светлого камня, чтобы открыть Врата Небес', 'Touch a Radiant Stone frame to open the Gates of Heaven'),
    'item.celestial.void_heart.lore2': ('Второй осколок света', 'The second shard of light'),
    'item.celestial.flame_shard.lore1': ('Первый осколок света', 'The first shard of light'),
    'item.celestial.light_shard.lore1': ('Третий осколок света', 'The third shard of light'),
    'item.celestial.wanderer_journal.lore1': ('ПКМ — прочитать. Страницы появляются по ходу истории', 'Right-click to read. Pages appear as the story unfolds'),
    'item.celestial.bronze_key.lore1': ('Открывает бронзовое хранилище в руинах (держите в руке)', 'Opens the bronze vault in the ruins (hold in hand)'),
    'item.celestial.silver_key.lore1': ('Открывает серебряное хранилище в руинах', 'Opens the silver vault in the ruins'),
    'item.celestial.golden_key.lore1': ('Открывает золотое хранилище в руинах', 'Opens the golden vault in the ruins'),
}


def advancement(path, parent, icon, criteria, frame, title_key, desc_key, root=False):
    reqs = [list(criteria.keys())] if 'impossible' not in criteria else [[k for k in criteria]]
    display = {'icon': {'id': icon}, 'title': {'translate': title_key}, 'description': {'translate': desc_key}, 'frame': frame,
               'show_toast': True, 'announce_to_chat': True}
    if root:
        display['background'] = 'minecraft:gui/advancements/backgrounds/end'
    adv = {'criteria': criteria, 'display': display, 'requirements': reqs}
    if parent:
        adv['parent'] = c('story/' + parent)
    if frame == 'challenge':
        adv['rewards'] = {'experience': 500}
    write_json(os.path.join(DATA, 'advancement/story', path + '.json'), adv)


def lang_patch(entries):
    for lang, idx in (('ru_ru', 0), ('en_us', 1)):
        path = os.path.join(ASSETS, 'lang', lang + '.json')
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for k, v in entries.items():
            data[k] = v[idx]
        write_json(path, dict(sorted(data.items())))


def main():
    entries = {}
    for i, (path, parent, icon, criteria, frame, ru_t, ru_d, en_t, en_d) in enumerate(STORY + SIDE):
        tk, dk = f'advancements.celestial.{path}.title', f'advancements.celestial.{path}.description'
        # для «Падения Серафима» засчитываем либо убийство, либо программную выдачу
        if 'impossible' in criteria:
            criteria = dict(criteria)
            adv_criteria = criteria
            write_reqs = [[k for k in adv_criteria]]
        advancement(path, parent, icon, criteria, frame, tk, dk, root=parent is None)
        entries[tk] = (ru_t, en_t)
        entries[dk] = (ru_d, en_d)
    for k in JOURNAL_RU:
        entries['journal.celestial.' + k] = (JOURNAL_RU[k], JOURNAL_EN[k])
    entries.update(MESSAGES)
    lang_patch(entries)
    print('ok: глав', len(STORY), 'доп. достижений', len(SIDE), 'строк', len(entries))


if __name__ == '__main__':
    main()
