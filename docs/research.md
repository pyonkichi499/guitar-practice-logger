# 調査結果

設計の前提にした機材・API の調査結果（2026-10-20 に調査）。「確認」は公式文書などの一次情報で確かめたもの、「推測」は裏付けがなく実機での確認が必要なもの。

## ZOOM G2 FOUR（USB オーディオ）

- **確認**: USB は 2 in / 2 out。44.1 kHz 固定（AD/DA は 24 bit）。
- **確認**: PC へ送られるのはエフェクト後の 2ch のみ。PC からの再生音は本体のモニター（ヘッドホン）に混ざるだけで、録音側には戻らない。マニュアルにループバックやドライ出力の設定はない。
- **確認**: Windows では専用ドライバ（G2 FOUR Series Driver）が必要。
- **推測**: ASIO 対応は公式文書で確認できなかった。ドライ音とウェット音の同時録音はできない可能性が高い。

**設計への影響**: 公開版（ギターのみ）は普通に録音するだけで作れる。クリックやバッキングを入れるには PC 側で混ぜる必要がある（[D2](design-decisions.md#d2-公開版の音はギターとクリックだけにする2026-10-20)）。

出典:

- https://zoomcorp.com/manuals/g2four_g2xfour-en/
- https://zoomcorp.com/en/gb/multi-effects/guitar-effects/g2-four-g2x-four/g2four-support/

## WSL2 での録音

- **確認（ユーザー報告ベース）**: WSLg は Windows 側の既定の入力を PulseAudio のソース（RDPSource）として公開し、録音はできる。ただし RDP 経由で、スリープ後に約 1 秒の遅延が出る不具合の報告がある。
- **確認**: usbipd で USB オーディオを直接つなぐには WSL のカーネルを自前でビルドする必要があり、実用的な録音の検証例は見つからなかった。

**設計への影響**: 録音は Windows 側で行う。WSL2 では録音済みのファイルを処理するだけにする。

出典:

- https://github.com/microsoft/wslg/issues/1026
- https://github.com/microsoft/WSL/issues/7686
- https://emkapro.de/en/2024/11/activate-usb-audio-under-wsl2/

## YouTube Data API v3

- **確認**: `videos.insert` のリファレンスに「未監査の API プロジェクトからアップロードした動画も非公開に制限されない」とある。2020 年以降の「未監査なら強制的に非公開」という制限は、文書上は撤廃されている。
- **確認**: 2026-06-01 からクォータが細分化され、`videos.insert` は専用の枠で既定 1 日 100 回。それ以外のメソッドは 1 日 10,000 units を共有する。「アップロード 1 回 1600 units（1 日 6 本程度）」という情報は古い。
- **確認**: OAuth 同意画面が「外部＋テスト」の状態だと、リフレッシュトークンは 7 日で失効する。
- **推測**: 本番モードにすれば 7 日の失効は避けられる。`youtube.upload` はセンシティブなスコープなので、未審査だと初回に警告画面が出るが、本人 1 人で使う分には問題ない見込み。

**要確認**: 公開設定でのアップロードが実際に通るか（Phase 2-A の最初に 1 本試す）。

出典:

- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.google.com/youtube/v3/determine_quota_cost
- https://developers.google.com/youtube/v3/revision_history
- https://developers.google.com/identity/protocols/oauth2

## Google Drive API

- **確認**: サービスアカウントにはストレージ容量がなく、ファイルを所有できない。個人の My Drive のフォルダを共有してアップロードしても `storageQuotaExceeded` になる。
- **推測**: 共有ドライブとドメイン全体の委任は Google Workspace の機能で、個人の Gmail アカウントでは使えない。

**設計への影響**: 個人のアカウントで OAuth（インストール型アプリ）を使う。YouTube と同じ OAuth クライアントでまとめて扱える。

出典:

- https://developers.google.com/workspace/drive/api/guides/about-shareddrives
