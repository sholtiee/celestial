#!/usr/bin/env python3
"""Статический линтер ресурсов Celestial (без запуска игры).

Ищет то, что игрок увидит как «нет текстуры», «сырой ключ перевода», z-fighting,
пустой дроп и т.п. Печатает находки с кодом проверки; код выхода 1, если есть находки.
Запуск: python3 tools/qa/lint_assets.py [--only CODE]
"""
import json
import os
import re
import sys
from collections import defaultdict
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, 'src/main/resources')
A = os.path.join(RES, 'assets/celestial')
D = os.path.join(RES, 'data/celestial')
JAVA = [os.path.join(ROOT, 'src/main/java'), os.path.join(ROOT, 'src/client/java')]
NS = 'celestial'

findings = defaultdict(list)


def report(code, msg):
    findings[code].append(msg)


def load(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        report('JSON_BROKEN', f'{os.path.relpath(path, ROOT)}: {e}')
        return None


def walk_json(base):
    for dirpath, _, files in os.walk(base):
        for f in files:
            if f.endswith('.json'):
                yield os.path.join(dirpath, f)


def split_id(ref, default_ns=NS):
    ref = ref.lstrip('#')
    if ':' in ref:
        ns, path = ref.split(':', 1)
    else:
        ns, path = 'minecraft', ref
    return ns, path


def own(ref):
    return isinstance(ref, str) and split_id(ref)[0] == NS


def model_path(ref):
    return os.path.join(A, 'models', split_id(ref)[1] + '.json')


def texture_path(ref):
    return os.path.join(A, 'textures', split_id(ref)[1] + '.png')


# ---------------------------------------------------------------- Java-реестр
def java_sources():
    for base in JAVA:
        for dirpath, _, files in os.walk(base):
            for f in files:
                if f.endswith('.java'):
                    p = os.path.join(dirpath, f)
                    with open(p, encoding='utf-8') as fh:
                        yield p, fh.read()


SOURCES = list(java_sources())
ALL_JAVA = '\n'.join(s for _, s in SOURCES)


def registered_blocks():
    """name -> (has_item, no_loot, unbreakable) из ModBlocks.java."""
    src = open(os.path.join(ROOT, 'src/main/java/dev/celestial/registry/ModBlocks.java'), encoding='utf-8').read()
    out = {}
    # каждая регистрация: от register*("name" до следующей ';' верхнего уровня (грубо: до ");\n")
    for m in re.finditer(r'(registerNoItem|register|flower)\("([a-z0-9_]+)"(.*?)\);\s*\n', src, re.S):
        kind, name, body = m.groups()
        if kind == 'flower':
            body += ' noOcclusion PLANT'
        # ofFullCopy(X) наследует свойства другого блока мода
        copy = re.search(r'ofFullCopy\(([A-Z_]+)\)', body)
        if copy and copy.group(1).lower() in out:
            body += out[copy.group(1).lower()][3]
        out[name] = (kind != 'registerNoItem', 'noLootTable' in body, 'strength(-1' in body or 'ofFullCopy(Blocks.BEDROCK' in body, body)
    return out


def registered_items():
    src = open(os.path.join(ROOT, 'src/main/java/dev/celestial/registry/ModItems.java'), encoding='utf-8').read()
    return set(re.findall(r'register\(\s*"([a-z0-9_]+)"', src))


def registered_entities():
    p = os.path.join(ROOT, 'src/main/java/dev/celestial/registry/ModEntities.java')
    return set(re.findall(r'"([a-z0-9_]+)"', open(p, encoding='utf-8').read())) if os.path.exists(p) else set()


BLOCKS = registered_blocks()
ENTITIES = registered_entities()
# яйца призыва регистрируются циклом в ModEntities: name + "_spawn_egg"
SPAWN_EGGS = {e + '_spawn_egg' for e in re.findall(r'register\(\s*"([a-z0-9_]+)"', open(os.path.join(ROOT, 'src/main/java/dev/celestial/registry/ModEntities.java')).read())} \
    if '_spawn_egg' in open(os.path.join(ROOT, 'src/main/java/dev/celestial/registry/ModEntities.java')).read() else set()
ITEMS = registered_items() | {n for n, v in BLOCKS.items() if v[0]} | SPAWN_EGGS
# служебные блоки построек — в выживании не добываются намеренно
STRUCTURE_ONLY = {'trial_crystal', 'trial_goal', 'vanishing_cloud', 'sealed_door', 'bell_altar', 'rune_pedestal', 'star_tile', 'seraph_seal', 'devourer_seal'}


# ---------------------------------------------------------------- модели и текстуры
def check_models():
    seen_models = set()

    def check_model(ref, origin):
        if not own(ref):
            return
        p = model_path(ref)
        if p in seen_models:
            return
        seen_models.add(p)
        if not os.path.exists(p):
            report('MODEL_MISSING', f'{origin} -> {ref}')
            return
        m = load(p)
        if not m:
            return
        if 'parent' in m:
            check_model(m['parent'], ref)
        textures = m.get('textures', {})
        for key, tex in textures.items():
            if isinstance(tex, str) and not tex.startswith('#') and own(tex):
                if not os.path.exists(texture_path(tex)):
                    report('TEXTURE_MISSING', f'{ref} [{key}] -> {tex}')
        check_elements(ref, m)

    for f in os.listdir(os.path.join(A, 'blockstates')):
        bs = load(os.path.join(A, 'blockstates', f))
        if not bs:
            continue
        for ref in re.findall(r'"model":\s*"([^"]+)"', json.dumps(bs)):
            check_model(ref, 'blockstate ' + f)
        name = f[:-5]
        if name not in BLOCKS:
            report('BLOCKSTATE_ORPHAN', f'blockstates/{f}: блок не зарегистрирован')
    for name in BLOCKS:
        if not os.path.exists(os.path.join(A, 'blockstates', name + '.json')):
            report('BLOCKSTATE_MISSING', f'{name}: нет blockstates/{name}.json -> пурпурный куб')
    items_dir = os.path.join(A, 'items')
    for f in os.listdir(items_dir):
        it = load(os.path.join(items_dir, f))
        if not it:
            continue
        for ref in re.findall(r'"model":\s*"([^"]+)"', json.dumps(it)):
            check_model(ref, 'item ' + f)
    for name in sorted(ITEMS):
        if not os.path.exists(os.path.join(items_dir, name + '.json')):
            report('ITEM_MODEL_MISSING', f'{name}: нет items/{name}.json -> пурпурный куб в руке')
    # непривязанные модели — не ошибка игры, пропускаем


def face_rect(el, face):
    (x1, y1, z1), (x2, y2, z2) = el['from'], el['to']
    planes = {'north': ('z', z1), 'south': ('z', z2), 'west': ('x', x1), 'east': ('x', x2), 'down': ('y', y1), 'up': ('y', y2)}
    axis, value = planes[face]
    if axis == 'z':
        rect = (min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2))
    elif axis == 'x':
        rect = (min(z1, z2), max(z1, z2), min(y1, y2), max(y1, y2))
    else:
        rect = (min(x1, x2), max(x1, x2), min(z1, z2), max(z1, z2))
    return axis, value, rect


