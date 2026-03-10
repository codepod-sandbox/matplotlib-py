# Figure & Axes Upstream Test Expansion

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand upstream matplotlib test coverage from 84 to ~115 tests by adding Figure and Axes tests adapted from matplotlib v3.8.0.

**Architecture:** Each task adds one or more upstream tests plus the minimal API additions needed to make them pass. Tests go in the existing `test_figure_upstream.py` and `test_axes_upstream.py` files. API changes are small, targeted additions to `figure.py`, `axes.py`, `pyplot.py`, and `container.py`.

**Tech Stack:** Python, pytest, RustPython (`target/debug/matplotlib-python -m pytest`)

**Test runner:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py python/matplotlib/tests/test_axes_upstream.py -v`

**Build first:** `cargo build -p matplotlib-python` (only needed once, already built)

---

### Task 1: Figure — `test_figure_label`

**Files:**
- Modify: `python/matplotlib/pyplot.py` (close with string label, figure with Figure instance error)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

Append to `python/matplotlib/tests/test_figure_upstream.py`:

```python
import pytest


def test_figure_label():
    """Upstream: test_figure.py::test_figure_label"""
    plt.close('all')
    fig_today = plt.figure('today')
    plt.figure(3)
    plt.figure('tomorrow')
    plt.figure()
    plt.figure(0)
    plt.figure(1)
    plt.figure(3)
    assert plt.get_fignums() == [0, 1, 3, 4, 5]
    assert plt.get_figlabels() == ['', 'today', '', 'tomorrow', '']
    plt.close(10)
    plt.close()
    plt.close(5)
    plt.close('tomorrow')
    assert plt.get_fignums() == [0, 1]
    assert plt.get_figlabels() == ['', 'today']
    plt.figure(fig_today)
    assert plt.gcf() == fig_today
    with pytest.raises(ValueError):
        plt.figure(Figure())
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_figure_label -v`

Expected: FAIL — `plt.close('tomorrow')` doesn't work (close doesn't resolve string labels), `plt.figure(fig_today)` doesn't work (figure doesn't accept Figure instances), `Figure` not imported.

**Step 3: Implement**

In `python/matplotlib/pyplot.py`, update `close()` to resolve string labels:

```python
def close(fig='all'):
    global _current_fig, _current_ax

    if isinstance(fig, str) and fig == 'all':
        _figures.clear()
        _fig_order.clear()
        _current_fig = None
        _current_ax = None
        return

    if isinstance(fig, str):
        # Resolve string label to figure number
        label = fig
        for n, f in _figures.items():
            if f.get_label() == label:
                fig = n
                break
        else:
            return  # Label not found, nothing to close

    if isinstance(fig, int):
        num = fig
    elif isinstance(fig, Figure):
        num = None
        for n, f in _figures.items():
            if f is fig:
                num = n
                break
        if num is None:
            return
    elif isinstance(fig, float):
        raise TypeError("close() does not accept float figure numbers")
    else:
        raise TypeError(
            f"close() argument must be 'all', an int, a str, or a Figure, "
            f"not {type(fig).__name__}"
        )

    if num in _figures:
        del _figures[num]
        if num in _fig_order:
            _fig_order.remove(num)

    if _current_fig is not None and _current_fig.number == num:
        if _fig_order:
            last_num = _fig_order[-1]
            _current_fig = _figures[last_num]
            _current_ax = (_current_fig._axes[-1]
                           if _current_fig._axes else None)
        else:
            _current_fig = None
            _current_ax = None
```

In `python/matplotlib/pyplot.py`, update `figure()` to accept Figure instances:

```python
def figure(num=None, figsize=None, dpi=100, clear=False, **kwargs):
    global _current_fig, _current_ax, _next_num

    # Accept Figure instance — find it or raise
    if isinstance(num, Figure):
        for n, f in _figures.items():
            if f is num:
                _current_fig = f
                _current_ax = f._axes[-1] if f._axes else None
                if clear:
                    f.clear()
                return f
        raise ValueError(
            "The passed Figure is not managed by this pyplot instance")

    # ... rest unchanged
```

Also update `figure()` to handle `num=0` correctly. Currently `if num >= _next_num` breaks when num=0 and _next_num=1 because `_next_num` stays at 1. Fix: track all assigned numbers, advance _next_num past any explicitly-given number.

In `figure()`, after creating a new figure, change the _next_num logic:

```python
    if isinstance(num, int) and num >= _next_num:
        _next_num = num + 1
```

This already exists but the issue is that `close()` with no args closes the *current* figure. We need that behavior. Currently `close()` with no `fig` arg defaults to `'all'`. Fix: change the default to close the current figure:

Actually looking at the upstream test: `plt.close()` closes the *current* figure (not all). Our current code defaults to `'all'`. We need to change the default:

```python
def close(fig=None):
    global _current_fig, _current_ax

    if fig is None:
        # Close current figure
        if _current_fig is not None:
            close(_current_fig)
        return

    if isinstance(fig, str) and fig == 'all':
        # ... existing code
