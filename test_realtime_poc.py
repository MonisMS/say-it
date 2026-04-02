"""
Proof-of-concept: test RealtimeSTT's start()/stop() pattern
against say-it's hotkey hold-and-release model.

Run with: python test_realtime_poc.py
Hold Enter to start recording, release (press Enter again) to stop.
"""
import sys

if __name__ == "__main__":
    print("Importing RealtimeSTT...")
    try:
        from RealtimeSTT import AudioToTextRecorder
    except ImportError:
        print("ERROR: RealtimeSTT not installed. Run: pip install RealtimeSTT")
        sys.exit(1)

    print("Initializing recorder (tiny model, ONNX VAD)...")
    print("This may take a moment on first run.\n")

    partial_results = []

    def on_partial(text):
        partial_results.append(text)
        print(f"\r[live] {text}          ", end="", flush=True)

    recorder = AudioToTextRecorder(
        model="tiny",
        language="en",
        silero_use_onnx=True,
        enable_realtime_transcription=True,
        realtime_model_type="tiny",
        realtime_processing_pause=0.2,
        on_realtime_transcription_update=on_partial,
        post_speech_silence_duration=0.5,
        ensure_sentence_ends_with_period=False,
        ensure_sentence_starting_uppercase=False,
        print_transcription_time=True,
    )

    print("Recorder ready.\n")
    print("--- Test 1: manual start/stop (simulates hotkey hold-release) ---")
    input("Press Enter to START recording...")

    recorder.start()
    print("[recording... speak now]")

    input("Press Enter to STOP recording...")
    recorder.stop()

    print("\n[processing...]")
    result = recorder.text()

    print(f"\n[FINAL RESULT]: '{result}'")
    print(f"[partial updates captured]: {len(partial_results)}")

    print("\n--- Test passed if result is non-empty ---")
    if result:
        print("PASS: start()/stop() pattern works.")
    else:
        print("FAIL or empty: no transcription returned. Check microphone.")

    recorder.shutdown()
    print("Done.")