def check_elements(ref, m):
    els = m.get('elements') or []
    for i, el in enumerate(els):
        for c in el.get('from', []) + el.get('to', []):
            if c < -16 or c > 32:
                report('ELEMENT_OUT_OF_RANGE', f'{ref} элемент {i}: координата {c} вне [-16,32]')
        for face, fd in (el.get('faces') or {}).items():
            uv = fd.get('uv')
            if uv and any(u < 0 or u > 16 for u in uv):
                report('UV_OUT_OF_RANGE', f'{ref} элемент {i} {face}: uv {uv} -> битая/шахматная текстура')
            if uv and (uv[0] == uv[2] or uv[1] == uv[3]):
                report('UV_ZERO_AREA', f'{ref} элемент {i} {face}: uv {uv} нулевой площади')
    # z-fighting: две грани разных элементов в одной плоскости, смотрят в одну сторону и перекрываются
    if any('rotation' in e for e in els):
        rotated = {i for i, e in enumerate(els) if 'rotation' in e}
    else:
        rotated = set()
    for (i, a), (j, b) in combinations(enumerate(els), 2):
        if i in rotated or j in rotated:
            continue
        for face in set(a.get('faces', {})) & set(b.get('faces', {})):
            # приём «оверлей» (как у ванильной травы): второй слой с tintindex рисуется поверх — не баг
            if ('tintindex' in a['faces'][face]) != ('tintindex' in b['faces'][face]):
                continue
            ax, av, ra = face_rect(a, face)
            _, bv, rb = face_rect(b, face)
            if abs(av - bv) > 1e-6:
                continue
            ox = min(ra[1], rb[1]) - max(ra[0], rb[0])
            oy = min(ra[3], rb[3]) - max(ra[2], rb[2])
            if ox > 1e-6 and oy > 1e-6:
                report('Z_FIGHTING', f'{ref}: элементы {i} и {j}, грань {face} в плоскости {ax}={av} перекрываются {ox:g}x{oy:g}')


