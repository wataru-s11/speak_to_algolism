# Windows録音手順（Audacity）

Step1ではリアルタイム録音機能は実装せず、`audio/` に配置したWAVファイルを処理します。以下は推奨録音手順です。

1. Audacityを起動する。
2. 録音デバイスに **USB PHONE** を選択する。
3. チャンネルを **Mono** に設定する。
4. プロジェクトレートを **16000 Hz** に設定する。
5. 録音して内容を確認する。
6. `ファイル` → `書き出し` → `WAV (Microsoft) signed 16-bit PCM` で保存する。
7. 保存した `.wav` ファイルを本プロジェクトの `audio/` フォルダへコピーする。

この後、`transcribe_batch.py` を実行すると `transcripts/` に `.txt` と `.json` が出力されます。
