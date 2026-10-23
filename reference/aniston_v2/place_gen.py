"""Establishing stills for the biography.

The reference answers "what goes on screen" during the life story with
ILLUSTRATIVE material - an animated map zooming to Pennsylvania, a town aerial,
a New York street, the Manhattan skyline, a childhood photo, her father's soap.
V4's biography answered it with another interview clip, twenty-four times in a
row, which is why fast cutting did not make it feel fast.

These are the establishing beats the narration actually names: Sherman Oaks,
New York, the Waldorf school, the Fame school, the six years of failed pilots,
the waitressing. Same ledger discipline as the other generators.
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
OUT = ROOT / "stills_place"
OUT.mkdir(exist_ok=True)
LEDGER = ROOT / "manifest" / "place_ledger.json"

MODEL = "fal-ai/flux/dev"
COST = 0.025
BUDGET = 3.00

STYLE = ("shot on 35mm, cinematic, natural light, muted colour, mild grain, "
         "photographic not rendered, no people in the foreground, "
         "no text, no signage lettering, no logos, no branding, 16:9")

PLACES = {
 "p_shermanoaks": "A wide establishing aerial of a leafy San Fernando Valley suburb in California at golden hour, low houses and palm trees",
 "p_la70s":       "A quiet 1970s Los Angeles residential street with parked cars of the era, warm afternoon light",
 "p_nycstreet":   "A New York City brownstone street on the Upper East Side, autumn, wet pavement, early morning",
 "p_nycskyline":  "The Manhattan skyline seen across the river at dawn, soft haze",
 "p_school":      "The stone facade of an old private school building in a city, tall windows, empty steps",
 "p_artschool":   "An empty performing arts school rehearsal room with a piano and a barre, morning light through high windows",
 "p_corridor":    "An empty school corridor with worn wooden floors and lockers, late afternoon light",
 "p_studio90s":   "An empty 1990s television studio floor with cameras and cable runs, work lights on",
 "p_soapset":     "A dated soap opera living room set on a studio floor, lit, nobody present",
 # first generation put a neon sign over the window reading "DINER DINER".
 # Regenerated with the sign written out of the frame.
 "p_diner":       "The empty interior of a classic American diner at night, chrome stools along a long counter, warm light, seen from inside, nobody present, no signage anywhere in frame",
 "p_waitress":    "An empty restaurant dining room at closing time, chairs stacked on tables, one light on",
 "p_office":      "A drab open-plan telemarketing office with rows of empty desks and old phones, fluorescent light",
 "p_bike":        "A bicycle leaning against a New York building on a grey day, messenger bag on the ground",
 "p_marquee":     "A small theatre marquee at dusk with blank unlettered panels, bulbs lit",
 "p_carpet":      "An empty red carpet with press barriers and camera stands before an event, evening",
 "p_apartment":   "A small sparse 1990s apartment interior with a couch and a television, afternoon light",

 # second wave: the whole script needs illustrative material, not just the
 # biography. Measured on v5, 36 of 59 near-identical frame pairs were the same
 # interview seconds apart - static talking heads look alike whichever second
 # you take, so the fix is fewer of them, not better shuffling.
 "q_gymfloor":   "An empty boutique gym studio with light wooden floor and mirrors, morning sun",
 "q_bands":      "Resistance bands and ankle straps laid out on a pale studio floor, overhead",
 "q_dumbbells":  "A rack of small dumbbells against a pale wall, shallow depth of field",
 "q_mat":        "A rolled exercise mat standing against a bright studio wall",
 "q_spinbike":   "A stationary bike alone in a bright studio, side on",
 "q_treadmill":  "A treadmill belt close and low in a bright gym, shallow focus",
 "q_ropes":      "A skipping rope coiled on a wooden gym floor, warm light",
 "q_gloves":     "Boxing gloves resting on a bench in a bright gym",
 "q_slantboard": "A wooden slant board on a studio floor, close, soft light",
 "q_towel":      "A folded towel and a water bottle on a gym bench, morning light",
 "q_stretch":    "An empty yoga studio with props stacked neatly, soft north light",
 "q_clockgym":   "A plain wall clock in a bright gym, close",
 "q_spine":      "An anatomical spine model on a physiotherapy desk, soft light",
 "q_physio":     "A physiotherapy treatment room with a bench and kinesio tape rolls",
 "q_kinesio":    "Rolls of coloured kinesio tape arranged on a white surface, overhead",
 "q_harness":    "A stunt harness and carabiners hanging in a film studio, daylight",
 "q_filmset":    "A film set with lighting stands and a camera dolly, crew absent, lit",
 "q_eiffel":     "The Eiffel Tower seen from below against a bright sky",
 "q_paris":      "A Paris street with Haussmann buildings in morning light",
 "q_kitchen":    "A bright modern kitchen counter with fruit and a water jug, nobody present",
 "q_fridge":     "An open fridge full of fresh vegetables and containers, bright",
 "q_market":     "A fresh produce market stall with vegetables in crates, daylight",
 "q_watchclock": "A wristwatch beside a glass of water on a kitchen counter, morning",
 "q_sunrise":    "Sunrise through a bedroom window over a made bed, warm quiet light",
 "q_running":    "An empty park path lined with trees at sunrise, nobody on it",
 "q_award":      "An awards stage with an empty podium and lights, before the audience arrives",
 "q_flashbulb":  "Press cameras on stands at an event barrier, out of focus lights beyond",
 "q_tvwall":     "A wall of old television screens all switched off in a dim room",

 # third wave: cues whose picture did not DEPICT the phrase. "moved to Los
 # Angeles" was pointing at an empty television studio because an earlier
 # de-duplication swap fixed a repeat and broke the meaning.
 "p_lasign":      "A wide view of the Los Angeles basin at dusk from the hills, freeways and downtown towers in haze",
 "p_lapalms":     "A Los Angeles boulevard lined with tall palm trees at golden hour, low buildings, wide establishing shot",
 "p_hospital69":  "The entrance of a modest 1960s American hospital building, warm evening light, empty forecourt",
 "p_nychome":     "A 1970s New York apartment building entrance with stone steps, autumn leaves on the pavement",
 "p_audition":    "An empty casting office waiting room with plastic chairs against a wall, harsh overhead light",
 "p_tvdial":      "A close view of an old television set switched on showing static, in a dim 1980s living room",

 # fourth wave: cues whose picture named one thing and showed another, all
 # read off frames of the V5 cut.
 # "Spinning" and "The bike" both pointed at q_spinbike, which generated a
 # ROAD bike standing in a white void - an outdoor bike under two lines about
 # indoor cycling. "The bag" pointed at q_gloves, gloves on a bench, with no
 # bag in it. "Nancy Dow, was an actress" pointed at an empty living-room set
 # that the cut had already used twice for her father.
 "q_spinbike2":   "A single indoor spin bike in a bright empty studio, side on, heavy weighted flywheel at the front, handlebars and a small console",
 "q_heavybag":    "A black leather heavy punching bag hanging from a chain in a bright empty boxing gym, morning light",
 "p_dressing":    "A vintage nineteen seventies theatre dressing room, a mirror ringed with round bulbs, a chair and a hairbrush on the counter, nobody present",
 "p_kojak":       "A nineteen seventies American living room at night, a wood cased television switched on showing an indistinct black and white police drama",
 "p_tvon":        "A close view of an old television set switched on showing an indistinct nineteen ninety sitcom living room scene, dim living room around it",
 # "Spinning" (W1) and "The bike" (W3) are fifty seconds apart and both need a
 # spin bike; one image used twice reads as an editing mistake, so there are
 # two of them, shot differently.
 "q_spinbike3":   "A row of indoor spin bikes in a dim cycling studio lit from the side, low three quarter angle, nobody riding",

 # The seven day markers. Each was an unchosen draw from the ungated week pool
 # in V5, and the pool contained a MARCH FITNESS studio segment with three men
 # in it - which held TUESDAY and SUNDAY - a GMA reporter, a red-carpet
 # step-and-repeat under FRIDAY / BOXING OR ROPE, and a woman having a facial
 # under THURSDAY / UPPER BODY AND BACK. A day card states what the day is, so
 # its picture has to show the day's work and nothing else.
 "d_monday":    "A long resistance band and ankle straps laid out beside an exercise mat on a pale studio floor, low angle, morning light",
 "d_tuesday":   "A bright empty gym with a treadmill and an indoor exercise bike standing side by side, morning light through tall windows",
 "d_wednesday": "Two small dumbbells and a rolled exercise mat on a bright studio floor seen from above, hard morning shadow",
 # first attempt generated a bare rig with nothing on it - regenerated
 "d_thursday":  "Resistance bands with handles hanging from a wall anchor in a bright gym, a bench and a rolled towel below them, side light",
 "d_friday":    "Boxing gloves and a coiled skipping rope on the floor of a bright boxing gym, a heavy bag out of focus behind",
 "d_saturday":  "An unrolled yoga mat with a foam roller and a stretching strap on a bright wooden floor, soft north light",
 "d_sunday":    "An empty sunlit bedroom with a neatly made bed and open curtains, quiet, nobody present",
}




def key() -> str:
    env = (ROOT.parent / ".env.local").read_text(encoding="utf-8")
    m = re.search(r"FAL_KEY=(\S+)", env)
    if not m:
        raise SystemExit("no FAL_KEY in .env.local")
    return m.group(1)


def main() -> None:
    K = key()
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent": 0.0, "items": {}}
    fails = 0
    for sid, base in PLACES.items():
        prompt = f"{base}, {STYLE}"
        h = hashlib.sha1(prompt.encode()).hexdigest()[:16]
        dst = OUT / f"{sid}.jpg"
        if led["items"].get(h, {}).get("state") == "done" and dst.exists():
            print(f"  {sid:<15} cached")
            continue
        if led["spent"] + COST > BUDGET:
            print("  BUDGET REACHED"); break
        if fails >= 3:
            print("  circuit breaker"); break
        try:
            r = requests.post(
                f"https://fal.run/{MODEL}",
                headers={"Authorization": f"Key {K}", "Content-Type": "application/json"},
                json={"prompt": prompt, "image_size": "landscape_16_9",
                      "num_images": 1, "num_inference_steps": 28}, timeout=180)
            if r.status_code == 200:
                led["spent"] += COST
            else:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:140]}")
            url = r.json()["images"][0]["url"]
            dst.write_bytes(requests.get(url, timeout=180).content)
            Image.open(dst).verify()
            led["items"][h] = {"id": sid, "state": "done", "url": url, "cost": COST}
            print(f"  {sid:<15} ok   ${led['spent']:.3f}")
            fails = 0
        except Exception as e:
            led["items"][h] = {"id": sid, "state": "failed", "error": str(e)[:200]}
            print(f"  {sid:<15} FAIL {str(e)[:100]}")
            fails += 1
        finally:
            LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")
            time.sleep(0.4)
    done = sum(1 for v in led["items"].values() if v.get("state") == "done")
    print(f"\n  {done} stills, spent ${led['spent']:.2f}")


if __name__ == "__main__":
    main()
