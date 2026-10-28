# 取り込み（`gpl intake`）の仕様

曲フォルダに書き出された WAV に、曲・録音日・BPM を付けてアーカイブへ移し、記録する。

## フォルダ構成

```text
<songs_root>/                 曲フォルダの親（DAW の書き出し先）
  chromatic/
    Export.wav                ← DAW が書き出した WAV（名前は何でもよい）
  song-a/

<archive_dir>/                取り込み後の WAV
  chromatic/
    20261021_chromatic_120.wav
  song-a/
    20261021_song-a_100.wav
```

## 処理の流れ

1. **走査**: 台帳に登録された曲ごとに、曲フォルダの WAV（拡張子 `.wav`、大文字小文字は区別しない）を探す。
   - 0 本: 何もしない。
   - 1 本: 取り込みの対象にする。録音日はファイルの更新日時（ローカル時刻）。
   - 2 本以上: その曲は飛ばし、警告を出す。
   - 台帳にないフォルダが `songs_root` にあれば、警告を出す。
2. **BPM の入力**: 対象の曲ごとに BPM を聞く。初期値はその曲の直近のテイクの BPM。正の整数でなければ聞き直す。初期値がなく空のまま Enter を押した場合も聞き直す。
3. **確認**: 一覧を表示し、`y` で確定する。`y` 以外ならここで終了し、ファイルは動かさない。
4. **実行**: 対象ごとに次の順で処理する。
   1. 元の WAV にメタデータを書き込む
   2. アーカイブへ移動する
   3. SQLite に記録する

## ファイル名の規則

```text
<archive_dir>/<曲 ID>/<録音日 YYYYMMDD>_<曲 ID>_<BPM>.wav
```

同じ名前のファイルがあれば（同じ日に同じ曲を 2 回取り込んだ場合など）、`_2`、`_3` と連番を付ける。

## WAV のメタデータ

WAV の ID3 チャンクに書き込む（[mutagen](https://mutagen.readthedocs.io/) を使用）。

| フレーム | 内容 | 例 |
|---|---|---|
| `TIT2` | 曲の表示名 | `クロマチック` |
| `TBPM` | BPM | `120` |
| `TDRC` | 録音日 | `2026-10-21` |
| `TXXX:gpl:song_id` | 曲 ID | `chromatic` |
| `TXXX:gpl:recorded_at` | 録音日時（ISO 8601、タイムゾーン付き） | `2026-10-21T22:30:00+09:00` |

## DB（SQLite）

```sql
CREATE TABLE takes (
    id          INTEGER PRIMARY KEY,
    song_id     TEXT    NOT NULL,         -- 曲 ID
    recorded_at TEXT    NOT NULL,         -- 録音日時（ISO 8601）
    bpm         INTEGER NOT NULL,
    file_path   TEXT    NOT NULL UNIQUE,  -- アーカイブ後のパス
    intaken_at  TEXT    NOT NULL          -- 取り込んだ日時（ISO 8601）
);
```

Phase 2-A で、YouTube の動画 ID や Drive のファイル ID などの列を追加する予定。

## 台帳（`songs.toml`）

```toml
[songs.chromatic]
title = "クロマチック"
kind = "chromatic"

[songs.song-a]
title = "曲A"
kind = "song"
```

- 曲 ID: 英小文字・数字で始まり、英小文字・数字・`-`・`_` だけを使う。
- `kind`: `song`（曲練習）または `chromatic`（クロマチック練習）。

## 異常時の挙動

| 状況 | 挙動 |
|---|---|
| 設定ファイルがない、または項目が足りない | エラーを表示して終了する（終了コード 1） |
| 確認で `y` 以外を入力した | ファイルを動かさずに終了する |
| Ctrl+C で中断した | 中断を表示して終了する（終了コード 130）。確定前ならファイルは動かない |
| 実行の途中で失敗した | それまでに処理したテイクはそのまま残る。失敗したテイクは、どの段階で失敗したかによって元の場所かアーカイブに残る。記録の修正コマンドはまだない |
