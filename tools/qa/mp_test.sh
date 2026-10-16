#!/bin/bash
# Мультиплеер: dev-сервер + два клиента (Alpha ведёт tools/scenarios/mp_alpha.txt, Beta — mp_beta.txt), оба по имени в офлайн-режиме.
# Логи: build/mp_server.log, build/mp_alpha.log, build/mp_beta.log; кадры — run/screenshots/mp_*.png.
set -u
cd "$(dirname "$0")/../.."
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home}
sed -i '' -E 's/^(soundCategory_[a-z_]+):.*/\1:0.0/' run/options.txt 2>/dev/null
rm -rf run/screenshots
./gradlew runServer --no-configuration-cache -q --args=nogui > build/mp_server.log 2>&1 < /dev/null &
until grep -qE "RCON running|BUILD FAILED|Crash" build/mp_server.log 2>/dev/null; do sleep 1; done
python3 tools/rcon.py "whitelist off" > /dev/null  # на dev-сервере включён белый список (имена в офлайне в него не добавляются)
client() {  # имя, сценарий
	CELESTIAL_AUTOPILOT="$(pwd)/tools/scenarios/$2" ./gradlew runClient --no-configuration-cache -q \
		--args="--quickPlayMultiplayer localhost:25565 --username $1" > "build/mp_$(echo "$1" | tr A-Z a-z).log" 2>&1 < /dev/null &
}
client Alpha mp_alpha.txt
sleep 25
client Beta mp_beta.txt
for _ in $(seq 240); do  # оба на сервере → операторы
	if python3 tools/rcon.py "list" 2>/dev/null | grep -q "Beta" && python3 tools/rcon.py "list" | grep -q "Alpha"; then
		python3 tools/rcon.py "op Alpha" "op Beta" > /dev/null
		echo "оба игрока на сервере"
		break
	fi
	sleep 1
done
for _ in $(seq ${TIMEOUT:-900}); do
	pgrep -f KnotClient > /dev/null || break
	if grep -qE "lost connection|Disconnecting" build/mp_server.log; then  # клиент выкинут — он так и будет висеть на экране отключения
		echo "!!! игрок отключён:"; grep -E "lost connection" build/mp_server.log | head -3; break
	fi
	sleep 1
done
pkill -f KnotClient 2>/dev/null
python3 tools/rcon.py "save-all flush" "stop" > /dev/null
for _ in $(seq 60); do pgrep -f KnotServer >/dev/null || break; sleep 1; done
grep -hE "Проверка|TEST|ERROR|Exception" build/mp_alpha.log | grep -v "Server thread\|Realms\|SignedJWT\|authlib\|Services are\|UnknownHost" | head -40
grep -E "ERROR|Exception" build/mp_server.log | grep -v "astral_void" | head -10
ls run/screenshots 2>/dev/null
