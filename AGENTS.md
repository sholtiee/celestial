# Celestial — руководство для агента

> Прочитай целиком перед работой. Затем — `HANDOFF.md` (текущий статус и что делать дальше) и `docs/PLAN.md` (общий план 2.0).
> Этот файл описывает **как** работать в проекте, HANDOFF — **что** сейчас делается.

## 1. Что это за проект
Fabric-мод **Celestial** для Minecraft **26.3**: измерение Рая, сюжет «Сага Небес» из 5 актов, механика «Угасания»
обычного мира, будущие измерения (Бездна, Ледяные Чертоги, Хроноград, Астрал). Цель пользователя — мод уровня
легендарных (Aether, Twilight Forest): контента больше, чем в ванилле, и сюжет, который влияет на обычную игру.

- Стек: Minecraft 26.3 (**не обфусцирован**, в коде имена Mojang), Fabric Loader 0.19.5, Fabric API 0.161.0+26.3,
  Loom 1.18-SNAPSHOT, Java 25. Пакет `dev.celestial`, id мода `celestial`.
- Репозиторий: приватный GitHub `sholtiee/celestial`, ветка `main`. Релизы помечаются тегами (`v0.2.0`).

## 2. Пользователь и правила работы
- Пишет по-русски, отвечать по-русски, кратко. Коммиты — на русском, с подробным телом.
- Пользователь разрешил работать **автономно волнами**: «делай», «продолжай». Не спрашивать по мелочам, решать самому.
- После каждого законченного шага: сборка → проверка в игре (автопилот) → коммит → `git push` → обновить `HANDOFF.md`.
- **Звук в dev-клиенте выключен** (просьба пользователя): `tools/autopilot.sh` сам ставит все `soundCategory_*` в 0
  в `run/options.txt`. Не включать. Запускать клиент можно.
- **Чужие ассеты не используем.** Все текстуры, модели, постройки, звуки генерируются скриптами из `tools/`.
  От ванильных развёрток можно брать только форму (альфа-канал), рисунок — свой. Ванильные текстуры не перекрашивать.
- Отложено пользователем (не делать без просьбы): оформление репозитория (README с картинками, лицензия, релизы, CI).

## 3. Окружение
- Сборка: `JAVA_HOME=/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home ./gradlew build`
  (у пользователя JAVA_HOME не задан). Jar: `build/libs/celestial-<версия>.jar`. Версия — `gradle.properties`.
- Python 3.13 + Pillow, nbtlib, numpy, soundfile (`pip3 install --user soundfile`; ffmpeg в системе без libvorbis).
- `.mcsrc/` (в .gitignore) — ванильные исходники и ресурсы для справки и для генераторов. Если папки нет:
  `tools/setup_mcsrc.sh`. Искать API так: `grep -rn "метод" .mcsrc/common/net/minecraft/...`.

## 4. Устройство кода
`src/main/java/dev/celestial/` — общее (сервер+клиент), `src/client/java/dev/celestial/client/` — только клиент.

| Пакет | Что внутри |
|---|---|
| `Celestial.java` | точка входа: порядок `init()` всех систем |
| `registry/` | ModBlocks, ModItems, ModEntities, ModBlockEntities, ModSounds, ModEffects, ModFeatures, ModGameRules, ModCreativeTab |
| `data/` | `PlayerData` (Благодать, навыки, репутация, кодекс, испытания, Сияние, поручения — Fabric attachment, синхр. с клиентом), `WorldState` (Угасание, акт, флаги — attachment на Верхнем мире), `CelestialData` (доступ/обновление), `BeaconNetwork` |
| `world/` | `HeavenDimension`, `portal/` (PortalType(s), PortalShape, PortalForcer, CelestialPortalBlock), `dim/` (CelestialDimension(s), DimensionPhysics — гравитация и выпадение) |
| `entity/` | мобы Рая, босс `FallenSeraph` (+`SeraphCrystal`), снаряды |
| `fading/` | Угасание: `Fading`, `Meteor(s)`, `Shadow`, `Stargazer` (профессия), `TelescopeBlock` |
| `grace/` | Благодать: `Skill`, `Spell`, `Grace`, `Spells`, `CodexEvents`, пакеты |
| `light/`, `block/light/` | светотехника (лучи, зеркала, призмы, приёмники) |
| `block/puzzle/`, `puzzle/` | загадки и награды (`PuzzleRewards.solved`) |
| `block/machine/` | кузня, алтарь наделения, лифт, маяки |
| `trial/` | движок испытаний (`TrialDefinitions` — список испытаний) |
| `quest/` | поручения ангелов |
| `story/` | `Story` (главы = достижения), `StoryEvents`, `Finale` |
| `command/` | `/celestial status|fading|act|grace|codex|learn|meteor|beacon|quest` |
| `client/` | рендеры (`render/`), HUD и Кодекс (`grace/`), автопилот (`dev/AutoPilot`), миксины (`mixin/`) |

