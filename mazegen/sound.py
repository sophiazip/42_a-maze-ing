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
