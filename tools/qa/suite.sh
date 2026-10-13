#!/bin/bash
# Набор сценариев подряд на одном сейве (S6.3 — сквозной прогон): tools/qa/suite.sh [--fresh] сценарий1 сценарий2 …
# После каждого сценария в чат пишется /celestial status (акт, Угасание). Логи — build/suite/<сценарий>.log,
# сводка — build/suite/report.md (tools/qa/suite_report.py: метки «TEST … expect=pass|fail» против «Проверка пройдена/неуспешна»).
set -u
cd "$(dirname "$0")/../.."
if [ "${1:-}" = "--fresh" ]; then
	shift
	rm -rf run/world && tools/fresh_save.sh
fi
mkdir -p build/suite
rm -f build/suite/*.log
for name in "$@"; do
	src=tools/scenarios/$name.txt
	tmp=tools/scenarios/_suite_$name.txt
	grep -v '^quit$' "$src" > "$tmp"
	printf '/celestial status\nwait 10\nquit\n' >> "$tmp"
	TIMEOUT=${TIMEOUT:-1500} tools/autopilot.sh "$tmp" > /dev/null 2>&1
	cp build/client.log "build/suite/$name.log"
	rm -f "$tmp"
	echo "прогон: $name"
done
python3 tools/qa/suite_report.py "$@"
