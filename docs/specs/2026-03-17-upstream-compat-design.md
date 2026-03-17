# Upstream Matplotlib Compatibility — Design

**Date:** 2026-03-17
**Status:** Approved

## Goal

Expand matplotlib-rust's upstream API coverage across five areas: tick formatters/locators, log/symlog scales, legend rendering, arrow annotations, and artist properties (alpha, zorder, linestyle). Each phase adds working implementation plus upstream tests ported from the real matplotlib test suite.

## Repo Rename

`matplotlib-py` → `matplotlib-rust`. Rename the GitHub repository accordingly. Follows the `numpy-rust` / `pillow-rust` naming convention and correctly reflects that the project includes a Rust backend.

## Licensing

- **Repo root:** Add a `LICENSE` file (BSD-3-Clause) and set the license field on the GitHub repository.
- **Copied files** (from CPython matplotlib): retain the original matplotlib copyright block verbatim at the top, followed by our BSD-3-Clause header.
- **New files:** BSD-3-Clause header only.
- matplotlib uses a PSF-derived BSD-compatible license; BSD-3 is compatible.

## Architecture

```
matplotlib-rust/
  python/matplotlib/
    ticker.py          ← copied from matplotlib, adapted
    scale.py           ← copied from matplotlib, adapted
    axis.py            ← new: XAxis/YAxis wrappers
    axes.py            ← modified: integrate scale/axis objects
    legend.py          ← copied from matplotlib, adapted
    patches.py         ← modified: arrow patch geometry
    backend_bases.py   ← modified: draw_arrow primitive
    _svg_backend.py    ← modified: draw_arrow (SVG)
    _pil_backend.py    ← modified: draw_arrow (PIL)
  crates/
    matplotlib-python/ ← existing RustPython binary
    matplotlib-ticker/ ← new (if _ticker C extension needed)
```

**Dependency boundary:** `numpy-rust` is used as-is for array operations. Any functionality that real matplotlib implements via its own C extensions (e.g., `matplotlib._ticker`) is owned here — reimplemented in Python first, with a Rust crate fallback if performance or missing runtime APIs require it.

## Phase 1 — `matplotlib.ticker`

**Files:** `python/matplotlib/ticker.py`, optionally `crates/matplotlib-ticker/`

Copy real matplotlib's `ticker.py` verbatim. Required adaptations:
- Replace `matplotlib._ticker` (C extension) imports: reimplement `_Edge_integer` and related in Python; promote to Rust crate only if needed
- Replace `rcParams` lookups with calls to our `rcsetup.py` equivalents or hardcoded defaults
- Drop `DateLocator`/`DateFormatter` (out of scope; date transforms not implemented)
- All numpy usage copies as-is (numpy-rust provides `np.log`, `np.power`, etc.)

**Formatters included:** `Formatter`, `NullFormatter`, `FixedFormatter`, `FuncFormatter`, `ScalarFormatter`, `LogFormatter`, `LogFormatterSciNotation`, `PercentFormatter`, `StrMethodFormatter`

**Locators included:** `Locator`, `NullLocator`, `FixedLocator`, `MultipleLocator`, `AutoLocator`, `LogLocator`, `MaxNLocator`

**New `axis.py`:** Thin `Axis` class holding a `major` and `minor` ticker (formatter + locator pair). Exposes:
- `set_major_formatter(fmt)` / `get_major_formatter()`
- `set_major_locator(loc)` / `get_major_locator()`
- `set_minor_locator(loc)` / `get_minor_locator()`
- `set_ticks(ticks)` / `get_ticks()`

`Axes.xaxis` and `Axes.yaxis` are `XAxis`/`YAxis` instances. Current hardcoded tick generation in axes/renderers is replaced by locator tick positions and formatter labels.

**Upstream tests:** Port `test_formatter_str`, `test_scalar_formatter`, `test_logformatter`, `test_auto_locator`, `test_multiple_locator`, `test_maxn_locator` from `lib/matplotlib/tests/test_ticker.py`.

## Phase 2 — Log/Symlog Scale Rendering

**Files:** `python/matplotlib/scale.py`, `python/matplotlib/axis.py` (extended), `python/matplotlib/axes.py`

Copy real matplotlib's `scale.py` verbatim. Adaptations: same rcParams and C-extension rules as Phase 1.

**Scale objects:** `LinearScale`, `LogScale`, `SymmetricalLogScale` (symlog), `FuncScale`. Each exposes:
- `forward(values)` — data → transformed coordinate
- `inverse(values)` — transformed → data
- `get_transform()` — returns a `ScaleTransform` usable by tick locators

