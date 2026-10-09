"""Tests for the projection / estimate formulas."""

import math

import pytest

from password_lab import estimates


def test_search_space():
    assert estimates.search_space(26, 4) == 26 ** 4
    assert estimates.search_space(95, 8) == 95 ** 8


def test_expected_guesses_half_the_space():
    assert estimates.expected_guesses(256) == (256 + 1) / 2
    assert estimates.expected_guesses(1) == 1.0


def test_worst_case_is_full_space():
    assert estimates.worst_case_guesses(256) == 256


def test_estimate_time_divides_by_rate():
    assert estimates.estimate_time_seconds(1000, 500) == 2.0


def test_estimate_time_rejects_nonpositive_rate():
    with pytest.raises(ValueError):
        estimates.estimate_time_seconds(10, 0)
    with pytest.raises(ValueError):
        estimates.estimate_time_seconds(10, -5)


def test_build_estimate_consistency():
    e = estimates.build_estimate(26, 8, guesses_per_second=1_000_000)
    assert e.search_space == 26 ** 8
    assert e.expected_guesses == (26 ** 8 + 1) / 2
    assert e.worst_case_guesses == 26 ** 8
    # expected time == expected guesses / rate
    assert math.isclose(e.expected_seconds, e.expected_guesses / 1_000_000)
    # worst case is always >= expected
    assert e.worst_case_seconds >= e.expected_seconds


def test_build_grid_covers_cross_product():
    grid = estimates.build_estimate_grid([26, 62], [4, 6, 8], 1000.0)
    assert len(grid) == 2 * 3
    pairs = {(e.alphabet_size, e.password_length) for e in grid}
    assert pairs == {(26, 4), (26, 6), (26, 8), (62, 4), (62, 6), (62, 8)}


def test_two_extra_characters_multiply():
    # Core claim of the whole project: +2 chars multiplies by alphabet^2.
    rate = 1e6
    e6 = estimates.build_estimate(26, 6, rate)
    e8 = estimates.build_estimate(26, 8, rate)
    assert e8.search_space == e6.search_space * (26 ** 2)


def test_humanize_seconds_ranges():
    assert "ms" in estimates.humanize_seconds(0.5)
    assert "seconds" in estimates.humanize_seconds(10)
    assert "minutes" in estimates.humanize_seconds(120)
    assert "years" in estimates.humanize_seconds(86400 * 365.25 * 5)
