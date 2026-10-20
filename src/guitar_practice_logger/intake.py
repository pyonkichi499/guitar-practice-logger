"""曲フォルダに書き出された WAV の取り込み。

1 回の取り込みで、各曲から WAV を 1 本だけ受け付ける。
録音日はファイルの更新日時から取る。
"""

import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .songs import Song
from .takes import Take, TakeStore
from .wavmeta import write_meta

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Candidate:
    song: Song
    source: Path
    recorded_at: datetime


@dataclass(frozen=True)
class Scan:
    candidates: list[Candidate]
    warnings: list[str]


def scan(songs_root: Path, songs: list[Song]) -> Scan:
    """取り込み対象を集める。曲フォルダに WAV が 2 本以上ある曲は対象外にする。"""
    candidates: list[Candidate] = []
    warnings: list[str] = []
    known_ids = {s.id for s in songs}

    for song in songs:
        folder = songs_root / song.id
        wavs = sorted(p for p in folder.glob("*") if p.suffix.lower() == ".wav")
        if not wavs:
            continue
        if len(wavs) > 1:
            names = ", ".join(p.name for p in wavs)
            warnings.append(f"{song.title}: WAV が {len(wavs)} 本あるため飛ばしました（{names}）")
            continue
        recorded_at = datetime.fromtimestamp(wavs[0].stat().st_mtime).astimezone()
        candidates.append(Candidate(song, wavs[0], recorded_at))

    if songs_root.exists():
        for folder in sorted(p for p in songs_root.iterdir() if p.is_dir()):
            if folder.name not in known_ids:
                warnings.append(f"台帳にないフォルダがあります: {folder.name}")

    return Scan(candidates, warnings)


def destination(archive_dir: Path, song_id: str, recorded_at: datetime, bpm: int) -> Path:
    """移動先のパス。同名があれば連番を付ける（同じ日に 2 回取り込んだ場合など）。"""
    folder = archive_dir / song_id
    stem = f"{recorded_at:%Y%m%d}_{song_id}_{bpm}"
    path = folder / f"{stem}.wav"
    n = 2
    while path.exists():
        path = folder / f"{stem}_{n}.wav"
        n += 1
    return path


def intake_one(candidate: Candidate, bpm: int, archive_dir: Path, store: TakeStore) -> Path:
    """メタデータを書き込み、移動し、記録する。移動先を返す。"""
    song = candidate.song
    write_meta(
        candidate.source,
        song_id=song.id,
        title=song.title,
        recorded_at=candidate.recorded_at,
        bpm=bpm,
    )
    dest = destination(archive_dir, song.id, candidate.recorded_at, bpm)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(candidate.source, dest)
    store.add(Take(song.id, candidate.recorded_at, bpm, dest))
    log.info("取り込みました: %s -> %s", candidate.source, dest)
    return dest


def ask_bpm(song: Song, default: int | None, ask: Callable[[str], str]) -> int:
    hint = f" [前回 {default}]" if default is not None else ""
    while True:
        answer = ask(f"{song.title} の BPM{hint}: ").strip()
        if not answer and default is not None:
            return default
        if answer.isdigit() and int(answer) > 0:
            return int(answer)
        print("BPM は正の整数で入力してください。")


def run(
    songs_root: Path,
    archive_dir: Path,
    songs: list[Song],
    store: TakeStore,
    ask: Callable[[str], str] = input,
) -> list[Path]:
    """対話的に取り込む。取り込んだファイルのパスを返す。"""
    result = scan(songs_root, songs)
    for w in result.warnings:
        print(f"警告: {w}")
    if not result.candidates:
        print("取り込む WAV はありません。")
        return []

    bpms = [ask_bpm(c.song, store.last_bpm(c.song.id), ask) for c in result.candidates]

    print("\n以下の内容で取り込みます:")
    for c, bpm in zip(result.candidates, bpms, strict=True):
        print(f"  {c.recorded_at:%Y-%m-%d %H:%M}  {c.song.title}  BPM {bpm}  ({c.source.name})")
    if ask("よろしいですか？ [y/N]: ").strip().lower() != "y":
        print("中止しました。ファイルは動かしていません。")
        return []

    return [
        intake_one(c, bpm, archive_dir, store)
        for c, bpm in zip(result.candidates, bpms, strict=True)
    ]
