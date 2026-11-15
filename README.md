# guitar-practice-logger

エレキギターの毎日の練習を録音して記録し、YouTube と Google ドライブに残すまでの手作業を減らすためのツール。

最終的には次の流れを自動化することを目指している。

```text
録音（DAW） → 取り込み（曲・BPM・録音日を付けて整理） → 動画化 → YouTube に公開 / WAV を GDrive に保存
```

## 現状

**Phase 1（録音して取り込むまで）と、Phase 2-A のうち動画化が使える状態。** YouTube への公開と GDrive への保存はまだない。

| できること | まだできないこと |
|---|---|
| 曲の登録と一覧表示 | YouTube への公開、GDrive への保存 |
| 書き出した WAV の取り込み（BPM の入力、名前の付け替え、メタデータの書き込み、記録） | 取り込んだ記録の修正 |
| 取り込み時の動画化（曲名・録音日・BPM を表示した MP4） | DB が消えたときに WAV から記録を作り直すこと（必要な情報は WAV に書き込み済み） |

今後の計画は [docs/roadmap.md](docs/roadmap.md) を参照。

## 用語

| 用語 | 意味 |
|---|---|
| 曲 | 練習メニューの単位。曲練習の曲のほか、クロマチック練習も「曲」として 1 つ登録する |
| 曲 ID | 曲を表す英小文字・数字の名前（例: `chromatic`、`song-a`）。フォルダ名とファイル名に使う |
| 台帳 | 登録した曲の一覧（`songs.toml`）。Git で管理する |
| 曲フォルダ | DAW から WAV を書き出す、曲ごとのフォルダ |
| テイク | 取り込んだ 1 本の録音。1 日に 1 曲あたり 1 本を想定 |
| 取り込み | `gpl intake`。曲フォルダの WAV に BPM などを付けてアーカイブへ移し、記録する |

## 前提

- Windows 11 ＋ WSL2（このツールは WSL2 上で動かし、Windows 側のフォルダを `/mnt/c` 経由で読む）
- WSL2 側に [uv](https://docs.astral.sh/uv/)、ffmpeg、日本語フォント（Noto Sans CJK JP。`sudo apt install fonts-noto-cjk`）
- 録音機材: ZOOM G2 FOUR（USB オーディオインターフェースとして使う）
- DAW: Cakewalk Next

## セットアップ

### 1. ツール

```zsh
uv sync
cp config.example.toml config.toml   # パスを環境に合わせて編集する（config.toml は Git 管理外）
```

`config.toml` の項目は次のとおり。相対パスは `config.toml` のある場所（リポジトリ直下）が基準になる。

| 項目 | 内容 | 例 |
|---|---|---|
| `songs_root` | 曲フォルダの親（Windows 側） | `/mnt/c/Users/<ユーザー>/Music/GuitarPractice/songs` |
| `archive_dir` | 取り込んだ WAV の移動先（Windows 側） | `/mnt/c/Users/<ユーザー>/Music/GuitarPractice/archive` |
| `songs_file` | 台帳 | `songs.toml` |
| `db_path` | テイクの記録（SQLite、WSL2 側） | `~/.local/share/guitar-practice-logger/takes.db` |

### 2. 曲の登録

```zsh
uv run gpl add-song chromatic クロマチック --kind chromatic
uv run gpl add-song song-a 曲A
uv run gpl songs   # 一覧表示
```

`add-song` は台帳に曲を追記し、曲フォルダ `<songs_root>/<曲 ID>` を作る。

### 3. DAW 側の準備（曲ごとに 1 回）

曲ごとに Cakewalk のプロジェクトを作り、次のように設定しておく。

- 書き出し先をその曲の曲フォルダにする（ファイル名は既定のままでよい）
- 曲のテンポを設定し、**クリック（メトロノーム）を書き出しに含める**
- 曲練習では、バッキング音源をプロジェクトの先頭に置き、書き出しも先頭から行う（将来ギターと混ぜられるように頭を揃えておくため）
- **書き出すのはギターとクリックだけにする**（バッキングはミュートする）。公開動画に市販曲の音源が入ると YouTube の著作権の自動検出に引っかかるため

> Cakewalk Next で書き出し先をプロジェクトごとに固定できるかは未確認。できない場合は、書き出すたびに曲フォルダを選ぶ。

## 毎日の使い方

1. 練習の最後に、メニューごとに 1 本ずつ録音し、それぞれの曲フォルダに書き出す。録り直したら上書きしてよい（最後のテイクが採用される）。
2. 取り込む。

   ```zsh
   uv run gpl intake
   ```

3. WAV がある曲ごとに BPM を聞かれるので入力する（Enter だけなら前回の値）。
4. 一覧を確認して `y` を押すと、WAV が `<archive_dir>/<曲 ID>/<録音日>_<曲 ID>_<BPM>.wav` に移り、同じ場所に同じ名前の MP4（YouTube 用の動画）ができる。`y` 以外ならファイルは動かない。
5. MP4 を YouTube Studio から手動でアップロードする（自動化は Phase 2-A の残り）。

注意:

- 録音日はファイルの更新日時から取る。
- 取り込みを忘れたまま翌日に同じ曲を書き出すと、前日分は上書きされて失われる。
- 1 つの曲フォルダに WAV が 2 本以上あると、その曲は飛ばされる（警告が出る）。
- WAV は曲フォルダ（`<songs_root>/<曲 ID>/`）の中に書き出す。`songs_root` の直下に置いた WAV は取り込まれない。
- 動画を作れなかった場合（ffmpeg がないなど）も、取り込み自体は完了する。`uv run gpl render` で MP4 がないテイクの動画を作り直せる（`--force` で全テイクを作り直す）。

詳しい挙動は [docs/specs/intake.md](docs/specs/intake.md) を参照。

## データの置き場所

| データ | 場所 | バックアップ |
|---|---|---|
| 取り込んだ WAV | `archive_dir`（Windows 側） | Phase 2-A で GDrive に保存する予定 |
| 台帳 | `songs.toml`（リポジトリ内） | Git |
| テイクの記録 | `db_path`（WSL2 側の SQLite） | なし。ただし WAV のファイル名とメタデータから作り直せる |
| 設定 | `config.toml`（リポジトリ内、Git 管理外） | なし |

## ドキュメント

| ファイル | 内容 |
|---|---|
| [docs/roadmap.md](docs/roadmap.md) | フェーズごとの計画と進み具合 |
| [docs/design-decisions.md](docs/design-decisions.md) | 設計判断とその理由、保留事項 |
| [docs/specs/intake.md](docs/specs/intake.md) | 取り込みの仕様（フォルダ構成、命名規則、メタデータ、DB） |
| [docs/research.md](docs/research.md) | 機材・API の調査結果 |

## 開発

```zsh
uv run pytest
uv run ruff check . && uv run ruff format .
```

ソースは `src/guitar_practice_logger/` にある。

| モジュール | 役割 |
|---|---|
| `cli.py` | コマンドの入口 |
| `config.py` | 設定ファイルの読み込み |
| `songs.py` | 台帳の読み書き |
| `intake.py` | 取り込み |
| `takes.py` | テイクの記録（SQLite） |
| `wavmeta.py` | WAV のメタデータ |
| `video.py` | 動画（MP4）の作成 |
