# New Plot Types Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 7 new plot types (step, stairs, stackplot, stem, pie, boxplot, violinplot) to matplotlib-py.

**Architecture:** Each plot type is a method on `Axes` that creates existing artist objects (Line2D, Polygon, Rectangle, PathCollection) or a new `Wedge` patch. One new renderer primitive (`draw_wedge`) is needed for pie charts. A simple Gaussian KDE helper is needed for violinplot. All artists render via the existing `draw(renderer, layout)` pattern.

**Tech Stack:** Pure Python on RustPython. Run tests with `target/debug/matplotlib-python -m pytest`. No pip, no CPython.

**Key files:**
- `python/matplotlib/axes.py` — all 7 new Axes methods go here
- `python/matplotlib/patches.py` — Wedge class
- `python/matplotlib/container.py` — StemContainer
- `python/matplotlib/backend_bases.py` — draw_wedge on RendererBase
- `python/matplotlib/_svg_backend.py` — RendererSVG.draw_wedge
- `python/matplotlib/_pil_backend.py` — RendererPIL.draw_wedge
- `python/matplotlib/tests/test_plot_types.py` — all tests for new plot types

**Run command:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py -v`
**Full suite:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q`

---

### Task 1: draw_wedge renderer primitive

**Files:**
- Modify: `python/matplotlib/backend_bases.py:29-62`
- Modify: `python/matplotlib/_svg_backend.py`
- Modify: `python/matplotlib/_pil_backend.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing test**

Create `python/matplotlib/tests/test_plot_types.py`:

```python
"""Tests for new plot types: step, stairs, stackplot, stem, pie, boxplot, violinplot."""

import math


class TestDrawWedge:
    """Tests for the draw_wedge renderer primitive."""

    def test_renderer_base_raises(self):
        from matplotlib.backend_bases import RendererBase
        r = RendererBase(100, 100, 72)
        try:
            r.draw_wedge(50, 50, 40, 0, 90, '#ff0000')
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError:
            pass

    def test_svg_draw_wedge_quarter(self):
        from matplotlib._svg_backend import RendererSVG
        r = RendererSVG(200, 200, 72)
        r.draw_wedge(100, 100, 50, 0, 90, '#ff0000')
        svg = r.get_result()
        assert '<path' in svg
        assert '#ff0000' in svg

    def test_svg_draw_wedge_full_circle(self):
        from matplotlib._svg_backend import RendererSVG
        r = RendererSVG(200, 200, 72)
        r.draw_wedge(100, 100, 50, 0, 360, '#00ff00')
        svg = r.get_result()
        assert '#00ff00' in svg

    def test_pil_draw_wedge(self):
        from matplotlib._pil_backend import RendererPIL
        r = RendererPIL(200, 200, 72)
        r.draw_wedge(100, 100, 50, 0, 90, '#ff0000')
        result = r.get_result()
        assert isinstance(result, bytes)
        assert len(result) > 0
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestDrawWedge -v`
Expected: FAIL — draw_wedge not defined

**Step 3: Implement draw_wedge**

In `python/matplotlib/backend_bases.py`, add after `draw_polygon`:

```python
    def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
        """Draw a filled wedge (pie slice).

        Parameters
        ----------
        cx, cy : float
            Center in pixel coordinates.
        r : float
            Radius in pixels.
        start_angle, end_angle : float
            Angles in degrees, counterclockwise from 3 o'clock.
        color : str
            Fill color (hex).
        """
        raise NotImplementedError
```

In `python/matplotlib/_svg_backend.py`, add to RendererSVG:

```python
    def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
        import math
        # Handle full circle
        if abs(end_angle - start_angle) >= 360:
            self._parts.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
                f'fill="{color}" stroke="none"/>'
            )
            return
        # SVG arcs use clockwise angles from 3 o'clock, but y is flipped
        # Convert math angles (CCW) to SVG (CW, y-down)
        a1 = math.radians(-start_angle)
        a2 = math.radians(-end_angle)
        x1 = cx + r * math.cos(a1)
        y1 = cy + r * math.sin(a1)
        x2 = cx + r * math.cos(a2)
        y2 = cy + r * math.sin(a2)
        sweep = end_angle - start_angle
        large_arc = 1 if abs(sweep) > 180 else 0
        # SVG arc: sweep-flag=1 means clockwise in SVG coords
        self._parts.append(
            f'<path d="M {cx:.2f},{cy:.2f} L {x1:.2f},{y1:.2f} '
            f'A {r:.2f},{r:.2f} 0 {large_arc},0 {x2:.2f},{y2:.2f} Z" '
            f'fill="{color}" stroke="none"/>'
        )
```

In `python/matplotlib/_pil_backend.py`, add to RendererPIL:

```python
    def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
        col = _to_rgb_255(color)
        # PIL pieslice uses degrees, 0=3 o'clock, counterclockwise is negative
        # PIL angles go clockwise with y-down, so negate for math convention
        bbox = [(int(cx - r), int(cy - r)), (int(cx + r), int(cy + r))]
        # PIL start/end are in degrees, measured clockwise from 3 o'clock
        # Our angles are CCW from 3 o'clock, and y is down, so negate
        self._draw.pieslice(bbox, int(-end_angle), int(-start_angle), fill=col)
```

**Step 4: Run test to verify it passes**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestDrawWedge -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/backend_bases.py python/matplotlib/_svg_backend.py python/matplotlib/_pil_backend.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add draw_wedge renderer primitive for pie charts"
```

---

### Task 2: Wedge patch class

**Files:**
- Modify: `python/matplotlib/patches.py:167-193`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing test**

Append to `test_plot_types.py`:

