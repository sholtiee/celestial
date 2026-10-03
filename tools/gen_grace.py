"""Переводы Благодати, заклинаний Сияния и Кодекса Небес (волна 0.2, шаг 8)."""
from gen_story import lang_patch

SKILLS = {
    'stamina_1': ('Выносливость I', 'Stamina I', '+2 взмаха крыльев Серафима.', '+2 Seraph wing flaps.'),
    'double_jump': ('Двойной прыжок', 'Double Jump', 'Прыжок в воздухе.', 'Jump again in mid-air.'),
    'stamina_2': ('Выносливость II', 'Stamina II', 'Ещё +3 взмаха крыльев.', '+3 more wing flaps.'),
    'dash': ('Рывок', 'Dash', 'Клавиша G: рывок вперёд (перезарядка 2 с).', 'G key: dash forward (2 s cooldown).'),
    'feather_fall': ('Пёрышко', 'Featherfall', 'Безопасная высота падения +9 блоков.', '+9 blocks of safe fall height.'),
    'radiance_pool': ('Сосуд Сияния', 'Radiance Vessel', 'Максимум Сияния 150.', 'Max Radiance 150.'),
    'light_bolt': ('Световой луч', 'Light Bolt', 'Заклинание: луч света (7 урона, 11 по нежити).', 'Spell: a bolt of light (7 damage, 11 vs undead).'),
    'inner_fire': ('Внутренний огонь', 'Inner Fire', 'Холод Ледяных Чертогов отнимает тепло вдвое медленнее.',
                   'The cold of the Frozen Halls drains warmth half as fast.'),
    'inner_light': ('Внутренний свет', 'Inner Light', 'Страх тьмы в Бездне растёт вдвое медленнее.', 'Fear of the dark grows half as fast in the Abyss.'),
    'radiance_regen': ('Родник Сияния', 'Radiance Spring', 'Сияние восстанавливается вдвое быстрее.', 'Radiance regenerates twice as fast.'),
    'healing_light': ('Исцеляющий свет', 'Healing Light', 'Заклинание: лечит и даёт регенерацию.', 'Spell: heals and grants regeneration.'),
    'beacon_recall': ('Возврат к маяку', 'Beacon Recall', 'Заклинание: перенос к ближайшему Небесному маяку.', 'Spell: teleport to the nearest Sky Beacon.'),
    'light_shield': ('Щит Света', 'Light Shield', 'Заклинание: поглощение и сопротивление.', 'Spell: absorption and resistance.'),
    'starfall': ('Звездопад', 'Starfall', 'Заклинание: дождь копий света туда, куда смотришь.', 'Spell: rain of light spears where you look.'),
    'vigor': ('Живучесть', 'Vigor', '+4 к максимальному здоровью.', '+4 max health.'),
    'heavenly_strike': ('Небесный удар', 'Heavenly Strike', '+15% урона в ближнем бою.', '+15% melee damage.'),
    'resilience': ('Стойкость', 'Resilience', '+2 брони.', '+2 armor.'),
    'flash': ('Вспышка', 'Flash', 'Заклинание: ослепляет и отбрасывает врагов рядом.', 'Spell: blinds and repels nearby foes.'),
    'second_wind': ('Второе дыхание', 'Second Wind', 'Раз в 10 минут спасает от смерти.', 'Once per 10 minutes, cheats death.'),
}
SPELLS = {
    'scouts': ('Светлячки-разведчики', 'Scout Wisps'), 'light_bolt': ('Световой луч', 'Light Bolt'),
    'healing_light': ('Исцеляющий свет', 'Healing Light'), 'light_shield': ('Щит Света', 'Light Shield'),
    'beacon_recall': ('Возврат к маяку', 'Beacon Recall'), 'starfall': ('Звездопад', 'Starfall'), 'flash': ('Вспышка', 'Flash'),
}
MOBS = {
    'fallen_guardian': ('страж Цитадели, потерявший свет. Боится Копья Света.', 'a Citadel guard who lost the light. Fears the Spear of Light.'),
    'storm_spirit': ('дитя гроз. Чаще всего встречается на Грозовом пике.', 'a child of storms, common on the Storm Peak.'),
    'winged_serpent': ('хищник небес, пикирует с высоты.', 'a sky predator that dives from above.'),
    'cloud_whale': ('гигант облаков. Мирный, плывёт стаями.', 'a cloud giant. Peaceful, travels in pods.'),
    'light_wisp': ('проводник: ведёт к ближайшей святыне.', 'a guide that leads to the nearest shrine.'),
    'angel': ('житель небесных деревень. Торгует и даёт поручения.', 'a sky village dweller. Trades and gives errands.'),
    'pegasus': ('крылатый конь. Бывает белым, золотым и грозовым.', 'a winged horse: white, golden or storm-born.'),
    'cherub': ('маленький помощник, собирает предметы.', 'a tiny helper that gathers items.'),
    'golden_ram': ('его руно — золотая шерсть.', 'its fleece is golden wool.'),
    'sky_ray': ('ездовой скат, катает двоих.', 'a rideable ray that carries two.'),
    'cloud_jelly': ('пружинит при касании, роняет небесное желе.', 'bounces on touch and drops sky jelly.'),
    'mimic': ('сундук с зубами. Ищите в руинах.', 'a chest with teeth. Found in ruins.'),
    'storm_elemental': ('мини-босс Грозового пика.', 'mini-boss of the Storm Peak.'),
    'fallen_seraph': ('владыка Цитадели. На его теле знак Безликого.', 'lord of the Citadel, marked by the Faceless.'),
}
PLACES = {
    'sky_village': ('дом ангелов: торговля и доска поручений.', 'home of angels: trade and an errand board.'),
    'sky_ruins': ('остатки древнего Рая. Здесь прячутся мимики.', 'remains of ancient Heaven. Mimics hide here.'),
    'trial_tower': ('семь этажей испытаний, награда — Благодать.', 'seven floors of trials that reward Grace.'),
    'beam_temple': ('загадка лучей: направь свет зеркалами.', 'a beam puzzle: guide the light with mirrors.'),
    'cloud_castle': ('замок-данж с ловушками и стражами.', 'a dungeon castle with traps and guards.'),
    'sky_lighthouse': ('Небесный маяк: узел сети телепортов.', 'a Sky Beacon: a node of the teleport network.'),
    'airship_wreck': ('обломки галеона с добычей.', 'a galleon wreck full of loot.'),
    'citadel': ('логово Падшего Серафима.', 'lair of the Fallen Seraph.'),
}
GUIDE = [
    ('Портал в Рай: рамка из светлого камня, зажигается Сердцем Пустоты.', 'Heaven portal: a glowstone frame lit with a Void Heart.'),
    ('Благодать даётся за испытания, загадки, поручения и боссов. Трать её во вкладке «Благодать».', 'Grace comes from trials, puzzles, errands and bosses. Spend it on the Grace tab.'),
    ('Сияние — мана заклинаний. В Раю восстанавливается вдвое быстрее.', 'Radiance is spell mana. It regenerates twice as fast in Heaven.'),
    ('V — произнести заклинание, B — сменить, G — рывок, K — Кодекс.', 'V casts a spell, B cycles, G dashes, K opens the Codex.'),
    ('Солнечная линза даёт луч; зеркала и призмы поворачивает Камертон.', 'A Sun Lens emits a beam; turn mirrors and prisms with a Tuning Fork.'),
    ('Небесная кузня: ядро, 4 светлых камня вокруг и луч сверху. Алмаз → эфирит.', 'Sky Forge: a core, 4 glowstone around and a beam from above. Diamond → aetherite.'),
    ('Алтарь наделения накладывает руны на снаряжение.', 'The Imbuing Altar puts runes on gear.'),
    ('Небесные маяки связаны в сеть: нажми на маяк, чтобы выбрать цель.', 'Sky Beacons form a network: use one to pick a destination.'),
    ('Угасание растёт со временем; каждый пройденный акт его снижает.', 'The Fading grows over time; each completed act reduces it.'),
]
TABS = {'saga': ('Сага', 'Saga'), 'grace': ('Благодать', 'Grace'), 'bestiary': ('Бестиарий', 'Bestiary'),
        'places': ('Места', 'Places'), 'guide': ('Справочник', 'Guide')}


