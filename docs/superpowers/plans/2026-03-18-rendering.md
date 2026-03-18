# Plan: Rendering Fixes and Improvements (Sub-project B)

**Date:** 2026-03-18
**Branch:** `feat/rendering`
**Worktree:** `packages/matplotlib-py/.worktrees/rendering/`
**Goal:** Fix polygon fill, wedge fill, extend marker shapes, and add `imshow()` to both PIL and SVG backends.

## Architecture

- **PIL backend** (`_pil_backend.py`): `RendererPIL` uses `PIL.ImageDraw` methods via `_draw`. All drawing goes through `_pil_native` Rust module indirectly via `ImageDraw`.
- **SVG backend** (`_svg_backend.py`): `RendererSVG` emits SVG strings directly.
- **`backend_bases.py`**: `RendererBase` defines the interface all backends implement.
- **`axes.py`**: `Axes` calls renderer methods via `Figure.canvas`.
- **`ImageDraw.py`** (`packages/pillow-rust/python/PIL/ImageDraw.py`): Pure-Python wrapper over `_pil_native` Rust module. Adding pure-Python methods here requires NO Rust rebuild.

## Tech Stack

- Python (no external deps in matplotlib-py)
- PIL/Pillow via `packages/pillow-rust` (Rust + pure-Python wrapper)
- SVG string generation (no XML library)
- Scanline polygon fill (pure Python, no numpy required)

## Worktree and Commands

```bash
cd /Users/sunny/work/codepod/codepod/packages/matplotlib-py/.worktrees/rendering
# Test binary: target/debug/matplotlib-python
# Run tests:
target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q
# Baseline: 868 passed, 0 failed
```

## File Map

| File | Action |
|------|--------|
| `packages/pillow-rust/python/PIL/ImageDraw.py` | Add `_normalise_polygon()`, `polygon()`, `_normalise_box()`, `pieslice()` |
| `python/matplotlib/_pil_backend.py` | Fix `draw_polygon()`, fix `draw_wedge()`, extend `draw_markers()` |
| `python/matplotlib/_svg_backend.py` | Extend `draw_markers()` with all marker shapes |
| `python/matplotlib/backend_bases.py` | Add `draw_image()` to `RendererBase`; add `marker` param to `draw_markers()` |
| `python/matplotlib/axes.py` | Add `imshow()`; pass `marker` param through `scatter()` |
| `python/matplotlib/tests/test_rendering_upstream.py` | New test file with 7 tests |

---

## Task 1: Add `polygon()` and `pieslice()` to `ImageDraw`

**File:** `packages/pillow-rust/python/PIL/ImageDraw.py`

No Rust rebuild needed — these are pure-Python methods on top of `self.line()`.

### 1.1 Write failing test

Add to `python/matplotlib/tests/test_rendering_upstream.py`:

```python
def test_polygon_fill_png():
    """fill_between() must produce solid fill pixels, not a hollow outline."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots(figsize=(2, 2), dpi=50)
    ax.fill_between([0, 1], [0, 0], [1, 1], color='red')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    # At least 10% of pixels should have red channel > 200 and green < 50
    red_pixels = sum(1 for r, g, b in pixels if r > 200 and g < 50)
    assert red_pixels > len(pixels) * 0.05, \
        f"Expected filled red region, got {red_pixels}/{len(pixels)} red pixels"
    plt.close(fig)
```

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py::test_polygon_fill_png -q`

Expected: FAIL (polygon currently draws hollow outline only).

### 1.2 Implement

In `packages/pillow-rust/python/PIL/ImageDraw.py`, add before the class definition or as module-level helpers:

```python
def _normalise_polygon(xy):
    """Convert sequence of points to list of (x, y) int tuples."""
    pts = []
    for item in xy:
        if hasattr(item, '__len__') and len(item) == 2:
            pts.append((int(item[0]), int(item[1])))
        else:
            raise ValueError(f"Expected (x, y) pairs, got {item!r}")
    return pts


def _normalise_box(xy):
    """Convert bounding box to (x0, y0, x1, y1) tuple."""
    if hasattr(xy, '__len__') and len(xy) == 4:
        return tuple(int(v) for v in xy)
    if hasattr(xy, '__len__') and len(xy) == 2:
        (x0, y0), (x1, y1) = xy
        return int(x0), int(y0), int(x1), int(y1)
    raise ValueError(f"Expected bounding box, got {xy!r}")
