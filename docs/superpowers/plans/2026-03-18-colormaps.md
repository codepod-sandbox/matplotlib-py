# Colormaps Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add full colormap support to matplotlib-rust: ~150 named colormaps, Colormap/LinearSegmentedColormap/ListedColormap hierarchy, ColormapRegistry, get_cmap, and ScalarMappable.

**Architecture:** Copy colormap data from upstream matplotlib 3.9.x (_cm.py, _cm_listed.py), append Colormap class hierarchy to existing colors.py, create new cm.py with registry and ScalarMappable, and add image.cmap/image.lut to rcsetup.py. All masked-array usage replaced with NaN-based approach. Lazy _lut initialization prevents WASM startup cost.

**Tech Stack:** Python (RustPython), numpy-rust, upstream matplotlib 3.9.x as source for copy+adapt

**Worktree:** `packages/matplotlib-py/.worktrees/colormaps/`
**Build:** `cargo build -p matplotlib-python` (from worktree root)
**Test new:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -v`
**Test full:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q`
**Baseline:** 848 passed, 0 failed

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `python/matplotlib/rcsetup.py` | Modify | Add `image.cmap` and `image.lut` to `_default_params` |
| `python/matplotlib/_cm_listed.py` | Create | Raw Python lists of RGBA floats for ALL listed colormaps in the upstream file — **no imports at all** |
| `python/matplotlib/_cm.py` | Create | Segment data dicts for classic colormaps (jet, hot, cool, bone, copper, etc.) — `import functools, numpy as np` only |
| `python/matplotlib/colors.py` | Extend | Append Colormap, LinearSegmentedColormap, ListedColormap, BoundaryNorm, TwoSlopeNorm, CenteredNorm |
| `python/matplotlib/cm.py` | Create | ColormapRegistry, `_colormaps` global, `get_cmap()`, `ScalarMappable` |
| `python/matplotlib/tests/test_cm_upstream.py` | Create | All 20 tests from spec |

**Dependency order:** rcsetup.py → _cm_listed.py → _cm.py → colors.py → cm.py → tests

---

## Chunk 1: Data files and test skeleton

### Task 1: rcsetup.py — add image.cmap and image.lut

**Files:**
- Modify: `python/matplotlib/rcsetup.py:74` (after `'savefig.format'` line)

- [ ] **Step 1: Write the failing test**

```python
# python/matplotlib/tests/test_cm_upstream.py  (create this file with just this test for now)
def test_rcparam_image_cmap():
    import matplotlib
    assert matplotlib.rcParams['image.cmap'] == 'viridis'
    assert matplotlib.rcParams['image.lut'] == 256
```

- [ ] **Step 2: Run to verify it fails**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py::test_rcparam_image_cmap -v
```
Expected: FAIL — `KeyError: 'image.cmap'`

- [ ] **Step 3: Add to `_default_params` in `rcsetup.py`**

In `python/matplotlib/rcsetup.py`, add inside `_default_params` after the `# Saving` block (line ~74):

```python
    # Image / colormap
    'image.cmap': 'viridis',
    'image.lut': 256,
```

- [ ] **Step 4: Run to verify it passes**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py::test_rcparam_image_cmap -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add python/matplotlib/rcsetup.py python/matplotlib/tests/test_cm_upstream.py
git commit -m "feat: add image.cmap and image.lut to rcsetup defaults"
```

---

### Task 2: _cm_listed.py — copy raw RGBA data from upstream

**Files:**
- Create: `python/matplotlib/_cm_listed.py`

The listed colormaps are large (~256 entries each). Copy the raw data arrays from upstream matplotlib 3.9.x. The upstream file is at:
`https://github.com/matplotlib/matplotlib/blob/v3.9.0/lib/matplotlib/_cm_listed.py`

**Critical adaptation rules:**
1. Remove **all** imports (the upstream file has `from .colors import ListedColormap` and no other imports — remove it entirely)
2. Remove all `ListedColormap(...)` constructor calls and any `datad = {...}` dict referencing them
3. Keep every `_*_data = [...]` assignment verbatim — do NOT filter to a subset; keep the full upstream file's data variables
4. Add the copyright header shown below

`test_get_cmap_by_name` requires `get_cmap('Blues')` to succeed. `Blues` lives in `_cm_listed.py` in upstream 3.9.x. Keeping the full upstream file guarantees Blues and all ColorBrewer maps are present.

