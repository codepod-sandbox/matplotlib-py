# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
# Ported from upstream matplotlib tests/test_cm.py and tests/test_colors.py
"""Upstream-ported tests for colormaps, registry, ScalarMappable, and norm classes."""
import numpy as np
import numpy.testing as npt
import pytest


# ---------------------------------------------------------------------------
# Registry and get_cmap
# ---------------------------------------------------------------------------

def test_get_cmap_return_default():
    from matplotlib import cm
    from matplotlib.colors import Colormap
    cmap = cm.get_cmap()
    assert isinstance(cmap, Colormap)
    assert cmap.name == 'viridis'


def test_get_cmap_by_name():
    from matplotlib import cm
    from matplotlib.colors import Colormap
    for name in ('hot', 'viridis', 'Blues'):
        cmap = cm.get_cmap(name)
        assert isinstance(cmap, Colormap), f"get_cmap({name!r}) did not return Colormap"


def test_get_cmap_bad_name():
    from matplotlib import cm
    with pytest.raises(ValueError):
        cm.get_cmap('nonexistent_cmap_xyz')


def test_register_cmap():
    from matplotlib import cm
    from matplotlib.colors import ListedColormap
    my_cmap = ListedColormap(['#ff0000', '#00ff00', '#0000ff'], name='my_test_cmap')
    cm._colormaps.register(my_cmap, name='my_test_cmap', force=True)
    retrieved = cm.get_cmap('my_test_cmap')
    assert retrieved.name == 'my_test_cmap'


def test_registry_getitem_keyerror():
    from matplotlib import cm
    with pytest.raises(KeyError):
        _ = cm._colormaps['nonexistent_cmap_xyz']


# ---------------------------------------------------------------------------
# Colormap.__call__
# ---------------------------------------------------------------------------

def test_colormap_call_scalar():
    from matplotlib import cm
    cmap = cm.get_cmap('viridis')
    for x in (0.0, 0.5, 1.0):
        result = cmap(x)
        assert isinstance(result, tuple), f"cmap({x}) should return tuple, got {type(result)}"
        assert len(result) == 4, f"cmap({x}) should return 4-tuple"
        assert all(isinstance(v, float) for v in result), f"all values should be float"
        assert all(0.0 <= v <= 1.0 for v in result), f"all values should be in [0, 1]"


def test_colormap_call_array():
    from matplotlib import cm
    cmap = cm.get_cmap('viridis')
    x = np.linspace(0, 1, 10)
    result = cmap(x)
    assert hasattr(result, 'shape'), "array input should return array"
    assert result.shape == (10, 4), f"expected (10, 4), got {result.shape}"
    assert result.dtype == np.float64 or str(result.dtype).startswith('float')


def test_colormap_bytes():
    from matplotlib import cm
    cmap = cm.get_cmap('viridis')
    result = cmap(0.5, bytes=True)
    assert isinstance(result, tuple), "bytes=True should return tuple"
    assert len(result) == 4
    assert all(isinstance(v, int) for v in result), f"bytes=True should return ints, got {result}"
    assert all(0 <= v <= 255 for v in result), f"bytes should be in [0,255], got {result}"


def test_colormap_reversed():
    from matplotlib import cm
    cmap = cm.get_cmap('viridis')
    rev = cmap.reversed()
    assert isinstance(rev.name, str)
    # cmap(0.0) should equal rev(1.0) — tolerance of 1/256 accounts for LUT rounding
    c0 = cmap(0.0)
    r1 = rev(1.0)
    npt.assert_allclose(c0, r1, atol=1/256, err_msg=f"cmap(0.0)={c0} != rev(1.0)={r1}")


# ---------------------------------------------------------------------------
# ListedColormap
# ---------------------------------------------------------------------------

def test_listed_colormap():
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(['r', 'g', 'b'])
    assert cmap.N == 3
    result = cmap(0.0)
    assert isinstance(result, tuple) and len(result) == 4
    # 0.0 should map to red: (1.0, 0.0, 0.0, 1.0)
    assert abs(result[0] - 1.0) < 1e-6, f"first color should be red, got {result}"
    assert abs(result[1] - 0.0) < 1e-6
    assert abs(result[2] - 0.0) < 1e-6


