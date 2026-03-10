# Renderer Architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the dual-tracking `_elements` dict pattern with a RendererBase abstraction and artist-driven rendering.

**Architecture:** Create a RendererBase interface with pixel-coordinate drawing primitives. SVG and PIL backends implement it. Artists get `draw(renderer, layout)` methods. Axes/Figure get `draw(renderer)` that orchestrate rendering. Then eliminate `_elements` entirely.

**Tech Stack:** Pure Python, RustPython runtime, PIL for PNG backend.

**Test command:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x -v`

**Test a single file:** `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_file.py -x -v`

---

### Task 1: Create RendererBase and AxesLayout

**Files:**
- Create: `python/matplotlib/backend_bases.py`
- Test: `python/matplotlib/tests/test_backend_bases.py`

**Step 1: Write the test file**

```python
"""Tests for RendererBase and AxesLayout."""

import pytest
from matplotlib.backend_bases import RendererBase, AxesLayout


class TestRendererBase:
    def test_init_stores_dimensions(self):
        r = RendererBase(640, 480, 100)
        assert r.width == 640
        assert r.height == 480
        assert r.dpi == 100

    def test_draw_line_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.draw_line([], [], '#000', 1.0, '-', 1.0)

    def test_draw_rect_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.draw_rect(0, 0, 10, 10, '#fff', '#000', 1.0, 1.0)

    def test_draw_circle_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.draw_circle(0, 0, 5, '#fff', '#000', 1.0, 1.0)

    def test_draw_polygon_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.draw_polygon([], [], '#fff', '#000', 1.0, 1.0)

    def test_draw_markers_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.draw_markers([], [], 'o', 6.0, '#000', 1.0)

    def test_draw_text_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.draw_text(0, 0, 'hi', 12, '#000', 'left', 'baseline', 0, 1.0)

    def test_get_result_raises(self):
        r = RendererBase(640, 480, 100)
        with pytest.raises(NotImplementedError):
            r.get_result()


class TestAxesLayout:
    def test_stores_geometry(self):
        layout = AxesLayout(
            plot_x=70, plot_y=40, plot_w=550, plot_h=390,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=5.0,
        )
        assert layout.plot_x == 70
        assert layout.plot_y == 40
        assert layout.plot_w == 550
        assert layout.plot_h == 390

    def test_sx_maps_data_to_pixel(self):
        layout = AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )
        assert layout.sx(0.0) == 0.0
        assert layout.sx(10.0) == 100.0
        assert layout.sx(5.0) == 50.0

    def test_sy_maps_data_to_pixel_inverted(self):
        """SVG/pixel y-axis is inverted: data y=0 maps to bottom (plot_y + plot_h)."""
        layout = AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )
        assert layout.sy(0.0) == 100.0   # bottom
        assert layout.sy(10.0) == 0.0     # top
        assert layout.sy(5.0) == 50.0     # middle
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`
Expected: FAIL (ImportError — module doesn't exist yet)

**Step 3: Implement backend_bases.py**

```python
"""matplotlib.backend_bases --- RendererBase and AxesLayout."""


class AxesLayout:
    """Geometry and coordinate transforms for one Axes at draw time."""

    __slots__ = ('plot_x', 'plot_y', 'plot_w', 'plot_h',
                 'xmin', 'xmax', 'ymin', 'ymax')

    def __init__(self, plot_x, plot_y, plot_w, plot_h,
                 xmin, xmax, ymin, ymax):
        self.plot_x = plot_x
        self.plot_y = plot_y
        self.plot_w = plot_w
        self.plot_h = plot_h
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

    def sx(self, v):
        """Map data x-coordinate to pixel x."""
        return self.plot_x + (v - self.xmin) / (self.xmax - self.xmin) * self.plot_w

    def sy(self, v):
        """Map data y-coordinate to pixel y (inverted: y increases downward)."""
        return self.plot_y + self.plot_h - (v - self.ymin) / (self.ymax - self.ymin) * self.plot_h


class RendererBase:
    """Abstract base class for all renderers."""

    def __init__(self, width, height, dpi):
        self.width = width
        self.height = height
        self.dpi = dpi

    def draw_line(self, x_pts, y_pts, color, linewidth, linestyle, alpha):
        raise NotImplementedError

    def draw_markers(self, x_pts, y_pts, marker, markersize, color, alpha):
        raise NotImplementedError

    def draw_rect(self, x, y, width, height, facecolor, edgecolor, linewidth, alpha):
        raise NotImplementedError

    def draw_circle(self, cx, cy, radius, facecolor, edgecolor, linewidth, alpha):
        raise NotImplementedError

    def draw_polygon(self, x_pts, y_pts, facecolor, edgecolor, linewidth, alpha):
        raise NotImplementedError

    def draw_text(self, x, y, text, fontsize, color, ha, va, rotation, alpha):
        raise NotImplementedError

    def set_clip_rect(self, x, y, width, height):
        raise NotImplementedError

    def clear_clip(self):
        raise NotImplementedError

    def get_result(self):
        raise NotImplementedError
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`
Expected: All PASS

**Step 5: Run full test suite for no regressions**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 6: Commit**

```bash
git add python/matplotlib/backend_bases.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add RendererBase and AxesLayout abstractions"
```

---

### Task 2: Implement RendererSVG

**Files:**
- Modify: `python/matplotlib/_svg_backend.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** Rewrite _svg_backend.py to contain a `RendererSVG` class that implements `RendererBase`. Keep the old `render_figure_svg()` function working alongside it for now (it will be removed later). Also keep `_nice_ticks`, `_fmt_tick`, `_esc`, `_svg_dash` as module-level helpers since they're used by the PIL backend and by Axes draw logic later.

**Step 1: Add RendererSVG tests to test_backend_bases.py**

Append these tests:

