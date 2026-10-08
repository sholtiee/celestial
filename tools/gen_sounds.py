"""Свой звук Celestial: синтез на numpy → ogg (soundfile/libsndfile). Музыка Рая, битвы с Серафимом, пластинка и эффекты.

Запуск: python3 tools/gen_sounds.py (долго: ~1 мин). Пишет assets/celestial/sounds/**.ogg и sounds.json.
Каждый звук детерминирован (фиксированное зерно), поэтому повторный запуск не меняет файлы, если не менялся код.
"""
import json
import os

import numpy as np
import soundfile as sf  # pip3 install --user soundfile

SR = 32000
ROOT = os.path.join(os.path.dirname(__file__), '..', 'src', 'main', 'resources', 'assets', 'celestial')
OUT = os.path.join(ROOT, 'sounds')


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def note(n):
    """MIDI → Гц."""
    return 440.0 * 2 ** ((n - 69) / 12)


def env(length, a=0.01, d=0.1, s=0.7, r=0.2):
    n = length
    out = np.ones(n) * s
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = max(1, min(ai, n)); out[:ai] = np.linspace(0, 1, ai)
    di = max(1, min(di, n - ai)); out[ai:ai + di] = np.linspace(1, s, di)
    ri = max(1, min(ri, n)); out[-ri:] *= np.linspace(1, 0, ri)
    return out


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # однополюсный фильтр (медленно, но звуки короткие)
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lowpass_fast(x, cutoff):
    """Фильтр для длинной музыки: свёртка с окном-ядром."""
    width = max(3, int(SR / cutoff))
    k = np.hanning(width)
    k /= k.sum()
    return np.convolve(x, k, mode='same')


def reverb(x, mix=0.35, room=0.75):
    out = x.copy()
    for delay, gain in ((0.0297, 0.8), (0.0371, 0.77), (0.0411, 0.74), (0.0437, 0.71), (0.089, 0.5), (0.131, 0.4)):
        d = int(delay * SR)
        y = np.zeros(len(x) + d * 12)
        y[:len(x)] = x
        for k in range(1, 12):
            g = (gain * room) ** k
            if g < 0.01:
                break
            y[d * k:d * k + len(x)] += x * g
        out = out + y[:len(x)] * mix / 4
    return out


def pad(freq, sec, detune=0.004, bright=1500):
    t = t_axis(sec)
    w = np.zeros_like(t)
    for d in (-detune, 0, detune):
        f = freq * (1 + d)
        w += 2 * (t * f % 1) - 1  # пила
    w = lowpass_fast(w / 3, bright)
    return w * env(len(t), a=sec * 0.3, d=0.1, s=1.0, r=sec * 0.4)


def bell(freq, sec=2.5, amp=1.0):
    t = t_axis(sec)
    partials = ((1, 1.0), (2.76, 0.5), (5.4, 0.25), (8.93, 0.12))
    w = sum(a * np.sin(2 * np.pi * freq * p * t) * np.exp(-t * (2.5 + p)) for p, a in partials)
    return amp * w


def place(track, sound, at):
    i = int(at * SR)
    end = min(len(track), i + len(sound))
    track[i:end] += sound[:end - i]


def normalize(x, peak=0.85):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def save(name, x, quality=4):
    """Моно Ogg Vorbis через libsndfile (ffmpeg без libvorbis кодирует только стерео, а позиционный звук должен быть моно)."""
    path = os.path.join(OUT, name + '.ogg')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.clip(normalize(x), -1, 1), SR, format='OGG', subtype='VORBIS',
             compression_level=1.0 - quality / 10)


