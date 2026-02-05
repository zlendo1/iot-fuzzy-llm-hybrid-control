from __future__ import annotations

import math

import pytest


class TestTriangularMF:
    @pytest.mark.unit
    def test_triangular_at_peak_returns_one(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=5.0, c=10.0)
        assert mf.compute_degree(5.0) == 1.0

    @pytest.mark.unit
    def test_triangular_at_left_foot_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=5.0, c=10.0)
        assert mf.compute_degree(0.0) == 0.0

    @pytest.mark.unit
    def test_triangular_at_right_foot_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=5.0, c=10.0)
        assert mf.compute_degree(10.0) == 0.0

    @pytest.mark.unit
    def test_triangular_rising_edge(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=10.0, c=20.0)
        assert mf.compute_degree(5.0) == 0.5

    @pytest.mark.unit
    def test_triangular_falling_edge(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=10.0, c=20.0)
        assert mf.compute_degree(15.0) == 0.5

    @pytest.mark.unit
    def test_triangular_outside_left_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=5.0, c=10.0)
        assert mf.compute_degree(-5.0) == 0.0

    @pytest.mark.unit
    def test_triangular_outside_right_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=5.0, c=10.0)
        assert mf.compute_degree(15.0) == 0.0

    @pytest.mark.unit
    def test_triangular_invalid_params_raises(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        with pytest.raises(ValueError, match="a <= b <= c required"):
            TriangularMF(a=10.0, b=5.0, c=0.0)

    @pytest.mark.unit
    def test_triangular_function_type(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=5.0, c=10.0)
        assert mf.function_type == "triangular"

    @pytest.mark.unit
    def test_triangular_degenerate_left_peak(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=0.0, c=10.0)
        assert mf.compute_degree(0.0) == 1.0
        assert mf.compute_degree(5.0) == 0.5

    @pytest.mark.unit
    def test_triangular_degenerate_right_peak(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=10.0, c=10.0)
        assert mf.compute_degree(10.0) == 1.0
        assert mf.compute_degree(5.0) == 0.5


class TestTrapezoidalMF:
    @pytest.mark.unit
    def test_trapezoidal_at_plateau_returns_one(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(10.0) == 1.0

    @pytest.mark.unit
    def test_trapezoidal_at_left_shoulder_returns_one(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(5.0) == 1.0

    @pytest.mark.unit
    def test_trapezoidal_at_right_shoulder_returns_one(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(15.0) == 1.0

    @pytest.mark.unit
    def test_trapezoidal_at_left_foot_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(0.0) == 0.0

    @pytest.mark.unit
    def test_trapezoidal_at_right_foot_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(20.0) == 0.0

    @pytest.mark.unit
    def test_trapezoidal_rising_edge(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=10.0, c=20.0, d=30.0)
        assert mf.compute_degree(5.0) == 0.5

    @pytest.mark.unit
    def test_trapezoidal_falling_edge(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=10.0, c=20.0, d=30.0)
        assert mf.compute_degree(25.0) == 0.5

    @pytest.mark.unit
    def test_trapezoidal_outside_left_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(-5.0) == 0.0

    @pytest.mark.unit
    def test_trapezoidal_outside_right_returns_zero(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.compute_degree(25.0) == 0.0

    @pytest.mark.unit
    def test_trapezoidal_invalid_params_raises(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        with pytest.raises(ValueError, match="a <= b <= c <= d required"):
            TrapezoidalMF(a=20.0, b=15.0, c=5.0, d=0.0)

    @pytest.mark.unit
    def test_trapezoidal_function_type(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        assert mf.function_type == "trapezoidal"

    @pytest.mark.unit
    def test_trapezoidal_degenerate_to_triangular(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=10.0, c=10.0, d=20.0)
        assert mf.compute_degree(10.0) == 1.0
        assert mf.compute_degree(5.0) == 0.5
        assert mf.compute_degree(15.0) == 0.5


class TestGaussianMF:
    @pytest.mark.unit
    def test_gaussian_at_mean_returns_one(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        mf = GaussianMF(mean=0.0, sigma=1.0)
        assert mf.compute_degree(0.0) == 1.0

    @pytest.mark.unit
    def test_gaussian_at_one_sigma(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        mf = GaussianMF(mean=0.0, sigma=1.0)
        expected = math.exp(-0.5)
        assert mf.compute_degree(1.0) == pytest.approx(expected)

    @pytest.mark.unit
    def test_gaussian_at_two_sigma(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        mf = GaussianMF(mean=0.0, sigma=1.0)
        expected = math.exp(-2.0)
        assert mf.compute_degree(2.0) == pytest.approx(expected)

    @pytest.mark.unit
    def test_gaussian_symmetric(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        mf = GaussianMF(mean=5.0, sigma=2.0)
        assert mf.compute_degree(3.0) == pytest.approx(mf.compute_degree(7.0))

    @pytest.mark.unit
    def test_gaussian_wider_sigma(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        narrow = GaussianMF(mean=0.0, sigma=1.0)
        wide = GaussianMF(mean=0.0, sigma=3.0)
        assert wide.compute_degree(2.0) > narrow.compute_degree(2.0)

    @pytest.mark.unit
    def test_gaussian_invalid_sigma_raises(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        with pytest.raises(ValueError, match="sigma must be positive"):
            GaussianMF(mean=0.0, sigma=0.0)

    @pytest.mark.unit
    def test_gaussian_negative_sigma_raises(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        with pytest.raises(ValueError, match="sigma must be positive"):
            GaussianMF(mean=0.0, sigma=-1.0)

    @pytest.mark.unit
    def test_gaussian_function_type(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        mf = GaussianMF(mean=0.0, sigma=1.0)
        assert mf.function_type == "gaussian"


class TestSigmoidMF:
    @pytest.mark.unit
    def test_sigmoid_at_inflection_returns_half(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=1.0, c=0.0)
        assert mf.compute_degree(0.0) == pytest.approx(0.5)

    @pytest.mark.unit
    def test_sigmoid_increasing_positive_a(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=1.0, c=0.0)
        assert mf.compute_degree(10.0) > mf.compute_degree(0.0)
        assert mf.compute_degree(-10.0) < mf.compute_degree(0.0)

    @pytest.mark.unit
    def test_sigmoid_decreasing_negative_a(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=-1.0, c=0.0)
        assert mf.compute_degree(10.0) < mf.compute_degree(0.0)
        assert mf.compute_degree(-10.0) > mf.compute_degree(0.0)

    @pytest.mark.unit
    def test_sigmoid_steep_slope(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        steep = SigmoidMF(a=10.0, c=0.0)
        gentle = SigmoidMF(a=1.0, c=0.0)
        assert steep.compute_degree(1.0) > gentle.compute_degree(1.0)

    @pytest.mark.unit
    def test_sigmoid_asymptotes(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=1.0, c=0.0)
        assert mf.compute_degree(100.0) == pytest.approx(1.0, abs=1e-10)
        assert mf.compute_degree(-100.0) == pytest.approx(0.0, abs=1e-10)

    @pytest.mark.unit
    def test_sigmoid_overflow_protection_positive(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=-1.0, c=0.0)
        result = mf.compute_degree(1000.0)
        assert result == 0.0

    @pytest.mark.unit
    def test_sigmoid_overflow_protection_negative(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=-1.0, c=0.0)
        result = mf.compute_degree(-1000.0)
        assert result == 1.0

    @pytest.mark.unit
    def test_sigmoid_zero_a_raises(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        with pytest.raises(ValueError, match="a cannot be zero"):
            SigmoidMF(a=0.0, c=0.0)

    @pytest.mark.unit
    def test_sigmoid_function_type(self) -> None:
        from src.data_processing.membership_functions import SigmoidMF

        mf = SigmoidMF(a=1.0, c=0.0)
        assert mf.function_type == "sigmoid"


class TestMembershipFunctionFactory:
    @pytest.mark.unit
    def test_factory_creates_triangular(self) -> None:
        from src.data_processing.membership_functions import (
            TriangularMF,
            create_membership_function,
        )

        config = {
            "function_type": "triangular",
            "parameters": {"a": 0.0, "b": 5.0, "c": 10.0},
        }
        mf = create_membership_function(config)
        assert isinstance(mf, TriangularMF)
        assert mf.a == 0.0
        assert mf.b == 5.0
        assert mf.c == 10.0

    @pytest.mark.unit
    def test_factory_creates_trapezoidal(self) -> None:
        from src.data_processing.membership_functions import (
            TrapezoidalMF,
            create_membership_function,
        )

        config = {
            "function_type": "trapezoidal",
            "parameters": {"a": 0.0, "b": 5.0, "c": 15.0, "d": 20.0},
        }
        mf = create_membership_function(config)
        assert isinstance(mf, TrapezoidalMF)
        assert mf.a == 0.0
        assert mf.b == 5.0
        assert mf.c == 15.0
        assert mf.d == 20.0

    @pytest.mark.unit
    def test_factory_creates_gaussian(self) -> None:
        from src.data_processing.membership_functions import (
            GaussianMF,
            create_membership_function,
        )

        config = {
            "function_type": "gaussian",
            "parameters": {"mean": 25.0, "sigma": 5.0},
        }
        mf = create_membership_function(config)
        assert isinstance(mf, GaussianMF)
        assert mf.mean == 25.0
        assert mf.sigma == 5.0

    @pytest.mark.unit
    def test_factory_creates_sigmoid(self) -> None:
        from src.data_processing.membership_functions import (
            SigmoidMF,
            create_membership_function,
        )

        config = {
            "function_type": "sigmoid",
            "parameters": {"a": 0.5, "c": 20.0},
        }
        mf = create_membership_function(config)
        assert isinstance(mf, SigmoidMF)
        assert mf.a == 0.5
        assert mf.c == 20.0

    @pytest.mark.unit
    def test_factory_unknown_type_raises(self) -> None:
        from src.data_processing.membership_functions import (
            MembershipFunctionError,
            create_membership_function,
        )

        config = {
            "function_type": "unknown",
            "parameters": {},
        }
        with pytest.raises(MembershipFunctionError, match="Unknown function type"):
            create_membership_function(config)

    @pytest.mark.unit
    def test_factory_missing_type_raises(self) -> None:
        from src.data_processing.membership_functions import (
            MembershipFunctionError,
            create_membership_function,
        )

        config = {"parameters": {"a": 0.0, "b": 5.0, "c": 10.0}}
        with pytest.raises(MembershipFunctionError, match="Missing 'function_type'"):
            create_membership_function(config)

    @pytest.mark.unit
    def test_factory_missing_param_raises(self) -> None:
        from src.data_processing.membership_functions import (
            MembershipFunctionError,
            create_membership_function,
        )

        config = {
            "function_type": "triangular",
            "parameters": {"a": 0.0, "b": 5.0},
        }
        with pytest.raises(MembershipFunctionError, match="Missing required parameter"):
            create_membership_function(config)

    @pytest.mark.unit
    def test_factory_invalid_param_value_raises(self) -> None:
        from src.data_processing.membership_functions import (
            MembershipFunctionError,
            create_membership_function,
        )

        config = {
            "function_type": "triangular",
            "parameters": {"a": 10.0, "b": 5.0, "c": 0.0},
        }
        with pytest.raises(MembershipFunctionError, match="Invalid parameters"):
            create_membership_function(config)

    @pytest.mark.unit
    def test_factory_parameters_not_dict_raises(self) -> None:
        from src.data_processing.membership_functions import (
            MembershipFunctionError,
            create_membership_function,
        )

        config = {
            "function_type": "triangular",
            "parameters": [0.0, 5.0, 10.0],
        }
        with pytest.raises(MembershipFunctionError, match="must be a dictionary"):
            create_membership_function(config)


class TestMembershipFunctionABC:
    @pytest.mark.unit
    def test_membership_function_is_abstract(self) -> None:
        from src.data_processing.membership_functions import MembershipFunction

        with pytest.raises(TypeError, match="abstract"):
            MembershipFunction()  # type: ignore[abstract]

    @pytest.mark.unit
    def test_all_implementations_are_frozen(self) -> None:
        from src.data_processing.membership_functions import (
            GaussianMF,
            SigmoidMF,
            TrapezoidalMF,
            TriangularMF,
        )

        tri = TriangularMF(a=0.0, b=5.0, c=10.0)
        trap = TrapezoidalMF(a=0.0, b=5.0, c=15.0, d=20.0)
        gauss = GaussianMF(mean=0.0, sigma=1.0)
        sig = SigmoidMF(a=1.0, c=0.0)

        with pytest.raises(AttributeError):
            tri.a = 1.0  # type: ignore[misc]
        with pytest.raises(AttributeError):
            trap.b = 1.0  # type: ignore[misc]
        with pytest.raises(AttributeError):
            gauss.mean = 1.0  # type: ignore[misc]
        with pytest.raises(AttributeError):
            sig.c = 1.0  # type: ignore[misc]


class TestMembershipFunctionEdgeCases:
    @pytest.mark.unit
    def test_triangular_negative_range(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=-10.0, b=-5.0, c=0.0)
        assert mf.compute_degree(-5.0) == 1.0
        assert mf.compute_degree(-7.5) == 0.5
        assert mf.compute_degree(-2.5) == 0.5

    @pytest.mark.unit
    def test_gaussian_far_from_mean(self) -> None:
        from src.data_processing.membership_functions import GaussianMF

        mf = GaussianMF(mean=0.0, sigma=1.0)
        assert mf.compute_degree(10.0) == pytest.approx(0.0, abs=1e-10)

    @pytest.mark.unit
    def test_trapezoidal_all_equal_params(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=5.0, b=5.0, c=5.0, d=5.0)
        assert mf.compute_degree(5.0) == 1.0
        assert mf.compute_degree(4.9) == 0.0
        assert mf.compute_degree(5.1) == 0.0

    @pytest.mark.unit
    def test_triangular_degenerate_falling_edge_only(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=10.0, c=10.0)
        assert mf.compute_degree(5.0) == 0.5
        assert mf.compute_degree(10.0) == 1.0
        assert mf.compute_degree(0.0) == 0.0

    @pytest.mark.unit
    def test_triangular_degenerate_rising_edge_only(self) -> None:
        from src.data_processing.membership_functions import TriangularMF

        mf = TriangularMF(a=0.0, b=0.0, c=10.0)
        assert mf.compute_degree(5.0) == 0.5
        assert mf.compute_degree(0.0) == 1.0
        assert mf.compute_degree(10.0) == 0.0

    @pytest.mark.unit
    def test_trapezoidal_degenerate_left_ramp(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=0.0, c=5.0, d=10.0)
        assert mf.compute_degree(0.0) == 1.0
        assert mf.compute_degree(5.0) == 1.0
        assert mf.compute_degree(7.5) == 0.5

    @pytest.mark.unit
    def test_trapezoidal_degenerate_right_ramp(self) -> None:
        from src.data_processing.membership_functions import TrapezoidalMF

        mf = TrapezoidalMF(a=0.0, b=5.0, c=10.0, d=10.0)
        assert mf.compute_degree(10.0) == 1.0
        assert mf.compute_degree(5.0) == 1.0
        assert mf.compute_degree(2.5) == 0.5
