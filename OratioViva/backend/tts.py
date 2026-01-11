from __future__ import annotations

import io
import math
import struct
import uuid
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from huggingface_hub import InferenceClient


@dataclass(frozen=True)
class VoicePreset:
    id: str
    model: str
    label: str
    language: str
    voice: Optional[str] = None
    description: Optional[str] = None


VOICE_PRESETS = [
    VoicePreset(
        id="kokoro_en_us_0",
        model="hexgrad/Kokoro-82M",
        language="en",
        label="Kokoro US Neutral",
        description="Rapide, clair, anglais US",
    ),
    VoicePreset(
        id="kokoro_en_gb_0",
        model="hexgrad/Kokoro-82M",
        language="en",
        label="Kokoro UK Bright",
        description="Anglais UK, ton clair",
    ),
    VoicePreset(
        id="kokoro_fr_0",
        model="hexgrad/Kokoro-82M",
        language="fr",
        label="Kokoro Français Clair",
        description="Français, neutralité",
    ),
    VoicePreset(
        id="parler_en_neutral",
        model="parler-tts/parler-tts-mini-v1.1",
        language="en",
        label="Parler Neutral",
        description="Parler-TTS avec prompt de style",
    ),
]

VOICE_BY_ID: Dict[str, VoicePreset] = {voice.id: voice for voice in VOICE_PRESETS}


@dataclass
class AudioResult:
    job_id: str
    audio_path: Path
    audio_url: str
    duration_seconds: float
    created_at: datetime
    model: str
    voice_id: str
    source: str  # "inference" or "stub"


class TTSService:
    def __init__(
        self,
        audio_dir: Path,
        base_audio_url: str = "/audio",
        hf_token: Optional[str] = None,
        use_stub: bool = False,
        fallback_stub: bool = True,
    ) -> None:
        self.audio_dir = audio_dir
        self.base_audio_url = base_audio_url.rstrip("/")
        self.hf_token = hf_token
        self.use_stub = use_stub
        self.fallback_stub = fallback_stub
        self._clients: Dict[str, InferenceClient] = {}
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def list_voices(self):
        return [voice.__dict__ for voice in VOICE_PRESETS]

    def synthesize(
        self,
        *,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        style: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> AudioResult:
        if voice_id not in VOICE_BY_ID:
            raise ValueError(f"Unknown voice_id: {voice_id}")

        job_id = job_id or str(uuid.uuid4())
        destination = self.audio_dir / f"{job_id}.wav"
        voice = VOICE_BY_ID[voice_id]
        created_at = datetime.now(timezone.utc)

        if self.use_stub:
            duration = self._generate_stub_audio(text, destination, speed=speed)
            return AudioResult(
                job_id=job_id,
                audio_path=destination,
                audio_url=f"{self.base_audio_url}/{destination.name}",
                duration_seconds=duration,
                created_at=created_at,
                model=voice.model,
                voice_id=voice_id,
                source="stub",
            )

        try:
            client = self._get_client(voice.model)
            # Only pass voice/style if provided to avoid model-specific errors.
            kwargs = {}
            if voice.voice:
                kwargs["voice"] = voice.voice
            if style:
                kwargs["style"] = style

            audio_bytes = client.text_to_speech(text, model=voice.model, **kwargs)
            duration = self._write_wav_bytes(audio_bytes, destination, speed=speed)
            return AudioResult(
                job_id=job_id,
                audio_path=destination,
                audio_url=f"{self.base_audio_url}/{destination.name}",
                duration_seconds=duration,
                created_at=created_at,
                model=voice.model,
                voice_id=voice_id,
                source="inference",
            )
        except Exception:
            if not self.fallback_stub:
                raise
            duration = self._generate_stub_audio(text, destination, speed=speed)
            return AudioResult(
                job_id=job_id,
                audio_path=destination,
                audio_url=f"{self.base_audio_url}/{destination.name}",
                duration_seconds=duration,
                created_at=created_at,
                model=voice.model,
                voice_id=voice_id,
                source="stub",
            )

    def _get_client(self, model: str) -> InferenceClient:
        if model not in self._clients:
            self._clients[model] = InferenceClient(model=model, token=self.hf_token)
        return self._clients[model]

    def _write_wav_bytes(self, audio_bytes: bytes, destination: Path, speed: float) -> float:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_in:
            params = wav_in.getparams()
            frames = wav_in.readframes(params.nframes)

        sample_rate = int(params.framerate * speed)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(destination), "wb") as wav_out:
            wav_out.setnchannels(params.nchannels)
            wav_out.setsampwidth(params.sampwidth)
            wav_out.setframerate(sample_rate)
            wav_out.writeframes(frames)

        duration = len(frames) / (params.sampwidth * params.nchannels * sample_rate)
        return duration

    def _generate_stub_audio(self, text: str, destination: Path, speed: float = 1.0) -> float:
        sample_rate = 24_000
        base_duration = max(1.0, min(5.0, len(text) / 20.0))
        duration = base_duration / speed
        frequency = 440.0
        amplitude = 0.2

        destination.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(destination), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            frame_count = int(sample_rate * duration)
            for i in range(frame_count):
                value = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav_file.writeframes(struct.pack("<h", value))

        return duration