```

Add `polygon()` method to `ImageDraw`:

```python
def polygon(self, xy, fill=None, outline=None):
    """Draw a filled polygon using scanline fill."""
    pts = _normalise_polygon(xy)
    if len(pts) < 3:
        return
    # Resolve color: fill takes priority, then outline, then white
    color = fill if fill is not None else (outline if outline is not None else (255, 255, 255))
    if isinstance(color, int):
        color = (color, color, color)

    if fill is not None:
        # Scanline fill
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        y_min, y_max = int(min(ys)), int(max(ys))
        n = len(pts)
        fill_color = fill if not isinstance(fill, int) else (fill, fill, fill)
        for y in range(y_min, y_max + 1):
            intersections = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y < max(y0, y1):
                    x = x0 + (x1 - x0) * (y - y0) / (y1 - y0)
                    intersections.append(x)
            intersections.sort()
            for k in range(0, len(intersections) - 1, 2):
                x_start = int(intersections[k])
                x_end = int(intersections[k + 1])
                if x_start <= x_end:
                    self.line([(x_start, y), (x_end, y)], fill=fill_color, width=1)

    if outline is not None:
        out_color = outline if not isinstance(outline, int) else (outline, outline, outline)
        for i in range(len(pts)):
            self.line([pts[i], pts[(i + 1) % len(pts)]], fill=out_color, width=1)
```

Add `pieslice()` method to `ImageDraw`:

```python
def pieslice(self, xy, start, end, fill=None, outline=None):
    """Draw a pie slice (filled wedge) using polygon()."""
    import math
    x0, y0, x1, y1 = _normalise_box(xy)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    sweep = end - start
    color = fill if fill is not None else (outline if outline is not None else (255, 255, 255))
    if isinstance(color, int):
        color = (color, color, color)
    n_segments = max(16, int(abs(sweep) / 2))
    pts = [(int(cx), int(cy))]
    for i in range(n_segments + 1):
        angle_deg = start + sweep * i / n_segments
        angle_rad = math.radians(angle_deg)
        px = cx + rx * math.cos(angle_rad)
        py = cy + ry * math.sin(angle_rad)
        pts.append((int(px), int(py)))
    self.polygon(pts, fill=color)
```

### 1.3 Run test

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py::test_polygon_fill_png -q`

Expected: Still FAIL (ImageDraw.polygon exists now but `draw_polygon()` in `_pil_backend.py` still does not call it). Proceed to Task 2.

---

## Task 2: Fix `draw_polygon()` and `draw_wedge()` in `_pil_backend.py`

**File:** `python/matplotlib/_pil_backend.py`

### 2.1 Write failing tests

Add to `python/matplotlib/tests/test_rendering_upstream.py`:

```python
def test_pie_fill_png():
    """Pie chart slices must be filled, not wireframe."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots(figsize=(2, 2), dpi=50)
    ax.pie([1, 2, 3], colors=['red', 'green', 'blue'])
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    # At least one strongly saturated pixel (any primary color component > 180
    # with the others < 80) indicates fill rather than just outline
    saturated = sum(
        1 for r, g, b in pixels
        if (r > 180 and g < 80 and b < 80)
        or (g > 180 and r < 80 and b < 80)
        or (b > 180 and r < 80 and g < 80)
    )
    assert saturated > len(pixels) * 0.03, \
        f"Expected filled pie slices, got {saturated}/{len(pixels)} saturated pixels"
    plt.close(fig)
```

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py::test_pie_fill_png -q`

Expected: FAIL.

### 2.2 Implement `draw_polygon()`

Find the current `draw_polygon()` in `_pil_backend.py`. It currently uses `self._draw.line()` to draw edges. Replace with:

```python
def draw_polygon(self, points, color, alpha):
    col = _to_rgb_255(color)
    pts = [(int(x), int(y)) for x, y in points]
    if len(pts) >= 3:
        self._draw.polygon(pts, fill=col)
```

Note: `_to_rgb_255` already exists in `_pil_backend.py` — use the existing helper.

### 2.3 Implement `draw_wedge()`

Find the current `draw_wedge()` which uses radial scanlines. Replace with:

```python
def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
    import math
    col = _to_rgb_255(color)
    sweep = end_angle - start_angle
    if abs(sweep) >= 360:
        self.draw_circle(cx, cy, r, color)
        return
    n_segments = max(16, int(abs(sweep) / 2))
    pts = [(int(cx), int(cy))]
    for i in range(n_segments + 1):
        angle_deg = start_angle + sweep * i / n_segments
        angle_rad = math.radians(angle_deg)
        x = cx + r * math.cos(angle_rad)
        # Negate y: screen coordinates have y increasing downward,
        # but angles are measured counterclockwise from x-axis.
        y = cy - r * math.sin(angle_rad)
        pts.append((int(x), int(y)))
    self._draw.polygon(pts, fill=col)