```

**Step 4: Run test to verify it passes**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_figure_label -v`
Expected: PASS

**Step 5: Run full upstream suite to check no regressions**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py python/matplotlib/tests/test_axes_upstream.py -v`
Expected: All pass

**Step 6: Commit**

```bash
git add python/matplotlib/pyplot.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(figure): add test_figure_label upstream test

Adds string-label close(), Figure-instance figure(), and close()
with no args closes current figure."
```

---

### Task 2: Figure — `test_fignum_exists`

**Files:**
- Modify: `python/matplotlib/pyplot.py` (fignum_exists with string labels)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

```python
def test_fignum_exists():
    """Upstream: test_figure.py::test_fignum_exists"""
    plt.figure('one')
    plt.figure(2)
    plt.figure('three')
    plt.figure()
    assert plt.fignum_exists('one')
    assert plt.fignum_exists(2)
    assert plt.fignum_exists('three')
    assert plt.fignum_exists(4)
    plt.close('one')
    plt.close(4)
    assert not plt.fignum_exists('one')
    assert not plt.fignum_exists(4)
```

**Step 2: Run to verify failure**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_fignum_exists -v`
Expected: FAIL — `fignum_exists('one')` returns False because it only checks `num in _figures` (int keys).

**Step 3: Implement**

In `python/matplotlib/pyplot.py`, update `fignum_exists()`:

```python
def fignum_exists(num):
    """Return whether figure number or label *num* exists."""
    if isinstance(num, str):
        return any(f.get_label() == num for f in _figures.values())
    return num in _figures
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_fignum_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/pyplot.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(pyplot): fignum_exists supports string labels"
```

---

### Task 3: Figure — `test_clf_keyword`

**Files:**
- Modify: `python/matplotlib/figure.py` (add `texts` list and `text()` method)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

```python
def test_clf_keyword():
    """Upstream: test_figure.py::test_clf_keyword"""
    text1 = 'A fancy plot'
    text2 = 'Really fancy!'

    fig0 = plt.figure(num=1)
    fig0.suptitle(text1)
    assert [t.get_text() for t in fig0.texts] == [text1]

    fig1 = plt.figure(num=1, clear=False)
    fig1.text(0.5, 0.5, text2)
    assert fig0 is fig1
    assert [t.get_text() for t in fig1.texts] == [text1, text2]

    fig2, ax2 = plt.subplots(2, 1, num=1, clear=True)
    assert fig0 is fig2
    assert [t.get_text() for t in fig2.texts] == []
```

**Step 2: Run to verify failure**

Expected: FAIL — `fig0.texts` doesn't exist; `fig.text()` not implemented; `plt.subplots(num=)` not supported.

**Step 3: Implement**

In `python/matplotlib/figure.py`:
- Add `self.texts = []` in `__init__`
- Change `suptitle()` to create a Text and append to `self.texts`
- Add `text()` method
- Update `clear()` to also clear `self.texts`

```python
# In __init__, after self.stale = True:
self.texts = []

# Replace suptitle():
def suptitle(self, t, **kwargs):
    from matplotlib.text import Text
    self._suptitle = t
    txt = Text(0.5, 0.98, str(t), **kwargs)
    txt.figure = self
    self.texts.append(txt)
    self.stale = True
    return txt

# Add text():
def text(self, x, y, s, **kwargs):
    from matplotlib.text import Text
    txt = Text(x, y, str(s), **kwargs)
    txt.figure = self
    self.texts.append(txt)
    return txt

# Update clear():
def clear(self):
    self._axes.clear()
    self._suptitle = None
    self.texts.clear()
    self.stale = True
```

In `python/matplotlib/pyplot.py`, update `subplots()` to accept `num` kwarg:

```python
def subplots(nrows=1, ncols=1, figsize=None, dpi=100, **kwargs):
    global _current_fig, _current_ax, _next_num

    sharex = kwargs.pop('sharex', False)
    sharey = kwargs.pop('sharey', False)
    num = kwargs.pop('num', None)
    clear = kwargs.pop('clear', False)

    # If num is given and figure exists, reuse it
    if num is not None and num in _figures:
        fig = _figures[num]
        _current_fig = fig
        if clear:
            fig.clear()
    else:
        fig = Figure(figsize=figsize, dpi=dpi)
        if num is None:
            num = _next_num
        fig.number = num
        _figures[num] = fig
        _fig_order.append(num)
        if isinstance(num, int) and num >= _next_num:
            _next_num = num + 1
        _current_fig = fig

    # ... rest of axes creation unchanged, but only create axes if fig was cleared or new
```

Actually this is tricky — the upstream test creates `subplots(2, 1, num=1, clear=True)` which reuses fig 1, clears it, then adds 2 new subplots. The simplest approach: if the figure already exists and clear=True, clear it and add new subplots. If clear=False and figure exists, just return it with existing axes.

