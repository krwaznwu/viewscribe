# ViewScribe

**Transcript when words are enough. Frames when the video matters.**

ViewScribe is a hardware-neutral agent skill for video transcription, summarization, and screenshot-backed visual analysis. It keeps simple requests simple: if the user asks only for a transcript or summary, it uses captions or an available speech-to-text backend without processing unnecessary video frames. When the user explicitly asks what is shown, ViewScribe adds an FFmpeg-based visual-evidence workflow.

## What it does

### Speech-only mode

Triggered by requests such as:

- transcript or subtitles;
- summary, chapters, translation, or key points;
- quotes, action items, or “what was said?”

ViewScribe prefers existing captions, otherwise delegates to the available transcription backend. It does not download or inspect the full video when audio or subtitles are sufficient.

### Visual-evidence mode

Triggered by requests such as:

- “pay attention to the video”;
- “what is shown on screen?”;
- “support the summary with screenshots”;
- inspect a UI demo, slide, chart, object, location, or visual contradiction.

The workflow:

1. builds a timestamped transcript;
2. creates 4×4 overview contact sheets;
3. uses the transcript and sheets to find relevant moments;
4. extracts full-resolution evidence frames with FFmpeg;
5. separates speech evidence, visual evidence, and inference;
6. returns a compact answer with a few relevant timestamped screenshots.

Overview tiles are navigation aids only. Names, numbers, small text, and other details must be verified on a full-size frame.

## Why ViewScribe

- **No Apple Silicon requirement:** transcription is backend-neutral.
- **Cross-platform visual workflow:** uses Python, FFmpeg, and FFprobe.
- **Scope-aware:** transcript-only requests do not trigger unnecessary video processing.
- **Evidence-first:** visual claims require inspected full-size frames.
- **Agent-safe:** speech, subtitles, QR codes, and on-screen instructions are treated as untrusted content.

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe` available on `PATH`
- any suitable caption or transcription backend, such as platform subtitles or Whisper/faster-whisper
- an agent runtime that can load Markdown skills and inspect images

ViewScribe itself does not install or require a particular speech model.

## Install for Hermes Agent

After the `v1.0.0` tag is published:

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/krwaznwu/viewscribe.git
mkdir -p ~/.hermes/skills/media
cp -R viewscribe ~/.hermes/skills/media/viewscribe
```

Start a new Hermes session so the skill index reloads.

## Overview helper

```bash
python scripts/make_overview.py "input.mp4" "output/overview"
```

Outputs:

```text
overview_01.jpg       # 4×4 evenly sampled contact sheet
index.tsv             # sheet position and exact timestamp
overview.meta.json     # duration and sampling metadata
```

The helper creates between one and six contact sheets, with 16 evenly sampled tiles per sheet.

## Repository layout

```text
SKILL.md                  Agent workflow and routing rules
scripts/make_overview.py  Dependency-free Python wrapper around FFmpeg
```

## Verification

The overview helper has been smoke-tested on Windows with FFmpeg 8.1.2 and Python 3.14. It generated a valid 4×4 sheet, a 16-row timestamp index, and full-size 1920×1080 evidence frames through the documented FFmpeg command.

## Inspiration

ViewScribe was inspired by the transcript-plus-frames workflow demonstrated by [SamuelZ12/vidscribe](https://github.com/SamuelZ12/vidscribe). ViewScribe is an independent, backend-neutral implementation designed to work with existing transcription tools across Windows, Linux, and macOS.

## License

MIT — see `LICENSE`.