```

### 2.4 Run tests

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py::test_polygon_fill_png python/matplotlib/tests/test_rendering_upstream.py::test_pie_fill_png -q`

Expected: Both pass.

Run full suite: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q`

Expected: 868 passed (no regressions), plus the 2 new tests = 870 passed.

### 2.5 Commit

```bash
git add packages/pillow-rust/python/PIL/ImageDraw.py python/matplotlib/_pil_backend.py python/matplotlib/tests/test_rendering_upstream.py
git commit -m "feat: polygon fill and wedge fix in PIL backend"
```

---

## Task 3: Extended marker types

**Files:** `python/matplotlib/backend_bases.py`, `python/matplotlib/_pil_backend.py`, `python/matplotlib/_svg_backend.py`, `python/matplotlib/axes.py`

### 3.1 Write failing tests

Add to `python/matplotlib/tests/test_rendering_upstream.py`:

```python
def test_markers_square_svg():
    """scatter with marker='s' produces <rect> elements in SVG."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [1, 2, 3], marker='s', color='blue')
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    assert '<rect' in svg, f"Expected <rect> elements for square markers, got SVG without <rect>"
    plt.close(fig)


def test_markers_triangle_svg():
    """scatter with marker='^' produces <polygon> elements in SVG."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [1, 2, 3], marker='^', color='green')
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    assert '<polygon' in svg, f"Expected <polygon> elements for triangle markers, got SVG without <polygon>"
    plt.close(fig)


