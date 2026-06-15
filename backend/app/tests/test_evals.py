"""V2.4: unit tests for the eval/calibration harness metric math.

The whole "is the critic trustworthy?" conclusion rests on these pure functions,
so they must be correct. No API key or model calls — just the math + validators.
"""

import pytest

from evals.run_eval import (
    _fractional_ranks,
    _passes_thresholds,
    _pearson,
    _predict_better,
    _spearman,
    _validate_items,
    _validate_pairs,
)


class TestPredictBetter:
    def test_a_wins(self):
        assert _predict_better(8.0, 5.0) == "a"

    def test_b_wins(self):
        assert _predict_better(5.0, 8.0) == "b"

    def test_tie(self):
        assert _predict_better(7.0, 7.0) == "tie"


class TestFractionalRanks:
    def test_strict_order(self):
        assert _fractional_ranks([10, 20, 30]) == [1.0, 2.0, 3.0]

    def test_unsorted_input(self):
        assert _fractional_ranks([30, 10, 20]) == [3.0, 1.0, 2.0]

    def test_ties_get_average_rank(self):
        assert _fractional_ranks([10, 10, 20]) == [1.5, 1.5, 3.0]

    def test_all_equal(self):
        assert _fractional_ranks([5, 5, 5]) == [2.0, 2.0, 2.0]


class TestSpearman:
    def test_perfect_positive(self):
        assert _spearman([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)

    def test_perfect_negative(self):
        assert _spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)

    def test_monotonic_nonlinear_is_one(self):
        # Spearman captures rank, so nonlinear-but-monotonic → 1.0
        assert _spearman([1, 2, 3, 4], [1, 4, 9, 16]) == pytest.approx(1.0)

    def test_too_few_points_returns_none(self):
        assert _spearman([1], [1]) is None

    def test_zero_variance_returns_none(self):
        assert _spearman([5, 5, 5], [1, 2, 3]) is None


class TestPearson:
    def test_perfect_correlation(self):
        assert _pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)


class TestThresholdGate:
    def test_both_above_passes(self):
        assert _passes_thresholds(0.8, 0.6) is True

    def test_at_threshold_passes(self):
        assert _passes_thresholds(0.75, 0.5) is True

    def test_low_win_rate_fails(self):
        assert _passes_thresholds(0.7, 0.6) is False

    def test_low_spearman_fails(self):
        assert _passes_thresholds(0.8, 0.4) is False

    def test_unmeasured_metrics_pass(self):
        # None = not measured (no data / no key) — does not fail the gate.
        assert _passes_thresholds(None, None) is True
        assert _passes_thresholds(None, 0.6) is True


class TestGoldValidators:
    def test_valid_items_pass(self):
        items = [{"id": "x", "label": "high", "work_description": "a real desc"}]
        assert _validate_items(items) == []

    def test_bad_label_flagged(self):
        items = [{"id": "x", "label": "great", "work_description": "d"}]
        assert len(_validate_items(items)) == 1

    def test_empty_description_flagged(self):
        items = [{"id": "x", "label": "low", "work_description": "  "}]
        assert len(_validate_items(items)) == 1

    def test_valid_pairs_pass(self):
        pairs = [{"id": "p", "better": "a", "a": "desc a", "b": "desc b"}]
        assert _validate_pairs(pairs) == []

    def test_bad_better_flagged(self):
        pairs = [{"id": "p", "better": "c", "a": "x", "b": "y"}]
        assert len(_validate_pairs(pairs)) == 1

    def test_empty_side_flagged(self):
        pairs = [{"id": "p", "better": "a", "a": "", "b": "y"}]
        assert len(_validate_pairs(pairs)) == 1
