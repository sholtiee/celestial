# Celestial: передача контекста (как продолжить работу)

> Читай этот файл первым при возобновлении. Полный план 2.0: `/Users/w/.claude/plans/sprightly-petting-scone.md` (копия ключевого ниже).

## Что это
Fabric-мод **Celestial** для Minecraft **26.3** (Fabric Loader 0.19.5, Fabric API 0.161.0+26.3, Loom 1.18, Java 25).
Игра не обфусцирована: в коде имена Mojang. Проект: `~/Documents/Code/Active/Celestial`, git, коммиты на русском.
Сборка: `JAVA_HOME=/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home ./gradlew build` (у пользователя JAVA_HOME не задан).

## Цель (утверждена пользователем)
Мод уровня легендарных: Рай + 4 новых измерения (Бездна, Ледяные Чертоги, Хроноград, Астрал), сюжет «Сага Небес» из 5 актов
с двумя концовками и «Угасанием» Верхнего мира (выключается `/gamerule celestial:fading false`). Пользователь сказал «делай» — работаем волнами автономно.

## Сделано
**0.1:** Рай (3 яруса островов, 4 биома), портал из светлого камня + Сердце Пустоты, 7 мобов, босс Падший Серафим (Цитадель),
экипировка (эфирит, крылья, нимб, парашют, звёздный лук, Копьё Света), сюжет Акта I (дневник, алтарь, финал).

**Волна 0.2 «Рай преображённый», шаги 1–8 из 11 сделаны:**
1. Каркас: `data/PlayerData` (Благодать, навыки, репутация, кодекс, испытания, Сияние, поручения; Fabric attachment, синхронизируется),
   `data/WorldState` (Угасание 0–5, акт, флаги; на Верхнем мире), `data/BeaconNetwork`, правила игры `celestial:fading|meteors|fading_days`,
   пакет `network/WorldStatePayload` → `client/ClientState`, команда `/celestial status|fading|act|grace|codex|beacon|quest`.
2. Обобщение: `world/portal/PortalType(s)`, `PortalShape`, `PortalForcer`, `CelestialPortalBlock`, `PortalActivation`;
   `world/dim/CelestialDimension(s)` + `DimensionPhysics` (гравитация, выпадение в другой мир). Новое измерение = запись в `PortalTypes` и `CelestialDimensions`.
3. Рай: флора (6 цветов, травы, облачный мох, светолиана, кристальный блок), облачная ива, звёздная сосна, водопады, жеоды, корни;
   биомы Небесные сады, Грозовой пик, Звёздная поляна; трава окрашивается цветом биома; растительность ставится на все ярусы (environment_scan).
4. Существа: породы пегаса (белый/золотой/грозовой), конская броня; херувим (от Allay), златорунный баран (от Sheep), небесный скат
   (от HappyGhast), облачная медуза, мимик, Грозовой элементаль (мини-босс). Пегасу нужны ванильные теги entity_type (can_equip_saddle и др.).
5. Светотехника `light/` + `block/light/`: Солнечная линза, Световой фонарь, зеркало, призма (белое → RGB), фильтры, перископ, приёмник;
   рендер луча `client/render/BeamRenderer` (лучи маяка по сегментам). Загадки `block/puzzle/`: печать-дверь, колокола + алтарь,
   рунный пьедестал (`puzzle/Riddles`), плитки-звёзды; `puzzle/PuzzleRewards` (Благодать, кодекс, растворяет печати в радиусе 12). Камертон.
   Машины `block/machine/`: Облачный лифт, Небесная кузня (ядро + 4 светлых камня + луч сверху; алмаз → эфирит), Алтарь наделения
   (руны → 7 зачарований JSON в `data/celestial/enchantment`), Небесные маяки (меню в чате, `BeaconTravel`).
6. Испытания `trial/`: `TrialDefinition(s)`, `TrialControllerBlock(Entity)` (кристалл испытания), `TrialGoalBlock`, `VanishingCloudBlock`;
   Башня Испытаний (7 этажей) в `tools/gen_structures.py::trial_tower`.
7. Поручения `quest/` (доска, 3 в день, убей/принеси/исследуй, награды, репутация), профессии ангелов (keeper/smith/astronomer/gardener,
   скидка за репутацию), постройки: большая деревня, Храм Лучей, Облачный замок, Небесный маяк, Обломки галеона.
   Проверено в игре: постройки, загадка Храма Лучей (перископ ×3 + зеркало ×1 Камертоном), доска поручений.
   Все достопримечательности Рая — один набор `heaven_landmarks` с весами (без наложений), Цитадель — отдельно с зоной исключения.
