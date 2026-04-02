import sys
import ctypes
import threading
import keyboard
import pystray
from PIL import Image, ImageDraw

from src.config         import Config
from src.streaming_stt  import StreamingSTT
from src.autotype       import AutoTyper
from src.history        import History
from src.overlay        import Overlay


def make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    return img


ICON_IDLE      = make_icon("#4CAF50")   # green
ICON_RECORDING = make_icon("#F44336")   # red
ICON_THINKING  = make_icon("#FF9800")   # orange


def show_message(title: str, text: str):
    ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)


def main():
    config    = Config()
    history   = History()
    autotyper = AutoTyper()
    overlay   = Overlay()

    _recording    = False
    _transcribing = False
    _lock         = threading.Lock()
    _icon         = [None]
    _target_hwnd  = [None]

    def set_status(label: str, img: Image.Image, overlay_text: str = "", dim: bool = False):
        icon = _icon[0]
        if icon is not None:
            icon.title = f"say-it  •  {label}"
            icon.icon  = img
        if overlay_text:
            overlay.show(overlay_text, dim=dim)
        else:
            overlay.hide()

    def on_partial(text):
        preview = (text[:40] + "...") if len(text) > 40 else text
        set_status(preview, ICON_RECORDING, overlay_text=f"  {preview}  ")

    stt = StreamingSTT(
        model_name=config.model,
        language=config.language,
        on_partial=on_partial,
    )

    def do_transcribe():
        nonlocal _transcribing
        set_status("Transcribing...", ICON_THINKING,
                   overlay_text="  Transcribing...  ", dim=True)
        text = stt.get_text()
        if text:
            autotyper.type(text, _target_hwnd[0])
            history.add(text)
        set_status("Idle", ICON_IDLE)
        with _lock:
            _transcribing = False

    def on_hotkey(e):
        nonlocal _recording, _transcribing
        if e.event_type == keyboard.KEY_DOWN:
            with _lock:
                if _recording or _transcribing:
                    return
                _recording = True
            _target_hwnd[0] = ctypes.windll.user32.GetForegroundWindow()
            set_status("Recording...", ICON_RECORDING,
                       overlay_text="  Recording...  ")
            stt.start()
        elif e.event_type == keyboard.KEY_UP:
            with _lock:
                if not _recording:
                    return
                _recording    = False
                _transcribing = True
            stt.stop()
            threading.Thread(target=do_transcribe, daemon=True).start()

    # ── Mode switching ──────────────────────────────────────────────────────

    def set_mode_auto(icon, item):
        stt.set_language("auto")
        set_status("Idle", ICON_IDLE)
        icon.update_menu()

    def set_mode_hindi(icon, item):
        stt.set_language("hi")
        set_status("Idle", ICON_IDLE)
        icon.update_menu()

    def show_history():
        import tkinter as tk
        rows = history.recent(20)

        win = tk.Toplevel(overlay.root)
        win.title("say-it — History")
        win.configure(bg="#1C1C1E")
        win.geometry("540x400")
        win.resizable(True, True)
        win.wm_attributes("-topmost", True)

        txt = tk.Text(
            win, bg="#1C1C1E", fg="#FFFFFF", font=("Segoe UI", 11),
            relief="flat", padx=12, pady=12, wrap="word", cursor="arrow",
        )
        txt.pack(expand=True, fill="both")

        if not rows:
            txt.insert("end", "No transcriptions yet.")
        else:
            for r in rows:
                txt.insert("end", f"{r[2][:19]}\n", "dim")
                txt.insert("end", f"{r[1]}\n\n")

        txt.tag_config("dim", foreground="#888888", font=("Segoe UI", 9))
        txt.config(state="normal")  # keep selectable/copyable

        tk.Button(
            win, text="Close", bg="#2a2a2a", fg="#fff",
            relief="flat", padx=16, pady=6, cursor="hand2",
            command=win.destroy,
        ).pack(pady=(0, 12))

        overlay.root.after(0, win.lift)

    def quit_app(icon):
        keyboard.unhook_all()
        overlay.destroy()
        icon.stop()
        stt.shutdown()
        sys.exit(0)

    keyboard.hook_key(config.hotkey, on_hotkey, suppress=True)

    menu = pystray.Menu(
        pystray.MenuItem("say-it", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Mode: Auto (default)", set_mode_auto),
        pystray.MenuItem("Mode: Hindi → Hindi",  set_mode_hindi),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Show History", lambda icon, item: show_history()),
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon("say-it", ICON_IDLE, "say-it  •  Idle", menu)
    _icon[0] = icon

    # pystray needs its own thread; tkinter mainloop must run on main thread
    threading.Thread(target=icon.run, daemon=True).start()

    print("say-it is running. Hold RIGHT ALT to record.")
    overlay.root.mainloop()


if __name__ == "__main__":
    main()