File structure after adaptation:
```python
# Copyright (c) 2012- Matplotlib Development Team; All Rights Reserved
# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
"""Raw RGBA list data for perceptual and categorical colormaps.

No imports — raw Python lists of [R, G, B, A] floats in [0, 1].
These are wrapped in ListedColormap by cm.py at registry construction time.
"""

_viridis_data = [
    [0.267004, 0.004874, 0.329415, 1.0],
    [0.268510, 0.009605, 0.335427, 1.0],
    # ... 254 more entries from upstream ...
]

_plasma_data = [ ... ]
# etc.
```

- [ ] **Step 1: Fetch and create the file**

Fetch upstream `_cm_listed.py` from:
```
https://raw.githubusercontent.com/matplotlib/matplotlib/v3.9.0/lib/matplotlib/_cm_listed.py
```

Strip **all import lines** (there is only one: `from .colors import ListedColormap`). Strip any line containing `ListedColormap(` and any `datad` dict that references `ListedColormap(...)`. Keep every `_*_data = [...]` assignment — do not filter. Add the copyright header shown above.

- [ ] **Step 2: Verify it's importable**

```bash
target/debug/matplotlib-python -c "from matplotlib._cm_listed import _viridis_data; print(len(_viridis_data), _viridis_data[0])"
```
Expected: `256 [0.267004, 0.004874, 0.329415, 1.0]` (exact values may vary slightly)

- [ ] **Step 3: Commit**

```bash
git add python/matplotlib/_cm_listed.py
git commit -m "feat: add _cm_listed.py — raw RGBA data for listed colormaps"
```

---

### Task 3: _cm.py — copy segment data from upstream

**Files:**
- Create: `python/matplotlib/_cm.py`

Fetch from upstream:
```
https://raw.githubusercontent.com/matplotlib/matplotlib/v3.9.0/lib/matplotlib/_cm.py
```

**Adaptation rules:**
1. Remove any `from matplotlib import ...` lines
2. Keep `import numpy as np` and `import functools`
3. Keep all `datad = {...}` content intact
4. Add copyright header

The result should look like:
```python
# Copyright (c) 2012- Matplotlib Development Team; All Rights Reserved
# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
"""Colormap segment data for classic colormaps (jet, hot, cool, bone, etc.)."""
import functools
import numpy as np

# ... segment data and datad dict from upstream ...

datad = {
    'Blues':   _Blues_data,
    'BrBG':    _BrBG_data,
    # ... all ~70 entries ...
    'jet':     {'red': [...], 'green': [...], 'blue': [...]},
    'hot':     {'red': [...], 'green': [...], 'blue': [...]},
    # etc.
}
```

- [ ] **Step 1: Create the file**

Fetch and adapt as described above.

- [ ] **Step 2: Verify it's importable**

```bash
target/debug/matplotlib-python -c "from matplotlib._cm import datad; print(len(datad), list(datad.keys())[:5])"
```
Expected: prints count ≥ 60 and names like `['Blues', 'BrBG', ...]`

- [ ] **Step 3: Commit**

```bash
git add python/matplotlib/_cm.py
git commit -m "feat: add _cm.py — segment data for classic colormaps"
```

---

### Task 4: Write the full test file (all 20 tests, all fail)

**Files:**
- Modify: `python/matplotlib/tests/test_cm_upstream.py`

Replace the test file (which has only `test_rcparam_image_cmap`) with the full test suite:

```python
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
```

- [ ] **Step 1: Write the full test file**

Replace `python/matplotlib/tests/test_cm_upstream.py` with the code above.

- [ ] **Step 2: Run all tests to confirm they all fail**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -q --tb=no
```
Expected: 20 failed (mostly `ImportError: cannot import name 'Colormap'` or `ModuleNotFoundError: No module named 'matplotlib.cm'`)

- [ ] **Step 3: Commit the test file**

```bash
git add python/matplotlib/tests/test_cm_upstream.py
git commit -m "test: add test_cm_upstream.py — 20 failing tests for colormap sub-project"
```

---

## Chunk 2: Colormap classes in colors.py

### Task 5: colors.py — Colormap base class + LinearSegmentedColormap

**Files:**
- Modify: `python/matplotlib/colors.py` (append after line 844)

**Context:** `colors.py` already has `to_rgba`, `to_rgba_array`, `Normalize`, `LogNorm`. You are appending new classes at the bottom of the file. No existing code changes needed.

- [ ] **Step 1: Write tests for this task only**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "colormap_call or linear_segmented or colormap_bytes or colormap_reversed" -v --tb=short
```
Expected: all fail with `ImportError`

- [ ] **Step 2: Append to `python/matplotlib/colors.py`**

Add the following at the end of `python/matplotlib/colors.py`:

