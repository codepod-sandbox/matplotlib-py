# New Plot Types Design

**Goal:** Add 7 missing plot types (step, stairs, stackplot, stem, pie, boxplot, violinplot) to reach broader matplotlib API parity.

**Architecture:** Each plot type is a method on Axes that creates artist objects (Line2D, Polygon, Rectangle, Wedge, PathCollection). Artists render themselves via the existing `draw(renderer, layout)` pattern. One new renderer primitive (`draw_wedge`) and one new patch class (`Wedge`) are needed for pie charts. A simple Gaussian KDE utility is needed for violinplot.

**Constraints:** RustPython-only, savefig use case, all existing 734 tests must continue passing.

---

## New Renderer Primitive

`draw_wedge(cx, cy, r, start_angle, end_angle, color)` — angles in degrees, counterclockwise from 3 o'clock (matching matplotlib convention).

- **SVG:** `<path>` with arc commands (M, A)
- **PIL:** `draw.pieslice()`

Added to `RendererBase`, `RendererSVG`, and `RendererPIL`.

## New Patch: Wedge

In `patches.py`:

```python
class Wedge(Patch):
    def __init__(self, center, r, theta1, theta2, **kwargs):
        self._center = tuple(center)
        self._r = r
        self._theta1 = theta1  # start angle (degrees)
        self._theta2 = theta2  # end angle (degrees)
        super().__init__(**kwargs)

    def draw(self, renderer, layout):
        # Convert center to pixels, compute pixel radius
        renderer.draw_wedge(cx_px, cy_px, r_px, self._theta1, self._theta2, color)
```

## New Utility: Simple Gaussian KDE

For violinplot. ~20 lines in a helper function in axes.py or a small `_kde.py`:

```python
def _gaussian_kde(data, n_points=100):
    """Simple Gaussian kernel density estimate."""
    # Silverman's rule of thumb for bandwidth
    # Evaluate at n_points evenly spaced across data range
    # Return (positions, densities)
```

## Plot Types

### 1. step(x, y, where='pre', **kwargs)
Transforms x/y into staircase coordinates, creates Line2D. `where` controls step placement: 'pre' (default), 'post', 'mid'.

### 2. stairs(values, edges=None, **kwargs)
For pre-binned histogram data. Takes N values and N+1 edges. Creates Line2D with staircase shape. If edges is None, uses range(len(values)+1).

### 3. stackplot(x, *args, labels=None, colors=None, **kwargs)
Stacked area chart. Computes cumulative sums, calls fill_between for each layer. Returns list of Polygons.

### 4. stem(x, y=None, linefmt=None, markerfmt=None, basefmt=None, bottom=0)
Lollipop chart. For each point: vertical Line2D from bottom to y, marker at (x, y). Plus a horizontal baseline. Returns StemContainer (new container class).

### 5. pie(x, labels=None, colors=None, explode=None, autopct=None, startangle=0, counterclock=True)
Creates Wedge patches for each slice. Proportional angles from data. Optional explosion offset, percentage labels. Sets equal aspect. Returns (wedges, texts) or (wedges, texts, autotexts).

### 6. boxplot(x, vert=True, widths=None, showfliers=True, showmeans=False)
For each dataset: Rectangle for IQR (Q1-Q3), line for median, whisker lines to 1.5*IQR, scatter markers for outliers. Returns dict of artists. Computes Q1, median, Q3 from sorted data.

### 7. violinplot(dataset, positions=None, vert=True, widths=0.5, showmeans=False, showmedians=False, showextrema=True)
KDE-based density plot. For each dataset: Polygon for violin body (mirrored KDE), optional lines for mean/median/extrema. Returns dict of artists.

## New Container: StemContainer

In `container.py`, similar to BarContainer/ErrorbarContainer:

```python
class StemContainer:
    def __init__(self, markerline, stemlines, baseline):
        self.markerline = markerline
        self.stemlines = stemlines
        self.baseline = baseline
```

## Files Modified

- `backend_bases.py` — add `draw_wedge` to RendererBase
- `_svg_backend.py` — implement `draw_wedge` in RendererSVG
- `_pil_backend.py` — implement `draw_wedge` in RendererPIL
- `patches.py` — add Wedge class
- `container.py` — add StemContainer
- `axes.py` — add 7 new methods, import Wedge, update auto-limits for Wedge
- `tests/test_backend_bases.py` — test draw_wedge
- `tests/test_axes.py` or new test file — tests for all 7 plot types