```python
class TestWedgePatch:
    def test_wedge_creation(self):
        from matplotlib.patches import Wedge
        w = Wedge((0, 0), 1.0, 0, 90)
        assert w._center == (0, 0)
        assert w._r == 1.0
        assert w._theta1 == 0
        assert w._theta2 == 90

    def test_wedge_color(self):
        from matplotlib.patches import Wedge
        w = Wedge((0, 0), 1.0, 0, 90, facecolor='red')
        fc = w.get_facecolor()
        assert fc[0] == 1.0  # red channel

    def test_wedge_draw(self):
        from matplotlib.patches import Wedge
        from matplotlib._svg_backend import RendererSVG
        from matplotlib.backend_bases import AxesLayout
        w = Wedge((5, 5), 3.0, 0, 180, facecolor='blue')
        renderer = RendererSVG(200, 200, 72)
        layout = AxesLayout(10, 10, 180, 180, 0, 10, 0, 10)
        w.draw(renderer, layout)
        svg = renderer.get_result()
        assert '<path' in svg or '<circle' in svg
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestWedgePatch -v`
Expected: FAIL — Wedge not defined

**Step 3: Implement Wedge**

Add to `python/matplotlib/patches.py` after the `Polygon` class:

```python
class Wedge(Patch):
    """A wedge (pie slice) defined by center, radius, and two angles."""

    def __init__(self, center, r, theta1, theta2, **kwargs):
        self._center = tuple(center)
        self._r = r
        self._theta1 = theta1  # start angle in degrees
        self._theta2 = theta2  # end angle in degrees
        super().__init__(**kwargs)

    def get_center(self):
        return self._center

    def set_center(self, center):
        self._center = tuple(center)

    def get_r(self):
        return self._r

    def get_theta1(self):
        return self._theta1

    def get_theta2(self):
        return self._theta2

    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        cx_px = layout.sx(self._center[0])
        cy_px = layout.sy(self._center[1])
        # Compute pixel radius from data radius
        edge_px = layout.sx(self._center[0] + self._r)
        r_px = abs(edge_px - cx_px)
        if r_px <= 0:
            return
        renderer.draw_wedge(cx_px, cy_px, r_px,
                            self._theta1, self._theta2,
                            self._resolved_facecolor_hex())
```

**Step 4: Run test to verify it passes**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestWedgePatch -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/patches.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add Wedge patch class for pie chart slices"
```

---

### Task 3: StemContainer

**Files:**
- Modify: `python/matplotlib/container.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing test**

Append to `test_plot_types.py`:

```python
class TestStemContainer:
    def test_stem_container_creation(self):
        from matplotlib.container import StemContainer
        sc = StemContainer(('marker', ['s1', 's2'], 'base'), label='test')
        assert sc.markerline == 'marker'
        assert sc.stemlines == ['s1', 's2']
        assert sc.baseline == 'base'
        assert sc.get_label() == 'test'
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStemContainer -v`
Expected: FAIL — StemContainer not defined

**Step 3: Implement StemContainer**

Add to `python/matplotlib/container.py`:

```python
class StemContainer(Container):
    """Container for stem plot artists (markerline, stemlines, baseline)."""

    def __new__(cls, markerline_stemlines_baseline, label=None):
        return super().__new__(cls, markerline_stemlines_baseline)

    def __init__(self, markerline_stemlines_baseline, label=None):
        super().__init__(markerline_stemlines_baseline)
        self.markerline = markerline_stemlines_baseline[0]
        self.stemlines = markerline_stemlines_baseline[1]
        self.baseline = markerline_stemlines_baseline[2]
        if label is not None:
            self.set_label(label)
```

**Step 4: Run test to verify it passes**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStemContainer -v`
Expected: PASS (1 test)

**Step 5: Commit**

```bash
git add python/matplotlib/container.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add StemContainer for stem plot artists"
```

---

### Task 4: step() and stairs()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestStep:
    def test_step_pre(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.step([1, 2, 3], [1, 4, 2], where='pre')
        assert len(lines) == 1
        line = lines[0]
        # 'pre' means step happens before the point
        xd = line.get_xdata()
        yd = line.get_ydata()
        assert len(xd) == 5  # 2*(n-1) + 1 = 5

    def test_step_post(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.step([1, 2, 3], [1, 4, 2], where='post')
        line = lines[0]
        xd = line.get_xdata()
        assert len(xd) == 5

    def test_step_mid(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.step([1, 2, 3], [1, 4, 2], where='mid')
        line = lines[0]
        xd = line.get_xdata()
        assert len(xd) == 7  # 3*(n-1) + 1 = 7 for mid

    def test_step_returns_line_list(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.step([0, 1], [0, 1])
        assert isinstance(result, list)

    def test_step_invalid_where(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        try:
            ax.step([1, 2], [1, 2], where='invalid')
            assert False, "Should raise ValueError"
        except ValueError:
            pass


class TestStairs:
    def test_stairs_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        line = ax.stairs([3, 2, 5, 1])
        xd = line.get_xdata()
        yd = line.get_ydata()
        # 4 values -> 5 edges (0,1,2,3,4), staircase has 2*4 points
        assert len(xd) == 2 * 4

    def test_stairs_with_edges(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        line = ax.stairs([3, 2, 5], [10, 20, 30, 40])
        xd = line.get_xdata()
        assert xd[0] == 10
        assert xd[-1] == 40

    def test_stairs_is_line(self):
        from matplotlib.lines import Line2D
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stairs([1, 2, 3])
        assert isinstance(result, Line2D)
```

