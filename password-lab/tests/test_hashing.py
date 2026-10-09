"""Tests for hashing verification behavior and the benchmark harness.

These use very cheap cost parameters so the suite stays fast.
"""

from password_lab import hashing


def test_sha256_benchmark_runs_and_verifies():
    r = hashing.benchmark_sha256("hunter2", salt_length_bytes=16,
                                 warmup=1, batches=2, per_batch=5)
    assert r.algorithm == "sha256"
    assert r.median_throughput > 0
    assert len(r.batch_throughputs) == 2
    assert r.verifications_timed == 10


def test_bcrypt_verifies_correct_and_wrong():
    import bcrypt

    stored = bcrypt.hashpw(b"hunter2", bcrypt.gensalt(rounds=4))
    assert bcrypt.checkpw(b"hunter2", stored) is True
    assert bcrypt.checkpw(b"wrongpw", stored) is False


def test_bcrypt_benchmark_cheap():
    r = hashing.benchmark_bcrypt("hunter2", rounds=4,
                                 warmup=1, batches=2, per_batch=3)
    assert r.algorithm == "bcrypt"
    assert r.params["log2_rounds"] == 4
    assert r.params["cost_factor"] == 16
    assert r.median_throughput > 0


def test_argon2_verifies_correct_and_wrong():
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    ph = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1,
                        hash_len=16, salt_len=8)
    stored = ph.hash("hunter2")
    assert ph.verify(stored, "hunter2") is True
    try:
        ph.verify(stored, "wrongpw")
    except VerifyMismatchError:
        pass
    else:
        raise AssertionError("argon2 should reject a wrong password")


def test_argon2_benchmark_cheap():
    r = hashing.benchmark_argon2("hunter2", time_cost=1, memory_kib=8,
                                 parallelism=1, hash_len=16, salt_length_bytes=8,
                                 warmup=1, batches=2, per_batch=2)
    assert r.algorithm == "argon2id"
    assert r.params["time_cost"] == 1
    assert r.median_throughput > 0


def test_slow_hashes_are_slower_than_sha256():
    # Core claim: a slow hash yields far lower verification throughput.
    sha = hashing.benchmark_sha256("hunter2", 16, warmup=1, batches=2, per_batch=50)
    bc = hashing.benchmark_bcrypt("hunter2", rounds=6, warmup=1, batches=2, per_batch=3)
    assert sha.median_throughput > bc.median_throughput
