from __future__ import annotations

import logging
import os
import wave
from pathlib import Path
from typing import Any

import imageio_ffmpeg
import numpy as np
import torch
from transformers import pipeline

from src.models.file_models import TranscriptSegment, TranscriptionResponse

logger = logging.getLogger(__name__)


def _ensure_ffmpeg_on_path() -> None:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = str(Path(ffmpeg_exe).parent)

    current_path = os.environ.get("PATH", "")
    parts = current_path.split(os.pathsep) if current_path else []
    if ffmpeg_dir not in parts:
        os.environ["PATH"] = ffmpeg_dir + (os.pathsep + current_path if current_path else "")

    # Some libraries consult explicit env vars before PATH.
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
    os.environ["FFMPEG_BINARY"] = ffmpeg_exe


class AudioTranscriber:
    def __init__(self, model_name: str = "openai/whisper-small", device: str = "auto") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None

    def _resolve_device(self) -> int | str:
        if self.device == "auto":
            if torch.cuda.is_available():
                return 0
            return -1
        if self.device in {"cpu", "-1"}:
            return -1
        if self.device == "cuda":
            return 0
        if self.device.isdigit():
            return int(self.device)
        return self.device

    def _get_model(self):
        if self._model is None:
            _ensure_ffmpeg_on_path()
            self._model = pipeline(
                task="automatic-speech-recognition",
                model=self.model_name,
                device=self._resolve_device(),
            )
        return self._model

    @staticmethod
    def _load_wav_audio(file_path: str) -> tuple[np.ndarray, int]:
        with wave.open(file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sample_width == 1:
            audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            audio = (audio - 128.0) / 128.0
        elif sample_width == 2:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 4:
            audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        return audio.astype(np.float32), int(sample_rate)

    @staticmethod
    def _resample_audio(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
        if src_rate == dst_rate:
            return audio
        if audio.size == 0:
            return audio

        src_duration = audio.shape[0] / float(src_rate)
        target_length = max(1, int(round(src_duration * dst_rate)))
        src_idx = np.linspace(0.0, audio.shape[0] - 1, num=audio.shape[0], dtype=np.float64)
        dst_idx = np.linspace(0.0, audio.shape[0] - 1, num=target_length, dtype=np.float64)
        resampled = np.interp(dst_idx, src_idx, audio.astype(np.float64))
        return resampled.astype(np.float32)

    def transcribe_audio(self, file_path: str) -> TranscriptionResponse:
        model = self._get_model()
        suffix = Path(file_path).suffix.lower()

        if suffix == ".wav":
            audio_array, sample_rate = self._load_wav_audio(file_path)
            target_rate = 16000
            if sample_rate != target_rate:
                audio_array = self._resample_audio(audio_array, sample_rate, target_rate)
                sample_rate = target_rate
            model_input: Any = {"array": audio_array, "sampling_rate": sample_rate}
        else:
            # mp3 path still uses ffmpeg-backed decoding.
            _ensure_ffmpeg_on_path()
            model_input = file_path

        result: dict[str, Any] = model(
            model_input,
            return_timestamps=True,
            generate_kwargs={"task": "transcribe"},
        )

        segments = [
            TranscriptSegment(
                start=float(seg.get("timestamp", (0.0, 0.0))[0] or 0.0),
                end=float(seg.get("timestamp", (0.0, 0.0))[1] or 0.0),
                text=str(seg.get("text", "")).strip(),
            )
            for seg in result.get("chunks", [])
        ]
        duration = segments[-1].end if segments else 0.0

        return TranscriptionResponse(
            text=str(result.get("text", "")).strip(),
            language="unknown",
            duration_seconds=duration,
            segments=segments,
            confidence_score=0.9,
        )


def setup_whisper(model_name: str = "openai/whisper-small", device: str = "auto") -> None:
    _ensure_ffmpeg_on_path()

    if device == "auto":
        resolved_device = 0 if torch.cuda.is_available() else -1
    elif device in {"cpu", "-1"}:
        resolved_device = -1
    elif device == "cuda":
        resolved_device = 0
    elif device.isdigit():
        resolved_device = int(device)
    else:
        resolved_device = device

    pipeline(
        task="automatic-speech-recognition",
        model=model_name,
        device=resolved_device,
    )