```python
# ---------------------------------------------------------------------------
# Colormap class hierarchy
# Adapted from upstream matplotlib/colors.py (matplotlib 3.9.x)
# Masked array usage replaced with NaN-based approach for RustPython compat.
# Copyright (c) 2012- Matplotlib Development Team
# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
# ---------------------------------------------------------------------------

import numpy as np


class Colormap:
    """Base class for all colormaps."""

    def __init__(self, name, N=256):
        self.name = name
        self.N = int(N)
        self._rgba_bad = (0.0, 0.0, 0.0, 0.0)  # transparent black
        self._rgba_under = None
        self._rgba_over = None

    def __call__(self, X, alpha=None, bytes=False):
        """Map scalar or array X in [0, 1] to RGBA.

        Parameters
        ----------
        X : scalar or array-like
            Values in [0, 1]. NaN values map to the "bad" color.
        alpha : float, optional
            Alpha multiplier applied after LUT lookup.
        bytes : bool
            If True, return uint8 values in [0, 255].

        Returns
        -------
        tuple (4,) for scalar input; ndarray (…, 4) for array input.
        """
        if not hasattr(self, '_lut'):
            self._init()

        scalar_input = not hasattr(X, '__len__') and not hasattr(X, 'shape')
        if scalar_input:
            X = np.array([float(X)], dtype=float)
        else:
            X = np.asarray(X, dtype=float)

        orig_shape = X.shape
        X = X.flatten()

        bad_mask = np.isnan(X)
        under_mask = X < 0.0
        over_mask = X > 1.0

        # Clip to valid LUT range
        Xc = np.clip(X, 0.0, 1.0)

        # Map to LUT indices
        idx = (Xc * (self.N - 1) + 0.5).astype(int)
        idx = np.clip(idx, 0, self.N - 1)

        # Index into LUT
        result = np.zeros((len(X), 4), dtype=float)
        idx_list = idx.tolist()
        for i, j in enumerate(idx_list):
            result[i] = self._lut[j]

        # Apply special colors
        bad_list = bad_mask.tolist()
        under_list = under_mask.tolist()
        over_list = over_mask.tolist()

        bad_color = list(self._rgba_bad)
        under_color = self._lut[0].tolist() if self._rgba_under is None else list(self._rgba_under)
        over_color = self._lut[self.N - 1].tolist() if self._rgba_over is None else list(self._rgba_over)

        for i in range(len(X)):
            if bad_list[i]:
                result[i] = bad_color
            elif under_list[i]:
                result[i] = under_color
            elif over_list[i]:
                result[i] = over_color

        # Apply alpha multiplier
        if alpha is not None:
            result[:, 3] = result[:, 3] * float(alpha)

        # Clip final result to [0, 1]
        result = np.clip(result, 0.0, 1.0)

        # Reshape to original shape + (4,)
        if len(orig_shape) > 1:
            result = result.reshape(orig_shape + (4,))
        elif len(orig_shape) == 0:
            result = result.reshape((4,))
        # else: already (N, 4)

        if bytes:
            result_bytes = (result * 255 + 0.5).astype(np.uint8)
            if scalar_input:
                return tuple(result_bytes[0].tolist())
            return result_bytes

        if scalar_input:
            return tuple(result[0].tolist())
        return result

    def reversed(self, name=None):
        """Return a reversed copy of this colormap."""
        raise NotImplementedError(f"{type(self).__name__} does not support reversed()")

    def set_bad(self, color='k', alpha=None):
        """Set the color for masked/NaN values."""
        self._rgba_bad = list(to_rgba(color, alpha=alpha))

    def set_under(self, color='k', alpha=None):
        """Set the color for out-of-range low values."""
        self._rgba_under = list(to_rgba(color, alpha=alpha))

    def set_over(self, color='k', alpha=None):
        """Set the color for out-of-range high values."""
        self._rgba_over = list(to_rgba(color, alpha=alpha))

    def is_gray(self):
        """Return True if the colormap is grayscale."""
        if not hasattr(self, '_lut'):
            self._init()
        lut_list = self._lut[:self.N].tolist()
        return all(
            abs(row[0] - row[1]) < 1e-9 and abs(row[0] - row[2]) < 1e-9
            for row in lut_list
        )

    def __repr__(self):
        return f"<{type(self).__name__} '{self.name}'>"

    def __eq__(self, other):
        if not isinstance(other, Colormap):
            return False
        return self.name == other.name

    def __copy__(self):
        cls = type(self)
        new = cls.__new__(cls)
        new.__dict__.update(self.__dict__.copy())
        if hasattr(self, '_lut'):
            new._lut = self._lut.copy()
        return new


class LinearSegmentedColormap(Colormap):
    """Colormap defined by piecewise-linear segment data.

    segmentdata : dict with keys 'red', 'green', 'blue' (and optionally 'alpha').
    Each value is either:
      - a list of (x, y0, y1) triples, or
      - a callable f(x) → values in [0, 1].
    """

    def __init__(self, name, segmentdata, N=256, gamma=1.0):
        super().__init__(name, N)
        self._segmentdata = segmentdata
        self._gamma = float(gamma)

    def _init(self):
        """Build the LUT array from segmentdata. Called lazily on first use."""
        x = np.linspace(0.0, 1.0, self.N)
        self._lut = np.zeros((self.N, 4), dtype=float)

        for ch_idx, channel in enumerate(('red', 'green', 'blue')):
            seg = self._segmentdata[channel]
            if callable(seg):
                vals = seg(x)
                self._lut[:, ch_idx] = np.asarray(vals, dtype=float)
            else:
                # seg is a list of (x_i, y0_i, y1_i)
                xs = np.array([pt[0] for pt in seg], dtype=float)
                # Use y1 (right-hand side) for interpolation
                ys = np.array([pt[2] for pt in seg], dtype=float)
                self._lut[:, ch_idx] = np.interp(x, xs, ys)

        # Alpha channel
        if 'alpha' in self._segmentdata:
            seg = self._segmentdata['alpha']
            if callable(seg):
                self._lut[:, 3] = np.asarray(seg(x), dtype=float)
            else:
                xs = np.array([pt[0] for pt in seg], dtype=float)
                ys = np.array([pt[2] for pt in seg], dtype=float)
                self._lut[:, 3] = np.interp(x, xs, ys)
        else:
            self._lut[:, 3] = 1.0

        # Apply gamma
        if self._gamma != 1.0:
            self._lut[:, :3] = self._lut[:, :3] ** self._gamma

        self._lut = np.clip(self._lut, 0.0, 1.0)

    def set_gamma(self, gamma):
        """Recompute LUT with a new gamma."""
        self._gamma = float(gamma)
        if hasattr(self, '_lut'):
            del self._lut

    @classmethod
    def from_list(cls, name, colors, N=256):
        """Create a LinearSegmentedColormap from a list of colors.

        Parameters
        ----------
        name : str
        colors : list of color specs, or list of (value, color) pairs
        N : int, number of LUT entries
        """
        if len(colors) == 0:
            raise ValueError("colors must not be empty")

        # Normalize: accept plain list or list of (val, color)
        if isinstance(colors[0], (list, tuple)) and len(colors[0]) == 2 and not isinstance(colors[0][0], str):
            # List of (val, color)
            vals = [float(c[0]) for c in colors]
            cols = [c[1] for c in colors]
        else:
            # Plain list of colors — evenly spaced
            n = len(colors)
            vals = [i / (n - 1) for i in range(n)] if n > 1 else [0.0]
            cols = colors

        rgba = [to_rgba(c) for c in cols]

        # Build segmentdata
        r_seg = [(vals[i], rgba[i][0], rgba[i][0]) for i in range(len(vals))]
        g_seg = [(vals[i], rgba[i][1], rgba[i][1]) for i in range(len(vals))]
        b_seg = [(vals[i], rgba[i][2], rgba[i][2]) for i in range(len(vals))]
        a_seg = [(vals[i], rgba[i][3], rgba[i][3]) for i in range(len(vals))]

        # Fix discontinuities: y0 of point i+1 = y1 of point i (no jump)
        segmentdata = {'red': r_seg, 'green': g_seg, 'blue': b_seg, 'alpha': a_seg}
        return cls(name, segmentdata, N=N)

    def reversed(self, name=None):
        if name is None:
            name = self.name + '_r'
        # Reverse segmentdata by flipping x coordinates: x → 1-x, swap y0/y1
        new_sd = {}
        for channel, seg in self._segmentdata.items():
            if callable(seg):
                orig = seg
                new_sd[channel] = lambda x, f=orig: f(1.0 - x)
            else:
                new_seg = [(1.0 - pt[0], pt[2], pt[1]) for pt in reversed(seg)]
                new_sd[channel] = new_seg
        cmap = LinearSegmentedColormap(name, new_sd, N=self.N, gamma=self._gamma)
        return cmap
```

