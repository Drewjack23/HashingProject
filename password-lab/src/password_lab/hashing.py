"""Experiment 2: hashing algorithm cost.

We compare how expensive it is to *verify* one candidate against a stored hash
for three constructions:

  * SHA-256  -- a fast general-purpose hash, used here only as an experimental
                baseline. It is NOT a recommended password-storage scheme.
                We use an explicit salted construction: SHA-256(salt || password).
  * bcrypt   -- a deliberately slow password hashing function with a cost factor.
  * Argon2id -- a memory-hard password hashing function with time, memory, and
                parallelism parameters.

The thing we measure is verification throughput: given a stored hash, how many
candidate checks per second can a single CPU worker do? That is the quantity an
attacker running a dictionary/brute-force attack actually cares about, and it is
also what a login server pays per attempt.

Important honesty notes baked into the design:

  * Hash *creation* is timed separately from *verification*.
  * Each algorithm verifies the SAME workload: one correct password repeated,
    checked against that algorithm's own stored hash with that algorithm's own
    verification API. We do not give different algorithms different work.
  * The verification APIs differ in what they do internally. bcrypt.checkpw and
    argon2's verify re-derive the hash from the candidate and compare; our
    SHA-256 baseline recomputes SHA-256(salt || candidate) and compares. All
    three therefore measure "cost of one verification attempt," which is the
    comparable quantity, but the SHA-256 number is best read as a floor.
  * Warm-up iterations run before timing. Multiple timed batches are collected
    so we can report median throughput and variability.
  * Everything is single-process, single-worker on purpose, so the numbers are
    a clean per-core baseline rather than a machine-maximum.
"""

from __future__ import annotations

import hashlib
import os
import statistics
import time
from dataclasses import dataclass, asdict, field
from typing import Callable, Dict, List

import bcrypt
from argon2 import PasswordHasher

try:
    from importlib.metadata import version as _pkg_version

    argon2_version = _pkg_version("argon2-cffi")
except Exception:  # pragma: no cover - defensive
    argon2_version = "unknown"


@dataclass
class AlgoResult:
    algorithm: str
    label: str
    params: Dict[str, object]
    salt_length_bytes: int
    hash_creation_seconds: float
    verifications_timed: int
    batch_throughputs: List[float] = field(default_factory=list)  # verifications/sec
    median_throughput: float = 0.0
    stdev_throughput: float = 0.0
    min_throughput: float = 0.0
    max_throughput: float = 0.0

    def as_dict(self) -> Dict:
        return asdict(self)


def _time_verifications(verify: Callable[[], None], count: int) -> float:
    """Run `verify` `count` times and return elapsed monotonic seconds."""
    start = time.monotonic()
    for _ in range(count):
        verify()
    return time.monotonic() - start


def _summarize(result: AlgoResult) -> AlgoResult:
    tp = result.batch_throughputs
    result.median_throughput = statistics.median(tp) if tp else 0.0
    result.stdev_throughput = statistics.pstdev(tp) if len(tp) > 1 else 0.0
    result.min_throughput = min(tp) if tp else 0.0
    result.max_throughput = max(tp) if tp else 0.0
    return result


def _benchmark(
    algorithm: str,
    label: str,
    params: Dict[str, object],
    salt_length_bytes: int,
    make_hash: Callable[[], object],
    make_verifier: Callable[[object], Callable[[], None]],
    warmup: int,
    batches: int,
    per_batch: int,
) -> AlgoResult:
    """Shared benchmark harness for one algorithm.

    `make_hash` creates and returns the stored hash (timed as creation).
    `make_verifier` turns that stored hash into a zero-arg callable that
    verifies the known-correct password once.
    """
    t0 = time.monotonic()
    stored = make_hash()
    creation = time.monotonic() - t0

    verify = make_verifier(stored)

    # Warm-up (not timed): lets caches / branch predictors settle.
    for _ in range(warmup):
        verify()

    result = AlgoResult(
        algorithm=algorithm,
        label=label,
        params=params,
        salt_length_bytes=salt_length_bytes,
        hash_creation_seconds=creation,
        verifications_timed=batches * per_batch,
    )
    for _ in range(batches):
        elapsed = _time_verifications(verify, per_batch)
        throughput = per_batch / elapsed if elapsed > 0 else 0.0
        result.batch_throughputs.append(throughput)
    return _summarize(result)


