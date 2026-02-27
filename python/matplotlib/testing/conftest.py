"""Pytest fixtures for matplotlib tests."""
import pytest


@pytest.fixture(autouse=True)
def mpl_test_settings():
    """Reset matplotlib state before/after each test."""
    import matplotlib.pyplot as plt
    yield
    plt.close('all')