- [ ] **Step 3: Run tests for this chunk**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "colormap_call or linear_segmented or colormap_bytes or colormap_reversed" -v --tb=short
```
Expected: still fail (no ListedColormap yet, and cm.get_cmap not yet available) — that's OK, we implement bottom-up

- [ ] **Step 4: Commit**

```bash
git add python/matplotlib/colors.py
git commit -m "feat: add Colormap and LinearSegmentedColormap to colors.py"
```

---

### Task 6: colors.py — ListedColormap

**Files:**
- Modify: `python/matplotlib/colors.py` (append after LinearSegmentedColormap)

- [ ] **Step 1: Append ListedColormap to `python/matplotlib/colors.py`**

```python
class ListedColormap(Colormap):
    """Colormap defined by a fixed list of colors.

    Parameters
    ----------
    colors : list of color specs
    name : str
    N : int or None — if None, defaults to len(colors)
    """

    def __init__(self, colors, name='from_list', N=None):
        if N is None:
            N = len(colors)
        super().__init__(name, N)
        self.colors = colors

    def _init(self):
        """Build LUT from the colors list."""
        rgba = to_rgba_array(self.colors)
        # Resample to N entries if needed
        if len(rgba.tolist()) != self.N:
            # Nearest-neighbor resample
            n_src = len(rgba.tolist())
            self._lut = np.zeros((self.N, 4), dtype=float)
            lut_list = []
            for i in range(self.N):
                src_idx = int(i * n_src / self.N)
                src_idx = min(src_idx, n_src - 1)
                lut_list.append(rgba[src_idx].tolist())
            self._lut = np.array(lut_list, dtype=float)
        else:
            self._lut = np.asarray(rgba.tolist(), dtype=float)

    def reversed(self, name=None):
        if name is None:
            name = self.name + '_r'
        colors = self.colors[::-1] if isinstance(self.colors, list) else list(reversed(self.colors))
        return ListedColormap(colors, name=name, N=self.N)