def check_textures():
    from PIL import Image
    tex_root = os.path.join(A, 'textures')
    for dirpath, _, files in os.walk(tex_root):
        for f in files:
            if not f.endswith('.png'):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, tex_root)
            try:
                im = Image.open(p)
                w, h = im.size
            except Exception as e:  # noqa: BLE001
                report('TEXTURE_BROKEN', f'{rel}: {e}')
                continue
            mcmeta = p + '.mcmeta'
            if rel.startswith(('block/', 'item/')):
                if h != w and not os.path.exists(mcmeta):
                    report('TEXTURE_NOT_SQUARE', f'{rel}: {w}x{h} без .mcmeta -> растянется/битая анимация')
                if os.path.exists(mcmeta) and h % w:
                    report('ANIM_FRAMES', f'{rel}: высота {h} не кратна ширине {w}')
                if w & (w - 1):
                    report('TEXTURE_NOT_POW2', f'{rel}: ширина {w} не степень 2 -> мипмапы ломают атлас')
                im = im.convert('RGBA')
                px = im.getdata()
                if all(a == 0 for *_, a in px):
                    report('TEXTURE_EMPTY', f'{rel}: полностью прозрачная -> невидимый блок/предмет')
                # пурпурно-чёрная шахматка — признак плейсхолдера
                magenta = sum(1 for r, g, b, a in px if a and r > 200 and g < 40 and b > 200)
                if magenta > len(px) * 0.2:
                    report('TEXTURE_PLACEHOLDER', f'{rel}: {magenta} пурпурных пикселей — похоже на заглушку')