```python
from matplotlib._svg_backend import RendererSVG


class TestRendererSVG:
    def test_init(self):
        r = RendererSVG(640, 480, 100)
        assert r.width == 640
        assert r.height == 480

    def test_draw_line_produces_polyline(self):
        r = RendererSVG(640, 480, 100)
        r.draw_line([100, 200], [50, 150], '#ff0000', 1.5, '-', 1.0)
        result = r.get_result()
        assert '<polyline' in result
        assert 'stroke="#ff0000"' in result

    def test_draw_line_dashed(self):
        r = RendererSVG(640, 480, 100)
        r.draw_line([100, 200], [50, 150], '#000', 1.0, '--', 1.0)
        result = r.get_result()
        assert 'stroke-dasharray' in result

    def test_draw_rect_produces_rect(self):
        r = RendererSVG(640, 480, 100)
        r.draw_rect(10, 20, 100, 50, '#0000ff', '#000000', 1.0, 1.0)
        result = r.get_result()
        assert '<rect' in result
        assert 'fill="#0000ff"' in result

    def test_draw_circle_produces_circle(self):
        r = RendererSVG(640, 480, 100)
        r.draw_circle(100, 100, 5, '#ff0000', 'none', 0, 1.0)
        result = r.get_result()
        assert '<circle' in result

    def test_draw_polygon_produces_polygon(self):
        r = RendererSVG(640, 480, 100)
        r.draw_polygon([10, 20, 30], [10, 30, 10], '#00ff00', 'none', 0, 0.5)
        result = r.get_result()
        assert '<polygon' in result
        assert 'fill-opacity="0.5"' in result

    def test_draw_text_produces_text(self):
        r = RendererSVG(640, 480, 100)
        r.draw_text(100, 50, 'Hello', 12, '#000', 'center', 'baseline', 0, 1.0)
        result = r.get_result()
        assert '<text' in result
        assert 'Hello' in result

    def test_draw_markers_produces_circles(self):
        r = RendererSVG(640, 480, 100)
        r.draw_markers([100, 200], [50, 150], 'o', 6.0, '#ff0000', 1.0)
        result = r.get_result()
        assert result.count('<circle') == 2

    def test_get_result_is_valid_svg(self):
        r = RendererSVG(640, 480, 100)
        result = r.get_result()
        assert result.startswith('<svg')
        assert result.endswith('</svg>')

    def test_set_clip_and_clear(self):
        r = RendererSVG(640, 480, 100)
        r.set_clip_rect(10, 10, 100, 100)
        r.draw_line([20, 80], [20, 80], '#000', 1.0, '-', 1.0)
        r.clear_clip()
        result = r.get_result()
        assert 'clipPath' in result

    def test_draw_rect_no_fill(self):
        r = RendererSVG(640, 480, 100)
        r.draw_rect(10, 20, 100, 50, 'none', '#000000', 1.0, 1.0)
        result = r.get_result()
        assert 'fill="none"' in result
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py::TestRendererSVG -x -v`
Expected: FAIL (ImportError — RendererSVG doesn't exist yet)

**Step 3: Implement RendererSVG**

Add the `RendererSVG` class to `python/matplotlib/_svg_backend.py`. Place it after the existing imports, before the existing `render_figure_svg` function. Keep all existing functions intact for now.

```python
from matplotlib.backend_bases import RendererBase


class RendererSVG(RendererBase):
    """SVG renderer implementing RendererBase."""

    def __init__(self, width, height, dpi):
        super().__init__(width, height, dpi)
        self._parts = []
        self._clip_counter = 0
        self._current_clip = None

    def draw_line(self, x_pts, y_pts, color, linewidth, linestyle, alpha):
        if not x_pts or len(x_pts) < 2:
            return
        dash = _svg_dash(linestyle)
        opacity = f' stroke-opacity="{alpha}"' if alpha < 1.0 else ''
        points = ' '.join(f'{x_pts[i]:.2f},{y_pts[i]:.2f}' for i in range(len(x_pts)))
        clip = f' clip-path="url(#{self._current_clip})"' if self._current_clip else ''
        self._parts.append(
            f'<polyline points="{points}" fill="none" '
            f'stroke="{color}" stroke-width="{linewidth}"{dash}{opacity}{clip}/>'
        )

    def draw_markers(self, x_pts, y_pts, marker, markersize, color, alpha):
        import math
        r = max(1, markersize / 2)
        opacity = f' fill-opacity="{alpha}"' if alpha < 1.0 else ''
        clip = f' clip-path="url(#{self._current_clip})"' if self._current_clip else ''
        for i in range(len(x_pts)):
            self._parts.append(
                f'<circle cx="{x_pts[i]:.2f}" cy="{y_pts[i]:.2f}" r="{r:.1f}" '
                f'fill="{color}"{opacity}{clip}/>'
            )

    def draw_rect(self, x, y, width, height, facecolor, edgecolor, linewidth, alpha):
        fc = facecolor if facecolor else 'none'
        ec = edgecolor if edgecolor else 'none'
        opacity = f' fill-opacity="{alpha}"' if alpha < 1.0 else ''
        stroke = f' stroke="{ec}" stroke-width="{linewidth}"' if ec != 'none' else ''
        clip = f' clip-path="url(#{self._current_clip})"' if self._current_clip else ''
        self._parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" '
            f'fill="{fc}"{stroke}{opacity}{clip}/>'
        )

    def draw_circle(self, cx, cy, radius, facecolor, edgecolor, linewidth, alpha):
        fc = facecolor if facecolor else 'none'
        opacity = f' fill-opacity="{alpha}"' if alpha < 1.0 else ''
        stroke = ''
        if edgecolor and edgecolor != 'none':
            stroke = f' stroke="{edgecolor}" stroke-width="{linewidth}"'
        clip = f' clip-path="url(#{self._current_clip})"' if self._current_clip else ''
        self._parts.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.1f}" '
            f'fill="{fc}"{stroke}{opacity}{clip}/>'
        )

    def draw_polygon(self, x_pts, y_pts, facecolor, edgecolor, linewidth, alpha):
        if len(x_pts) < 3:
            return
        fc = facecolor if facecolor else 'none'
        points = ' '.join(f'{x_pts[i]:.2f},{y_pts[i]:.2f}' for i in range(len(x_pts)))
        stroke = ''
        if edgecolor and edgecolor != 'none':
            stroke = f' stroke="{edgecolor}" stroke-width="{linewidth}"'
        clip = f' clip-path="url(#{self._current_clip})"' if self._current_clip else ''
        self._parts.append(
            f'<polygon points="{points}" fill="{fc}" '
            f'fill-opacity="{alpha}"{stroke}{clip}/>'
        )

    def draw_text(self, x, y, text, fontsize, color, ha, va, rotation, alpha):
        anchor_map = {'left': 'start', 'center': 'middle', 'right': 'end'}
        anchor = anchor_map.get(ha, 'start')
        opacity = f' fill-opacity="{alpha}"' if alpha < 1.0 else ''
        rot = ''
        if rotation and rotation != 0:
            rot = f' transform="rotate({-rotation}, {x:.1f}, {y:.1f})"'
        self._parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" '
            f'text-anchor="{anchor}" font-size="{fontsize}" '
            f'fill="{color}"{opacity}{rot}>{_esc(text)}</text>'
        )

    def set_clip_rect(self, x, y, width, height):
        self._clip_counter += 1
        clip_id = f'clip-r-{self._clip_counter}'
        self._current_clip = clip_id
        self._parts.append(f'<defs><clipPath id="{clip_id}">')
        self._parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}"/>'
        )
        self._parts.append('</clipPath></defs>')

    def clear_clip(self):
        self._current_clip = None

    def get_result(self):
        header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">'
        )
        return header + '\n' + '\n'.join(self._parts) + '\n</svg>'
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`
Expected: All PASS

**Step 5: Run full test suite for no regressions**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 6: Commit**

```bash
git add python/matplotlib/_svg_backend.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add RendererSVG implementing RendererBase"
```

---

### Task 3: Implement RendererPIL

**Files:**
- Modify: `python/matplotlib/_pil_backend.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** Add a `RendererPIL` class to _pil_backend.py that implements RendererBase. Keep the old `render_figure_png()` function working for now.

**Step 1: Add RendererPIL tests to test_backend_bases.py**

Append these tests:

```python
from matplotlib._pil_backend import RendererPIL


class TestRendererPIL:
    def test_init(self):
        r = RendererPIL(640, 480, 100)
        assert r.width == 640
        assert r.height == 480

    def test_get_result_returns_png_bytes(self):
        r = RendererPIL(100, 100, 72)
        result = r.get_result()
        assert isinstance(result, bytes)
        # PNG magic bytes
        assert result[:4] == b'\x89PNG'

    def test_draw_line(self):
        r = RendererPIL(100, 100, 72)
        r.draw_line([10, 90], [10, 90], '#ff0000', 1.5, '-', 1.0)
        result = r.get_result()
        assert isinstance(result, bytes)

    def test_draw_rect(self):
        r = RendererPIL(100, 100, 72)
        r.draw_rect(10, 10, 80, 80, '#0000ff', '#000000', 1.0, 1.0)
        result = r.get_result()
        assert isinstance(result, bytes)

    def test_draw_circle(self):
        r = RendererPIL(100, 100, 72)
        r.draw_circle(50, 50, 20, '#ff0000', 'none', 0, 1.0)
        result = r.get_result()
        assert isinstance(result, bytes)

    def test_draw_polygon(self):
        r = RendererPIL(100, 100, 72)
        r.draw_polygon([10, 50, 90], [90, 10, 90], '#00ff00', 'none', 0, 1.0)
        result = r.get_result()
        assert isinstance(result, bytes)

    def test_draw_text(self):
        r = RendererPIL(100, 100, 72)
        r.draw_text(50, 50, 'Hi', 12, '#000', 'left', 'baseline', 0, 1.0)
        result = r.get_result()
        assert isinstance(result, bytes)

    def test_draw_markers(self):
        r = RendererPIL(100, 100, 72)
        r.draw_markers([20, 80], [20, 80], 'o', 6.0, '#ff0000', 1.0)
        result = r.get_result()
        assert isinstance(result, bytes)
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py::TestRendererPIL -x -v`
Expected: FAIL (ImportError)

**Step 3: Implement RendererPIL**

Add to `python/matplotlib/_pil_backend.py`, before the existing functions:

```python
from matplotlib.backend_bases import RendererBase
import io


class RendererPIL(RendererBase):
    """PIL/PNG renderer implementing RendererBase."""

    def __init__(self, width, height, dpi):
        super().__init__(width, height, dpi)
        from PIL import Image, ImageDraw
        self._img = Image.new('RGB', (width, height), (255, 255, 255))
        self._draw = ImageDraw.Draw(self._img)
        self._clip = None  # (x, y, x2, y2) or None

    def _in_clip(self, x, y):
        """Check if point is within clip rect (basic clipping)."""
        if self._clip is None:
            return True
        cx, cy, cx2, cy2 = self._clip
        return cx <= x <= cx2 and cy <= y <= cy2

    def draw_line(self, x_pts, y_pts, color, linewidth, linestyle, alpha):
        if len(x_pts) < 2:
            return
        fill = _to_rgb_255(color)
        w = max(1, int(linewidth))
        for i in range(len(x_pts) - 1):
            self._draw.line(
                [(int(x_pts[i]), int(y_pts[i])),
                 (int(x_pts[i + 1]), int(y_pts[i + 1]))],
                fill=fill, width=w
            )

    def draw_markers(self, x_pts, y_pts, marker, markersize, color, alpha):
        fill = _to_rgb_255(color)
        r = max(1, int(markersize / 2))
        for i in range(len(x_pts)):
            cx, cy = int(x_pts[i]), int(y_pts[i])
            self._draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=fill)

    def draw_rect(self, x, y, width, height, facecolor, edgecolor, linewidth, alpha):
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + width), int(y + height)
        fc = None
        if facecolor and facecolor != 'none':
            fc = _to_rgb_255(facecolor)
        ec = None
        if edgecolor and edgecolor != 'none':
            ec = _to_rgb_255(edgecolor)
        self._draw.rectangle([(x1, y1), (x2, y2)], fill=fc, outline=ec,
                             width=max(1, int(linewidth)) if ec else 0)

    def draw_circle(self, cx, cy, radius, facecolor, edgecolor, linewidth, alpha):
        fc = None
        if facecolor and facecolor != 'none':
            fc = _to_rgb_255(facecolor)
        ec = None
        if edgecolor and edgecolor != 'none':
            ec = _to_rgb_255(edgecolor)
        r = int(radius)
        self._draw.ellipse(
            [(int(cx) - r, int(cy) - r), (int(cx) + r, int(cy) + r)],
            fill=fc, outline=ec
        )

    def draw_polygon(self, x_pts, y_pts, facecolor, edgecolor, linewidth, alpha):
        if len(x_pts) < 3:
            return
        fc = None
        if facecolor and facecolor != 'none':
            fc = _to_rgb_255(facecolor)
        points = [(int(x_pts[i]), int(y_pts[i])) for i in range(len(x_pts))]
        self._draw.polygon(points, fill=fc)

    def draw_text(self, x, y, text, fontsize, color, ha, va, rotation, alpha):
        try:
            fill = _to_rgb_255(color)
        except Exception:
            fill = (0, 0, 0)
        self._draw.text((int(x), int(y)), text, fill=fill)

    def set_clip_rect(self, x, y, width, height):
        self._clip = (x, y, x + width, y + height)

    def clear_clip(self):
        self._clip = None

    def get_result(self):
        buf = io.BytesIO()
        self._img.save(buf, format='PNG')
        return buf.getvalue()
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`
Expected: All PASS

**Step 5: Run full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 6: Commit**

```bash
git add python/matplotlib/_pil_backend.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add RendererPIL implementing RendererBase"
```

---

### Task 4: Add draw() to Line2D

**Files:**
- Modify: `python/matplotlib/lines.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** Line2D gets a `draw(renderer, layout)` method. It transforms its data using layout.sx/layout.sy and calls renderer.draw_line + renderer.draw_markers.