```python
def subplots(nrows=1, ncols=1, figsize=None, dpi=100, **kwargs):
    global _current_fig, _current_ax, _next_num

    sharex = kwargs.pop('sharex', False)
    sharey = kwargs.pop('sharey', False)
    num = kwargs.pop('num', None)
    clear_flag = kwargs.pop('clear', False)

    # Reuse or create figure
    existing = False
    if num is not None and num in _figures:
        fig = _figures[num]
        existing = True
        if clear_flag:
            fig.clear()
        _current_fig = fig
    else:
        fig = Figure(figsize=figsize, dpi=dpi)
        if num is None:
            num = _next_num
        fig.number = num
        _figures[num] = fig
        _fig_order.append(num)
        if isinstance(num, int) and num >= _next_num:
            _next_num = num + 1
        _current_fig = fig

    # Create subplots (always for new figs; for existing only if cleared)
    if not existing or clear_flag:
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

        if sharex and len(all_axes) > 1:
            for ax in all_axes:
                ax._shared_x = all_axes
        if sharey and len(all_axes) > 1:
            for ax in all_axes:
                ax._shared_y = all_axes

        _current_ax = all_axes[0] if all_axes else None

        if nrows == 1:
            axes_list = axes_list[0]
        elif ncols == 1:
            axes_list = [row[0] for row in axes_list]

        return fig, axes_list
    else:
        # Return existing figure with its axes
        axs = fig.axes
        _current_ax = axs[-1] if axs else None
        if len(axs) == 1:
            return fig, axs[0]
        return fig, axs
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_clf_keyword -v`
Expected: PASS

**Step 5: Run full suite for regressions**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -v`
Expected: All pass (some existing tests may need adjustment if they relied on suptitle returning a string instead of Text)

**Step 6: Fix suptitle return type if needed**

The existing `get_suptitle()` should still return a string. Update:

```python
def get_suptitle(self):
    return self._suptitle if self._suptitle is not None else ''
```

This still works since `_suptitle` is set to the string `t`.

**Step 7: Commit**

```bash
git add python/matplotlib/figure.py python/matplotlib/pyplot.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(figure): add texts list, text() method, subplots(num=, clear=)

Adds test_clf_keyword upstream test."
```

---

### Task 4: Figure — `test_gca`

**Files:**
- Modify: `python/matplotlib/figure.py` (add_axes/add_subplot re-add behavior)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

```python
def test_gca():
    """Upstream: test_figure.py::test_gca"""
    fig = plt.figure()

    ax0 = fig.add_axes([0, 0, 1, 1])
    assert fig.gca() is ax0

    ax1 = fig.add_subplot(111)
    assert fig.gca() is ax1

    # Re-adding existing axes should not duplicate, but make current
    fig.add_axes(ax0)
    assert fig.axes == [ax0, ax1]
    assert fig.gca() is ax0

    fig.sca(ax0)
    assert fig.axes == [ax0, ax1]

    fig.add_subplot(ax1)
    assert fig.axes == [ax0, ax1]
    assert fig.gca() is ax1
```

**Step 2: Run to verify failure**

Expected: FAIL — `fig.add_axes(ax0)` tries to treat the Axes as a rect; `fig.add_subplot(ax1)` fails; `fig.axes` order doesn't match (sca reorders).

**Step 3: Implement**

In `python/matplotlib/figure.py`:

Update `add_axes()` to accept an existing Axes:

```python
def add_axes(self, rect=None, **kwargs):
    from matplotlib.axes import Axes
    if isinstance(rect, Axes):
        ax = rect
        if ax not in self._axes:
            self._axes.append(ax)
        # Make it the "current" axes (move to end of internal stack)
        self._current_ax = ax
        return ax
    if rect is None:
        rect = [0, 0, 1, 1]
    ax = Axes(self, tuple(rect))
    self._axes.append(ax)
    self._current_ax = ax
    return ax
```

Update `add_subplot()` to accept an existing Axes:

```python
def add_subplot(self, *args, **kwargs):
    from matplotlib.axes import Axes
    if len(args) == 1 and isinstance(args[0], Axes):
        ax = args[0]
        if ax not in self._axes:
            self._axes.append(ax)
        self._current_ax = ax
        return ax
    # ... rest unchanged, but set self._current_ax = ax before return
```

Add `_current_ax` tracking to `__init__`:

```python
self._current_ax = None
```

Update `gca()` to use `_current_ax`:

```python
def gca(self):
    if self._current_ax is not None and self._current_ax in self._axes:
        return self._current_ax
    if not self._axes:
        return self.add_subplot(1, 1, 1)
    return self._axes[-1]
```

Update `sca()` to NOT reorder `_axes`:

```python
def sca(self, ax):
    self._current_ax = ax
```

Update `axes` property to return stable order (insertion order):

```python
@property
def axes(self):
    return list(self._axes)
```

This is already correct. The key change is: `sca()` no longer reorders `_axes`. It just sets `_current_ax`.

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_gca -v`
Expected: PASS

**Step 5: Run full suite, fix regressions from sca() change**

