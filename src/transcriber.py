import numpy as np
from faster_whisper import WhisperModel


def _load_model(model_name: str) -> tuple:
    """
    Try GPU first (float16), fall back to CPU (int8).
    Returns (model, device_label).
    """
    try:
        model = WhisperModel(model_name, device="cuda", compute_type="float16")
        return model, "GPU"
    except Exception:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        return model, "CPU"


class Transcriber:
    def __init__(self, model_name: str = "small", language: str = "auto",
                 task: str = "transcribe"):
        print(f"Loading model '{model_name}' (first run downloads it)...")
        self.model, device = _load_model(model_name)
        self.language = None if language == "auto" else language
        # task = "transcribe" → output in spoken language
        # task = "translate"  → always output in English
        self.task = task
        print(f"Model ready on {device}.\n")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            task=self.task,
            beam_size=1,                  # greedy decoding — ~2x faster, minimal quality loss
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300, "threshold": 0.3},
            condition_on_previous_text=False,
            no_speech_threshold=0.4,
            temperature=0,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
