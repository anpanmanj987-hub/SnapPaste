"""Japanese and English text for the phone page replies and the command line."""
from __future__ import annotations

import os
import sys

LANGUAGES = ("ja", "en")

MESSAGES = {
    # Image validation (shown on the phone)
    "empty_image": ("画像が空です。JPEG・PNG・WebPを選んでください。", "The image is empty. Choose a JPEG, PNG or WebP image."),
    "image_too_large": ("画像の容量が上限を超えています。小さい画像を選んでください。", "The image is too large. Choose a smaller one."),
    "too_many_pixels": ("画像の画素数が上限を超えています。", "The image has too many pixels."),
    "animated": ("アニメーション画像には対応していません。", "Animated images are not supported."),
    "pixel_bomb": ("画像の画素数が安全上の上限を超えています。", "The image exceeds the safe pixel limit."),
    "unsupported": ("JPEG・PNG・WebPを選んでください。HEICはJPEGへ変換してください。", "Choose a JPEG, PNG or WebP image. Convert HEIC to JPEG first."),
    "corrupt": ("画像を読み込めませんでした。壊れていない別の画像を選んでください。", "Could not read the image. Choose another one that is not damaged."),
    # HTTP replies (shown on the phone)
    "host_mismatch": ("接続先が一致しません。PCのQRコードから接続してください。", "Wrong address. Connect from the QR code on the PC."),
    "bad_token": ("接続コードが無効です。PCの新しいQRコードから接続してください。", "Invalid connection code. Connect from the new QR code on the PC."),
    "bad_origin": ("この送信元からは操作できません。PCのQRコードから接続してください。", "Requests from this page are not allowed. Connect from the QR code on the PC."),
    "not_found": ("ページが見つかりません。", "Page not found."),
    "no_cors": ("外部ページからの操作は許可していません。", "Requests from other sites are not allowed."),
    "no_endpoint": ("送信先が見つかりません。", "Unknown endpoint."),
    "length_required": ("画像サイズを指定した送信が必要です。", "Send the image with a Content-Length."),
    "bad_length": ("画像サイズが不正です。", "Invalid image size."),
    "no_image": ("画像を選択してください。", "Choose an image."),
    "upload_too_large": ("画像の容量が上限を超えています。", "The image is larger than the limit."),
    "busy": ("別の画像を処理中です。少し待って再送してください。", "Another image is being processed. Wait a moment and send again."),
    "receive_timeout": ("画像の受信がタイムアウトしました。通信を確認して再送してください。", "Receiving the image timed out. Check the connection and send again."),
    "incomplete": ("画像を最後まで受信できませんでした。", "The image did not arrive completely."),
    "processed_dry_run": ("画像を処理しました。dry-runのためクリップボードは更新していません。", "Image processed. The clipboard was not updated (dry-run)."),
    "copied": ("PCのクリップボードに画像をコピーしました。PCで貼り付けてください。", "Copied the image to the PC clipboard. Paste it on the PC."),
    "clipboard_failed": ("クリップボードへコピーできませんでした。PCがロック中でないか確認し、少し待って再送してください。",
                         "Could not copy to the clipboard. Make sure the PC is not locked, then send again."),
    "processing_failed": ("画像を処理できませんでした。別の画像で再試行してください。", "Could not process the image. Try another one."),
    # Clipboard (command line and logs)
    "empty_data": ("画像データが空です。", "The image data is empty."),
    "clipboard_unavailable": ("クリップボードを開けません。PCがロック中か、他のアプリが使用中です。", "Cannot open the clipboard. The PC may be locked, or another app is using it."),
    "windows_only": ("Windows以外では --dry-run を指定してください。", "Use --dry-run on systems other than Windows."),
    "init_timeout": ("Windowsクリップボードの初期化がタイムアウトしました。", "Initializing the Windows clipboard timed out."),
    "init_failed": ("Windowsクリップボードを初期化できませんでした。", "Could not initialize the Windows clipboard."),
    "worker_stopped": ("クリップボードの受信処理が停止しています。", "The clipboard worker has stopped."),
    "worker_busy": ("クリップボードの処理中です。再送してください。", "The clipboard is busy. Send again."),
    "worker_timeout": ("クリップボードの処理がタイムアウトしました。PCで状態を確認してください。", "The clipboard operation timed out. Check the PC."),
    # Command line
    "cli_description": ("SnapPaste: スマホの写真をWindowsの画像クリップボードへ送信します。", "SnapPaste: send phone photos to the Windows image clipboard."),
    "help_host": ("待受IPv4 (既定:127.0.0.1)。LAN公開は明示してください", "IPv4 address to listen on (default: 127.0.0.1). LAN access must be explicit"),
    "help_advertise": ("QRに表示するPCのIPv4。0.0.0.0待受時は必須", "PC IPv4 address shown in the QR code; required with --host 0.0.0.0"),
    "help_port": ("待受port (既定:8766)", "TCP port (default: 8766)"),
    "help_max_edge": ("処理後の長辺上限px (1..8192、既定:1920)", "Longest edge after processing, in px (1..8192, default: 1920)"),
    "help_max_mib": ("受信容量上限MiB (1..25、既定:25)", "Upload size limit in MiB (1..25, default: 25)"),
    "help_max_pixels": ("入力画素数上限 (最大50,000,000)", "Input pixel limit (at most 50,000,000)"),
    "help_timeout": ("ソケットの読取タイムアウト秒 (既定:10)", "Socket read timeout in seconds (default: 10)"),
    "help_dry_run": ("画像処理だけ確認。クリップボード更新・画像保存を行いません", "Process images only; never update the clipboard or save images"),
    "help_no_qr": ("ターミナルQRを省略し参加URLだけ表示", "Print only the join URL, without the terminal QR code"),
    "cli_dry_run_required": ("Windows以外では --dry-run を明示してください。クリップボードは更新しません。", "On systems other than Windows, pass --dry-run. The clipboard is not updated."),
    "cli_dry_run_notice": ("dry-run: クリップボードは更新せず、画像も保存しません。", "dry-run: the clipboard is not updated and no images are saved."),
    "cli_join_url": ("参加URL (この起動中だけ有効・共有しないでください):", "Join URL (valid while this host runs; do not share it):"),
    "cli_no_qr": ("QRを表示できません。参加URLをスマートフォンで開いてください。", "Cannot show the QR code here. Open the join URL on your phone."),
    "cli_running": ("Ctrl+Cで終了。LAN通信は平文HTTPです。信頼できるネットワークで利用してください。", "Press Ctrl+C to stop. LAN traffic is plain HTTP; use a trusted network."),
    "cli_stopped": ("SnapPasteを終了します。", "SnapPaste stopped."),
    "cli_start_failed": ("起動できませんでした", "Could not start"),
}


def language(header: str | None) -> str:
    """Pick ja or en from an Accept-Language header; anything else is English."""
    for part in (header or "").split(","):
        tag = part.split(";")[0].strip().lower()
        if tag.startswith("ja"):
            return "ja"
        if tag.startswith("en"):
            return "en"
    return "en"


def cli_language() -> str:
    """SNAPPASTE_LANG, then LC_ALL/LC_MESSAGES/LANG, then the Windows display language."""
    choice = os.environ.get("SNAPPASTE_LANG", "").lower()
    if choice in LANGUAGES:
        return choice
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value and value not in ("C", "POSIX"):
            return "ja" if value.lower().startswith("ja") else "en"
    if sys.platform == "win32":
        import ctypes
        try:
            # Primary language ID 0x11 is Japanese.
            return "ja" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x11 else "en"
        except (AttributeError, OSError):
            pass
    return "en"


def text(key: str, lang: str = "en", detail: str = "") -> str:
    message = MESSAGES[key][LANGUAGES.index(lang) if lang in LANGUAGES else 1]
    if not detail:
        return message
    return f"{message}：{detail}" if lang == "ja" else f"{message}: {detail}"
