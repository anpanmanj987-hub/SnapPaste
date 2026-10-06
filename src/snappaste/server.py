"""Small local HTTP host, with bounded clients and an authenticated upload path."""
from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import ipaddress
import json
import math
import secrets
import socket
import threading
import time

from . import __version__
from .images import MAX_BYTES, MAX_PIXELS, MAX_EDGE, normalize_image, dib_bytes, ImageValidationError
from .clipboard import ClipboardError


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8766
    advertised_host: str | None = None
    max_bytes: int = MAX_BYTES
    max_pixels: int = MAX_PIXELS
    max_edge: int = MAX_EDGE
    socket_timeout: float = 10.0
    max_clients: int = 8

    def __post_init__(self):
        ipaddress.IPv4Address(self.host)
        if self.advertised_host:
            address = ipaddress.IPv4Address(self.advertised_host)
            if address.is_unspecified or address.is_multicast:
                raise ValueError("advertised address must be a usable IPv4 address")
        if self.host == "0.0.0.0" and not self.advertised_host:
            raise ValueError("--host 0.0.0.0 requires --advertise with the PC's LAN IPv4 address")
        if not 0 <= self.port <= 65535:
            raise ValueError("port must be 0..65535")
        if not math.isfinite(self.socket_timeout) or min(self.max_bytes, self.max_pixels, self.max_edge, self.socket_timeout, self.max_clients) <= 0:
            raise ValueError("limits must be positive")
        if self.max_edge > 8192 or self.max_bytes > MAX_BYTES or self.max_pixels > MAX_PIXELS:
            raise ValueError("limits cannot exceed 25 MiB, 50 MP, or 8192 pixels")


ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/api.mjs": ("api.mjs", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}


def read_upload(stream, connection, length: int, timeout: float) -> bytes:
    """A trickling peer cannot renew the total body deadline indefinitely."""
    deadline = time.monotonic() + timeout
    remaining = length
    chunks = []
    while remaining:
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("upload deadline exceeded")
        connection.settimeout(left)
        chunk = stream.read1(min(65536, remaining))
        if not chunk:
            raise EOFError("incomplete upload")
        if time.monotonic() >= deadline:
            raise TimeoutError("upload deadline exceeded")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


DRAIN_BYTES = MAX_BYTES + 64 * 1024
DRAIN_SECONDS = 2.0


def discard_body(stream, connection, length: int, timeout: float = DRAIN_SECONDS) -> None:
    """Read and drop an unread request body within a short, bounded time."""
    deadline = time.monotonic() + timeout
    remaining = min(length, DRAIN_BYTES)
    try:
        while remaining > 0:
            left = deadline - time.monotonic()
            if left <= 0:
                return
            connection.settimeout(left)
            chunk = stream.read1(min(65536, remaining))
            if not chunk:
                return
            remaining -= len(chunk)
    except OSError:
        return


class SnapPasteServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, config, clipboard, token):
        self.config, self.clipboard, self.token = config, clipboard, token
        self.processing = threading.Lock()
        self._clients = threading.BoundedSemaphore(config.max_clients)
        super().__init__((config.host, config.port), RequestHandler)
        advertised = config.advertised_host or config.host
        self.authority = f"{advertised}:{self.server_address[1]}"
        self.origin = f"http://{self.authority}"
        self.join_url = f"{self.origin}/#token={token}"

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(self.config.socket_timeout)
        return connection, address

    def process_request(self, request, client_address):
        if not self._clients.acquire(blocking=False):
            try:
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._clients.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._clients.release()

    def server_close(self):
        super().server_close()
        self.clipboard.close()


