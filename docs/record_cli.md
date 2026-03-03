# `record_audio.py` 使い方

USBマイク（デバイス名に `USB PHONE` を含む）から音声を録音し、`audio/` 配下に 16kHz mono WAV を保存するCLIです。

## インストール

```powershell
pip install -r requirements.txt
```

## デバイス一覧表示

```powershell
python record_audio.py --list-devices
```

入力デバイスの index を確認できます。`USB PHONE` を含むデバイスがあるか確認してください。

## 録音（基本）

```powershell
python record_audio.py --seconds 600 --out audio/test_10min.wav
```

- サンプルレート: `16000`
- チャンネル: `1`（mono）
- 1秒ごとに経過秒数を表示
- `Ctrl+C` で中断すると、その時点までの音声を保存

## デバイス選択

### 自動選択（既定）

`--device-index` を指定しない場合、入力デバイス名に `USB PHONE` を含む最初のデバイスを自動選択します。

### 明示指定

```powershell
python record_audio.py --device-index 3 --seconds 60 --out audio/test.wav
```

## 既定値

- `--seconds`: `600`
- `--out`: `audio/record_YYYYmmdd_HHMMSS.wav`
