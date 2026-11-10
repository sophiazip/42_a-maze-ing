"""8-bit chiptune synthesizer and low-latency streaming audio engine."""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
import threading
import time
from typing import List, Optional, Sequence, Tuple

SAMPLE_RATE = 22050
FRAME_MS = 20
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000
FRAME_BYTES = FRAME_SAMPLES * 2
SILENCE_FRAME = b"\x00" * FRAME_BYTES

# C major pentatonic across 2.5 octaves: always consonant regardless of order.
PENTATONIC_HZ: Tuple[float, ...] = (
    261.63, 293.66, 329.63, 392.00, 440.00,
    523.25, 587.33, 659.25, 783.99, 880.00,
    1046.50, 1174.66, 1318.51,
)


def _sample_wave(phase: float, wave: str) -> float:
    """Return a normalized [-1.0, 1.0] sample for the requested 8-bit wave."""
    frac = phase % 1.0
    if wave == "square25":
        return 1.0 if frac < 0.25 else -1.0
    if wave == "triangle":
        return 4.0 * abs(frac - 0.5) - 1.0
    return 1.0 if frac < 0.5 else -1.0


def synthesize_tone(
    freq: float,
    duration_s: float,
    wave: str = "square",
    volume: float = 0.20,
    end_freq: Optional[float] = None,
) -> bytes:
    """Synthesize a mono 16-bit signed PCM 8-bit tone with envelope."""
    total_samples = max(1, int(SAMPLE_RATE * duration_s))
    target_freq = freq if end_freq is None else end_freq
    attack = max(1, int(total_samples * 0.06))
    release = max(1, int(total_samples * 0.30))

    pcm = bytearray(total_samples * 2)
    phase = 0.0
    for idx in range(total_samples):
        t = idx / total_samples
        cur_freq = freq + (target_freq - freq) * t
        phase += cur_freq / SAMPLE_RATE

        env = 1.0
        if idx < attack:
            env = idx / attack
        elif idx > total_samples - release:
            env = max(0.0, (total_samples - idx) / release)

        amp = max(-1.0, min(1.0, _sample_wave(phase, wave) * env * volume))
        sample_int = int(amp * 32767)
        struct.pack_into("<h", pcm, idx * 2, sample_int)
    return bytes(pcm)


def synthesize_sequence(
    notes: Sequence[Tuple[float, float, str]],
    volume: float = 0.22,
) -> bytes:
    """Concatenate a sequence of (freq_hz, duration_s, wave) notes."""
    chunks: List[bytes] = [
        synthesize_tone(freq, dur, wave=wave, volume=volume)
        for freq, dur, wave in notes
    ]
    return b"".join(chunks)


def synthesize_victory_fanfare() -> bytes:
    """Build an upbeat 8-bit arpeggio fanfare for reaching the maze exit."""
    notes: Tuple[Tuple[float, float, str], ...] = (
        (523.25, 0.065, "square25"),
        (659.25, 0.065, "square25"),
        (783.99, 0.065, "square25"),
        (1046.50, 0.11, "square"),
        (783.99, 0.065, "square25"),
        (1046.50, 0.24, "square"),
    )
    return synthesize_sequence(notes, volume=0.24)


def _find_player_cmd() -> Optional[List[str]]:
    """Return a low-latency streaming raw PCM CLI player command."""
    paplay = shutil.which("paplay")
    if paplay is not None:
        return [
            paplay,
            "--raw",
            f"--rate={SAMPLE_RATE}",
            "--channels=1",
            "--format=s16le",
            "--latency-msec=40",
            "--process-time-msec=15",
        ]
    pw_play = shutil.which("pw-play")
    if pw_play is not None:
        return [
            pw_play,
            "--raw",
            "--rate",
            str(SAMPLE_RATE),
            "--channels",
            "1",
            "--format",
            "s16",
            "-",
        ]
    return None


