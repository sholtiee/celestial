#!/bin/bash
# Headless-проверка мода: запускает dev-сервер, выполняет команды через RCON и останавливает его.
# Аргумент "sleep:N" ждёт N секунд. Пример:
#   tools/devserver.sh "execute in celestial:heaven run forceload add -128 -128 127 127" sleep:40
set -u
cd "$(dirname "$0")/.."
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home}
LOG=${LOG:-build/devserver.log}
mkdir -p build
./gradlew runServer --no-configuration-cache -q --args=nogui > "$LOG" 2>&1 < /dev/null &
until grep -qE "RCON running|BUILD FAILED|Exception in|Crash|Failed to load registries" "$LOG" 2>/dev/null; do sleep 1; done
if grep -qE "Failed to load registries|Crash" "$LOG"; then
	echo "!!! сервер не запустился:"; grep -E "Failed to parse|Caused by" "$LOG" | head -20
	pkill -f KnotServer; exit 1
fi
for cmd in "$@"; do
	case "$cmd" in
		sleep:*) sleep "${cmd#sleep:}" ;;
		*) python3 tools/rcon.py "$cmd" ;;
	esac
done
python3 tools/rcon.py "save-all flush" "stop" > /dev/null
for _ in $(seq 60); do pgrep -f KnotServer >/dev/null || break; sleep 1; done
grep -E "ERROR|Exception|FATAL" "$LOG" | grep -v "Dev warning" | head -20
exit 0