```

- [ ] **Step 2: Smoke-test ListedColormap directly**

```bash
target/debug/matplotlib-python -c "
from matplotlib.colors import ListedColormap
import numpy as np
cmap = ListedColormap(['r', 'g', 'b'])
print('N =', cmap.N)
print('cmap(0.0) =', cmap(0.0))
print('cmap(0.5) =', cmap(0.5))
print('cmap(1.0) =', cmap(1.0))
arr = cmap(np.linspace(0, 1, 5))
print('array shape:', arr.shape)
"
```
Expected: `N = 3`, `cmap(0.0) = (1.0, 0.0, 0.0, 1.0)` (red), shape `(5, 4)`

- [ ] **Step 3: Run listed_colormap test**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py::test_listed_colormap -v
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add python/matplotlib/colors.py
git commit -m "feat: add ListedColormap to colors.py"
```

---

### Task 7: colors.py — BoundaryNorm, TwoSlopeNorm, CenteredNorm

**Files:**
- Modify: `python/matplotlib/colors.py` (append after ListedColormap)

- [ ] **Step 1: Append norm classes to `python/matplotlib/colors.py`**

```python
class BoundaryNorm(Normalize):
    """Map values into integer bins defined by boundaries.

    Parameters
    ----------
    boundaries : array-like, strictly increasing
    ncolors : int — number of colors (bins) in the colormap
    clip : bool
    """

    def __init__(self, boundaries, ncolors, clip=False):
        b = sorted(float(x) for x in boundaries)
        if len(b) < 2:
            raise ValueError("boundaries must have at least 2 entries")
        super().__init__(vmin=b[0], vmax=b[-1], clip=clip)
        self.boundaries = b
        self.ncolors = int(ncolors)
        self._n_regions = len(b) - 1

    def __call__(self, value, clip=None):
        import numpy as np
        scalar = not hasattr(value, '__len__') and not hasattr(value, 'shape')
        arr = np.asarray(value, dtype=float)
        flat = arr.flatten().tolist()
        result = []
        for v in flat:
            if np.isnan(v):
                result.append(float('nan'))
                continue
            # Find which bin v falls into using searchsorted
            idx = 0
            for i in range(len(self.boundaries) - 1):
                if v >= self.boundaries[i]:
                    idx = i
            # Map bin index to [0, 1] via ncolors
            r = (idx + 0.5) / self.ncolors
            if self.clip:
                r = max(0.0, min(1.0, r))
            result.append(r)
        out = np.array(result, dtype=float)
        if scalar:
            return float(out[0])
        return out.reshape(arr.shape)


class TwoSlopeNorm(Normalize):
    """Diverging normalization with separate slopes below/above vcenter.

    Maps vmin→0, vcenter→0.5, vmax→1.
    """

    def __init__(self, vcenter, vmin=None, vmax=None):
        super().__init__(vmin=vmin, vmax=vmax)
        self.vcenter = float(vcenter)

    def __call__(self, value, clip=None):
        import numpy as np
        if self.vmin is None or self.vmax is None:
            raise ValueError("TwoSlopeNorm requires vmin and vmax")
        vmin = float(self.vmin)
        vmax = float(self.vmax)
        vc = self.vcenter

        scalar = not hasattr(value, '__len__') and not hasattr(value, 'shape')
        arr = np.asarray(value, dtype=float)
        flat = arr.flatten().tolist()
        result = []
        for v in flat:
            if np.isnan(v):
                result.append(float('nan'))
            elif v <= vc:
                # Map [vmin, vcenter] → [0, 0.5]
                if vc == vmin:
                    result.append(0.5)
                else:
                    result.append(0.5 * (v - vmin) / (vc - vmin))
            else:
                # Map [vcenter, vmax] → [0.5, 1.0]
                if vmax == vc:
                    result.append(0.5)
                else:
                    result.append(0.5 + 0.5 * (v - vc) / (vmax - vc))
        out = np.array(result, dtype=float)
        if self.clip:
            out = np.clip(out, 0.0, 1.0)
        if scalar:
            return float(out[0])
        return out.reshape(arr.shape)


class CenteredNorm(Normalize):
    """Normalize symmetrically around a center value.

    Maps [vcenter - halfrange, vcenter + halfrange] → [0, 1].
    halfrange is determined from the data if not provided.
    """

    def __init__(self, vcenter=0.0, halfrange=None):
        super().__init__()
        self.vcenter = float(vcenter)
        self._halfrange = float(halfrange) if halfrange is not None else None

    def __call__(self, value, clip=None):
        import numpy as np
        scalar = not hasattr(value, '__len__') and not hasattr(value, 'shape')
        arr = np.asarray(value, dtype=float)

        if self._halfrange is None:
            # Determine halfrange from data (max abs deviation from vcenter)
            flat = arr.flatten().tolist()
            valid = [abs(v - self.vcenter) for v in flat if not np.isnan(v)]
            halfrange = max(valid) if valid else 1.0
        else:
            halfrange = self._halfrange

        if halfrange == 0.0:
            halfrange = 1.0

        vmin = self.vcenter - halfrange
        vmax = self.vcenter + halfrange
        flat = arr.flatten().tolist()
        result = []
        for v in flat:
            if np.isnan(v):
                result.append(float('nan'))
            else:
                r = (v - vmin) / (vmax - vmin)
                use_clip = self.clip if clip is None else clip
                if use_clip:
                    r = max(0.0, min(1.0, r))
                result.append(r)
        out = np.array(result, dtype=float)
        if scalar:
            return float(out[0])
        return out.reshape(arr.shape)
```