# ---------------------------------------------------------------- музыка
def heaven_music(seed, chords, bpm=60, bars=24, root=60):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    track = np.zeros(int(bar * bars * SR + SR * 4))
    for b in range(bars):
        ch = chords[b % len(chords)]
        for n in ch:
            place(track, pad(note(root + n - 12), bar * 1.25, bright=900) * 0.22, b * bar)
        # колокольчики-арпеджио, разреженные
        for s in range(8):
            if rng.random() < 0.45:
                n = ch[rng.integers(len(ch))] + 12 * rng.integers(1, 3)
                place(track, bell(note(root + n), 3.0, 0.18), b * bar + s * beat / 2)
    return reverb(track, 0.5, 0.85)


def battle_music(seed, bars=32, bpm=132):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    track = np.zeros(int(bar * bars * SR + SR * 3))
    prog = [(0, 3, 7), (-4, 0, 3), (-2, 2, 5), (-5, -1, 2)]  # Am – F – G – E
    root = 57
    t_k = t_axis(0.35)
    kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-t_k * 30)) * t_k) * np.exp(-t_k * 9)
    t_s = t_axis(0.25)
    snare = rng.standard_normal(len(t_s)) * np.exp(-t_s * 18) * 0.5 + np.sin(2 * np.pi * 190 * t_s) * np.exp(-t_s * 25) * 0.4
    for b in range(bars):
        ch = prog[(b // 2) % len(prog)]
        for n in ch:
            place(track, pad(note(root + n), bar * 1.05, detune=0.006, bright=2200) * 0.2, b * bar)
        bass = pad(note(root + ch[0] - 24), bar, detune=0.002, bright=500) * 0.45
        place(track, bass, b * bar)
        intensity = min(1.0, b / 8)
        for s in range(4):
            place(track, kick * 0.8, b * bar + s * beat)
            if s % 2 == 1:
                place(track, snare * intensity, b * bar + s * beat)
            if b >= 8:
                place(track, snare * 0.25, b * bar + s * beat + beat / 2)
        if b >= 4:  # тревожная мелодия колоколов
            for s in range(8):
                if rng.random() < 0.6:
                    n = ch[rng.integers(len(ch))] + 12
                    place(track, bell(note(root + n), 1.2, 0.22), b * bar + s * beat / 2)
    return reverb(track, 0.25, 0.6)


def choir(seed, sec=100):
    rng = np.random.default_rng(seed)
    chords = [(0, 4, 7, 11), (-3, 0, 4, 7), (-7, -3, 0, 4), (-5, -1, 2, 7)]
    track = np.zeros(int(sec * SR) + SR * 6)
    seg = 6.0
    for i in range(int(sec / seg)):
        ch = chords[i % len(chords)]
        for n in ch:
            t = t_axis(seg * 1.4)
            f = note(60 + n)
            vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6)
            v = sum(np.sin(2 * np.pi * f * k * vib * t) / k ** 1.4 for k in range(1, 7))
            # «а-а»: формантный подъём ~800 Гц
            v = v + 0.3 * np.sin(2 * np.pi * 800 * t) * np.sin(2 * np.pi * f * t)
            place(track, v * env(len(t), a=2.0, d=0.5, s=0.9, r=2.5) * 0.15, i * seg)
        if rng.random() < 0.7:
            place(track, bell(note(84 + ch[rng.integers(4)]), 4.0, 0.12), i * seg + 1.5)
    return reverb(track, 0.6, 0.9)


def abyss_music(seed, sec=110):
    """Бездна: низкий гул, медленно дрейфующие кластеры, редкие далёкие колокола и «капли»."""
    rng = np.random.default_rng(seed)
    track = np.zeros(int(sec * SR) + SR * 6)
    t = t_axis(sec)
    drone = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) / (i + 1) for i, f in enumerate((36.7, 55.0, 73.4)))
    drone *= 0.5 + 0.5 * np.sin(2 * np.pi * t / 23.0) ** 2
    place(track, lowpass_fast(drone, 220) * 0.6, 0)
    clusters = [(-12, -11, -5), (-10, -7, -3), (-14, -9, -8), (-12, -5, -4)]
    for i in range(int(sec / 9)):
        for n in clusters[i % len(clusters)]:
            place(track, pad(note(57 + n), 12.0, detune=0.009, bright=600) * 0.12, i * 9)
    for _ in range(int(sec / 7)):
        at = rng.random() * sec
        place(track, bell(note(rng.choice([69, 72, 76, 81])), 5.0, 0.06), at)
        tt = t_axis(0.3)
        place(track, np.sin(2 * np.pi * (1800 - 900 * tt / 0.3) * tt) * np.exp(-tt * 18) * 0.05, rng.random() * sec)  # капля
    return reverb(track, 0.7, 0.92)


