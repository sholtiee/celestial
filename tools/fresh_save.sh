#!/bin/bash
# Копирует run/world в run/saves/test (творческий режим, читы) для автопилота.
# Если мира нет — сначала генерирует его dev-сервером.
set -e
cd "$(dirname "$0")/.."
[ -d run/world ] || tools/devserver.sh > /dev/null
rm -rf run/saves/test && mkdir -p run/saves && cp -R run/world run/saves/test && rm -f run/saves/test/session.lock
python3 - <<'PY'
import nbtlib
f = nbtlib.load('run/saves/test/level.dat'); d = f['Data']
d['allowCommands'] = nbtlib.Byte(1); d['GameType'] = nbtlib.Int(1); d['LevelName'] = nbtlib.String('test')
f.save()
PY
echo "сейв test готов"
