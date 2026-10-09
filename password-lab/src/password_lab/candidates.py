"""Candidate generation and enumeration.

This module defines two things that the rest of the project relies on:

1.  A *consistent* enumeration order over a fixed alphabet and length. The
    order is plain lexicographic order over the alphabet (odometer style,
    last character changes fastest). Every experiment that "guesses" passwords
    walks candidates in exactly this order, so a target's rank is fully
    determined by the alphabet and the password itself.

2.  A seeded generator for synthetic targets. Given a seed we can reproduce the
    exact same set of target passwords on any machine.

Nothing here touches the network or any real credential. All passwords are
drawn from a small, explicit alphabet.
"""

from __future__ import annotations

import itertools
import random
from typing import Iterator, List


def search_space(alphabet_size: int, length: int) -> int:
    """Total number of candidates of a fixed length over an alphabet.

    This is simply alphabet_size ** length. It assumes every position can hold
    any symbol independently (no structure, no restrictions).
    """
    if alphabet_size < 0 or length < 0:
        raise ValueError("alphabet_size and length must be non-negative")
    return alphabet_size ** length


def enumerate_candidates(alphabet: str, length: int) -> Iterator[str]:
    """Yield every candidate of the given length in lexicographic order.

    The order matches itertools.product over the alphabet, which is an
    "odometer": the rightmost character advances fastest. This is the single
    canonical order used by the whole project.
    """
    if length < 0:
        raise ValueError("length must be non-negative")
    for tup in itertools.product(alphabet, repeat=length):
        yield "".join(tup)


def candidate_rank(alphabet: str, password: str) -> int:
    """Return the 1-based position of `password` in the enumeration order.

    Rank 1 means it is the very first candidate tried. The returned value is
    the number of guesses an exhaustive search needs to reach this password
    (inclusive), assuming the search walks `enumerate_candidates` from the top.

    Raises ValueError if the password contains a symbol outside the alphabet.
    """
    index = {ch: i for i, ch in enumerate(alphabet)}
    base = len(alphabet)
    rank0 = 0
    for ch in password:
        if ch not in index:
            raise ValueError(f"character {ch!r} is not in the alphabet")
        rank0 = rank0 * base + index[ch]
    # rank0 is the 0-based position; convert to a 1-based guess count.
    return rank0 + 1


def generate_targets(alphabet: str, length: int, count: int, seed: int) -> List[str]:
    """Generate `count` synthetic target passwords of a fixed length.

    Targets are drawn uniformly at random from the alphabet using a seeded
    PRNG, so the same seed always yields the same targets. Targets are unique
    within the returned list when the search space allows it; if `count`
    exceeds the search space we raise, because you cannot pick that many
    distinct passwords.
    """
    space = search_space(len(alphabet), length)
    if count > space:
        raise ValueError(
            f"requested {count} unique targets but only {space} candidates exist"
        )
    rng = random.Random(seed)
    seen = set()
    targets: List[str] = []
    while len(targets) < count:
        pw = "".join(rng.choice(alphabet) for _ in range(length))
        if pw in seen:
            continue
        seen.add(pw)
        targets.append(pw)
    return targets