def devourer_battle(seed, bars=36, bpm=118):
    """Битва с Пожирателем: тяжёлый пульс, «рёв» низкой пилы, хор-кластеры, ускорение к концу."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    track = np.zeros(int(bar * bars * SR + SR * 3))
    root = 50
    prog = [(0, 1, 7), (0, 3, 6), (-2, 1, 5), (-4, 0, 3)]
    tk = t_axis(0.5)
    kick = np.sin(2 * np.pi * (40 + 90 * np.exp(-tk * 25)) * tk) * np.exp(-tk * 6)
    ts = t_axis(0.3)
    hit = rng.standard_normal(len(ts)) * np.exp(-ts * 14) * 0.6 + np.sin(2 * np.pi * 140 * ts) * np.exp(-ts * 20) * 0.5
    for b in range(bars):
        ch = prog[(b // 2) % len(prog)]
        for n in ch:
            place(track, pad(note(root + n), bar * 1.05, detune=0.012, bright=1200) * 0.18, b * bar)
        growl = pad(note(root + ch[0] - 24), bar, detune=0.02, bright=320) * 0.5
        place(track, growl, b * bar)
        for st in range(8 if b >= 20 else 4):
            step = beat * (0.5 if b >= 20 else 1)
            place(track, kick * 0.9, b * bar + st * step)
        place(track, hit * 0.8, b * bar + beat)
        place(track, hit * 0.8, b * bar + beat * 3)
        if b >= 8 and b % 2 == 0:
            for k in range(3):
                place(track, bell(note(root + 24 + ch[k]), 1.6, 0.18), b * bar + k * beat / 2)
    return reverb(track, 0.3, 0.7)


def frozen_music(seed, sec=120):
    """Ледяные Чертоги: вой ветра, хрустальные арпеджио (лидийский лад), высокое мерцание и редкий глухой «треск» ледника."""
    rng = np.random.default_rng(seed)
    track = np.zeros(int(sec * SR) + SR * 6)
    t = t_axis(sec)
    wind = lowpass_fast(rng.standard_normal(len(t)), 900) - lowpass_fast(rng.standard_normal(len(t)), 120)
    wind *= 0.25 + 0.75 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 17.0 + 1.3)) ** 3
    place(track, wind * 0.35, 0)
    scale = [0, 2, 4, 6, 7, 9, 11, 12, 14, 16]  # лидийский от ре
    root = 62
    for i in range(int(sec / 12)):
        chord = [(0, 4, 7), (2, 6, 9), (-3, 2, 7), (-5, 2, 6)][i % 4]
        for n in chord:
            place(track, pad(note(root - 12 + n), 14.0, detune=0.005, bright=900) * 0.09, i * 12)
        for k in range(10):  # арпеджио «сосулек»
            n = scale[rng.integers(0, len(scale))] + 12
            place(track, bell(note(root + n), 3.0, 0.07 + 0.03 * rng.random()), i * 12 + 1.0 + k * 1.05 + rng.random() * 0.2)
    for _ in range(int(sec / 15)):  # далёкий треск ледника
        tt = t_axis(1.5)
        crack = lowpass(rng.standard_normal(len(tt)), 700) * np.exp(-tt * 3) * 0.3
        place(track, crack, rng.random() * sec)
    shimmer = sum(np.sin(2 * np.pi * note(root + 36 + n) * t + rng.random() * 6) for n in (0, 7, 14)) * 0.012
    place(track, shimmer * (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.0)), 0)
    return reverb(track, 0.75, 0.93)


def archon_battle(seed, bars=40, bpm=140):
    """Битва с Морозным Архонтом: стеклянное остинато, тяжёлый пульс, метель-шум, хор-кластеры; с 24-го такта — вдвое плотнее."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = beat * 4
    track = np.zeros(int(bar * bars * SR + SR * 3))
    root = 57
    prog = [(0, 3, 7), (-4, 0, 3), (-2, 2, 5), (-5, -1, 2)]
    tk = t_axis(0.45)
    kick = np.sin(2 * np.pi * (45 + 100 * np.exp(-tk * 28)) * tk) * np.exp(-tk * 7)
    ts = t_axis(0.25)
    snare = rng.standard_normal(len(ts)) * np.exp(-ts * 16) * 0.5 + np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 25) * 0.4
    for b in range(bars):
        ch = prog[(b // 2) % len(prog)]
        dense = b >= 24
        for n in ch:
            place(track, pad(note(root + n), bar * 1.05, detune=0.008, bright=1600) * 0.14, b * bar)
        place(track, pad(note(root + ch[0] - 24), bar, detune=0.015, bright=280) * 0.45, b * bar)
        for st in range(8):  # стеклянное остинато восьмыми
            n = ch[st % 3] + (12 if st % 4 < 2 else 24)
            place(track, bell(note(root + n), 0.7, 0.12 if dense else 0.09), b * bar + st * beat / 2)
        for st in range(4 if not dense else 8):
            place(track, kick * 0.9, b * bar + st * beat * (1 if not dense else 0.5))
        place(track, snare * 0.7, b * bar + beat)
        place(track, snare * 0.7, b * bar + beat * 3)
        if b % 4 == 3:  # порыв метели на стыке фраз
            tt = t_axis(bar)
            gust = lowpass_fast(rng.standard_normal(len(tt)), 1500) * np.sin(np.pi * tt / bar) ** 2 * 0.25
            place(track, gust, b * bar)
    return reverb(track, 0.32, 0.72)


# ---------------------------------------------------------------- эффекты
def frozen_sfx():
    rng = np.random.default_rng(17)
    out = {}
    t = t_axis(3.0)  # рёв Архонта: стеклянные обертоны над хриплым шумом
    glass = sum(np.sin(2 * np.pi * f * (1 - 0.12 * t / 3) * t + rng.random() * 6) * a for f, a in ((180, 1), (271, 0.7), (497, 0.5), (1210, 0.25)))
    out['archon_roar'] = lowpass(glass * (1 + 0.4 * np.sin(2 * np.pi * 13 * t)) + rng.standard_normal(len(t)) * 0.7, 2600) * \
        env(len(t), a=0.2, d=0.5, s=0.75, r=1.3)
    t = t_axis(0.8)  # треск льда
    clicks = (rng.random(len(t)) < 0.004).astype(float) * rng.standard_normal(len(t))
    out['ice_crack'] = lowpass(clicks * 6 + rng.standard_normal(len(t)) * 0.3, 3500) * np.exp(-t * 5)
    t = t_axis(1.0)  # скрежет скользящей глыбы
    scrape = lowpass(rng.standard_normal(len(t)), 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))
    out['glacier_slide'] = scrape * env(len(t), a=0.05, d=0.2, s=0.8, r=0.4) + np.sin(2 * np.pi * 95 * t) * np.exp(-t * 3) * 0.3
    t = t_axis(2.6)  # ледяной колокол: колокол + мерцание
    out['ice_bell'] = bell(note(86), 2.6, 1.0) + bell(note(93), 2.6, 0.5) + \
        sum(np.sin(2 * np.pi * note(105 + k) * t) * np.exp(-t * (3 + k)) * 0.05 for k in (0, 4, 7))
    t = t_axis(0.7)  # шип вырастает из пола
    out['spike_rise'] = (np.sin(2 * np.pi * (300 + 1600 * t / 0.7) * t) * 0.4 + lowpass(rng.standard_normal(len(t)), 2400) * 0.7) * \
        np.exp(-t * 4) + (rng.random(len(t)) < 0.01) * rng.standard_normal(len(t)) * 0.8 * np.exp(-t * 6)
    t = t_axis(2.4)  # вой ледяного волка: глиссандо с вибрато
    f = 380 + 260 * np.sin(np.pi * np.clip(t / 2.0, 0, 1)) ** 1.5
    phase = 2 * np.pi * np.cumsum(f * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))) / SR
    out['wolf_howl'] = (np.sin(phase) + 0.3 * np.sin(2 * phase) + 0.1 * np.sin(3 * phase)) * env(len(t), a=0.3, d=0.4, s=0.8, r=0.8)
    t = t_axis(0.4)
    f = 900 - 500 * t / 0.4
    phase = 2 * np.pi * np.cumsum(f) / SR
    out['wolf_hurt'] = (np.sin(phase) + 0.4 * np.sin(2 * phase)) * np.exp(-t * 7)
    t = t_axis(0.6)  # треск стража: глухой удар + осколки
    out['guardian_crack'] = np.sin(2 * np.pi * (70 + 120 * np.exp(-t * 20)) * t) * np.exp(-t * 7) + \
        lowpass(rng.standard_normal(len(t)), 4000) * np.exp(-t * 12) * 0.6 + sum(bell(note(n), 0.6, 0.15) for n in (96, 101))
    return {k: reverb(v, 0.25, 0.6) for k, v in out.items()}


