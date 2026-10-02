#!/usr/bin/env python3
"""Склеивает скриншоты в сетку 2×N: python3 tools/contact.py out.png a.png b.png ..."""
import sys
from PIL import Image

out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size
rows = (len(ims) + 1) // 2
sheet = Image.new('RGB', (w * 2, h * rows))
for i, im in enumerate(ims):
    sheet.paste(im.resize((w, h)), ((i % 2) * w, (i // 2) * h))
sheet.thumbnail((1600, 450 * rows))
sheet.save(out)
