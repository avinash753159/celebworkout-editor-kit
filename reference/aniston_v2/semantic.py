"""Pick b-roll by MEANING, not just by era.

The standing complaint about this cut, and it is a fair one: the 61 entries in
cues.py pin 61 moments to pictures that depict them, and the other ~280 shots
are drawn round-robin from an era-locked pool. Era-locked is not wrong - a
Friends clip cannot play under her childhood any more - but it is not right
either. Nothing asks whether THIS window suits THIS sentence.

This embeds every candidate window with CLIP and every shot's narration with
the same model, so a shot can be chosen by similarity instead of by turn.
Measured on this machine: 92ms per window on CPU torch, about fourteen minutes
for the whole candidate set, cached afterwards in manifest/clip.npz.

It does NOT override cues.py. A cue is a hand-made statement about what a
sentence means and outranks any similarity score.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
NPZ = ROOT / "manifest" / "clip.npz"
MODEL = "openai/clip-vit-base-patch32"
BATCH = 16

_IMG: np.ndarray | None = None
_KEYS: dict[str, int] | None = None
_MODEL = None
_PROC = None


def _feat(out):
    """transformers 5.x returns BaseModelOutputWithPooling from
    get_image_features / get_text_features, not a bare tensor. The 512-d CLIP
    embedding is pooler_output; last_hidden_state is the 50x768 token stack and
    is not what we want."""
    return out.pooler_output if hasattr(out, "pooler_output") else out


def _load_model():
    global _MODEL, _PROC
    if _MODEL is None:
        from transformers import CLIPModel, CLIPProcessor
        _MODEL = CLIPModel.from_pretrained(MODEL).eval()
        _PROC = CLIPProcessor.from_pretrained(MODEL)
    return _MODEL, _PROC


def _load_index():
    global _IMG, _KEYS
    if _IMG is None:
        if not NPZ.exists():
            _IMG, _KEYS = np.zeros((0, 512), np.float32), {}
        else:
            d = np.load(NPZ, allow_pickle=True)
            _IMG = d["vecs"]
            _KEYS = {k: i for i, k in enumerate(d["keys"].tolist())}
    return _IMG, _KEYS


def ready() -> bool:
    _, keys = _load_index()
    return len(keys) > 0


def text_vec(text: str) -> np.ndarray:
    import torch
    m, pr = _load_model()
    with torch.no_grad():
        out = _feat(m.get_text_features(
            **pr(text=[text[:300]], return_tensors="pt", padding=True,
                 truncation=True, max_length=77)))
    v = out.detach().numpy()[0].astype(np.float32)
    return v / max(1e-9, np.linalg.norm(v))


def score(text: str, windows: list[tuple[str, float]]) -> np.ndarray:
    """Cosine similarity of each window to the sentence. Windows with no
    embedding score 0, so they neither win nor are excluded."""
    img, keys = _load_index()
    if not keys or not windows:
        return np.zeros(len(windows), np.float32)
    tv = text_vec(text)
    out = np.zeros(len(windows), np.float32)
    for i, (v, t) in enumerate(windows):
        j = keys.get(f"{v}@{t:.2f}")
        if j is not None:
            out[i] = float(img[j] @ tv)
    return out


def embedded(windows: list[tuple[str, float]]) -> list[bool]:
    """Which of these candidates the index can actually score.

    THIS EXISTS BECAUSE OF SHOT 211. `score()` returns 0.0 for anything it has
    never embedded, documented above as "neither win nor are excluded" - which
    is true for one unknown among many known, and catastrophically false when
    EVERY candidate is unknown. main() only ever embedded video windows, so no
    still in this project had a vector; every `score(text, stills).argmax()`
    in build5 therefore returned index 0 and picked whatever happened to sit
    first in the pool list, while the code around it said "choose by meaning
    like everything else does".

    That is how D3 shot 211 got f_saladplate - a grilled chicken breast on
    salad leaves - under a card reading "When I wake up, I have warm lemon
    water and then I have a shake or avocado and eggs", with the narration on
    "to start the day hydrated". Nothing was wrong with the still and nothing
    was wrong with the ranking; the ranking was never consulted.

    Callers use this to tell "meaning says this one" apart from "meaning had
    nothing to say and I took the first".
    """
    _, keys = _load_index()
    return [f"{v}@{t:.2f}" in keys for v, t in windows]


STILL_DIRS = ("stills", "stills_move", "stills_food", "stills_place")

# Real photographs (photos/) are registered under short stable names in
# manifest/photos.json["names"] -> content hash -> file, exactly the
# indirection build5.py:_still_path uses to reach photos/. The files on disk
# keep long hash-suffixed names, not the ph_* stems, so a plain glob of
# STILL_DIRS (the old fix attempt) would never find them - "photos" is not
# even a directory of stem-named files the way stills/ is. Reuse the name ->
# hash -> file lookup instead of inventing a second one.
_PHOTOS_LEDGER = ROOT / "manifest" / "photos.json"
_PHOTO_NAMES: dict = {}
if _PHOTOS_LEDGER.exists():
    _pd = json.loads(_PHOTOS_LEDGER.read_text(encoding="utf-8"))
    _by_hash = _pd.get("by_hash", {})
    for _n, _h in _pd.get("names", {}).items():
        if _h in _by_hash:
            _PHOTO_NAMES[_n] = _by_hash[_h]["file"]


def still_windows() -> list[tuple[str, float]]:
    """Every still in the project, keyed the way the pools key them
    (reels5.S -> ("still:<stem>", 0.0)). Stills were missing from the index
    entirely - see embedded(). Photographs (still:ph_*) are included via
    _PHOTO_NAMES since their on-disk files are not stem-named."""
    seen = {}
    for d in STILL_DIRS:
        for p in sorted((ROOT / d).glob("*.jpg")):
            seen.setdefault(p.stem, p)
    names = set(seen) | set(_PHOTO_NAMES)
    return [(f"still:{s}", 0.0) for s in sorted(names)]


def _still_file(stem: str):
    for d in STILL_DIRS:
        p = ROOT / d / f"{stem}.jpg"
        if p.exists():
            return p
    if stem in _PHOTO_NAMES:
        # photos_169 first - the 16:9 rendition is what the film shows, so it
        # is what the index has to score. See photo_frame.py.
        for d in ("photos_169", "photos"):
            p = ROOT / d / _PHOTO_NAMES[stem]
            if p.exists():
                return p
    return None


def _grab(vid: str, t: float):
    from PIL import Image
    import io
    if vid.startswith("still:"):
        p = _still_file(vid[len("still:"):])
        if p is None:
            return None
        return Image.open(p).convert("RGB")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", f"hd/{vid}.mp4",
         "-frames:v", "1", "-vf", "scale=256:-2", "-f", "image2pipe",
         "-vcodec", "mjpeg", "-q:v", "4", "-"], capture_output=True, cwd=str(ROOT))
    if not r.stdout:
        return None
    try:
        return Image.open(io.BytesIO(r.stdout)).convert("RGB")
    except Exception:
        return None


def main() -> None:
    import torch
    import reels5 as R
    # STILLS TOO. They were left out for every pass up to this one, which made
    # every "pick the still by meaning" branch in build5 a no-op returning
    # element 0 of the pool. See embedded().
    wins = sorted({w for v in R.DUR if v not in R.BANNED
                   for w in R.windows(v, subject=False)}
                  | {w for v in R.DUR if v not in R.BANNED
                     for w in R.windows(v, subject=True)}
                  | set(R.TRAIN_OK)
                  | set(still_windows()))
    img, keys = _load_index()
    have = dict(keys)
    vecs = list(img)
    todo = [w for w in wins if f"{w[0]}@{w[1]:.2f}" not in have]
    print(f"  {len(wins)} candidate windows, {len(todo)} to embed")
    if not todo:
        return
    m, pr = _load_model()
    buf_im, buf_k = [], []

    def flush():
        if not buf_im:
            return
        with torch.no_grad():
            f = _feat(m.get_image_features(**pr(images=buf_im, return_tensors="pt")))
        f = f.detach().numpy().astype(np.float32)
        f /= np.maximum(1e-9, np.linalg.norm(f, axis=1, keepdims=True))
        for k, v in zip(buf_k, f):
            have[k] = len(vecs)
            vecs.append(v)
        buf_im.clear()
        buf_k.clear()

    for i, (vid, t) in enumerate(todo, 1):
        im = _grab(vid, t)
        if im is not None:
            buf_im.append(im)
            buf_k.append(f"{vid}@{t:.2f}")
        if len(buf_im) >= BATCH:
            flush()
        if i % 400 == 0:
            flush()
            np.savez_compressed(NPZ, vecs=np.array(vecs, np.float32),
                                keys=np.array(list(have.keys())))
            print(f"    {i}/{len(todo)}", flush=True)
    flush()
    np.savez_compressed(NPZ, vecs=np.array(vecs, np.float32),
                        keys=np.array(list(have.keys())))
    print(f"  {len(have)} windows embedded -> {NPZ.name}")


if __name__ == "__main__":
    main()
