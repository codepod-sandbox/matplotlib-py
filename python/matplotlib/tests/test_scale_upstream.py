# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
# Ported from lib/matplotlib/tests/test_axes.py (scale sections)
import pytest
import numpy as np


def test_linear_scale_identity():
    """LinearScale forward/inverse are identity."""
    from matplotlib.scale import LinearScale
    s = LinearScale()
    vals = np.array([0.0, 1.0, 2.0, -3.0])
    np.testing.assert_array_equal(s.forward(vals), vals)
    np.testing.assert_array_equal(s.inverse(vals), vals)


def test_log_scale_forward():
    """LogScale(base=10) forward maps 1→0, 10→1, 100→2 (in log10)."""
    from matplotlib.scale import LogScale
    s = LogScale(base=10)
    vals = np.array([1.0, 10.0, 100.0])
    result = s.forward(vals)
    np.testing.assert_allclose(result, [0.0, 1.0, 2.0], atol=1e-10)


def test_log_scale_inverse():
    """LogScale(base=10) inverse maps 0→1, 1→10, 2→100."""
    from matplotlib.scale import LogScale
    s = LogScale(base=10)
    vals = np.array([0.0, 1.0, 2.0])
    result = s.inverse(vals)
    np.testing.assert_allclose(result, [1.0, 10.0, 100.0], atol=1e-10)


def test_log_scale_nonpos():
    """LogScale masks non-positive values."""
    from matplotlib.scale import LogScale
    import numpy.ma as ma
    s = LogScale(base=10)
    vals = np.array([-1.0, 0.0, 1.0, 10.0])
    result = s.forward(vals)
    assert isinstance(result, ma.MaskedArray)
    assert result.mask[0]   # -1 masked
    assert result.mask[1]   # 0 masked
    assert not result.mask[2]  # 1 unmasked
    assert not result.mask[3]  # 10 unmasked


def test_symlog_scale():
    """SymmetricalLogScale is symmetric around zero."""
    from matplotlib.scale import SymmetricalLogScale
    s = SymmetricalLogScale(base=10, linthresh=1.0)
    fwd = s.forward(np.array([1.0, -1.0]))
    assert abs(fwd[0]) == abs(fwd[1])


def test_func_scale():
    """FuncScale applies user-provided forward/inverse callables."""
    from matplotlib.scale import FuncScale
    s = FuncScale(forward=np.sqrt, inverse=np.square)
    vals = np.array([1.0, 4.0, 9.0])
    result = s.forward(vals)
    np.testing.assert_allclose(result, [1.0, 2.0, 3.0])
    np.testing.assert_allclose(s.inverse(result), vals)
