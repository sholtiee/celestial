#!/bin/bash
# Запускает dev-клиент без звука, проигрывает сценарий автопилота и ждёт выхода.
#   tools/autopilot.sh tools/scenarios/heaven_tour.txt
set -u
cd "$(dirname "$0")/.."
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home}
export CELESTIAL_AUTOPILOT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
SAVE=${SAVE:-test}
sed -i '' -E 's/^(soundCategory_[a-z_]+):.*/\1:0.0/' run/options.txt 2>/dev/null
mkdir -p build
rm -rf run/screenshots
./gradlew runClient --no-configuration-cache -q --args="--quickPlaySingleplayer $SAVE" > build/client.log 2>&1 < /dev/null &
GRADLE_PID=$!
# сторож: если игра упала при загрузке или зависла — гасим через ${TIMEOUT:-420} с
for _ in $(seq ${TIMEOUT:-420}); do
	kill -0 $GRADLE_PID 2>/dev/null || break
	if grep -qE "Failed to load registries|Crash report|Exception in thread \"Render thread\"" build/client.log; then
		echo "!!! клиент упал при загрузке"; break
	fi
	sleep 1
done
pkill -f KnotClient 2>/dev/null
wait $GRADLE_PID 2>/dev/null
grep -E "Автопилот|ERROR|Exception" build/client.log | grep -v "Realms\|SignedJWT" | head -40
ls run/screenshots 2>/dev/null
