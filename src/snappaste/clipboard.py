"""Clipboard lifecycle, with Windows libraries loaded only in native mode."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
import queue
import sys
import threading
import time


class ClipboardError(RuntimeError):
    pass


class DryRunClipboard:
    mode = "dry-run"

    def write(self, data: bytes) -> None:
        """Validate that processing produced data, without saving or copying it."""
        if not data:
            raise ClipboardError("画像データが空です。")

    def close(self) -> None:
        pass


def _bind(library, name, arguments, result):
    function = getattr(library, name)
    function.argtypes = arguments
    function.restype = result
    return function


def _bind_clipboard(user32, kernel32):
    handle = ctypes.c_void_p
    _bind(user32, "OpenClipboard", [handle], wintypes.BOOL)
    _bind(user32, "EmptyClipboard", [], wintypes.BOOL)
    _bind(user32, "SetClipboardData", [wintypes.UINT, handle], handle)
    _bind(user32, "CloseClipboard", [], wintypes.BOOL)
    _bind(kernel32, "GlobalAlloc", [wintypes.UINT, ctypes.c_size_t], handle)
    _bind(kernel32, "GlobalLock", [handle], handle)
    _bind(kernel32, "GlobalUnlock", [handle], wintypes.BOOL)
    _bind(kernel32, "GlobalFree", [handle], handle)


class NativeClipboardWriter:
    """Synchronous ownership transaction; owner HWND belongs to the calling thread."""
    def __init__(self, user32, kernel32, hwnd, *, attempts: int = 15,
                 retry_delay: float = 0.05, get_last_error=None, set_last_error=None):
        if not hwnd or attempts < 1 or retry_delay < 0:
            raise ValueError("valid owner and bounded retry settings are required")
        self.user32, self.kernel32, self.hwnd = user32, kernel32, hwnd
        self.attempts, self.retry_delay = attempts, retry_delay
        self.get_last_error = get_last_error or ctypes.get_last_error
        self.set_last_error = set_last_error or ctypes.set_last_error

    def _error(self, operation):
        return ClipboardError(f"{operation} failed (Win32 error {self.get_last_error()})")

    def write(self, data: bytes) -> None:
        if not data:
            raise ClipboardError("画像データが空です。")
        memory = self.kernel32.GlobalAlloc(2, len(data))  # GMEM_MOVEABLE
        if not memory:
            raise self._error("GlobalAlloc")
        transferred = False
        opened = False
        locked = False
        try:
            pointer = self.kernel32.GlobalLock(memory)
            if not pointer:
                raise self._error("GlobalLock")
            locked = True
            ctypes.memmove(pointer, data, len(data))
            self.set_last_error(0)
            unlocked = self.kernel32.GlobalUnlock(memory)
            if not unlocked and self.get_last_error() != 0:
                raise self._error("GlobalUnlock")
            locked = False
            for attempt in range(self.attempts):
                if self.user32.OpenClipboard(self.hwnd):
                    opened = True
                    break
                if attempt + 1 < self.attempts:
                    time.sleep(self.retry_delay)
            if not opened:
                raise ClipboardError("クリップボードを開けません。PCがロック中か、他のアプリが使用中です。")
            if not self.user32.EmptyClipboard():
                raise self._error("EmptyClipboard")
            if not self.user32.SetClipboardData(8, memory):  # CF_DIB
                raise self._error("SetClipboardData")
            transferred = True
        finally:
            close_error = None
            if locked:
                self.kernel32.GlobalUnlock(memory)
            if opened and not self.user32.CloseClipboard():
                close_error = self._error("CloseClipboard")
            if not transferred:
                self.kernel32.GlobalFree(memory)
            if close_error and sys.exc_info()[0] is None:
                raise close_error


@dataclass
class _WriteJob:
    data: bytes
    done: threading.Event = field(default_factory=threading.Event)
    error: Exception | None = None
    cancelled: bool = False


class WindowsClipboard:
    """One native worker owns a hidden HWND and pumps its message queue."""
    mode = "windows"

    def __init__(self):
        if sys.platform != "win32":
            raise ClipboardError("Windows以外では --dry-run を指定してください。")
        self._jobs = queue.Queue(maxsize=1)
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._startup_error = None
        self._thread = threading.Thread(target=self._run, name="SnapPasteClipboard", daemon=True)
        self._thread.start()
        if not self._ready.wait(5):
            self._stop.set()
            raise ClipboardError("Windowsクリップボードの初期化がタイムアウトしました。")
        if self._startup_error:
            raise ClipboardError("Windowsクリップボードを初期化できませんでした。") from self._startup_error

    def _run(self):
        hwnd = None
        user32 = None
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            _bind_clipboard(user32, kernel32)
            _bind(kernel32, "GetModuleHandleW", [wintypes.LPCWSTR], ctypes.c_void_p)
            _bind(user32, "CreateWindowExW", [wintypes.DWORD, wintypes.LPCWSTR,
                  wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                  ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                  ctypes.c_void_p, ctypes.c_void_p], ctypes.c_void_p)
            _bind(user32, "DestroyWindow", [ctypes.c_void_p], wintypes.BOOL)

            class MSG(ctypes.Structure):
                _fields_ = [("hwnd", ctypes.c_void_p), ("message", wintypes.UINT),
                            ("wParam", ctypes.c_size_t), ("lParam", ctypes.c_ssize_t),
                            ("time", wintypes.DWORD), ("pt", wintypes.POINT),
                            ("lPrivate", wintypes.DWORD)]

            _bind(user32, "PeekMessageW", [ctypes.POINTER(MSG), ctypes.c_void_p,
                  wintypes.UINT, wintypes.UINT, wintypes.UINT], wintypes.BOOL)
            _bind(user32, "TranslateMessage", [ctypes.POINTER(MSG)], wintypes.BOOL)
            _bind(user32, "DispatchMessageW", [ctypes.POINTER(MSG)], ctypes.c_ssize_t)
            # STATIC is an OS-provided window class; HWND_MESSAGE is pointer-width -3.
            hwnd = user32.CreateWindowExW(0, "STATIC", "SnapPasteClipboard", 0,
                                        0, 0, 0, 0, ctypes.c_void_p(-3), None,
                                        kernel32.GetModuleHandleW(None), None)
            if not hwnd:
                raise ClipboardError(f"CreateWindowExW failed ({ctypes.get_last_error()})")
            writer = NativeClipboardWriter(user32, kernel32, hwnd)
            self._ready.set()
            message = MSG()
            while not self._stop.is_set():
                while user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
                    user32.TranslateMessage(ctypes.byref(message))
                    user32.DispatchMessageW(ctypes.byref(message))
                try:
                    job = self._jobs.get(timeout=0.02)
                except queue.Empty:
                    continue
                try:
                    if not job.cancelled:
                        writer.write(job.data)
                except Exception as error:
                    job.error = error
                finally:
                    job.done.set()
        except Exception as error:
            self._startup_error = error
        finally:
            self._ready.set()
            if hwnd and user32:
                user32.DestroyWindow(hwnd)

    def write(self, data: bytes) -> None:
        if self._stop.is_set() or not self._thread.is_alive():
            raise ClipboardError("クリップボードの受信処理が停止しています。")
        job = _WriteJob(data)
        try:
            self._jobs.put_nowait(job)
        except queue.Full as error:
            raise ClipboardError("クリップボードの処理中です。再送してください。") from error
        if not job.done.wait(5):
            job.cancelled = True
            raise ClipboardError("クリップボードの処理がタイムアウトしました。PCで状態を確認してください。")
        if job.error:
            raise ClipboardError(str(job.error)) from job.error

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
