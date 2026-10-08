#!/bin/bash
# Пересобирает все сгенерированные ресурсы мода в правильном порядке.
set -e
cd "$(dirname "$0")"
python3 gen_assets.py
python3 gen_flora.py
python3 gen_mechanics.py
python3 gen_world.py
python3 gen_structures.py
python3 gen_story.py
python3 gen_grace.py
python3 gen_fading.py
python3 gen_places.py
python3 gen_boss.py
python3 gen_abyss.py
python3 gen_starlight.py
python3 gen_abyss_mobs.py
python3 gen_abyss_gear.py
python3 gen_abyss_boss.py
python3 gen_polish.py
python3 gen_particles.py
python3 gen_frozen.py
python3 gen_frozen_puzzles.py
python3 gen_frozen_mobs.py
python3 gen_archon.py
python3 gen_frozen_places.py
python3 gen_puzzles_c.py
python3 gen_heaven_mobs.py
python3 gen_archangels.py
python3 gen_lore.py
python3 gen_eden.py
python3 gen_achievements.py
python3 gen_animated.py
python3 gen_tags_lang.py
