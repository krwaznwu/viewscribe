#!/usr/bin/env python3
"""Create evenly sampled 4x4 video overview sheets using ffmpeg."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def duration_seconds(ffprobe: str, source: Path) -> float:
    result = run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(source)], capture=True)
    value = result.stdout.strip()
    duration = float(value)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"invalid media duration: {value!r}")
    return duration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input video file")
    parser.add_argument("output", type=Path, help="output directory")
    parser.add_argument("--sheets", type=int, choices=range(1, 7), help="force 1-6 sheets")
    parser.add_argument("--height", type=int, default=178, help="tile height (default: 178)")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        parser.error("ffmpeg and ffprobe must be available on PATH")
    if not args.input.is_file():
        parser.error(f"input file not found: {args.input}")

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("overview_*.jpg"):
        stale.unlink()
    for stale_name in ("index.tsv", "overview.meta.json"):
        (out / stale_name).unlink(missing_ok=True)
    duration = duration_seconds(ffprobe, args.input.resolve())
    sheets = args.sheets or min(6, max(1, math.floor(duration / 160 + 0.5)))
    count = sheets * 16
    times = [duration * (i + 0.5) / count for i in range(count)]
    tile_h = args.height
    tile_w = round(tile_h * 16 / 9)
    if tile_w % 2:
        tile_w += 1

    with tempfile.TemporaryDirectory(prefix="video-overview-") as tmp_name:
        tmp = Path(tmp_name)
        for i, sec in enumerate(times):
            frame = tmp / f"frame_{i:04d}.jpg"
            run([ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-ss", f"{sec:.3f}", "-i", str(args.input.resolve()), "-frames:v", "1", "-q:v", "3", "-vf", f"scale={tile_w}:{tile_h}:force_original_aspect_ratio=decrease,pad={tile_w}:{tile_h}:(ow-iw)/2:(oh-ih)/2:color=black", str(frame)])
            if not frame.exists() or frame.stat().st_size == 0:
                raise RuntimeError(f"ffmpeg produced no frame at {timestamp(sec)}")

        for sheet in range(sheets):
            target = out / f"overview_{sheet + 1:02d}.jpg"
            run([ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-framerate", "1", "-start_number", str(sheet * 16), "-i", str(tmp / "frame_%04d.jpg"), "-frames:v", "1", "-vf", "tile=4x4:nb_frames=16:padding=2:margin=1:color=white", "-q:v", "3", str(target)])
            if not target.exists() or target.stat().st_size == 0:
                raise RuntimeError(f"failed to create {target.name}")

    with (out / "index.tsv").open("w", encoding="utf-8", newline="") as handle:
        handle.write("sheet\ttile\tseconds\ttimestamp\n")
        for i, sec in enumerate(times):
            handle.write(f"overview_{i // 16 + 1:02d}.jpg\t{i % 16 + 1:02d}\t{sec:.3f}\t{timestamp(sec)}\n")

    meta = {"input": str(args.input.resolve()), "duration_seconds": duration, "sheets": sheets, "tiles": count, "tile_size": [tile_w, tile_h], "sampling": "even midpoint"}
    (out / "overview.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"command failed with exit code {exc.returncode}", file=sys.stderr)
        raise SystemExit(exc.returncode)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