def test_markers_square_png():
    """scatter with marker='s' produces non-white pixels in correct positions."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots(figsize=(2, 2), dpi=50)
    ax.scatter([0.5], [0.5], marker='s', s=200, color='blue')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    blue_pixels = sum(1 for r, g, b in pixels if b > 150 and r < 100 and g < 100)
    assert blue_pixels > 5, \
        f"Expected blue square marker pixels, got {blue_pixels}"
    plt.close(fig)
```

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py::test_markers_square_svg python/matplotlib/tests/test_rendering_upstream.py::test_markers_triangle_svg python/matplotlib/tests/test_rendering_upstream.py::test_markers_square_png -q`

Expected: FAIL (marker param not wired up).

### 3.2 Update `RendererBase.draw_markers()` signature

In `python/matplotlib/backend_bases.py`, update `draw_markers()`:

```python
def draw_markers(self, positions, color, size, marker='o'):
    """Draw markers at each position.

    Parameters
    ----------
    positions : list of (x, y)
    color : color spec
    size : float, radius in pixels
    marker : str
        Marker style. One of: 'o', '.', 's', '^', 'v', 'D', '+', 'x', '*'
    """
    pass  # subclasses implement
```

### 3.3 Update `scatter()` in `axes.py`

Find `scatter()` in `python/matplotlib/axes.py`. Currently it calls `draw_markers()` without passing `marker`. Update the call:

```python
# Before:
renderer.draw_markers(positions, color, size)

# After:
renderer.draw_markers(positions, color, size, marker=marker)
```

Also ensure `scatter()` accepts and uses `marker` kwarg (it should already have `marker='o'` in its signature — verify and add if missing).

### 3.4 Implement extended markers in `RendererSVG`

In `python/matplotlib/_svg_backend.py`, update `draw_markers()`:

```python
def draw_markers(self, positions, color, size, marker='o'):
    col = _to_svg_color(color)
    r = size
    for x, y in positions:
        if marker in ('o', '.'):
            self._elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{col}" />'
            )
        elif marker == 's':
            half = r
            self._elements.append(
                f'<rect x="{x - half:.2f}" y="{y - half:.2f}" '
                f'width="{2 * half:.2f}" height="{2 * half:.2f}" fill="{col}" />'
            )
        elif marker == '^':
            # Triangle pointing up
            pts = f"{x:.2f},{y - r:.2f} {x - r:.2f},{y + r:.2f} {x + r:.2f},{y + r:.2f}"
            self._elements.append(f'<polygon points="{pts}" fill="{col}" />')
        elif marker == 'v':
            # Triangle pointing down
            pts = f"{x:.2f},{y + r:.2f} {x - r:.2f},{y - r:.2f} {x + r:.2f},{y - r:.2f}"
            self._elements.append(f'<polygon points="{pts}" fill="{col}" />')
        elif marker == 'D':
            # Diamond
            pts = (f"{x:.2f},{y - r:.2f} {x + r:.2f},{y:.2f} "
                   f"{x:.2f},{y + r:.2f} {x - r:.2f},{y:.2f}")
            self._elements.append(f'<polygon points="{pts}" fill="{col}" />')
        elif marker == '+':
            w = r * 0.25
            self._elements.append(
                f'<rect x="{x - w:.2f}" y="{y - r:.2f}" '
                f'width="{2 * w:.2f}" height="{2 * r:.2f}" fill="{col}" />'
            )
            self._elements.append(
                f'<rect x="{x - r:.2f}" y="{y - w:.2f}" '
                f'width="{2 * r:.2f}" height="{2 * w:.2f}" fill="{col}" />'
            )
        elif marker == 'x':
            stroke_w = max(1, r * 0.4)
            self._elements.append(
                f'<line x1="{x - r:.2f}" y1="{y - r:.2f}" '
                f'x2="{x + r:.2f}" y2="{y + r:.2f}" '
                f'stroke="{col}" stroke-width="{stroke_w:.2f}" />'
            )
            self._elements.append(
                f'<line x1="{x + r:.2f}" y1="{y - r:.2f}" '
                f'x2="{x - r:.2f}" y2="{y + r:.2f}" '
                f'stroke="{col}" stroke-width="{stroke_w:.2f}" />'
            )
        elif marker == '*':
            # Star: combine + and x
            w = r * 0.25
            self._elements.append(
                f'<rect x="{x - w:.2f}" y="{y - r:.2f}" '
                f'width="{2 * w:.2f}" height="{2 * r:.2f}" fill="{col}" />'
            )
            self._elements.append(
                f'<rect x="{x - r:.2f}" y="{y - w:.2f}" '
                f'width="{2 * r:.2f}" height="{2 * w:.2f}" fill="{col}" />'
            )
            stroke_w = max(1, r * 0.4)
            self._elements.append(
                f'<line x1="{x - r * 0.7:.2f}" y1="{y - r * 0.7:.2f}" '
                f'x2="{x + r * 0.7:.2f}" y2="{y + r * 0.7:.2f}" '
                f'stroke="{col}" stroke-width="{stroke_w:.2f}" />'
            )
            self._elements.append(
                f'<line x1="{x + r * 0.7:.2f}" y1="{y - r * 0.7:.2f}" '
                f'x2="{x - r * 0.7:.2f}" y2="{y + r * 0.7:.2f}" '
                f'stroke="{col}" stroke-width="{stroke_w:.2f}" />'
            )
        else:
            # Unknown marker: fall back to circle
            self._elements.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{col}" />'
            )
```

Note: `_to_svg_color` — use whatever the existing helper is called in `_svg_backend.py`.

### 3.5 Implement extended markers in `RendererPIL`

In `python/matplotlib/_pil_backend.py`, update `draw_markers()`:

```python
def draw_markers(self, positions, color, size, marker='o'):
    import math
    col = _to_rgb_255(color)
    r = int(size)
    for x, y in positions:
        x, y = int(x), int(y)
        if marker in ('o', '.'):
            self._draw.ellipse(
                [(x - r, y - r), (x + r, y + r)], fill=col
            )
        elif marker == 's':
            pts = [
                (x - r, y - r), (x + r, y - r),
                (x + r, y + r), (x - r, y + r),
            ]
            self._draw.polygon(pts, fill=col)
        elif marker == '^':
            pts = [(x, y - r), (x - r, y + r), (x + r, y + r)]
            self._draw.polygon(pts, fill=col)
        elif marker == 'v':
            pts = [(x, y + r), (x - r, y - r), (x + r, y - r)]
            self._draw.polygon(pts, fill=col)
        elif marker == 'D':
            pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
            self._draw.polygon(pts, fill=col)
        elif marker == '+':
            w = max(1, r // 4)
            self._draw.polygon(
                [(x - w, y - r), (x + w, y - r), (x + w, y + r), (x - w, y + r)],
                fill=col
            )
            self._draw.polygon(
                [(x - r, y - w), (x + r, y - w), (x + r, y + w), (x - r, y + w)],
                fill=col
            )
        elif marker == 'x':
            self._draw.line([(x - r, y - r), (x + r, y + r)], fill=col, width=max(1, r // 3))
            self._draw.line([(x + r, y - r), (x - r, y + r)], fill=col, width=max(1, r // 3))
        elif marker == '*':
            w = max(1, r // 4)
            self._draw.polygon(
                [(x - w, y - r), (x + w, y - r), (x + w, y + r), (x - w, y + r)],
                fill=col
            )
            self._draw.polygon(
                [(x - r, y - w), (x + r, y - w), (x + r, y + w), (x - r, y + w)],
                fill=col
            )
            self._draw.line(
                [(x - int(r * 0.7), y - int(r * 0.7)),
                 (x + int(r * 0.7), y + int(r * 0.7))],
                fill=col, width=max(1, r // 3)
            )
            self._draw.line(
                [(x + int(r * 0.7), y - int(r * 0.7)),
                 (x - int(r * 0.7), y + int(r * 0.7))],
                fill=col, width=max(1, r // 3)
            )
        else:
            # Unknown: fall back to circle
            self._draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=col)
```

### 3.6 Run tests

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py -q
target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q
```

Expected: all 5 new tests pass, full suite = 873 passed, 0 failed.

### 3.7 Commit

```bash
git add python/matplotlib/backend_bases.py python/matplotlib/_pil_backend.py \
        python/matplotlib/_svg_backend.py python/matplotlib/axes.py \
        python/matplotlib/tests/test_rendering_upstream.py
git commit -m "feat: extended marker shapes in PIL and SVG backends"
```

---

## Task 4: `imshow()` — image rendering

**Files:** `python/matplotlib/backend_bases.py`, `python/matplotlib/_pil_backend.py`, `python/matplotlib/_svg_backend.py`, `python/matplotlib/axes.py`

### 4.1 Write failing tests

Add to `python/matplotlib/tests/test_rendering_upstream.py`:

```python
def test_imshow_svg():
    """imshow() produces a base64 data URL image embedded in SVG."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots()
    data = [[0, 128, 255], [64, 192, 32]]
    ax.imshow(data, cmap='viridis')
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    assert 'data:image/png;base64,' in svg, \
        "Expected base64 PNG embedded in SVG for imshow()"
    plt.close(fig)