- [ ] **Step 2: Run norm tests**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "boundary_norm or two_slope or centered_norm" -v
```
Expected: 3 PASS

- [ ] **Step 3: Commit**

```bash
git add python/matplotlib/colors.py
git commit -m "feat: add BoundaryNorm, TwoSlopeNorm, CenteredNorm to colors.py"
```

---

## Chunk 3: Registry, ScalarMappable, and full test run

### Task 8: cm.py — ColormapRegistry + _colormaps + get_cmap

**Files:**
- Create: `python/matplotlib/cm.py`

- [ ] **Step 1: Run registry tests to confirm they fail**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "get_cmap or register or registry or all_colormaps" -v --tb=line
```
Expected: fail with `ModuleNotFoundError: No module named 'matplotlib.cm'`

- [ ] **Step 2: Create `python/matplotlib/cm.py`**

```python
# Copyright (c) 2012- Matplotlib Development Team; All Rights Reserved
# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
"""
matplotlib.cm — colormap registry, get_cmap(), and ScalarMappable.

Adapted from upstream matplotlib/cm.py (3.9.x).
"""

from matplotlib.colors import (
    Colormap, LinearSegmentedColormap, ListedColormap, Normalize,
)
import matplotlib._cm as _cm
import matplotlib._cm_listed as _cm_listed


class ColormapRegistry:
    """Dict-like registry of named Colormap objects.

    Pre-populated with all built-in colormaps at import time.
    Reversed (_r) variants are also included.
    """

    def __init__(self, cmaps):
        # cmaps: dict of name → Colormap
        self._cmaps = dict(cmaps)

    def __getitem__(self, item):
        try:
            return self._cmaps[item]
        except KeyError:
            raise KeyError(f"Unknown colormap: {item!r}") from None

    def __iter__(self):
        return iter(self._cmaps)

    def __len__(self):
        return len(self._cmaps)

    def __contains__(self, item):
        return item in self._cmaps

    def register(self, cmap, *, name=None, force=False):
        """Register a colormap.

        Parameters
        ----------
        cmap : Colormap
        name : str, optional — defaults to cmap.name
        force : bool — if False, raises ValueError if name already exists
        """
        if name is None:
            name = cmap.name
        if not isinstance(cmap, Colormap):
            raise ValueError(f"register() requires a Colormap instance, got {type(cmap)}")
        if name in self._cmaps and not force:
            raise ValueError(
                f"A colormap named {name!r} is already registered. "
                "Use force=True to overwrite."
            )
        self._cmaps[name] = cmap

    def get_cmap(self, name=None, lut=None):
        """Look up a colormap by name (or return the default).

        Parameters
        ----------
        name : str, Colormap, or None
            None → rcParams['image.cmap']; Colormap instance → returned as-is.
        lut : int, optional
            If provided, resample the colormap to this many entries.

        Returns
        -------
        Colormap
        """
        if name is None:
            import matplotlib
            name = matplotlib.rcParams.get('image.cmap', 'viridis')

        if isinstance(name, Colormap):
            cmap = name
        elif isinstance(name, str):
            if name not in self._cmaps:
                raise ValueError(
                    f"Unknown colormap {name!r}. "
                    f"Use cm._colormaps to see available names."
                )
            cmap = self._cmaps[name]
        else:
            raise TypeError(f"get_cmap() expects str or Colormap, got {type(name)}")

        if lut is not None:
            cmap = cmap.__copy__()
            cmap.N = int(lut)
            if hasattr(cmap, '_lut'):
                del cmap._lut

        return cmap


def _build_registry():
    """Build the global colormap registry at import time."""
    cmaps = {}

    # 1. LinearSegmentedColormaps from _cm.datad
    for name, data in _cm.datad.items():
        cmap = LinearSegmentedColormap(name, data, N=256)
        cmaps[name] = cmap

    # 2. ListedColormaps from _cm_listed
    _listed_map = {
        'viridis':  '_viridis_data',
        'plasma':   '_plasma_data',
        'inferno':  '_inferno_data',
        'magma':    '_magma_data',
        'cividis':  '_cividis_data',
        'turbo':    '_turbo_data',
        'tab10':    '_tab10_data',
        'tab20':    '_tab20_data',
        'tab20b':   '_tab20b_data',
        'tab20c':   '_tab20c_data',
        'Set1':     '_Set1_data',
        'Set2':     '_Set2_data',
        'Set3':     '_Set3_data',
        'Paired':   '_Paired_data',
        'Accent':   '_Accent_data',
        'Dark2':    '_Dark2_data',
        'Pastel1':  '_Pastel1_data',
        'Pastel2':  '_Pastel2_data',
    }
    for cmap_name, attr in _listed_map.items():
        data = getattr(_cm_listed, attr, None)
        if data is not None:
            cmap = ListedColormap(data, name=cmap_name)
            cmaps[cmap_name] = cmap

    # 3. Add _r (reversed) variants for every registered colormap
    base_names = list(cmaps.keys())
    for name in base_names:
        r_name = name + '_r'
        if r_name not in cmaps:
            try:
                cmaps[r_name] = cmaps[name].reversed(name=r_name)
            except NotImplementedError:
                pass

    return ColormapRegistry(cmaps)


# Module-level registry — populated once at import time
_colormaps = _build_registry()


def get_cmap(name=None, lut=None):
    """Return a Colormap instance by name (or the default colormap).

    Parameters
    ----------
    name : str or Colormap or None
    lut : int, optional

    Returns
    -------
    Colormap
    """
    return _colormaps.get_cmap(name, lut)
```

