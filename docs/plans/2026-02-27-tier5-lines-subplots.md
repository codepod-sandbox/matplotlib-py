# Tier 5: Line2D Properties & Subplot Layouts — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add test_lines.py (Line2D property tests) and test_subplots.py (shared axes, GridSpec, twinx/twiny, label_outer) with supporting implementation.

**Architecture:** Line2D already has full getter/setter API — just needs tests. Subplot features require new code: axis-linking mechanism for sharex/sharey, GridSpec class for advanced layouts, twinx/twiny for secondary axes, and label_outer() for hiding inner subplot labels.

**Tech Stack:** Pure Python, pytest. No numpy.

---

### Task 1: test_lines.py — Line2D construction & defaults

**Files:**
- Create: `python/matplotlib/tests/test_lines.py`

**Step 1: Write the tests**

```python
"""Tests for matplotlib.lines module — Line2D artist."""

import pytest

from matplotlib.lines import Line2D
from matplotlib.colors import to_hex


class TestLine2DConstruction:
    def test_basic_construction(self):
        """Line2D stores x/y data."""
        line = Line2D([1, 2, 3], [4, 5, 6])
        assert line.get_xdata() == [1, 2, 3]
        assert line.get_ydata() == [4, 5, 6]

    def test_default_color(self):
        """Default color is C0."""
        line = Line2D([0], [0])
        assert line.get_color() == 'C0'

    def test_default_linewidth(self):
        """Default linewidth is 1.5."""
        line = Line2D([0], [0])
        assert line.get_linewidth() == 1.5

    def test_default_linestyle(self):
        """Default linestyle is '-'."""
        line = Line2D([0], [0])
        assert line.get_linestyle() == '-'

    def test_default_marker(self):
        """Default marker is 'None' (string)."""
        line = Line2D([0], [0])
        assert line.get_marker() == 'None'

    def test_default_markersize(self):
        """Default markersize is 6.0."""
        line = Line2D([0], [0])
        assert line.get_markersize() == 6.0

    def test_default_fillstyle(self):
        """Default fillstyle is 'full'."""
        line = Line2D([0], [0])
        assert line.get_fillstyle() == 'full'

    def test_default_drawstyle(self):
        """Default drawstyle is 'default'."""
        line = Line2D([0], [0])
        assert line.get_drawstyle() == 'default'

    def test_explicit_kwargs(self):
        """Explicit kwargs override defaults."""
        line = Line2D([0], [0], color='red', linewidth=3.0,
                       linestyle='--', marker='o')
        assert line.get_color() == 'red'
        assert line.get_linewidth() == 3.0
        assert line.get_linestyle() == '--'
        assert line.get_marker() == 'o'

    def test_label(self):
        """Label is set via kwarg."""
        line = Line2D([0], [0], label='test')
        assert line.get_label() == 'test'

    def test_no_label(self):
        """No label kwarg gives empty label."""
        line = Line2D([0], [0])
        assert line.get_label() == ''
```

**Step 2: Run tests to verify they pass**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_lines.py -v`
Expected: All 11 PASS (Line2D already exists)

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_lines.py
git commit -m "test: add Line2D construction and defaults tests (Tier 5)"
```

---

### Task 2: test_lines.py — getter/setter round-trips & aliases

**Files:**
- Modify: `python/matplotlib/tests/test_lines.py`

**Step 1: Add tests to the file**