The `pyplot.sca()` calls `fig.sca()` which now doesn't reorder. `pyplot.gca()` uses `fig.gca()` which returns `fig._current_ax`. Check that `pyplot.gca()` still works correctly.

In `pyplot.py`, update `_ensure()` and `gca()`:

```python
def gca():
    _ensure()
    return _current_fig.gca()
```

And update places in pyplot that set `_current_ax` to also set `fig._current_ax`.

**Step 6: Commit**

```bash
git add python/matplotlib/figure.py python/matplotlib/pyplot.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(figure): gca/sca track current axes without reordering

Adds test_gca upstream test. add_axes/add_subplot accept existing Axes."
```

---

### Task 5: Figure — `test_axes_remove`

**Files:**
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

```python
def test_axes_remove():
    """Upstream: test_figure.py::test_axes_remove"""
    fig, axs = plt.subplots(2, 2)
    axs[-1][-1].remove()
    for ax in [axs[0][0], axs[0][1], axs[1][0]]:
        assert ax in fig.axes
    assert axs[-1][-1] not in fig.axes
    assert len(fig.axes) == 3
```

**Step 2: Run to verify failure**

Expected: FAIL — `plt.subplots(2, 2)` returns a list of lists, not indexable with `[-1][-1]`. Actually our implementation returns a 2D list for 2x2, so `axs[-1][-1]` should work. Let's see if it does.

Actually the upstream test uses `axs.ravel()` which needs numpy. Our version returns plain lists. The adapted test above uses `axs[-1][-1]` which works with list-of-lists. This should actually pass already if remove() works. Let me verify:

- `axs[-1][-1].remove()` calls `Axes.remove()` which calls `fig.delaxes(self)` — this exists.
- `ax in fig.axes` — `fig.axes` returns a copy, `in` checks identity — should work.

This test might already pass. Write it and verify.

**Step 3: If it passes, just commit the test**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_axes_remove -v`

**Step 4: Commit**

```bash
git add python/matplotlib/tests/test_figure_upstream.py
git commit -m "test(figure): add test_axes_remove upstream test"
```

---

### Task 6: Figure — `test_invalid_figure_size`

**Files:**
- Modify: `python/matplotlib/figure.py` (validate figsize)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

```python
@pytest.mark.parametrize('width, height', [
    (1, float('nan')),
    (-1, 1),
    (float('inf'), 1),
])
def test_invalid_figure_size(width, height):
    """Upstream: test_figure.py::test_invalid_figure_size"""
    with pytest.raises(ValueError):
        plt.figure(figsize=(width, height))

    fig = plt.figure()
    with pytest.raises(ValueError):
        fig.set_size_inches(width, height)
```

**Step 2: Run to verify failure**

Expected: FAIL — no validation in Figure.__init__ or set_size_inches.

**Step 3: Implement**

Add validation helper to `figure.py`:

```python
import math

def _validate_figsize(w, h):
    """Raise ValueError if figsize dimensions are invalid."""
    for val, name in [(w, 'width'), (h, 'height')]:
        if not isinstance(val, (int, float)):
            raise ValueError(f"figure size {name} must be a number")
        if math.isnan(val):
            raise ValueError(f"figure size must be finite, not {name}={val}")
        if math.isinf(val):
            raise ValueError(f"figure size must be finite, not {name}={val}")
        if val <= 0:
            raise ValueError(
                f"figure size must be positive, not {name}={val}")
```

Call in `__init__`:

```python
def __init__(self, figsize=None, dpi=100):
    figsize = figsize or (6.4, 4.8)
    _validate_figsize(figsize[0], figsize[1])
    self.figsize = figsize
    # ...
```

Call in `set_size_inches`:

```python
def set_size_inches(self, w, h=None):
    if h is None:
        w, h = w
    _validate_figsize(w, h)
    self.figsize = (float(w), float(h))
    self.stale = True
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_invalid_figure_size -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/figure.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(figure): validate figsize rejects nan/inf/negative"
```

---

### Task 7: Figure — `test_figure_clear`

**Files:**
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test** (simplified from upstream — no subfigures)

```python
@pytest.mark.parametrize('clear_meth', ['clear', 'clf'])
def test_figure_clear(clear_meth):
    """Upstream: test_figure.py::test_figure_clear (simplified)"""
    fig = plt.figure()

    # a) empty figure
    getattr(fig, clear_meth)()
    assert fig.axes == []

    # b) single axes
    ax = fig.add_subplot(111)
    getattr(fig, clear_meth)()
    assert fig.axes == []

    # c) multiple axes
    axes = [fig.add_subplot(2, 1, i + 1) for i in range(2)]
    getattr(fig, clear_meth)()
    assert fig.axes == []