**Step 2: Run test to verify they fail**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStep -v`
Expected: FAIL — step not defined

**Step 3: Implement step() and stairs()**

In `python/matplotlib/axes.py`, add after the `axvline` method (after line 473):

```python
    def step(self, x, y, where='pre', **kwargs):
        """Step plot.

        Parameters
        ----------
        x, y : array-like
            Data coordinates.
        where : {'pre', 'post', 'mid'}, default 'pre'
            Where the step is placed relative to the data point.
        """
        x_list = list(x)
        y_list = list(y)
        n = len(x_list)
        if n < 2:
            return self.plot(x_list, y_list, **kwargs)

        if where == 'pre':
            # Step before the point: (x0,y0), (x1,y0), (x1,y1), (x2,y1), (x2,y2)
            xs, ys = [x_list[0]], [y_list[0]]
            for i in range(1, n):
                xs.extend([x_list[i], x_list[i]])
                ys.extend([y_list[i - 1], y_list[i]])
        elif where == 'post':
            # Step after the point: (x0,y0), (x0,y1), (x1,y1), (x1,y2), (x2,y2)
            xs, ys = [x_list[0]], [y_list[0]]
            for i in range(1, n):
                xs.extend([x_list[i - 1], x_list[i]])
                ys.extend([y_list[i], y_list[i]])
        elif where == 'mid':
            # Step at midpoint between x values
            xs, ys = [x_list[0]], [y_list[0]]
            for i in range(1, n):
                mid = (x_list[i - 1] + x_list[i]) / 2
                xs.extend([mid, mid, x_list[i]])
                ys.extend([y_list[i - 1], y_list[i], y_list[i]])
        else:
            raise ValueError(
                f"'where' must be 'pre', 'post', or 'mid', not {where!r}")

        return self.plot(xs, ys, **kwargs)

    def stairs(self, values, edges=None, **kwargs):
        """Staircase plot for pre-binned data.

        Parameters
        ----------
        values : array-like
            N bin values.
        edges : array-like, optional
            N+1 bin edges. Defaults to range(N+1).
        """
        vals = list(values)
        n = len(vals)
        if edges is None:
            edg = list(range(n + 1))
        else:
            edg = list(edges)

        # Build staircase: for each bin, horizontal line at value
        xs, ys = [], []
        for i in range(n):
            xs.extend([edg[i], edg[i + 1]])
            ys.extend([vals[i], vals[i]])

        kwargs.setdefault('linestyle', '-')
        line = Line2D(xs, ys,
                      color=kwargs.pop('color', None) or self._next_color(),
                      linewidth=kwargs.pop('linewidth', kwargs.pop('lw', 1.5)),
                      linestyle=kwargs.pop('linestyle', '-'),
                      label=kwargs.pop('label', None))
        line.axes = self
        line.figure = self.figure
        self.lines.append(line)
        return line
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStep python/matplotlib/tests/test_plot_types.py::TestStairs -v`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add step() and stairs() plot types"
```

---