def sfx():
    rng = np.random.default_rng(7)
    out = {}
    t = t_axis(0.45)
    noise = rng.standard_normal(len(t))
    out['wing_flap'] = lowpass(noise, 900) * np.sin(np.pi * np.clip(t / 0.35, 0, 1)) ** 2
    t = t_axis(1.6)
    out['spell_cast'] = sum(bell(note(n), 1.6, 0.6) for n in (84, 88, 91)) + \
        lowpass(rng.standard_normal(len(t)), 4000) * np.exp(-t * 6) * 0.2
    t = t_axis(0.6)
    out['light_bolt'] = np.sin(2 * np.pi * (2400 * np.exp(-t * 6) + 300) * t) * np.exp(-t * 5) + \
        rng.standard_normal(len(t)) * np.exp(-t * 12) * 0.3
    t = t_axis(3.0)
    sweep = lowpass(rng.standard_normal(len(t)), 1200) * np.sin(np.pi * t / 3.0) ** 2
    out['meteor_whoosh'] = sweep * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    t = t_axis(3.5)
    out['meteor_impact'] = np.sin(2 * np.pi * (40 + 80 * np.exp(-t * 4)) * t) * np.exp(-t * 1.5) + \
        lowpass(rng.standard_normal(len(t)), 600) * np.exp(-t * 2.5) * 0.8
    t = t_axis(2.2)
    whisper = lowpass(rng.standard_normal(len(t)), 2500) - lowpass(rng.standard_normal(len(t)), 400)
    out['shadow_ambient'] = whisper * (0.5 + 0.5 * np.sin(2 * np.pi * 1.7 * t)) * np.sin(np.pi * t / 2.2)
    t = t_axis(0.7)
    out['shadow_blink'] = np.sin(2 * np.pi * (900 * np.exp(-t * 8) + 80) * t) * np.exp(-t * 4) * 0.7 + \
        lowpass(rng.standard_normal(len(t)), 1500) * np.exp(-t * 7) * 0.5
    t = t_axis(1.2)
    out['crystal_break'] = sum(bell(note(n), 1.2, 0.4) for n in (91, 94, 98, 101)) + rng.standard_normal(len(t)) * np.exp(-t * 20) * 0.6
    t = t_axis(2.6)
    growl = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) for f in (70, 105, 141, 212)) * (1 + 0.4 * np.sin(2 * np.pi * 23 * t))
    out['seraph_roar'] = lowpass(growl + rng.standard_normal(len(t)) * 0.6, 1400) * env(len(t), a=0.15, d=0.4, s=0.7, r=1.2)
    t = t_axis(4.0)
    out['fading_grow'] = sum(np.sin(2 * np.pi * f * (1 - 0.15 * t / 4) * t) / i for i, f in enumerate((55, 82.5, 110, 164), 1)) * \
        env(len(t), a=1.0, d=0.5, s=0.8, r=1.5)
    t = t_axis(1.8)
    out['trial_start'] = sum(np.sin(2 * np.pi * note(n) * t) * (0.6 if i else 1) for i, n in enumerate((55, 62, 67))) * \
        env(len(t), a=0.08, d=0.3, s=0.6, r=0.9)
    t = t_axis(3.2)
    growl = sum(np.sin(2 * np.pi * f * (1 - 0.2 * t / 3.2) * t + rng.random() * 6) for f in (45, 68, 90, 135))
    out['devourer_roar'] = lowpass(growl * (1 + 0.5 * np.sin(2 * np.pi * 17 * t)) + rng.standard_normal(len(t)) * 0.8, 900) * \
        env(len(t), a=0.3, d=0.5, s=0.8, r=1.4)
    t = t_axis(0.9)
    screech = np.sin(2 * np.pi * (1400 + 600 * np.sin(2 * np.pi * 9 * t)) * t) * 0.6 + rng.standard_normal(len(t)) * 0.3
    out['hunter_screech'] = screech * env(len(t), a=0.05, d=0.2, s=0.6, r=0.4)
    t = t_axis(0.7)
    out['light_eater_feed'] = (np.sin(2 * np.pi * (2400 * np.exp(-t * 4) + 200) * t) * 0.5 +
                               lowpass(rng.standard_normal(len(t)), 3000) * 0.4) * np.exp(-t * 4)
    t = t_axis(0.6)
    crunch = lowpass(rng.standard_normal(len(t)), 1800) * (np.sin(2 * np.pi * 30 * t) > 0) * np.exp(-t * 5)
    out['worm_bite'] = crunch + np.sin(2 * np.pi * 70 * t) * np.exp(-t * 8) * 0.8
    return {k: reverb(v, 0.2, 0.5) for k, v in out.items()}


