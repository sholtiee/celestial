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
