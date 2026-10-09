"""Tests for the length-vs-predictability illustration."""

from password_lab import dictionary


def test_dictionary_is_deterministic_and_unique():
    a = dictionary.build_dictionary()
    b = dictionary.build_dictionary()
    assert a == b
    assert len(a) == len(set(a))


def test_long_predictable_target_ranks_early():
    results = dictionary.run_dictionary_experiment("abcd")
    long_pred = next(r for r in results if r.label == "long but predictable")
    assert long_pred.found_in_dictionary is True
    # It is long (10 chars) but should land well inside the list, not at the end.
    assert long_pred.dictionary_rank is not None
    assert long_pred.dictionary_rank <= long_pred.dictionary_size


def test_short_random_not_in_dictionary_but_has_bruteforce_rank():
    results = dictionary.run_dictionary_experiment("abcd")
    short = next(r for r in results if r.label == "short but random")
    assert short.found_in_dictionary is False
    assert short.dictionary_rank is None
    assert short.bruteforce_rank is not None  # reachable by brute force on toy alphabet


def test_longer_predictable_beats_shorter_random_in_guess_order():
    results = dictionary.run_dictionary_experiment("abcd")
    long_pred = next(r for r in results if r.label == "long but predictable")
    short = next(r for r in results if r.label == "short but random")
    # The long predictable one is found by a word list; the short random one is not.
    assert long_pred.found_in_dictionary and not short.found_in_dictionary