**Step 1: Add test**

Append to test_backend_bases.py:

```python
from matplotlib.lines import Line2D
from matplotlib.backend_bases import AxesLayout
from matplotlib._svg_backend import RendererSVG


class TestLine2DDraw:
    def _make_layout(self):
        return AxesLayout(
            plot_x=70, plot_y=40, plot_w=550, plot_h=390,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )

    def test_draw_produces_polyline(self):
        line = Line2D([0, 5, 10], [0, 10, 5], color='#ff0000', linewidth=2.0)
        r = RendererSVG(640, 480, 100)
        line.draw(r, self._make_layout())
        result = r.get_result()
        assert '<polyline' in result
        assert 'stroke="#ff0000"' in result

    def test_draw_with_marker(self):
        line = Line2D([0, 10], [0, 10], color='#000', marker='o')
        r = RendererSVG(640, 480, 100)
        line.draw(r, self._make_layout())
        result = r.get_result()
        assert '<circle' in result

    def test_draw_invisible_produces_nothing(self):
        line = Line2D([0, 10], [0, 10], color='#000')
        line.set_visible(False)
        r = RendererSVG(640, 480, 100)
        line.draw(r, self._make_layout())
        result = r.get_result()
        assert '<polyline' not in result

    def test_draw_none_linestyle_no_polyline(self):
        line = Line2D([0, 10], [0, 10], color='#000', linestyle='None', marker='o')
        r = RendererSVG(640, 480, 100)
        line.draw(r, self._make_layout())
        result = r.get_result()
        assert '<polyline' not in result
        assert '<circle' in result
```

**Step 2: Run to verify fail**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py::TestLine2DDraw -x -v`
Expected: FAIL (AttributeError: Line2D has no draw method)

**Step 3: Implement draw() on Line2D**

Add to `python/matplotlib/lines.py`, after the `_as_element` method:

```python
    def draw(self, renderer, layout):
        """Draw this line onto the renderer using layout for coordinate mapping."""
        if not self.get_visible():
            return
        x_px = [layout.sx(v) for v in self._xdata]
        y_px = [layout.sy(v) for v in self._ydata]
        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        color = to_hex(self._color)

        # Draw line
        if (self._linestyle not in ('None', 'none', '')
                and len(x_px) >= 2):
            renderer.draw_line(x_px, y_px, color,
                               float(self._linewidth), self._linestyle, alpha)

        # Draw markers
        if self._marker and self._marker not in ('None', 'none', ''):
            renderer.draw_markers(x_px, y_px, self._marker,
                                  float(self._markersize), color, alpha)
```

**Step 4: Run tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`
Expected: All PASS

**Step 5: Full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 6: Commit**

```bash
git add python/matplotlib/lines.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add draw() method to Line2D"
```

---

### Task 5: Add draw() to Rectangle, Circle, and new Polygon patch

