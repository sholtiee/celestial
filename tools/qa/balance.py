"""Таблица баланса (S6.2): металлы по актам и существа — из исходников, в docs/BALANCE.md. Проверяет, что тиры металлов растут по актам.

Запуск: python3 tools/qa/balance.py  (печатает нарушения кривой; код возврата 1, если они есть)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'src/main/java/dev/celestial')
ITEMS = open(os.path.join(SRC, 'registry/ModItems.java'), encoding='utf-8').read()

# металл → акт, имена констант
TIERS = [('Эфирит', 1, 'ETHERITE'), ('Бездновый обсидиан', 2, 'ABYSSAL'), ('Морозная сталь', 3, 'FROST'), ('Хронит', 4, 'CHRONITE'),
         ('Целестит', 5, 'CELESTITE')]
VANILLA = {'Алмаз': (1561, 8.0, 3.0, 20, 2.0, 0.0), 'Незерит': (2031, 9.0, 4.0, 20, 3.0, 0.1)}
# существа → акт (для кривой: обычные мобы и боссы)
MOBS = {1: ['FallenGuardian', 'WingedSerpent', 'StormSpirit', 'Shadow', 'Mimic', 'StormElemental'], 2: ['BlindHunter', 'DeepWorm', 'LightEater', 'Nephilim'],
        3: ['FrostWraith', 'IceGuardian'], 4: ['ClockworkSentry', 'BrassDoll', 'WinderBeetle', 'Ophanim'], 5: ['StarDevourer']}
BOSSES = [('FallenSeraph', 1), ('LightDevourer', 2), ('FrostArchon', 3), ('Clockmaker', 4), ('Faceless', 5)]


def tool(const):
    m = re.search(rf'{const}_TOOL = new ToolMaterial\([^,]+, (\d+), ([\d.]+)F, ([\d.]+)F', ITEMS)
    return int(m.group(1)), float(m.group(2)), float(m.group(3))


def armor(const):
    m = re.search(rf'{const}_ARMOR = new ArmorMaterial\((\d+),\s*Map\.of\(([^)]*)\),\s*\d+, [\w.]+, ([\d.]+)F, ([\d.]+)F', ITEMS, re.S)
    pts = dict(re.findall(r'ArmorType\.(\w+), (\d+)', m.group(2)))
    total = sum(int(pts[k]) for k in ('HELMET', 'CHESTPLATE', 'LEGGINGS', 'BOOTS'))
    return int(m.group(1)), total, float(m.group(3)), float(m.group(4))


def mob(name):
    for sub in ('entity', 'boss', 'fading'):
        path = os.path.join(SRC, sub, name + '.java')
        if os.path.exists(path):
            t = open(path, encoding='utf-8').read()
            g = lambda a: (re.search(rf'Attributes\.{a}, ([\d.]+)', t) or [None, '—'])[1]  # noqa: E731
            return g('MAX_HEALTH'), g('ATTACK_DAMAGE'), g('ARMOR')
    return '?', '?', '?'


def main():
    out = ['# Баланс (генерируется `tools/qa/balance.py`, руками не править)', '',
           '## Металлы по актам', '', '| Металл | Акт | Прочность | Скорость | Урон+ | Броня (сумма) | Прочность брони ×25 | Твёрдость | Отбрасывание |',
           '|---|---|---|---|---|---|---|---|---|']
    for name, (dur, spd, dmg, _, tough, kb) in VANILLA.items():
        out.append(f'| {name} (ваниль) | — | {dur} | {spd} | {dmg} | 20 | — | {tough} | {kb} |')
    rows, problems = [], []
    for name, act, const in TIERS:
        t, a = tool(const), armor(const)
        rows.append((act, t, a))
        out.append(f'| {name} | {act} | {t[0]} | {t[1]} | {t[2]} | {a[1]} | {a[0]} | {a[2]} | {a[3]} |')
    for (a1, t1, r1), (a2, t2, r2) in zip(rows, rows[1:]):
        if not (t2[0] >= t1[0] and t2[1] >= t1[1] and t2[2] >= t1[2] and r2[0] >= r1[0] and r2[1] >= r1[1] and r2[2] >= r1[2]):
            problems.append(f'металл акта {a2} не сильнее металла акта {a1}')
    out += ['', '## Существа по актам', '', '| Акт | Существо | Здоровье | Урон | Броня |', '|---|---|---|---|---|']
    for act, names in MOBS.items():
        for n in names:
            hp, dmg, arm = mob(n)
            out.append(f'| {act} | {n} | {hp} | {dmg} | {arm} |')
    out += ['', '## Боссы', '', '| Акт | Босс | Здоровье | Урон | Броня |', '|---|---|---|---|---|']
    prev = 0
    for n, act in BOSSES:
        hp, dmg, arm = mob(n)
        out.append(f'| {act} | {n} | {hp} | {dmg} | {arm} |')
        if float(hp) <= prev:
            problems.append(f'босс акта {act} не крепче предыдущего')
        prev = float(hp)
    with open(os.path.join(ROOT, 'docs/BALANCE.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    for p in problems:
        print('BALANCE:', p)
    print('ok: docs/BALANCE.md,', len(problems), 'нарушений кривой')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
