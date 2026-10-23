from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import torch
import torchaudio
from chatterbox.tts_turbo import ChatterboxTurboTTS
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
SCRIPT = ROOT / "script_v3.md"
QUOTES = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
BLOCK_DIR = ROOT / "assets" / "audio" / "blocks"
CHUNK_DIR = ROOT / "assets" / "audio" / "chunks"
REFERENCE = PROJECT / "work" / "voicetest_am_michael.wav"
RAW_MASTER = ROOT / "assets" / "audio" / "narration_raw.wav"
MASTER = ROOT / "assets" / "audio" / "narration.wav"
MANIFEST = ROOT / "audio_manifest.json"
FINAL_MIX_DIR = ROOT / "assets" / "audio" / "final_mix"
FINAL_IDS = {"E1V4", "E2V4", "E3", "E4V4"}


def parse_script() -> list[dict]:
    header = re.compile(r"^###\s+([^|]+?)\s*\|\s*kind=(vo|bite)(?:\s*\|\s*quote=([^\s]+))?.*$")
    blocks: list[dict] = []
    current: dict | None = None
    for raw in SCRIPT.read_text(encoding="utf-8").splitlines():
        match = header.match(raw.strip())
        if match:
            if current:
                current["text"] = " ".join(current.pop("lines")).strip()
                blocks.append(current)
            current = {"id": match.group(1).strip(), "kind": match.group(2), "quote": match.group(3), "lines": []}
        elif current and raw.strip():
            current["lines"].append(raw.strip())
    if current:
        current["text"] = " ".join(current.pop("lines")).strip()
        blocks.append(current)
    return blocks


def sentence_chunks(text: str, max_chars: int = 260) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def trim_edges(audio: AudioSegment, threshold: float = -44.0, pad_ms: int = 65) -> AudioSegment:
    if audio.dBFS == float("-inf"):
        return audio
    ranges = detect_nonsilent(audio, min_silence_len=70, silence_thresh=threshold, seek_step=5)
    if not ranges:
        return audio
    start = max(0, ranges[0][0] - pad_ms)
    end = min(len(audio), ranges[-1][1] + pad_ms)
    return audio[start:end]


def standardize(audio: AudioSegment) -> AudioSegment:
    return audio.set_frame_rate(48000).set_channels(2).set_sample_width(2)


def render_voice(model: ChatterboxTurboTTS, block_id: str, text: str) -> Path:
    out = BLOCK_DIR / f"{block_id}.wav"
    if out.exists() and out.stat().st_size > 10_000:
        return out
    joined = AudioSegment.silent(duration=0, frame_rate=48000).set_channels(2)
    for index, chunk in enumerate(sentence_chunks(text)):
        chunk_path = CHUNK_DIR / f"{block_id}_{index:02d}.wav"
        if not chunk_path.exists() or chunk_path.stat().st_size < 10_000:
            torch.manual_seed(2300 + sum(ord(c) for c in block_id) + index)
            wav = model.generate(
                chunk,
                repetition_penalty=1.24,
                top_p=0.92,
                temperature=0.67,
                top_k=700,
            )
            torchaudio.save(str(chunk_path), wav, model.sr)
        piece = standardize(trim_edges(AudioSegment.from_wav(chunk_path)))
        if index:
            joined += AudioSegment.silent(duration=90, frame_rate=48000).set_channels(2)
        joined += piece
    joined.export(out, format="wav")
    return out


def render_bite(block: dict) -> Path:
    quote_id = block["quote"]
    source = PROJECT / "bites" / f"{quote_id}.wav"
    if not source.exists():
        raise FileNotFoundError(source)
    out = BLOCK_DIR / f"{block['id']}.wav"
    if not out.exists() or out.stat().st_size < 10_000:
        bite = standardize(trim_edges(AudioSegment.from_wav(source), threshold=-48.0, pad_ms=90))
        bite = bite.fade_in(25).fade_out(35)
        bite.export(out, format="wav")
    return out


def loudness_normalize() -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "warning", "-i", str(RAW_MASTER),
            "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=8,alimiter=limit=0.84:level=false",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(MASTER),
        ],
        check=True,
    )