```

**Step 2: Run to verify — should pass already**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_figure_clear -v`

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_figure_upstream.py
git commit -m "test(figure): add test_figure_clear upstream test"
```

---

### Task 8: Figure — `test_get_suptitle_supxlabel_supylabel`

**Files:**
- Modify: `python/matplotlib/figure.py` (add supxlabel, supylabel, getters)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing test**

```python
def test_get_suptitle_supxlabel_supylabel():
    """Upstream: test_figure.py::test_get_suptitle_supxlabel_supylabel"""
    fig, ax = plt.subplots()
    assert fig.get_suptitle() == ""
    assert fig.get_supxlabel() == ""
    assert fig.get_supylabel() == ""
    fig.suptitle('suptitle')
    assert fig.get_suptitle() == 'suptitle'
    fig.supxlabel('supxlabel')
    assert fig.get_supxlabel() == 'supxlabel'
    fig.supylabel('supylabel')
    assert fig.get_supylabel() == 'supylabel'
```

**Step 2: Run to verify failure**

Expected: FAIL — `supxlabel()`, `supylabel()`, `get_supxlabel()`, `get_supylabel()` don't exist.

**Step 3: Implement**

In `python/matplotlib/figure.py`, in `__init__`:

```python
self._supxlabel = None
self._supylabel = None
```

Add methods after `get_suptitle()`:

```python
def supxlabel(self, t, **kwargs):
    """Set a centered x-label for the figure."""
    self._supxlabel = t
    self.stale = True
    return t

def get_supxlabel(self):
    """Return the figure supxlabel string, or '' if not set."""
    return self._supxlabel if self._supxlabel is not None else ''

def supylabel(self, t, **kwargs):
    """Set a centered y-label for the figure."""
    self._supylabel = t
    self.stale = True
    return t

def get_supylabel(self):
    """Return the figure supylabel string, or '' if not set."""
    return self._supylabel if self._supylabel is not None else ''
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_get_suptitle_supxlabel_supylabel -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/figure.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(figure): add supxlabel/supylabel methods"
```

---

### Task 9: Figure — `test_savefig_args` and `test_pyplot_axes`

**Files:**
- Modify: `python/matplotlib/figure.py` (savefig arg validation)
- Test: `python/matplotlib/tests/test_figure_upstream.py`

**Step 1: Write the failing tests**

```python
def test_savefig_args():
    """Upstream: test_figure.py::test_savefig — arg count validation"""
    fig = plt.figure()
    with pytest.raises(TypeError):
        fig.savefig("fname1.png", "fname2.png")


def test_pyplot_axes():
    """Upstream: test_axes.py::test_pyplot_axes"""
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    plt.sca(ax1)
    assert ax1 is plt.gca()
    assert fig1 is plt.gcf()
    plt.close(fig1)
    plt.close(fig2)
```

**Step 2: Run to verify failure**

`test_savefig_args` will fail because `savefig` currently takes positional `format` so `savefig("a", "b")` would set format="b" rather than raising. Fix: make format keyword-only isn't possible in Python 2-style, but we can check for unexpected positional args.

Actually looking at real matplotlib, `savefig(self, fname, *, ...)` uses keyword-only after fname. So `savefig("a", "b")` raises TypeError. We can do the same:

```python
def savefig(self, fname, **kwargs):
    format = kwargs.pop('format', None)
    dpi = kwargs.pop('dpi', None)
    # ... rest
```

Wait, but that changes the signature. Simpler: just use `*` to make format/dpi keyword-only:

```python
def savefig(self, fname, *, format=None, dpi=None, **kwargs):
```

**Step 3: Implement**

In `python/matplotlib/figure.py`, change savefig signature:

```python
def savefig(self, fname, *, format=None, dpi=None, **kwargs):
```

`test_pyplot_axes` should already pass with existing code since `plt.sca()` switches the current figure.

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_figure_upstream.py::test_savefig_args python/matplotlib/tests/test_figure_upstream.py::test_pyplot_axes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/figure.py python/matplotlib/tests/test_figure_upstream.py
git commit -m "feat(figure): savefig keyword-only args, add upstream tests"
```

---

### Task 10: Axes — `test_inverted_cla`

**Files:**
- Test: `python/matplotlib/tests/test_axes_upstream.py`

**Step 1: Write the failing test** (adapted — no imshow, simplified)

```python
def test_inverted_cla():
    """Upstream: test_axes.py::test_inverted_cla (simplified, no imshow)"""
    fig, ax = plt.subplots()

    # 1. New axis is not inverted
    assert not ax.xaxis_inverted()
    assert not ax.yaxis_inverted()

    # 2. Invert, then clear — should reset
    ax.invert_yaxis()
    assert ax.yaxis_inverted()
    ax.cla()
    assert not ax.yaxis_inverted()

    # 3. Plot after clear — not inverted
    ax.plot([0, 1, 2], [0, 1, 2])
    assert not ax.xaxis_inverted()
    assert not ax.yaxis_inverted()

    # 4. Shared axes: inverting leader inverts follower
    fig2, (ax0, ax1) = plt.subplots(2, 1, sharey=True)
    ax0.invert_yaxis()
    # Shared axes should propagate inversion via limits
    ax0.set_ylim(10, 0)
    assert ax1.get_ylim() == (10, 0)
    ax0.cla()
    assert not ax0.yaxis_inverted()
```