```python
class TestLine2DSetters:
    def test_set_get_color(self):
        line = Line2D([0], [0])
        line.set_color('blue')
        assert line.get_color() == 'blue'

    def test_set_c_alias(self):
        """set_c is an alias for set_color."""
        line = Line2D([0], [0])
        line.set_c('green')
        assert line.get_color() == 'green'

    def test_set_get_linewidth(self):
        line = Line2D([0], [0])
        line.set_linewidth(5.0)
        assert line.get_linewidth() == 5.0

    def test_set_lw_alias(self):
        """set_lw is an alias for set_linewidth."""
        line = Line2D([0], [0])
        line.set_lw(2.5)
        assert line.get_linewidth() == 2.5

    def test_set_get_linestyle(self):
        line = Line2D([0], [0])
        line.set_linestyle(':')
        assert line.get_linestyle() == ':'

    def test_set_ls_alias(self):
        """set_ls is an alias for set_linestyle."""
        line = Line2D([0], [0])
        line.set_ls('-.')
        assert line.get_linestyle() == '-.'

    def test_set_get_marker(self):
        line = Line2D([0], [0])
        line.set_marker('s')
        assert line.get_marker() == 's'

    def test_set_get_markersize(self):
        line = Line2D([0], [0])
        line.set_markersize(12.0)
        assert line.get_markersize() == 12.0

    def test_set_ms_alias(self):
        """set_ms is an alias for set_markersize."""
        line = Line2D([0], [0])
        line.set_ms(8.0)
        assert line.get_markersize() == 8.0

    def test_set_get_fillstyle(self):
        line = Line2D([0], [0])
        line.set_fillstyle('none')
        assert line.get_fillstyle() == 'none'

    def test_set_get_drawstyle(self):
        line = Line2D([0], [0])
        line.set_drawstyle('steps')
        assert line.get_drawstyle() == 'steps'
```

**Step 2: Run tests**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_lines.py -v`
Expected: All 22 PASS

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_lines.py
git commit -m "test: add Line2D getter/setter and alias tests (Tier 5)"
```

---

### Task 3: test_lines.py — data manipulation, _as_element, Artist integration

**Files:**
- Modify: `python/matplotlib/tests/test_lines.py`

**Step 1: Add tests**

```python
class TestLine2DData:
    def test_get_data(self):
        """get_data returns (xdata, ydata) tuple."""
        line = Line2D([1, 2], [3, 4])
        x, y = line.get_data()
        assert x == [1, 2]
        assert y == [3, 4]

    def test_set_data(self):
        """set_data replaces both x and y."""
        line = Line2D([1, 2], [3, 4])
        line.set_data([10, 20], [30, 40])
        assert line.get_xdata() == [10, 20]
        assert line.get_ydata() == [30, 40]

    def test_set_xdata(self):
        line = Line2D([1, 2], [3, 4])
        line.set_xdata([10, 20, 30])
        assert line.get_xdata() == [10, 20, 30]
        assert line.get_ydata() == [3, 4]  # unchanged

    def test_set_ydata(self):
        line = Line2D([1, 2], [3, 4])
        line.set_ydata([10, 20, 30])
        assert line.get_ydata() == [10, 20, 30]
        assert line.get_xdata() == [1, 2]  # unchanged

    def test_data_is_copy(self):
        """get_xdata/get_ydata return copies, not references."""
        line = Line2D([1, 2], [3, 4])
        xd = line.get_xdata()
        xd.append(999)
        assert line.get_xdata() == [1, 2]


class TestLine2DAsElement:
    def test_as_element_type(self):
        """_as_element returns dict with type='line'."""
        line = Line2D([1, 2], [3, 4], color='red')
        elem = line._as_element()
        assert elem['type'] == 'line'

    def test_as_element_data(self):
        line = Line2D([1, 2], [3, 4])
        elem = line._as_element()
        assert elem['x'] == [1, 2]
        assert elem['y'] == [3, 4]

    def test_as_element_color_hex(self):
        """Color is converted to hex in the element dict."""
        line = Line2D([0], [0], color='red')
        elem = line._as_element()
        assert elem['color'] == '#ff0000'

    def test_as_element_marker_none(self):
        """Marker 'None' becomes None in element dict."""
        line = Line2D([0], [0])
        elem = line._as_element()
        assert elem['marker'] is None

    def test_as_element_marker_set(self):
        line = Line2D([0], [0], marker='o')
        elem = line._as_element()
        assert elem['marker'] == 'o'


class TestLine2DArtist:
    def test_zorder(self):
        """Line2D default zorder is 2."""
        line = Line2D([0], [0])
        assert line.get_zorder() == 2

    def test_visible(self):
        """Line2D defaults to visible."""
        line = Line2D([0], [0])
        assert line.get_visible() is True

    def test_set_visible(self):
        line = Line2D([0], [0])
        line.set_visible(False)
        assert line.get_visible() is False

    def test_set_alpha(self):
        line = Line2D([0], [0])
        line.set_alpha(0.5)
        assert line.get_alpha() == 0.5

    def test_batch_set(self):
        """Artist.set() applies multiple properties."""
        line = Line2D([0], [0])
        line.set(color='red', linewidth=3.0, visible=False)
        assert line.get_color() == 'red'
        assert line.get_linewidth() == 3.0
        assert line.get_visible() is False

    def test_remove_from_axes(self):
        """Line2D.remove() removes from axes' lines list."""
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.plot([1, 2], [3, 4])
        line = lines[0]
        assert line in ax.lines
        line.remove()
        assert line not in ax.lines
        plt.close('all')
```

