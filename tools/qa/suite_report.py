"""Сводка прогона tools/qa/suite.sh: по каждому сценарию — проверки с ожиданием (expect=pass|fail) и их исход,
прочие «Проверка пройдена/неуспешна», исключения в логе, строка /celestial status в конце. Пишет build/suite/report.md."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR = os.path.join(ROOT, 'build/suite')
NOISE = ('Realms', 'SignedJWT', 'sessionserver', 'SocketTimeout', 'astral_void', 'authlib', 'UnknownHost', 'Services are unavailable')


def analyse(name):
    path = os.path.join(DIR, name + '.log')
    if not os.path.exists(path):
        return None
    lines = [ln for ln in open(path, encoding='utf-8', errors='replace') if 'Server thread' not in ln]
    checks, loose, pending, errors, status = [], 0, None, [], []
    for ln in lines:
        m = re.search(r'\[CHAT\] \[[^\]]+\] TEST (.*)', ln)
        if m:
            pending = m.group(1).strip()
            continue
        r = re.search(r'Проверка (пройдена|неуспешна)', ln)
        if r:
            ok = r.group(1) == 'пройдена'
            if pending:
                exp = re.search(r'expect=(pass|fail)', pending)
                want = exp.group(1) == 'pass' if exp else True
                checks.append((pending, ok == want, ok))
                pending = None
            else:
                loose += 1
        if ('Exception' in ln or '/ERROR]' in ln) and not any(n in ln for n in NOISE):
            errors.append(ln.strip()[:200])
        if re.search(r'Акт|акт[: ]|Угасание', ln) and '[CHAT]' in ln:
            status.append(ln.split('[CHAT]', 1)[1].strip())
    return checks, loose, errors, status[-3:]


def main(names):
    out = ['# Сквозной прогон', '']
    total_bad = 0
    for name in names:
        res = analyse(name)
        if res is None:
            out.append(f'## {name}\nлога нет\n')
            total_bad += 1
            continue
        checks, loose, errors, status = res
        bad = [c for c in checks if not c[1]]
        total_bad += len(bad) + len(errors)
        out.append(f'## {name}: {len(checks) - len(bad)}/{len(checks)} проверок по ожиданию, ещё {loose} без метки, ошибок в логе {len(errors)}')
        out += [f'- ✗ {c[0]} (вышло: {"пройдена" if c[2] else "неуспешна"})' for c in bad]
        out += [f'- ошибка: {e}' for e in errors[:5]]
        out += [f'- статус: {s}' for s in status]
        out.append('')
    os.makedirs(DIR, exist_ok=True)
    with open(os.path.join(DIR, 'report.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 1 if total_bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
