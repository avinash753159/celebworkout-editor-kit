"""Food stills for the diet section.

The reference spends ~23% of its runtime on the diet, cutting every second or
two over food footage while the narrator reads the lists. V3 had four food
stills, which at this cutting rate is nowhere near enough - the same plate
would come back a dozen times.

Same ledger discipline as stills_gen.py: charge on API acceptance, cache on a
fingerprint of the prompt, circuit-break on three consecutive failures.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stills_food"
OUT.mkdir(exist_ok=True)
LEDGER = ROOT / "manifest" / "food_ledger.json"

MODEL = "fal-ai/flux/dev"
COST = 0.025
BUDGET = 2.00

STYLE = ("shot on 35mm, shallow depth of field, soft natural window light, "
         "appetising food photography, natural colour, mild grain, "
         "photographic not rendered, no text, no labels, no branding, "
         "no packaging, no hands, no people, 16:9")

FOOD = {
 # fruits
 "f_berries":   "A bowl of mixed berries, blueberries raspberries blackberries strawberries, overhead on a pale wooden table",
 "f_apples":    "Whole red and green apples in a shallow ceramic bowl on a kitchen counter",
 "f_bananas":   "A bunch of ripe bananas on a marble counter beside a glass of water",
 "f_stonefruit":"Halved peaches and plums on a slate board, cut faces up",
 "f_kiwi":      "Sliced kiwi fruit fanned on a white plate, close and overhead",
 # vegetables
 "f_greens":    "A pile of fresh spinach and kale leaves on a wooden board, close",
 "f_broccoli":  "Raw broccoli florets and celery sticks arranged on a pale board",
 "f_tomatoes":  "Ripe tomatoes on the vine beside sliced mushrooms on a dark board",
 "f_sweetpot":  "Roasted sweet potato wedges on a baking tray, close and warm",
 "f_saladbowl": "A large green salad bowl with leaves, tomato and cucumber, overhead",
 # proteins
 "f_chicken":   "A grilled chicken breast sliced on a white plate with green salad",
 "f_fish":      "A cooked salmon fillet on a plate with steamed greens and lemon",
 "f_eggs2":     "Two poached eggs on avocado toast on a white plate, overhead",
 "f_turkey":    "Sliced lean turkey breast on a board with herbs",
 # grains
 "f_quinoa":    "A bowl of cooked quinoa and couscous side by side on a linen cloth",
 "f_oats":      "A bowl of porridge oats topped with berries and seeds, overhead",
 "f_rice":      "A bowl of brown rice beside whole wheat pasta on a wooden surface",
 # fats
 "f_oliveoil":  "Olive oil being poured into a small dish beside whole olives",
 "f_avocado":   "A halved avocado on a board beside almonds and walnuts",
 "f_nuts":      "Assorted nuts and seeds in small wooden bowls, overhead, close",
 # beverages
 "f_water2":    "A tall glass of iced water with lemon on a bright kitchen counter",
 "f_coffee2":   "A cup of black coffee on a saucer beside a small jug, morning light",
 "f_tea":       "A glass cup of herbal tea with mint leaves on a pale surface",
 "f_juice":     "A glass of fresh green celery juice on a kitchen counter",
 # meals / context
 "f_lasagna":   "A slice of vegetable lasagna on a plate, close, warm light",
 "f_burger":    "A grilled chicken burger in a wholemeal bun on a board",
 "f_smoothie":  "A blended berry smoothie in a tall glass with a banana beside it",
 "f_mexican":   "Tacos with fresh salsa and lime on a rustic plate, overhead",
 "f_froyo2":    "A bowl of frozen yogurt topped with granola on a counter at night",
 "f_clock":     "An empty plate and a fork on a table beside a wall clock, muted",

 # second wave: the diet section runs ~117s at 1.6s a shot, so 30 stills meant
 # each plate came back 2.4 times. These take it under 1.6.
 "f_berries2":  "Fresh strawberries and raspberries spilling from a punnet onto a wooden board",
 "f_citrus":    "Halved oranges and lemons on a pale marble surface, overhead",
 "f_melon":     "Sliced watermelon and cantaloupe on a white plate, close",
 "f_peppers":   "Red yellow and green peppers on a wooden board beside a knife",
 "f_cucumber":  "Sliced cucumber and cherry tomatoes in a glass bowl, overhead",
 "f_asparagus": "Roasted asparagus spears on a baking tray with lemon",
 "f_eggs3":     "Soft boiled eggs halved on a plate with sourdough toast",
 "f_prawns":    "Grilled prawns on a plate with fresh herbs and lime",
 "f_steak":     "A lean sliced steak on a board with rocket leaves",
 "f_lentils":   "A bowl of cooked lentils and grains with parsley, overhead",
 "f_bread":     "Sliced wholemeal seeded bread on a wooden board",
 "f_porridge":  "A bowl of oatmeal with sliced banana and honey, morning light",
 # first generation came back a squash and chickpea stew, which went to air
 # under HEALTHY FATS / SEEDS. Regenerated with the seeds spilled, not plated,
 # so there is nothing for the model to read as a cooked dish.
 "f_seeds":     "Raw pumpkin seeds, sunflower seeds and chia seeds spilled in separate heaps on a dark stone surface, close and directly overhead, no bowl, no dish, uncooked",
 "f_olives":    "Green and black olives in a shallow dish beside olive oil",
 "f_greentea":  "A glass teapot and cup of green tea on a pale surface",
 "f_lemonwater":"A glass of water with lemon slices on a kitchen counter, morning",
 "f_saladplate":"A composed salad with grilled chicken and avocado, overhead",
 "f_soup":      "A bowl of vegetable soup with bread on a wooden table",
}



def key() -> str:
    env = (ROOT.parent / ".env.local").read_text(encoding="utf-8")
    m = re.search(r"FAL_KEY=(\S+)", env)
    if not m:
        raise SystemExit("no FAL_KEY in .env.local")
    k = m.group(1)
    print(f"  key from .env.local: {k[:6]}...{k[-4:]}")
    return k


def fp(prompt: str) -> str:
    return hashlib.sha1(prompt.encode()).hexdigest()[:16]


def main() -> None:
    K = key()
    led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent": 0.0, "items": {}}
    fails = 0
    for sid, base in FOOD.items():
        prompt = f"{base}, {STYLE}"
        h = fp(prompt)
        rec = led["items"].get(h)
        dst = OUT / f"{sid}.jpg"
        if rec and rec.get("state") == "done" and dst.exists():
            print(f"  {sid:<12} cached")
            continue
        if led["spent"] + COST > BUDGET:
            print("  BUDGET REACHED - stopping")
            break
        if fails >= 3:
            print("  3 consecutive failures - circuit breaker, stopping")
            break
        try:
            r = requests.post(
                f"https://fal.run/{MODEL}",
                headers={"Authorization": f"Key {K}", "Content-Type": "application/json"},
                json={"prompt": prompt, "image_size": "landscape_16_9",
                      "num_images": 1, "num_inference_steps": 28},
                timeout=180)
            accepted = r.status_code == 200
            if accepted:                       # charge on acceptance
                led["spent"] += COST
            if not accepted:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:160]}")
            url = r.json()["images"][0]["url"]
            img = requests.get(url, timeout=180).content
            dst.write_bytes(img)
            Image.open(dst).verify()
            led["items"][h] = {"id": sid, "state": "done", "url": url,
                               "cost": COST, "prompt": prompt}
            print(f"  {sid:<12} ok    ${led['spent']:.3f}")
            fails = 0
        except Exception as e:
            led["items"][h] = {"id": sid, "state": "failed", "error": str(e)[:200]}
            print(f"  {sid:<12} FAIL  {str(e)[:110]}")
            fails += 1
        finally:
            LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")
            time.sleep(0.4)

    done = sum(1 for v in led["items"].values() if v.get("state") == "done")
    print(f"\n  {done} stills, spent ${led['spent']:.2f}")


if __name__ == "__main__":
    main()