def test_imshow_png():
    """imshow() with RGB array renders correct pixel colors."""
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots(figsize=(1, 1), dpi=10)
    # 2x2 RGB image: top-left red, top-right green, bottom-left blue, bottom-right white
    data = [
        [[255, 0, 0], [0, 255, 0]],
        [[0, 0, 255], [255, 255, 255]],
    ]
    ax.imshow(data)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    # At least one highly red pixel, one highly green, one highly blue
    has_red = any(r > 200 and g < 50 for r, g, b in pixels)
    has_green = any(g > 200 and r < 50 for r, g, b in pixels)
    has_blue = any(b > 200 and r < 50 for r, g, b in pixels)
    assert has_red, "Expected red pixel from imshow"
    assert has_green, "Expected green pixel from imshow"
    assert has_blue, "Expected blue pixel from imshow"
    plt.close(fig)
```

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py::test_imshow_svg python/matplotlib/tests/test_rendering_upstream.py::test_imshow_png -q`

Expected: FAIL (`Axes` has no `imshow`, `RendererBase` has no `draw_image`).

### 4.2 Add `draw_image()` to `RendererBase`

In `python/matplotlib/backend_bases.py`:

```python
def draw_image(self, x, y, width, height, rgba_array):
    """Draw an image.

    Parameters
    ----------
    x, y : float
        Bottom-left corner in display coordinates.
    width, height : float
        Size in display coordinates.
    rgba_array : list of lists
        2D list of (R, G, B, A) tuples, shape [rows][cols],
        where row 0 is the top of the image.
    """
    pass  # subclasses implement
```

### 4.3 Implement `draw_image()` in `RendererSVG`

In `python/matplotlib/_svg_backend.py`, add `draw_image()`:

```python
def draw_image(self, x, y, width, height, rgba_array):
    """Embed image as base64 PNG data URL."""
    import base64
    import io
    from PIL import Image

    rows = len(rgba_array)
    cols = len(rgba_array[0]) if rows > 0 else 0
    if rows == 0 or cols == 0:
        return

    # Build a PIL image from rgba_array
    img = Image.new('RGBA', (cols, rows))
    pixels = []
    for row in rgba_array:
        for pixel in row:
            if len(pixel) == 3:
                pixels.append((int(pixel[0]), int(pixel[1]), int(pixel[2]), 255))
            else:
                pixels.append((int(pixel[0]), int(pixel[1]), int(pixel[2]), int(pixel[3])))
    img.putdata(pixels)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    data_url = f'data:image/png;base64,{b64}'

    # SVG y-axis: y=0 is top. x,y here are bottom-left in display coords.
    # SVG image origin is top-left, so we use (y - height) if y is bottom.
    svg_y = y - height
    self._elements.append(
        f'<image x="{x:.2f}" y="{svg_y:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'href="{data_url}" />'
    )
```