**Files:**
- Modify: `python/matplotlib/patches.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** Rectangle and Circle get `draw(renderer, layout)`. Also add a new `Polygon` patch class for fill_between support.

**Step 1: Add tests**

Append to test_backend_bases.py:

```python
from matplotlib.patches import Rectangle, Circle, Polygon


class TestRectangleDraw:
    def _make_layout(self):
        return AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )

    def test_draw_produces_rect(self):
        rect = Rectangle((2, 0), 3, 5, facecolor='#0000ff', edgecolor='#000000')
        r = RendererSVG(100, 100, 100)
        rect.draw(r, self._make_layout())
        result = r.get_result()
        assert '<rect' in result

    def test_draw_invisible(self):
        rect = Rectangle((0, 0), 5, 5)
        rect.set_visible(False)
        r = RendererSVG(100, 100, 100)
        rect.draw(r, self._make_layout())
        result = r.get_result()
        assert '<rect' not in result


class TestCircleDraw:
    def _make_layout(self):
        return AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )

    def test_draw_produces_circle(self):
        c = Circle((5, 5), 2, facecolor='#ff0000')
        r = RendererSVG(100, 100, 100)
        c.draw(r, self._make_layout())
        result = r.get_result()
        assert '<circle' in result

    def test_draw_invisible(self):
        c = Circle((5, 5), 2)
        c.set_visible(False)
        r = RendererSVG(100, 100, 100)
        c.draw(r, self._make_layout())
        result = r.get_result()
        assert '<circle' not in result


class TestPolygonPatch:
    def test_init(self):
        p = Polygon([(0, 0), (1, 1), (2, 0)], facecolor='#00ff00')
        assert len(p.get_xy()) == 3

    def test_draw_produces_polygon(self):
        p = Polygon([(0, 0), (10, 10), (10, 0)], facecolor='#00ff00')
        layout = AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )
        r = RendererSVG(100, 100, 100)
        p.draw(r, layout)
        result = r.get_result()
        assert '<polygon' in result

    def test_get_set_xy(self):
        p = Polygon([(0, 0), (1, 1)])
        p.set_xy([(2, 2), (3, 3), (4, 4)])
        assert len(p.get_xy()) == 3
```

**Step 2: Run to verify fail**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py::TestRectangleDraw -x -v`
Expected: FAIL

**Step 3: Implement draw() on patches and add Polygon**

Add to `python/matplotlib/patches.py`:

In `Patch` base class, add a helper:

```python
    def _resolved_facecolor_hex(self):
        """Return facecolor as hex string, handling 'none'."""
        fc = self._facecolor
        if isinstance(fc, str) and fc.lower() == 'none':
            return 'none'
        return to_hex(fc)

    def _resolved_edgecolor_hex(self):
        """Return edgecolor as hex string, handling 'none'."""
        ec = self._edgecolor
        if isinstance(ec, str) and ec.lower() == 'none':
            return 'none'
        return to_hex(ec)
```

Add import at top of patches.py: `from matplotlib.colors import to_rgba, to_hex`

In `Rectangle`, add:

```python
    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        x0, y0 = self._xy
        x1 = x0 + self._width
        y1 = y0 + self._height

        # Transform corners to pixel coords
        px_left = layout.sx(x0)
        px_right = layout.sx(x1)
        px_top = layout.sy(y1)     # y1 is top in data, maps to smaller pixel y
        px_bottom = layout.sy(y0)  # y0 is bottom in data, maps to larger pixel y

        pw = px_right - px_left
        ph = px_bottom - px_top
        if pw <= 0 or ph <= 0:
            return

        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        renderer.draw_rect(
            px_left, px_top, pw, ph,
            self._resolved_facecolor_hex(),
            self._resolved_edgecolor_hex(),
            self._linewidth, alpha,
        )
```

In `Circle`, add:

```python
    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        cx_px = layout.sx(self._center[0])
        cy_px = layout.sy(self._center[1])
        # Scale radius using x-axis (approximate)
        r_px = abs(layout.sx(self._center[0] + self._radius) - cx_px)
        if r_px <= 0:
            return

        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        renderer.draw_circle(
            cx_px, cy_px, r_px,
            self._resolved_facecolor_hex(),
            self._resolved_edgecolor_hex(),
            self._linewidth, alpha,
        )
```

Add new `Polygon` class after `Circle`:

```python
class Polygon(Patch):
    """A polygon defined by a list of (x, y) vertices."""

    def __init__(self, xy, closed=True, **kwargs):
        self._xy = [tuple(pt) for pt in xy]
        self._closed = closed
        super().__init__(**kwargs)

    def get_xy(self):
        return list(self._xy)

    def set_xy(self, xy):
        self._xy = [tuple(pt) for pt in xy]

    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        if len(self._xy) < 3:
            return
        x_px = [layout.sx(pt[0]) for pt in self._xy]
        y_px = [layout.sy(pt[1]) for pt in self._xy]
        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        renderer.draw_polygon(
            x_px, y_px,
            self._resolved_facecolor_hex(),
            self._resolved_edgecolor_hex(),
            self._linewidth, alpha,
        )
```

**Step 4: Run tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`
Expected: All PASS

**Step 5: Full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 6: Commit**

```bash
git add python/matplotlib/patches.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add draw() to Rectangle, Circle, and new Polygon patch"
```

---

### Task 6: Add draw() to PathCollection and Text

**Files:**
- Modify: `python/matplotlib/collections.py`
- Modify: `python/matplotlib/text.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Step 1: Add tests**

```python
from matplotlib.collections import PathCollection
from matplotlib.text import Text, Annotation


class TestPathCollectionDraw:
    def _make_layout(self):
        return AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )

    def test_draw_produces_circles(self):
        pc = PathCollection(offsets=[(2, 3), (5, 7)], sizes=[20],
                            facecolors=['#ff0000'])
        r = RendererSVG(100, 100, 100)
        pc.draw(r, self._make_layout())
        result = r.get_result()
        assert result.count('<circle') == 2

    def test_draw_empty(self):
        pc = PathCollection(offsets=[], sizes=[20], facecolors=['#ff0000'])
        r = RendererSVG(100, 100, 100)
        pc.draw(r, self._make_layout())
        result = r.get_result()
        assert '<circle' not in result

    def test_draw_invisible(self):
        pc = PathCollection(offsets=[(5, 5)], sizes=[20], facecolors=['#ff0000'])
        pc.set_visible(False)
        r = RendererSVG(100, 100, 100)
        pc.draw(r, self._make_layout())
        result = r.get_result()
        assert '<circle' not in result


class TestTextDraw:
    def _make_layout(self):
        return AxesLayout(
            plot_x=0, plot_y=0, plot_w=100, plot_h=100,
            xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0,
        )

    def test_draw_produces_text(self):
        t = Text(5, 5, 'hello')
        r = RendererSVG(100, 100, 100)
        t.draw(r, self._make_layout())
        result = r.get_result()
        assert 'hello' in result
        assert '<text' in result

    def test_draw_invisible(self):
        t = Text(5, 5, 'hidden')
        t.set_visible(False)
        r = RendererSVG(100, 100, 100)
        t.draw(r, self._make_layout())
        result = r.get_result()
        assert 'hidden' not in result
```

**Step 2: Run to verify fail**

**Step 3: Implement**

In `python/matplotlib/collections.py`, add to `PathCollection`:

