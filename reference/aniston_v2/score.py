"""Original score. A pulse, a bass, and a pad - not a drone.

The last build's music was four sine partials through a comb delay and it
sounded like an MRI. This has a tempo, a kick on the beat and a hat offbeat,
so it does the job library music does on this format: keep the floor moving
under the narration without asking for attention.

Written rather than licensed so nothing in the film can be Content-ID claimed.
"""
from __future__ import annotations

import numpy as np

SR = 48_000
BPM = 92.0
BEAT = 60.0 / BPM

PROG = [(45, (0, 3, 7, 10)), (50, (0, 3, 7, 10)),
        (53, (0, 4, 7, 11)), (48, (0, 4, 7, 11))]
BARS = 4.0          # beats per chord


def hz(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n: int, a: float, d: float) -> np.ndarray:
    """Attack then exponential decay. `a` is clamped to n - a short note must
    still get a complete envelope rather than a truncated ramp."""
    if n <= 0:
        return np.zeros(0)
    e = np.zeros(n)
    ai = min(max(int(a * SR), 1), n)
    e[:ai] = np.linspace(0, 1, ai)
    if n > ai:
        e[ai:] = np.exp(-np.linspace(0, 6, n - ai))
    return e


def hold(n: int, a: float, r: float) -> np.ndarray:
    """Attack, sustain, release - for pads, which must not decay away."""
    if n <= 0:
        return np.zeros(0)
    e = np.ones(n)
    ai = min(max(int(a * SR), 1), n // 2 or 1)
    ri = min(max(int(r * SR), 1), n // 2 or 1)
    e[:ai] = np.linspace(0, 1, ai) ** 1.5
    e[n - ri:] = np.linspace(1, 0, ri) ** 1.5
    return e


def kick(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    f = 110 * np.exp(-t * 30) + 46
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.18) * 0.9


def hat(n: int, rng) -> np.ndarray:
    return rng.standard_normal(n) * env(n, 0.001, 0.03) * 0.10


def pad(freq: float, n: int, amp: float) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, w in enumerate((1.0, 0.5, 0.22, 0.10), start=1):
        out += w * np.sin(2 * np.pi * freq * k * t + k * 0.6)
    return out * amp


def bass(freq: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) * 0.8
            + np.sin(2 * np.pi * freq * 2 * t) * 0.16) * env(n, 0.01, 0.55) * 0.55


def build(seconds: float, seed: int = 11) -> np.ndarray:
    rng = np.random.default_rng(seed)
    total = int(round(seconds * SR))
    L = np.zeros(total)
    R = np.zeros(total)

    # chord pads
    pos, i = 0, 0
    chord_len = int(BARS * BEAT * SR)
    while pos < total:
        root, ivs = PROG[i % len(PROG)]
        n = min(chord_len + int(0.9 * SR), total - pos)
        e = hold(n, 1.2, 0.9)
        for j, iv in enumerate(ivs):
            v = pad(hz(root + iv + 12), n, 0.16 / (1 + j * 0.6)) * e
            p = -0.3 + 0.6 * j / max(len(ivs) - 1, 1)
            L[pos:pos + n] += v * (1 - p) * 0.5
            R[pos:pos + n] += v * (1 + p) * 0.5
        pos += chord_len
        i += 1

    # kick on 1 and 3, hat on offbeats, bass following the root
    beat_i = 0
    t = 0.0
    while t < seconds:
        s = int(t * SR)
        if beat_i % 4 in (0, 2):
            n = min(int(0.3 * SR), total - s)
            if n > 0:
                k = kick(n)
                L[s:s + n] += k
                R[s:s + n] += k
        n = min(int(0.06 * SR), total - s)
        if n > 0 and beat_i % 2 == 1:
            h = hat(n, rng)
            L[s:s + n] += h * 0.8
            R[s:s + n] += h * 1.2
        if beat_i % 4 == 0:
            root = PROG[(beat_i // 16) % len(PROG)][0]
            n = min(int(BEAT * 2 * SR), total - s)
            if n > 0:
                b = bass(hz(root - 12), n)
                L[s:s + n] += b
                R[s:s + n] += b
        t += BEAT
        beat_i += 1

    # float32 throughout: stacking two float64 channels for a ten-minute bed
    # asked for 478 MiB in one allocation and failed on this machine.
    st = np.stack([L, R], axis=1).astype(np.float32)
    peak = float(np.max(np.abs(st))) or 1.0
    st *= np.float32(0.42 / peak)
    f = int(3.0 * SR)
    st[:f] *= np.linspace(0, 1, f, dtype=np.float32)[:, None]
    st[-f:] *= np.linspace(1, 0, f, dtype=np.float32)[:, None]
    return st
