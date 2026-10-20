import os
import wave
from datetime import datetime
from pathlib import Path

import pytest

from guitar_practice_logger import intake
from guitar_practice_logger.songs import Song, SongError, add_song, load_songs
from guitar_practice_logger.takes import TakeStore
from guitar_practice_logger.wavmeta import read_meta

CHROMATIC = Song("chromatic", "クロマチック", "chromatic")
SONG_A = Song("song-a", "曲A")


def make_wav(path: Path, mtime: datetime | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * 2 * 441)
    if mtime:
        os.utime(path, (mtime.timestamp(), mtime.timestamp()))
    return path


@pytest.fixture
def env(tmp_path):
    store = TakeStore(tmp_path / "takes.db")
    yield tmp_path / "songs", tmp_path / "archive", store
    store.close()


def answers(*values):
    it = iter(values)
    return lambda _prompt: next(it)


def test_intake_moves_renames_and_records(env):
    songs_root, archive, store = env
    recorded = datetime(2026, 10, 21, 22, 30)
    make_wav(songs_root / "chromatic" / "Export.wav", recorded)

    done = intake.run(songs_root, archive, [CHROMATIC, SONG_A], store, answers("120", "y"))

    dest = archive / "chromatic" / "20261021_chromatic_120.wav"
    assert done == [dest]
    assert dest.exists()
    assert not (songs_root / "chromatic" / "Export.wav").exists()
    assert store.last_bpm("chromatic") == 120
    meta = read_meta(dest)
    assert meta["song_id"] == "chromatic"
    assert meta["title"] == "クロマチック"
    assert meta["bpm"] == "120"
    assert meta["recorded_at"].startswith("2026-10-21T22:30")


def test_previous_bpm_is_default(env):
    songs_root, archive, store = env
    make_wav(songs_root / "song-a" / "Export.wav", datetime(2026, 10, 21))
    intake.run(songs_root, archive, [SONG_A], store, answers("100", "y"))

    make_wav(songs_root / "song-a" / "Export.wav", datetime(2026, 10, 22))
    intake.run(songs_root, archive, [SONG_A], store, answers("", "y"))

    assert (archive / "song-a" / "20261022_song-a_100.wav").exists()


def test_cancel_leaves_files_untouched(env):
    songs_root, archive, store = env
    src = make_wav(songs_root / "song-a" / "Export.wav")

    assert intake.run(songs_root, archive, [SONG_A], store, answers("100", "n")) == []
    assert src.exists()
    assert store.last_bpm("song-a") is None


def test_invalid_bpm_is_asked_again(env):
    songs_root, archive, store = env
    make_wav(songs_root / "song-a" / "Export.wav", datetime(2026, 10, 21))

    intake.run(songs_root, archive, [SONG_A], store, answers("", "abc", "0", "90", "y"))

    assert (archive / "song-a" / "20261021_song-a_90.wav").exists()


def test_scan_skips_folder_with_multiple_wavs(env):
    songs_root, _, _ = env
    make_wav(songs_root / "song-a" / "1.wav")
    make_wav(songs_root / "song-a" / "2.wav")
    (songs_root / "unknown").mkdir()

    result = intake.scan(songs_root, [SONG_A])

    assert result.candidates == []
    assert any("2 本" in w for w in result.warnings)
    assert any("unknown" in w for w in result.warnings)


def test_same_day_reintake_gets_suffix(env):
    songs_root, archive, store = env
    for _ in range(2):
        make_wav(songs_root / "song-a" / "Export.wav", datetime(2026, 10, 21))
        intake.run(songs_root, archive, [SONG_A], store, answers("100", "y"))

    assert (archive / "song-a" / "20261021_song-a_100.wav").exists()
    assert (archive / "song-a" / "20261021_song-a_100_2.wav").exists()


def test_add_song(tmp_path):
    songs_file = tmp_path / "songs.toml"
    folder = add_song(songs_file, tmp_path / "songs", SONG_A)

    assert folder.is_dir()
    assert load_songs(songs_file) == [SONG_A]
    with pytest.raises(SongError):
        add_song(songs_file, tmp_path / "songs", SONG_A)
    with pytest.raises(SongError):
        add_song(songs_file, tmp_path / "songs", Song("曲B", "曲B"))
