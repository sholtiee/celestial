#!/bin/bash
# Собирает карту-выставку run/showcase (плоский творческий мир) dev-сервером и копирует её в run/saves/showcase.
set -e
cd "$(dirname "$0")/.."
python3 tools/gen_showcase.py
cp run/server.properties build/server.properties.bak
trap 'cp build/server.properties.bak run/server.properties' EXIT
sed -i '' -E 's/^level-name=.*/level-name=showcase/; s/^level-type=.*/level-type=minecraft\\:flat/; s/^gamemode=.*/gamemode=creative/; s/^force-gamemode=.*/force-gamemode=true/' run/server.properties
sed -i '' -E 's/^generate-structures=.*/generate-structures=false/' run/server.properties
rm -rf run/showcase
tools/devserver.sh "@build/showcase_cmds.txt"
rm -rf run/saves/showcase && mkdir -p run/saves && cp -R run/showcase run/saves/showcase && rm -f run/saves/showcase/session.lock
python3 - <<'PY'
import nbtlib
f = nbtlib.load('run/saves/showcase/level.dat'); d = f['Data']
d['allowCommands'] = nbtlib.Byte(1); d['GameType'] = nbtlib.Int(1); d['LevelName'] = nbtlib.String('Celestial Showcase')
f.save()
PY
echo "карта готова: run/saves/showcase"
