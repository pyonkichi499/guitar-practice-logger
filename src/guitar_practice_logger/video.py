"""テイクの WAV から YouTube 用の MP4 を作る（ffmpeg を使う）。

映像は曲名・録音日・BPM を表示した静止画。静止画なので 1 fps にして、変換を速くする。
"""

import logging
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

FONT = "Noto Sans CJK JP"
WIDTH, HEIGHT = 1280, 720
BACKGROUND = "0x1e1e1e"


class VideoError(Exception):
    pass


def video_path(wav: Path) -> Path:
    """WAV に対応する MP4 のパス（同じフォルダ・同じ名前）。"""
    return wav.with_suffix(".mp4")


def card_lines(title: str, recorded_at: datetime, bpm: int) -> list[tuple[str, int]]:
    """静止画に出す行と文字の大きさ。"""
    return [(title, 96), (f"{recorded_at:%Y-%m-%d}", 56), (f"BPM {bpm}", 56)]


def _drawtext_filter(lines: list[tuple[str, int]], workdir: Path) -> str:
    """行ごとに中央揃えの drawtext をつなぐ。

    文字列は textfile で渡し、フィルタ文字列のエスケープを避ける。
    """
    gap = 32
    total = sum(size for _, size in lines) + gap * (len(lines) - 1)
    y = (HEIGHT - total) // 2
    filters = []
    for i, (text, size) in enumerate(lines):
        textfile = workdir / f"line{i}.txt"
        textfile.write_text(text, encoding="utf-8")
        filters.append(
            f"drawtext=font='{FONT}':textfile='{textfile}':fontsize={size}"
            f":fontcolor=white:x=(w-text_w)/2:y={y}"
        )
        y += size + gap
    return ",".join(filters)


def render(wav: Path, *, title: str, recorded_at: datetime, bpm: int) -> Path:
    """WAV と同じ場所に MP4 を作り、そのパスを返す。既にあれば上書きする。"""
    if shutil.which("ffmpeg") is None:
        raise VideoError("ffmpeg が見つかりません")

    out = video_path(wav)
    # 途中で失敗したときに、不完全な MP4 を完成品と取り違えないようにする
    partial = out.with_name(f"{out.stem}.part.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        vf = _drawtext_filter(card_lines(title, recorded_at, bpm), Path(tmp))
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"color=c={BACKGROUND}:s={WIDTH}x{HEIGHT}:r=1",
            "-i", str(wav),
            "-vf", vf,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(partial),
        ]  # fmt: skip
        log.debug("ffmpeg: %s", cmd)
        proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        partial.unlink(missing_ok=True)
        raise VideoError(f"ffmpeg が失敗しました（{wav.name}）: {proc.stderr.strip()}")
    partial.replace(out)
    log.info("動画を作りました: %s", out)
    return out
