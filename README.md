# SnapPaste

スマホで撮影・選択した写真を、Windows PCの画像クリップボードへ送る小さなローカルツールです。ブラウザでプレビューを確かめてから送信し、PCのアプリで `Ctrl+V` で貼り付けます。スマホ用アプリや外部画像処理サービスは不要です。

**0.1.0a2 / MIT / アルファ版。** [English](README.en.md)

0.1.0a2は公開前レビュー後の修正版です。Linuxでの今回の検証と、0.1.0a1のmacOS検証記録を分けて [検証記録](docs/VALIDATION.md) に記載しています。

## インストール

Python 3.10以上が必要です。このディレクトリを取得して、Windows PowerShellで実行します。

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python -m snappaste --help
```

既定では `127.0.0.1:8766` だけに待ち受けます。スマホから使うときは、PCとスマホを同じネットワークにつなぎ、**PCのLAN IPv4アドレス**を指定してください。Windowsの `ipconfig` で確認できます。

```powershell
.venv\Scripts\python -m snappaste --host 192.168.1.20
```

上のアドレスは例です。自分のPCのアドレスへ置き換えてください。全インターフェイスで待ち受ける場合は、QRに表示するアドレスも明示します。

```powershell
.venv\Scripts\python -m snappaste --host 0.0.0.0 --advertise 192.168.1.20
```

起動時のQRまたは参加URLをスマホで開きます。カメラで撮るかライブラリから選び、プレビュー後に「PCへ送信する」を押してください。**コピー完了の表示が出た後**にPCで貼り付けます。`Ctrl+C` で受信ホストを終了します。QRと参加URLはこの起動中の操作権限を含むため、他人へ共有しないでください。再起動するとコードが変わります。

## 動作確認モード

macOS/Linuxでは `--dry-run` の明示が必要です。Windowsでも指定できます。転送・向き補正・縮小・DIB生成まで実行しますが、**クリップボード更新も画像の保存も行いません**。画面と完了メッセージにもdry-runを表示します。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m snappaste --dry-run
```

## 画像と上限

- JPEG、PNG、静止WebP。HEICはJPEGへ変換してください。アニメーションと対応外形式は拒否します。
- 受信上限25MiB、入力上限50,000,000画素。長辺1920px以内、縦横比を維持し、小さい画像は拡大しません。
- EXIFの向きを反映し、透過は白背景に合成します。Windowsには24bit RGBの `CF_DIB` としてコピーします。
- 画素から画像を作り直し、元のEXIF/GPS/XMP/ICC/コメントなどを出力へ引き継ぎません。元画像のICC色変換は行わないため、広色域の写真では色が変わることがあります。
- 原本はホストへ送信されます。元画像に含まれるメタデータは**ホストで処理した後**に除去します。既定ではディスクに保存しません。

`--max-edge`、`--max-mib`、`--max-pixels`で上限を変更できます。受信容量・入力画素数は上記の安全上限を超えられません。`--no-qr` でURL表示だけにできます。

## ネットワークについて

LAN通信は平文HTTPです。写真や操作トークンの暗号化を保証しません。信頼できる家庭内などのネットワークで使用し、ポートをインターネットへ公開しないでください。外部CDN、解析、クラウド、画像処理サービスには接続しません。

ホストは起動ごとのトークンと厳密なHost/Originを確認します。画像処理は同時に1件、接続は最大8件です。読取タイムアウトは既定10秒です。ブラウザのカメラ導線は `input type=file` を使い、`getUserMedia`を必要としません。撮影・選択画面の表示はスマホのブラウザによって異なります。

接続できない場合はPCのIPv4、同じWi-Fi、ホストの起動、Windowsファイアウォールのプライベートネットワーク設定を確認してください。ゲストWi-Fiの端末間隔離やVPNで接続できない場合があります。

## 検証と開発

```sh
python -m pip install .
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

自動テストは画像処理、DIB行配置、実HTTPの認証・制限、CLI、Win32メモリ所有権の失敗分岐を対象とします。Win32の境界だけをfakeにしたテストはWindows実機の証明ではありません。**Windows実機の貼り付けと実スマホの撮影は未検証です。** 各検証の実施結果は [検証記録](docs/VALIDATION.md) と [実装報告](docs/IMPLEMENTATION-REPORT.md) を確認してください。

[設計](docs/DESIGN.md) · [公開手順](docs/PUBLISHING.md) · [引継ぎ](docs/HANDOFF.md)
