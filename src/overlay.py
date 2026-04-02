"""
Floating overlay pill that sits above the Windows taskbar.
Shows recording/transcribing status. Uses tkinter (ships with Python).

Threading: ALL tkinter calls must happen on the main thread via root.after(0, fn).
"""
import ctypes
import tkinter as tk


class Overlay:
    W  = 260
    H  = 50
    BG = "#1C1C1E"
    FG = "#FFFFFF"
    FG_DIM = "#888888"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("say-it-overlay")
        self.root.overrideredirect(True)           # no title bar
        self.root.wm_attributes("-topmost", True)  # always on top
        self.root.wm_attributes("-alpha", 0.93)
        self.root.wm_attributes("-toolwindow", True)  # don't steal focus
        self.root.configure(bg=self.BG)
        self.root.withdraw()                       # hidden at start

        self._label = tk.Label(
            self.root,
            text="",
            bg=self.BG,
            fg=self.FG,
            font=("Segoe UI", 12),
            padx=20,
        )
        self._label.pack(expand=True, fill="both")

        self._position()
        self._corners_applied = False

    def _position(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - self.W) // 2
        y  = sh - self.H - 72      # above taskbar
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _apply_rounded_corners(self):
        """Win11 native rounded corners via DWM."""
        try:
            hwnd = int(self.root.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass  # Win10 fallback: square corners, still looks fine

    def show(self, text: str, dim: bool = False):
        """Show overlay with text. Thread-safe."""
        self.root.after(0, self._show, text, dim)

    def _show(self, text: str, dim: bool):
        self._label.config(text=text, fg=self.FG_DIM if dim else self.FG)
        self.root.deiconify()
        self.root.lift()
        if not self._corners_applied:
            self.root.after(50, self._apply_rounded_corners)
            self._corners_applied = True

    def hide(self):
        """Hide overlay. Thread-safe."""
        self.root.after(0, self.root.withdraw)

    def destroy(self):
        """Call from quit handler to stop mainloop."""
        self.root.after(0, self.root.destroy)