def check_block_transparency():
    """Полупрозрачная текстура на блоке без cutout/translucent -> чёрные дыры вместо прозрачности."""
    from PIL import Image
    for name, (has_item, no_loot, unbreakable, body) in BLOCKS.items():
        bs_path = os.path.join(A, 'blockstates', name + '.json')
        if not os.path.exists(bs_path):
            continue
        refs = set(re.findall(r'"model":\s*"([^"]+)"', open(bs_path).read()))
        for ref in refs:
            if not own(ref) or not os.path.exists(model_path(ref)):
                continue
            m = json.load(open(model_path(ref)))
            parent = m.get('parent', '')
            full = parent.split('/')[-1] in ('cube_all', 'cube', 'cube_column', 'cube_bottom_top', 'cube_column_horizontal', 'leaves') \
                or (not parent and any(e.get('from') == [0, 0, 0] and e.get('to') == [16, 16, 16] for e in m.get('elements', [])))
            if not full or 'noOcclusion' in body or 'leavesProperties' in body:
                continue
            for key, tex in (m.get('textures') or {}).items():
                if not isinstance(tex, str) or tex.startswith('#') or not own(tex) or not os.path.exists(texture_path(tex)) or 'overlay' in key + tex:
                    continue
                im = Image.open(texture_path(tex)).convert('RGBA')
                alphas = [a for *_, a in im.getdata()]
                holes = sum(1 for a in alphas if a == 0)
                translucent = sum(1 for a in alphas if 0 < a < 255)
                if holes or translucent:
                    report('ALPHA_ON_OPAQUE', f'{name}: полный непрозрачный блок, но {tex} имеет {holes} дыр и {translucent} полупрозрачных пикс. -> сквозь блок видно пустоту/x-ray, соседние грани отсечены')


# ---------------------------------------------------------------- частицы и звуки
def check_particles_sounds():
    pdir = os.path.join(A, 'particles')
    if os.path.isdir(pdir):
        for f in os.listdir(pdir):
            p = load(os.path.join(pdir, f))
            for t in (p or {}).get('textures', []):
                if own(t) and not os.path.exists(os.path.join(A, 'textures/particle', split_id(t)[1] + '.png')):
                    report('PARTICLE_TEXTURE_MISSING', f'particles/{f} -> {t}')
    sounds = load(os.path.join(A, 'sounds.json')) or {}
    for event, spec in sounds.items():
        for s in spec.get('sounds', []):
            name = s if isinstance(s, str) else s.get('name')
            if isinstance(s, dict) and s.get('type') == 'event':
                continue
            if own(name) and not os.path.exists(os.path.join(A, 'sounds', split_id(name)[1] + '.ogg')):
                report('SOUND_MISSING', f'{event} -> {name} (тишина + ошибка в логе)')
    used = set(re.findall(r'"celestial:([a-z0-9_./]+)"', ALL_JAVA))
    for m in re.finditer(r'SoundEvent\w*\s+(\w+)\s*=\s*\w+\("([a-z0-9_.]+)"', ALL_JAVA):
        if m.group(2) not in sounds:
            report('SOUND_EVENT_UNDEFINED', f'{m.group(1)} = "{m.group(2)}" нет в sounds.json')