**Step 2: Run tests**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_lines.py -v`
Expected: All ~38 PASS

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_lines.py
git commit -m "test: add Line2D data, _as_element, and Artist integration tests (Tier 5)"
```

---

### Task 4: Implement sharex/sharey + tests

**Files:**
- Modify: `python/matplotlib/axes.py` — add `_shared_x`, `_shared_y` attrs and linking
- Modify: `python/matplotlib/pyplot.py` — add `sharex`/`sharey` params to `subplots()`
- Create: `python/matplotlib/tests/test_subplots.py`

**Step 1: Write the failing tests**

Create `python/matplotlib/tests/test_subplots.py`:

```python
"""Tests for subplot layouts — sharex, sharey, GridSpec, twinx, label_outer."""

import pytest

import matplotlib.pyplot as plt
from matplotlib.axes import Axes


class TestSharexSharey:
    def test_sharex_true(self):
        """sharex=True links x-limits across all subplots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax1.set_xlim(0, 10)
        assert ax2.get_xlim() == (0, 10)
        plt.close('all')

    def test_sharey_true(self):
        """sharey=True links y-limits across all subplots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax1.set_ylim(-5, 5)
        assert ax2.get_ylim() == (-5, 5)
        plt.close('all')

    def test_sharex_bidirectional(self):
        """Setting limits on either shared axes updates the other."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax2.set_xlim(100, 200)
        assert ax1.get_xlim() == (100, 200)
        plt.close('all')

    def test_sharey_bidirectional(self):
        """Setting limits on either shared axes updates the other."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax2.set_ylim(10, 20)
        assert ax1.get_ylim() == (10, 20)
        plt.close('all')

    def test_sharex_grid(self):
        """sharex=True on 2x2 grid links all x-limits."""
        fig, axes = plt.subplots(2, 2, sharex=True)
        axes[0][0].set_xlim(0, 100)
        for row in axes:
            for ax in row:
                assert ax.get_xlim() == (0, 100)
        plt.close('all')

    def test_no_share_independent(self):
        """Without share, axes have independent limits."""
        fig, (ax1, ax2) = plt.subplots(1, 2)
        ax1.set_xlim(0, 10)
        ax2.set_xlim(100, 200)
        assert ax1.get_xlim() == (0, 10)
        assert ax2.get_xlim() == (100, 200)
        plt.close('all')
```

**Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py::TestSharexSharey -v`
Expected: FAIL — subplots() doesn't accept sharex/sharey yet

**Step 3: Implement shared axes**

In `python/matplotlib/axes.py`, add to `__init__`:

```python
# Shared axes
self._shared_x = []  # list of axes sharing x-limits
self._shared_y = []  # list of axes sharing y-limits
```

Replace `set_xlim` to propagate to shared axes:

```python
def set_xlim(self, left=None, right=None, _propagating=False):
    # Validate: reject NaN or Inf
    for val, name in [(left, 'left'), (right, 'right')]:
        if val is not None:
            if math.isnan(val):
                raise ValueError(
                    f"Axis limits cannot be NaN: {name}={val}")
            if math.isinf(val):
                raise ValueError(
                    f"Axis limits cannot be Inf: {name}={val}")
    self._xlim = (left, right)
    # Propagate to shared axes
    if not _propagating:
        for other in self._shared_x:
            if other is not self:
                other.set_xlim(left, right, _propagating=True)
```

Same pattern for `set_ylim`:

```python
def set_ylim(self, bottom=None, top=None, _propagating=False):
    for val, name in [(bottom, 'bottom'), (top, 'top')]:
        if val is not None:
            if math.isnan(val):
                raise ValueError(
                    f"Axis limits cannot be NaN: {name}={val}")
            if math.isinf(val):
                raise ValueError(
                    f"Axis limits cannot be Inf: {name}={val}")
    self._ylim = (bottom, top)
    if not _propagating:
        for other in self._shared_y:
            if other is not self:
                other.set_ylim(bottom, top, _propagating=True)
```

In `python/matplotlib/pyplot.py`, update `subplots()`:

```python
def subplots(nrows=1, ncols=1, figsize=None, dpi=100, **kwargs):
    """Create a Figure and a set of subplots."""
    global _current_fig, _current_ax, _next_num

    sharex = kwargs.pop('sharex', False)
    sharey = kwargs.pop('sharey', False)

    fig = Figure(figsize=figsize, dpi=dpi)
    num = _next_num
    fig.number = num
    _figures[num] = fig
    _fig_order.append(num)
    _next_num = num + 1
    _current_fig = fig

    if nrows == 1 and ncols == 1:
        ax = fig.add_subplot(1, 1, 1)
        _current_ax = ax
        return fig, ax

    all_axes = []
    axes_list = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            ax = fig.add_subplot(nrows, ncols, r * ncols + c + 1)
            row.append(ax)
            all_axes.append(ax)
        axes_list.append(row)

    # Link shared axes
    if sharex and len(all_axes) > 1:
        for ax in all_axes:
            ax._shared_x = all_axes
    if sharey and len(all_axes) > 1:
        for ax in all_axes:
            ax._shared_y = all_axes

    _current_ax = axes_list[0][0] if axes_list else None

    if nrows == 1:
        axes_list = axes_list[0]
    elif ncols == 1:
        axes_list = [row[0] for row in axes_list]

    return fig, axes_list
```

**Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py -v`
Expected: All 6 PASS

**Step 5: Run full test suite to check for regressions**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/ -v`
Expected: All existing tests still pass

**Step 6: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/pyplot.py python/matplotlib/tests/test_subplots.py
git commit -m "feat: add sharex/sharey axis linking with tests (Tier 5)"
```

---

### Task 5: Implement twinx/twiny + tests

**Files:**
- Modify: `python/matplotlib/axes.py` — add `twinx()` and `twiny()` methods
- Modify: `python/matplotlib/tests/test_subplots.py` — add twin axes tests

**Step 1: Write the failing tests**

Add to `python/matplotlib/tests/test_subplots.py`:

