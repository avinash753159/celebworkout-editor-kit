"""A picture for every movement the narration names.

Pass 2. MOVE_REVIEW.md records that 15 of 17 exercise pins showed something
other than the named movement - three women standing under BANDED GLUTE BRIDGE,
a face close-up under REVERSE LUNGE, a caption reading LATERAL DELTOID RAISE
under OVERHEAD PRESS.

The footage does not exist: nobody has filmed Aniston doing a dead bug. The
owner's instruction is to use a picture where video is missing. Each still below
depicts the movement plainly, in the channel's register - a real gym, a real
person mid-movement, no text.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stills_move"
OUT.mkdir(exist_ok=True)
LEDGER = ROOT / "manifest" / "move_ledger.json"
MODEL, COST, BUDGET = "fal-ai/flux/dev", 0.025, 1.20

STYLE = ("photographed in a bright modern gym studio, natural window light, "
         "full body visible in frame, side view, clean uncluttered background, "
         "athletic woman in her fifties in plain dark leggings and a plain "
         "sports top, shot on 35mm, natural colour, photographic not rendered, "
         "no text, no logos, no branding, no equipment brand marks, 16:9")

MOVES = {
 "mv_glutebridge":  "A woman lying on her back on a mat, knees bent, hips lifted high off the floor in a glute bridge, a resistance band around her thighs",
 "mv_hipabduction": "Rear view of a woman standing in a bright gym, both legs straight and together at the top, feet apart at the bottom so the legs form a narrow upside-down V, a thick loop resistance band stretched across both ankles, both hands on her hips, seen from directly behind, full body",
 "mv_slantsquat":   "A woman squatting with her feet on a slanted wooden board, knees bent, arms forward for balance",
 "mv_reverselunge": "A woman mid reverse lunge, one knee lowered toward the floor behind her, torso upright",
 "mv_intervals":    "A woman running on a treadmill in a bright gym, side view, mid stride",
 "mv_elliptical":   "A woman on an elliptical cross-trainer in a bright gym, side view",
 "mv_lateralraise": "A woman standing, arms raised out to both sides at shoulder height against a resistance band",
 "mv_kneelingrow":  "A woman kneeling upright on both knees on a mat, side on to camera, pulling a resistance band anchored in front of her back toward her ribs, elbow driving straight behind her, back flat",
 "mv_plank":        "A woman holding a forearm plank on a mat, forearms flat on the floor, elbows under shoulders, hips level with shoulders, body perfectly horizontal and parallel to the ground, strict side view",
 "mv_deadbug":      "A woman lying on her back on a mat with both arms reaching to the ceiling and opposite arm and leg extended in a dead bug",
 "mv_bandedrow":    "A woman seated on the floor pulling a resistance band toward her waist with both hands, back straight",
 "mv_overheadpress":"A woman standing pressing two light dumbbells overhead, arms extended",
 "mv_quadruped":    "A woman on hands and knees on a mat extending one straight leg behind her",
 "mv_jumprope":     "A woman skipping with a jump rope in a gym, rope blurred in motion, mid jump",
 "mv_padwork":      "A woman in boxing gloves striking focus pads held by a trainer, side view",
 "mv_catcow":       "A woman kneeling on all fours on an exercise mat with BOTH KNEES TOUCHING THE FLOOR and both hands on the floor, back arched up like an angry cat, knees bent at ninety degrees, thighs vertical, photographed from the side at floor level",
 "mv_hipopener":    "A woman in a low kneeling lunge stretching her hip open on a mat",
}


def key():
    m = re.search(r"FAL_KEY=(\S+)", (ROOT.parent / ".env.local").read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("no FAL_KEY")
    return m.group(1)


def main():
    K = key()
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent": 0.0, "items": {}}
    fails = 0
    for sid, base in MOVES.items():
        prompt = f"{base}, {STYLE}"
        h = hashlib.sha1(prompt.encode()).hexdigest()[:16]
        dst = OUT / f"{sid}.jpg"
        if led["items"].get(h, {}).get("state") == "done" and dst.exists():
            print(f"  {sid:<18} cached"); continue
        if led["spent"] + COST > BUDGET:
            print("  BUDGET REACHED"); break
        if fails >= 3:
            print("  circuit breaker"); break
        try:
            r = requests.post(f"https://fal.run/{MODEL}",
                headers={"Authorization": f"Key {K}", "Content-Type": "application/json"},
                json={"prompt": prompt, "image_size": "landscape_16_9",
                      "num_images": 1, "num_inference_steps": 30}, timeout=180)
            if r.status_code == 200:
                led["spent"] += COST
            else:
                raise RuntimeError(f"HTTP {r.status_code}")
            url = r.json()["images"][0]["url"]
            dst.write_bytes(requests.get(url, timeout=180).content)
            Image.open(dst).verify()
            led["items"][h] = {"id": sid, "state": "done", "url": url, "cost": COST}
            print(f"  {sid:<18} ok   ${led['spent']:.3f}")
            fails = 0
        except Exception as e:
            led["items"][h] = {"id": sid, "state": "failed", "error": str(e)[:160]}
            print(f"  {sid:<18} FAIL {str(e)[:70]}"); fails += 1
        finally:
            LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")
            time.sleep(0.35)
    print(f"\n  spent ${led['spent']:.2f}")


if __name__ == "__main__":
    main()