# ---------------------------------------------------------------- переводы
def check_lang():
    ru = load(os.path.join(A, 'lang/ru_ru.json')) or {}
    en = load(os.path.join(A, 'lang/en_us.json')) or {}
    for k in sorted(set(ru) - set(en)):
        report('LANG_EN_MISSING', k)
    for k in sorted(set(en) - set(ru)):
        report('LANG_RU_MISSING', k)
    for k, v in ru.items():
        if isinstance(v, str) and re.search(r'[A-Za-z]{4,}', v) and not re.search(r'[А-Яа-яЁё]', v) and v != 'Celestial':
            report('LANG_RU_UNTRANSLATED', f'{k} = {v!r}')
    for k, v in en.items():
        if isinstance(v, str) and re.search(r'[А-Яа-яЁё]', v):
            report('LANG_EN_CYRILLIC', f'{k} = {v!r}')
        if k in ru and isinstance(v, str):
            # число аргументов %s/%d должно совпадать, иначе в игре «%s» или краш форматирования
            if len(re.findall(r'%(?:\d+\$)?[sd]', v)) != len(re.findall(r'%(?:\d+\$)?[sd]', ru[k])):
                report('LANG_ARGS_MISMATCH', f'{k}: en {v!r} / ru {ru[k]!r}')
    keys = set(ru) | set(en)
    for name in BLOCKS:
        if BLOCKS[name][0] and f'block.{NS}.{name}' not in keys:
            report('LANG_NAME_MISSING', f'block.{NS}.{name}')
    blocks_with_item = {n for n, v in BLOCKS.items() if v[0]}
    for name in registered_items():
        if f'item.{NS}.{name}' not in keys and name not in blocks_with_item:
            report('LANG_NAME_MISSING', f'item.{NS}.{name}')
    # теги предметов мода: перевод tag.item.<ns>.<путь> (его показывают EMI/REI и Fabric предупреждает при запуске, BUG-038)
    tag_dir = os.path.join(D, 'tags/item')
    if os.path.isdir(tag_dir):
        for dp, _, files in os.walk(tag_dir):
            for f in files:
                if f.endswith('.json'):
                    path = os.path.relpath(os.path.join(dp, f), tag_dir)[:-5].replace(os.sep, '.')
                    if f'tag.item.{NS}.{path}' not in keys:
                        report('LANG_TAG_MISSING', f'tag.item.{NS}.{path}')
    # литералы translatable("...") в коде
    for path, src in SOURCES:
        for k in re.findall(r'translatable\("([a-z0-9_.]+)"\)', src):
            if k not in keys and not k.startswith(('key.', 'gui.', 'options.', 'chat.', 'container.')):
                report('LANG_KEY_UNKNOWN', f'{k}  ({os.path.relpath(path, ROOT)})')
        # префиксы с конкатенацией: проверяем, что вообще есть хоть один ключ с этим префиксом
        for k in re.findall(r'translatable\("([a-z0-9_.]+\.)"\s*\+', src):
            if not any(x.startswith(k) for x in keys):
                report('LANG_PREFIX_UNKNOWN', f'{k}*  ({os.path.relpath(path, ROOT)})')


# ---------------------------------------------------------------- данные
def all_ids_in(obj):
    s = json.dumps(obj)
    return re.findall(r'"#?celestial:([a-z0-9_/]+)"', s)


def check_data():
    loot_dir = os.path.join(D, 'loot_table')
    # дроп блоков: ломаемый блок без таблицы лута -> ничего не выпадает
    for name, (has_item, no_loot, unbreakable, body) in BLOCKS.items():
        p = os.path.join(loot_dir, 'blocks', name + '.json')
        if not no_loot and not unbreakable and not os.path.exists(p) and 'dropsLike' not in body:
            report('BLOCK_NO_DROP', f'{name}: ломается, но нет loot_table/blocks/{name}.json -> пропадает при добыче')
    known = ITEMS | set(BLOCKS) | ENTITIES
    for p in walk_json(D):
        rel = os.path.relpath(p, D)
        obj = load(p)
        if obj is None:
            continue
        if rel.startswith(('loot_table', 'recipe', 'advancement', 'trade_set', 'villager_trade')):
            for m in re.finditer(r'"(item|id|result|block|name)":\s*"celestial:([a-z0-9_]+)"', json.dumps(obj)):
                if m.group(2) not in known:
                    report('DATA_UNKNOWN_ID', f'{rel}: {m.group(1)}=celestial:{m.group(2)}')
        if rel.startswith('tags/'):
            for v in obj.get('values', []):
                ref = v if isinstance(v, str) else v.get('id')
                if not own(ref) or ref.startswith('#'):
                    continue
                kind = rel.split('/')[1]
                path = split_id(ref)[1]
                ok = {'block': path in BLOCKS, 'item': path in ITEMS, 'entity_type': path in ENTITIES}.get(kind, True)
                if not ok and kind in ('block', 'item', 'entity_type'):
                    report('TAG_UNKNOWN_ID', f'{rel}: {ref}')
    # рецепт, дающий предмет, которого нет в игре, ловится выше; предметы без способа получения
    obtainable = set()
    for p in walk_json(D):
        obtainable.update(all_ids_in(load(p) or {}))
    for name in sorted(ITEMS - STRUCTURE_ONLY - SPAWN_EGGS):
        if name not in obtainable and not re.search(rf'\b{name.upper()}\b', re.sub(r'register\("[^"]+"', '', ALL_JAVA).replace('ModItems.' + name.upper() + ' =', '')):
            report('ITEM_UNOBTAINABLE', f'{name}: не упомянут ни в данных, ни в коде кроме регистрации')