def benchmark_sha256(
    password: str, salt_length_bytes: int, warmup: int, batches: int, per_batch: int
) -> AlgoResult:
    salt = os.urandom(salt_length_bytes)
    pw_bytes = password.encode("utf-8")

    def make_hash():
        return hashlib.sha256(salt + pw_bytes).hexdigest()

    def make_verifier(stored):
        def verify():
            # Recompute salted digest and compare in constant time.
            import hmac

            candidate = hashlib.sha256(salt + pw_bytes).hexdigest()
            hmac.compare_digest(candidate, stored)

        return verify

    return _benchmark(
        algorithm="sha256",
        label="SHA-256 (salted baseline, NOT for password storage)",
        params={"construction": "sha256(salt || password)", "hex_digest": True},
        salt_length_bytes=salt_length_bytes,
        make_hash=make_hash,
        make_verifier=make_verifier,
        warmup=warmup,
        batches=batches,
        per_batch=per_batch,
    )


def benchmark_bcrypt(
    password: str, rounds: int, warmup: int, batches: int, per_batch: int
) -> AlgoResult:
    pw_bytes = password.encode("utf-8")

    def make_hash():
        return bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=rounds))

    def make_verifier(stored):
        def verify():
            bcrypt.checkpw(pw_bytes, stored)

        return verify

    # bcrypt embeds its own salt; its length is fixed by the algorithm (16 bytes).
    return _benchmark(
        algorithm="bcrypt",
        label="bcrypt",
        params={"log2_rounds": rounds, "cost_factor": 2 ** rounds},
        salt_length_bytes=16,
        make_hash=make_hash,
        make_verifier=make_verifier,
        warmup=warmup,
        batches=batches,
        per_batch=per_batch,
    )


def benchmark_argon2(
    password: str,
    time_cost: int,
    memory_kib: int,
    parallelism: int,
    hash_len: int,
    salt_length_bytes: int,
    warmup: int,
    batches: int,
    per_batch: int,
) -> AlgoResult:
    ph = PasswordHasher(
        time_cost=time_cost,
        memory_cost=memory_kib,
        parallelism=parallelism,
        hash_len=hash_len,
        salt_len=salt_length_bytes,
    )

    def make_hash():
        return ph.hash(password)

    def make_verifier(stored):
        def verify():
            try:
                ph.verify(stored, password)
            except Exception:  # pragma: no cover - should not happen for correct pw
                pass

        return verify

    return _benchmark(
        algorithm="argon2id",
        label="Argon2id",
        params={
            "time_cost": time_cost,
            "memory_kib": memory_kib,
            "memory_mib": round(memory_kib / 1024, 2),
            "parallelism": parallelism,
            "hash_len": hash_len,
            "argon2_cffi_version": argon2_version,
        },
        salt_length_bytes=salt_length_bytes,
        make_hash=make_hash,
        make_verifier=make_verifier,
        warmup=warmup,
        batches=batches,
        per_batch=per_batch,
    )


def run_hashing_experiment(cfg, password: str = "correct horse") -> List[AlgoResult]:
    """Run all three algorithm benchmarks with parameters from the config."""
    results = [
        benchmark_sha256(
            password,
            cfg.salt_length_bytes,
            cfg.hash_warmup,
            cfg.hash_batches,
            cfg.hash_verifications_per_batch,
        ),
        benchmark_bcrypt(
            password,
            cfg.bcrypt_rounds,
            cfg.hash_warmup,
            cfg.hash_batches,
            cfg.hash_verifications_per_batch,
        ),
        benchmark_argon2(
            password,
            cfg.argon2_time_cost,
            cfg.argon2_memory_kib,
            cfg.argon2_parallelism,
            cfg.argon2_hash_len,
            cfg.salt_length_bytes,
            cfg.hash_warmup,
            cfg.hash_batches,
            cfg.hash_verifications_per_batch,
        ),
    ]
    return results