Note: check whether PIL is available in the SVG backend's context. If not, implement a minimal PNG encoder. However, since `packages/pillow-rust` is part of this project, PIL should be available.

If PIL is not available in the SVG path, use this minimal PNG encoder fallback (add as a module-level helper):

```python
def _encode_png_base64(rgba_array):
    """Minimal PNG encoder for imshow in SVG backend. Returns base64 string."""
    import base64
    import struct
    import zlib

    rows = len(rgba_array)
    cols = len(rgba_array[0]) if rows > 0 else 0

    def make_png(width, height, pixel_rows):
        def chunk(name, data):
            c = name + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

        header = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr = chunk(b'IHDR', ihdr_data)

        raw_data = b''
        for row in pixel_rows:
            raw_data += b'\x00'  # filter type: None
            for r, g, b in row:
                raw_data += bytes([int(r), int(g), int(b)])
        idat = chunk(b'IDAT', zlib.compress(raw_data))
        iend = chunk(b'IEND', b'')
        return header + ihdr + idat + iend

    # Convert rgba_array to RGB rows (drop alpha)
    pixel_rows = []
    for row in rgba_array:
        prow = []
        for px in row:
            prow.append((px[0], px[1], px[2]))
        pixel_rows.append(prow)

    png_bytes = make_png(cols, rows, pixel_rows)
    return base64.b64encode(png_bytes).decode('ascii')
```

Use this fallback if PIL import fails:

```python
def draw_image(self, x, y, width, height, rgba_array):
    try:
        import base64, io
        from PIL import Image
        rows = len(rgba_array)
        cols = len(rgba_array[0]) if rows > 0 else 0
        img = Image.new('RGB', (cols, rows))
        pixels = [(int(px[0]), int(px[1]), int(px[2])) for row in rgba_array for px in row]
        img.putdata(pixels)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    except ImportError:
        b64 = _encode_png_base64(rgba_array)
    data_url = f'data:image/png;base64,{b64}'
    svg_y = y - height
    self._elements.append(
        f'<image x="{x:.2f}" y="{svg_y:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'href="{data_url}" />'
    )
```

### 4.4 Implement `draw_image()` in `RendererPIL`

In `python/matplotlib/_pil_backend.py`, add `draw_image()`:

```python
def draw_image(self, x, y, width, height, rgba_array):
    """Paste an image into the canvas at (x, y) bottom-left, size (width, height)."""
    from PIL import Image

    rows = len(rgba_array)
    cols = len(rgba_array[0]) if rows > 0 else 0
    if rows == 0 or cols == 0:
        return

    src = Image.new('RGB', (cols, rows))
    pixels = []
    for row in rgba_array:
        for px in row:
            pixels.append((int(px[0]), int(px[1]), int(px[2])))
    src.putdata(pixels)

    # Scale to display size
    disp_w = max(1, int(width))
    disp_h = max(1, int(height))
    src = src.resize((disp_w, disp_h), Image.NEAREST)

    # y is bottom-left in display coords; PIL paste uses top-left.
    # Display coords: y=0 is top (screen coords), so top-left = (x, y - height).
    paste_x = int(x)
    paste_y = int(y - height)
    self._img.paste(src, (paste_x, paste_y))
```

Note: `self._img` must be the underlying PIL `Image` object. Check the existing `RendererPIL` to confirm the attribute name. If it's different (e.g., `self._image`, `self.image`), adjust accordingly.

### 4.5 Add `Axes.imshow()`

In `python/matplotlib/axes.py`, add `imshow()` method:

```python
def imshow(self, X, cmap=None, vmin=None, vmax=None, origin='upper', aspect='auto'):
    """Display an image on the axes.

    Parameters
    ----------
    X : array-like
        2D array (M×N) → apply colormap.
        3D array (M×N×3) → RGB image.
        3D array (M×N×4) → RGBA image.
    cmap : str, optional
        Colormap name (default: 'viridis'). Only used for 2D input.
    vmin, vmax : float, optional
        Colormap value range. If None, use min/max of X.
    origin : str
        'upper' (default): row 0 is top. 'lower': row 0 is bottom.
    aspect : str
        Ignored currently; kept for API compatibility.

    Returns
    -------
    None
    """
    # Lazy import to avoid WASM startup cost
    import matplotlib.cm as _cm

    # Normalise X to list of lists of tuples
    rows = list(X)
    if len(rows) == 0:
        return
    first_row = list(rows[0])
    if len(first_row) == 0:
        return

    first_cell = first_row[0]
    # Determine if scalar (2D array) or RGB/RGBA (3D array)
    is_scalar = not hasattr(first_cell, '__len__')

    if is_scalar:
        # 2D array: apply colormap
        if cmap is None:
            cmap = 'viridis'
        colormap = _cm.get_cmap(cmap)
        flat_vals = [float(v) for row in rows for v in row]
        lo = vmin if vmin is not None else min(flat_vals)
        hi = vmax if vmax is not None else max(flat_vals)
        rng = (hi - lo) if hi != lo else 1.0
        rgba_array = []
        for row in rows:
            rgba_row = []
            for v in row:
                t = (float(v) - lo) / rng
                t = max(0.0, min(1.0, t))
                rgba = colormap(t)  # returns (r, g, b, a) floats 0-1
                rgba_row.append(
                    (int(rgba[0] * 255), int(rgba[1] * 255),
                     int(rgba[2] * 255), int(rgba[3] * 255))
                )
            rgba_array.append(rgba_row)
    else:
        # 3D array: RGB or RGBA
        rgba_array = []
        for row in rows:
            rgba_row = []
            for px in row:
                px = list(px)
                if len(px) == 3:
                    rgba_row.append((int(px[0]), int(px[1]), int(px[2]), 255))
                else:
                    rgba_row.append((int(px[0]), int(px[1]), int(px[2]), int(px[3])))
            rgba_array.append(rgba_row)

    if origin == 'lower':
        rgba_array = list(reversed(rgba_array))

    # Store the image for rendering; renderer will call draw_image() during draw.
    # We store it as a pending artist and call draw_image() at draw time.
    self._images = getattr(self, '_images', [])
    self._images.append(rgba_array)

    # Trigger rendering if a renderer is already attached.
    # In the standard draw path, _draw_images() is called from draw().
    self._needs_draw = True
```

Then ensure `Axes.draw()` (or equivalent) calls `_draw_images()`. Add a helper:

```python
def _draw_images(self, renderer):
    """Render all pending images."""
    images = getattr(self, '_images', [])
    if not images:
        return
    # Get axes bounding box in display coordinates
    x0, y0, x1, y1 = self._get_display_bbox()
    ax_width = x1 - x0
    ax_height = y1 - y0
    for rgba_array in images:
        renderer.draw_image(x0, y1, ax_width, ax_height, rgba_array)
```

Call `self._draw_images(renderer)` at the end of `Axes.draw()`.

