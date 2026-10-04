#!/bin/bash
# QA-фузз: в каждом измерении призывает по 5 каждой сущности мода, гонит 5 минут /tick sprint,
# затем MSPT и количество выживших. Ищем краши, исключения, лаги, размножение/исчезновение.
# Запуск: tools/qa/fuzz_server.sh  → лог build/fuzz.log, сводка в stdout
cd "$(dirname "$0")/../.."
ENTS="fallen_guardian storm_spirit winged_serpent cloud_whale light_wisp angel pegasus fallen_seraph cherub golden_ram sky_ray cloud_jelly mimic storm_elemental shadow blind_hunter light_eater deep_worm frost_wraith light_devourer"
ARGS=()
yfor() { case $1 in minecraft:overworld) echo 100;; celestial:heaven) echo 150;; celestial:abyss) echo 70;; *) echo 120;; esac; }  # bash 3.2: без ассоц. массивов
X=0
for dim in minecraft:overworld celestial:heaven celestial:abyss celestial:frozen_halls; do
	X=$((X + 400))
	ARGS+=("execute in $dim run forceload add $((X-48)) -48 $((X+48)) 48")
	ARGS+=("sleep:8")
	for e in $ENTS; do
		for i in 1 2 3 4 5; do
			ARGS+=("execute in $dim run summon celestial:$e $((X + RANDOM % 40 - 20)) $(yfor $dim) $((RANDOM % 40 - 20))")
		done
	done
done
ARGS+=("tick query" "tick sprint 6000" "sleep:150" "tick query")
X=0
for dim in minecraft:overworld celestial:heaven celestial:abyss celestial:frozen_halls; do
	X=$((X + 400))
	for e in $ENTS; do
		ARGS+=("execute in $dim positioned $X $(yfor $dim) 0 if entity @e[type=celestial:$e,distance=..200]")
	done
	ARGS+=("execute in $dim positioned $X $(yfor $dim) 0 if entity @e[type=item,distance=..200]")
	ARGS+=("execute in $dim run kill @e[type=!player,distance=..300,x=$X,y=$(yfor $dim),z=0]")
	ARGS+=("execute in $dim run forceload remove all")
done
LOG=build/fuzz.log tools/devserver.sh "${ARGS[@]}"
