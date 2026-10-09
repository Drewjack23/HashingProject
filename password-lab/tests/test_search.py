"""Tests for the exhaustive search experiment."""

from password_lab import candidates, search


def test_crack_one_finds_first_candidate_fast():
    r = search.crack_one("abcd", 3, "aaa", max_seconds=5.0)
    assert r.found is True
    assert r.completed is True
    assert r.guesses_attempted == 1
    assert r.target_rank == 1


def test_crack_one_guesses_equal_rank_when_found():
    alphabet = "abcd"
    target = "bcd"
    expected_rank = candidates.candidate_rank(alphabet, target)
    r = search.crack_one(alphabet, 3, target, max_seconds=5.0)
    assert r.found is True
    assert r.guesses_attempted == expected_rank
    assert r.target_rank == expected_rank


def test_timeout_is_not_reported_as_crack():
    # A large-ish space with essentially zero budget: must not claim success.
    r = search.crack_one("abcd", 8, "dddd" + "dddd", max_seconds=0.0)
    assert r.completed is False
    assert r.found is False


def test_total_candidates_recorded():
    r = search.crack_one("abcd", 4, "aaaa", max_seconds=5.0)
    assert r.total_candidates == 4 ** 4


def test_run_length_experiment_shapes():
    alphabet = "abcd"
    lengths = [3, 4]
    targets = {
        3: candidates.generate_targets(alphabet, 3, 4, seed=1),
        4: candidates.generate_targets(alphabet, 4, 4, seed=2),
    }
    results = search.run_length_experiment(alphabet, lengths, targets, max_seconds=5.0)
    assert len(results) == 8
    assert all(r.found for r in results)  # toy space, all should be found quickly


def test_measured_rate_positive_or_none():
    alphabet = "abcd"
    targets = {4: candidates.generate_targets(alphabet, 4, 6, seed=3)}
    results = search.run_length_experiment(alphabet, [4], targets, max_seconds=5.0)
    rate = search.measured_guesses_per_second(results)
    assert rate is None or rate > 0