## 5. Ресурсы генерируются — руками JSON не править
`tools/build_assets.sh` запускает по порядку: gen_assets → gen_flora → gen_mechanics → gen_world → gen_structures →
gen_story → gen_grace → gen_fading → gen_places → gen_boss. Повторный запуск без изменений не даёт диффа.
- `gen_assets.py` — база: блоки, предметы, мобы (текстуры через `mob_textures.py`, `textures.py`), лут, рецепты.
  **Перезаписывает** lang-файлы; все остальные скрипты дописывают переводы через `gen_story.lang_patch({ключ: (ru, en)})`.
- `gen_world.py` — измерение Рая (тип, шумы, биомы, фичи). `gen_structures.py` — постройки Рая (класс `Template` → .nbt).
- `gen_places.py` — постройки Угасания в ванильных мирах + Звездочёт. `gen_sounds.py` — звук (НЕ входит в build_assets,
  запускать вручную: ogg каждый раз чуть другие).
- Новые теги дописываются к существующим файлам (см. `add_tag` в gen_fading.py).

### Как добавить…
- **Блок**: `ModBlocks.register(...)` + текстура/модель/blockstate/лут/перевод в генераторе (`simple_cube`, `self_drop`), теги инструмента.
- **Моба**: класс в `entity/`, `ModEntities.register` (создаёт и яйцо), атрибуты в `ModEntities.init`, рендер в
  `client/render/CelestialRenderers`, текстура (`mob_textures.humanoid` и т.п.), лут `entity_loot`, перевод, спавн в биоме.
  Новый моб автоматически попадёт в Кодекс при убийстве; добавь его в список `MOBS` в `CodexScreen` и описание `codex.celestial.mob.<id>`.
- **Постройку**: функция-шаблон на `Template` + `jigsaw()/structure_set()` (см. gen_places.py), тег `codex_places`.
  Сущности блоков в шаблоне требуют `id` в NBT. Испытание: блок `celestial:trial_crystal` с NBT `{'Trial': '<id>'}` +
  запись в `TrialDefinitions` + лут `chests/trial_<id>`. Печати `sealed_door` в радиусе 10 открываются после успеха.
- **Измерение**: запись в `world/dim/CelestialDimensions` (+ `PortalTypes`, если портал-рамка) и генератор по образцу gen_world.py.
- **Навык/заклинание**: `grace/Skill`, `grace/Spell` + логика в `Spells`, переводы в gen_grace.py.
- **Звук**: синтез в gen_sounds.py (`SOUNDS`), событие в `ModSounds`, субтитр в gen_boss.py.

## 6. Проверка (обязательна перед коммитом)
1. `./gradlew build` без ошибок.
2. `tools/devserver.sh "команда" sleep:N ...` — dev-сервер + RCON (пароль `celestial-dev`): ловит ошибки регистров и датапака.
3. **Автопилот**: `tools/autopilot.sh tools/scenarios/<сценарий>.txt` — клиент проходит сценарий, скриншоты в `run/screenshots`,
   лог в `build/client.log` (`grep -E "CHAT|Автопилот|Exception" build/client.log`). Склейка: `python3 tools/contact.py out.png a.png b.png`.
   Шаги сценария: `/команда`, `wait N`, `shot имя`, `use X Y Z грань`, `userel dx dy dz грань`, `usenear <id блока>`,
   `interact <id сущности>`, `useitem`, `hold jump|forward|back|left|right|sneak|attack|use N`, `press cast|cycle|dash|codex`,
   `codex <вкладка>`, `fly`, `goto <структура> dx dy dz yaw pitch`, `camera front|back|first`, `togglehud`, `clearchat`,
   `closescreen`, `pos`, `quit`. Сейв для тестов — `run/saves/test` (`tools/fresh_save.sh`).
   Подводные камни: тестовый сейв накапливает состояние (акт, Угасание, игрок может оказаться в другом измерении —
   в начале сценария явно телепортируйся `execute in <мир> run tp`); `goto` ищет структуру в текущем измерении игрока;
   в выживании дотягиваешься на 4,5 блока; без опоры мобы и игрок падают в пустоту Рая; `TIMEOUT=600` для долгих сценариев.
