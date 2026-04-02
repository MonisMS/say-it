"""
Streaming transcriber using whisper_streaming's LocalAgreement algorithm.

Architecture:
- Audio captured via sounddevice during key hold
- Every CHUNK_SECONDS of audio, process_iter() commits confirmed words
- Audio buffer stays bounded (trimmed after commit) — never grows to full length
- On key release, finish() flushes the uncommitted tail only (~3-5s max)
- Result: 40s recording → ~3-8s wait, not 40s
"""

import io
import queue
import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from src.whisper_online_core import OnlineASRProcessor


class _ASRShim:
    """
    Connects our WhisperModel to OnlineASRProcessor's expected interface.
    """
    sep = ""

    def __init__(self, model: WhisperModel, language=None):
        self.model = model
        self.language = language

    def transcribe(self, audio: np.ndarray, init_prompt=""):
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            initial_prompt=init_prompt or None,
            beam_size=1,
            word_timestamps=True,
            condition_on_previous_text=True,
            repetition_penalty=1.5,
            temperature=0,
            vad_filter=False,
        )
        return list(segments)

    def ts_words(self, segments):
        out = []
        for seg in segments:
            if not seg.words:
                continue
            if seg.no_speech_prob > 0.9:
                continue
            for w in seg.words:
                out.append((w.start, w.end, w.word))
        return out

    def segments_end_ts(self, segments):
        return [s.end for s in segments]

    def use_vad(self):
        pass


class StreamingSTT:
    """
    Hold-to-record streaming transcriber.

    Usage:
        stt.start()            # key DOWN
        stt.stop()             # key UP (fast, non-blocking)
        text = stt.get_text()  # blocks only for the last ~3-5s chunk
    """

    SAMPLE_RATE   = 16000
    CHUNK_SECONDS = 3.0

    def __init__(self, model_name="small", language=None, on_partial=None):
        self._language   = None if not language or language == "auto" else language
        self._on_partial = on_partial

        print(f"Loading model '{model_name}'...")
        self._model = WhisperModel(model_name, device="cpu", compute_type="int8")
        print("Model ready on CPU.")

        self._shim   = _ASRShim(self._model, self._language)
        self._online = self._make_processor()

        self._audio_q          = queue.Queue()
        self._stream           = None
        self._processor_thread = None
        self._stop_event       = threading.Event()
        self._committed_parts  = []

    def _make_processor(self):
        return OnlineASRProcessor(
            self._shim,
            tokenizer=None,
            buffer_trimming=("segment", 30),
            logfile=io.StringIO(),
        )

    def _sd_callback(self, indata, frames, time_info, status):
        self._audio_q.put(indata.copy().flatten())

    def _process_loop(self):
        chunk_samples = int(self.CHUNK_SECONDS * self.SAMPLE_RATE)
        pending = np.array([], dtype=np.float32)

        while not self._stop_event.is_set() or not self._audio_q.empty():
            try:
                chunk = self._audio_q.get(timeout=0.1)
                pending = np.concatenate([pending, chunk])
            except queue.Empty:
                continue

            if len(pending) >= chunk_samples:
                self._online.insert_audio_chunk(pending[:chunk_samples])
                pending = pending[chunk_samples:]
                _, _, text = self._online.process_iter()
                if text:
                    self._committed_parts.append(text)
                    if self._on_partial:
                        self._on_partial(" ".join(self._committed_parts))

        # Insert remaining audio so finish() can flush it
        if len(pending) > 0:
            self._online.insert_audio_chunk(pending)

        # Final process_iter() — handles short recordings under CHUNK_SECONDS
        _, _, text = self._online.process_iter()
        if text:
            self._committed_parts.append(text)
            if self._on_partial:
                self._on_partial(" ".join(self._committed_parts))

    def start(self):
        self._committed_parts = []
        self._stop_event.clear()
        self._online.init()

        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._sd_callback,
        )
        self._processor_thread = threading.Thread(
            target=self._process_loop, daemon=True
        )
        self._stream.start()
        self._processor_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def get_text(self) -> str:
        if self._processor_thread:
            self._processor_thread.join(timeout=30.0)

        _, _, tail = self._online.finish()
        if tail:
            self._committed_parts.append(tail)

        return " ".join(self._committed_parts).strip()

    def set_language(self, language: str):
        if self._language == language:
            return
        self._language = None if not language or language == "auto" else language
        self._shim.language = self._language
        self._online = self._make_processor()

    def shutdown(self):
        self._stop_event.set()
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
