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


# ---------------------------------------------------------------- эффекты
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
    return {k: reverb(v, 0.2, 0.5) for k, v in out.items()}


SOUNDS = {  # событие → (файл(ы), категория для субтитров, стрим?)
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
}


def main():
    print('музыка Рая…')
    save('music/heaven_1', heaven_music(1, [(0, 4, 7, 11), (-3, 0, 4, 7), (-7, -3, 0, 4), (-5, -1, 2, 7)]), 3)
    save('music/heaven_2', heaven_music(2, [(2, 5, 9, 12), (-3, 0, 4, 7), (0, 4, 7, 11), (-5, 2, 5, 9)], bpm=54, root=62), 3)
    print('битва с Серафимом…')
    save('music/seraph_battle', battle_music(3), 3)
    print('пластинка…')
    save('records/heavenly_choir', choir(4), 3)
    print('эффекты…')
    for k, v in sfx().items():
        save('sfx/' + k, v, 5)
    sounds = {}
    for event, (files, sub, stream) in SOUNDS.items():
        entry = {'sounds': [{'name': 'celestial:' + f, **({'stream': True} if stream else {})} for f in files]}
        if sub:
            entry['subtitle'] = 'subtitles.celestial.' + sub
        sounds[event] = entry
    with open(os.path.join(ROOT, 'sounds.json'), 'w', encoding='utf-8') as f:
        json.dump(sounds, f, ensure_ascii=False, indent=2)
    total = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(OUT) for fn in fns)
    print(f'ok: звуки, {len(SOUNDS)} событий, {total // 1024} КБ')


if __name__ == '__main__':
    main()