def final_mix_path(block_id: str, source: Path) -> Path:
    """Give the rebuilt closing minute one consistent, restrained broadcast contour."""
    if block_id not in FINAL_IDS:
        return source
    FINAL_MIX_DIR.mkdir(parents=True, exist_ok=True)
    out = FINAL_MIX_DIR / f"{block_id}.wav"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    target = "-21.0" if block_id == "E3" else "-20.5"
    lowpass = "12000" if block_id == "E3" else "16000"
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "warning", "-i", str(source),
            "-af", f"highpass=f=70,lowpass=f={lowpass},loudnorm=I={target}:TP=-4:LRA=5",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(out),
        ],
        check=True,
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--assemble-only", action="store_true")
    args = parser.parse_args()

    BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_MIX_DIR.mkdir(parents=True, exist_ok=True)
    blocks = parse_script()
    voice_blocks = [b for b in blocks if b["kind"] == "vo"]
    if args.shard_count > 1:
        voice_blocks = [b for index, b in enumerate(voice_blocks) if index % args.shard_count == args.shard_index]
    if args.test:
        voice_blocks = voice_blocks[:1]

    if not args.assemble_only:
        thread_cap = 4 if args.shard_count > 1 else 12
        torch.set_num_threads(max(2, min(thread_cap, (torch.get_num_threads() or 8))))
        print("Loading Chatterbox Nano on CPU...", flush=True)
        model = ChatterboxTurboTTS.from_pretrained(device="cpu", nano=True)
        model.prepare_conditionals(str(REFERENCE), exaggeration=0.0, norm_loudness=True)
        print(f"Loaded {model.model_label} at {model.sr} Hz", flush=True)

        for index, block in enumerate(voice_blocks, 1):
            print(f"VOICE {index:02d}/{len(voice_blocks):02d} {block['id']}", flush=True)
            render_voice(model, block["id"], block["text"])
    if args.test:
        print(BLOCK_DIR / f"{voice_blocks[0]['id']}.wav")
        return
    if args.shard_count > 1:
        print(f"SHARD {args.shard_index + 1}/{args.shard_count} COMPLETE", flush=True)
        return

    for block in blocks:
        if block["kind"] == "bite" and not args.assemble_only:
            render_bite(block)

    master = AudioSegment.silent(duration=0, frame_rate=48000).set_channels(2)
    timeline: list[dict] = []
    previous_section = None
    script_text = SCRIPT.read_text(encoding="utf-8")
    sections = {}
    for match in re.finditer(r"^###\s+([^|]+?)\s*\|.*?section=([^\s]+)", script_text, flags=re.M):
        sections[match.group(1).strip()] = match.group(2).strip()

    for index, block in enumerate(blocks):
        if index:
            section = sections.get(block["id"])
            if section == "end":
                gap = 520 if section != previous_section else 380
            else:
                gap = 360 if section and section != previous_section else 235
            master += AudioSegment.silent(duration=gap, frame_rate=48000).set_channels(2)
        start_ms = len(master)
        path = BLOCK_DIR / f"{block['id']}.wav"
        path = final_mix_path(block["id"], path)
        if block["id"] in FINAL_IDS:
            edge = 120 if block["id"] == "E3" else 80
            piece = standardize(AudioSegment.from_wav(path)).fade_in(edge).fade_out(edge + 20)
        else:
            piece = standardize(AudioSegment.from_wav(path)).fade_in(18).fade_out(25)
        master += piece
        end_ms = len(master)
        timeline.append(
            {
                "id": block["id"],
                "kind": block["kind"],
                "quote": block.get("quote"),
                "source": QUOTES.get(block.get("quote") or "", {}).get("src"),
                "start": round(start_ms / 1000, 3),
                "duration": round((end_ms - start_ms) / 1000, 3),
                "end": round(end_ms / 1000, 3),
            }
        )
        previous_section = sections.get(block["id"])

    master += AudioSegment.silent(duration=500, frame_rate=48000).set_channels(2)
    master.export(RAW_MASTER, format="wav")
    loudness_normalize()
    payload = {
        "engine": "Resemble AI Chatterbox Nano",
        "model_repo": "ResembleAI/chatterbox-nano",
        "voice_reference": str(REFERENCE),
        "sample_rate": 48000,
        "duration": round(len(master) / 1000, 3),
        "blocks": timeline,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"MASTER {MASTER} ({len(master) / 1000:.3f}s)", flush=True)


if __name__ == "__main__":
    main()