Note: `_get_display_bbox()` should already exist (it's used for axes border drawing). If not, compute from `self._x_lim`, `self._y_lim` and figure DPI/size. Use whatever the existing pattern is.

### 4.6 Run tests

```bash
target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_rendering_upstream.py -q
target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q
```

Expected: all 7 new tests pass, full suite = 875 passed, 0 failed.

### 4.7 Commit

```bash
git add python/matplotlib/backend_bases.py python/matplotlib/_pil_backend.py \
        python/matplotlib/_svg_backend.py python/matplotlib/axes.py \
        python/matplotlib/tests/test_rendering_upstream.py
git commit -m "feat: add imshow() with PIL and SVG rendering support"
```

---

## Complete Test File

This is the full `python/matplotlib/tests/test_rendering_upstream.py` file to create:

```python
"""Tests for rendering fixes and improvements (sub-project B).

Baseline: 868 passed, 0 failed. Any regression is a bug.
"""
import io
import pytest


def test_polygon_fill_png():
    """fill_between() must produce solid fill pixels, not a hollow outline."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(2, 2), dpi=50)
    ax.fill_between([0, 1], [0, 0], [1, 1], color='red')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    red_pixels = sum(1 for r, g, b in pixels if r > 200 and g < 50)
    assert red_pixels > len(pixels) * 0.05, \
        f"Expected filled red region, got {red_pixels}/{len(pixels)} red pixels"
    plt.close(fig)


def test_pie_fill_png():
    """Pie chart slices must be filled, not wireframe."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(2, 2), dpi=50)
    ax.pie([1, 2, 3], colors=['red', 'green', 'blue'])
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    saturated = sum(
        1 for r, g, b in pixels
        if (r > 180 and g < 80 and b < 80)
        or (g > 180 and r < 80 and b < 80)
        or (b > 180 and r < 80 and g < 80)
    )
    assert saturated > len(pixels) * 0.03, \
        f"Expected filled pie slices, got {saturated}/{len(pixels)} saturated pixels"
    plt.close(fig)


def test_markers_square_svg():
    """scatter with marker='s' produces <rect> elements in SVG."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [1, 2, 3], marker='s', color='blue')
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    assert '<rect' in svg, \
        f"Expected <rect> elements for square markers, got SVG without <rect>"
    plt.close(fig)


def test_markers_triangle_svg():
    """scatter with marker='^' produces <polygon> elements in SVG."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [1, 2, 3], marker='^', color='green')
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    assert '<polygon' in svg, \
        f"Expected <polygon> elements for triangle markers, got SVG without <polygon>"
    plt.close(fig)


def test_markers_square_png():
    """scatter with marker='s' produces non-white pixels in correct positions."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(2, 2), dpi=50)
    ax.scatter([0.5], [0.5], marker='s', s=200, color='blue')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    blue_pixels = sum(1 for r, g, b in pixels if b > 150 and r < 100 and g < 100)
    assert blue_pixels > 5, \
        f"Expected blue square marker pixels, got {blue_pixels}"
    plt.close(fig)


def test_imshow_svg():
    """imshow() produces a base64 data URL image embedded in SVG."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    data = [[0, 128, 255], [64, 192, 32]]
    ax.imshow(data, cmap='viridis')
    buf = io.StringIO()
    fig.savefig(buf, format='svg')
    svg = buf.getvalue()
    assert 'data:image/png;base64,' in svg, \
        "Expected base64 PNG embedded in SVG for imshow()"
    plt.close(fig)


def test_imshow_png():
    """imshow() with RGB array renders correct pixel colors."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(1, 1), dpi=10)
    data = [
        [[255, 0, 0], [0, 255, 0]],
        [[0, 0, 255], [255, 255, 255]],
    ]
    ax.imshow(data)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    from PIL import Image
    img = Image.open(buf).convert('RGB')
    pixels = list(img.getdata())
    has_red = any(r > 200 and g < 50 for r, g, b in pixels)
    has_green = any(g > 200 and r < 50 for r, g, b in pixels)
    has_blue = any(b > 200 and r < 50 for r, g, b in pixels)
    assert has_red, "Expected red pixel from imshow"
    assert has_green, "Expected green pixel from imshow"
    assert has_blue, "Expected blue pixel from imshow"
    plt.close(fig)
```

---

## Execution Order

1. Create test file `python/matplotlib/tests/test_rendering_upstream.py` with all 7 tests.
2. Run full test file — all 7 should FAIL (baseline still 868 passed).
3. Task 1: Add `polygon()`, `pieslice()` to `ImageDraw.py`.
4. Task 2: Fix `draw_polygon()`, `draw_wedge()` in `_pil_backend.py`. Run tests 1–2 → pass. Commit.
5. Task 3: Update `draw_markers()` in all files; wire `marker` param through `scatter()`. Run tests 3–5 → pass. Commit.
6. Task 4: Add `draw_image()` to all backends; add `Axes.imshow()`. Run tests 6–7 → pass. Commit.
7. Final run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -q` → 875 passed, 0 failed.

## Gotchas

- **PIL y-axis**: y increases downward. In `draw_wedge()`, `sin` must be negated: `y = cy - r * sin(angle)`.
- **`_to_rgb_255`**: Check the exact name of the color-conversion helper in `_pil_backend.py` before using it.
- **`_to_svg_color`**: Check the exact name in `_svg_backend.py`.
- **`self._img` vs `self._image`**: Verify the PIL image attribute name in `RendererPIL` before implementing `draw_image()`.
- **`_get_display_bbox()`**: Check if it exists in `Axes`; if not, derive display coords from existing axes geometry helpers.
- **No `from matplotlib import cm` in `__init__.py`**: `imshow()` uses `import matplotlib.cm as _cm` inside the method body.
- **Baseline invariant**: 868 passed must not regress. Run full suite after each commit.
- **`io.StringIO` for SVG**: SVG output is text. Use `io.StringIO()`, not `io.BytesIO()`.