4. `tools/render_map.py` — карта Рая сверху (для ландшафта).
5. **QA-инструменты** (`tools/qa/`): `lint_assets.py` (ресурсы без запуска игры — должен печатать «Итого находок: 0»),
   `scan_world.py [--dim celestial/heaven ...]` (читает region-файлы `run/saves/test`: радуги, швы по чанкам, висящие растения, водопады в пустоту),
   `fuzz_server.sh` (все мобы × 4 измерения на dev-сервере). Сценарии проверок: `qa_critical`, `qa_high`, `qa_high2`, `qa_sanctum`, `qa_parkour`,
   `qa_riddle`, `qa_hud`, `qa_visual_fix`, `qa_bypass`, `qa_showroom` (все блоки/предметы/мобы), `qa_flyover` (облёт измерений). Реестр багов — `docs/BUGS.md`.
   Чтобы перегенерировать измерение после правок генерации: `rm -rf run/saves/test/dimensions/celestial/<dim>` и `qa_regen*.txt`.
   Результаты проверок в сценариях — строки «Проверка пройдена/неуспешна» после метки `/say TEST ...` в чате (`build/client.log`).

## 6a. Головоломки и защита от обходов
- Награда за загадку — **Реликварий** (`block/puzzle/ReliquaryBlock`): неразрушим, не контейнер, открывается, только когда в радиусе 8 нет `sealed_door`.
  В шаблонах: `reliquary(t, x, y, z, loot)` из `gen_structures.py` (не `chest`).
- Родные источники и приёмники света в шаблонах ставятся со свойством `sealed=True`: приёмник принимает только луч родного источника,
  не ломается, не перекрашивается Камертоном и сам растворяет примыкающие печати. Свои фонарь/приёмник игрока загадку не решают.
- `SealedDoorBlock` на красный камень не реагирует. Открывают: `PuzzleRewards.solved` (колокола, плитки, пьедестал), победа в испытании, `sealed`-приёмник.
- Испытание-паркур: `trial/TrialGuard` (нельзя строить рядом) + провал при телепорте/элитрах/езде/левитации.
- Ошибки на рунном пьедестале: `puzzle/Attempts` (блокировка 20 с, удваивается).
- Мобов испытаний и призывов боссов помечай `Darkness.NO_REPEL`, иначе Оберег их удалит.
- Новая загадка с объёмом (зал, лабиринт, арена): её `BlockEntity` реализует `puzzle/PuzzleZone` — пока не решена, `PuzzleZoneGuard` запрещает
  в объёме ставить блоки и лить вёдра (не в творческом). Блоки, по которым кликают (колокол, глыба), реализуют `PuzzleInteractive` — клик с блоком в руке проходит.
  Шаблоны залов заполняй явным воздухом (`t.fill(..., 'minecraft:air')`), иначе рельеф затекает внутрь.
Скриншоты смотреть самому (Read по png) — это основной способ убедиться, что всё выглядит правильно.

## 7. Особенности API 26.3 (на них уже наступали)
- Лут-таблицы: `condition` / `modifier` (не conditions/functions). Порядок фич одинаков во всех биомах (`FEATURE_ORDER`),
  иначе «Feature order cycle». `environment_scan.max_steps` ≤ 32. Feature — record + MapCodec в `BuiltInRegistries.FEATURE_TYPE`.
- Окрашивание: `BlockColorRegistry.register(List.of(BlockTintSources.grass()), block)`.
- Время: `level.getOverworldClockTime()`; скорость часов — `ServerClockManager.setRate`; команда `/time of minecraft:overworld query time`.
- Скорость игрока с сервера: `player.needsSync = true` (hurtMarked нет). `randomTeleport(x,y,z,particles, state -> false)`.
- GUI: `Screen.extractRenderState(GuiGraphicsExtractor, mx, my, a)`, `graphics.text/fill/centeredText`; HUD:
  `HudElementRegistry.attachElementAfter`; скрыт ли HUD — `mc.gui.hud.isHidden()`; клавиши — скан-коды SDL
  (V=25, B=5, G=10, K=14, W=26, space=44), `KeyMappingHelper.registerKeyMapping`, `KeyMapping.Category(Identifier)`.
- Рендер: отрисовка **отложенная** (`SubmitNodeCollector.submitModel`) — `setupAnim` вызывается позже, позу модели задавай
  в своём `setupAnim` (см. `SeraphRenderer.WingPair`). Вращения: `pose.rotateDegrees(Axis.XP, deg)`.
- Аргумент команды с `:` — `StringArgumentType.greedyString()`. Профессии: `VillagerProfession` record + `PoiHelper.register`,
  сделки data-driven (`trade_set`, `villager_trade`, теги `villager_trade/...`), создаются лениво.
- `EndCrystal.hurtServer` final и взрывается — для своих кристаллов писать свою сущность. Гравитация 0 у снаряда + вода = застревает.
- `/place structure` для jigsaw кладёт шаблон от угла чанка. Энтити-теги для ездовых мобов: `can_equip_saddle` и др.
- Ogg для игры — моно (позиционный звук), через soundfile/libsndfile.
