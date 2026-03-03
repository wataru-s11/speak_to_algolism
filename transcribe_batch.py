from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from utils import (
    ensure_directories,
    decode_output_bytes,
    load_config,
    project_root_from_config,
    resolve_path,
    run_command,
    setup_logger,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def discover_wavs(audio_dir: Path) -> List[Path]:
    return sorted(audio_dir.glob("*.wav"))


def read_transcript_text(transcript_txt: Path, fallback: str = "") -> str:
    if transcript_txt.exists():
        return transcript_txt.read_text(encoding="utf-8", errors="ignore").strip()
    return fallback.strip()


def transcribe_file(
    wav_path: Path,
    transcripts_dir: Path,
    whisper_exe: Path,
    model_path: Path,
    language: str,
    logger,
) -> Dict[str, Any]:
    base = wav_path.stem
    transcript_txt = transcripts_dir / f"{base}.txt"
    transcript_json = transcripts_dir / f"{base}.json"
    output_base = transcripts_dir / base

    started_at = utc_now_iso()

    command = [
        str(whisper_exe),
        "-m",
        str(model_path),
        "-f",
        str(wav_path),
        "-l",
        language,
        "-otxt",
        "-of",
        str(output_base),
    ]

    return_code = -1
    try:
        result = run_command(command, logger)
        return_code = result.returncode
        transcript_text = read_transcript_text(
            transcript_txt, fallback=decode_output_bytes(result.stdout)
        )
    except subprocess.CalledProcessError as exc:
        return_code = exc.returncode
        logger.exception("Transcription failed for '%s'", wav_path)
        raise

    ended_at = utc_now_iso()

    payload: Dict[str, Any] = {
        "input_path": str(wav_path),
        "started_at": started_at,
        "ended_at": ended_at,
        "language": language,
        "model": str(model_path),
        "transcript_text": transcript_text,
        "whisper_cmd": command,
        "return_code": return_code,
    }

    transcript_txt.write_text(transcript_text + "\n", encoding="utf-8")
    transcript_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch transcribe WAV files using whisper.cpp and save txt + json outputs."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file (YAML or JSON). Default: config.yaml",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip WAV files that already have transcripts/<base>.json",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logger = setup_logger(verbose=args.verbose)
    config = load_config(args.config)

    root = project_root_from_config(args.config)
    audio_dir = resolve_path(root, config.get("audio_dir", "audio"))
    transcripts_dir = resolve_path(root, config.get("transcripts_dir", "transcripts"))
    whisper_exe = resolve_path(root, config["whisper_exe"])
    model_path = resolve_path(root, config["model_path"])
    language = config.get("language", "ja")

    ensure_directories([audio_dir, transcripts_dir])

    if not whisper_exe.exists():
        raise FileNotFoundError(f"whisper executable not found: {whisper_exe}")
    if not model_path.exists():
        raise FileNotFoundError(f"whisper model not found: {model_path}")

    wav_files = discover_wavs(audio_dir)
    if not wav_files:
        logger.info("No WAV files found in: %s", audio_dir)
        return

    logger.info("Found %d WAV file(s)", len(wav_files))

    processed = 0
    skipped = 0
    for wav_path in wav_files:
        out_json = transcripts_dir / f"{wav_path.stem}.json"
        if args.skip_existing and out_json.exists():
            skipped += 1
            logger.info("Skipping (already exists): %s", wav_path.name)
            continue

        logger.info("Transcribing: %s", wav_path.name)
        transcribe_file(
            wav_path=wav_path,
            transcripts_dir=transcripts_dir,
            whisper_exe=whisper_exe,
            model_path=model_path,
            language=language,
            logger=logger,
        )
        processed += 1

    logger.info("Done. processed=%d skipped=%d", processed, skipped)


if __name__ == "__main__":
    main()