```python
    def draw(self, renderer, layout):
        """Draw scatter points using renderer."""
        if not self.get_visible():
            return
        if not self._offsets:
            return
        import math
        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0

        # Determine color
        if self._facecolors:
            color = to_hex(self._facecolors[0])
        else:
            color = to_hex('C0')

        # Determine size -> radius
        s = self._sizes[0] if self._sizes else 20.0
        r = max(1.0, math.sqrt(s) / 2)

        for pt in self._offsets:
            cx = layout.sx(pt[0])
            cy = layout.sy(pt[1])
            renderer.draw_circle(cx, cy, r, color, 'none', 0, alpha)
```

In `python/matplotlib/text.py`, add to `Text` (after `set_position`):

```python
    def draw(self, renderer, layout):
        """Draw this text using the renderer."""
        if not self.get_visible():
            return
        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        px = layout.sx(self._x)
        py = layout.sy(self._y)
        color = '#000000'  # default text color
        renderer.draw_text(px, py, self._text, self._fontsize, color,
                           self._ha, self._va, self._rotation, alpha)
```

**Step 4: Run tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`

**Step 5: Full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`

**Step 6: Commit**

```bash
git add python/matplotlib/collections.py python/matplotlib/text.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add draw() to PathCollection and Text"
```

---

### Task 7: Add Axes.draw(renderer) and Axes._compute_layout()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** This is the big integration piece. Axes gets `_compute_layout()` to create an AxesLayout, and `draw(renderer)` that draws the frame, grid, ticks, artists, title, labels, and legend. This replaces the logic currently in `_render_axes` in both backends.

**Step 1: Add tests**

```python
import matplotlib.pyplot as plt


class TestAxesDraw:
    def test_empty_axes_draw(self):
        """Drawing empty axes should produce frame and ticks without errors."""
        fig, ax = plt.subplots()
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        # Should have the frame rect
        assert '<rect' in result
        plt.close('all')

    def test_axes_draw_with_line(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 0])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<polyline' in result
        plt.close('all')

    def test_axes_draw_with_scatter(self):
        fig, ax = plt.subplots()
        ax.scatter([1, 2, 3], [1, 2, 3])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<circle' in result
        plt.close('all')

    def test_axes_draw_with_bar(self):
        fig, ax = plt.subplots()
        ax.bar([1, 2, 3], [4, 5, 6])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<rect' in result
        plt.close('all')

    def test_axes_draw_with_title_and_labels(self):
        fig, ax = plt.subplots()
        ax.set_title('Title')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.plot([0, 1], [0, 1])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert 'Title' in result
        plt.close('all')

    def test_axes_draw_with_legend(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], label='data')
        ax.legend()
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert 'data' in result
        plt.close('all')

    def test_axes_draw_with_grid(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.grid(True)
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        # Grid lines should be present (dashed)
        assert 'stroke-dasharray' in result
        plt.close('all')
```

**Step 2: Run to verify fail**

**Step 3: Implement Axes.draw() and _compute_layout()**

Add imports at top of `python/matplotlib/axes.py`:

```python
from matplotlib.backend_bases import AxesLayout
from matplotlib._svg_backend import _nice_ticks, _fmt_tick, _esc
```

Add methods to the Axes class (after `cla()`):

```python
    def _compute_layout(self, fig_w_px, fig_h_px):
        """Compute plot area geometry and data-to-pixel transforms."""
        ml, mr, mt, mb = 70, 20, 40, 50
        plot_x = ml
        plot_y = mt
        plot_w = fig_w_px - ml - mr
        plot_h = fig_h_px - mt - mb

        if plot_w <= 0 or plot_h <= 0:
            return None

        xmin, xmax = self.get_xlim()
        ymin, ymax = self.get_ylim()

        # Padding
        dx = (xmax - xmin) or 1.0
        dy = (ymax - ymin) or 1.0
        xmin -= dx * 0.05
        xmax += dx * 0.05
        ymin -= dy * 0.05
        ymax += dy * 0.05

        return AxesLayout(plot_x, plot_y, plot_w, plot_h,
                          xmin, xmax, ymin, ymax)

    def draw(self, renderer):
        """Draw this axes and all its artists onto the renderer."""
        layout = self._compute_layout(renderer.width, renderer.height)
        if layout is None:
            return

        px, py, pw, ph = layout.plot_x, layout.plot_y, layout.plot_w, layout.plot_h

        # Frame
        renderer.draw_rect(px, py, pw, ph, 'none', '#000000', 1.0, 1.0)

        # Grid
        if self._grid:
            xticks = _nice_ticks(layout.xmin, layout.xmax, 8)
            yticks = _nice_ticks(layout.ymin, layout.ymax, 6)
            for t in xticks:
                tx = layout.sx(t)
                if px < tx < px + pw:
                    renderer.draw_line([tx, tx], [py, py + ph],
                                       '#dddddd', 0.5, '--', 1.0)
            for t in yticks:
                ty = layout.sy(t)
                if py < ty < py + ph:
                    renderer.draw_line([px, px + pw], [ty, ty],
                                       '#dddddd', 0.5, '--', 1.0)

        # Tick marks and labels
        xticks = _nice_ticks(layout.xmin, layout.xmax, 8)
        yticks = _nice_ticks(layout.ymin, layout.ymax, 6)
        for t in xticks:
            tx = layout.sx(t)
            if px <= tx <= px + pw:
                renderer.draw_line([tx, tx], [py + ph, py + ph + 5],
                                   '#000000', 1.0, '-', 1.0)
                renderer.draw_text(tx, py + ph + 18, _fmt_tick(t),
                                   11, '#333333', 'center', 'baseline', 0, 1.0)
        for t in yticks:
            ty = layout.sy(t)
            if py <= ty <= py + ph:
                renderer.draw_line([px - 5, px], [ty, ty],
                                   '#000000', 1.0, '-', 1.0)
                renderer.draw_text(px - 8, ty + 4, _fmt_tick(t),
                                   11, '#333333', 'right', 'baseline', 0, 1.0)

        # Clipping for data area
        renderer.set_clip_rect(px, py, pw, ph)

        # Draw all artists sorted by zorder
        all_artists = []
        for line in self.lines:
            all_artists.append(line)
        for patch in self.patches:
            all_artists.append(patch)
        for coll in self.collections:
            all_artists.append(coll)
        for text_obj in self.texts:
            all_artists.append(text_obj)
        all_artists.sort(key=lambda a: a.get_zorder())

        for artist in all_artists:
            if hasattr(artist, 'draw') and callable(artist.draw):
                artist.draw(renderer, layout)

        renderer.clear_clip()

        # Title
        if self._title:
            renderer.draw_text(px + pw / 2, py - 10, self._title,
                               14, '#000000', 'center', 'baseline', 0, 1.0)

        # Axis labels
        if self._xlabel and self._xlabel_visible:
            renderer.draw_text(px + pw / 2, renderer.height - 5,
                               self._xlabel, 12, '#333333', 'center',
                               'baseline', 0, 1.0)
        if self._ylabel and self._ylabel_visible:
            ty = py + ph / 2
            renderer.draw_text(15, ty, self._ylabel, 12, '#333333',
                               'center', 'baseline', 90, 1.0)

        # Legend
        if self._legend:
            self._draw_legend(renderer, px + pw - 10, py + 10)

    def _draw_legend(self, renderer, right_x, top_y):
        """Draw a legend box."""
        handles, labels = self.get_legend_handles_labels()
        if not labels:
            return
        lw = 120
        lh = len(labels) * 20 + 10
        lx = right_x - lw
        ly = top_y
        renderer.draw_rect(lx, ly, lw, lh, '#ffffff', '#999999', 0.5, 1.0)

        for i, (handle, label) in enumerate(zip(handles, labels)):
            iy = ly + 15 + i * 20
            # Get color from handle
            color = '#000000'
            if hasattr(handle, 'get_color'):
                from matplotlib.colors import to_hex
                try:
                    color = to_hex(handle.get_color())
                except Exception:
                    pass
            renderer.draw_line([lx + 5, lx + 25], [iy, iy],
                               color, 2.0, '-', 1.0)
            renderer.draw_text(lx + 30, iy + 4, label,
                               11, '#333333', 'left', 'baseline', 0, 1.0)
```