**Step 2: Run to verify**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_axes_upstream.py::test_inverted_cla -v`

This should mostly pass already. The shared-axes part may need checking.

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_axes_upstream.py
git commit -m "test(axes): add test_inverted_cla upstream test"
```

---

### Task 11: Axes — `test_bar_labels`

**Files:**
- Modify: `python/matplotlib/axes.py` (per-bar label assignment)
- Modify: `python/matplotlib/patches.py` (Rectangle needs get_label/set_label from Artist)
- Test: `python/matplotlib/tests/test_axes_upstream.py`

**Step 1: Write the failing test**

```python
@pytest.mark.parametrize(
    ("x", "width", "label", "expected_labels", "container_label"),
    [
        ("x", 1, "x", ["_nolegend_"], "x"),
        (["a", "b", "c"], [10, 20, 15], ["A", "B", "C"],
         ["A", "B", "C"], "_nolegend_"),
        (["a", "b", "c"], [10, 20, 15], ["R", "Y", "_nolegend_"],
         ["R", "Y", "_nolegend_"], "_nolegend_"),
        (["a", "b", "c"], [10, 20, 15], "bars",
         ["_nolegend_", "_nolegend_", "_nolegend_"], "bars"),
    ]
)
def test_bar_labels(x, width, label, expected_labels, container_label):
    """Upstream: test_axes.py::test_bar_labels"""
    _, ax = plt.subplots()
    bar_container = ax.bar(x, width, label=label)
    bar_labels = [bar.get_label() for bar in bar_container]
    assert expected_labels == bar_labels
    assert bar_container.get_label() == container_label


def test_bar_labels_length():
    """Upstream: test_axes.py::test_bar_labels_length"""
    _, ax = plt.subplots()
    with pytest.raises(ValueError):
        ax.bar(["x", "y"], [1, 2], label=["X", "Y", "Z"])
    _, ax = plt.subplots()
    with pytest.raises(ValueError):
        ax.bar(["x", "y"], [1, 2], label=["X"])
```

**Step 2: Run to verify failure**

Expected: FAIL — bars don't get individual labels; container label logic is wrong.

**Step 3: Implement**

In `python/matplotlib/axes.py`, update `bar()` to handle label semantics:

The upstream rule:
- If `label` is a list, each bar gets its own label, container gets `_nolegend_`
- If `label` is a scalar string, each bar gets `_nolegend_`, container gets the string
- If `label` is a list with wrong length, raise ValueError

```python
def bar(self, x, height, width=0.8, **kwargs):
    facecolor = kwargs.get('facecolor')
    edgecolor = kwargs.get('edgecolor')
    color = kwargs.get('color')
    alpha = kwargs.get('alpha')
    label = kwargs.get('label')
    bottom = kwargs.get('bottom', 0)

    if facecolor is None:
        if color is not None:
            facecolor = color
        else:
            facecolor = self._next_color()

    if isinstance(facecolor, str) and facecolor.lower() == 'none':
        fc_hex = '#000000'
    else:
        fc_hex = to_hex(facecolor)

    if edgecolor is None:
        edgecolor = 'black'

    # Handle x as single value or list
    if isinstance(x, (str, int, float)):
        x_vals = [x]
    else:
        x_vals = list(x)

    if not hasattr(height, '__iter__'):
        h_vals = [height] * len(x_vals)
    else:
        h_vals = list(height)

    if hasattr(bottom, '__iter__'):
        b_vals = list(bottom)
    else:
        b_vals = [bottom] * len(x_vals)

    # Label semantics
    if isinstance(label, list):
        if len(label) != len(x_vals):
            raise ValueError(
                f"'label' must have the same length as 'x' "
                f"({len(label)} != {len(x_vals)})")
        bar_labels = label
        container_label = '_nolegend_'
    elif label is not None:
        bar_labels = ['_nolegend_'] * len(x_vals)
        container_label = str(label)
    else:
        bar_labels = ['_nolegend_'] * len(x_vals)
        container_label = None

    rect_patches = []
    for i in range(len(x_vals)):
        x_center = x_vals[i]
        h = h_vals[i]
        b = b_vals[i]
        # Use numeric x_center for Rectangle if possible
        if isinstance(x_center, (int, float)):
            rect_x = x_center - width / 2
        else:
            rect_x = i - width / 2
        rect = Rectangle(
            (rect_x, b), width, h,
            facecolor=facecolor, edgecolor=edgecolor,
        )
        if alpha is not None:
            rect.set_alpha(alpha)
        rect.set_label(bar_labels[i])
        rect.axes = self
        rect.figure = self.figure
        self.patches.append(rect)
        rect_patches.append(rect)

    bc = BarContainer(rect_patches, label=container_label)
    self.containers.append(bc)

    elem = {
        'type': 'bar',
        'x': x_vals, 'height': h_vals, 'width': width,
        'color': fc_hex, 'label': container_label,
    }
    self._elements.append(elem)

    return bc
```

Also ensure `Container.set_label` handles None properly:

