# ローカル文字起こしパイプライン（Step1）

USBマイクで録音したWAVを `whisper.cpp` で文字起こしし、後段LLM処理に渡しやすい `.txt` と `.json` を生成します。

## ディレクトリ構成

- `audio/` : 入力WAV
- `transcripts/` : 出力（`<base>.txt` / `<base>.json`）
- `models/` : `ggml` モデル格納
- `bin/whispercpp/` : `whisper-cli.exe` 格納
- `config.yaml` : 実行設定
- `transcribe_batch.py` : 一括文字起こし
- `utils.py` : 共通処理（設定読み込み・実行・ログ）
- `record_windows.md` : Audacity録音手順

## 事前準備

1. `whisper.cpp` の実行ファイルを配置
   - 例: `bin/whispercpp/whisper-cli.exe`
2. `ggml` モデルを配置
   - 例: `models/ggml-base.bin`
3. 必要に応じて設定を更新
   - `config.yaml`

## 依存関係

- Python標準ライブラリ
- `PyYAML`（`config.yaml` を使う場合）

```powershell
pip install pyyaml
```

> YAML依存を避けたい場合は、`config.json` を作成して `--config` で指定可能です。

## 実行例

### 通常実行

```powershell
python transcribe_batch.py --config config.yaml
```

### 既存JSONがある音声をスキップ

```powershell
python transcribe_batch.py --config config.yaml --skip-existing
```

## 出力仕様

### `transcripts/<base>.txt`
- 生テキスト

### `transcripts/<base>.json`
- メタ情報付き
- キー:
  - `input_path`
  - `started_at`
  - `ended_at`
  - `language`
  - `model`
  - `transcript_text`
  - `whisper_cmd`
  - `return_code`