8. Благодать `grace/`: `Skill` (17 навыков, 3 ветки), `Spell` (7 заклинаний), `Grace` (изучение, Сияние, пассивки атрибутами,
   второе дыхание), `Spells` (логика заклинаний на сервере), `CodexEvents` (записи бестиария/мест). Клиент `client/grace/`:
   `GraceClient` (клавиши V заклинание, B смена, G рывок, K Кодекс; HUD Сияния; двойной прыжок и рывок считаются на клиенте),
   `CodexScreen` (вкладки Сага/Благодать/Бестиарий/Места/Справочник). Крылья Серафима: взмахов 5 (+2/+3 от навыков).
   Переводы в `tools/gen_grace.py`. Команда `/celestial learn <навык>`. Проверено сценарием `grace_test.txt`.

## Что дальше (волна 0.2, шаги 9–11)
- **9:** Угасание v1: удлинение ночей, бонусы монстрам, метеориты (сущность + кратер со звёздным кварцем), Тени в Верхнем мире,
  Звездочёт (жители, телескоп), сюжетные места: Звёздная обсерватория, Пылающее святилище (Ад), Разломы Пустоты (Энд). Переделка Акта I.
- **10:** переделка Серафима (модель с 4 крыльями, кристаллы-лекари на арене), свой звук `tools/gen_sounds.py` (numpy + ffmpeg).
- **11:** полировка, README, `.jar`.
Затем волны 0.3 Бездна → 0.4 Ледяные Чертоги → 0.5 Хроноград → 0.6 Астрал (финал, две концовки) → 1.0.

## Репозиторий
Приватный GitHub: `sholtiee/celestial` (ветка `main`). После каждого шага: коммит + `git push`.
**Отложенная задача (попросил пользователь):** оформить репозиторий: описание, темы, README с картинками и GIF
(скриншоты автопилота из `run/screenshots`), лицензия (сейчас All-Rights-Reserved в fabric.mod.json), CHANGELOG по волнам,
GitHub Actions уже собирает `.jar` (`.github/workflows/build.yml` из шаблона Fabric; проверить, что он работает на Java 25), релизы с `.jar`.

## Как устроен проект
- Java: `src/main/java/dev/celestial/**` (общее), `src/client/java/dev/celestial/client/**` (рендер, автопилот).
- Ресурсы **генерируются**: `tools/build_assets.sh` = gen_assets → gen_flora → gen_mechanics → gen_world → gen_structures → gen_story.
  Переводы ru/en собираются там же: gen_assets перезаписывает lang, остальные дописывают через `gen_story.lang_patch`.
  Новые теги дописываются к существующим файлам (см. конец gen_flora/gen_mechanics).
- Ванильные исходники и ресурсы для справки: `.mcsrc/{common,client,assets}` (в .gitignore; создаются через `./gradlew genSources` и распаковку jar).

## Проверка без ручного управления
- `tools/devserver.sh "cmd" sleep:N ...`: dev-сервер, команды через RCON (пароль `celestial-dev`), ошибки регистров ловит сам.
- `tools/render_map.py`: карта Рая из region-файлов → `build/heaven_map.png`.
- `tools/fresh_save.sh`: копирует run/world в сейв `test` (творческий режим, читы).
- `tools/autopilot.sh tools/scenarios/X.txt`: клиент без звука проходит сценарий, скриншоты в `run/screenshots`.
  Шаги: `/команда`, `wait N`, `shot имя`, `use X Y Z грань`, `userel dx dy dz грань`, `useitem`, `hold jump|forward|… N`,
  `fly`, `goto <structure> dx dy dz yaw pitch`, `camera front|back|first`, `togglehud`, `clearchat`, `closescreen`, `pos`,
  `press cast|cycle|dash|codex` (клавиши мода), `codex <вкладка>`, `quit`.
  Подводные камни: в выживании игрок дотягивается на 4,5 блока; после смерти автопилот сам возрождает; `/gamerule advance_time` (не doDaylightCycle).
- `tools/contact.py out.png a.png b.png ...`: склейка скриншотов.

## Особенности API 26.3 (уже наступали)
Окрашивание: `BlockColorRegistry.register(List.of(BlockTintSources.grass()), block)`. Лут: `condition` / `modifier`, а не conditions/functions.
Порядок фич должен быть одинаковым во всех биомах (`FEATURE_ORDER` в gen_world). `environment_scan.max_steps` ≤ 32. Feature — record + MapCodec,
регистрируется в `BuiltInRegistries.FEATURE_TYPE`. Позиционирование: `pose.rotateDegrees(Axis.XP, deg)`. Время: `getOverworldClockTime()`.
Скорость игрока с сервера: `entity.needsSync = true`. Скрыт ли HUD: `mc.gui.hud.isHidden()`.
Аргумент команды с `:` — `StringArgumentType.greedyString()` (word() не пускает двоеточие). Сущности блоков в шаблонах: в NBT нужен `id` (например `celestial:beam_source`).
