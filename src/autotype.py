"""
Text injection: raw Win32 clipboard + keyboard.send('ctrl+v').

Key findings from research into working tools (VoicePaste, hushtype):
- Raw ctypes SendInput(Ctrl+V) gets unreliably intercepted by the keyboard library's own hook.
- keyboard.send() is the correct way to fire keystrokes when the keyboard library is already active.
- SetForegroundWindow / focus manipulation at paste time HURTS — it moves focus away from
  the text cursor inside the window. Hushtype (reference impl) does zero focus manipulation.
- Stuck modifier keys (from Right Alt / AltGr suppress) must be released before paste.
- Raw ctypes Win32 clipboard IS the right approach for clipboard (works in PyInstaller bundles).
"""

import time
import ctypes
import threading
import keyboard

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Fix return/arg types for 64-bit Windows
kernel32.GlobalAlloc.restype    = ctypes.c_void_p
kernel32.GlobalAlloc.argtypes   = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalLock.restype     = ctypes.c_void_p
kernel32.GlobalLock.argtypes    = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes  = [ctypes.c_void_p]
kernel32.GlobalFree.restype     = ctypes.c_void_p
kernel32.GlobalFree.argtypes    = [ctypes.c_void_p]
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.GetClipboardData.restype  = ctypes.c_void_p

CF_UNICODETEXT = 13
GMEM_MOVEABLE  = 0x0002

# Terminal window classes that need Ctrl+Shift+V
_TERMINAL_CLASSES = {
    'CASCADIA_HOSTING_WINDOW_CLASS',
    'ConsoleWindowClass',
    'VirtualConsoleClass',
    'mintty',
    'PuTTY',
}

_clipboard_lock = threading.Lock()

# Modifier virtual key codes
_MODIFIERS = [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]  # LShift RShift LCtrl RCtrl LAlt RAlt


# ---------------------------------------------------------------------------
# Clipboard helpers — raw Win32, no pyperclip (works in PyInstaller)
# ---------------------------------------------------------------------------

def _clipboard_get() -> str:
    try:
        if not user32.OpenClipboard(0):
            return ''
        try:
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ''
            p = kernel32.GlobalLock(ctypes.c_void_p(h))
            if not p:
                return ''
            try:
                return ctypes.wstring_at(p)
            finally:
                kernel32.GlobalUnlock(ctypes.c_void_p(h))
        finally:
            user32.CloseClipboard()
    except Exception:
        return ''


def _clipboard_set(text: str):
    encoded = (text + '\x00').encode('utf-16-le')
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    if not h:
        raise OSError("GlobalAlloc failed")
    p = kernel32.GlobalLock(h)
    if not p:
        kernel32.GlobalFree(h)
        raise OSError("GlobalLock failed")
    ctypes.memmove(p, encoded, len(encoded))
    kernel32.GlobalUnlock(h)
    if not user32.OpenClipboard(0):
        kernel32.GlobalFree(h)
        raise OSError("OpenClipboard failed")
    try:
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_UNICODETEXT, h)
    finally:
        user32.CloseClipboard()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _release_stuck_modifiers():
    """
    Release any modifier keys still logically pressed (e.g. phantom Ctrl from AltGr).
    Must be called before sending Ctrl+V so Windows doesn't see double-Ctrl.
    """
    for vk in _MODIFIERS:
        if user32.GetAsyncKeyState(vk) & 0x8000:
            keyboard.release(keyboard.key_to_scan_codes(vk)[0])


def _get_window_class(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _get_window_title(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class AutoTyper:
    def type(self, text: str, target_hwnd=None):
        with _clipboard_lock:
            fg = user32.GetForegroundWindow()
            win_class = _get_window_class(fg)
            win_title = _get_window_title(fg)
            print(f"[paste] foreground: '{win_title}' ({win_class})", flush=True)

            use_shift = win_class in _TERMINAL_CLASSES

            old_text = _clipboard_get()
            try:
                _clipboard_set(text)
                time.sleep(0.1)             # let clipboard settle

                _release_stuck_modifiers()  # clear any stuck Alt/Ctrl from hotkey
                time.sleep(0.05)

                if use_shift:
                    keyboard.send('ctrl+shift+v')
                else:
                    keyboard.send('ctrl+v')

                time.sleep(0.1)
            finally:
                if old_text:
                    try:
                        _clipboard_set(old_text)
                    except Exception:
                        pass
