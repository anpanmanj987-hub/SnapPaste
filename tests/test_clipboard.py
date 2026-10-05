"""Only the Win32 boundary is fake: real writer must conserve transferred memory."""
import ctypes
import unittest

try:
    from snappaste.clipboard import NativeClipboardWriter, ClipboardError
except ImportError:
    NativeClipboardWriter = None


class FakeWindows:
    def __init__(self, fail="", open_failures=0):
        self.fail = fail
        self.open_failures = open_failures
        self.opens = 0
        self.closed = 0
        self.freed = 0
        self.owner = None
        self.clipboard = None
        self.buffer = None
        self.order = []
        self.error = 0

    def GlobalAlloc(self, flags, size):
        self.order.append("allocate")
        if self.fail == "allocate":
            return 0
        if flags != 2:
            raise AssertionError("clipboard memory must be movable")
        self.buffer = ctypes.create_string_buffer(size)
        return 0x100000001

    def GlobalLock(self, handle):
        if self.fail == "lock":
            return 0
        return ctypes.addressof(self.buffer)

    def GlobalUnlock(self, handle):
        self.error = 0
        return 0  # zero with NO_ERROR is the normal final unlock.

    def GlobalFree(self, handle):
        self.freed += 1
        return 0

    def OpenClipboard(self, owner):
        self.order.append("open")
        self.owner = owner
        self.opens += 1
        return self.opens > self.open_failures

    def EmptyClipboard(self):
        if self.fail == "empty":
            return 0
        self.clipboard = None
        return 1

    def SetClipboardData(self, format, handle):
        if self.fail == "set":
            return 0
        if self.owner != 0x100000002 or format != 8:
            raise AssertionError("invalid owner or image format")
        self.clipboard = self.buffer.raw
        return handle

    def CloseClipboard(self):
        self.closed += 1
        return 0 if self.fail == "close" else 1


class ClipboardTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(NativeClipboardWriter, "native clipboard writer is not implemented")

    def writer(self, api, attempts=3):
        return NativeClipboardWriter(api, api, 0x100000002, attempts=attempts,
                                     retry_delay=0, get_last_error=lambda: api.error,
                                     set_last_error=lambda n: setattr(api, "error", n))

    def test_success_transfers_bytes_without_freeing(self):
        api = FakeWindows()
        self.writer(api).write(b"DIB pixels")
        self.assertEqual(api.clipboard, b"DIB pixels")
        self.assertEqual(api.freed, 0)
        self.assertEqual(api.closed, 1)
        self.assertEqual(api.order[:2], ["allocate", "open"])

    def test_set_failure_frees_untransferred_memory_and_closes(self):
        api = FakeWindows(fail="set")
        with self.assertRaises(ClipboardError):
            self.writer(api).write(b"pixels")
        self.assertEqual(api.freed, 1)
        self.assertEqual(api.closed, 1)

    def test_lock_failure_frees_before_open(self):
        api = FakeWindows(fail="lock")
        with self.assertRaises(ClipboardError):
            self.writer(api).write(b"pixels")
        self.assertEqual(api.freed, 1)
        self.assertEqual(api.opens, 0)

    def test_allocate_failure_does_not_open_clipboard(self):
        api = FakeWindows(fail="allocate")
        with self.assertRaises(ClipboardError):
            self.writer(api).write(b"pixels")
        self.assertEqual(api.opens, 0)
        self.assertEqual(api.freed, 0)

    def test_open_retries_are_bounded_and_failed_memory_is_freed(self):
        api = FakeWindows(open_failures=100)
        with self.assertRaises(ClipboardError):
            self.writer(api).write(b"pixels")
        self.assertEqual(api.opens, 3)
        self.assertEqual(api.freed, 1)
        self.assertEqual(api.closed, 0)

    def test_temporary_contention_can_recover(self):
        api = FakeWindows(open_failures=2)
        self.writer(api).write(b"pixels")
        self.assertEqual(api.clipboard, b"pixels")
        self.assertEqual(api.opens, 3)

    def test_empty_failure_closes_and_frees(self):
        api = FakeWindows(fail="empty")
        with self.assertRaises(ClipboardError):
            self.writer(api).write(b"pixels")
        self.assertEqual(api.closed, 1)
        self.assertEqual(api.freed, 1)

    def test_null_owner_is_rejected(self):
        api = FakeWindows()
        with self.assertRaises(ValueError):
            NativeClipboardWriter(api, api, 0)

    def test_close_failure_is_reported_without_freeing_system_memory(self):
        api = FakeWindows(fail="close")
        with self.assertRaises(ClipboardError):
            self.writer(api).write(b"pixels")
        self.assertEqual(api.clipboard, b"pixels")
        self.assertEqual(api.freed, 0)


if __name__ == "__main__":
    unittest.main()
