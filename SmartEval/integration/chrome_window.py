"""Track and close only the newly opened Chrome window, without activating it."""
import ctypes
from ctypes import wintypes
import os


class ChromeWindowTracker:
    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None
        self.target = None
        if self.user32:
            self.user32.GetForegroundWindow.restype = wintypes.HWND
            self.user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            self.user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            self.user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
            self.user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.before = self.windows()

    def windows(self):
        found = {}
        if not self.user32:
            return found
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def visit(handle, _):
            class_name = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(handle, class_name, len(class_name))
            if class_name.value == "Chrome_WidgetWin_1":
                title = ctypes.create_unicode_buffer(2048)
                pid = wintypes.DWORD()
                self.user32.GetWindowTextW(handle, title, len(title))
                self.user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
                if title.value.endswith(" - Google Chrome"):
                    found[handle] = (pid.value, title.value)
            return True

        self.user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        self.user32.EnumWindows(callback_type(visit), 0)
        return found

    def capture(self):
        current = self.windows()
        new = set(current) - set(self.before)
        if len(new) == 1:
            handle = new.pop()
            if handle == self.user32.GetForegroundWindow():
                self.target = (handle, current[handle])

    def close(self):
        if self.target is None:
            return False
        handle, identity = self.target
        if self.windows().get(handle) != identity:
            return False
        # WM_CLOSE is delivered to this window even if another app now has focus.
        return bool(self.user32.PostMessageW(handle, 0x0010, 0, 0))
