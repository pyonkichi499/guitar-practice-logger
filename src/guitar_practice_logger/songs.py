"""曲の台帳（TOML）の読み書き。"""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w

SONG_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
KINDS = ("song", "chromatic")


class SongError(Exception):
    pass


@dataclass(frozen=True)
class Song:
    id: str  # フォルダ名・ファイル名に使う英数字の ID
    title: str  # 動画などに載せる表示名
    kind: str = "song"


def load_songs(songs_file: Path) -> list[Song]:
    if not songs_file.exists():
        return []
    with songs_file.open("rb") as f:
        raw = tomllib.load(f)
    return [Song(id=song_id, **attrs) for song_id, attrs in raw.get("songs", {}).items()]


def save_songs(songs_file: Path, songs: list[Song]) -> None:
    data = {"songs": {s.id: {"title": s.title, "kind": s.kind} for s in songs}}
    songs_file.parent.mkdir(parents=True, exist_ok=True)
    songs_file.write_text(tomli_w.dumps(data), encoding="utf-8")


def add_song(songs_file: Path, songs_root: Path, song: Song) -> Path:
    """台帳に曲を追加し、書き出し用のフォルダを作る。作ったフォルダを返す。"""
    if not SONG_ID_PATTERN.match(song.id):
        raise SongError(f"ID は英小文字・数字・-・_ で指定してください: {song.id}")
    if song.kind not in KINDS:
        raise SongError(f"種別は {', '.join(KINDS)} のいずれかです: {song.kind}")

    songs = load_songs(songs_file)
    if any(s.id == song.id for s in songs):
        raise SongError(f"ID が既に登録されています: {song.id}")

    folder = songs_root / song.id
    folder.mkdir(parents=True, exist_ok=True)
    save_songs(songs_file, [*songs, song])
    return folder
