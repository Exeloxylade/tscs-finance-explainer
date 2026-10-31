"""Generate a music bed and SFX as WAV files. Pure Python stdlib, no installs.

Usage:
  python make_audio.py --out <project>/assets --duration 12 --bpm 100 --mood dark

Writes: music.wav, whoosh_a.wav, whoosh_b.wav, impact.wav, riser.wav, pop.wav
Every sound is seeded, so the same args give the same files.
"""
import argparse
import math
import os
import random
import struct
import wave

SR = 44100

MOODS = {
    # chord roots (MIDI) per bar, chord shape, pad brightness 0..1
    "dark": ([57, 53, 48, 55], [0, 3, 7, 10], 0.25),     # Am7 Fmaj C G (minor-ish)
    "epic": ([50, 46, 41, 48], [0, 7, 12, 15], 0.35),    # Dm Bb F C, open fifths
    "bright": ([60, 55, 57, 53], [0, 4, 7, 11], 0.45),   # C G Am F, major 7
}


def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12.0)


def lowpass(buf, cutoff):
    a = 1.0 - math.exp(-2.0 * math.pi * cutoff / SR)
    y = 0.0
    out = [0.0] * len(buf)
    for i, x in enumerate(buf):
        y += a * (x - y)
        out[i] = y
    return out


def highpass(buf, cutoff):
    lp = lowpass(buf, cutoff)
    return [x - l for x, l in zip(buf, lp)]


def normalize(buf, peak=0.89):  # 0.89 ~ -1 dBFS
    m = max(1e-9, max(abs(x) for x in buf))
    return [x * peak / m for x in buf]


def write(path, buf):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32767)) for x in buf))
    print("wrote", path, f"{len(buf) / SR:.2f}s")


def music(duration, bpm, mood, seed):
    rnd = random.Random(seed)
    roots, shape, bright = MOODS[mood]
    n = int(duration * SR)
    beat = 60.0 / bpm
    bar = beat * 4
    pad = [0.0] * n
    phases = {}
    for i in range(n):
        t = i / SR
        b = int(t / bar) % len(roots)
        s = 0.0
        for k, iv in enumerate(shape):
            for det in (-0.08, 0.08):
                f = midi_hz(roots[b] + iv) * (1 + det / 100)
                key = (k, det)
                ph = phases.get(key, rnd.random()) + f / SR
                ph -= int(ph)
                phases[key] = ph
                s += 2 * ph - 1  # saw
        pad[i] = s / (len(shape) * 2)
    pad = lowpass(lowpass(pad, 400 + 2600 * bright), 1800 + 3000 * bright)
    # slow swell per bar
    for i in range(n):
        t = i / SR
        pad[i] *= 0.55 + 0.45 * math.sin(math.pi * ((t % bar) / bar)) ** 0.5

    drums = [0.0] * n
    nbeats = int(duration / beat) + 1
    for k in range(nbeats):
        st = int(k * beat * SR)
        # kick on every beat: pitch-drop sine + click
        for j in range(int(0.35 * SR)):
            if st + j >= n:
                break
            t = j / SR
            f = 45 + 110 * math.exp(-t * 28)
            drums[st + j] += 0.9 * math.sin(2 * math.pi * f * t) * math.exp(-t * 9)
        # soft hat on the off-beat
        hs = int((k + 0.5) * beat * SR)
        for j in range(int(0.05 * SR)):
            if hs + j >= n:
                break
            drums[hs + j] += 0.12 * (rnd.random() * 2 - 1) * math.exp(-j / SR * 70)
    drums = highpass(drums, 30)

    out = [0.62 * p + 0.5 * d for p, d in zip(pad, drums)]
    fade = int(min(1.5, duration / 4) * SR)
    for j in range(fade):
        out[j] *= j / fade
        out[n - 1 - j] *= j / fade
    return normalize(out, 0.8)


def whoosh(length, seed, up=True):
    rnd = random.Random(seed)
    n = int(length * SR)
    noise = [rnd.random() * 2 - 1 for _ in range(n)]
    out, y = [0.0] * n, 0.0
    for i, x in enumerate(noise):
        p = i / n
        sweep = p if up else 1 - p
        cut = 300 + 5000 * sweep ** 2
        a = 1.0 - math.exp(-2 * math.pi * cut / SR)
        y += a * (x - y)
        env = math.sin(math.pi * p) ** 1.5  # swell in, out
        out[i] = y * env
    return normalize(out, 0.85)


def impact(seed):
    rnd = random.Random(seed)
    n = int(2.2 * SR)
    out = [0.0] * n
    for i in range(n):
        t = i / SR
        f = 38 + 90 * math.exp(-t * 14)
        boom = math.sin(2 * math.pi * f * t) * math.exp(-t * 2.4)
        crack = (rnd.random() * 2 - 1) * math.exp(-t * 30)
        out[i] = boom + 0.35 * crack
    return normalize(lowpass(out, 3500), 0.89)