class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # Every request closes: unread rejected bodies cannot become requests.
    server_version = "SnapPaste"
    sys_version = ""

    def log_message(self, format, *args):
        # No request logging: path, capability and photo bytes remain private.
        pass

    def parse_request(self):
        ok = super().parse_request()
        lengths = self.headers.get_all("Content-Length", []) if ok else []
        raw = lengths[0] if len(lengths) == 1 else ""
        self.unread = int(raw) if raw.isascii() and raw.isdigit() and len(raw) <= 10 else 0
        return ok

    def finish(self):
        # Rejections reply before reading the photo. Closing a socket with unread
        # data makes Windows reset the connection, and the phone then sees a network
        # error instead of the reply (for example "scan the new QR code").
        try:
            if getattr(self, "unread", 0) and not self.wfile.closed:
                self.wfile.flush()
                discard_body(self.rfile, self.connection, self.unread)
        except OSError:
            pass
        finally:
            super().finish()

    def _reply(self, status, content, mime="application/json; charset=utf-8"):
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' blob:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError, socket.timeout):
                pass

    def _error(self, status, message):
        self._reply(status, {"ok": False, "message": message})

    def _host_ok(self):
        hosts = self.headers.get_all("Host", [])
        if hosts != [self.server.authority]:
            self._error(403, "接続先が一致しません。PCのQRコードから接続してください。")
            return False
        return True

    def _authorized(self, mutate=False):
        if not self._host_ok():
            return False
        supplied = self.headers.get_all("X-SnapPaste-Token", [])
        if len(supplied) != 1 or not supplied[0].isascii() or not secrets.compare_digest(supplied[0], self.server.token):
            self._error(401, "接続コードが無効です。PCの新しいQRコードから接続してください。")
            return False
        if mutate and self.headers.get_all("Origin", []) != [self.server.origin]:
            self._error(403, "この送信元からは操作できません。PCのQRコードから接続してください。")
            return False
        return True

    def do_GET(self):
        if self.path == "/api/status":
            if not self._authorized():
                return
            self._reply(200, {"ok": True, "version": __version__, "mode": self.server.clipboard.mode,
                             "max_bytes": self.server.config.max_bytes,
                             "max_edge": self.server.config.max_edge})
            return
        if not self._host_ok():
            return
        asset = ASSETS.get(self.path)
        if not asset:
            self._error(404, "ページが見つかりません。")
            return
        name, mime = asset
        self._reply(200, files("snappaste").joinpath("static", name).read_bytes(), mime)

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self._error(403, "外部ページからの操作は許可していません。")

    def do_POST(self):
        if not self._authorized(mutate=True):
            return
        if self.path != "/api/upload":
            self._error(404, "送信先が見つかりません。")
            return
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get_all("Transfer-Encoding") or len(lengths) != 1:
            self._error(411, "画像サイズを指定した送信が必要です。")
            return
        try:
            raw = lengths[0]
            if not raw.isascii() or not raw.isdigit() or len(raw) > 10:
                raise ValueError
            length = int(raw)
        except ValueError:
            self._error(400, "画像サイズが不正です。")
            return
        if length < 1:
            self._error(400, "画像を選択してください。")
            return
        if length > self.server.config.max_bytes:
            self._error(413, "画像の容量が上限を超えています。")
            return
        if not self.server.processing.acquire(blocking=False):
            self._error(429, "別の画像を処理中です。少し待って再送してください。")
            return
        try:
            self.unread = 0  # A failed read means a broken or slow peer: do not wait for it again.
            try:
                content = read_upload(self.rfile, self.connection, length, self.server.config.socket_timeout)
            except (socket.timeout, OSError):
                self._error(408, "画像の受信がタイムアウトしました。通信を確認して再送してください。")
                return
            except EOFError:
                self._error(400, "画像を最後まで受信できませんでした。")
                return
            if len(content) != length:
                self._error(400, "画像を最後まで受信できませんでした。")
                return
            config = self.server.config
            image = normalize_image(content, max_bytes=config.max_bytes,
                                    max_pixels=config.max_pixels, max_edge=config.max_edge)
            self.server.clipboard.write(dib_bytes(image))
            dry_run = self.server.clipboard.mode == "dry-run"
            self._reply(200, {"ok": True, "dry_run": dry_run, "clipboard_updated": not dry_run,
                             "width": image.width, "height": image.height,
                             "message": ("画像を処理しました。dry-runのためクリップボードは更新していません。"
                                         if dry_run else "PCのクリップボードに画像をコピーしました。PCで貼り付けてください。")})
        except ImageValidationError as error:
            status = 413 if error.code == "too_large" else 415 if error.code == "unsupported" else 422
            self._error(status, str(error))
        except ClipboardError:
            self._error(503, "クリップボードへコピーできませんでした。PCがロック中でないか確認し、少し待って再送してください。")
        except Exception:
            self._error(500, "画像を処理できませんでした。別の画像で再試行してください。")
        finally:
            self.server.processing.release()


def make_server(config: ServerConfig, clipboard, *, token: str | None = None) -> SnapPasteServer:
    return SnapPasteServer(config, clipboard, token or secrets.token_urlsafe(32))
