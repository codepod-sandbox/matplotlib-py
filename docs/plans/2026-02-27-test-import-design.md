# Design: Import Matplotlib Tests & Feature Expansion

## Goal

Import the original matplotlib test suite (logic/assertion tests, no image comparison) and expand matplotlib-py's feature set to pass them. Target: ~200-300 passing tests covering all major API surface.

## Dependencies

- **numpy-rust** (sibling repo) — used as numpy dependency for array operations
- **pytest** — test runner

## Architecture

### Test Infrastructure

```
python/matplotlib/
├── testing/
│   ├── __init__.py          # setup(), test helpers
│   └── conftest.py          # pytest fixtures
├── tests/
│   ├── conftest.py          # imports testing.conftest fixtures
│   ├── test_colors.py       # Tier 1: color parsing/conversion
│   ├── test_pyplot.py       # Tier 2: pyplot state machine
│   ├── test_figure.py       # Tier 3: figure management
│   ├── test_axes.py         # Tier 4: plot types & axes API
│   ├── test_lines.py        # Tier 5: Line2D properties
│   └── test_subplots.py     # Tier 5: subplot layouts
```

**Key fixture:** `mpl_test_settings` (autouse) — closes all figures after each test, resets global state.

No image comparison infrastructure. Tests are pure assertion/logic tests adapted from upstream matplotlib.

### Implementation Tiers

#### Tier 0: Test Infrastructure
- `matplotlib.testing` package with `setup()` and fixtures
- `conftest.py` with autouse cleanup fixture
- pytest configuration (pyproject.toml or setup.cfg)

#### Tier 1: Colors (`test_colors.py`, ~30-40 tests)
Features needed:
- `to_rgba()`, `to_rgba_array()` — RGBA conversion (alpha support)
- `is_color_like()` — validate color specs
- `same_color()` — color equality comparison
- `Normalize`, `LogNorm` — value normalization classes
- `Colormap`, `ListedColormap` — colormap objects
- CSS4 full color names dictionary
- Hex shorthand (`#rgb` → `#rrggbb`)
- RGBA tuple support (4-tuple with alpha)

#### Tier 2: Pyplot (`test_pyplot.py`, ~20 tests)
Features needed:
- `sca()` — set current axes
- `subplot()` — single subplot creation/reuse
- `axes()` — explicit axes placement
- `cla()`, `clf()` — clear axes/figure
- `ion()`, `ioff()`, `isinteractive()` — interactive mode flags
- `rc()`, `rcParams` — configuration system (dict-like)

#### Tier 3: Figure (`test_figure.py`, ~30-40 tests)
Features needed:
- `suptitle()` — figure-level title
- `set_size_inches()` / `get_size_inches()` — figure sizing
- `tight_layout()` — layout adjustment (can be no-op initially)
- `get_axes()` — axes list access
- `delaxes()` — remove axes
- `add_axes()` — add axes by position rect
- `fignum_exists()` — figure number tracking

#### Tier 4: Axes (`test_axes.py`, ~150-200 tests)
New plot types:
- `errorbar()` — error bar plots
- `fill_between()`, `fill_betweenx()` — filled regions
- `pie()` — pie charts
- `stem()` — stem plots
- `step()` — step plots
- `axhline()`, `axvline()`, `axhspan()`, `axvspan()` — reference lines/spans
- `imshow()` — image display (basic)

Axes configuration:
- `set_xscale()` / `set_yscale()` — log/linear/symlog
- `set_aspect()` — aspect ratio
- `invert_xaxis()` / `invert_yaxis()` — axis inversion
- `twinx()` / `twiny()` — twin axes
- `set_xticks()` / `set_yticks()` — explicit tick positions
- `set_xticklabels()` / `set_yticklabels()` — tick labels
- `tick_params()` — tick styling
- `get_xlim()` / `get_ylim()` — limit getters
- `cla()` — clear axes

Text/annotations:
- `text()` — arbitrary text placement
- `annotate()` — annotations with arrows

Return types (proper objects instead of dicts):
- `Line2D` — returned by `plot()`
- `PathCollection` — returned by `scatter()`
- `BarContainer` — returned by `bar()`

#### Tier 5: Lines & Subplots (~30 tests)
- `matplotlib.lines.Line2D` — full property access (color, linewidth, linestyle, marker, data, etc.)
- `matplotlib.collections.PathCollection` — scatter collection
- Shared axes (`sharex`, `sharey`)
- `GridSpec` basics
- `label_outer()` — hide inner subplot labels

### Adaptation Strategy for Tests

1. **Copy** original test functions from matplotlib GitHub
2. **Strip** `@image_comparison` and `@check_figures_equal` decorators — skip those tests
3. **Keep** pure assertion tests as-is where possible
4. **Skip** tests requiring heavy internals we won't implement (transforms, backend_bases, etc.)
5. **Mark `pytest.mark.skip`** for tests needing features not yet built — these become the roadmap

### Object Model Evolution

Current: plot()/scatter()/bar() return plain dicts.
Target: Return proper objects (Line2D, PathCollection, BarContainer) that store properties and expose getters/setters.

This is the biggest architectural change — moving from dict-based elements to proper Artist objects. The rendering backends will need to dispatch on these objects instead of dict `type` fields.

### rcParams System

Implement as a dict subclass:
- Default values for all known keys
- Validation on set
- `rc_context()` context manager for temporary overrides
- `rc()` function for setting groups

### Scope Exclusions

- Image comparison testing infrastructure
- 3D plotting (mplot3d)
- Animation
- Interactive backends/widgets
- PDF/PS backends
- Advanced text rendering (TeX, mathtext)
- Polar/geographic projections
- Complex transforms pipeline
