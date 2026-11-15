"""Unit tests for the 8-bit chiptune synthesizer and player."""

from __future__ import annotations

import unittest

from mazegen.sound import (
    ChiptunePlayer,
    SAMPLE_RATE,
    synthesize_tone,
    synthesize_victory_fanfare,
)


class TestSound(unittest.TestCase):
    """Verify PCM synthesis and safe headless ChiptunePlayer lifecycle."""

    def test_synthesize_tone_produces_16bit_pcm(self) -> None:
        """Synthesized tone length matches sample rate and duration."""
        for wave in ("square", "square25", "triangle"):
            pcm = synthesize_tone(440.0, 0.05, wave=wave, end_freq=880.0)
            expected_bytes = int(SAMPLE_RATE * 0.05) * 2
            self.assertEqual(len(pcm), expected_bytes)
            self.assertTrue(any(b != 0 for b in pcm))

    def test_victory_fanfare_non_empty(self) -> None:
        """Victory fanfare generates multi-note PCM data."""
        fanfare = synthesize_victory_fanfare()
        self.assertGreater(len(fanfare), SAMPLE_RATE // 2)

    def test_disabled_player_is_safe(self) -> None:
        """Disabled ChiptunePlayer ignores events and closes cleanly."""
        player = ChiptunePlayer(enabled=False)
        self.assertFalse(player.available)
        self.assertTrue(player.muted)
        player.play_carve(0.5, (2, 3), backtrack=False)
        player.play_solve(0.8)
        player.play_trace(0.9)
        player.play_victory()
        player.play_ui_click()
        self.assertTrue(player.toggle_mute())
        player.close()


if __name__ == "__main__":
    unittest.main()