def check_lore():
    """Летопись (docs/LORE.md): переводы ru/en на всё, паритет ключей и «у каждого листа есть способ открыться» (S6.1).

    Способ открыться ищем в коде и данных: Lore.unlock(..., "id"), свиток {sheet:"id"} в лут-таблицах, `Sheet` скрижали в шаблонах.
    Листы, которым нужен ещё не написанный движок сцен (Отблески, пролог, видения, беседы), и подвиги из PENDING печатаются отдельно и не считаются находками.
    """
    import gzip
    import sys as _sys
    _sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import lore_data as L
    data = load(os.path.join(D, 'lore/lore.json'))
    if not data:
        report('LORE_DATA', 'нет data/celestial/lore/lore.json')
        return
    ru = load(os.path.join(A, 'lang/ru_ru.json')) or {}
    en = load(os.path.join(A, 'lang/en_us.json')) or {}
    for key in ru:  # одинаковые плейсхолдеры (%s, %d) в обоих языках
        if key in en and len(re.findall(r'%[sd]', ru[key])) != len(re.findall(r'%[sd]', en[key])):
            report('LANG_PLACEHOLDERS', f'{key}: число %s/%d в ru и en разное')
    for key in sorted({k for k in ru if k.startswith('lore.celestial.')} ^ {k for k in en if k.startswith('lore.celestial.')}):
        report('LORE_LANG_PARITY', f'{key}: есть только в одном языке')
    for sh in data['sheets']:
        p = f"lore.celestial.sheet.{sh['id']}"
        need = ['.title', '.how', '.ref'] + (['.quote'] if sh['has_quote'] else []) + [f'.{k}' for k, f in (('s', 'has_s'), ('a', 'has_a'), ('t', 'has_t')) if sh[f]]
        for suffix in need:
            if p + suffix not in ru or p + suffix not in en:
                report('LORE_LANG_MISSING', f'{p + suffix}')
        if not (sh['has_s'] or sh['has_a'] or sh['has_t']):
            report('LORE_EMPTY_SHEET', f"{sh['id']}: ни «Писания», ни «Апокрифа», ни «Предания»")
        if not os.path.exists(os.path.join(A, f"textures/gui/lore/{sh['art']}.png")):
            report('LORE_NO_ART', f"{sh['id']}: нет картинки {sh['art']}")
        for g in sh['gloss']:
            if g not in data['glossary']:
                report('LORE_BAD_GLOSSARY', f"{sh['id']}: слово {g} не в Глоссарии")
    for g in data['glossary']:
        for suffix in ('', '.who', '.here'):
            if f'lore.celestial.gloss.{g}{suffix}' not in ru:
                report('LORE_LANG_MISSING', f'lore.celestial.gloss.{g}{suffix}')
    json_text = ''
    for dirpath, _, files in os.walk(D):
        for f in files:
            if f.endswith('.json'):
                with open(os.path.join(dirpath, f), encoding='utf-8') as fh:
                    json_text += fh.read()
    nbt_bytes = b''
    for dirpath, _, files in os.walk(os.path.join(D, 'structure')):
        for f in files:
            if f.endswith('.nbt'):
                with open(os.path.join(dirpath, f), 'rb') as fh:
                    try:
                        nbt_bytes += gzip.decompress(fh.read())
                    except OSError:
                        pass
    pending = []
    for sh in data['sheets']:
        i = sh['id']
        found = bool(re.search(rf'unlock\([^)]*"{i}"', ALL_JAVA)) or (sh['src'] == 'scroll' and f'sheet:\\"{i}\\"' in json_text) \
            or (sh['src'] == 'tablet' and i.encode() in nbt_bytes)
        scenes = load(os.path.join(D, 'memory/scenes.json')) or {}
        found = found or any(sc.get('sheet') == i and sid.encode() in nbt_bytes for sid, sc in scenes.items())  # Отблеск с якорем в постройке
        if found:
            continue
        if sh['src'] in ('glimpse', 'prologue', 'vision', 'conv') or i in getattr(L, 'PENDING', {}):
            pending.append(f"{i} ({sh['src']}{': ' + L.PENDING[i] if i in getattr(L, 'PENDING', {}) else ''})")
        else:
            report('LORE_NO_OPENER', f"{i}: источник «{sh['src']}», но в коде и данных способа открыть нет")
    if pending:
        print('Листы Летописи, ждущие движка сцен или своей волны (не находки): ' + ', '.join(pending))