def main():
    e = {
        'codex.celestial.title': ('Кодекс Небес', 'Codex of the Heavens'),
        'codex.celestial.new_entry': ('Новая запись в Кодексе: %s', 'New Codex entry: %s'),
        'codex.celestial.grace.points': ('Благодать: %s', 'Grace: %s'),
        'codex.celestial.grace.cost': ('Цена: %s Благодати', 'Cost: %s Grace'),
        'codex.celestial.grace.requires': ('Требует: %s', 'Requires: %s'),
        'codex.celestial.branch.wings': ('Крылья', 'Wings'),
        'codex.celestial.branch.light': ('Свет', 'Light'),
        'codex.celestial.branch.might': ('Твердь', 'Might'),
        'codex.celestial.saga.act': ('Акт: %s', 'Act: %s'),
        'codex.celestial.saga.fading': ('Угасание мира: %s из 5', 'World Fading: %s of 5'),
        'codex.celestial.saga.stats': ('Благодать %s · Репутация %s · Испытаний %s · Записей %s',
                                       'Grace %s · Reputation %s · Trials %s · Entries %s'),
        'codex.celestial.saga.text.0': ('Акт I «Угасающий свет». Свет мира гаснет. Собери три осколка: Пламя (Пылающее святилище в Аду), '
                                        'Пустоту (дракон Энда или Разлом Пустоты) и Свет (Падший Серафим в Цитадели Рая) — и верни их на алтарь Цитадели.',
                                        'Act I "The Fading Light". The world\'s light is fading. Gather three shards: Flame (the Blazing Sanctuary in the Nether), '
                                        'Void (the Ender Dragon or a Void Rift) and Light (the Fallen Seraph in Heaven\'s Citadel), then return them to the Citadel altar.'),
        'codex.celestial.saga.text.1': ('Акт II «Ниже облаков». На груди Серафима был знак Безликого. На нижнем ярусе Рая открылся Разлом — '
                                        'спустись в Бездну, найди Затонувший храм с картой и одолей Пожирателя Света в его Логове. '
                                        'Держи огонь в руке: тьма Бездны сводит с ума.',
                                        'Act II "Beneath the Clouds". The Seraph bore the mark of the Faceless. A Rift has opened on Heaven\'s lowest tier: '
                                        'descend into the Abyss, find a Sunken Temple with a map and defeat the Light Devourer in its Lair. '
                                        'Keep a flame in hand: the dark of the Abyss drives you mad.'),
        'codex.celestial.saga.text.2': ('Акт II пройден. Пожиратель Света пал, Тёмное Ядро у тебя. Ядро тянет к холоду: где-то вмёрзли в лёд '
                                        'ангелы, бежавшие от Безликого. Сага продолжится в Ледяных Чертогах.',
                                        'Act II complete. The Light Devourer has fallen and the Dark Core is yours. The Core pulls toward the cold: '
                                        'somewhere, angels who fled the Faceless are frozen in ice. The saga continues in the Frozen Halls.'),
        'grace.celestial.second_wind': ('Второе дыхание спасло тебя от смерти!', 'Second Wind saved you from death!'),
        'grace.celestial.locked': ('Сначала изучи предыдущий навык', 'Learn the previous skill first'),
        'grace.celestial.not_enough': ('Нужно %s Благодати', 'Requires %s Grace'),
        'grace.celestial.learned': ('Изучено: %s', 'Learned: %s'),
        'spell.celestial.unknown': ('Это заклинание ещё не изучено', 'You have not learned this spell'),
        'spell.celestial.no_radiance': ('Не хватает Сияния', 'Not enough Radiance'),
        'spell.celestial.scouts.result': ('Светлячки нашли врагов: %s', 'Scouts found foes: %s'),
        'spell.celestial.recall.none': ('В этом мире нет Небесных маяков', 'No Sky Beacons in this world'),
        'key.category.celestial.celestial': ('Celestial', 'Celestial'),
        'key.celestial.cast': ('Произнести заклинание', 'Cast spell'),
        'key.celestial.cycle_spell': ('Сменить заклинание', 'Cycle spell'),
        'key.celestial.dash': ('Рывок', 'Dash'),
        'key.celestial.codex': ('Кодекс Небес', 'Codex of the Heavens'),
    }
    for k, (ru, en, dru, den) in SKILLS.items():
        e[f'skill.celestial.{k}'] = (ru, en)
        e[f'skill.celestial.{k}.desc'] = (dru, den)
    for k, v in SPELLS.items():
        e[f'spell.celestial.{k}'] = v
    for k, v in MOBS.items():
        e[f'codex.celestial.mob.{k}'] = v
    for k, v in PLACES.items():
        e[f'codex.celestial.place.{k}'] = v
    for i, v in enumerate(GUIDE, 1):
        e[f'codex.celestial.guide.{i}'] = v
    for k, v in TABS.items():
        e[f'codex.celestial.tab.{k}'] = v
    lang_patch(e)


if __name__ == '__main__':
    main()