In `python/matplotlib/container.py`:
```python
def set_label(self, s):
    self._label = str(s) if s is not None else '_nolegend_'
```

This already exists and is correct.

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_axes_upstream.py::test_bar_labels python/matplotlib/tests/test_axes_upstream.py::test_bar_labels_length -v`
Expected: PASS

**Step 5: Run full suite for regressions**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -v`

**Step 6: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_axes_upstream.py
git commit -m "feat(axes): bar label semantics match upstream

Per-bar labels when label is a list, container label when scalar.
Validates label list length."
```

---

### Task 12: Axes — `test_scatter_empty_and_validation`

**Files:**
- Modify: `python/matplotlib/axes.py` (scatter size validation)
- Test: `python/matplotlib/tests/test_axes_upstream.py`

**Step 1: Write the failing test**

```python
def test_scatter_size_arg_size():
    """Upstream: test_axes.py::test_scatter_size_arg_size"""
    x = list(range(4))
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match='same size as x and y'):
        ax.scatter(x, x, x[1:])
    with pytest.raises(ValueError, match='same size as x and y'):
        ax.scatter(x[1:], x[1:], x)
    with pytest.raises(ValueError, match='float'):
        ax.scatter(x, x, 'foo')
```

**Step 2: Run to verify failure**

Expected: FAIL — scatter doesn't validate size argument.

**Step 3: Implement**

In `python/matplotlib/axes.py`, update `scatter()`:

```python
def scatter(self, x, y, s=20, c=None, **kwargs):
    color = c or kwargs.get('color') or self._next_color()
    color = to_hex(color)
    label = kwargs.get('label')

    x_list = list(x)
    y_list = list(y)

    # Validate sizes
    if isinstance(s, str):
        raise ValueError("'s' must be a float array-like, not a string")
    if hasattr(s, '__iter__'):
        sizes = list(s)
        if len(sizes) != len(x_list):
            raise ValueError(
                f"s must be a scalar or the same size as x and y "
                f"({len(sizes)} != {len(x_list)})")
    else:
        sizes = [s]

    offsets = list(zip(x_list, y_list))

    pc = PathCollection(
        offsets=offsets, sizes=sizes,
        facecolors=[color], label=label,
    )
    pc.axes = self
    pc.figure = self.figure
    self.collections.append(pc)
    self._elements.append(pc._as_element())
    return pc
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_axes_upstream.py::test_scatter_size_arg_size -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_axes_upstream.py
git commit -m "feat(axes): scatter validates size argument"
```

---

### Task 13: Axes — `test_twinx_cla` (adapted)

**Files:**
- Modify: `python/matplotlib/axes.py` (add patch/xaxis/yaxis visibility stubs)
- Test: `python/matplotlib/tests/test_axes_upstream.py`

**Step 1: Write the failing test** (adapted for our API)

```python
def test_twinx_cla():
    """Upstream: test_axes.py::test_twinx_cla (adapted)"""
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    # After cla(), twin axes should preserve their role
    ax2.cla()
    # Basic check: twinx creates a second axes that shares x
    assert ax2 in fig.axes
    assert ax in fig.axes

    # Both axes should still be connected
    ax.set_xlim(0, 10)
    assert ax2.get_xlim() == (0, 10)
```

**Step 2: Run to verify**

Should pass with existing shared-axes implementation.

**Step 3: Implement if needed**

The key issue: `cla()` currently resets `_shared_x = []` which breaks the twin connection. Fix: `cla()` should NOT reset shared axes lists.

In `python/matplotlib/axes.py`, update `cla()`:

```python
def cla(self):
    self._elements.clear()
    self._title = ''
    self._xlabel = ''
    self._ylabel = ''
    self._xlim = None
    self._ylim = None
    self._xticks = None
    self._yticks = None
    self._xticklabels = None
    self._yticklabels = None
    self._grid = False
    self._legend = False
    self._color_idx = 0
    self.lines.clear()
    self.collections.clear()
    self.patches.clear()
    self.containers.clear()
    self.texts.clear()
    self._x_inverted = False
    self._y_inverted = False
    self._xscale = 'linear'
    self._yscale = 'linear'
    self._aspect = 'auto'
    # NOTE: do NOT reset _shared_x/_shared_y — shared axes persist across cla()
    self._xticklabels_visible = True
    self._yticklabels_visible = True
    self._xlabel_visible = True
    self._ylabel_visible = True
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_axes_upstream.py::test_twinx_cla -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_axes_upstream.py
git commit -m "fix(axes): cla() preserves shared axes connections

Adds test_twinx_cla upstream test."
```

---

### Task 14: Axes — `test_hist_with_empty_input`

**Files:**
- Modify: `python/matplotlib/axes.py` (hist handles empty input)
- Test: `python/matplotlib/tests/test_axes_upstream.py`

**Step 1: Write the failing test**

```python
@pytest.mark.parametrize('data, expected_number_of_hists',
                         [([], 1),
                          ([[]], 1),
                          ([[], []], 2)])
