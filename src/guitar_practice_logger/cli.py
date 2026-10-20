"""コマンドラインの入口。"""

import argparse
import logging
import sys

from . import intake
from .config import ConfigError, load_config
from .songs import KINDS, Song, SongError, add_song, load_songs
from .takes import TakeStore


def cmd_add_song(args: argparse.Namespace) -> None:
    config = load_config()
    folder = add_song(config.songs_file, config.songs_root, Song(args.id, args.title, args.kind))
    print(f"登録しました: {args.title}（書き出し先: {folder}）")


def cmd_songs(_: argparse.Namespace) -> None:
    config = load_config()
    for s in load_songs(config.songs_file):
        print(f"{s.id}\t{s.kind}\t{s.title}")


def cmd_intake(_: argparse.Namespace) -> None:
    config = load_config()
    store = TakeStore(config.db_path)
    try:
        done = intake.run(
            config.songs_root, config.archive_dir, load_songs(config.songs_file), store
        )
    finally:
        store.close()
    if done:
        print(f"{len(done)} 本取り込みました。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gpl", description="ギター練習の録音の取り込み")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細なログを出す")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("add-song", help="曲を登録し、書き出し用フォルダを作る")
    p.add_argument("id", help="英数字の ID（フォルダ名・ファイル名に使う）")
    p.add_argument("title", help="表示名")
    p.add_argument("--kind", choices=KINDS, default="song")
    p.set_defaults(func=cmd_add_song)

    p = sub.add_parser("songs", help="登録済みの曲を一覧表示する")
    p.set_defaults(func=cmd_songs)

    p = sub.add_parser("intake", help="曲フォルダの WAV を取り込む")
    p.set_defaults(func=cmd_intake)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        args.func(args)
    except (ConfigError, SongError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n中断しました。", file=sys.stderr)
        sys.exit(130)