### Task 5: stackplot()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestStackplot:
    def test_stackplot_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stackplot([1, 2, 3], [1, 2, 3], [2, 1, 2])
        assert len(result) == 2  # two layers -> two polygons

    def test_stackplot_returns_polygons(self):
        from matplotlib.patches import Polygon
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stackplot([1, 2, 3], [1, 2, 3])
        assert len(result) == 1
        assert isinstance(result[0], Polygon)

    def test_stackplot_labels(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stackplot([1, 2, 3], [1, 2, 3], [2, 1, 2],
                              labels=['A', 'B'])
        assert result[0].get_label() == 'A'
        assert result[1].get_label() == 'B'

    def test_stackplot_cumulative(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        polys = ax.stackplot([1, 2], [10, 20], [5, 10])
        # Second polygon should sit on top of first
        # Just check we got two patches in ax.patches
        assert len(ax.patches) >= 2
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStackplot -v`
Expected: FAIL — stackplot not defined

**Step 3: Implement stackplot()**

In `python/matplotlib/axes.py`, add after `stairs()`:

```python
    def stackplot(self, x, *args, labels=None, colors=None, **kwargs):
        """Stacked area plot.

        Parameters
        ----------
        x : array-like
            X coordinates.
        *args : array-like
            Each argument is a y-dataset to stack.
        labels : list of str, optional
            Labels for each layer.
        colors : list, optional
            Colors for each layer.
        """
        from matplotlib.patches import Polygon
        x_list = list(x)
        ys = [list(a) for a in args]
        n = len(x_list)

        if labels is None:
            labels = ['_nolegend_'] * len(ys)
        if colors is None:
            colors = [self._next_color() for _ in ys]
        else:
            colors = [to_hex(c) for c in colors]

        alpha = kwargs.get('alpha', 0.5)

        # Cumulative stacking
        baseline = [0.0] * n
        polys = []
        for i, y_data in enumerate(ys):
            top = [baseline[j] + y_data[j] for j in range(n)]

            # Build polygon: forward along top, backward along baseline
            verts = []
            for j in range(n):
                verts.append((x_list[j], top[j]))
            for j in range(n - 1, -1, -1):
                verts.append((x_list[j], baseline[j]))

            poly = Polygon(verts, facecolor=colors[i], edgecolor='none')
            poly.set_alpha(alpha)
            poly.set_label(labels[i])
            poly.axes = self
            poly.figure = self.figure
            self.patches.append(poly)
            polys.append(poly)

            baseline = top

        return polys
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStackplot -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add stackplot() for stacked area charts"
```

---

### Task 6: stem()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestStem:
    def test_stem_basic(self):
        from matplotlib.container import StemContainer
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stem([1, 2, 3], [4, 5, 6])
        assert isinstance(result, StemContainer)

    def test_stem_has_markerline(self):
        from matplotlib.lines import Line2D
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2, 3], [4, 5, 6])
        assert isinstance(sc.markerline, Line2D)

    def test_stem_has_baseline(self):
        from matplotlib.lines import Line2D
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2, 3], [4, 5, 6])
        assert isinstance(sc.baseline, Line2D)

    def test_stem_stemlines_count(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2, 3], [4, 5, 6])
        assert len(sc.stemlines) == 3

    def test_stem_y_only(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([4, 5, 6])
        # x defaults to [0, 1, 2]
        assert sc.markerline.get_xdata() == [0, 1, 2]

    def test_stem_custom_bottom(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2], [3, 4], bottom=1)
        # baseline should be at y=1
        assert sc.baseline.get_ydata() == [1, 1]
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStem -v`
Expected: FAIL — stem not defined

**Step 3: Implement stem()**

In `python/matplotlib/axes.py`, add the import at the top:

```python
from matplotlib.container import BarContainer, ErrorbarContainer, StemContainer
```

Then add the method after `stackplot()`:

```python
    def stem(self, *args, linefmt=None, markerfmt=None, basefmt=None,
             bottom=0, label=None, **kwargs):
        """Stem plot (lollipop chart).

        Parameters
        ----------
        *args : (y,) or (x, y)
        linefmt : str, optional
            Format for stem lines.
        markerfmt : str, optional
            Format for markers.
        basefmt : str, optional
            Format for baseline.
        bottom : float, default 0
            Y-position of the baseline.
        label : str, optional
        """
        if len(args) == 1:
            y_list = list(args[0])
            x_list = list(range(len(y_list)))
        elif len(args) == 2:
            x_list = list(args[0])
            y_list = list(args[1])
        else:
            raise TypeError(f"stem() takes 1-2 positional args, got {len(args)}")

        color = self._next_color()

        # Stem lines: vertical line from bottom to each y
        stemlines = []
        for i in range(len(x_list)):
            sl = Line2D([x_list[i], x_list[i]], [bottom, y_list[i]],
                        color=color, linewidth=1.0, linestyle='-')
            sl.set_label('_nolegend_')
            sl.axes = self
            sl.figure = self.figure
            self.lines.append(sl)
            stemlines.append(sl)

        # Marker line: markers at the tip of each stem
        markerline = Line2D(x_list, y_list, color=color,
                            linewidth=0, linestyle='None', marker='o')
        markerline.set_label('_nolegend_')
        markerline.axes = self
        markerline.figure = self.figure
        self.lines.append(markerline)

        # Baseline: horizontal line at bottom
        baseline = Line2D([min(x_list), max(x_list)], [bottom, bottom],
                          color='C3', linewidth=1.0, linestyle='-')
        baseline.set_label('_nolegend_')
        baseline.axes = self
        baseline.figure = self.figure
        self.lines.append(baseline)

        sc = StemContainer((markerline, stemlines, baseline), label=label)
        self.containers.append(sc)
        return sc
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestStem -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add stem() plot type"
```

---

### Task 7: pie()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestPie:
    def test_pie_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.pie([1, 2, 3])
        wedges, texts = result[0], result[1]
        assert len(wedges) == 3

    def test_pie_wedge_angles_sum_to_360(self):
        from matplotlib.patches import Wedge
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1, 1, 1, 1])
        assert len(wedges) == 4
        # Each wedge should span 90 degrees
        for w in wedges:
            assert isinstance(w, Wedge)
            span = w._theta2 - w._theta1
            assert abs(span - 90.0) < 0.01

    def test_pie_labels(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1, 2], labels=['A', 'B'])
        assert len(texts) == 2
        assert texts[0].get_text() == 'A'
        assert texts[1].get_text() == 'B'

    def test_pie_colors(self):
        from matplotlib.colors import to_hex
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1, 1], colors=['red', 'blue'])
        assert to_hex(wedges[0]._facecolor) == to_hex('red')
        assert to_hex(wedges[1]._facecolor) == to_hex('blue')

    def test_pie_startangle(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1], startangle=90)
        assert wedges[0]._theta1 == 90

    def test_pie_autopct(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie([1, 3], autopct='%1.0f%%')
        assert len(autotexts) == 2
        assert autotexts[0].get_text() == '25%'
        assert autotexts[1].get_text() == '75%'

    def test_pie_sets_equal_aspect(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.pie([1, 2, 3])
        assert ax.get_aspect() == 'equal'
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestPie -v`
Expected: FAIL — pie not defined

**Step 3: Implement pie()**

In `python/matplotlib/axes.py`, add the import at the top:

```python
from matplotlib.patches import Rectangle, Polygon, Wedge
```

(Remove the existing `from matplotlib.patches import Rectangle` line and replace with the above.)

Then add the method after `stem()`:

```python
    def pie(self, x, labels=None, colors=None, explode=None,
            autopct=None, startangle=0, counterclock=True, **kwargs):
        """Pie chart.

        Parameters
        ----------
        x : array-like
            Wedge sizes (will be normalized to sum to 360 degrees).
        labels : list of str, optional
        colors : list, optional
        explode : list of float, optional
            Fraction to offset each wedge from center.
        autopct : str or None, optional
            Format string for percentage labels (e.g. '%1.1f%%').
        startangle : float, default 0
            Starting angle in degrees (CCW from 3 o'clock).
        counterclock : bool, default True
        """
        vals = list(x)
        total = sum(vals)
        if total == 0:
            return [], []

        n = len(vals)
        if colors is None:
            colors = [DEFAULT_CYCLE[i % len(DEFAULT_CYCLE)] for i in range(n)]
        if labels is None:
            labels = [None] * n
        if explode is None:
            explode = [0.0] * n

        self.set_aspect('equal')

        # Center of pie in data coordinates
        cx, cy = 0.0, 0.0
        radius = 1.0

        wedges = []
        texts = []
        autotexts = [] if autopct else None

        angle = startangle
        for i in range(n):
            frac = vals[i] / total
            sweep = frac * 360.0
            if not counterclock:
                sweep = -sweep

            theta1 = angle
            theta2 = angle + sweep

            # Explode offset
            if explode[i] != 0:
                mid_angle = math.radians((theta1 + theta2) / 2)
                dx = explode[i] * math.cos(mid_angle)
                dy = explode[i] * math.sin(mid_angle)
            else:
                dx, dy = 0, 0

            w = Wedge((cx + dx, cy + dy), radius, theta1, theta2,
                      facecolor=colors[i], edgecolor='white')
            w.axes = self
            w.figure = self.figure
            self.patches.append(w)
            wedges.append(w)

            # Label text at 1.1 * radius
            if labels[i] is not None:
                mid_angle = math.radians((theta1 + theta2) / 2)
                lx = cx + dx + 1.2 * radius * math.cos(mid_angle)
                ly = cy + dy + 1.2 * radius * math.sin(mid_angle)
                ha = 'left' if math.cos(mid_angle) >= 0 else 'right'
                t = Text(lx, ly, labels[i], ha=ha, va='center', fontsize=11)
                t.axes = self
                t.figure = self.figure
                self.texts.append(t)
                texts.append(t)

            # Autopct text at 0.6 * radius
            if autopct is not None:
                pct = frac * 100
                mid_angle = math.radians((theta1 + theta2) / 2)
                px = cx + dx + 0.6 * radius * math.cos(mid_angle)
                py = cy + dy + 0.6 * radius * math.sin(mid_angle)
                pct_text = autopct % pct
                at = Text(px, py, pct_text, ha='center', va='center',
                          fontsize=10)
                at.axes = self
                at.figure = self.figure
                self.texts.append(at)
                autotexts.append(at)

            angle = theta2

        if autopct is not None:
            return wedges, texts, autotexts
        return wedges, texts
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestPie -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add pie() chart with wedges, labels, and autopct"
```

---

### Task 8: boxplot()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestBoxplot:
    def test_boxplot_single(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.boxplot([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        assert 'boxes' in result
        assert 'medians' in result
        assert 'whiskers' in result
        assert len(result['boxes']) == 1
        assert len(result['medians']) == 1

    def test_boxplot_multiple(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.boxplot([[1, 2, 3, 4, 5], [10, 20, 30, 40, 50]])
        assert len(result['boxes']) == 2
        assert len(result['medians']) == 2

    def test_boxplot_median_value(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.boxplot([1, 2, 3, 4, 5])
        # Median of [1,2,3,4,5] = 3
        med_line = result['medians'][0]
        assert med_line.get_ydata()[0] == 3

    def test_boxplot_fliers(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is an outlier
        result = ax.boxplot(data)
        assert 'fliers' in result
        # Should have at least one flier point
        assert len(result['fliers']) == 1

    def test_boxplot_no_fliers(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.boxplot([1, 2, 3, 4, 5], showfliers=False)
        assert len(result['fliers']) == 0

    def test_boxplot_vert_false(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.boxplot([1, 2, 3, 4, 5], vert=False)
        assert len(result['boxes']) == 1
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestBoxplot -v`
Expected: FAIL — boxplot not defined

**Step 3: Implement boxplot()**

Add helper functions near the bottom of `python/matplotlib/axes.py` (before the `_parse_plot_args` function):

```python
def _percentile(data, pct):
    """Simple percentile calculation (linear interpolation)."""
    sorted_d = sorted(data)
    n = len(sorted_d)
    if n == 0:
        return 0
    if n == 1:
        return sorted_d[0]
    k = (n - 1) * pct / 100.0
    f = int(k)
    c = f + 1
    if c >= n:
        return sorted_d[-1]
    return sorted_d[f] + (k - f) * (sorted_d[c] - sorted_d[f])


def _median(data):
    """Simple median calculation."""
    return _percentile(data, 50)
```

Then add the method on Axes after `pie()`:

```python
    def boxplot(self, x, vert=True, widths=None, showfliers=True,
                showmeans=False, **kwargs):
        """Box-and-whisker plot.

        Parameters
        ----------
        x : array-like or list of array-like
            Dataset(s). Single dataset or list of datasets.
        vert : bool, default True
            Vertical boxes if True, horizontal if False.
        widths : float or list, optional
            Box widths. Default 0.5.
        showfliers : bool, default True
            Show outlier points.
        showmeans : bool, default False
            Show mean markers.
        """
        # Normalize input: always a list of datasets
        if not hasattr(x[0], '__iter__'):
            datasets = [list(x)]
        else:
            datasets = [list(d) for d in x]

        n = len(datasets)
        if widths is None:
            widths = [0.5] * n
        elif not hasattr(widths, '__iter__'):
            widths = [widths] * n

        result = {
            'boxes': [],
            'medians': [],
            'whiskers': [],
            'caps': [],
            'fliers': [],
            'means': [],
        }

        for i, data in enumerate(datasets):
            pos = i + 1  # 1-indexed position
            w = widths[i]
            sorted_data = sorted(data)

            q1 = _percentile(sorted_data, 25)
            med = _median(sorted_data)
            q3 = _percentile(sorted_data, 75)
            iqr = q3 - q1

            # Whisker limits: 1.5 * IQR
            whisker_lo = q1 - 1.5 * iqr
            whisker_hi = q3 + 1.5 * iqr
            # Clamp to actual data range
            actual_lo = min(v for v in sorted_data if v >= whisker_lo)
            actual_hi = max(v for v in sorted_data if v <= whisker_hi)

            if vert:
                # Box: Rectangle from q1 to q3
                box = Rectangle((pos - w / 2, q1), w, q3 - q1,
                                facecolor='white', edgecolor='black')
                box.set_label('_nolegend_')
                box.axes = self
                box.figure = self.figure
                self.patches.append(box)
                result['boxes'].append(box)

                # Median line
                med_line = Line2D([pos - w / 2, pos + w / 2], [med, med],
                                  color='orange', linewidth=2.0)
                med_line.set_label('_nolegend_')
                med_line.axes = self
                med_line.figure = self.figure
                self.lines.append(med_line)
                result['medians'].append(med_line)

                # Whiskers
                lo_whisker = Line2D([pos, pos], [actual_lo, q1],
                                    color='black', linewidth=1.0, linestyle='--')
                lo_whisker.set_label('_nolegend_')
                lo_whisker.axes = self
                lo_whisker.figure = self.figure
                self.lines.append(lo_whisker)

                hi_whisker = Line2D([pos, pos], [q3, actual_hi],
                                    color='black', linewidth=1.0, linestyle='--')
                hi_whisker.set_label('_nolegend_')
                hi_whisker.axes = self
                hi_whisker.figure = self.figure
                self.lines.append(hi_whisker)
                result['whiskers'].extend([lo_whisker, hi_whisker])

                # Caps
                lo_cap = Line2D([pos - w / 4, pos + w / 4],
                                [actual_lo, actual_lo],
                                color='black', linewidth=1.0)
                lo_cap.set_label('_nolegend_')
                lo_cap.axes = self
                lo_cap.figure = self.figure
                self.lines.append(lo_cap)

                hi_cap = Line2D([pos - w / 4, pos + w / 4],
                                [actual_hi, actual_hi],
                                color='black', linewidth=1.0)
                hi_cap.set_label('_nolegend_')
                hi_cap.axes = self
                hi_cap.figure = self.figure
                self.lines.append(hi_cap)
                result['caps'].extend([lo_cap, hi_cap])

                # Fliers (outliers)
                if showfliers:
                    flier_pts = [v for v in sorted_data
                                 if v < actual_lo or v > actual_hi]
                    if flier_pts:
                        flier_x = [pos] * len(flier_pts)
                        pc = PathCollection(
                            offsets=list(zip(flier_x, flier_pts)),
                            sizes=[20], facecolors=['black'])
                        pc.set_label('_nolegend_')
                        pc.axes = self
                        pc.figure = self.figure
                        self.collections.append(pc)
                        result['fliers'].append(pc)

                # Means
                if showmeans:
                    mean_val = sum(data) / len(data)
                    mean_pc = PathCollection(
                        offsets=[(pos, mean_val)],
                        sizes=[50], facecolors=['green'])
                    mean_pc.set_label('_nolegend_')
                    mean_pc.axes = self
                    mean_pc.figure = self.figure
                    self.collections.append(mean_pc)
                    result['means'].append(mean_pc)

            else:
                # Horizontal boxplot: swap x <-> y
                box = Rectangle((q1, pos - w / 2), q3 - q1, w,
                                facecolor='white', edgecolor='black')
                box.set_label('_nolegend_')
                box.axes = self
                box.figure = self.figure
                self.patches.append(box)
                result['boxes'].append(box)

                med_line = Line2D([med, med], [pos - w / 2, pos + w / 2],
                                  color='orange', linewidth=2.0)
                med_line.set_label('_nolegend_')
                med_line.axes = self
                med_line.figure = self.figure
                self.lines.append(med_line)
                result['medians'].append(med_line)

                lo_whisker = Line2D([actual_lo, q1], [pos, pos],
                                    color='black', linewidth=1.0, linestyle='--')
                lo_whisker.set_label('_nolegend_')
                lo_whisker.axes = self
                lo_whisker.figure = self.figure
                self.lines.append(lo_whisker)

                hi_whisker = Line2D([q3, actual_hi], [pos, pos],
                                    color='black', linewidth=1.0, linestyle='--')
                hi_whisker.set_label('_nolegend_')
                hi_whisker.axes = self
                hi_whisker.figure = self.figure
                self.lines.append(hi_whisker)
                result['whiskers'].extend([lo_whisker, hi_whisker])

                lo_cap = Line2D([actual_lo, actual_lo],
                                [pos - w / 4, pos + w / 4],
                                color='black', linewidth=1.0)
                lo_cap.set_label('_nolegend_')
                lo_cap.axes = self
                lo_cap.figure = self.figure
                self.lines.append(lo_cap)

                hi_cap = Line2D([actual_hi, actual_hi],
                                [pos - w / 4, pos + w / 4],
                                color='black', linewidth=1.0)
                hi_cap.set_label('_nolegend_')
                hi_cap.axes = self
                hi_cap.figure = self.figure
                self.lines.append(hi_cap)
                result['caps'].extend([lo_cap, hi_cap])

                if showfliers:
                    flier_pts = [v for v in sorted_data
                                 if v < actual_lo or v > actual_hi]
                    if flier_pts:
                        flier_y = [pos] * len(flier_pts)
                        pc = PathCollection(
                            offsets=list(zip(flier_pts, flier_y)),
                            sizes=[20], facecolors=['black'])
                        pc.set_label('_nolegend_')
                        pc.axes = self
                        pc.figure = self.figure
                        self.collections.append(pc)
                        result['fliers'].append(pc)

        return result
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestBoxplot -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add boxplot() with boxes, whiskers, medians, and fliers"
```

---

### Task 9: violinplot()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestViolinplot:
    def test_violinplot_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        assert 'bodies' in result

    def test_violinplot_returns_bodies(self):
        from matplotlib.patches import Polygon
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([1, 2, 3, 4, 5])
        assert len(result['bodies']) == 1
        assert isinstance(result['bodies'][0], Polygon)

    def test_violinplot_multiple(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([[1, 2, 3, 4, 5], [10, 20, 30]])
        assert len(result['bodies']) == 2

    def test_violinplot_showmedians(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([1, 2, 3, 4, 5], showmedians=True)
        assert 'cmedians' in result
        assert len(result['cmedians']) == 1

    def test_violinplot_showmeans(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([1, 2, 3, 4, 5], showmeans=True)
        assert 'cmeans' in result
        assert len(result['cmeans']) == 1

    def test_violinplot_showextrema(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([1, 2, 3, 4, 5], showextrema=True)
        assert 'cmins' in result
        assert 'cmaxes' in result
        assert 'cbars' in result

    def test_violinplot_vert_false(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.violinplot([1, 2, 3, 4, 5], vert=False)
        assert len(result['bodies']) == 1
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestViolinplot -v`
Expected: FAIL — violinplot not defined

**Step 3: Implement KDE helper and violinplot()**

Add the KDE helper near the bottom of `python/matplotlib/axes.py` (near the other helper functions):

```python
def _gaussian_kde(data, n_points=100):
    """Simple Gaussian kernel density estimate.

    Uses Silverman's rule of thumb for bandwidth.
    Returns (positions, densities).
    """
    n = len(data)
    if n == 0:
        return [], []

    mean = sum(data) / n
    var = sum((v - mean) ** 2 for v in data) / n
    std = math.sqrt(var) if var > 0 else 1.0

    # Silverman's rule of thumb
    bw = 1.06 * std * (n ** -0.2) if std > 0 else 1.0

    lo = min(data) - 3 * bw
    hi = max(data) + 3 * bw
    step = (hi - lo) / (n_points - 1) if n_points > 1 else 1.0
    positions = [lo + i * step for i in range(n_points)]

    densities = []
    coeff = 1.0 / (n * bw * math.sqrt(2 * math.pi))
    for p in positions:
        total = 0.0
        for d in data:
            z = (p - d) / bw
            total += math.exp(-0.5 * z * z)
        densities.append(total * coeff)

    return positions, densities
```

Then add the `violinplot` method on Axes after `boxplot()`:

```python
    def violinplot(self, dataset, positions=None, vert=True, widths=0.5,
                   showmeans=False, showmedians=False, showextrema=True,
                   **kwargs):
        """Violin plot.

        Parameters
        ----------
        dataset : array-like or list of array-like
            Dataset(s).
        positions : array-like, optional
            Positions of violins (default: 1, 2, ..., N).
        vert : bool, default True
        widths : float, default 0.5
        showmeans : bool, default False
        showmedians : bool, default False
        showextrema : bool, default True
        """
        from matplotlib.patches import Polygon

        # Normalize: always list of datasets
        if not hasattr(dataset[0], '__iter__'):
            datasets = [list(dataset)]
        else:
            datasets = [list(d) for d in dataset]

        n = len(datasets)
        if positions is None:
            positions = list(range(1, n + 1))

        if not hasattr(widths, '__iter__'):
            widths = [widths] * n

        result = {
            'bodies': [],
            'cmeans': [],
            'cmedians': [],
            'cmins': [],
            'cmaxes': [],
            'cbars': [],
        }

        for i, data in enumerate(datasets):
            pos = positions[i]
            w = widths[i]
            color = self._next_color()

            # Compute KDE
            kde_pos, kde_dens = _gaussian_kde(data, n_points=50)
            if not kde_dens:
                continue

            # Scale densities so max width = widths/2
            max_d = max(kde_dens) if kde_dens else 1.0
            if max_d > 0:
                scale = (w / 2) / max_d
            else:
                scale = 1.0

            # Build mirrored polygon
            if vert:
                verts = []
                # Right side
                for j in range(len(kde_pos)):
                    verts.append((pos + kde_dens[j] * scale, kde_pos[j]))
                # Left side (reversed)
                for j in range(len(kde_pos) - 1, -1, -1):
                    verts.append((pos - kde_dens[j] * scale, kde_pos[j]))
            else:
                verts = []
                # Top side
                for j in range(len(kde_pos)):
                    verts.append((kde_pos[j], pos + kde_dens[j] * scale))
                # Bottom side (reversed)
                for j in range(len(kde_pos) - 1, -1, -1):
                    verts.append((kde_pos[j], pos - kde_dens[j] * scale))

            poly = Polygon(verts, facecolor=color, edgecolor='black')
            poly.set_alpha(0.5)
            poly.set_label('_nolegend_')
            poly.axes = self
            poly.figure = self.figure
            self.patches.append(poly)
            result['bodies'].append(poly)

            sorted_data = sorted(data)
            data_min = sorted_data[0]
            data_max = sorted_data[-1]
            data_mean = sum(data) / len(data)
            data_med = _median(data)

            if showextrema:
                if vert:
                    # Vertical bar through center
                    bar = Line2D([pos, pos], [data_min, data_max],
                                 color='black', linewidth=1.0)
                    bar.set_label('_nolegend_')
                    bar.axes = self
                    bar.figure = self.figure
                    self.lines.append(bar)
                    result['cbars'].append(bar)

                    # Min/max caps
                    min_line = Line2D([pos - w / 4, pos + w / 4],
                                     [data_min, data_min],
                                     color='black', linewidth=1.0)
                    min_line.set_label('_nolegend_')
                    min_line.axes = self
                    min_line.figure = self.figure
                    self.lines.append(min_line)
                    result['cmins'].append(min_line)

                    max_line = Line2D([pos - w / 4, pos + w / 4],
                                     [data_max, data_max],
                                     color='black', linewidth=1.0)
                    max_line.set_label('_nolegend_')
                    max_line.axes = self
                    max_line.figure = self.figure
                    self.lines.append(max_line)
                    result['cmaxes'].append(max_line)
                else:
                    bar = Line2D([data_min, data_max], [pos, pos],
                                 color='black', linewidth=1.0)
                    bar.set_label('_nolegend_')
                    bar.axes = self
                    bar.figure = self.figure
                    self.lines.append(bar)
                    result['cbars'].append(bar)

                    min_line = Line2D([data_min, data_min],
                                     [pos - w / 4, pos + w / 4],
                                     color='black', linewidth=1.0)
                    min_line.set_label('_nolegend_')
                    min_line.axes = self
                    min_line.figure = self.figure
                    self.lines.append(min_line)
                    result['cmins'].append(min_line)

                    max_line = Line2D([data_max, data_max],
                                     [pos - w / 4, pos + w / 4],
                                     color='black', linewidth=1.0)
                    max_line.set_label('_nolegend_')
                    max_line.axes = self
                    max_line.figure = self.figure
                    self.lines.append(max_line)
                    result['cmaxes'].append(max_line)

            if showmeans:
                if vert:
                    m = Line2D([pos - w / 4, pos + w / 4],
                               [data_mean, data_mean],
                               color='red', linewidth=1.5)
                else:
                    m = Line2D([data_mean, data_mean],
                               [pos - w / 4, pos + w / 4],
                               color='red', linewidth=1.5)
                m.set_label('_nolegend_')
                m.axes = self
                m.figure = self.figure
                self.lines.append(m)
                result['cmeans'].append(m)

            if showmedians:
                if vert:
                    m = Line2D([pos - w / 4, pos + w / 4],
                               [data_med, data_med],
                               color='blue', linewidth=1.5)
                else:
                    m = Line2D([data_med, data_med],
                               [pos - w / 4, pos + w / 4],
                               color='blue', linewidth=1.5)
                m.set_label('_nolegend_')
                m.axes = self
                m.figure = self.figure
                self.lines.append(m)
                result['cmedians'].append(m)

        return result
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestViolinplot -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add violinplot() with KDE, means, medians, and extrema"
```

---

### Task 10: pyplot wrappers

**Files:**
- Modify: `python/matplotlib/pyplot.py`
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing tests**

Append to `test_plot_types.py`:

```python
class TestPyplotWrappers:
    def test_step(self):
        import matplotlib.pyplot as plt
        result = plt.step([1, 2], [3, 4])
        assert result is not None

    def test_stairs(self):
        import matplotlib.pyplot as plt
        result = plt.stairs([1, 2, 3])
        assert result is not None

    def test_stackplot(self):
        import matplotlib.pyplot as plt
        result = plt.stackplot([1, 2], [3, 4])
        assert result is not None

    def test_stem(self):
        import matplotlib.pyplot as plt
        result = plt.stem([1, 2, 3])
        assert result is not None

    def test_pie(self):
        import matplotlib.pyplot as plt
        result = plt.pie([1, 2, 3])
        assert result is not None

    def test_boxplot(self):
        import matplotlib.pyplot as plt
        result = plt.boxplot([1, 2, 3, 4, 5])
        assert result is not None

    def test_violinplot(self):
        import matplotlib.pyplot as plt
        result = plt.violinplot([1, 2, 3, 4, 5])
        assert result is not None
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestPyplotWrappers -v`
Expected: FAIL — pyplot has no step/stairs/etc.

**Step 3: Add pyplot wrappers**

Check what's in pyplot currently, then add wrappers. In `python/matplotlib/pyplot.py`, add after existing plot wrappers:

```python
def step(x, y, where='pre', **kwargs):
    return gca().step(x, y, where=where, **kwargs)

def stairs(values, edges=None, **kwargs):
    return gca().stairs(values, edges=edges, **kwargs)

def stackplot(x, *args, **kwargs):
    return gca().stackplot(x, *args, **kwargs)

def stem(*args, **kwargs):
    return gca().stem(*args, **kwargs)

def pie(x, **kwargs):
    return gca().pie(x, **kwargs)

def boxplot(x, **kwargs):
    return gca().boxplot(x, **kwargs)

def violinplot(dataset, **kwargs):
    return gca().violinplot(dataset, **kwargs)
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestPyplotWrappers -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/pyplot.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: add pyplot wrappers for all 7 new plot types"
```

---

### Task 11: Auto-limits support for Wedge patches

**Files:**
- Modify: `python/matplotlib/axes.py` (in `_auto_xlim` and `_auto_ylim`)
- Test: `python/matplotlib/tests/test_plot_types.py`

**Step 1: Write the failing test**

Append to `test_plot_types.py`:

```python
class TestAutoLimitsNewTypes:
    def test_pie_auto_limits(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.pie([1, 2, 3])
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        # Pie is centered at (0,0) with radius 1, so limits should encompass that
        assert xlim[0] <= -1.0
        assert xlim[1] >= 1.0
        assert ylim[0] <= -1.0
        assert ylim[1] >= 1.0

    def test_boxplot_auto_limits(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.boxplot([1, 2, 3, 4, 5])
        ylim = ax.get_ylim()
        assert ylim[0] <= 1.0
        assert ylim[1] >= 5.0
```

**Step 2: Run test to verify it fails**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestAutoLimitsNewTypes -v`
Expected: May pass already (Wedge patches have center+radius but _auto_xlim doesn't know about them). Check.

**Step 3: Update _auto_xlim and _auto_ylim**

In `python/matplotlib/axes.py`, update the `_auto_xlim` method to handle Wedge patches. In the `for patch in self.patches:` block, add:

```python
            elif hasattr(patch, '_center') and hasattr(patch, '_r'):
                # Wedge or Circle
                xs.append(patch._center[0] - patch._r)
                xs.append(patch._center[0] + patch._r)
```

Similarly in `_auto_ylim`:

```python
            elif hasattr(patch, '_center') and hasattr(patch, '_r'):
                # Wedge or Circle
                ys.append(patch._center[1] - patch._r)
                ys.append(patch._center[1] + patch._r)
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py::TestAutoLimitsNewTypes -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_plot_types.py
git commit -m "feat: update auto-limits to handle Wedge and Circle patches"
```

---

### Task 12: Full test suite verification

**Step 1: Run all new tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_plot_types.py -v`
Expected: ALL PASS (52 tests total across all Test classes)

**Step 2: Run full test suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q`
Expected: 734 + 52 = ~786 tests, ALL PASS

**Step 3: End-to-end savefig test (manual)**

Create a quick script to verify rendering works:

```python
# /tmp/test_new_plots.py
import matplotlib.pyplot as plt

# Step plot
fig, ax = plt.subplots()
ax.step([1,2,3,4], [1,4,2,5])
ax.set_title('Step')
fig.savefig('/tmp/test_step.svg')

# Pie chart
fig, ax = plt.subplots()
ax.pie([30, 20, 50], labels=['A', 'B', 'C'], autopct='%1.0f%%')
ax.set_title('Pie')
fig.savefig('/tmp/test_pie.svg')

# Boxplot
fig, ax = plt.subplots()
ax.boxplot([[1,2,3,4,5,6,7,8,9,10], [5,10,15,20,25]])
ax.set_title('Boxplot')
fig.savefig('/tmp/test_boxplot.svg')

print('All saved OK')
```

Run: `target/debug/matplotlib-python /tmp/test_new_plots.py`
Expected: prints "All saved OK", files exist at /tmp/

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address any issues found in full suite run"
```