```python
class TestTwinAxes:
    def test_twinx_creates_axes(self):
        """twinx() creates a new Axes on the same Figure."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        assert isinstance(ax2, Axes)
        assert ax2.figure is fig
        plt.close('all')

    def test_twinx_shares_x(self):
        """twinx() shares x-axis with parent."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.set_xlim(0, 10)
        assert ax2.get_xlim() == (0, 10)
        plt.close('all')

    def test_twinx_independent_y(self):
        """twinx() has independent y-axis."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.set_ylim(0, 10)
        ax2.set_ylim(100, 200)
        assert ax1.get_ylim() == (0, 10)
        assert ax2.get_ylim() == (100, 200)
        plt.close('all')

    def test_twiny_creates_axes(self):
        """twiny() creates a new Axes on the same Figure."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twiny()
        assert isinstance(ax2, Axes)
        assert ax2.figure is fig
        plt.close('all')

    def test_twiny_shares_y(self):
        """twiny() shares y-axis with parent."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twiny()
        ax1.set_ylim(0, 10)
        assert ax2.get_ylim() == (0, 10)
        plt.close('all')

    def test_twiny_independent_x(self):
        """twiny() has independent x-axis."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twiny()
        ax1.set_xlim(0, 10)
        ax2.set_xlim(100, 200)
        assert ax1.get_xlim() == (0, 10)
        assert ax2.get_xlim() == (100, 200)
        plt.close('all')
```

**Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py::TestTwinAxes -v`
Expected: FAIL — twinx/twiny not implemented

**Step 3: Implement twinx/twiny**

Add to `Axes` class in `python/matplotlib/axes.py` (after the `axis()` method, before batch setter):

```python
# ------------------------------------------------------------------
# Twin axes
# ------------------------------------------------------------------

def twinx(self):
    """Create a twin Axes sharing the x-axis."""
    ax2 = Axes(self.figure, self._position)
    self.figure._axes.append(ax2)
    # Share x-axis
    shared = self._shared_x if self._shared_x else [self]
    shared.append(ax2)
    for a in shared:
        a._shared_x = shared
    # Copy current x-limits
    if self._xlim is not None:
        ax2._xlim = self._xlim
    return ax2

def twiny(self):
    """Create a twin Axes sharing the y-axis."""
    ax2 = Axes(self.figure, self._position)
    self.figure._axes.append(ax2)
    # Share y-axis
    shared = self._shared_y if self._shared_y else [self]
    shared.append(ax2)
    for a in shared:
        a._shared_y = shared
    # Copy current y-limits
    if self._ylim is not None:
        ax2._ylim = self._ylim
    return ax2
```

**Step 4: Run tests**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_subplots.py
git commit -m "feat: add twinx/twiny with shared axis linking (Tier 5)"
```

---

### Task 6: Implement GridSpec + tests

**Files:**
- Create: `python/matplotlib/gridspec.py` — GridSpec class
- Modify: `python/matplotlib/__init__.py` or ensure importable
- Modify: `python/matplotlib/figure.py` — `add_subplot()` accepts SubplotSpec
- Modify: `python/matplotlib/tests/test_subplots.py` — GridSpec tests

**Step 1: Write the failing tests**

Add to `python/matplotlib/tests/test_subplots.py`:

```python
from matplotlib.gridspec import GridSpec, SubplotSpec


class TestGridSpec:
    def test_gridspec_creation(self):
        """GridSpec(nrows, ncols) creates a grid specification."""
        gs = GridSpec(2, 3)
        assert gs.nrows == 2
        assert gs.ncols == 3

    def test_gridspec_indexing(self):
        """gs[row, col] returns a SubplotSpec."""
        gs = GridSpec(2, 2)
        ss = gs[0, 0]
        assert isinstance(ss, SubplotSpec)

    def test_gridspec_row_slice(self):
        """gs[0, :] spans the full first row."""
        gs = GridSpec(2, 3)
        ss = gs[0, :]
        assert ss.rowspan == (0, 1)
        assert ss.colspan == (0, 3)

    def test_gridspec_col_slice(self):
        """gs[:, 0] spans the full first column."""
        gs = GridSpec(2, 3)
        ss = gs[:, 0]
        assert ss.rowspan == (0, 2)
        assert ss.colspan == (0, 1)

    def test_gridspec_block(self):
        """gs[0:2, 0:2] spans a 2x2 block."""
        gs = GridSpec(3, 3)
        ss = gs[0:2, 0:2]
        assert ss.rowspan == (0, 2)
        assert ss.colspan == (0, 2)

    def test_add_subplot_with_subplotspec(self):
        """Figure.add_subplot(SubplotSpec) creates an axes."""
        fig = plt.figure()
        gs = GridSpec(2, 2)
        ax = fig.add_subplot(gs[0, 0])
        assert isinstance(ax, Axes)
        assert ax.figure is fig
        plt.close('all')

    def test_gridspec_different_spans(self):
        """GridSpec supports axes with different spans."""
        fig = plt.figure()
        gs = GridSpec(2, 2)
        ax_top = fig.add_subplot(gs[0, :])    # top row, full width
        ax_bl = fig.add_subplot(gs[1, 0])     # bottom-left
        ax_br = fig.add_subplot(gs[1, 1])     # bottom-right
        assert len(fig.axes) == 3
        plt.close('all')
```

**Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py::TestGridSpec -v`
Expected: FAIL — gridspec module doesn't exist

**Step 3: Create `python/matplotlib/gridspec.py`**

```python
"""matplotlib.gridspec — GridSpec for advanced subplot layouts."""


class SubplotSpec:
    """Specification for the location of a subplot in a GridSpec."""

    def __init__(self, gridspec, rowspan, colspan):
        self._gridspec = gridspec
        self.rowspan = rowspan  # (start, stop)
        self.colspan = colspan  # (start, stop)

    def get_gridspec(self):
        return self._gridspec


class GridSpec:
    """A grid layout to place subplots within a figure.

    Usage::

        gs = GridSpec(2, 3)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1:3])
        ax3 = fig.add_subplot(gs[1, :])
    """

    def __init__(self, nrows, ncols, **kwargs):
        self.nrows = nrows
        self.ncols = ncols

    def __getitem__(self, key):
        """Return a SubplotSpec for the given grid position.

        Supports integer indexing and slicing:
            gs[0, 0]     -> single cell
            gs[0, :]     -> full row
            gs[:, 0]     -> full column
            gs[0:2, 0:2] -> block
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise IndexError("GridSpec index must be a 2-tuple (row, col)")

        row_key, col_key = key

        # Normalize row
        if isinstance(row_key, int):
            rowspan = (row_key, row_key + 1)
        elif isinstance(row_key, slice):
            start = row_key.start if row_key.start is not None else 0
            stop = row_key.stop if row_key.stop is not None else self.nrows
            rowspan = (start, stop)
        else:
            raise IndexError(f"Invalid row index: {row_key}")

        # Normalize col
        if isinstance(col_key, int):
            colspan = (col_key, col_key + 1)
        elif isinstance(col_key, slice):
            start = col_key.start if col_key.start is not None else 0
            stop = col_key.stop if col_key.stop is not None else self.ncols
            colspan = (start, stop)
        else:
            raise IndexError(f"Invalid col index: {col_key}")

        return SubplotSpec(self, rowspan, colspan)
```

**Step 4: Update `Figure.add_subplot()` to accept SubplotSpec**

In `python/matplotlib/figure.py`, update the import and method:

Add import at top:
```python
from matplotlib.gridspec import SubplotSpec
```

Replace `add_subplot`:
```python
def add_subplot(self, *args, **kwargs):
    """Add an Axes to the figure.

    Accepts:
        add_subplot(nrows, ncols, index)
        add_subplot(SubplotSpec)
    """
    if len(args) == 1 and isinstance(args[0], SubplotSpec):
        ss = args[0]
        pos = (ss.rowspan, ss.colspan)
    elif len(args) == 3:
        nrows, ncols, index = args
        pos = (nrows, ncols, index)
    elif len(args) == 0:
        pos = (1, 1, 1)
    else:
        nrows = args[0] if len(args) > 0 else kwargs.get('nrows', 1)
        ncols = args[1] if len(args) > 1 else kwargs.get('ncols', 1)
        index = args[2] if len(args) > 2 else kwargs.get('index', 1)
        pos = (nrows, ncols, index)

    ax = Axes(self, pos)
    self._axes.append(ax)
    return ax
```

**Step 5: Run tests**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py -v`
Expected: All PASS

**Step 6: Run full test suite**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/ -v`
Expected: No regressions

**Step 7: Commit**

```bash
git add python/matplotlib/gridspec.py python/matplotlib/figure.py python/matplotlib/tests/test_subplots.py
git commit -m "feat: add GridSpec with SubplotSpec indexing/slicing (Tier 5)"
```

---

### Task 7: Implement label_outer() + tests

**Files:**
- Modify: `python/matplotlib/axes.py` — add `label_outer()` method and tick label visibility
- Modify: `python/matplotlib/tests/test_subplots.py` — label_outer tests

**Step 1: Write the failing tests**

Add to `python/matplotlib/tests/test_subplots.py`:

```python
class TestLabelOuter:
    def test_label_outer_hides_inner_xlabels(self):
        """label_outer() hides x-tick labels on non-bottom subplots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax1.label_outer()
        assert ax1._xticklabels_visible is False
        assert ax1._xlabel_visible is False
        plt.close('all')

    def test_label_outer_keeps_bottom_xlabels(self):
        """label_outer() keeps x-tick labels on bottom subplots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax2.label_outer()
        assert ax2._xticklabels_visible is True
        assert ax2._xlabel_visible is True
        plt.close('all')

    def test_label_outer_hides_inner_ylabels(self):
        """label_outer() hides y-tick labels on non-left subplots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax2.label_outer()
        assert ax2._yticklabels_visible is False
        assert ax2._ylabel_visible is False
        plt.close('all')

    def test_label_outer_keeps_left_ylabels(self):
        """label_outer() keeps y-tick labels on left subplots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax1.label_outer()
        assert ax1._yticklabels_visible is True
        assert ax1._ylabel_visible is True
        plt.close('all')

    def test_label_outer_2x2(self):
        """label_outer() on a 2x2 grid hides inner labels correctly."""
        fig, axes = plt.subplots(2, 2, sharex=True, sharey=True)
        for row in axes:
            for ax in row:
                ax.label_outer()

        # Top-left: keep y-labels, hide x-labels
        assert axes[0][0]._yticklabels_visible is True
        assert axes[0][0]._xticklabels_visible is False

        # Top-right: hide both y and x labels
        assert axes[0][1]._yticklabels_visible is False
        assert axes[0][1]._xticklabels_visible is False

        # Bottom-left: keep both
        assert axes[1][0]._yticklabels_visible is True
        assert axes[1][0]._xticklabels_visible is True

        # Bottom-right: keep x, hide y
        assert axes[1][1]._yticklabels_visible is False
        assert axes[1][1]._xticklabels_visible is True
        plt.close('all')
```

**Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py::TestLabelOuter -v`
Expected: FAIL — label_outer() not implemented

**Step 3: Implement label_outer()**

In `python/matplotlib/axes.py`, add visibility attrs to `__init__`:

```python
# Tick/label visibility (for label_outer)
self._xticklabels_visible = True
self._yticklabels_visible = True
self._xlabel_visible = True
self._ylabel_visible = True
```

Add `label_outer()` method to `Axes` class (after `axis()` method):

```python
def label_outer(self):
    """Only show outer labels and tick labels for subplots.

    Hides x-axis labels/ticks if this is not a bottom-row subplot,
    and y-axis labels/ticks if this is not a left-column subplot.
    """
    pos = self._position
    # Determine grid position from (nrows, ncols, index) tuple
    if isinstance(pos, tuple) and len(pos) == 3:
        nrows, ncols, index = pos
        row = (index - 1) // ncols
        col = (index - 1) % ncols
        is_bottom = (row == nrows - 1)
        is_left = (col == 0)
    else:
        # Non-grid axes — keep all labels
        is_bottom = True
        is_left = True

    if not is_bottom:
        self._xticklabels_visible = False
        self._xlabel_visible = False

    if not is_left:
        self._yticklabels_visible = False
        self._ylabel_visible = False
```

**Step 4: Run tests**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py -v`
Expected: All PASS

**Step 5: Run full test suite**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/ -v`
Expected: No regressions

**Step 6: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_subplots.py
git commit -m "feat: add label_outer() for hiding inner subplot labels (Tier 5)"
```

---

### Task 8: Additional subplot tests — layout edge cases

**Files:**
- Modify: `python/matplotlib/tests/test_subplots.py` — edge cases and integration

**Step 1: Add tests**

```python
class TestSubplotLayout:
    def test_subplots_1x1(self):
        """subplots(1,1) returns single Axes, not list."""
        fig, ax = plt.subplots(1, 1)
        assert isinstance(ax, Axes)
        plt.close('all')

    def test_subplots_1xn_flat(self):
        """subplots(1, n) returns flat list, not nested."""
        fig, axes = plt.subplots(1, 3)
        assert isinstance(axes, list)
        assert len(axes) == 3
        assert all(isinstance(a, Axes) for a in axes)
        plt.close('all')

    def test_subplots_nx1_flat(self):
        """subplots(n, 1) returns flat list, not nested."""
        fig, axes = plt.subplots(3, 1)
        assert isinstance(axes, list)
        assert len(axes) == 3
        assert all(isinstance(a, Axes) for a in axes)
        plt.close('all')

    def test_subplots_nxm_nested(self):
        """subplots(n, m) with n>1 and m>1 returns nested list."""
        fig, axes = plt.subplots(2, 3)
        assert isinstance(axes, list)
        assert len(axes) == 2
        assert all(isinstance(row, list) for row in axes)
        assert all(len(row) == 3 for row in axes)
        plt.close('all')

    def test_subplots_figure_axes_count(self):
        """Figure has correct number of axes after subplots()."""
        fig, axes = plt.subplots(2, 3)
        assert len(fig.axes) == 6
        plt.close('all')

    def test_subplot_3digit(self):
        """subplot(211) creates subplot at position (2,1,1)."""
        fig = plt.figure()
        ax = plt.subplot(211)
        assert ax._position == (2, 1, 1)
        plt.close('all')

    def test_subplot_reuse(self):
        """subplot() reuses existing axes at same position."""
        fig = plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(211)
        assert ax1 is ax2
        plt.close('all')

    def test_add_subplot_with_gridspec(self):
        """add_subplot with GridSpec positions axes correctly."""
        from matplotlib.gridspec import GridSpec
        fig = plt.figure()
        gs = GridSpec(2, 2)
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        assert len(fig.axes) == 3
        plt.close('all')
```

**Step 2: Run tests**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/test_subplots.py -v`
Expected: All PASS (these test existing features + new features from earlier tasks)

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_subplots.py
git commit -m "test: add subplot layout edge cases and integration tests (Tier 5)"
```

---

### Task 9: Final full test suite run

**Step 1: Run full suite**

Run: `PYTHONPATH=python .venv/bin/python -m pytest python/matplotlib/tests/ -v`
Expected: All tests pass (~220+ total across 6 test files)

**Step 2: Summary**

New test files:
- `test_lines.py` — ~38 tests for Line2D properties
- `test_subplots.py` — ~30 tests for sharex/sharey, twinx/twiny, GridSpec, label_outer, layout

New implementation:
- `python/matplotlib/gridspec.py` — GridSpec + SubplotSpec
- Shared axis linking in `axes.py` (set_xlim/set_ylim propagation)
- `twinx()`/`twiny()` in `axes.py`
- `label_outer()` in `axes.py`
- `sharex`/`sharey` params in `pyplot.subplots()`
- `SubplotSpec` support in `figure.add_subplot()`