# ---------------------------------------------------------------------------
# LinearSegmentedColormap
# ---------------------------------------------------------------------------

def test_linear_segmented_from_list():
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('test_lr', ['blue', 'red'])
    result = cmap(0.5)
    assert isinstance(result, tuple) and len(result) == 4
    assert all(0.0 <= v <= 1.0 for v in result), f"RGBA values out of range: {result}"


# ---------------------------------------------------------------------------
# Norm classes
# ---------------------------------------------------------------------------

def test_boundary_norm():
    from matplotlib.colors import BoundaryNorm
    norm = BoundaryNorm([0, 1, 2, 3], ncolors=3)
    result = norm(1.5)
    # 1.5 is in bin [1, 2] → bin index 1 → normalized value = (1+0.5)/3 = 0.5
    assert abs(float(result) - 0.5) < 1e-6, f"BoundaryNorm(1.5) expected 0.5, got {result}"


def test_two_slope_norm():
    from matplotlib.colors import TwoSlopeNorm
    norm = TwoSlopeNorm(vcenter=0, vmin=-1, vmax=2)
    x = np.array([-1.0, 0.0, 2.0])
    result = norm(x)
    result_list = result.tolist() if hasattr(result, 'tolist') else list(result)
    npt.assert_allclose(result_list, [0.0, 0.5, 1.0], atol=1e-6)


def test_centered_norm():
    from matplotlib.colors import CenteredNorm
    norm = CenteredNorm()
    x = np.array([-1.0, 0.0, 1.0])
    result = norm(x)
    result_list = result.tolist() if hasattr(result, 'tolist') else list(result)
    npt.assert_allclose(result_list, [0.0, 0.5, 1.0], atol=1e-6)


# ---------------------------------------------------------------------------
# ScalarMappable
# ---------------------------------------------------------------------------

def test_scalar_mappable_to_rgba():
    from matplotlib import cm
    from matplotlib.colors import Normalize
    sm = cm.ScalarMappable(norm=Normalize(0, 1), cmap='viridis')
    x = np.array([0.0, 0.5, 1.0])
    result = sm.to_rgba(x)
    assert hasattr(result, 'shape'), "to_rgba should return array"
    assert result.shape == (3, 4), f"expected (3, 4), got {result.shape}"


def test_scalar_mappable_set_clim():
    from matplotlib import cm
    sm = cm.ScalarMappable(cmap='viridis')
    sm.set_clim(0, 10)
    assert sm.get_clim() == (0, 10)


def test_scalar_mappable_autoscale():
    from matplotlib import cm
    sm = cm.ScalarMappable(cmap='viridis')
    sm.set_array(np.array([1.0, 2.0, 3.0]))
    sm.autoscale()
    vmin, vmax = sm.get_clim()
    assert vmin == 1.0, f"expected vmin=1.0, got {vmin}"
    assert vmax == 3.0, f"expected vmax=3.0, got {vmax}"


def test_scalar_mappable_norm_false():
    from matplotlib import cm
    from matplotlib.colors import Normalize
    sm = cm.ScalarMappable(norm=Normalize(0, 1), cmap='viridis')
    x = np.array([0.0, 0.5, 1.0])
    result = sm.to_rgba(x, norm=False)
    assert result.shape == (3, 4)


# ---------------------------------------------------------------------------
# Exhaustive registry test
# ---------------------------------------------------------------------------

def test_all_colormaps_callable():
    from matplotlib import cm
    from matplotlib.colors import Colormap
    names = list(cm._colormaps)
    assert len(names) >= 100, f"expected ≥100 colormaps, got {len(names)}"
    errors = []
    for name in names:
        try:
            cmap = cm._colormaps[name]
            result = cmap(0.5)
            assert isinstance(result, tuple) and len(result) == 4
        except Exception as e:
            errors.append(f"{name}: {e}")
    assert not errors, "Some colormaps failed:\n" + "\n".join(errors[:10])


# ---------------------------------------------------------------------------
# rcParams
# ---------------------------------------------------------------------------

def test_rcparam_image_cmap():
    import matplotlib
    assert matplotlib.rcParams['image.cmap'] == 'viridis'
    assert matplotlib.rcParams['image.lut'] == 256
