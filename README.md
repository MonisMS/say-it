# say-it

**Voice to text. Fully local. Nothing leaves your machine.**

Hold a key, speak, release. Your words appear wherever your cursor is — in any app, any text box, anywhere on Windows.

No account. No internet after setup. No one listening.

---

## Why say-it

Every other voice typing tool sends your audio to a server somewhere.

| Tool | Where your voice goes |
|---|---|
| Google Dictation | Google's servers |
| OpenAI Whisper API | OpenAI's servers |
| Wispr Flow | Their servers |
| Dragon | Nuance/Microsoft |
| **say-it** | **Your machine. Only your machine.** |

This matters if you're a doctor, lawyer, journalist, or anyone who speaks things that shouldn't leave the room.

---

## How it works

1. Hold **Right Alt**
2. Speak
3. Release — text appears where your cursor is

That's it. Works in Chrome, VS Code, Notepad, WhatsApp Web, anywhere.

---

## Features

- **100% local** — Whisper runs on your CPU or GPU, nothing is sent anywhere
- **Works offline** — after the one-time model download, no internet needed ever
- **Any app** — pastes into whatever window you're working in
- **Language modes** — switch between Auto, Hindi, or translate-to-English from the tray
- **History** — right-click the tray icon to see past transcriptions
- **Lightweight** — lives in your system tray, uses no resources when idle

---

## Installation

### Requirements
- Windows 10 or 11 (64-bit)
- Microphone
- Internet connection (first run only, to download the AI model)

### Steps

1. Download `say-it.exe` from [Releases](../../releases)
2. Run it — Windows may show a security warning, click **More info → Run anyway**
3. The tray icon appears (green dot)
4. First run downloads the AI model (~450 MB) — wait about 2 minutes
5. Done. Hold Right Alt and start speaking

> The security warning appears because the app isn't signed with a paid certificate yet. The code is fully open source — you can verify exactly what it does.

---

## Language modes

Right-click the tray icon to switch:

| Mode | What it does |
|---|---|
| Auto (default) | Detects your language, transcribes as-is |
| Hindi → Hindi | Forces Hindi, outputs Devanagari script |
| Any language → English | Speak anything, get English text |

---

## Building from source

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/say-it
cd say-it

# Install dependencies (Windows)
install.bat

# Run directly
run.bat

# Build .exe
build.bat
```

Requires Windows Python 3.10+.

---

## Configuration

Settings are stored at `%APPDATA%\say-it\config.json`:

```json
{
  "model": "small",
  "language": "auto",
  "task": "transcribe",
  "hotkey": "right alt",
  "sample_rate": 16000,
  "device": null
}
```

**Models** (trade-off between speed and accuracy):

| Model | Size | Speed (CPU) | Accuracy |
|---|---|---|---|
| `tiny` | 75 MB | ~1s | Basic |
| `base` | 145 MB | ~1-2s | Okay |
| `small` | 450 MB | ~2-3s | Good (default) |
| `medium` | 1.5 GB | ~5-10s | Better |
| `large-v3` | 3 GB | ~15-20s | Best |

GPU (NVIDIA) is auto-detected — if you have one, transcription is near-instant.

---

## Privacy

- Audio is processed entirely on your device by [OpenAI Whisper](https://github.com/openai/whisper) via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- No telemetry, no analytics, no network calls after model download
- No account required
- History is stored locally in SQLite at `%APPDATA%\say-it\history.db`
- Source code is fully open — read every line

---

## Tech stack

- **Transcription**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Whisper on CPU/GPU)
- **Hotkey**: [keyboard](https://github.com/boppreh/keyboard)
- **Tray**: [pystray](https://github.com/moses-palmer/pystray)
- **Audio**: [sounddevice](https://python-sounddevice.readthedocs.io/)
- **Paste**: Win32 clipboard API (raw ctypes)

---

## Roadmap

- [ ] Installer with auto-start on Windows boot
- [ ] Microsoft Store release (zero install friction)
- [ ] Custom hotkey from tray settings
- [ ] Mac support
- [ ] Punctuation mode

---

## License

MIT — do whatever you want with it.
