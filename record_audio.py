from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import sounddevice as sd
import soundfile as sf


DEFAULT_SECONDS = 600
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
AUTO_DEVICE_KEYWORD = "USB PHONE"


def list_input_devices() -> None:
    print("Input devices:")
    for index, device in enumerate(sd.query_devices()):
        max_inputs = int(device.get("max_input_channels", 0))
        if max_inputs <= 0:
            continue
        name = device.get("name", "(unknown)")
        default_sr = int(device.get("default_samplerate", 0))
        print(
            f"  [{index}] {name} | inputs={max_inputs} | default_samplerate={default_sr}"
        )


def auto_select_device_index() -> int:
    keyword = AUTO_DEVICE_KEYWORD.lower()
    for index, device in enumerate(sd.query_devices()):
        if int(device.get("max_input_channels", 0)) <= 0:
            continue
        name = str(device.get("name", ""))
        if keyword in name.lower():
            return index
    raise RuntimeError(
        f"入力デバイス名に '{AUTO_DEVICE_KEYWORD}' を含むデバイスが見つかりませんでした。\n"
        "`python record_audio.py --list-devices` でデバイス一覧を確認し、"
        "`--device-index` を指定してください。"
    )


def default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("audio") / f"record_{timestamp}.wav"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record audio from USB microphone and save 16kHz mono WAV."
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available input devices and exit.",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=DEFAULT_SECONDS,
        help=f"Recording seconds (default: {DEFAULT_SECONDS}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=default_output_path(),
        help="Output WAV path (default: audio/record_YYYYmmdd_HHMMSS.wav).",
    )
    parser.add_argument(
        "--device-index",
        type=int,
        default=None,
        help="Input device index. If omitted, auto-selects a device containing 'USB PHONE'.",
    )
    return parser.parse_args()


def record_to_wav(out_path: Path, seconds: int, device_index: int) -> None:
    if seconds <= 0:
        raise ValueError("--seconds は1以上を指定してください。")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Recording device index: {device_index}")
    print(f"Output path: {out_path}")
    print(
        f"Format: {DEFAULT_SAMPLE_RATE} Hz, {DEFAULT_CHANNELS} channel(s), PCM_16 | Duration: {seconds} sec"
    )

    blocksize = DEFAULT_SAMPLE_RATE
    elapsed = 0

    try:
        with sf.SoundFile(
            str(out_path),
            mode="w",
            samplerate=DEFAULT_SAMPLE_RATE,
            channels=DEFAULT_CHANNELS,
            subtype="PCM_16",
        ) as wav_file:
            with sd.InputStream(
                samplerate=DEFAULT_SAMPLE_RATE,
                channels=DEFAULT_CHANNELS,
                dtype="int16",
                device=device_index,
                blocksize=blocksize,
            ) as stream:
                print("Recording started... Press Ctrl+C to stop early.")
                while elapsed < seconds:
                    data, overflowed = stream.read(blocksize)
                    if overflowed:
                        print("Warning: input overflow detected.", file=sys.stderr)
                    wav_file.write(data)
                    elapsed += 1
                    print(f"Elapsed: {elapsed}/{seconds} sec")
    except KeyboardInterrupt:
        print(f"\nRecording interrupted at {elapsed} sec. Partial audio saved: {out_path}")
        return

    print(f"Recording finished. Saved: {out_path}")


def main() -> None:
    args = parse_args()

    try:
        if args.list_devices:
            list_input_devices()
            return

        if args.device_index is not None:
            device_index = args.device_index
        else:
            device_index = auto_select_device_index()

        record_to_wav(out_path=args.out, seconds=args.seconds, device_index=device_index)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