SOUNDS = {  # событие → (файл(ы), категория для субтитров, стрим?)
    'music.abyss': (['music/abyss_1'], None, True),
    'music.devourer_battle': (['music/devourer_battle'], None, True),
    'entity.light_devourer.roar': (['sfx/devourer_roar'], 'devourer_roar', False),
    'entity.blind_hunter.screech': (['sfx/hunter_screech'], 'hunter_screech', False),
    'entity.light_eater.feed': (['sfx/light_eater_feed'], 'light_eater_feed', False),
    'entity.deep_worm.bite': (['sfx/worm_bite'], 'worm_bite', False),
    'music.heaven': (['music/heaven_1', 'music/heaven_2'], None, True),
    'music.seraph_battle': (['music/seraph_battle'], None, True),
    'music_disc.heavenly_choir': (['records/heavenly_choir'], None, True),
    'entity.wing_flap': (['sfx/wing_flap'], 'wing_flap', False),
    'spell.cast': (['sfx/spell_cast'], 'spell_cast', False),
    'spell.light_bolt': (['sfx/light_bolt'], 'light_bolt', False),
    'meteor.whoosh': (['sfx/meteor_whoosh'], 'meteor_whoosh', False),
    'meteor.impact': (['sfx/meteor_impact'], 'meteor_impact', False),
    'entity.shadow.ambient': (['sfx/shadow_ambient'], 'shadow_ambient', False),
    'entity.shadow.blink': (['sfx/shadow_blink'], 'shadow_blink', False),
    'entity.seraph_crystal.break': (['sfx/crystal_break'], 'crystal_break', False),
    'entity.fallen_seraph.roar': (['sfx/seraph_roar'], 'seraph_roar', False),
    'fading.grow': (['sfx/fading_grow'], 'fading_grow', False),
    'trial.start': (['sfx/trial_start'], 'trial_start', False),
    'music.frozen': (['music/frozen_1'], None, True),
    'music.archon_battle': (['music/archon_battle'], None, True),
    'entity.frost_archon.roar': (['sfx/archon_roar'], 'archon_roar', False),
    'block.ice.crack': (['sfx/ice_crack'], 'ice_crack', False),
    'block.glacier.slide': (['sfx/glacier_slide'], 'glacier_slide', False),
    'block.ice_bell.ring': (['sfx/ice_bell'], 'ice_bell', False),
    'entity.ice_spike.rise': (['sfx/spike_rise'], 'spike_rise', False),
    'entity.ice_wolf.howl': (['sfx/wolf_howl'], 'wolf_howl', False),
    'entity.ice_wolf.hurt': (['sfx/wolf_hurt'], 'wolf_hurt', False),
    'entity.ice_guardian.crack': (['sfx/guardian_crack'], 'guardian_crack', False),
}


