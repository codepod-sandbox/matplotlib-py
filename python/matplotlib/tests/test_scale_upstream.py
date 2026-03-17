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


def test_set_xscale_log_changes_locator():
    """ax.set_xscale('log') must install LogLocator on xaxis."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import LogLocator
    from matplotlib.scale import LogScale
    fig, ax = plt.subplots()
    ax.set_xscale('log')
    assert isinstance(ax.xaxis.get_scale(), LogScale)
    assert isinstance(ax.xaxis.get_major_locator(), LogLocator)
    plt.close('all')


def test_set_xscale_linear_is_default():
    """ax.set_xscale('linear') (or default) uses LinearScale."""
    import matplotlib.pyplot as plt
    from matplotlib.scale import LinearScale
    fig, ax = plt.subplots()
    assert isinstance(ax.xaxis.get_scale(), LinearScale)
    plt.close('all')


def test_axes_layout_sx_linear():
    """AxesLayout.sx with linear scale behaves as before."""
    from matplotlib.backend_bases import AxesLayout
    from matplotlib.scale import LinearScale
    layout = AxesLayout(0, 0, 100, 100, 0, 10, 0, 10,
                        LinearScale(), LinearScale())
    assert abs(layout.sx(5) - 50) < 0.01


def test_axes_layout_sx_log():
    """AxesLayout.sx with LogScale maps in log space."""
    from matplotlib.backend_bases import AxesLayout
    from matplotlib.scale import LogScale
    s = LogScale(base=10)
    # data range: [1, 100]; forward: [0, 2]
    layout = AxesLayout(0, 0, 200, 100, 1, 100, 1, 10,
                        s, LogScale(base=10))
    # sx(10) → forward(10)=1.0, linear map [0,2]→[0,200] → 100
    assert abs(layout.sx(10) - 100) < 0.5


def test_axes_layout_backward_compat_no_scales():
    """AxesLayout constructed without scale args must work as before."""
    from matplotlib.backend_bases import AxesLayout
    layout = AxesLayout(0, 0, 100, 100, 0, 10, 0, 10)
    assert abs(layout.sx(5) - 50) < 0.01
    assert abs(layout.sy(5) - 50) < 0.01


def test_cla_resets_scale():
    """cla() must reset axis scale to LinearScale and _xscale to 'linear'."""
    import matplotlib.pyplot as plt
    from matplotlib.scale import LinearScale
    fig, ax = plt.subplots()
    ax.set_xscale('log')
    ax.cla()
    assert isinstance(ax.xaxis.get_scale(), LinearScale)
    assert ax.get_xscale() == 'linear'
    plt.close('all')
