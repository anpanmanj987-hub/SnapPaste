"""Start an explicit local/LAN receiver; native Windows is the default backend."""
from __future__ import annotations

import argparse
import sys
from . import __version__
from .clipboard import ClipboardError, DryRunClipboard, WindowsClipboard
from .server import ServerConfig, make_server


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SnapPaste: スマホの写真をWindowsの画像クリップボードへ送信します。")
    parser.add_argument("--version", action="version", version=f"SnapPaste {__version__}")
    parser.add_argument("--host", default="127.0.0.1", help="待受IPv4 (既定:127.0.0.1)。LAN公開は明示してください")
    parser.add_argument("--advertise", help="QRに表示するPCのIPv4。0.0.0.0待受時は必須")
    parser.add_argument("--port", type=int, default=8766, help="待受port (既定:8766)")
    parser.add_argument("--max-edge", type=int, default=1920, help="処理後の長辺上限px (1..8192、既定:1920)")
    parser.add_argument("--max-mib", type=int, default=25, help="受信容量上限MiB (1..25、既定:25)")
    parser.add_argument("--max-pixels", type=int, default=50_000_000, help="入力画素数上限 (最大50,000,000)")
    parser.add_argument("--timeout", type=float, default=10, help="ソケットの読取タイムアウト秒 (既定:10)")
    parser.add_argument("--dry-run", action="store_true", help="画像処理だけ確認。クリップボード更新・画像保存を行いません")
    parser.add_argument("--no-qr", action="store_true", help="ターミナルQRを省略し参加URLだけ表示")
    args = parser.parse_args(argv)
    try:
        config = ServerConfig(host=args.host, port=args.port, advertised_host=args.advertise,
                              max_edge=args.max_edge, max_bytes=args.max_mib * 1024 * 1024,
                              max_pixels=args.max_pixels, socket_timeout=args.timeout)
    except ValueError as error:
        parser.error(str(error))
    if sys.platform != "win32" and not args.dry_run:
        parser.error("Windows以外では --dry-run を明示してください。クリップボードは更新しません。")
    clipboard = None
    server = None
    try:
        clipboard = DryRunClipboard() if args.dry_run else WindowsClipboard()
        server = make_server(config, clipboard)
        print(f"SnapPaste {__version__} / {clipboard.mode}", flush=True)
        if args.dry_run:
            print("dry-run: クリップボードは更新せず、画像も保存しません。", flush=True)
        print(f"参加URL (この起動中だけ有効・共有しないでください):\n{server.join_url}", flush=True)
        if not args.no_qr:
            import qrcode
            qr = qrcode.QRCode(border=2)
            qr.add_data(server.join_url)
            qr.make(fit=True)
            try:
                qr.print_ascii(out=sys.stdout, invert=True)
            except UnicodeError:
                print("QRを表示できません。参加URLをスマートフォンで開いてください。", flush=True)
        print("Ctrl+Cで終了。LAN通信は平文HTTPです。信頼できるネットワークで利用してください。", flush=True)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\nSnapPasteを終了します。", flush=True)
    except (OSError, ClipboardError) as error:
        print(f"起動できませんでした: {error}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.server_close()
        elif clipboard is not None:
            clipboard.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
