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
    # Акт II «Ниже облаков»
    ('beneath_the_clouds', 'light_returns', c('abyss_stone'),
     {'entered': {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': c('abyss')}}}, 'goal',
     'Ниже облаков', 'Спустись в Бездну через Разлом на дне Рая', 'Beneath the Clouds', 'Descend into the Abyss through the Rift at the bottom of Heaven'),
    ('heart_of_darkness', 'beneath_the_clouds', c('dark_core'),
     {'killed': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                                         'predicate': {'minecraft:entity_type': c('light_devourer')}}}},
      'impossible': {'trigger': 'minecraft:impossible'}}, 'challenge',
     'Сердце тьмы', 'Одолей Пожирателя Света в его Логове', 'Heart of Darkness', 'Defeat the Light Devourer in its Lair'),
]

SIDE = [
    ('starlight_bottled', 'light_returns', c('starlight_flask'),
     {'flask': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('starlight_flask')}]}}}, 'task',
     'Звёзды в склянке', 'Набери Флакон звёздного света из Звездоловки', 'Stars in a Bottle', 'Fill a Flask of Starlight at a Star Catcher'),
    ('silent_steps', 'beneath_the_clouds', c('blind_hunter_spawn_egg'),
     {'killed': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                                         'predicate': {'minecraft:entity_type': c('blind_hunter')}}}}}, 'task',
     'Тише шагов', 'Одолей Слепого охотника', 'Quieter than Footsteps', 'Defeat a Blind Hunter'),
    ('worm_breaker', 'beneath_the_clouds', c('worm_chitin'),
     {'killed': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                                         'predicate': {'minecraft:entity_type': c('deep_worm')}}}}}, 'goal',
     'Из-под камня', 'Одолей Глубинного червя', 'From Beneath the Stone', 'Defeat the Deep Worm'),
    ('dark_suits_me', 'beneath_the_clouds', c('abyssal_chestplate'),
     {'armor': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': c('abyssal_chestplate')}]}}}, 'goal',
     'Тьма мне к лицу', 'Выкуй нагрудник из безднового обсидиана', 'The Dark Suits Me', 'Forge an Abyssal Chestplate'),
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
    'intro': 'Странник,\n\nесли ты читаешь это — свет небес гаснет. Ночи становятся длиннее, звёзды падают одна за другой, а во тьме бродят Тени.\n\nТри осколка держали свет: Пламя, Пустота и Свет. Их разбросали по трём мирам. Звездочёты в обсерваториях знают больше — загляни в телескоп.',
    'task_flame': '§lПервый осколок§r\n\nОсколок Пламени хранит Пылающее святилище над лавовым морем Ада: пройди испытание огнём. Его находили и в адских крепостях, бастионах, у ифритов.',
    'flame': 'Пламя у тебя. Оно тёплое, но не обжигает — словно помнит, каким было небо.',
    'task_void': '§lВторой осколок§r\n\nСердце Пустоты бьётся внутри дракона Энда. Победи его — и Сердце упадёт к твоим ногам. Ещё его находят у Разломов Пустоты на окраинах Энда, откуда сочатся Тени.',
    'void': 'Сердце Пустоты пульсирует в руке. Оно открывает то, что закрыто для смертных.',
    'task_gates': '§lВрата§r\n\nСветлый камень куётся из светокаменной пыли, кварца Ада и золота. Сложи из него рамку (как портал в Ад) и коснись её Сердцем Пустоты.',
    'gates': 'Рай! Острова парят над облаками, а гравитация тут мягче. Осторожно у края: упадёшь — окажешься высоко над Верхним миром.\n\nСветлячки укажут путь к святыням.',
    'task_seraph': '§lТретий осколок§r\n\nОсколок Света украл Падший Серафим. Он спит в Небесной Цитадели под печатью. Подготовься: эфиритовая броня, звёздный лук и запас манны.',
    'seraph': 'Серафим пал. Его крылья и нимб теперь твои — как и Осколок Света.\n\nНо на его груди выжжен знак: лицо без лица. Серафим не предал небо сам — что-то поглотило его.',
    'task_altar': '§lПоследний шаг§r\n\nВ Цитадели стоит Небесный алтарь. Положи на него все три осколка.',
    'task_abyss': '§lАкт II. Ниже облаков§r\n\nНа нижнем ярусе Рая открылся Разлом — чёрная воронка в треснувшем острове. Шагни в неё.\n\nВ Бездне почти нет света: держи огонь в руке, бери Флаконы звёздного света.',
    'abyss': 'Бездна. Тьма здесь живая: она давит на разум, а в ней бродят твари, что едят свет.\n\nГде-то в глубине — Логово того, кто стережёт путь к Безликому. Ищи Затонувшие храмы: там хранят карты.',
    'devourer': 'Пожиратель Света пал, и в его груди нашлось Тёмное Ядро — сгусток украденного света.\n\nУгасание отступило ещё на ступень. Но Ядро холодное: оно помнит путь ещё ниже… или выше?\n\n§oКонец Акта II.§r',
    'finale': 'Свет вернулся — но не весь.\n\nУгасание отступило, звёзды загорелись снова. А из-под облаков Рая тянет холодом: там, внизу, ждёт тот, кто оставил знак на Серафиме.\n\n§oКонец Акта I. Сага Небес продолжается…§r',
}
JOURNAL_EN = {
    'intro': 'Wanderer,\n\nif you are reading this, the light of the heavens is fading. Nights grow longer, stars fall one by one and Shadows roam the dark.\n\nThree shards held the light: Flame, Void and Light. They were scattered across three worlds. The stargazers in their observatories know more: look through a telescope.',
    'task_flame': '§lThe first shard§r\n\nThe Flame Shard is guarded by the Blazing Sanctuary above the Nether lava sea: pass its trial of fire. It has also turned up in fortresses, bastions and blazes.',
    'flame': 'The Flame is yours. It is warm but does not burn, as if it remembers the sky.',
    'task_void': '§lThe second shard§r\n\nThe Void Heart beats inside the Ender Dragon. Defeat it and the Heart will fall at your feet. It is also found at the Void Rifts on the End\'s outskirts, where Shadows seep through.',
    'void': 'The Void Heart pulses in your hand. It opens what is closed to mortals.',
    'task_gates': '§lThe Gates§r\n\nRadiant Stone is forged from glowstone dust, Nether quartz and gold. Build a frame of it (like a Nether portal) and touch it with the Void Heart.',
    'gates': 'Heaven! Islands float above the clouds and gravity is gentle here. Mind the edge: fall off and you will find yourself high above the Overworld.\n\nThe wisps will guide you to the shrines.',
    'task_seraph': '§lThe third shard§r\n\nThe Light Shard was stolen by the Fallen Seraph. He sleeps sealed in the Celestial Citadel. Prepare well: etherite armor, a starbow and plenty of manna.',
    'seraph': 'The Seraph has fallen. His wings and halo are yours now, and so is the Light Shard.\n\nBut a mark is burned into his chest: a face without a face. The Seraph did not betray the sky. Something devoured him.',
    'task_altar': '§lThe last step§r\n\nThe Celestial Altar stands in the Citadel. Place all three shards upon it.',
    'task_abyss': '§lAct II. Beneath the Clouds§r\n\nA Rift has opened on Heaven\'s lowest tier: a black funnel in a cracked island. Step into it.\n\nThere is almost no light in the Abyss: keep a flame in hand and carry Flasks of Starlight.',
    'abyss': 'The Abyss. The dark here is alive: it weighs on the mind, and creatures that eat light roam it.\n\nSomewhere deep lies the Lair of the one who guards the way to the Faceless. Seek the Sunken Temples: they keep maps.',
    'devourer': 'The Light Devourer has fallen, and in its chest lay the Dark Core, a clot of stolen light.\n\nThe Fading recedes another stage. But the Core is cold: it remembers a way even deeper... or higher?\n\n§oEnd of Act II.§r',
    'finale': 'The light has returned, though not all of it.\n\nThe Fading recedes and the stars burn again. Yet a chill rises from beneath Heaven\'s clouds: down there waits whoever left that mark on the Seraph.\n\n§oEnd of Act I. The Saga of the Heavens continues...§r',
}
MESSAGES = {
    'story.celestial.dream': ('§eТебе снится сон: небо гаснет, а чей-то голос просит о помощи. Проснувшись, ты находишь в сумке старый дневник.',
                              '§eYou dream of a darkening sky and a voice asking for help. When you wake, an old journal is in your bag.'),
    'story.celestial.void_heart_drop': ('§5Из тела дракона выпадает пульсирующее Сердце Пустоты…', '§5A pulsing Void Heart falls from the dragon...'),
    'story.celestial.portal_lit': ('§6Рамка вспыхивает золотым светом. Врата Небес открыты!', '§6The frame flares with golden light. The Gates of Heaven are open!'),
    'story.celestial.seraph_defeated': ('§6Серафим рассыпается светом. Осколок Света свободен! На миг ты видишь на его груди знак — лицо без лица. Отнеси все три осколка на алтарь Цитадели.',
                                        '§6The Seraph dissolves into light. The Light Shard is free! For a moment you see a mark on his chest: a face without a face. Bring all three shards to the Citadel altar.'),
    'story.celestial.act2.title': ('§5Сердце тьмы', '§5Heart of Darkness'),
    'story.celestial.act2.subtitle': ('Акт II «Ниже облаков» пройден', 'Act II "Beneath the Clouds" complete'),
    'story.celestial.act2.1': ('§d✦ Пожиратель рассыпается клочьями тьмы, и над Логовом впервые за века вспыхивают жаровни.',
                               '§d✦ The Devourer crumbles into shreds of darkness, and the braziers of the Lair blaze for the first time in ages.'),
    'story.celestial.act2.2': ('§d✦ В твоих руках Тёмное Ядро — свет, который Безликий успел проглотить.',
                               '§d✦ In your hands is the Dark Core: light the Faceless had already swallowed.'),
    'story.celestial.act2.3': ('§8✦ Ядро тянет к холоду. Где-то бьются в лёд замёрзшие крылья… Сага Небес продолжается.',
                               '§8✦ The Core pulls toward the cold. Somewhere, frozen wings beat against ice... The Saga of the Heavens continues.'),
    'story.celestial.finale.title': ('§6Свет возвращается', '§6The Light Returns'),
    'story.celestial.finale.subtitle': ('Акт I «Угасающий свет» пройден', 'Act I "The Fading Light" complete'),
    'story.celestial.epilogue.1': ('§e✦ Осколки сливаются в столп света, и он пронзает облака.', '§e✦ The shards merge into a pillar of light that pierces the clouds.'),
    'story.celestial.epilogue.2': ('§e✦ Над Верхним миром снова загораются звёзды.', '§e✦ Stars light up above the Overworld again.'),
    'story.celestial.epilogue.3': ('§e✦ Ангелы выходят из домов и поют — но звездочёты хмурятся: свет вернулся не весь.', '§e✦ The angels step out and sing, but the stargazers frown: not all the light came back.'),
    'story.celestial.epilogue.4': ('§e✦ Тебя коснулось Благословение небес: +2 сердца, навсегда.', '§e✦ The Blessing of the heavens is upon you: +2 hearts, forever.'),
    'story.celestial.epilogue.5': ('§8✦ Из-под облаков доносится шёпот: «Свет — лишь пища…» Сага Небес продолжается.', '§8✦ A whisper rises from beneath the clouds: "Light is only food..." The Saga of the Heavens continues.'),
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
    'quest.celestial.done_today': ('Это поручение уже выполнено сегодня', 'You already completed this quest today'),
    'quest.celestial.explore_here': ('Ты уже здесь — это поручение берут на другой доске, вдали от цели', 'You are already here: take this errand from another board, away from its goal'),
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