**Step 4: Run tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`

**Step 5: Full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`

**Step 6: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add Axes.draw(renderer) with layout computation"
```

---

### Task 8: Add Figure.draw(renderer) and rewire savefig()

**Files:**
- Modify: `python/matplotlib/figure.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** Figure gets `draw(renderer)` that iterates axes and draws figure-level text. Then `savefig()` is rewired to create a Renderer and call `self.draw(renderer)` instead of delegating to old functions.

**Step 1: Add tests**

```python
from matplotlib.figure import Figure


class TestFigureDraw:
    def test_figure_draw_empty(self):
        fig = Figure()
        r = RendererSVG(640, 480, 100)
        fig.draw(r)
        result = r.get_result()
        assert '<svg' in result

    def test_figure_draw_with_axes(self):
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([0, 1], [0, 1])
        r = RendererSVG(640, 480, 100)
        fig.draw(r)
        result = r.get_result()
        assert '<polyline' in result

    def test_figure_draw_with_suptitle(self):
        fig = Figure()
        fig.suptitle('My Title')
        fig.add_subplot(1, 1, 1)
        r = RendererSVG(640, 480, 100)
        fig.draw(r)
        result = r.get_result()
        assert 'My Title' in result

    def test_savefig_svg_uses_new_renderer(self, tmp_path):
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([0, 1, 2], [0, 1, 0])
        path = str(tmp_path / 'test.svg')
        fig.savefig(path)
        with open(path) as f:
            content = f.read()
        assert '<svg' in content
        assert '<polyline' in content

    def test_savefig_png_uses_new_renderer(self, tmp_path):
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([0, 1], [0, 1])
        path = str(tmp_path / 'test.png')
        fig.savefig(path, format='png')
        with open(path, 'rb') as f:
            data = f.read()
        assert data[:4] == b'\x89PNG'
```

**Step 2: Run to verify fail**

**Step 3: Implement Figure.draw() and rewire savefig()**

In `python/matplotlib/figure.py`, add `draw(renderer)` method and modify `savefig`:

```python
    def draw(self, renderer):
        """Draw the figure and all its contents onto the renderer."""
        # White background
        renderer.draw_rect(0, 0, renderer.width, renderer.height,
                           '#ffffff', 'none', 0, 1.0)

        # Draw all axes
        for ax in self._axes:
            ax.draw(renderer)

        # Draw figure-level text (suptitle)
        if self._suptitle:
            renderer.draw_text(
                renderer.width / 2, 20, self._suptitle,
                14, '#000000', 'center', 'baseline', 0, 1.0)
```

Modify `savefig` to use the new renderer:

```python
    def savefig(self, fname, *, format=None, dpi=None, **kwargs):
        """Save figure to *fname*.  Format inferred from extension if not given."""
        dpi = dpi or self.dpi
        if format is None and isinstance(fname, str):
            if fname.lower().endswith('.png'):
                format = 'png'
            elif fname.lower().endswith('.svg'):
                format = 'svg'
            else:
                format = 'svg'

        w_px = int(self.figsize[0] * dpi)
        h_px = int(self.figsize[1] * dpi)

        if format == 'png':
            from matplotlib._pil_backend import RendererPIL
            renderer = RendererPIL(w_px, h_px, dpi)
        else:
            from matplotlib._svg_backend import RendererSVG
            renderer = RendererSVG(w_px, h_px, dpi)

        self.draw(renderer)
        result = renderer.get_result()

        if isinstance(result, bytes):
            with open(fname, 'wb') as f:
                f.write(result)
        else:
            with open(fname, 'w') as f:
                f.write(result)
```

Note: Remove the `from matplotlib.text import Text` import at the top of figure.py — it's no longer needed by suptitle since we're using draw() now. Actually, keep it — suptitle still creates a Text object for `self.texts`.