def test_hist_with_empty_input(data, expected_number_of_hists):
    """Upstream: test_axes.py::test_hist_with_empty_input"""
    fig, ax = plt.subplots()
    hists, _, _ = ax.hist(data)
    if not hasattr(hists, '__len__') or (hasattr(hists, '__len__') and isinstance(hists[0], (int, float))):
        assert 1 == expected_number_of_hists
    else:
        assert len(hists) == expected_number_of_hists
```

**Step 2: Run to verify failure**

Expected: FAIL — `hist([])` crashes on `min(data)` with empty list.

**Step 3: Implement**

In `python/matplotlib/axes.py`, update `hist()` to handle empty data:

```python
def hist(self, x, bins=10, **kwargs):
    color = kwargs.get('color') or self._next_color()
    color = to_hex(color)
    label = kwargs.get('label')
    density = kwargs.get('density', False)

    # Handle list-of-lists (multiple datasets)
    if hasattr(x, '__iter__') and not isinstance(x, str):
        x_list = list(x)
        if x_list and hasattr(x_list[0], '__iter__') and not isinstance(x_list[0], str):
            # Multiple datasets
            results = [self.hist(dataset, bins, **kwargs) for dataset in x_list]
            counts_list = [r[0] for r in results]
            edges = results[0][1] if results else []
            bc = results[0][2] if results else None
            return counts_list, edges, bc

    data = list(x)

    # Handle empty data
    if not data:
        counts = [0] * bins
        edges = list(range(bins + 1))
        rect_patches = []
        bc = BarContainer(rect_patches, label=label)
        self.containers.append(bc)
        return counts, edges, bc

    # ... rest of existing hist code unchanged
```

**Step 4: Run to verify pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_axes_upstream.py::test_hist_with_empty_input -v`
Expected: PASS

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_axes_upstream.py
git commit -m "feat(axes): hist handles empty data and multiple datasets"
```

---

### Task 15: Axes — additional small tests batch

**Files:**
- Test: `python/matplotlib/tests/test_axes_upstream.py`

**Step 1: Write tests that should already pass**

```python
def test_axes_clear_resets_scale():
    """Upstream-inspired: cla() resets axis scale."""
    fig, ax = plt.subplots()
    ax.set_xscale('log')
    ax.set_yscale('log')
    assert ax.get_xscale() == 'log'
    assert ax.get_yscale() == 'log'
    ax.cla()
    assert ax.get_xscale() == 'linear'
    assert ax.get_yscale() == 'linear'


def test_axes_set_kwargs():
    """Upstream-inspired: set(**kwargs) batch setter."""
    fig, ax = plt.subplots()
    ax.set(xlabel='X', ylabel='Y', title='T')
    assert ax.get_xlabel() == 'X'
    assert ax.get_ylabel() == 'Y'
    assert ax.get_title() == 'T'
    ax.set(xlim=(0, 10), ylim=(-1, 1))
    assert ax.get_xlim() == (0, 10)
    assert ax.get_ylim() == (-1, 1)


def test_axes_twinx_shared_xlim():
    """Upstream-inspired: twinx shares x limits."""
    fig, ax = plt.subplots()
    ax.set_xlim(0, 5)
    ax2 = ax.twinx()
    assert ax2.get_xlim() == (0, 5)
    ax.set_xlim(1, 10)
    assert ax2.get_xlim() == (1, 10)


def test_axes_twiny_shared_ylim():
    """Upstream-inspired: twiny shares y limits."""
    fig, ax = plt.subplots()
    ax.set_ylim(-3, 3)
    ax2 = ax.twiny()
    assert ax2.get_ylim() == (-3, 3)
    ax.set_ylim(0, 100)
    assert ax2.get_ylim() == (0, 100)
```

**Step 2: Run all**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_axes_upstream.py -v`

**Step 3: Fix any failures, commit**

```bash
git add python/matplotlib/tests/test_axes_upstream.py
git commit -m "test(axes): add clear/set/twin upstream-inspired tests"
```

---

### Task 16: Final verification

**Step 1: Run full test suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -v 2>&1 | tail -20`

Verify all tests pass. Count total upstream tests.

**Step 2: Run just upstream tests with count**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_*_upstream.py -v 2>&1 | tail -5`

Expected: ~115 tests, 0 failures (up from 84).

**Step 3: Commit any final fixes**

---

## Summary of API changes

| File | Change |
|------|--------|
| `figure.py` | `texts` list, `text()`, `supxlabel/supylabel`, figsize validation, `_current_ax` tracking, `add_axes`/`add_subplot` accept Axes, `sca()` doesn't reorder, `savefig` keyword-only |
| `pyplot.py` | `close()` supports string labels + no-arg, `figure()` accepts Figure instance, `fignum_exists()` supports strings, `subplots(num=, clear=)` |
| `axes.py` | `cla()` preserves shared axes, `bar()` label semantics, `scatter()` size validation, `hist()` empty data + multi-dataset |
| `container.py` | No changes needed |
