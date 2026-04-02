from RealtimeSTT import AudioToTextRecorder


class STT:
    """
    Wrapper around RealtimeSTT for say-it's hold-to-record hotkey model.

    Usage:
        stt.start()          # hotkey down
        stt.stop()           # hotkey up
        text = stt.get_text()  # blocks until transcription ready, then returns
    """

    def __init__(self, model_name="small", language="auto", on_partial=None):
        self._model_name = model_name
        self._language = language
        self._on_partial = on_partial
        self._recorder = self._make_recorder()

    def _make_recorder(self):
        lang = "" if not self._language or self._language == "auto" else self._language
        kwargs = dict(
            model=self._model_name,
            language=lang,
            silero_use_onnx=True,
            enable_realtime_transcription=self._on_partial is not None,
            realtime_model_type="tiny",
            realtime_processing_pause=0.2,
            post_speech_silence_duration=0.5,
            faster_whisper_vad_filter=True,
            ensure_sentence_ends_with_period=False,
            ensure_sentence_starting_uppercase=False,
            print_transcription_time=False,
            no_log_file=True,
        )
        if self._on_partial:
            kwargs["on_realtime_transcription_update"] = self._on_partial
        return AudioToTextRecorder(**kwargs)

    def start(self):
        self._recorder.start()

    def stop(self):
        self._recorder.stop()

    def get_text(self) -> str:
        """Blocking — returns final transcription after stop()."""
        return self._recorder.text() or ""

    def set_language(self, language: str):
        if self._language == language:
            return
        self._language = language
        try:
            self._recorder.shutdown()
        except Exception:
            pass
        self._recorder = self._make_recorder()

    def shutdown(self):
        try:
            self._recorder.shutdown()
        except Exception:
            pass
