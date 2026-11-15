"""8-bit chiptune synthesizer and non-blocking audio player for A-Maze-ing."""

from __future__ import annotations

import math
import queue
import shutil
import struct
import subprocess
import threading
from typing import List, Optional, Sequence, Tuple

SAMPLE_RATE = 22050

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
    """Return a streaming raw PCM CLI player command if available."""
    paplay = shutil.which("paplay")
    if paplay is not None:
        return [
            paplay,
            "--raw",
            f"--rate={SAMPLE_RATE}",
            "--channels=1",
            "--format=s16le",
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


class ChiptunePlayer:
    """Non-blocking background 8-bit sound engine for animation events."""

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the audio queue and background playback thread."""
        self._cmd = _find_player_cmd() if enabled else None
        self.available = self._cmd is not None
        self.muted = not self.available
        self._closed = False
        self._queue: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=6)
        self._proc: Optional[subprocess.Popen[bytes]] = None
        self._thread: Optional[threading.Thread] = None

        if self.available:
            self._thread = threading.Thread(
                target=self._worker,
                name="mazegen-8bit-audio",
                daemon=True,
            )
            self._thread.start()

    def _enqueue(self, data: bytes, priority: bool = False) -> None:
        """Push PCM audio to the playback queue without blocking the UI."""
        if self._closed or self.muted or not self.available:
            return
        if priority:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
        try:
            self._queue.put_nowait(data)
        except queue.Full:
            pass

    def _open_stream(self) -> Optional[subprocess.Popen[bytes]]:
        """Spawn the streaming audio subprocess."""
        if self._cmd is None:
            return None
        try:
            return subprocess.Popen(
                self._cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            self.available = False
            self.muted = True
            return None

    def _worker(self) -> None:
        """Drain queued PCM chunks into the audio player's stdin."""
        proc = self._open_stream()
        self._proc = proc
        if proc is None or proc.stdin is None:
            return
        try:
            while not self._closed:
                chunk = self._queue.get()
                if chunk is None:
                    break
                if proc.poll() is not None:
                    break
                try:
                    proc.stdin.write(chunk)
                    proc.stdin.flush()
                except OSError:
                    break
        finally:
            self._terminate_proc(proc)

    @staticmethod
    def _terminate_proc(proc: subprocess.Popen[bytes]) -> None:
        """Close stdin and terminate the audio player subprocess cleanly."""
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except OSError:
            pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def toggle_mute(self) -> bool:
        """Toggle mute state and return the new muted boolean."""
        if not self.available:
            return True
        self.muted = not self.muted
        if not self.muted:
            self.play_ui_click()
        return self.muted

    def play_carve(
        self,
        progress: float,
        cell: Tuple[int, int],
        backtrack: bool = False,
    ) -> None:
        """Play a short 8-bit blip reacting to maze carving."""
        base_idx = (cell[0] * 3 + cell[1] * 5) % 8
        lift = int(max(0.0, min(1.0, progress)) * 4)
        idx = min(len(PENTATONIC_HZ) - 1, base_idx + lift)
        if backtrack:
            freq = PENTATONIC_HZ[max(0, idx - 3)] * 0.75
            tone = synthesize_tone(
                freq, 0.032, wave="triangle", volume=0.14
            )
        else:
            freq = PENTATONIC_HZ[idx]
            tone = synthesize_tone(
                freq, 0.030, wave="square25", volume=0.15
            )
        self._enqueue(tone)

    def play_solve(self, progress: float) -> None:
        """Play a rising 8-bit radar pulse as BFS approaches the exit."""
        clamped = max(0.0, min(1.0, progress))
        idx = min(
            len(PENTATONIC_HZ) - 1,
            int(clamped * (len(PENTATONIC_HZ) - 1)),
        )
        freq = PENTATONIC_HZ[idx]
        tone = synthesize_tone(
            freq,
            0.038,
            wave="triangle",
            volume=0.18,
            end_freq=freq * (1.0 + 0.08 * math.sin(clamped * math.pi)),
        )
        self._enqueue(tone)

    def play_trace(self, progress: float) -> None:
        """Play an ascending lock-in note as the shortest path is drawn."""
        clamped = max(0.0, min(1.0, progress))
        idx = min(
            len(PENTATONIC_HZ) - 1,
            3 + int(clamped * (len(PENTATONIC_HZ) - 4)),
        )
        tone = synthesize_tone(
            PENTATONIC_HZ[idx], 0.035, wave="square", volume=0.18
        )
        self._enqueue(tone)

    def play_victory(self) -> None:
        """Play the 8-bit victory fanfare when the exit is reached."""
        self._enqueue(synthesize_victory_fanfare(), priority=True)

    def play_ui_click(self) -> None:
        """Play a crisp 8-bit UI confirmation chirp."""
        tone = synthesize_tone(
            659.25, 0.025, wave="square25", volume=0.16, end_freq=880.0
        )
        self._enqueue(tone, priority=True)

    def close(self) -> None:
        """Shut down the background audio thread and player process."""
        if self._closed:
            return
        self._closed = True
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread is not None:
            self._thread.join(timeout=0.5)