**Step 4: Run tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`

**Step 5: Full suite** — this is critical since savefig() changed

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 6: Commit**

```bash
git add python/matplotlib/figure.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: add Figure.draw(renderer) and rewire savefig to use renderers"
```

---

### Task 9: Handle barh, errorbar, fill_between, fill_betweenx, axhline, axvline in Axes.draw()

**Files:**
- Modify: `python/matplotlib/axes.py`
- Test: `python/matplotlib/tests/test_backend_bases.py` (append)

**Context:** Several plot types currently only exist in `_elements` with no artist objects: `barh`, `fill_between`, `fill_betweenx`. And `axhline`/`axvline` have Line2D objects but need special rendering (spanning the plot area). `errorbar` has a container but the error whiskers themselves are in `_elements` only.

We need to:
1. Make `fill_between` / `fill_betweenx` create Polygon artists
2. Make `barh` create Rectangle artists
3. Make `errorbar` store whisker data on the container so Axes.draw can render them
4. Mark `axhline`/`axvline` Line2D objects with a flag so Axes.draw renders them spanning the plot area

**Step 1: Add tests**

```python
class TestAxesDrawPlotTypes:
    def test_fill_between(self):
        fig, ax = plt.subplots()
        ax.fill_between([0, 1, 2], [0, 1, 0], [0, 0, 0])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<polygon' in result
        plt.close('all')

    def test_fill_betweenx(self):
        fig, ax = plt.subplots()
        ax.fill_betweenx([0, 1, 2], [0, 1, 0], [0, 0, 0])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<polygon' in result
        plt.close('all')

    def test_barh(self):
        fig, ax = plt.subplots()
        ax.barh([0, 1, 2], [3, 5, 2])
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<rect' in result
        plt.close('all')

    def test_errorbar(self):
        fig, ax = plt.subplots()
        ax.errorbar([0, 1, 2], [1, 2, 1], yerr=0.5)
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        # Should have the data line and error whiskers
        assert '<polyline' in result or '<line' in result
        plt.close('all')

    def test_axhline(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])  # need data for limits
        ax.axhline(y=0.5)
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<polyline' in result or '<line' in result
        plt.close('all')

    def test_axvline(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.axvline(x=0.5)
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert '<polyline' in result or '<line' in result
        plt.close('all')

    def test_text(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.text(0.5, 0.5, 'Hello')
        r = RendererSVG(640, 480, 100)
        ax.draw(r)
        result = r.get_result()
        assert 'Hello' in result
        plt.close('all')
```

**Step 2: Run to verify fail**

**Step 3: Modify Axes plot methods**

These changes go in `python/matplotlib/axes.py`.

**fill_between — create a Polygon instead of just a dict:**

```python
    def fill_between(self, x, y1, y2=0, **kwargs):
        """Fill between two curves."""
        _validate_1d(x, 'x')
        _validate_1d(y1, 'y1')
        if hasattr(y2, '__iter__'):
            _validate_1d(y2, 'y2')

        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        alpha = kwargs.get('alpha', 0.5)

        x_list = list(x)
        y1_list = list(y1)
        y2_list = list(y2) if hasattr(y2, '__iter__') else [y2] * len(x_list)

        # Build polygon vertices: forward along y1, backward along y2
        verts = []
        for i in range(len(x_list)):
            verts.append((x_list[i], y1_list[i]))
        for i in range(len(x_list) - 1, -1, -1):
            verts.append((x_list[i], y2_list[i]))

        from matplotlib.patches import Polygon
        poly = Polygon(verts, facecolor=color, edgecolor='none')
        poly.set_alpha(alpha)
        if label:
            poly.set_label(label)
        poly.axes = self
        poly.figure = self.figure
        self.patches.append(poly)

        # Keep _elements for backward compat during transition
        elem = {
            'type': 'fill_between',
            'x': x_list, 'y1': y1_list, 'y2': y2_list,
            'color': color, 'alpha': alpha, 'label': label,
        }
        self._elements.append(elem)
        return poly
```

**fill_betweenx — same pattern but horizontal:**

```python
    def fill_betweenx(self, y, x1, x2=0, **kwargs):
        """Fill between two curves in the x-direction."""
        _validate_1d(y, 'y')
        _validate_1d(x1, 'x1')
        if hasattr(x2, '__iter__'):
            _validate_1d(x2, 'x2')

        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        alpha = kwargs.get('alpha', 0.5)

        y_list = list(y)
        x1_list = list(x1)
        x2_list = list(x2) if hasattr(x2, '__iter__') else [x2] * len(y_list)

        # Build polygon: forward along x1, backward along x2
        verts = []
        for i in range(len(y_list)):
            verts.append((x1_list[i], y_list[i]))
        for i in range(len(y_list) - 1, -1, -1):
            verts.append((x2_list[i], y_list[i]))

        from matplotlib.patches import Polygon
        poly = Polygon(verts, facecolor=color, edgecolor='none')
        poly.set_alpha(alpha)
        if label:
            poly.set_label(label)
        poly.axes = self
        poly.figure = self.figure
        self.patches.append(poly)

        elem = {
            'type': 'fill_betweenx',
            'y': y_list, 'x1': x1_list, 'x2': x2_list,
            'color': color, 'alpha': alpha, 'label': label,
        }
        self._elements.append(elem)
        return poly
```

**barh — create Rectangle patches:**

```python
    def barh(self, y, width, height=0.8, **kwargs):
        """Horizontal bar chart."""
        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        y_vals = list(y)
        w_vals = list(width)

        rect_patches = []
        for i in range(len(y_vals)):
            y_center = y_vals[i]
            w = w_vals[i]
            rect = Rectangle(
                (0, y_center - height / 2),
                w,
                height,
                facecolor=color,
                edgecolor='black',
            )
            rect.axes = self
            rect.figure = self.figure
            self.patches.append(rect)
            rect_patches.append(rect)

        bc = BarContainer(rect_patches, label=label)
        self.containers.append(bc)

        elem = {
            'type': 'barh',
            'y': y_vals, 'width': w_vals, 'height': height,
            'color': color, 'label': label,
        }
        self._elements.append(elem)
        return bc
```

**axhline / axvline — tag the Line2D so Axes.draw knows to span the plot:**

Add a `_spanning` attribute. In `axhline`:

```python
    def axhline(self, y=0, **kwargs):
        """Add a horizontal line across the axes."""
        color = kwargs.get('color') or kwargs.get('c', 'black')
        color = to_hex(color)
        linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.0))
        label = kwargs.get('label')

        line = Line2D(
            [0], [y],
            color=color, linewidth=linewidth, linestyle=linestyle, label=label,
        )
        line._spanning = 'horizontal'
        line.axes = self
        line.figure = self.figure
        self.lines.append(line)

        elem = {
            'type': 'axhline',
            'x': [], 'y': [y], 'color': color,
            'linestyle': linestyle, 'linewidth': linewidth,
            'label': label,
        }
        self._elements.append(elem)
        return line
```

In `axvline`, same pattern with `line._spanning = 'vertical'`.

**errorbar — store whisker data on the container:**

In `errorbar`, add `_xerr_data` and `_yerr_data` to the container:

```python
        ec._yerr_data = (x_list, y_list, yerr) if yerr is not None else None
        ec._xerr_data = (x_list, y_list, xerr) if xerr is not None else None
```

**Then update Axes.draw to handle spanning lines and errorbar whiskers.**

In the `draw()` method, after drawing all artists and before `renderer.clear_clip()`, add special handling:

```python
        # Draw spanning lines (axhline/axvline) — they span the full plot area
        for line in self.lines:
            if not line.get_visible():
                continue
            spanning = getattr(line, '_spanning', None)
            if spanning == 'horizontal':
                y_val = line._ydata[0]
                py_val = layout.sy(y_val)
                alpha = line.get_alpha() if line.get_alpha() is not None else 1.0
                renderer.draw_line(
                    [float(px), float(px + pw)], [py_val, py_val],
                    to_hex(line._color), float(line._linewidth),
                    line._linestyle, alpha)
            elif spanning == 'vertical':
                x_val = line._xdata[0]
                px_val = layout.sx(x_val)
                alpha = line.get_alpha() if line.get_alpha() is not None else 1.0
                renderer.draw_line(
                    [px_val, px_val], [float(py), float(py + ph)],
                    to_hex(line._color), float(line._linewidth),
                    line._linestyle, alpha)

        # Draw errorbar whiskers
        for container in self.containers:
            if hasattr(container, '_yerr_data') and container._yerr_data:
                x_list, y_list, yerr = container._yerr_data
                yerr_list = list(yerr) if hasattr(yerr, '__iter__') else [yerr] * len(x_list)
                color = '#000000'
                if hasattr(container, 'lines') and container.lines[0]:
                    color = to_hex(container.lines[0]._color)
                for i in range(len(x_list)):
                    err = yerr_list[i] if i < len(yerr_list) else yerr_list[-1]
                    cx = layout.sx(x_list[i])
                    y_lo = layout.sy(y_list[i] - err)
                    y_hi = layout.sy(y_list[i] + err)
                    renderer.draw_line([cx, cx], [y_lo, y_hi], color, 1.0, '-', 1.0)
                    cap = 3
                    renderer.draw_line([cx - cap, cx + cap], [y_lo, y_lo], color, 1.0, '-', 1.0)
                    renderer.draw_line([cx - cap, cx + cap], [y_hi, y_hi], color, 1.0, '-', 1.0)

            if hasattr(container, '_xerr_data') and container._xerr_data:
                x_list, y_list, xerr = container._xerr_data
                xerr_list = list(xerr) if hasattr(xerr, '__iter__') else [xerr] * len(x_list)
                color = '#000000'
                if hasattr(container, 'lines') and container.lines[0]:
                    color = to_hex(container.lines[0]._color)
                for i in range(len(x_list)):
                    err = xerr_list[i] if i < len(xerr_list) else xerr_list[-1]
                    cy = layout.sy(y_list[i])
                    x_lo = layout.sx(x_list[i] - err)
                    x_hi = layout.sx(x_list[i] + err)
                    renderer.draw_line([x_lo, x_hi], [cy, cy], color, 1.0, '-', 1.0)
                    cap = 3
                    renderer.draw_line([x_lo, x_lo], [cy - cap, cy + cap], color, 1.0, '-', 1.0)
                    renderer.draw_line([x_hi, x_hi], [cy - cap, cy + cap], color, 1.0, '-', 1.0)
```

Also, in the artist drawing loop, skip spanning lines (they're drawn separately):

```python
        for artist in all_artists:
            if hasattr(artist, '_spanning') and artist._spanning:
                continue  # drawn separately
            if hasattr(artist, 'draw') and callable(artist.draw):
                artist.draw(renderer, layout)
```

**Step 4: Run tests**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/test_backend_bases.py -x -v`