**Integration:** Each `Axis` holds a `Scale` object (default `LinearScale`). `ax.set_xscale('log')` / `ax.set_yscale('log')` sets the axis scale and updates the default locator/formatter to `LogLocator`/`LogFormatter`. Data-to-pixel mapping in the renderers passes values through `scale.forward()` before the linear pixel mapping step.

**Upstream tests:** Port `test_logscale_nonpos`, `test_logscale_mask`, `test_symlog`, `test_symlog2` from `lib/matplotlib/tests/test_axes.py`.

## Phase 3 — `ax.legend()`

**Files:** `python/matplotlib/legend.py`, `python/matplotlib/axes.py`

Copy real matplotlib's `legend.py`. Adaptations:
- Drop handler map extensibility (keep default handlers: Line2D → line swatch, Patch → colored box)
- Drop shadow, fancy box, draggable
- Drop `BboxTransformTo` / `BboxTransformFrom` (replace with direct pixel math)
- Retain: `loc`, `ncol`, `bbox_to_anchor`, `framealpha`, `title`, `handles`/`labels`, `fontsize`

**Rendering:** Legend box is drawn using existing renderer primitives (`draw_rectangle`, `draw_text`, `draw_line`). No new renderer primitives needed.

`ax.legend()` returns a `Legend` object. `Figure.draw()` calls `ax.legend_.draw(renderer, layout)` after plotting artists.

**Upstream tests:** Port `test_legend_auto`, `test_legend_loc`, `test_legend_ncol`, `test_no_handles_labels`, `test_legend_title` from `lib/matplotlib/tests/test_legend.py`.

## Phase 4 — Arrow Annotations

**Files:** `python/matplotlib/patches.py`, `python/matplotlib/text.py`, `python/matplotlib/backend_bases.py`, `_svg_backend.py`, `_pil_backend.py`

**New renderer primitive:** `draw_arrow(x1, y1, x2, y2, arrowstyle, color, linewidth)` added to `RendererBase`, `RendererSVG`, `RendererPIL`.
- SVG: `<path>` with `marker-end` referencing a `<marker>` arrowhead definition
- PIL: draw line + filled polygon for arrowhead

**`FancyArrowPatch` (simplified):** Add to `patches.py`. Supports `arrowstyle` strings: `'->'`, `'<-'`, `'<->'`, `'-'`, `'fancy'`. Handles `shrinkA`/`shrinkB` (shorten arrow at endpoints). Geometry copied from real matplotlib's `patches.py`, stripping transform-dependent code in favor of direct pixel coordinates.

**`Annotation` update:** `text.py` `Annotation.draw()` constructs a `FancyArrowPatch` when `arrowprops` is set and delegates to `draw_arrow`.

**Upstream tests:** Port `test_annotate_default_arrow`, `test_annotate_arrowprops` from `lib/matplotlib/tests/test_text.py`.

## Phase 5 — Artist Properties

**Files:** `python/matplotlib/artist.py` (new base), `axes.py`, `lines.py`, `patches.py`, `text.py`, renderers

**New `artist.py`:** Base `Artist` class with `alpha`, `zorder`, `visible`, `clip_on`, `label`. All artist classes inherit from it. Currently properties are duplicated per-class; this consolidates them.

**Zorder:** `Figure.draw()` sorts artists by `zorder` before calling `draw()`. Default zorder: lines=2, patches=1, text=3 (matching real matplotlib defaults).

**Alpha:** Passed through to renderer color functions. SVG: `opacity` attribute. PIL: `RGBA` blend.

**Linestyle dashes:** Extend current `'solid'`/`'dashed'`/`'dotted'` to support `(offset, (on, off, ...))` tuple format and named styles `'dashdot'`, `'loosely dashed'`, etc. SVG: `stroke-dasharray`. PIL: manual segment iteration.

**Upstream tests:** Port `test_alpha`, `test_zorder`, `test_linestyle_variants` from `lib/matplotlib/tests/test_artist.py` and `test_lines.py`.

## Test Strategy

Each phase adds tests to a new `test_<phase>_upstream.py` file (e.g., `test_ticker_upstream.py`, `test_scale_upstream.py`). Tests are ported from real matplotlib with the original file path and function name noted in a comment. All 789 existing tests must continue passing throughout.

## Out of Scope

- `imshow` / colorbar / colormaps
- Date formatters/locators
- LaTeX/mathtext rendering
- Interactive/pick events
- `tight_layout` implementation
- `constrained_layout`
