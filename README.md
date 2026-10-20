# guitar-practice-logger

ギター練習の録音を取り込み、記録するツール。設計の経緯は [docs/design-decisions.md](docs/design-decisions.md) を参照。

## セットアップ

```zsh
uv sync
mkdir -p ~/.config/guitar-practice-logger
cp config.example.toml ~/.config/guitar-practice-logger/config.toml  # パスを環境に合わせて編集
```

## 使い方

```zsh
# 曲を登録する（台帳に追記し、書き出し用フォルダ <songs_root>/<ID> を作る）
uv run gpl add-song chromatic クロマチック --kind chromatic
uv run gpl add-song song-a 曲A

# 登録済みの曲を一覧表示する
uv run gpl songs

# 練習の最後に、DAW から各曲のフォルダへ 1 本ずつ書き出してから取り込む
uv run gpl intake
```

`intake` は WAV がある曲ごとに BPM を聞き（Enter で前回値）、確認後に次の処理を行う。

- WAV にメタデータ（曲・録音日・BPM）を書き込む
- `<archive_dir>/<ID>/<録音日>_<ID>_<BPM>.wav` へ移動する
- SQLite に記録する

録音日はファイルの更新日時から取る。1 つの曲フォルダに WAV が 2 本以上ある曲は取り込まずに飛ばす。

## 開発

```zsh
uv run pytest
uv run ruff check . && uv run ruff format .
```
