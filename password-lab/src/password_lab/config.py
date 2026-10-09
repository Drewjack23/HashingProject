"""Configuration object shared by every experiment.

Conservative defaults are chosen so the bounded demo finishes quickly on a
laptop. The CLI (see cli.py) exposes every field as a flag.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class Config:
    # --- reproducibility ---
    seed: int = 1234

    # --- experiment 1: exhaustive search ---
    # Deliberately tiny "toy" alphabet so that length 8 is still tractable.
    alphabet: str = "abcd"
    lengths: List[int] = field(default_factory=lambda: [4, 6, 8])
    targets_per_length: int = 10

    # --- experiment 2: hashing cost ---
    # Low cost factors keep the demo fast but are clearly labeled as such.
    bcrypt_rounds: int = 8          # log2 cost; real deployments use 12+.
    argon2_time_cost: int = 2       # iterations
    argon2_memory_kib: int = 65536  # 64 MiB
    argon2_parallelism: int = 1
    argon2_hash_len: int = 32
    salt_length_bytes: int = 16
    hash_warmup: int = 3
    hash_batches: int = 5
    hash_verifications_per_batch: int = 20

    # --- experiment 3: dictionary / predictability (defined in dictionary.py) ---

    # --- estimates ---
    estimate_alphabets: List[int] = field(default_factory=lambda: [26, 62, 95])
    estimate_lengths: List[int] = field(default_factory=lambda: [4, 6, 8, 10, 12])

    # --- runtime budget ---
    # Maximum wall-clock seconds any single exhaustive search may run before it
    # is marked incomplete. A timed-out search is NEVER reported as a crack.
    max_seconds_per_search: float = 10.0

    # --- output ---
    output_dir: str = "results"

    def as_dict(self) -> Dict:
        return asdict(self)
