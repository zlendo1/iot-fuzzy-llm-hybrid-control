import pytest


@pytest.mark.unit
def test_placeholder() -> None:
    assert True


@pytest.mark.unit
def test_python_version_meets_minimum_requirements() -> None:
    import sys

    assert sys.version_info >= (3, 9)