**Step 5: Full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`

**Step 6: Commit**

```bash
git add python/matplotlib/axes.py python/matplotlib/tests/test_backend_bases.py
git commit -m "feat: convert barh, fill_between, errorbar, axhline/axvline to artist-driven rendering"
```

---

### Task 10: Update _auto_xlim/_auto_ylim to use artists only

**Files:**
- Modify: `python/matplotlib/axes.py`

**Context:** Now that all plot types create proper artists (Rectangle patches for bar/barh, Polygon patches for fill_between, etc.), `_auto_xlim` and `_auto_ylim` can compute ranges from artist lists alone, without the `_elements` fallback.

**Step 1: No new tests needed — existing tests cover this behavior**

**Step 2: Modify _auto_xlim**

```python
    def _auto_xlim(self):
        """Auto-calculate x limits from artist data."""
        xs = []
        for line in self.lines:
            spanning = getattr(line, '_spanning', None)
            if spanning == 'horizontal':
                continue  # axhline doesn't contribute to x range
            if spanning == 'vertical':
                xs.extend(line.get_xdata())
                continue
            xs.extend(line.get_xdata())
        for coll in self.collections:
            for pt in coll.get_offsets():
                xs.append(pt[0])
        for patch in self.patches:
            if hasattr(patch, '_xy') and hasattr(patch, '_width'):
                # Rectangle
                xs.append(patch._xy[0])
                xs.append(patch._xy[0] + patch._width)
            elif hasattr(patch, '_xy'):
                # Polygon
                for pt in patch._xy:
                    xs.append(pt[0])
        if not xs:
            return (0.0, 1.0)
        return (min(xs), max(xs))
```

**Step 3: Modify _auto_ylim**

```python
    def _auto_ylim(self):
        """Auto-calculate y limits from artist data."""
        ys = []
        for line in self.lines:
            spanning = getattr(line, '_spanning', None)
            if spanning == 'vertical':
                continue  # axvline doesn't contribute to y range
            if spanning == 'horizontal':
                ys.extend(line.get_ydata())
                continue
            ys.extend(line.get_ydata())
        for coll in self.collections:
            for pt in coll.get_offsets():
                ys.append(pt[1])
        for patch in self.patches:
            if hasattr(patch, '_xy') and hasattr(patch, '_height'):
                # Rectangle
                ys.append(patch._xy[1])
                ys.append(patch._xy[1] + patch._height)
            elif hasattr(patch, '_xy'):
                # Polygon
                for pt in patch._xy:
                    ys.append(pt[1])
        # Bars start from 0
        if ys and any(hasattr(p, '_height') for p in self.patches):
            ys.append(0)
        if not ys:
            return (0.0, 1.0)
        return (min(ys), max(ys))
```

**Step 4: Run full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed

**Step 5: Commit**

```bash
git add python/matplotlib/axes.py
git commit -m "refactor: compute auto limits from artists instead of _elements"
```

---

### Task 11: Remove _elements and _as_element

**Files:**
- Modify: `python/matplotlib/axes.py` — remove all `self._elements.append(...)` lines, remove `self._elements = []` init
- Modify: `python/matplotlib/lines.py` — remove `_as_element()` method
- Modify: `python/matplotlib/collections.py` — remove `_as_element()` method
- Modify: `python/matplotlib/_svg_backend.py` — remove `render_figure_svg()`, `_render_axes()`, `_draw_*` functions, `_data_range()` (but keep `_nice_ticks`, `_fmt_tick`, `_esc`, `_svg_dash`, `RendererSVG`)
- Modify: `python/matplotlib/_pil_backend.py` — remove `render_figure_png()`, `_render_axes()`, `_draw_*` functions, `_data_range()` (but keep `_to_rgb_255`, `RendererPIL`)
- Modify: `python/matplotlib/tests/test_pyplot.py` — update 2 assertions that reference `_elements`
- Modify: `python/matplotlib/tests/test_axes.py` — update 1 assertion that references `_elements`
- Modify: `python/matplotlib/tests/test_collections.py` — remove `_as_element` test class
- Modify: `python/matplotlib/tests/test_lines.py` — remove `_as_element` tests

**Step 1: Update tests first**

In `test_pyplot.py`, find lines referencing `_elements` and replace with equivalent artist-based assertions:
- `assert len(ax._elements) > 0` → `assert len(ax.lines) > 0 or len(ax.patches) > 0`
- `assert ax._elements == []` → `assert ax.lines == [] and ax.patches == [] and ax.collections == []`

In `test_axes.py`, line 466:
- `assert ax._elements == []` → `assert ax.lines == [] and ax.patches == [] and ax.collections == [] and ax.texts == []`

In `test_collections.py`, remove the entire `_as_element` test class (lines ~317-387).

In `test_lines.py`, remove the `_as_element` tests (test_as_element_type through test_as_element_marker_set, ~lines 168-194).

**Step 2: Remove _elements from Axes.__init__ and cla()**

In `axes.py`:
- Remove `self._elements = []` from `__init__`
- Remove `self._elements.clear()` from `cla()`
- Remove all `self._elements.append(...)` lines from every plot method

**Step 3: Remove _as_element from artists**

In `lines.py`: delete the `_as_element()` method entirely.
In `collections.py`: delete the `_as_element()` method entirely.

**Step 4: Clean up old backend functions**

In `_svg_backend.py`, remove these functions:
- `render_figure_svg()`
- `_render_axes()`
- `_draw_line()`, `_draw_scatter()`, `_draw_bar()`, `_draw_barh()`, `_draw_errorbar()`, `_draw_fill_between()`, `_draw_fill_betweenx()`, `_draw_axhline()`, `_draw_axvline()`, `_draw_text()`, `_draw_legend()`
- `_data_range()`

Keep: `RendererSVG`, `_svg_dash()`, `_nice_ticks()`, `_fmt_tick()`, `_esc()`, and the imports.

In `_pil_backend.py`, remove these functions:
- `render_figure_png()`
- `_render_axes()`
- `_draw_line()`, `_draw_scatter()`, `_draw_bar()`, `_draw_barh()`, `_draw_errorbar()`, `_draw_fill_between()`, `_draw_axhline()`, `_draw_axvline()`, `_draw_text()`
- `_data_range()`

Keep: `RendererPIL`, `_to_rgb_255()`, and the imports.

**Step 5: Run full suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x`
Expected: 672+ passed (with updated test assertions)

If any tests fail, fix them — they likely reference `_elements` in ways not caught above.

**Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove _elements and _as_element, complete artist-driven rendering"
```

---

### Task 12: Final cleanup and verification

**Files:**
- All modified files from previous tasks

**Step 1: Search for any remaining _elements references**

Run: `grep -r '_elements' python/matplotlib/`
Expected: No hits (or only in comments)

**Step 2: Search for any remaining _as_element references**

Run: `grep -r '_as_element' python/matplotlib/`
Expected: No hits

**Step 3: Run full test suite**

Run: `target/debug/matplotlib-python -m pytest python/matplotlib/tests/ -x -v`
Expected: All tests pass

**Step 4: Verify savefig still works end-to-end**

```bash
target/debug/matplotlib-python -c "
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3], [0, 1, 4, 9], 'r-o', label='quadratic')
ax.bar([0, 1, 2, 3], [1, 2, 3, 4], alpha=0.3, label='bars')
ax.set_title('Test Plot')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.legend()
ax.grid(True)
fig.savefig('/tmp/test_refactor.svg')
print('SVG saved successfully')
fig.savefig('/tmp/test_refactor.png')
print('PNG saved successfully')
"
```

**Step 5: Commit if needed**

```bash
git add -A
git commit -m "chore: final cleanup of renderer architecture refactor"
```