- [ ] **Step 3: Run registry tests**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "get_cmap or register or registry or all_colormaps" -v --tb=short
```
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add python/matplotlib/cm.py
git commit -m "feat: add cm.py — ColormapRegistry, _colormaps, get_cmap"
```

---

### Task 9: cm.py — ScalarMappable

**Files:**
- Modify: `python/matplotlib/cm.py` (append ScalarMappable class)

- [ ] **Step 1: Run ScalarMappable tests to confirm they fail**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "scalar_mappable" -v --tb=line
```
Expected: fail with `ImportError: cannot import name 'ScalarMappable'`

- [ ] **Step 2: Append ScalarMappable to `python/matplotlib/cm.py`**

```python

class ScalarMappable:
    """Mixin for artists that map scalar data to colors.

    Adapted from upstream matplotlib/cm.py ScalarMappable.
    Event/callback infrastructure removed.
    """

    def __init__(self, norm=None, cmap=None):
        """
        Parameters
        ----------
        norm : Normalize or None
        cmap : str or Colormap or None — defaults to rcParams['image.cmap']
        """
        self._A = None
        self.set_cmap(cmap)
        self.set_norm(norm)

    def set_array(self, A):
        """Set the data array."""
        import numpy as np
        if A is not None:
            self._A = np.asarray(A, dtype=float)
        else:
            self._A = None

    def get_array(self):
        """Return the data array."""
        return self._A

    def set_cmap(self, cmap):
        """Set the colormap. Accepts name string or Colormap instance."""
        if cmap is None:
            import matplotlib
            cmap = matplotlib.rcParams.get('image.cmap', 'viridis')
        if isinstance(cmap, str):
            cmap = get_cmap(cmap)
        if not isinstance(cmap, Colormap):
            raise TypeError(f"cmap must be a Colormap or str, got {type(cmap)}")
        self._cmap = cmap

    def get_cmap(self):
        """Return the current Colormap."""
        return self._cmap

    def set_norm(self, norm):
        """Set the normalization. Accepts Normalize instance or None."""
        if norm is None:
            norm = Normalize()
        if not isinstance(norm, Normalize):
            raise TypeError(f"norm must be a Normalize instance or None, got {type(norm)}")
        self.norm = norm

    def get_norm(self):
        """Return the current Normalize instance."""
        return self.norm

    def get_clim(self):
        """Return (vmin, vmax)."""
        return self.norm.vmin, self.norm.vmax

    def set_clim(self, vmin=None, vmax=None):
        """Set vmin and vmax on the norm."""
        if vmin is not None:
            self.norm.vmin = float(vmin)
        if vmax is not None:
            self.norm.vmax = float(vmax)

    def autoscale(self):
        """Set vmin/vmax from the current data array."""
        import numpy as np
        if self._A is None:
            raise ValueError("autoscale() requires set_array() to be called first")
        flat = self._A.flatten().tolist()
        valid = [v for v in flat if not np.isnan(v)]
        if not valid:
            return
        self.norm.vmin = min(valid)
        self.norm.vmax = max(valid)

    def autoscale_None(self):
        """Set vmin/vmax only where not already set."""
        import numpy as np
        if self._A is None:
            return
        if self.norm.vmin is None or self.norm.vmax is None:
            flat = self._A.flatten().tolist()
            valid = [v for v in flat if not np.isnan(v)]
            if not valid:
                return
            if self.norm.vmin is None:
                self.norm.vmin = min(valid)
            if self.norm.vmax is None:
                self.norm.vmax = max(valid)

    def to_rgba(self, x, alpha=None, bytes=False, norm=True):
        """Map data array x to RGBA.

        Parameters
        ----------
        x : array-like
        alpha : float, optional
        bytes : bool
        norm : bool — if True, apply self.norm before mapping

        Returns
        -------
        ndarray of shape (*x.shape, 4), float64 or uint8
        """
        import numpy as np
        x = np.asarray(x, dtype=float)
        if norm:
            x = self.norm(x)
            if not hasattr(x, 'shape'):
                x = np.asarray(x, dtype=float)
        return self._cmap(x, alpha=alpha, bytes=bytes)
