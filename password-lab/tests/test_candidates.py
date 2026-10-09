"""Tests for search-space math and candidate enumeration."""

from password_lab import candidates


def test_search_space_basic():
    assert candidates.search_space(4, 4) == 256
    assert candidates.search_space(4, 6) == 4096
    assert candidates.search_space(4, 8) == 65536
    assert candidates.search_space(26, 0) == 1  # one empty string
    assert candidates.search_space(10, 1) == 10


def test_enumeration_order_is_lexicographic_odometer():
    got = list(candidates.enumerate_candidates("ab", 2))
    assert got == ["aa", "ab", "ba", "bb"]


def test_enumeration_count_matches_search_space():
    alphabet = "abcd"
    for n in (1, 2, 3):
        count = sum(1 for _ in candidates.enumerate_candidates(alphabet, n))
        assert count == candidates.search_space(len(alphabet), n)


def test_candidate_rank_matches_enumeration_position():
    alphabet = "abcd"
    enum = list(candidates.enumerate_candidates(alphabet, 3))
    for i, pw in enumerate(enum):
        assert candidates.candidate_rank(alphabet, pw) == i + 1


def test_candidate_rank_first_and_last():
    alphabet = "abcd"
    assert candidates.candidate_rank(alphabet, "aaaa") == 1
    assert candidates.candidate_rank(alphabet, "dddd") == candidates.search_space(4, 4)


def test_candidate_rank_rejects_foreign_char():
    try:
        candidates.candidate_rank("abcd", "e")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for char outside alphabet")


def test_generate_targets_reproducible():
    a = candidates.generate_targets("abcd", 4, 10, seed=99)
    b = candidates.generate_targets("abcd", 4, 10, seed=99)
    assert a == b
    assert len(a) == 10
    assert len(set(a)) == 10  # unique
    assert all(len(t) == 4 for t in a)
    assert all(ch in "abcd" for t in a for ch in t)


def test_generate_targets_too_many_raises():
    try:
        candidates.generate_targets("ab", 2, 5, seed=1)  # only 4 possible
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError when count exceeds search space")