def write_sounds_json():
    sounds = {}
    for event, (files, sub, stream) in SOUNDS.items():
        entry = {'sounds': [{'name': 'celestial:' + f, **({'stream': True} if stream else {})} for f in files]}
        if sub:
            entry['subtitle'] = 'subtitles.celestial.' + sub
        sounds[event] = entry
    with open(os.path.join(ROOT, 'sounds.json'), 'w', encoding='utf-8') as f:
        json.dump(sounds, f, ensure_ascii=False, indent=2)


def frozen_only():
    """Только звуки волны 0.4 (python3 gen_sounds.py frozen) — остальные ogg не перекодируются."""
    print('Ледяные Чертоги…')
    save('music/frozen_1', frozen_music(8), 3)
    save('music/archon_battle', archon_battle(9), 3)
    for k, v in frozen_sfx().items():
        save('sfx/' + k, v, 5)
    write_sounds_json()
    print('ok: звуки Чертогов')


def main():
    import sys
    if sys.argv[1:] == ['frozen']:
        frozen_only()
        return
    print('музыка Рая…')
    save('music/heaven_1', heaven_music(1, [(0, 4, 7, 11), (-3, 0, 4, 7), (-7, -3, 0, 4), (-5, -1, 2, 7)]), 3)
    save('music/heaven_2', heaven_music(2, [(2, 5, 9, 12), (-3, 0, 4, 7), (0, 4, 7, 11), (-5, 2, 5, 9)], bpm=54, root=62), 3)
    print('битва с Серафимом…')
    save('music/seraph_battle', battle_music(3), 3)
    print('пластинка…')
    save('records/heavenly_choir', choir(4), 3)
    print('Бездна…')
    save('music/abyss_1', abyss_music(5), 3)
    save('music/devourer_battle', devourer_battle(6), 3)
    print('эффекты…')
    for k, v in sfx().items():
        save('sfx/' + k, v, 5)
    save('music/frozen_1', frozen_music(8), 3)
    save('music/archon_battle', archon_battle(9), 3)
    for k, v in frozen_sfx().items():
        save('sfx/' + k, v, 5)
    write_sounds_json()
    total = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(OUT) for fn in fns)
    print(f'ok: звуки, {len(SOUNDS)} событий, {total // 1024} КБ')


if __name__ == '__main__':
    main()
