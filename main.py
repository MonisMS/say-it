import sys
import ctypes
import threading
import keyboard
import pystray
from PIL import Image, ImageDraw

from src.config      import Config
from src.recorder    import Recorder, list_input_devices
from src.transcriber import Transcriber
from src.autotype    import AutoTyper
from src.history     import History


def make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    return img


ICON_IDLE      = make_icon("#4CAF50")  # green
ICON_RECORDING = make_icon("#F44336")  # red
ICON_THINKING  = make_icon("#FF9800")  # orange


def show_message(title: str, text: str):
    ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)


def main():
    config      = Config()
    history     = History()
    list_input_devices()
    recorder    = Recorder(sample_rate=config.sample_rate, device=config.device)
    transcriber = Transcriber(
        model_name=config.model,
        language=config.language,
        task=getattr(config, 'task', 'transcribe'),
    )
    autotyper = AutoTyper()

    _recording   = False
    _lock        = threading.Lock()
    _icon        = [None]
    _target_hwnd = [None]

    def set_status(label: str, img: Image.Image):
        icon = _icon[0]
        if icon is not None:
            icon.title = f"say-it  •  {label}"
            icon.icon  = img

    def do_transcribe():
        set_status("Transcribing...", ICON_THINKING)
        audio = recorder.stop()
        if audio is None or len(audio) < config.sample_rate * 0.3:
            print("Too short, skipping.")
            set_status("Idle", ICON_IDLE)
            return
        print("Transcribing...", end="", flush=True)
        text = transcriber.transcribe(audio)
        if not text:
            print(" nothing detected.")
            set_status("Idle", ICON_IDLE)
            return
        print(f" done.\n> {text}\n")
        autotyper.type(text, _target_hwnd[0])
        history.add(text)
        set_status("Idle", ICON_IDLE)

    def on_hotkey(e):
        nonlocal _recording
        if e.event_type == keyboard.KEY_DOWN:
            with _lock:
                if _recording:
                    return
                _recording = True
            _target_hwnd[0] = ctypes.windll.user32.GetForegroundWindow()
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(_target_hwnd[0], buf, 256)
            print(f"Recording... (target: '{buf.value}')", flush=True)
            set_status("Recording...", ICON_RECORDING)
            recorder.start()
        elif e.event_type == keyboard.KEY_UP:
            with _lock:
                if not _recording:
                    return
                _recording = False
            print("stopped.")
            threading.Thread(target=do_transcribe, daemon=True).start()

    # ── Mode switching ──────────────────────────────────────────────────────

    def set_mode_transcribe(icon, item):
        transcriber.task = "transcribe"
        transcriber.language = None if config.language == "auto" else config.language
        print("Mode: Transcribe (original language)")
        set_status("Transcribe mode", ICON_IDLE)
        icon.update_menu()

    def set_mode_hindi(icon, item):
        transcriber.task = "transcribe"
        transcriber.language = "hi"
        print("Mode: Hindi → Hindi")
        set_status("Hindi mode", ICON_IDLE)
        icon.update_menu()

    def set_mode_translate(icon, item):
        transcriber.task = "translate"
        transcriber.language = None   # auto-detect input language
        print("Mode: Translate → English")
        set_status("Translate mode", ICON_IDLE)
        icon.update_menu()

    def show_history():
        rows = history.recent(20)
        if not rows:
            show_message("say-it  —  History", "No transcriptions yet.")
            return
        lines = "\n".join(f"[{r[2][:19]}]  {r[1]}" for r in rows)
        show_message("say-it  —  History", lines)

    def quit_app(icon):
        keyboard.unhook_all()
        icon.stop()
        sys.exit(0)

    keyboard.hook_key(config.hotkey, on_hotkey, suppress=True)

    menu = pystray.Menu(
        pystray.MenuItem("say-it", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Mode: Auto (default)",      set_mode_transcribe),
        pystray.MenuItem("Mode: Hindi → Hindi",       set_mode_hindi),
        pystray.MenuItem("Mode: Any language → English", set_mode_translate),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Show History", lambda icon, item: show_history()),
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon("say-it", ICON_IDLE, "say-it  •  Idle", menu)
    _icon[0] = icon

    print("say-it is running.")
    print("Hold RIGHT ALT to record, release to transcribe.")
    print("Right-click the tray icon to switch language mode or show history.\n")

    icon.run()


if __name__ == "__main__":
    main()
