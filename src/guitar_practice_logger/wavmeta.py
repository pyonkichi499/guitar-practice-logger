"""WAV へのメタデータ（ID3 チャンク）の書き込みと読み出し。

DB が失われても、WAV 単体から曲・録音日・BPM を復元できるようにするため。
"""

from datetime import datetime
from pathlib import Path

from mutagen.id3 import TBPM, TDRC, TIT2, TXXX
from mutagen.wave import WAVE

SONG_ID_DESC = "gpl:song_id"
RECORDED_AT_DESC = "gpl:recorded_at"


def write_meta(path: Path, *, song_id: str, title: str, recorded_at: datetime, bpm: int) -> None:
    wav = WAVE(path)
    if wav.tags is None:
        wav.add_tags()
    tags = wav.tags
    tags.add(TIT2(encoding=3, text=[title]))
    tags.add(TBPM(encoding=3, text=[str(bpm)]))
    tags.add(TDRC(encoding=3, text=[recorded_at.strftime("%Y-%m-%d")]))
    tags.add(TXXX(encoding=3, desc=SONG_ID_DESC, text=[song_id]))
    tags.add(
        TXXX(encoding=3, desc=RECORDED_AT_DESC, text=[recorded_at.isoformat(timespec="seconds")])
    )
    wav.save()


def read_meta(path: Path) -> dict[str, str]:
    tags = WAVE(path).tags
    if tags is None:
        return {}
    return {
        "song_id": str(tags[f"TXXX:{SONG_ID_DESC}"]),
        "title": str(tags["TIT2"]),
        "bpm": str(tags["TBPM"]),
        "recorded_at": str(tags[f"TXXX:{RECORDED_AT_DESC}"]),
    }