def riser(length, seed):
    rnd = random.Random(seed)
    n = int(length * SR)
    out, y, ph = [0.0] * n, 0.0, 0.0
    for i in range(n):
        p = i / n
        f = 120 * 2 ** (p * 3)  # up three octaves
        ph += f / SR
        ph -= int(ph)
        tone = 2 * ph - 1
        x = rnd.random() * 2 - 1
        cut = 400 + 7000 * p ** 2
        y += (1 - math.exp(-2 * math.pi * cut / SR)) * (x - y)
        out[i] = (0.4 * tone + 0.8 * y) * p ** 2
    return normalize(lowpass(out, 6000), 0.8)


def pop(seed):
    n = int(0.18 * SR)
    out = []
    for i in range(n):
        t = i / SR
        f = 900 * math.exp(-t * 18) + 300
        out.append(math.sin(2 * math.pi * f * t) * math.exp(-t * 30))
    return normalize(out, 0.7)


def _bandnoise(rnd, n, lo, hi):
    """noise between lo and hi Hz: two one-pole lowpasses (hi) minus a slower one (lo)."""
    a_hi = 1.0 - math.exp(-2 * math.pi * hi / SR)
    a_lo = 1.0 - math.exp(-2 * math.pi * lo / SR)
    y1 = y2 = z = 0.0
    out = [0.0] * n
    for i in range(n):
        x = rnd.random() * 2 - 1
        y1 += a_hi * (x - y1); y2 += a_hi * (y1 - y2)   # 2-pole low-pass at hi
        z += a_lo * (y2 - z)                             # low part, removed below
        out[i] = y2 - z
    return out


def swish(seed, length=0.24, centre=3200, body=0.35):
    """Measured target (reference transitions): bright part lasts ~0.2 s, sits ~19 dB
    above its surroundings in 4-8 kHz, with a soft low body under it (+5 dB at 40-200 Hz).
    Fast 6 ms attack, ~55 ms decay, a short 90->55 Hz thump. Peak -6 dBFS, not -1."""
    rnd = random.Random(seed)
    n = int(length * SR)
    air = _bandnoise(rnd, n, centre * 0.45, centre * 2.2)
    out = [0.0] * n
    for i in range(n):
        t = i / SR
        env = min(1.0, t / 0.006) * math.exp(-t / 0.055)
        f = 55 + 35 * math.exp(-t * 30)
        thump = math.sin(2 * math.pi * f * t) * math.exp(-t / 0.07)
        out[i] = air[i] * env + body * thump
    return normalize(out, 0.5)


def tick(seed):
    """UI tick for chips/labels appearing: 30 ms, soft, mid-high. Peak -9 dBFS."""
    rnd = random.Random(seed)
    n = int(0.05 * SR)
    air = _bandnoise(rnd, n, 1800, 6000)
    out = []
    for i in range(n):
        t = i / SR
        out.append(air[i] * math.exp(-t / 0.008) + 0.4 * math.sin(2 * math.pi * 1400 * t) * math.exp(-t / 0.012))
    return normalize(out, 0.35)


def thud(seed):
    """Soft hit for a stamp / big number: rounded 65 Hz body + a little paper slap. Peak -6 dBFS."""
    rnd = random.Random(seed)
    n = int(0.6 * SR)
    slap = _bandnoise(rnd, n, 600, 4000)
    out = []
    for i in range(n):
        t = i / SR
        f = 65 + 40 * math.exp(-t * 25)
        out.append(math.sin(2 * math.pi * f * t) * math.exp(-t / 0.16) + 0.5 * slap[i] * math.exp(-t / 0.02))
    return normalize(lowpass(out, 5000), 0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=12)
    ap.add_argument("--bpm", type=float, default=100)
    ap.add_argument("--mood", choices=sorted(MOODS), default="dark")
    ap.add_argument("--riser", type=float, default=2.0, help="riser length, seconds")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    j = lambda f: os.path.join(a.out, f)
    write(j("music.wav"), music(a.duration, a.bpm, a.mood, a.seed))
    write(j("whoosh_a.wav"), whoosh(0.9, a.seed + 1, up=True))
    write(j("whoosh_b.wav"), whoosh(1.1, a.seed + 2, up=False))
    write(j("impact.wav"), impact(a.seed + 3))
    write(j("riser.wav"), riser(a.riser, a.seed + 4))
    write(j("pop.wav"), pop(a.seed + 5))
    # documentary transition kit (measured against a finance-explainer reference, see SKILL)
    write(j("swish_a.wav"), swish(a.seed + 11, 0.24, 3200))
    write(j("swish_b.wav"), swish(a.seed + 12, 0.26, 2600))
    write(j("swish_c.wav"), swish(a.seed + 13, 0.22, 3800, body=0.45))
    write(j("tick.wav"), tick(a.seed + 14))
    write(j("thud.wav"), thud(a.seed + 15))


if __name__ == "__main__":
    main()
