"""Start an explicit local/LAN receiver; native Windows is the default backend."""
from __future__ import annotations

import argparse
import sys
from . import __version__
from .clipboard import ClipboardError, DryRunClipboard, WindowsClipboard
from .messages import cli_language, text
from .server import ServerConfig, make_server


def main(argv=None) -> int:
    # Redirected Windows output can use an encoding that cannot represent Japanese.
    # Keep that encoding so consumers can still decode it, but escape unsupported text.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    lang = cli_language()
    say = lambda key: text(key, lang)
    parser = argparse.ArgumentParser(description=say("cli_description"))
    parser.add_argument("--version", action="version", version=f"SnapPaste {__version__}")
    parser.add_argument("--host", default="127.0.0.1", help=say("help_host"))
    parser.add_argument("--advertise", help=say("help_advertise"))
    parser.add_argument("--port", type=int, default=8766, help=say("help_port"))
    parser.add_argument("--max-edge", type=int, default=1920, help=say("help_max_edge"))
    parser.add_argument("--max-mib", type=int, default=25, help=say("help_max_mib"))
    parser.add_argument("--max-pixels", type=int, default=50_000_000, help=say("help_max_pixels"))
    parser.add_argument("--timeout", type=float, default=10, help=say("help_timeout"))
    parser.add_argument("--dry-run", action="store_true", help=say("help_dry_run"))
    parser.add_argument("--no-qr", action="store_true", help=say("help_no_qr"))
    args = parser.parse_args(argv)
    try:
        config = ServerConfig(host=args.host, port=args.port, advertised_host=args.advertise,
                              max_edge=args.max_edge, max_bytes=args.max_mib * 1024 * 1024,
                              max_pixels=args.max_pixels, socket_timeout=args.timeout)
    except ValueError as error:
        parser.error(str(error))
    if sys.platform != "win32" and not args.dry_run:
        parser.error(say("cli_dry_run_required"))
    clipboard = None
    server = None
    try:
        clipboard = DryRunClipboard() if args.dry_run else WindowsClipboard()
        server = make_server(config, clipboard)
        print(f"SnapPaste {__version__} / {clipboard.mode}", flush=True)
        if args.dry_run:
            print(say("cli_dry_run_notice"), flush=True)
        print(f"{say('cli_join_url')}\n{server.join_url}", flush=True)
        if not args.no_qr:
            import qrcode
            qr = qrcode.QRCode(border=2)
            qr.add_data(server.join_url)
            qr.make(fit=True)
            try:
                qr.print_ascii(out=sys.stdout, invert=True)
            except UnicodeError:
                print(say("cli_no_qr"), flush=True)
        print(say("cli_running"), flush=True)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n" + say("cli_stopped"), flush=True)
    except (OSError, ClipboardError) as error:
        print(text("cli_start_failed", lang, str(error)), file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.server_close()
        elif clipboard is not None:
            clipboard.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