def check_scenes():
    """Отблески (data/celestial/memory/scenes.json): шаблон сцены есть, шаги известны, актёры в шагах существуют, переводы на месте,
    у сцены есть Отпечаток света хоть в одной постройке (иначе её не пережить без команды)."""
    import gzip
    scenes = load(os.path.join(D, 'memory/scenes.json'))
    if scenes is None:
        return
    ru = load(os.path.join(A, 'lang/ru_ru.json')) or {}
    en = load(os.path.join(A, 'lang/en_us.json')) or {}
    known = {'wait', 'near', 'look', 'move', 'face', 'pose', 'hold', 'say', 'voice', 'particles', 'dim', 'spawn', 'entity', 'despawn', 'end'}
    nbt_bytes = b''
    for dirpath, _, files in os.walk(os.path.join(D, 'structure')):
        for f in files:
            if f.endswith('.nbt') and 'memory' not in dirpath:
                with open(os.path.join(dirpath, f), 'rb') as fh:
                    try:
                        nbt_bytes += gzip.decompress(fh.read())
                    except OSError:
                        pass
    for sid, sc in scenes.items():
        ns, path = sc['stage'].split(':')
        if not os.path.exists(os.path.join(D, 'structure', path + '.nbt')):
            report('SCENE_NO_STAGE', f'{sid}: нет шаблона {sc["stage"]}')
        actors = {a['id'] for a in sc['actors']}
        def lang(key):
            if key not in ru or key not in en:
                report('SCENE_LANG_MISSING', f'{sid}: {key}')
        lang(sc['thought']) if sc.get('thought') else None
        for st in sc['steps']:
            t = st['t']
            if t not in known:
                report('SCENE_BAD_STEP', f'{sid}: шаг {t}')
            if t == 'spawn':
                actors.add(st['actor']['id'])
            if t == 'entity' and 'id' in st:
                actors.add(st['id'])
            if 'actor' in st and isinstance(st['actor'], str) and st['actor'] not in actors:
                report('SCENE_BAD_ACTOR', f'{sid}: шаг {t} — нет актёра {st["actor"]}')
            if t in ('say', 'voice'):
                lang(st['key'])
            if t == 'say':
                lang('memory.celestial.who.' + st['actor'])
        if sid.encode() not in nbt_bytes:
            report('SCENE_NO_ANCHOR', f'{sid}: нет Отпечатка света (memory_anchor с Scene) ни в одной постройке')


CHECKS = [check_models, check_textures, check_block_transparency, check_particles_sounds, check_lang, check_data, check_lore, check_scenes]


def main():
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    for check in CHECKS:
        try:
            check()
        except Exception as e:  # noqa: BLE001
            report('LINTER_CRASH', f'{check.__name__}: {e!r}')
    total = 0
    for code in sorted(findings):
        if only and code != only:
            continue
        items = findings[code]
        total += len(items)
        print(f'\n== {code} ({len(items)})')
        for msg in items:
            print('  ' + msg)
    print(f'\nИтого находок: {total}')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
