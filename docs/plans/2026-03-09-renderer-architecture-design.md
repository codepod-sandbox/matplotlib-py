# Renderer Architecture Design

## Goal

Replace the dual-tracking `_elements` dict pattern with a proper Renderer abstraction and artist-driven rendering, bringing matplotlib-py's architecture closer to real matplotlib while keeping it simple for a savefig-only use case.

## Problem

Every Axes plot method currently stores data in two places:
1. **Artist objects** (Line2D, Rectangle, etc.) in typed lists (`self.lines`, `self.patches`, etc.)
2. **Raw dicts** in `self._elements` via `_as_element()`

Backends only read the dicts. Artists are effectively decorative — they satisfy the API surface but don't participate in rendering. This causes:
- Data duplication and sync issues
- Both backends must be updated for every new plot type
- No clean extension path for new artists (imshow, contour, etc.)

## Design

### RendererBase Interface

New file `python/matplotlib/backend_bases.py`. Abstract class with pixel-coordinate drawing primitives:

- `draw_line(x_pts, y_pts, color, linewidth, linestyle, alpha)`
- `draw_markers(x_pts, y_pts, marker, markersize, color, alpha)`
- `draw_rect(x, y, width, height, facecolor, edgecolor, linewidth, alpha)`
- `draw_circle(cx, cy, radius, facecolor, edgecolor, linewidth, alpha)`
- `draw_polygon(x_pts, y_pts, facecolor, edgecolor, linewidth, alpha)`
- `draw_text(x, y, text, fontsize, color, ha, va, rotation, alpha)`
- `set_clip_rect(x, y, width, height)` / `clear_clip()`
- `get_result()` — returns SVG string or PNG bytes

### Backend Implementations

- `RendererSVG` in `_svg_backend.py` — accumulates SVG fragments
- `RendererPIL` in `_pil_backend.py` — draws via PIL ImageDraw

Backends shrink to just implementing these primitives. No more per-element-type dispatch functions.

### Coordinate Transformation in Axes

Axes computes an `AxesLayout` at draw time containing:
- Plot area bounds (plot_x, plot_y, plot_w, plot_h) in pixels
- Data limits (xmin, xmax, ymin, ymax)
- Transform functions `sx(data_val) -> pixel_x` and `sy(data_val) -> pixel_y`

This replaces the duplicate sx/sy logic currently in both backends.

### Artist draw() Methods

Each artist gets `draw(renderer, layout)`:
- Transforms its own data coordinates to pixels via `layout.sx`/`layout.sy`
- Calls renderer primitives to render itself
- Checks `get_visible()` before drawing

Artists that get draw(): Line2D, Rectangle, Circle, PathCollection, Text, Annotation, and a new Polygon artist.

### New Polygon Artist

`fill_between` currently creates no artist (dict only). A Polygon artist (vertices + facecolor/edgecolor) fills this gap and calls `renderer.draw_polygon()`.

### Axes.draw(renderer) Flow

1. Compute AxesLayout from figure pixel dimensions
2. Draw frame/border via `renderer.draw_rect()`
3. Draw grid lines via `renderer.draw_line()`
4. Draw tick marks and labels
5. Set clip rect to plot area
6. Iterate all artists (from lines, patches, collections, texts) sorted by zorder, call `artist.draw(renderer, layout)`
7. Clear clip
8. Draw title, axis labels, legend

### Figure.draw(renderer) Flow

1. Iterate `self._axes`, call `ax.draw(renderer)`
2. Draw figure-level text (suptitle, supxlabel, supylabel)

### savefig() Flow

```
figure.savefig(fname)
  -> create RendererSVG or RendererPIL(w_px, h_px, dpi)
  -> figure.draw(renderer)
  -> renderer.get_result()
  -> write to file
```

### Eliminated

- `self._elements` list on Axes
- `_as_element()` methods on all artists
- Top-level `render_figure_svg()` and `render_figure_png()` functions
- `_elements` fallback in `_auto_xlim()`/`_auto_ylim()`

### Explicitly Not Done

- No Transform objects (sx/sy functions are sufficient for savefig-only)
- No `draw_image` primitive (added with imshow later)
- No Spine class (frame drawing stays in Axes.draw)
- No Legend artist class (legend drawing stays in Axes.draw)
- No stale-tracking (full redraw each savefig)

## Constraints

- All 672 existing tests pass at every step
- Tests asserting on removed internals (`_elements`, `_as_element`) are updated
- RustPython binary is the test runtime (`target/debug/matplotlib-python -m pytest`)

## Approach

Bottom-up: RendererBase -> backend implementations -> artist draw() methods -> Axes/Figure draw() -> eliminate _elements. Each step is independently testable.
