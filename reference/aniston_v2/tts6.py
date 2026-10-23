"""Narration v5 — section 2 worker. Turns script.md into audio5/ and produces
word-level timings. This is the ONLY section that spends money.

Modelled on tts4.py's structure (one ElevenLabs request per VO block,
previous_text/next_text for prosody continuity) but:

  - reads script.md + quotes.json directly, NOT script4.all_speech()/BITES
    (those are the OLD script — H2 subscribe block, biography blocks that
    no longer exist).
  - writes to audio5/ and manifest/audio5.json — NEVER touches audio4/.
  - the ledger is a real spend ledger: unit_price, api_calls_200 (incremented
    the instant an HTTP 200 comes back, before any parse/write), spent,
    prior_spend, total_project_spend. Persisted to disk after every block.
  - a global breaker halts the whole run after 3 CONSECUTIVE non-200
    responses, and a hard stop if spent would exceed $2.00.
  - after every VO block renders (or is served from cache), immediately
    runs word_times5.transcribe_block against it.
  - records an intended gap_after (seconds) per block for the downstream
    join — real pauses between thoughts, not baked into the block audio.

Run:
    python3 tts5.py
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script4 import VOICE_ID, VOICE_SETTINGS  # noqa: E402
import word_times5  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "audio6"
OUT.mkdir(exist_ok=True)
HD = ROOT / "hd"
LEDGER_PATH = ROOT / "manifest" / "audio6.json"

KEY = Path("C:/Users/avina/ytceleb/elevenlabs_key.txt").read_text(encoding="utf-8").strip()
MODEL = "eleven_multilingual_v2"
FMT = "mp3_44100_192"
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

UNIT_PRICE = 0.05
PRIOR_SPEND = 4.85
HARD_STOP_SPEND = 2.00          # this job's own spend, not counting prior
MAX_CONSECUTIVE_FAILURES = 3

HEADER_RE = re.compile(
    r"^###\s+(?P<id>\S+)\s*\|\s*kind=(?P<kind>\w+)\s*\|\s*(?P<rest>.+?)\s*$"
)


def probe(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def parse_script(path: Path) -> list[dict]:
    """Parse script.md into ordered blocks: id, kind, section/quote, text."""
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = []
    cur = None
    body: list[str] = []
    for line in lines:
        m = HEADER_RE.match(line)
        if m:
            if cur is not None:
                cur["text"] = " ".join(" ".join(body).split())
                blocks.append(cur)
            kind = m.group("kind")
            rest = m.group("rest")
            cur = {"block": m.group("id"), "kind": kind}
            if kind == "vo":
                sec = re.search(r"section=(\S+)", rest)
                cur["section"] = sec.group(1) if sec else ""
            elif kind == "bite":
                q = re.search(r"quote=(\S+)", rest)
                cur["quote"] = q.group(1) if q else ""
            body = []
        else:
            if cur is not None:
                body.append(line.strip())
    if cur is not None:
        cur["text"] = " ".join(" ".join(body).split())
        blocks.append(cur)
    return blocks


def gap_for(i: int, blocks: list[dict]) -> float:
    """Intended silent gap (seconds) after block i, for the downstream join."""
    if i == len(blocks) - 1:
        return 0.0
    cur, nxt = blocks[i], blocks[i + 1]
    if cur["kind"] == "bite" or nxt["kind"] == "bite":
        return 0.5
    if cur.get("section") != nxt.get("section"):
        return 0.7
    return 0.4


def cut_bite(block: dict, quote: dict) -> tuple[Path, float]:
    qid = quote["id"]
    vid = quote["video_id"]
    t0, t1 = quote["in_point"], quote["out_point"]
    wav = OUT / f"bite_{qid}.wav"
    if not wav.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
             "-i", str(HD / f"{vid}.mp4"), "-t", f"{t1 - t0:.3f}",
             "-vn", "-ac", "2", "-ar", "48000",
             "-af", "afade=t=in:d=0.03,afade=t=out:st=%.3f:d=0.03,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11" % max(0.0, t1 - t0 - 0.03),
             "-c:a", "pcm_s16le", str(wav)], check=True)
    return wav, probe(wav)


def load_ledger() -> dict:
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    return {"blocks": [], "api_calls_200": 0, "unit_price": UNIT_PRICE,
            "prior_spend": PRIOR_SPEND, "spent": 0.0, "total_project_spend": PRIOR_SPEND,
            "voice": VOICE_ID, "model": MODEL, "total_seconds": 0.0}


def save_ledger(ledger: dict) -> None:
    ledger["spent"] = round(ledger["api_calls_200"] * UNIT_PRICE, 2)
    ledger["total_project_spend"] = round(PRIOR_SPEND + ledger["spent"], 2)
    ledger["total_seconds"] = sum(b["seconds"] for b in ledger["blocks"])
    LEDGER_PATH.write_text(json.dumps(ledger, indent=1), encoding="utf-8")


def main() -> None:
    t_start = time.time()

    blocks = parse_script(ROOT / "script.md")
    quotes = {q["id"]: q for q in json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))}

    vo_texts = [b["text"] for b in blocks if b["kind"] == "vo"]
    vo_i = 0

    ledger = load_ledger()
    done = {b["block"]: b for b in ledger["blocks"]}
    api_calls_200 = ledger.get("api_calls_200", 0)
    consecutive_failures = 0
    wt_have = word_times5.load_word_times()

    print(f"  {len(blocks)} blocks parsed "
          f"({sum(1 for b in blocks if b['kind']=='vo')} vo, "
          f"{sum(1 for b in blocks if b['kind']=='bite')} bite)")
    print(f"  resuming with api_calls_200={api_calls_200} "
          f"(spent so far this job: ${api_calls_200*UNIT_PRICE:.2f})")

    for i, b in enumerate(blocks):
        bid = b["block"]
        gap_after = gap_for(i, blocks)

        if b["kind"] == "bite":
            quote = quotes[b["quote"]]
            wav, secs = cut_bite(b, quote)
            print(f"  {bid:<4} BITE  {secs:6.3f}s  {quote['outlet']}")
            entry = {"block": bid, "kind": "bite", "file": wav.name, "seconds": secs,
                      "quote_id": quote["id"], "source": quote["video_id"],
                      "t0": quote["in_point"], "t1": quote["out_point"],
                      "credit": quote["outlet"], "text": quote["text"],
                      "gap_after": gap_after}
            done[bid] = entry
            ledger["blocks"] = list(done.values())
            save_ledger(ledger)
            continue

        # ---- VO block ----
        payload = b["text"]

        # CACHE ON THE WORDS, NOT THE BLOCK ID.
        #
        # tts5 keyed this on `bid` plus "does the mp3 exist". That is safe only
        # while a block id means the same sentence forever. It does not: this
        # script reuses W1, W2, H1 for completely different narration, so the
        # old key would have served V10's audio under V11's words - the same
        # class of fault that once put V5's soundtrack under V6's picture, and
        # that BRIEF.md section 7 exists to prevent.
        #
        # The digest covers the text AND the voice settings, so changing either
        # re-renders and changing neither is free.
        sig = hashlib.sha1(
            (payload + VOICE_ID + MODEL + json.dumps(VOICE_SETTINGS, sort_keys=True))
            .encode("utf-8")).hexdigest()[:12]
        mp3 = OUT / f"{bid}_{sig}.mp3"

        if bid in done and done[bid].get("sig") == sig and mp3.exists():
            secs = probe(mp3)
            print(f"  {bid:<4} VO    cached {secs:6.3f}s")
            entry = dict(done[bid])
            entry.update({"seconds": secs, "sig": sig, "text": payload,
                          "gap_after": gap_after})
            done[bid] = entry
            vo_i += 1
        elif mp3.exists() and mp3.stat().st_size > 12_000:
            secs = probe(mp3)
            print(f"  {bid:<4} VO    cached (no ledger row) {secs:6.3f}s")
            entry = {"block": bid, "kind": "vo", "file": mp3.name, "seconds": secs,
                      "sig": sig, "text": payload, "gap_after": gap_after}
            done[bid] = entry
            vo_i += 1
        else:
            body = {
                "text": payload,
                "model_id": MODEL,
                "voice_settings": VOICE_SETTINGS,
                "previous_text": vo_texts[vo_i - 1] if vo_i > 0 else None,
                "next_text": vo_texts[vo_i + 1] if vo_i + 1 < len(vo_texts) else None,
            }
            got_200 = False
            while not got_200:
                r = requests.post(URL, params={"output_format": FMT},
                                  headers={"xi-api-key": KEY,
                                           "Content-Type": "application/json"},
                                  json=body, timeout=300)
                if r.status_code == 200:
                    # charge the instant the 200 comes back, before parse/write
                    api_calls_200 += 1
                    consecutive_failures = 0
                    ledger["api_calls_200"] = api_calls_200
                    save_ledger(ledger)
                    got_200 = True
                    spent_now = round(api_calls_200 * UNIT_PRICE, 2)
                    if spent_now > HARD_STOP_SPEND:
                        print(f"  HARD STOP: spend ${spent_now:.2f} exceeds "
                              f"${HARD_STOP_SPEND:.2f} job cap. Halting after charge, "
                              f"before writing {bid}.")
                        raise SystemExit(1)
                    mp3.write_bytes(r.content)
                else:
                    consecutive_failures += 1
                    print(f"  {bid} HTTP {r.status_code} "
                          f"(consecutive failure {consecutive_failures}): {r.text[:160]}")
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        print("  HALT: 3 consecutive non-200 responses. Stopping.")
                        raise SystemExit(1)
                    time.sleep(4 * consecutive_failures)

            secs = probe(mp3)
            wpm = len(payload.split()) / secs * 60
            print(f"  {bid:<4} VO    {secs:6.3f}s  {len(payload.split()):>4}w  {wpm:5.1f} wpm  "
                  f"[api_calls_200={api_calls_200} spent=${api_calls_200*UNIT_PRICE:.2f}]")
            entry = {"block": bid, "kind": "vo", "file": mp3.name, "seconds": secs,
                      "sig": sig, "text": payload, "gap_after": gap_after}
            done[bid] = entry
            vo_i += 1

        ledger["blocks"] = list(done.values())
        save_ledger(ledger)

        # word-level timings, right after this block renders
        words = word_times5.transcribe_block(bid, OUT / entry["file"], wt_have)
        span = words[-1][2] if words else 0.0
        print(f"       whisper {len(words):>4} words  {span:6.2f}s")

    runtime = time.time() - t_start
    total = sum(x["seconds"] for x in ledger["blocks"])
    bite_secs = sum(x["seconds"] for x in ledger["blocks"] if x["kind"] == "bite")
    print(f"\nTOTAL {total:.2f}s = {int(total)//60}:{total%60:05.2f}")
    print(f"  narrator {total-bite_secs:7.1f}s   her {bite_secs:6.1f}s "
          f"({bite_secs/total*100:.0f}%)")
    print(f"  api_calls_200={ledger['api_calls_200']}  spent=${ledger['spent']:.2f}  "
          f"total_project_spend=${ledger['total_project_spend']:.2f}")
    print(f"  runtime {runtime:.1f}s = {runtime/60:.2f} min")


if __name__ == "__main__":
    main()