```

- [ ] **Step 3: Run ScalarMappable tests**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -k "scalar_mappable" -v
```
Expected: all 4 PASS

- [ ] **Step 4: Commit**

```bash
git add python/matplotlib/cm.py
git commit -m "feat: add ScalarMappable to cm.py"
```

---

### Task 10: Run the full test suite

**Note on `__init__.py`:** Do NOT add `from matplotlib import cm` to `python/matplotlib/__init__.py`. All tests use `from matplotlib import cm` (submodule import), which works without modifying `__init__.py`. Adding the eager import would run `_build_registry()` — constructing ~300 colormap objects — at every `import matplotlib`, hurting WASM startup time. Leave `__init__.py` unchanged.

- [ ] **Step 1: Run the full test suite for new tests**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_cm_upstream.py -v
```
Expected: **20 passed**

- [ ] **Step 3: Run the full test suite (regression check)**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q
```
Expected: **≥ 868 passed** (848 baseline + 20 new), 0 failed

---

### Task 11: Final commit with counts

- [ ] **Step 1: Verify final counts**

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q --tb=no 2>&1 | tail -3
```
Expected: `868 passed` (or more if some colormaps added bonus tests), 0 failed.

- [ ] **Step 2: Spot-check a few colormaps**

```bash
target/debug/matplotlib-python -c "
from matplotlib import cm
import numpy as np

for name in ['viridis', 'plasma', 'hot', 'jet', 'Blues', 'tab10']:
    cmap = cm.get_cmap(name)
    r = cmap(0.5)
    print(f'{name}: {r}')

print(f'Total registered: {len(cm._colormaps)}')
"
```
Expected: each prints a valid 4-tuple; total ≥ 200 (including _r variants)

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: colormaps sub-project A — ~150 named colormaps, Colormap hierarchy, ColormapRegistry, ScalarMappable"
```
