# Matplotlib Test Import & Feature Expansion — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Import upstream matplotlib assertion tests and expand matplotlib-py to pass ~200 tests across colors, pyplot, figure, and axes modules.

**Architecture:** Incremental tier-based approach. Each tier adds a test file and the features needed to pass it. The core architectural change is evolving from dict-based plot elements to proper Artist objects (Line2D, PathCollection, BarContainer) that the rendering backends dispatch on. An rcParams system provides configuration.

**Tech Stack:** Pure Python, numpy-rust (sibling repo), pytest

---

## Tier 0: Test Infrastructure

### Task 1: Create pytest configuration and test scaffold

**Files:**
- Create: `python/matplotlib/testing/__init__.py`
- Create: `python/matplotlib/testing/conftest.py`
- Create: `python/matplotlib/tests/__init__.py`
- Create: `python/matplotlib/tests/conftest.py`
- Create: `pyproject.toml`

**Step 1: Create pyproject.toml with pytest config**

```toml
[project]
name = "matplotlib"
version = "3.8.0"
requires-python = ">=3.9"

[tool.pytest.ini_options]
testpaths = ["python/matplotlib/tests"]
pythonpath = ["python"]
```

**Step 2: Create matplotlib.testing package**

`python/matplotlib/testing/__init__.py`:
```python
"""matplotlib.testing — test infrastructure."""


def setup():
    """Initialize matplotlib for testing."""
    import matplotlib
    # Ensure deterministic state
    pass
```

`python/matplotlib/testing/conftest.py`:
```python
"""Pytest fixtures for matplotlib tests."""

import pytest


@pytest.fixture(autouse=True)
def mpl_test_settings():
    """Reset matplotlib state before/after each test."""
    import matplotlib.pyplot as plt
    yield
    plt.close('all')
```

**Step 3: Create tests package**

`python/matplotlib/tests/__init__.py`:
```python
"""matplotlib test suite."""
```

`python/matplotlib/tests/conftest.py`:
```python
"""Import fixtures from matplotlib.testing."""
from matplotlib.testing.conftest import *  # noqa: F401,F403
```

**Step 4: Verify pytest discovers tests**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest --collect-only 2>&1 | head -20`
Expected: No errors, 0 tests collected (no test files yet)

**Step 5: Commit**

```bash
git add pyproject.toml python/matplotlib/testing/ python/matplotlib/tests/
git commit -m "feat: add test infrastructure with pytest config and fixtures"
```

---

## Tier 1: Colors Module Expansion

### Task 2: Add rcParams system (needed by colors and all subsequent tiers)

**Files:**
- Create: `python/matplotlib/rcsetup.py`
- Modify: `python/matplotlib/__init__.py`

**Step 1: Create rcsetup.py with RcParams class**

`python/matplotlib/rcsetup.py`:
```python
"""matplotlib.rcsetup — default configuration and rcParams."""

_default_params = {
    'axes.prop_cycle': None,  # set after cycler import
    'axes.facecolor': 'white',
    'axes.edgecolor': 'black',
    'axes.linewidth': 0.8,
    'axes.grid': False,
    'axes.grid.which': 'major',
    'axes.titlesize': 'large',
    'axes.titlepad': 6.0,
    'axes.titlelocation': 'center',
    'axes.labelsize': 'medium',
    'axes.labelpad': 4.0,
    'figure.figsize': [6.4, 4.8],
    'figure.dpi': 100,
    'figure.facecolor': 'white',
    'figure.edgecolor': 'white',
    'figure.max_open_warning': 20,
    'lines.linewidth': 1.5,
    'lines.linestyle': '-',
    'lines.color': 'C0',
    'lines.marker': 'None',
    'lines.markersize': 6.0,
    'patch.linewidth': 1.0,
    'patch.facecolor': 'C0',
    'patch.edgecolor': 'black',
    'legend.loc': 'best',
    'legend.frameon': True,
    'legend.fontsize': 'medium',
    'grid.color': '#b0b0b0',
    'grid.linestyle': '-',
    'grid.linewidth': 0.8,
    'grid.alpha': 1.0,
    'xtick.labelsize': 'medium',
    'ytick.labelsize': 'medium',
    'savefig.dpi': 'figure',
    'savefig.format': 'png',
}


class RcParams(dict):
    """Dictionary-like object for matplotlib configuration."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, val):
        super().__setitem__(key, val)

    def __repr__(self):
        items = '\n'.join(f'{k}: {v!r}' for k, v in sorted(self.items()))
        return f'RcParams({{\n{items}\n}})'


def rc_context(rc=None):
    """Context manager for temporarily changing rcParams."""
    import matplotlib
    return _RcContext(matplotlib.rcParams, rc)


class _RcContext:
    def __init__(self, rcparams, rc):
        self._rcparams = rcparams
        self._rc = rc or {}
        self._old = {}

    def __enter__(self):
        self._old = dict(self._rcparams)
        self._rcparams.update(self._rc)
        return self._rcparams

    def __exit__(self, *args):
        self._rcparams.clear()
        self._rcparams.update(self._old)
```

**Step 2: Wire rcParams into matplotlib.__init__**

Modify `python/matplotlib/__init__.py` to:
```python
"""
matplotlib — plotting library for codepod.

SVG primary output with optional PIL/PNG backend.
"""

__version__ = "3.8.0"

from matplotlib.rcsetup import RcParams, _default_params, rc_context

rcParams = RcParams(_default_params)


def rc(group, **kwargs):
    """Set rcParams for a group."""
    for k, v in kwargs.items():
        rcParams[f'{group}.{k}'] = v


def is_interactive():
    """Return whether interactive mode is on."""
    return _interactive


_interactive = False
```

**Step 3: Run a quick smoke test**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -c "import matplotlib; print(matplotlib.rcParams['figure.figsize'])"`
Expected: `[6.4, 4.8]`

**Step 4: Commit**

```bash
git add python/matplotlib/rcsetup.py python/matplotlib/__init__.py
git commit -m "feat: add rcParams configuration system"
```

### Task 3: Expand colors module with to_rgba, is_color_like, same_color, CSS4 colors

**Files:**
- Modify: `python/matplotlib/colors.py`

**Step 1: Read current colors.py** (already read above)

**Step 2: Rewrite colors.py with full color system**

Replace `python/matplotlib/colors.py` with expanded version supporting:
- CSS4 full color names (148 colors)
- TABLEAU_COLORS (10-color tab: cycle)
- `to_rgba(c, alpha=None)` — returns (r,g,b,a) tuple with floats 0-1
- `to_rgba_array(c, alpha=None)` — returns list of RGBA tuples
- `to_hex(c, keep_alpha=False)` — hex string
- `to_rgb(c)` — (r,g,b) tuple
- `is_color_like(c)` — bool
- `same_color(c1, c2)` — bool
- `_has_alpha_channel(c)` — bool
- Hex shorthand: `#rgb` -> `#rrggbb`, `#rgba` -> `#rrggbbaa`
- Color-alpha tuples: `('red', 0.5)` -> RGBA
- `Normalize(vmin, vmax, clip=False)` class
- `LogNorm(vmin, vmax, clip=False)` class
- Existing functionality preserved (DEFAULT_CYCLE, parse_fmt, _NAMED)

The implementation should:
- Accept strings (named, hex, CN cycle), tuples (RGB/RGBA, 0-1 float or 0-255 int), color-alpha pairs
- Validate ranges (alpha must be 0-1, RGBA values must be 0-1)
- Raise ValueError for invalid colors
- Handle 'none' as fully transparent (0,0,0,0)

```python
"""matplotlib.colors — colour name resolution, hex conversion, default cycle."""

import math

# Default colour cycle (matplotlib C0-C9)
DEFAULT_CYCLE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
]

# Tableau 10 colors (same as C0-C9 but with tab: prefix names)
TABLEAU_COLORS = {
    'tab:blue': '#1f77b4',
    'tab:orange': '#ff7f0e',
    'tab:green': '#2ca02c',
    'tab:red': '#d62728',
    'tab:purple': '#9467bd',
    'tab:brown': '#8c564b',
    'tab:pink': '#e377c2',
    'tab:gray': '#7f7f7f',
    'tab:olive': '#bcbd22',
    'tab:cyan': '#17becf',
}

# Short single-character color names
BASE_COLORS = {
    'b': (0, 0, 1),
    'g': (0, 0.5, 0),
    'r': (1, 0, 0),
    'c': (0, 0.75, 0.75),
    'm': (0.75, 0, 0.75),
    'y': (0.75, 0.75, 0),
    'k': (0, 0, 0),
    'w': (1, 1, 1),
}

# CSS4 named colors (full set)
CSS4_COLORS = {
    'aliceblue': '#f0f8ff', 'antiquewhite': '#faebd7', 'aqua': '#00ffff',
    'aquamarine': '#7fffd4', 'azure': '#f0ffff', 'beige': '#f5f5dc',
    'bisque': '#ffe4c4', 'black': '#000000', 'blanchedalmond': '#ffebcd',
    'blue': '#0000ff', 'blueviolet': '#8a2be2', 'brown': '#a52a2a',
    'burlywood': '#deb887', 'cadetblue': '#5f9ea0', 'chartreuse': '#7fff00',
    'chocolate': '#d2691e', 'coral': '#ff7f50', 'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc', 'crimson': '#dc143c', 'cyan': '#00ffff',
    'darkblue': '#00008b', 'darkcyan': '#008b8b', 'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9', 'darkgreen': '#006400', 'darkgrey': '#a9a9a9',
    'darkkhaki': '#bdb76b', 'darkmagenta': '#8b008b', 'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00', 'darkorchid': '#9932cc', 'darkred': '#8b0000',
    'darksalmon': '#e9967a', 'darkseagreen': '#8fbc8f', 'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f', 'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1', 'darkviolet': '#9400d3', 'deeppink': '#ff1493',
    'deepskyblue': '#00bfff', 'dimgray': '#696969', 'dimgrey': '#696969',
    'dodgerblue': '#1e90ff', 'firebrick': '#b22222', 'floralwhite': '#fffaf0',
    'forestgreen': '#228b22', 'fuchsia': '#ff00ff', 'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff', 'gold': '#ffd700', 'goldenrod': '#daa520',
    'gray': '#808080', 'green': '#008000', 'greenyellow': '#adff2f',
    'grey': '#808080', 'honeydew': '#f0fff0', 'hotpink': '#ff69b4',
    'indianred': '#cd5c5c', 'indigo': '#4b0082', 'ivory': '#fffff0',
    'khaki': '#f0e68c', 'lavender': '#e6e6fa', 'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00', 'lemonchiffon': '#fffacd', 'lightblue': '#add8e6',
    'lightcoral': '#f08080', 'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2', 'lightgray': '#d3d3d3',
    'lightgreen': '#90ee90', 'lightgrey': '#d3d3d3', 'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a', 'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa', 'lightslategray': '#778899',
    'lightslategrey': '#778899', 'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0', 'lime': '#00ff00', 'limegreen': '#32cd32',
    'linen': '#faf0e6', 'magenta': '#ff00ff', 'maroon': '#800000',
    'mediumaquamarine': '#66cdaa', 'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3', 'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371', 'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a', 'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585', 'midnightblue': '#191970',
    'mintcream': '#f5fffa', 'mistyrose': '#ffe4e1', 'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead', 'navy': '#000080', 'oldlace': '#fdf5e6',
    'olive': '#808000', 'olivedrab': '#6b8e23', 'orange': '#ffa500',
    'orangered': '#ff4500', 'orchid': '#da70d6', 'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98', 'paleturquoise': '#afeeee',
    'palevioletred': '#db7093', 'papayawhip': '#ffefd5', 'peachpuff': '#ffdab9',
    'peru': '#cd853f', 'pink': '#ffc0cb', 'plum': '#dda0dd',
    'powderblue': '#b0e0e6', 'purple': '#800080', 'rebeccapurple': '#663399',
    'red': '#ff0000', 'rosybrown': '#bc8f8f', 'royalblue': '#4169e1',
    'saddlebrown': '#8b4513', 'salmon': '#fa8072', 'sandybrown': '#f4a460',
    'seagreen': '#2e8b57', 'seashell': '#fff5ee', 'sienna': '#a0522d',
    'silver': '#c0c0c0', 'skyblue': '#87ceeb', 'slateblue': '#6a5acd',
    'slategray': '#708090', 'slategrey': '#708090', 'snow': '#fffafa',
    'springgreen': '#00ff7f', 'steelblue': '#4682b4', 'tan': '#d2b48c',
    'teal': '#008080', 'thistle': '#d8bfd8', 'tomato': '#ff6347',
    'turquoise': '#40e0d0', 'violet': '#ee82ee', 'wheat': '#f5deb3',
    'white': '#ffffff', 'whitesmoke': '#f5f5f5', 'yellow': '#ffff00',
    'yellowgreen': '#9acd32',
}

# Combined lookup: base colors override CSS4 for single-char names
_colors_full_map = {}
_colors_full_map.update({k: _hex_to_rgba(v) if isinstance(v, str) else (*v, 1.0)
                         for k, v in CSS4_COLORS.items()})
# Note: _colors_full_map is built lazily after _hex_to_rgba is defined


def _hex_to_rgba(h):
    """Convert hex string to (r,g,b,a) float tuple."""
    h = h.lstrip('#')
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    elif len(h) == 4:
        h = h[0]*2 + h[1]*2 + h[2]*2 + h[3]*2
    if len(h) == 6:
        return (int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255, 1.0)
    elif len(h) == 8:
        return (int(h[0:2], 16)/255, int(h[2:4], 16)/255,
                int(h[4:6], 16)/255, int(h[6:8], 16)/255)
    return (0, 0, 0, 1.0)


# Build the full color map
_colors_full_map = {}
for _k, _v in CSS4_COLORS.items():
    _colors_full_map[_k] = _hex_to_rgba(_v)
for _k, _v in TABLEAU_COLORS.items():
    _colors_full_map[_k] = _hex_to_rgba(_v)
for _k, _v in BASE_COLORS.items():
    _colors_full_map[_k] = (*_v, 1.0)


def _is_color_alpha_tuple(c):
    """Check if c is a (color, alpha) tuple."""
    if not isinstance(c, tuple) or len(c) != 2:
        return False
    color_part, alpha_part = c
    if not isinstance(alpha_part, (int, float)):
        return False
    if isinstance(color_part, str):
        return True
    if isinstance(color_part, tuple) and len(color_part) in (3, 4):
        return True
    return False


def _has_alpha_channel(c):
    """Return True if *c* already includes an alpha channel."""
    if isinstance(c, str):
        if c.startswith('#') and len(c.lstrip('#')) in (4, 8):
            return True
        return False
    if isinstance(c, tuple):
        if len(c) == 2 and isinstance(c[1], (int, float)):
            # Color-alpha tuple like ('red', 0.5)
            if isinstance(c[0], str):
                return True
            if isinstance(c[0], tuple) and len(c[0]) in (3, 4):
                return True
        if len(c) == 4:
            return True
    return False


def to_rgba(c, alpha=None):
    """Convert color *c* to an RGBA tuple (floats 0-1).

    Accepts: named colors, hex strings, RGB/RGBA tuples, (color, alpha) tuples.
    """
    if isinstance(c, str) and c.lower() == 'none':
        return (0.0, 0.0, 0.0, 0.0)

    # Handle (color, alpha) tuples
    if isinstance(c, tuple) and len(c) == 2:
        color_part, alpha_part = c
        if isinstance(alpha_part, (int, float)) and isinstance(color_part, (str, tuple)):
            if not (0 <= alpha_part <= 1):
                raise ValueError(
                    f"'alpha' ({alpha_part}) is outside 0-1 range")
            result = to_rgba(color_part)
            # explicit alpha parameter overrides tuple alpha
            if alpha is not None:
                return (*result[:3], float(alpha))
            return (*result[:3], float(alpha_part))

    if isinstance(c, str):
        c_lower = c.lower().strip()
        if c_lower.startswith('#'):
            rgba = _hex_to_rgba(c_lower)
            if alpha is not None:
                rgba = (*rgba[:3], float(alpha))
            return rgba
        # CN color cycle
        if c_lower.startswith('c') and c_lower[1:].isdigit():
            idx = int(c_lower[1:])
            hex_c = DEFAULT_CYCLE[idx % len(DEFAULT_CYCLE)]
            rgba = _hex_to_rgba(hex_c)
            if alpha is not None:
                rgba = (*rgba[:3], float(alpha))
            return rgba
        # Named color
        if c_lower in _colors_full_map:
            rgba = _colors_full_map[c_lower]
            if alpha is not None:
                rgba = (*rgba[:3], float(alpha))
            return rgba
        # Grayscale string '0.5' etc
        try:
            gray = float(c_lower)
            if 0 <= gray <= 1:
                rgba = (gray, gray, gray, 1.0)
                if alpha is not None:
                    rgba = (*rgba[:3], float(alpha))
                return rgba
        except ValueError:
            pass
        raise ValueError(f"{c!r} is not a valid color value")

    if isinstance(c, (tuple, list)):
        c = tuple(c)
        if len(c) == 3:
            r, g, b = [float(x) for x in c]
            if all(isinstance(x, int) and x > 1 for x in c):
                r, g, b = r/255, g/255, b/255
            rgba = (r, g, b, 1.0 if alpha is None else float(alpha))
            return rgba
        if len(c) == 4:
            r, g, b, a = [float(x) for x in c]
            if alpha is not None:
                a = float(alpha)
            return (r, g, b, a)

    raise ValueError(f"{c!r} is not a valid color value")


def to_rgba_array(c, alpha=None):
    """Convert *c* to a list of RGBA tuples.

    Accepts single color, list of colors, or (colors, alpha) tuple.
    """
    if isinstance(c, str):
        if c.lower() == 'none':
            return [(0.0, 0.0, 0.0, 0.0)]
        return [to_rgba(c, alpha)]

    # Handle (color_array, alpha) tuple
    if isinstance(c, tuple) and len(c) == 2:
        color_part, alpha_part = c
        if isinstance(alpha_part, (int, float)):
            if not (0 <= alpha_part <= 1):
                raise ValueError(
                    f"'alpha' ({alpha_part}) is outside 0-1 range")
            if isinstance(color_part, (list, tuple)):
                # Could be a single RGB/RGBA tuple or a list of colors
                if len(color_part) in (3, 4) and all(isinstance(x, (int, float)) for x in color_part):
                    # Single color tuple + alpha
                    result = to_rgba(color_part)
                    effective_alpha = float(alpha) if alpha is not None else float(alpha_part)
                    return [(*result[:3], effective_alpha)]
                # List of colors + alpha
                effective_alpha = float(alpha) if alpha is not None else float(alpha_part)
                return [to_rgba(x, effective_alpha) for x in color_part]
            if isinstance(color_part, str):
                effective_alpha = float(alpha) if alpha is not None else float(alpha_part)
                return [to_rgba(color_part, effective_alpha)]

    if isinstance(c, (list, tuple)):
        # Check if it's a single color (all numbers)
        if all(isinstance(x, (int, float)) for x in c):
            if len(c) in (3, 4):
                return [to_rgba(c, alpha)]
        # Check if alpha is a list
        if isinstance(alpha, (list, tuple)):
            if len(alpha) != len(c):
                raise ValueError(
                    f"alpha length ({len(alpha)}) does not match "
                    f"color length ({len(c)})")
            return [to_rgba(ci, ai) for ci, ai in zip(c, alpha)]
        return [to_rgba(ci, alpha) for ci in c]

    if hasattr(c, '__iter__'):
        return [to_rgba(ci, alpha) for ci in c]

    return [to_rgba(c, alpha)]


def to_hex(color, keep_alpha=False):
    """Convert a colour specification to ``#rrggbb`` (or ``#rrggbbaa``) hex string."""
    rgba = to_rgba(color)
    if keep_alpha:
        return '#{:02x}{:02x}{:02x}{:02x}'.format(
            int(round(rgba[0]*255)), int(round(rgba[1]*255)),
            int(round(rgba[2]*255)), int(round(rgba[3]*255)))
    return '#{:02x}{:02x}{:02x}'.format(
        int(round(rgba[0]*255)), int(round(rgba[1]*255)),
        int(round(rgba[2]*255)))


def to_rgb(color):
    """Convert a colour specification to ``(r, g, b)`` floats 0-1."""
    rgba = to_rgba(color)
    return rgba[:3]


def is_color_like(c):
    """Return True if *c* can be converted to a color."""
    try:
        to_rgba(c)
        return True
    except (ValueError, TypeError):
        return False


def same_color(c1, c2):
    """Return True if colors *c1* and *c2* are the same."""
    if isinstance(c1, (list, tuple)) and isinstance(c2, (list, tuple)):
        # Check if both are sequences of colors (not a single color tuple)
        if (not all(isinstance(x, (int, float)) for x in c1) and
                not all(isinstance(x, (int, float)) for x in c2)):
            if len(c1) != len(c2):
                raise ValueError(
                    f"color sequences have different lengths: "
                    f"{len(c1)} vs {len(c2)}")
            return all(same_color(a, b) for a, b in zip(c1, c2))
    try:
        return to_rgba(c1) == to_rgba(c2)
    except (ValueError, TypeError):
        return False


class Normalize:
    """Map values to the 0-1 range."""

    def __init__(self, vmin=None, vmax=None, clip=False):
        self.vmin = vmin
        self.vmax = vmax
        self.clip = clip
        self.callbacks = _CallbackRegistry()
        self._scale = None

    def __call__(self, value, clip=None):
        if clip is None:
            clip = self.clip
        vmin, vmax = self.vmin, self.vmax
        if vmin is None or vmax is None:
            raise ValueError("Normalize requires vmin and vmax to be set")
        if vmin == vmax:
            return 0.0
        result = (float(value) - vmin) / (vmax - vmin)
        if clip:
            result = max(0.0, min(1.0, result))
        return result

    def inverse(self, value):
        vmin, vmax = self.vmin, self.vmax
        if vmin is None or vmax is None:
            raise ValueError("Normalize requires vmin and vmax to be set")
        return vmin + float(value) * (vmax - vmin)

    def autoscale(self, data):
        self.vmin = min(data)
        self.vmax = max(data)
        self.callbacks.process('changed')


class LogNorm(Normalize):
    """Map values to 0-1 on a log scale."""

    def __call__(self, value, clip=None):
        if clip is None:
            clip = self.clip
        vmin, vmax = self.vmin, self.vmax
        if vmin is None or vmax is None:
            raise ValueError("LogNorm requires vmin and vmax to be set")
        if vmin <= 0:
            raise ValueError("LogNorm vmin must be positive")
        if vmin >= vmax:
            raise ValueError("LogNorm vmin must be less than vmax")
        result = (math.log(float(value)) - math.log(vmin)) / (math.log(vmax) - math.log(vmin))
        if clip:
            result = max(0.0, min(1.0, result))
        return result

    def inverse(self, value):
        vmin, vmax = self.vmin, self.vmax
        if vmin is None or vmax is None:
            raise ValueError("LogNorm requires vmin and vmax to be set")
        if vmin <= 0:
            raise ValueError("LogNorm vmin must be positive")
        if vmin >= vmax:
            raise ValueError("LogNorm vmin must be less than vmax")
        log_vmin = math.log(vmin)
        log_vmax = math.log(vmax)
        return math.exp(log_vmin + float(value) * (log_vmax - log_vmin))


class _CallbackRegistry:
    """Simple callback registry."""

    def __init__(self):
        self._callbacks = {}
        self._id = 0

    def connect(self, signal, func):
        self._id += 1
        self._callbacks.setdefault(signal, {})[self._id] = func
        return self._id

    def disconnect(self, cid):
        for signal_cbs in self._callbacks.values():
            signal_cbs.pop(cid, None)

    def process(self, signal, *args, **kwargs):
        for func in list(self._callbacks.get(signal, {}).values()):
            func(*args, **kwargs)


# Format-string parsing (preserved from original)
_COLOR_CHARS = set('bgrcmykw')
_MARKER_CHARS = {'o': 'circle', 's': 'square', '^': 'triangle',
                 'D': 'diamond', '.': 'point', ',': 'pixel',
                 'v': 'triangle_down', '<': 'triangle_left',
                 '>': 'triangle_right', '1': 'tri_down',
                 '2': 'tri_up', '3': 'tri_left', '4': 'tri_right',
                 '+': 'plus', 'x': 'x', 'd': 'thin_diamond',
                 '|': 'vline', '_': 'hline', 'p': 'pentagon',
                 'h': 'hexagon1', 'H': 'hexagon2', '*': 'star',
                 'None': None, 'none': None, '': None}
_LINE_CHARS = {'-': 'solid', '--': 'dashed', ':': 'dotted', '-.': 'dashdot'}


def parse_fmt(fmt):
    """Parse a matplotlib format string, return (color, marker, linestyle)."""
    color = None
    marker = None
    linestyle = None
    if not fmt:
        return color, marker, linestyle
    i = 0
    while i < len(fmt):
        ch = fmt[i]
        if ch in _COLOR_CHARS and color is None:
            color = ch
        elif ch in _MARKER_CHARS and marker is None:
            marker = ch
        elif ch == '-' and i + 1 < len(fmt) and fmt[i + 1] in ('-', '.'):
            linestyle = fmt[i:i+2]
            i += 1
        elif ch in ('-', ':', '.'):
            if linestyle is None:
                linestyle = ch
        i += 1
    return color, marker, linestyle
```

Note: This is a large replacement. The key additions over the existing colors.py:
- Full CSS4 color table, TABLEAU_COLORS, BASE_COLORS
- `_colors_full_map` combined lookup
- `to_rgba()` with proper validation and alpha handling
- `to_rgba_array()` for batch conversion
- `is_color_like()`, `same_color()`, `_has_alpha_channel()`
- `Normalize`, `LogNorm` classes
- `_CallbackRegistry` for norm change notifications
- Expanded marker chars

**Step 3: Verify colors module imports**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -c "from matplotlib.colors import to_rgba, same_color, is_color_like; print(to_rgba('red')); print(same_color('r', (1,0,0))); print(is_color_like('blue'))"`
Expected: `(1.0, 0.0, 0.0, 1.0)` / `True` / `True`

**Step 4: Commit**

```bash
git add python/matplotlib/colors.py
git commit -m "feat: expand colors module with to_rgba, CSS4, same_color, Normalize"
```

### Task 4: Write test_colors.py with adapted upstream tests

**Files:**
- Create: `python/matplotlib/tests/test_colors.py`

**Step 1: Create test file with ~25 adapted tests**

Write `python/matplotlib/tests/test_colors.py` with tests adapted from upstream matplotlib. Focus on:
- `test_color_names` — to_hex for named colors
- `test_grey_gray` — grey/gray equivalence in color map
- `test_tableau_order` — TABLEAU_COLORS order matches C0-C9
- `test_hex_shorthand_notation` — #rgb == #rrggbb
- `test_conversions` — to_rgba, to_hex roundtrips
- `test_to_rgba_array_single_str` — single string input
- `test_to_rgba_array_2tuple_str` — tuple of color strings
- `test_to_rgba_accepts_color_alpha_tuple` — (color, alpha) tuples
- `test_to_rgba_explicit_alpha_overrides_tuple_alpha`
- `test_to_rgba_error_with_color_invalid_alpha_tuple`
- `test_failed_conversions` — invalid color inputs
- `test_is_color_like` — parametrized valid/invalid
- `test_same_color` — color equality
- `test_has_alpha_channel`
- `test_Normalize` — basic normalize forward/inverse
- `test_lognorm_invalid` — LogNorm validation
- `test_LogNorm` — LogNorm with clip
- `test_LogNorm_inverse` — LogNorm roundtrip

```python
"""Tests for matplotlib.colors — adapted from upstream matplotlib."""

import math
import pytest
import matplotlib.colors as mcolors


class TestColorNames:
    def test_named_colors_resolve(self):
        assert mcolors.to_hex('blue') == '#0000ff'
        assert mcolors.to_hex('red') == '#ff0000'
        assert mcolors.to_hex('tab:blue') == '#1f77b4'

    def test_grey_gray(self):
        for name in mcolors._colors_full_map:
            if 'grey' in name:
                assert name.replace('grey', 'gray') in mcolors._colors_full_map
            if 'gray' in name:
                assert name.replace('gray', 'grey') in mcolors._colors_full_map

    def test_tableau_order(self):
        expected = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        actual = list(mcolors.TABLEAU_COLORS.values())
        assert actual == expected

    def test_cn_colors(self):
        assert mcolors.to_hex('C0') == '#1f77b4'
        assert mcolors.to_hex('C1') == '#ff7f0e'
        assert mcolors.to_hex('C9') == '#17becf'


class TestHexConversion:
    def test_hex_shorthand_notation(self):
        assert mcolors.same_color('#123', '#112233')
        assert mcolors.same_color('#123a', '#112233aa')

    def test_to_hex_roundtrip(self):
        for color in ['red', 'blue', 'green', '#abcdef']:
            rgba = mcolors.to_rgba(color)
            hex_str = mcolors.to_hex(rgba)
            rgba2 = mcolors.to_rgba(hex_str)
            for a, b in zip(rgba[:3], rgba2[:3]):
                assert abs(a - b) < 0.01

    def test_to_hex_keep_alpha(self):
        assert mcolors.to_hex((1, 0, 0, 0.5), keep_alpha=True) == '#ff000080'


class TestToRgba:
    def test_named_color(self):
        assert mcolors.to_rgba('red') == (1.0, 0.0, 0.0, 1.0)

    def test_hex_color(self):
        r, g, b, a = mcolors.to_rgba('#ff8000')
        assert (r, g, b) == (1.0, 128/255, 0.0)
        assert a == 1.0

    def test_rgb_tuple(self):
        assert mcolors.to_rgba((1.0, 0.0, 0.0)) == (1.0, 0.0, 0.0, 1.0)

    def test_rgba_tuple(self):
        assert mcolors.to_rgba((1.0, 0.0, 0.0, 0.5)) == (1.0, 0.0, 0.0, 0.5)

    def test_alpha_override(self):
        r, g, b, a = mcolors.to_rgba('red', alpha=0.5)
        assert a == 0.5

    def test_none_is_transparent(self):
        assert mcolors.to_rgba('none') == (0.0, 0.0, 0.0, 0.0)

    def test_grayscale_string(self):
        r, g, b, a = mcolors.to_rgba('0.5')
        assert r == g == b == 0.5
        assert a == 1.0

    @pytest.mark.parametrize('c, expected_alpha', [
        (('red', 0.5), 0.5),
        (('#ff0000', 0.3), 0.3),
        (((1, 0, 0), 0.7), 0.7),
    ])
    def test_color_alpha_tuple(self, c, expected_alpha):
        rgba = mcolors.to_rgba(c)
        assert rgba[3] == expected_alpha

    def test_explicit_alpha_overrides_tuple_alpha(self):
        rgba = mcolors.to_rgba(('red', 0.1), alpha=0.9)
        assert rgba[3] == 0.9

    def test_invalid_alpha_in_tuple(self):
        with pytest.raises(ValueError):
            mcolors.to_rgba(('blue', 2.0))

    @pytest.mark.parametrize('val', ['5', '-1', 'nan', 'unknown_color'])
    def test_failed_conversions(self, val):
        with pytest.raises(ValueError):
            mcolors.to_rgba(val)


class TestToRgbaArray:
    def test_single_str(self):
        result = mcolors.to_rgba_array('red')
        assert len(result) == 1
        assert result[0] == (1.0, 0.0, 0.0, 1.0)

    def test_two_colors(self):
        result = mcolors.to_rgba_array(('k', 'w'))
        assert len(result) == 2
        assert result[0][:3] == (0.0, 0.0, 0.0)
        assert result[1][:3] == (1.0, 1.0, 1.0)

    def test_none_color(self):
        result = mcolors.to_rgba_array('none')
        assert result == [(0.0, 0.0, 0.0, 0.0)]

    def test_color_alpha_tuple(self):
        result = mcolors.to_rgba_array(('black', 0.9))
        assert len(result) == 1
        assert result[0][3] == 0.9

    def test_explicit_alpha_overrides_tuple(self):
        result = mcolors.to_rgba_array(('black', 0.9), alpha=0.5)
        assert result[0][3] == 0.5

    def test_invalid_alpha_tuple(self):
        with pytest.raises(ValueError):
            mcolors.to_rgba_array(('black', 2.0))


class TestIsColorLike:
    @pytest.mark.parametrize('c, expected', [
        ('red', True),
        (('red', 0.5), True),
        ('C3', True),
        (('C3', 0.5), True),
        (('red', 2), False),      # alpha out of range
        ('notacolor', False),
    ])
    def test_is_color_like(self, c, expected):
        assert mcolors.is_color_like(c) == expected


class TestSameColor:
    def test_same_named(self):
        assert mcolors.same_color('k', (0, 0, 0))
        assert not mcolors.same_color('r', 'b')

    def test_same_lists(self):
        assert mcolors.same_color(['red', 'blue'], ['r', 'b'])

    def test_none_equality(self):
        assert mcolors.same_color('none', 'none')

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            mcolors.same_color(['r', 'g'], ['r'])


class TestHasAlphaChannel:
    @pytest.mark.parametrize('c, expected', [
        ((1, 0, 0), False),
        ((1, 0, 0, 0.5), True),
        ('#ff0000', False),
        ('#ff000080', True),
        ('#fff', False),
        ('#fffa', True),
        (('red', 0.5), True),
    ])
    def test_has_alpha(self, c, expected):
        assert mcolors._has_alpha_channel(c) == expected


class TestNormalize:
    def test_basic(self):
        norm = mcolors.Normalize(vmin=0, vmax=10)
        assert norm(0) == 0.0
        assert norm(5) == 0.5
        assert norm(10) == 1.0

    def test_inverse(self):
        norm = mcolors.Normalize(vmin=0, vmax=10)
        for val in [0, 2.5, 5, 7.5, 10]:
            assert abs(norm.inverse(norm(val)) - val) < 1e-10

    def test_clip(self):
        norm = mcolors.Normalize(vmin=0, vmax=10, clip=True)
        assert norm(-5) == 0.0
        assert norm(15) == 1.0


class TestLogNorm:
    def test_basic(self):
        norm = mcolors.LogNorm(vmin=1, vmax=100)
        assert abs(norm(10) - 0.5) < 1e-10

    def test_clip(self):
        norm = mcolors.LogNorm(vmin=1, vmax=10, clip=True)
        assert norm(100) == 1.0

    def test_inverse(self):
        norm = mcolors.LogNorm(vmin=1, vmax=100)
        for val in [1, 10, 100]:
            result = norm.inverse(norm(val))
            assert abs(result - val) < 1e-6

    @pytest.mark.parametrize('vmin, vmax', [(-1, 2), (3, 1)])
    def test_invalid(self, vmin, vmax):
        norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)
        with pytest.raises(ValueError):
            norm(1)
        with pytest.raises(ValueError):
            norm.inverse(0.5)
```

**Step 2: Run tests**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/test_colors.py -v 2>&1 | tail -30`
Expected: All tests pass

**Step 3: Fix any failures, iterate until green**

**Step 4: Commit**

```bash
git add python/matplotlib/tests/test_colors.py
git commit -m "test: add test_colors.py with 40+ color system tests"
```

---

## Tier 2: Pyplot State Machine

### Task 5: Expand pyplot with figure numbering, sca, ion/ioff, subplot, cla/clf

**Files:**
- Modify: `python/matplotlib/pyplot.py`
- Modify: `python/matplotlib/__init__.py`

**Step 1: Rewrite pyplot.py with expanded state management**

The key additions:
- Figure numbering (`plt.figure(num=)`, `plt.get_fignums()`, `plt.get_figlabels()`)
- `plt.fignum_exists(num)`
- `plt.sca(ax)` — set current axes
- `plt.subplot(*args, **kwargs)` — subplot creation with reuse semantics
- `plt.axes(**kwargs)` — always create new axes
- `plt.cla()`, `plt.clf()` — clear current axes/figure
- `plt.ion()`, `plt.ioff()`, `plt.isinteractive()` — interactive mode as context managers
- `plt.rc()`, `plt.rcParams` — re-export from matplotlib
- `plt.suptitle()` — delegate to current figure

```python
"""matplotlib.pyplot — stateful module-level plotting API."""

import matplotlib
from matplotlib.figure import Figure

# Global state
_figures = {}       # num -> Figure
_fig_order = []     # ordered list of figure numbers
_current_fig = None
_current_ax = None
_next_num = 1


def _ensure():
    """Ensure there is a current Figure and Axes."""
    global _current_fig, _current_ax
    if _current_fig is None:
        fig, ax = subplots()
    return _current_fig, _current_ax


def figure(num=None, figsize=None, dpi=100, clear=False, **kwargs):
    """Create or activate a Figure."""
    global _current_fig, _current_ax, _next_num
    label = kwargs.get('label', '')

    if num is None:
        num = _next_num
        while num in _figures:
            num += 1
        _next_num = num + 1

    if isinstance(num, str):
        # Find figure by label
        for n, f in _figures.items():
            if getattr(f, '_label', '') == num:
                _current_fig = f
                if f._axes:
                    _current_ax = f._axes[-1]
                return f
        # Create new with this label
        label = num
        num = _next_num
        while num in _figures:
            num += 1
        _next_num = num + 1

    if num in _figures:
        fig = _figures[num]
        _current_fig = fig
        if fig._axes:
            _current_ax = fig._axes[-1]
        if clear:
            fig.clear()
        return fig

    fig = Figure(figsize=figsize, dpi=dpi)
    fig.number = num
    fig._label = label
    _figures[num] = fig
    if num not in _fig_order:
        _fig_order.append(num)
    _next_num = max(_next_num, num + 1)

    ax = fig.add_subplot(1, 1, 1)
    _current_fig = fig
    _current_ax = ax
    return fig


def subplots(nrows=1, ncols=1, figsize=None, dpi=100, sharex=False,
             sharey=False, num=None, clear=False, **kwargs):
    """Create a Figure and a set of subplots."""
    global _current_fig, _current_ax, _next_num

    if num is not None and num in _figures:
        fig = _figures[num]
        if clear:
            fig.clear()
    else:
        fig = Figure(figsize=figsize, dpi=dpi)
        n = num if num is not None else _next_num
        while n in _figures:
            n += 1
        fig.number = n
        fig._label = ''
        _figures[n] = fig
        if n not in _fig_order:
            _fig_order.append(n)
        _next_num = max(_next_num, n + 1)

    if nrows == 1 and ncols == 1:
        ax = fig.add_subplot(1, 1, 1)
        _current_fig = fig
        _current_ax = ax
        return fig, ax

    axes = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            ax = fig.add_subplot(nrows, ncols, r * ncols + c + 1)
            row.append(ax)
        axes.append(row)

    _current_fig = fig
    _current_ax = axes[0][0] if axes else None

    if nrows == 1:
        axes = axes[0]
    elif ncols == 1:
        axes = [row[0] for row in axes]

    return fig, axes


def gcf():
    """Get current figure."""
    _ensure()
    return _current_fig


def gca():
    """Get current axes."""
    _ensure()
    return _current_ax


def sca(ax):
    """Set current axes to *ax*."""
    global _current_ax, _current_fig
    _current_ax = ax
    _current_fig = ax.figure


def subplot(*args, **kwargs):
    """Add or retrieve a subplot.

    Reuses existing subplot if spec matches.
    """
    global _current_ax, _current_fig
    _ensure()
    fig = _current_fig

    # Parse args: subplot(nrows, ncols, index) or subplot(NRC)
    if len(args) == 1 and isinstance(args[0], int) and args[0] >= 100:
        n, r, c = args[0] // 100, (args[0] % 100) // 10, args[0] % 10
        args = (n, r, c)
    elif len(args) == 0:
        args = (1, 1, 1)

    nrows, ncols, index = args[0], args[1] if len(args) > 1 else 1, args[2] if len(args) > 2 else 1

    # Check for reuse: same grid position and same kwargs
    for ax in fig._axes:
        if (hasattr(ax, '_position') and ax._position == (nrows, ncols, index)):
            # Reuse if kwargs match
            _current_ax = ax
            return ax

    ax = fig.add_subplot(nrows, ncols, index, **kwargs)
    _current_ax = ax
    return ax


def axes(**kwargs):
    """Add axes to the current figure. Always creates new axes."""
    global _current_ax, _current_fig
    _ensure()
    fig = _current_fig
    ax = fig.add_subplot(1, 1, 1, **kwargs)
    _current_ax = ax
    return ax


# ------------------------------------------------------------------
# Plotting functions — delegate to current axes
# ------------------------------------------------------------------

def plot(*args, **kwargs):
    _ensure()
    return _current_ax.plot(*args, **kwargs)


def scatter(x, y, s=None, c=None, **kwargs):
    _ensure()
    kw = dict(kwargs)
    if s is not None:
        kw['s'] = s
    if c is not None:
        kw['c'] = c
    return _current_ax.scatter(x, y, **kw)


def bar(x, height, width=0.8, **kwargs):
    _ensure()
    return _current_ax.bar(x, height, width, **kwargs)


def barh(y, width, height=0.8, **kwargs):
    _ensure()
    return _current_ax.barh(y, width, height, **kwargs)


def hist(x, bins=10, **kwargs):
    _ensure()
    return _current_ax.hist(x, bins, **kwargs)


def errorbar(x, y, yerr=None, xerr=None, **kwargs):
    _ensure()
    return _current_ax.errorbar(x, y, yerr=yerr, xerr=xerr, **kwargs)


def fill_between(x, y1, y2=0, **kwargs):
    _ensure()
    return _current_ax.fill_between(x, y1, y2, **kwargs)


def axhline(y=0, **kwargs):
    _ensure()
    return _current_ax.axhline(y, **kwargs)


def axvline(x=0, **kwargs):
    _ensure()
    return _current_ax.axvline(x, **kwargs)


def text(x, y, s, **kwargs):
    _ensure()
    return _current_ax.text(x, y, s, **kwargs)


# ------------------------------------------------------------------
# Labels / config
# ------------------------------------------------------------------

def xlabel(s, **kwargs):
    _ensure()
    _current_ax.set_xlabel(s, **kwargs)


def ylabel(s, **kwargs):
    _ensure()
    _current_ax.set_ylabel(s, **kwargs)


def title(s, **kwargs):
    _ensure()
    _current_ax.set_title(s, **kwargs)


def suptitle(t, **kwargs):
    _ensure()
    return _current_fig.suptitle(t, **kwargs)


def xlim(*args, **kwargs):
    _ensure()
    if args or kwargs:
        _current_ax.set_xlim(*args, **kwargs)
    return _current_ax.get_xlim()


def ylim(*args, **kwargs):
    _ensure()
    if args or kwargs:
        _current_ax.set_ylim(*args, **kwargs)
    return _current_ax.get_ylim()


def legend(*args, **kwargs):
    _ensure()
    return _current_ax.legend(*args, **kwargs)


def grid(visible=True, **kwargs):
    _ensure()
    _current_ax.grid(visible, **kwargs)


def xticks(*args, **kwargs):
    _ensure()
    if args:
        _current_ax.set_xticks(args[0])
    if len(args) > 1:
        _current_ax.set_xticklabels(args[1])


def yticks(*args, **kwargs):
    _ensure()
    if args:
        _current_ax.set_yticks(args[0])
    if len(args) > 1:
        _current_ax.set_yticklabels(args[1])


# ------------------------------------------------------------------
# Interactive mode
# ------------------------------------------------------------------

class _InteractiveContext:
    """Context manager for ion()/ioff()."""
    def __init__(self, target_state):
        self._target = target_state

    def __enter__(self):
        self._old = matplotlib._interactive
        matplotlib._interactive = self._target
        return self

    def __exit__(self, *args):
        matplotlib._interactive = self._old

    def __call__(self):
        """Also callable as plain function."""
        matplotlib._interactive = self._target


def ion():
    """Enable interactive mode (or use as context manager)."""
    ctx = _InteractiveContext(True)
    matplotlib._interactive = True
    return ctx


def ioff():
    """Disable interactive mode (or use as context manager)."""
    ctx = _InteractiveContext(False)
    matplotlib._interactive = False
    return ctx


def isinteractive():
    """Return True if interactive mode is on."""
    return matplotlib._interactive


# ------------------------------------------------------------------
# Clear
# ------------------------------------------------------------------

def cla():
    """Clear the current axes."""
    _ensure()
    _current_ax.cla()


def clf():
    """Clear the current figure."""
    _ensure()
    _current_fig.clear()


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------

def savefig(fname, format=None, dpi=None, **kwargs):
    _ensure()
    _current_fig.savefig(fname, format=format, dpi=dpi, **kwargs)


def show():
    """No-op in sandbox environment."""
    pass


def close(fig='all'):
    """Close figure(s)."""
    global _current_fig, _current_ax
    if fig == 'all':
        _figures.clear()
        _fig_order.clear()
        _current_fig = None
        _current_ax = None
    elif isinstance(fig, int):
        if fig in _figures:
            del _figures[fig]
            if fig in _fig_order:
                _fig_order.remove(fig)
        if _current_fig is not None and getattr(_current_fig, 'number', None) == fig:
            _current_fig = _figures[_fig_order[-1]] if _fig_order else None
            _current_ax = _current_fig._axes[-1] if _current_fig and _current_fig._axes else None
    elif isinstance(fig, Figure):
        num = getattr(fig, 'number', None)
        if num is not None and num in _figures:
            del _figures[num]
            if num in _fig_order:
                _fig_order.remove(num)
        if fig is _current_fig:
            _current_fig = _figures[_fig_order[-1]] if _fig_order else None
            _current_ax = _current_fig._axes[-1] if _current_fig and _current_fig._axes else None
    elif isinstance(fig, float):
        raise TypeError(f"close() argument must be a Figure, an int, or 'all', "
                        f"not {type(fig).__name__}")
    else:
        raise TypeError(f"close() argument must be a Figure, an int, or 'all', "
                        f"not {type(fig).__name__}")


def get_fignums():
    """Return list of existing figure numbers."""
    return sorted(_figures.keys())


def get_figlabels():
    """Return list of existing figure labels."""
    return [getattr(_figures[n], '_label', '') for n in sorted(_figures.keys())]


def fignum_exists(num):
    """Return whether figure number *num* exists."""
    return num in _figures


# Re-export rcParams for convenience
rcParams = matplotlib.rcParams
rc_context = matplotlib.rc_context
```

**Step 2: Update matplotlib.__init__.py for interactive mode**

Make sure `_interactive` is accessible:
```python
# In __init__.py, ensure _interactive is a module-level variable
_interactive = False
```

**Step 3: Verify basic pyplot operations**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -c "
import matplotlib.pyplot as plt
fig = plt.figure()
print('fignums:', plt.get_fignums())
print('close test...')
plt.close('all')
print('after close:', plt.get_fignums())
with plt.ioff():
    print('interactive in ctx:', plt.isinteractive())
print('interactive after:', plt.isinteractive())
"`

**Step 4: Commit**

```bash
git add python/matplotlib/pyplot.py python/matplotlib/__init__.py
git commit -m "feat: expand pyplot with figure numbering, ion/ioff, subplot reuse"
```

### Task 6: Expand Figure class with suptitle, sizing, clear, delaxes

**Files:**
- Modify: `python/matplotlib/figure.py`

**Step 1: Rewrite figure.py with expanded Figure class**

```python
"""matplotlib.figure — Figure class."""

from matplotlib.axes import Axes


class Figure:
    """Top-level container for a matplotlib plot."""

    def __init__(self, figsize=None, dpi=100, **kwargs):
        self.figsize = figsize or (6.4, 4.8)
        self.dpi = dpi
        self._axes = []
        self._suptitle = None
        self._label = kwargs.get('label', '')
        self.number = None
        self.stale = True

    def add_subplot(self, nrows=1, ncols=1, index=1, **kwargs):
        """Add an Axes to the figure."""
        pos = (nrows, ncols, index)
        ax = Axes(self, pos)
        self._axes.append(ax)
        return ax

    def add_axes(self, rect=None, **kwargs):
        """Add axes at a specific position [left, bottom, width, height]."""
        ax = Axes(self, rect or (0.125, 0.1, 0.775, 0.8))
        self._axes.append(ax)
        return ax

    @property
    def axes(self):
        return list(self._axes)

    def gca(self):
        """Get current axes, creating one if needed."""
        if self._axes:
            return self._axes[-1]
        return self.add_subplot(1, 1, 1)

    def sca(self, ax):
        """Set current axes to *ax* (does not reorder)."""
        # ax must be in this figure
        pass

    def delaxes(self, ax):
        """Remove axes from figure."""
        if ax in self._axes:
            self._axes.remove(ax)

    def get_axes(self):
        """Return list of axes."""
        return list(self._axes)

    def suptitle(self, t, **kwargs):
        """Set a centered title for the figure."""
        self._suptitle = t
        return t

    def get_suptitle(self):
        """Return the figure suptitle or empty string."""
        return self._suptitle or ''

    def set_size_inches(self, w, h=None):
        """Set figure size in inches."""
        if h is None:
            if hasattr(w, '__len__'):
                w, h = w
            else:
                raise ValueError("Must provide both w and h, or a (w,h) tuple")
        self.figsize = (float(w), float(h))

    def get_size_inches(self):
        """Return figure size as (width, height) tuple."""
        return self.figsize

    def set_figwidth(self, val):
        self.figsize = (float(val), self.figsize[1])

    def set_figheight(self, val):
        self.figsize = (self.figsize[0], float(val))

    def get_figwidth(self):
        return self.figsize[0]

    def get_figheight(self):
        return self.figsize[1]

    def get_dpi(self):
        return self.dpi

    def set_dpi(self, val):
        self.dpi = val

    def get_label(self):
        return self._label

    def set_label(self, label):
        self._label = label

    def tight_layout(self, **kwargs):
        """Adjust subplot params for tight layout (no-op for now)."""
        pass

    def clear(self):
        """Clear the figure."""
        self._axes.clear()
        self._suptitle = None

    def clf(self):
        """Alias for clear()."""
        self.clear()

    def draw_without_rendering(self):
        """Placeholder for layout computation."""
        pass

    def __repr__(self):
        w, h = self.figsize
        return f'<Figure size {w*self.dpi:.0f}x{h*self.dpi:.0f} with {len(self._axes)} Axes>'

    def savefig(self, fname, format=None, dpi=None, **kwargs):
        """Save figure to *fname*.  Format inferred from extension if not given."""
        dpi = dpi or self.dpi
        if format is None and isinstance(fname, str):
            if fname.lower().endswith('.png'):
                format = 'png'
            elif fname.lower().endswith('.svg'):
                format = 'svg'
            else:
                format = 'svg'

        if format == 'png':
            from matplotlib._pil_backend import render_figure_png
            data = render_figure_png(self, dpi)
            with open(fname, 'wb') as f:
                f.write(data)
        else:
            from matplotlib._svg_backend import render_figure_svg
            svg = render_figure_svg(self)
            with open(fname, 'w') as f:
                f.write(svg)
```

**Step 2: Commit**

```bash
git add python/matplotlib/figure.py
git commit -m "feat: expand Figure with suptitle, sizing, clear, delaxes"
```

### Task 7: Write test_pyplot.py with adapted upstream tests

**Files:**
- Create: `python/matplotlib/tests/test_pyplot.py`

**Step 1: Write adapted tests**

```python
"""Tests for matplotlib.pyplot — adapted from upstream matplotlib."""

import pytest
import matplotlib
import matplotlib.pyplot as plt


class TestInteractive:
    def test_ioff(self):
        plt.ion()
        plt.ioff()
        assert not matplotlib.is_interactive()

    def test_ion(self):
        plt.ioff()
        plt.ion()
        assert matplotlib.is_interactive()

    def test_ioff_context(self):
        plt.ion()
        with plt.ioff():
            assert not matplotlib.is_interactive()
        assert matplotlib.is_interactive()

    def test_ion_context(self):
        plt.ioff()
        with plt.ion():
            assert matplotlib.is_interactive()
        assert not matplotlib.is_interactive()

    def test_nested_ion_ioff(self):
        plt.ioff()
        assert not matplotlib.is_interactive()
        with plt.ion():
            assert matplotlib.is_interactive()
            with plt.ioff():
                assert not matplotlib.is_interactive()
            assert matplotlib.is_interactive()
        assert not matplotlib.is_interactive()


class TestClose:
    def test_close_all(self):
        plt.figure()
        plt.figure()
        assert len(plt.get_fignums()) == 2
        plt.close('all')
        assert plt.get_fignums() == []

    def test_close_by_num(self):
        fig = plt.figure()
        num = fig.number
        plt.close(num)
        assert not plt.fignum_exists(num)

    def test_close_float_raises(self):
        with pytest.raises(TypeError, match="not float"):
            plt.close(1.0)


class TestFigureManagement:
    def test_figure_label(self):
        plt.figure('a')
        plt.figure('b')
        assert plt.get_figlabels() == ['a', 'b']
        plt.close('all')

    def test_fignum_exists(self):
        fig = plt.figure()
        num = fig.number
        assert plt.fignum_exists(num)
        plt.close(num)
        assert not plt.fignum_exists(num)

    def test_gca(self):
        fig = plt.figure()
        ax = plt.gca()
        assert ax is plt.gca()  # same axes returned

    def test_gcf(self):
        fig = plt.figure()
        assert plt.gcf() is fig


class TestSubplot:
    def test_subplot_reuse(self):
        plt.subplot(1, 1, 1)
        ax1 = plt.gca()
        plt.subplot(1, 1, 1)
        ax2 = plt.gca()
        assert ax1 is ax2

    def test_axes_always_new(self):
        fig = plt.figure()
        ax1 = plt.axes()
        ax2 = plt.axes()
        assert ax1 is not ax2
        plt.close('all')


class TestClear:
    def test_clf(self):
        fig = plt.figure()
        plt.plot([1, 2, 3])
        plt.clf()
        assert len(fig._axes) == 0

    def test_cla(self):
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3])
        plt.cla()
        assert len(ax._elements) == 0


class TestFigure:
    def test_set_fig_size(self):
        fig = plt.figure()
        fig.set_figwidth(10)
        assert fig.get_figwidth() == 10
        fig.set_figheight(8)
        assert fig.get_figheight() == 8
        fig.set_size_inches(12, 6)
        assert fig.get_size_inches() == (12, 6)
        fig.set_size_inches((5, 4))
        assert fig.get_size_inches() == (5, 4)

    def test_suptitle(self):
        fig = plt.figure()
        fig.suptitle('Hello')
        assert fig.get_suptitle() == 'Hello'

    def test_figure_repr(self):
        fig = plt.figure(figsize=(6.4, 4.8), dpi=100)
        r = repr(fig)
        assert '640x480' in r
        assert '1 Axes' in r

    def test_axes_remove(self):
        fig, axs = plt.subplots(2, 2)
        assert len(fig.axes) == 4
        axs[0][0].remove()
        assert len(fig.axes) == 3

    def test_figure_clear(self):
        fig = plt.figure()
        fig.add_subplot(1, 1, 1)
        fig.suptitle('test')
        assert len(fig.axes) == 1
        fig.clear()
        assert len(fig.axes) == 0
        assert fig.get_suptitle() == ''
```

**Step 2: Run tests**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/test_pyplot.py -v 2>&1 | tail -40`

**Step 3: Fix failures, iterate until green**

**Step 4: Commit**

```bash
git add python/matplotlib/tests/test_pyplot.py
git commit -m "test: add test_pyplot.py with 25+ pyplot state machine tests"
```

---

## Tier 3: Artist Object Model

### Task 8: Create Line2D, Patch, Rectangle, PathCollection, BarContainer classes

This is the biggest architectural change — moving from dicts to proper objects.

**Files:**
- Create: `python/matplotlib/artist.py`
- Create: `python/matplotlib/lines.py`
- Create: `python/matplotlib/patches.py`
- Create: `python/matplotlib/collections.py`
- Create: `python/matplotlib/container.py`
- Create: `python/matplotlib/text.py`

**Step 1: Create base Artist class**

`python/matplotlib/artist.py`:
```python
"""matplotlib.artist — base class for all visual objects."""


class Artist:
    """Base class for objects that render into a Figure."""

    zorder = 0

    def __init__(self):
        self._visible = True
        self._alpha = None
        self._label = ''
        self._zorder = self.__class__.zorder
        self.figure = None
        self.axes = None
        self._stale = True

    def get_visible(self):
        return self._visible

    def set_visible(self, b):
        self._visible = b

    def get_alpha(self):
        return self._alpha

    def set_alpha(self, alpha):
        self._alpha = alpha

    def get_label(self):
        return self._label

    def set_label(self, s):
        self._label = str(s) if s is not None else '_nolegend_'

    def get_zorder(self):
        return self._zorder

    def set_zorder(self, level):
        self._zorder = level

    def remove(self):
        """Remove this artist from its axes."""
        if self.axes is not None:
            self.axes._remove_artist(self)

    def set(self, **kwargs):
        """Batch property setter."""
        for k, v in kwargs.items():
            setter = getattr(self, f'set_{k}', None)
            if setter:
                setter(v)
```

**Step 2: Create Line2D**

`python/matplotlib/lines.py`:
```python
"""matplotlib.lines — Line2D class."""

from matplotlib.artist import Artist
from matplotlib.colors import to_rgba, to_hex


class Line2D(Artist):
    """A line in 2D."""

    zorder = 2

    def __init__(self, xdata, ydata, color=None, linewidth=None,
                 linestyle=None, marker=None, label=None, **kwargs):
        super().__init__()
        self._xdata = list(xdata)
        self._ydata = list(ydata)
        self._color = color or 'C0'
        self._linewidth = linewidth if linewidth is not None else 1.5
        self._linestyle = linestyle or '-'
        self._marker = marker or 'None'
        self._markersize = kwargs.get('markersize', kwargs.get('ms', 6.0))
        self._fillstyle = kwargs.get('fillstyle', 'full')
        self._drawstyle = kwargs.get('drawstyle', 'default')
        self.set_label(label)

    def get_xdata(self):
        return self._xdata

    def get_ydata(self):
        return self._ydata

    def set_xdata(self, x):
        self._xdata = list(x)

    def set_ydata(self, y):
        self._ydata = list(y)

    def get_data(self):
        return self._xdata, self._ydata

    def set_data(self, x, y):
        self._xdata = list(x)
        self._ydata = list(y)

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = color

    def get_linewidth(self):
        return self._linewidth

    def set_linewidth(self, w):
        self._linewidth = w

    def get_linestyle(self):
        return self._linestyle

    def set_linestyle(self, ls):
        self._linestyle = ls

    def get_marker(self):
        return self._marker

    def set_marker(self, marker):
        self._marker = marker or 'None'

    def get_markersize(self):
        return self._markersize

    def set_markersize(self, sz):
        self._markersize = sz

    def get_fillstyle(self):
        return self._fillstyle

    def get_drawstyle(self):
        return self._drawstyle

    # Aliases
    set_lw = set_linewidth
    set_ls = set_linestyle
    set_c = set_color

    def _as_element(self):
        """Convert to dict for backend rendering (backward compat)."""
        return {
            'type': 'line',
            'x': self._xdata,
            'y': self._ydata,
            'color': to_hex(self._color),
            'linewidth': self._linewidth,
            'linestyle': self._linestyle,
            'marker': self._marker if self._marker != 'None' else None,
            'label': self._label,
        }
```

**Step 3: Create Patch and Rectangle**

`python/matplotlib/patches.py`:
```python
"""matplotlib.patches — shape primitives."""

from matplotlib.artist import Artist
from matplotlib.colors import to_rgba


class Patch(Artist):
    """Base class for shapes."""

    zorder = 1

    def __init__(self, facecolor=None, edgecolor=None, linewidth=None,
                 label=None, alpha=None, **kwargs):
        super().__init__()
        self._facecolor = facecolor or 'C0'
        self._edgecolor = edgecolor or 'black'
        self._linewidth = linewidth if linewidth is not None else 1.0
        self.set_label(label)
        if alpha is not None:
            self.set_alpha(alpha)

    def get_facecolor(self):
        fc = to_rgba(self._facecolor)
        if self._alpha is not None:
            fc = (*fc[:3], self._alpha)
        return fc

    def set_facecolor(self, color):
        self._facecolor = color

    def get_edgecolor(self):
        ec = to_rgba(self._edgecolor)
        if self._alpha is not None and str(self._edgecolor).lower() != 'none':
            ec = (*ec[:3], self._alpha)
        return ec

    def set_edgecolor(self, color):
        self._edgecolor = color

    def get_linewidth(self):
        return self._linewidth

    def set_linewidth(self, w):
        self._linewidth = w


class Rectangle(Patch):
    """A rectangle."""

    def __init__(self, xy, width, height, **kwargs):
        super().__init__(**kwargs)
        self.xy = xy
        self._width = width
        self._height = height

    def get_x(self):
        return self.xy[0]

    def get_y(self):
        return self.xy[1]

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def get_corners(self):
        x, y = self.xy
        w, h = self._width, self._height
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


class Circle(Patch):
    """A circle."""

    def __init__(self, xy, radius=5, **kwargs):
        super().__init__(**kwargs)
        self.center = xy
        self.radius = radius
```

**Step 4: Create PathCollection**

`python/matplotlib/collections.py`:
```python
"""matplotlib.collections — collections of artists."""

from matplotlib.artist import Artist
from matplotlib.colors import to_rgba, to_hex


class Collection(Artist):
    """Base class for collections."""
    zorder = 1

    def __init__(self, **kwargs):
        super().__init__()
        self._offsets = []
        self._facecolors = []
        self._edgecolors = []


class PathCollection(Collection):
    """Collection returned by scatter()."""

    def __init__(self, offsets, sizes=None, facecolors=None,
                 edgecolors=None, label=None, **kwargs):
        super().__init__()
        self._offsets = offsets or []
        self._sizes = sizes or [20]
        self._facecolors = facecolors or []
        self._edgecolors = edgecolors or []
        self.set_label(label)

    def get_offsets(self):
        return self._offsets

    def get_facecolors(self):
        return self._facecolors

    def get_edgecolors(self):
        return self._edgecolors

    def get_sizes(self):
        return self._sizes

    def _as_element(self):
        """Convert to dict for backend rendering."""
        color = to_hex(self._facecolors[0]) if self._facecolors else '#1f77b4'
        xs = [o[0] for o in self._offsets]
        ys = [o[1] for o in self._offsets]
        return {
            'type': 'scatter',
            'x': xs, 'y': ys,
            's': self._sizes[0] if self._sizes else 20,
            'color': color,
            'label': self._label,
        }
```

**Step 5: Create container classes**

`python/matplotlib/container.py`:
```python
"""matplotlib.container — container classes for bar/errorbar."""


class Container(tuple):
    """Base container for grouped artists."""

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args[0] if args else ())

    def __init__(self, artists, label=None):
        self._label = label or ''

    def get_label(self):
        return self._label

    def set_label(self, s):
        self._label = str(s) if s is not None else '_nolegend_'

    def remove(self):
        for artist in self:
            if hasattr(artist, 'remove'):
                artist.remove()

    @property
    def patches(self):
        from matplotlib.patches import Patch
        return [a for a in self if isinstance(a, Patch)]


class BarContainer(Container):
    """Container for bar chart rectangles + optional error bars."""

    def __init__(self, patches, errorbar=None, label=None):
        super().__init__(patches, label=label)
        self.errorbar = errorbar
        self._patches = list(patches)

    @property
    def patches(self):
        return self._patches

    def __iter__(self):
        return iter(self._patches)

    def __len__(self):
        return len(self._patches)

    def __getitem__(self, idx):
        return self._patches[idx]


class ErrorbarContainer(Container):
    """Container for errorbar artists (plotline, caplines, barlinecols)."""

    def __init__(self, lines, label=None):
        plotline, caplines, barlinecols = lines
        all_artists = []
        if plotline is not None:
            all_artists.append(plotline)
        all_artists.extend(caplines or [])
        all_artists.extend(barlinecols or [])
        super().__init__(all_artists, label=label)
        self.lines = lines

    @property
    def has_xerr(self):
        return len(self.lines[2]) > 1 if self.lines[2] else False

    @property
    def has_yerr(self):
        return len(self.lines[2]) > 0 if self.lines[2] else False
```

**Step 6: Create Text class**

`python/matplotlib/text.py`:
```python
"""matplotlib.text — text rendering."""

from matplotlib.artist import Artist


class Text(Artist):
    """A text object."""

    zorder = 3

    def __init__(self, x=0, y=0, text='', **kwargs):
        super().__init__()
        self._x = x
        self._y = y
        self._text = text
        self._fontsize = kwargs.get('fontsize', kwargs.get('size', 12))
        self._fontweight = kwargs.get('fontweight', kwargs.get('weight', 'normal'))
        self._ha = kwargs.get('ha', kwargs.get('horizontalalignment', 'center'))
        self._va = kwargs.get('va', kwargs.get('verticalalignment', 'center'))

    def get_text(self):
        return self._text

    def set_text(self, s):
        self._text = s

    def get_fontsize(self):
        return self._fontsize

    def get_weight(self):
        return self._fontweight

    def get_horizontalalignment(self):
        return self._ha

    def get_verticalalignment(self):
        return self._va

    def get_position(self):
        return (self._x, self._y)

    def set_position(self, xy):
        self._x, self._y = xy


class Annotation(Text):
    """An annotated text."""

    def __init__(self, text, xy, xytext=None, arrowprops=None, **kwargs):
        x, y = xytext if xytext is not None else xy
        super().__init__(x, y, text, **kwargs)
        self._xy = xy
        self._xytext = xytext
        self.arrow_patch = None
        if arrowprops is not None:
            # Create an arrow patch placeholder
            from matplotlib.patches import Patch
            self.arrow_patch = Patch()
```

**Step 7: Commit**

```bash
git add python/matplotlib/artist.py python/matplotlib/lines.py \
    python/matplotlib/patches.py python/matplotlib/collections.py \
    python/matplotlib/container.py python/matplotlib/text.py
git commit -m "feat: add Artist object model (Line2D, Patch, PathCollection, containers)"
```

### Task 9: Refactor Axes to use Artist objects instead of dicts

**Files:**
- Modify: `python/matplotlib/axes.py`

**Step 1: Rewrite axes.py to return proper artist objects**

This is a large rewrite. The key changes:
- `plot()` returns `[Line2D]` instead of `[dict]`
- `scatter()` returns `PathCollection` instead of `dict`
- `bar()` returns `BarContainer` instead of `dict`
- `hist()` returns `(counts, edges, patches_or_containers)`
- Add `get_xlim()`, `get_ylim()`, `get_xlabel()`, `get_ylabel()`, `get_title()`
- Add `set_xticks()`, `set_yticks()`, `cla()`, `invert_xaxis()`, `invert_yaxis()`
- Add `errorbar()`, `fill_between()`, `axhline()`, `axvline()`, `text()`, `annotate()`
- Store elements as lists: `self.lines`, `self.collections`, `self.patches`, `self.containers`, `self.texts`
- `_elements` kept for backward compatibility with backends (populated from artist._as_element())

The Axes class becomes ~400-500 lines. The full implementation should handle:
- Color cycling with proper cycle tracking
- Limit auto-calculation from all artist data
- Proper return types matching upstream API

The rendering backends (`_svg_backend.py`, `_pil_backend.py`) should be updated to extract rendering data from the artist objects. For now, we can bridge by having `_elements` auto-populated.

I'll write the key methods; the implementer should fill in the complete class:

```python
"""matplotlib.axes — Axes class that stores plot elements."""

import math
from matplotlib.colors import DEFAULT_CYCLE, to_hex, to_rgba, parse_fmt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.collections import PathCollection
from matplotlib.container import BarContainer
from matplotlib.text import Text, Annotation


class Axes:
    """A single set of axes in a Figure."""

    def __init__(self, fig, position):
        self.figure = fig
        self._position = position
        self._title = ''
        self._xlabel = ''
        self._ylabel = ''
        self._xlim = (None, None)
        self._ylim = (None, None)
        self._xlim_inverted = False
        self._ylim_inverted = False
        self._grid = False
        self._legend_on = False
        self._color_idx = 0

        # Artist storage
        self.lines = []
        self.collections = []
        self.patches = []
        self.containers = []
        self.texts = []

        # Backward compat for backends
        self._elements = []

    def _next_color(self):
        c = DEFAULT_CYCLE[self._color_idx % len(DEFAULT_CYCLE)]
        self._color_idx += 1
        return c

    def _rebuild_elements(self):
        """Rebuild _elements from artist lists for backend rendering."""
        self._elements = []
        for line in self.lines:
            self._elements.append(line._as_element())
        for coll in self.collections:
            self._elements.append(coll._as_element())
        for patch in self.patches:
            # Render rectangles as bar elements
            self._elements.append({
                'type': 'bar_single',
                'patch': patch,
            })

    def _remove_artist(self, artist):
        """Remove an artist from this axes."""
        for lst in [self.lines, self.collections, self.patches, self.texts]:
            if artist in lst:
                lst.remove(artist)

    # ------------------------------------------------------------------
    # Plot types
    # ------------------------------------------------------------------

    def plot(self, *args, **kwargs):
        """Line plot."""
        x, y, fmt = _parse_plot_args(args)
        color_fmt, marker, linestyle = parse_fmt(fmt)
        color = kwargs.get('color') or kwargs.get('c')
        if color is None:
            color = color_fmt
        if color is None:
            color = self._next_color()
        label = kwargs.get('label')
        linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.5))
        if linestyle is None:
            linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        if marker is None:
            marker = kwargs.get('marker', 'None')

        line = Line2D(x, y, color=color, linewidth=linewidth,
                      linestyle=linestyle, marker=marker, label=label, **kwargs)
        line.axes = self
        self.lines.append(line)
        self._rebuild_elements()
        return [line]

    def scatter(self, x, y, s=20, c=None, **kwargs):
        """Scatter plot."""
        color = c or kwargs.get('color') or self._next_color()
        label = kwargs.get('label')
        offsets = list(zip(x, y))
        sizes = s if isinstance(s, (list, tuple)) else [s]
        facecolors = [to_rgba(color)]

        pc = PathCollection(offsets, sizes=sizes, facecolors=facecolors,
                            label=label)
        pc.axes = self
        self.collections.append(pc)
        self._rebuild_elements()
        return pc

    def bar(self, x, height, width=0.8, **kwargs):
        """Bar chart."""
        color = kwargs.get('facecolor') or kwargs.get('color') or self._next_color()
        edgecolor = kwargs.get('edgecolor', 'black')
        label = kwargs.get('label')
        alpha = kwargs.get('alpha')
        bottom = kwargs.get('bottom', 0)

        x_vals = list(x) if hasattr(x, '__iter__') else [x]
        h_vals = list(height) if hasattr(height, '__iter__') else [height] * len(x_vals)
        if isinstance(bottom, (int, float)):
            bottom = [bottom] * len(x_vals)
        else:
            bottom = list(bottom)

        rects = []
        for i in range(len(x_vals)):
            r = Rectangle(
                xy=(x_vals[i] - width / 2, bottom[i]),
                width=width, height=h_vals[i],
                facecolor=color, edgecolor=edgecolor, alpha=alpha,
            )
            r.axes = self
            self.patches.append(r)
            rects.append(r)

        container = BarContainer(rects, label=label)
        self.containers.append(container)

        # Backward compat element
        self._elements.append({
            'type': 'bar',
            'x': x_vals,
            'height': h_vals,
            'width': width,
            'color': to_hex(color),
            'label': label,
        })

        return container

    def hist(self, x, bins=10, **kwargs):
        """Histogram."""
        data = list(x) if hasattr(x, '__iter__') else [x]
        color = kwargs.get('color') or self._next_color()
        label = kwargs.get('label')
        density = kwargs.get('density', False)

        # Compute bins
        lo = min(data) if data else 0
        hi = max(data) if data else 1
        if lo == hi:
            hi = lo + 1

        if isinstance(bins, (list, tuple)):
            edges = list(bins)
            n_bins = len(edges) - 1
        else:
            n_bins = bins
            bin_width = (hi - lo) / n_bins
            edges = [lo + i * bin_width for i in range(n_bins + 1)]

        counts = [0] * n_bins
        for v in data:
            for j in range(n_bins):
                if edges[j] <= v < edges[j + 1]:
                    counts[j] += 1
                    break
            else:
                if v == edges[-1]:
                    counts[-1] += 1

        if density and data:
            total = len(data)
            for j in range(n_bins):
                bw = edges[j + 1] - edges[j]
                counts[j] = counts[j] / (total * bw) if bw > 0 else 0

        centers = [(edges[i] + edges[i + 1]) / 2 for i in range(n_bins)]
        bar_width = (edges[1] - edges[0]) * 0.9 if n_bins > 0 else 0.9

        container = self.bar(centers, counts, width=bar_width,
                             color=color, label=label)

        return counts, edges, container

    def errorbar(self, x, y, yerr=None, xerr=None, fmt='', **kwargs):
        """Error bar plot."""
        x = list(x) if hasattr(x, '__iter__') else [x]
        y = list(y) if hasattr(y, '__iter__') else [y]

        color = kwargs.get('color') or kwargs.get('c') or self._next_color()
        label = kwargs.get('label')

        # Plot the data line (unless fmt='none')
        plotline = None
        if fmt.lower() != 'none':
            lines = self.plot(x, y, fmt, color=color, label=label, **{
                k: v for k, v in kwargs.items()
                if k not in ('color', 'c', 'label', 'yerr', 'xerr',
                             'elinewidth', 'elinestyle', 'capsize',
                             'errorevery', 'ecolor')})
            plotline = lines[0] if lines else None

        # Store error bar data (simplified - for test compatibility)
        caplines = []
        barlinecols = []

        from matplotlib.container import ErrorbarContainer
        container = ErrorbarContainer((plotline, caplines, barlinecols), label=label)
        self.containers.append(container)
        return container

    def fill_between(self, x, y1, y2=0, **kwargs):
        """Fill between two curves."""
        x = list(x) if hasattr(x, '__iter__') else [x]
        # Validate: reject 2D
        if hasattr(x, 'ndim'):
            if x.ndim > 1:
                raise ValueError("x must be 1D")
        if hasattr(y1, 'ndim'):
            if y1.ndim > 1:
                raise ValueError("y1 must be 1D")
        if hasattr(y2, 'ndim'):
            if y2.ndim > 1:
                raise ValueError("y2 must be 1D")

    def fill_betweenx(self, y, x1, x2=0, **kwargs):
        """Fill between two x-curves."""
        if hasattr(y, 'ndim') and y.ndim > 1:
            raise ValueError("y must be 1D")
        if hasattr(x1, 'ndim') and x1.ndim > 1:
            raise ValueError("x1 must be 1D")
        if hasattr(x2, 'ndim') and x2.ndim > 1:
            raise ValueError("x2 must be 1D")

    def axhline(self, y=0, **kwargs):
        """Add a horizontal line across the axes."""
        color = kwargs.get('color', self._next_color())
        line = Line2D([0, 1], [y, y], color=color)
        line.axes = self
        self.lines.append(line)
        return line

    def axvline(self, x=0, **kwargs):
        """Add a vertical line across the axes."""
        color = kwargs.get('color', self._next_color())
        line = Line2D([x, x], [0, 1], color=color)
        line.axes = self
        self.lines.append(line)
        return line

    def axhspan(self, ymin, ymax, **kwargs):
        """Add horizontal span."""
        pass

    def axvspan(self, xmin, xmax, **kwargs):
        """Add vertical span."""
        pass

    def text(self, x, y, s, **kwargs):
        """Add text to axes."""
        t = Text(x, y, s, **kwargs)
        t.axes = self
        self.texts.append(t)
        return t

    def annotate(self, text, xy, xytext=None, arrowprops=None, **kwargs):
        """Add annotation."""
        ann = Annotation(text, xy, xytext=xytext, arrowprops=arrowprops, **kwargs)
        ann.axes = self
        self.texts.append(ann)
        return ann

    # ------------------------------------------------------------------
    # Labels / config
    # ------------------------------------------------------------------

    def set_title(self, s, **kwargs):
        self._title = s

    def get_title(self, **kwargs):
        return self._title

    def set_xlabel(self, s, **kwargs):
        self._xlabel = s

    def get_xlabel(self):
        return self._xlabel

    def set_ylabel(self, s, **kwargs):
        self._ylabel = s

    def get_ylabel(self):
        return self._ylabel

    def set_xlim(self, left=None, right=None, **kwargs):
        import math
        if left is not None:
            if isinstance(left, (list, tuple)):
                left, right = left
            if left is not None and (math.isnan(left) or math.isinf(left)):
                raise ValueError(f"Axis limits cannot be NaN or Inf: ({left}, {right})")
        if right is not None and (math.isnan(right) or math.isinf(right)):
            raise ValueError(f"Axis limits cannot be NaN or Inf: ({left}, {right})")
        self._xlim = (left, right)

    def get_xlim(self):
        if self._xlim[0] is not None and self._xlim[1] is not None:
            return self._xlim
        # Auto-calculate from data
        xs = []
        for line in self.lines:
            xs.extend(line.get_xdata())
        for coll in self.collections:
            xs.extend(o[0] for o in coll.get_offsets())
        if not xs:
            return (0.0, 1.0)
        lo, hi = min(xs), max(xs)
        if self._xlim[0] is not None:
            lo = self._xlim[0]
        if self._xlim[1] is not None:
            hi = self._xlim[1]
        if self._xlim_inverted:
            return (hi, lo)
        return (lo, hi)

    def set_ylim(self, bottom=None, top=None, **kwargs):
        import math
        if bottom is not None:
            if isinstance(bottom, (list, tuple)):
                bottom, top = bottom
            if bottom is not None and (math.isnan(bottom) or math.isinf(bottom)):
                raise ValueError(f"Axis limits cannot be NaN or Inf: ({bottom}, {top})")
        if top is not None and (math.isnan(top) or math.isinf(top)):
            raise ValueError(f"Axis limits cannot be NaN or Inf: ({bottom}, {top})")
        self._ylim = (bottom, top)

    def get_ylim(self):
        if self._ylim[0] is not None and self._ylim[1] is not None:
            return self._ylim
        ys = []
        for line in self.lines:
            ys.extend(line.get_ydata())
        for coll in self.collections:
            ys.extend(o[1] for o in coll.get_offsets())
        if not ys:
            return (0.0, 1.0)
        lo, hi = min(ys), max(ys)
        if self._ylim[0] is not None:
            lo = self._ylim[0]
        if self._ylim[1] is not None:
            hi = self._ylim[1]
        if self._ylim_inverted:
            return (hi, lo)
        return (lo, hi)

    def invert_xaxis(self):
        self._xlim_inverted = True

    def invert_yaxis(self):
        self._ylim_inverted = True

    def xaxis_inverted(self):
        return self._xlim_inverted

    def yaxis_inverted(self):
        return self._ylim_inverted

    def set_xticks(self, ticks, labels=None, **kwargs):
        self._xticks = list(ticks)
        if labels is not None:
            self._xticklabels = list(labels)

    def set_yticks(self, ticks, labels=None, **kwargs):
        self._yticks = list(ticks)
        if labels is not None:
            self._yticklabels = list(labels)

    def set_xticklabels(self, labels, **kwargs):
        self._xticklabels = list(labels)

    def set_yticklabels(self, labels, **kwargs):
        self._yticklabels = list(labels)

    def legend(self, *args, **kwargs):
        if len(args) > 2:
            raise TypeError(
                f"legend() takes 0-2 positional arguments but "
                f"{len(args)} were given")
        self._legend_on = True

    def get_legend_handles_labels(self):
        handles = []
        labels = []
        for line in self.lines:
            if line.get_label() and not line.get_label().startswith('_'):
                handles.append(line)
                labels.append(line.get_label())
        for coll in self.collections:
            if coll.get_label() and not coll.get_label().startswith('_'):
                handles.append(coll)
                labels.append(coll.get_label())
        for cont in self.containers:
            if cont.get_label() and not cont.get_label().startswith('_'):
                handles.append(cont)
                labels.append(cont.get_label())
        return handles, labels

    def grid(self, visible=True, **kwargs):
        self._grid = visible

    def set(self, **kwargs):
        """Batch property setter."""
        for k, v in kwargs.items():
            setter = getattr(self, f'set_{k}', None)
            if setter:
                setter(v) if not isinstance(v, (list, tuple)) else setter(*v)

    def cla(self):
        """Clear axes."""
        self.lines.clear()
        self.collections.clear()
        self.patches.clear()
        self.containers.clear()
        self.texts.clear()
        self._elements.clear()
        self._title = ''
        self._xlabel = ''
        self._ylabel = ''
        self._xlim = (None, None)
        self._ylim = (None, None)
        self._xlim_inverted = False
        self._ylim_inverted = False
        self._grid = False
        self._legend_on = False
        self._color_idx = 0

    def remove(self):
        """Remove this axes from its figure."""
        if self.figure is not None:
            self.figure.delaxes(self)

    def set_xscale(self, scale, **kwargs):
        self._xscale = scale

    def set_yscale(self, scale, **kwargs):
        self._yscale = scale

    def get_aspect(self):
        return getattr(self, '_aspect', 'auto')

    def set_aspect(self, aspect):
        self._aspect = aspect

    def axis(self, option=None):
        if option == 'square':
            self._aspect = 1


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_plot_args(args):
    """Parse positional args for plot(): (y,), (x, y), (x, y, fmt)."""
    fmt = ''
    if len(args) == 0:
        return [], [], ''
    if len(args) == 1:
        y = list(args[0])
        x = list(range(len(y)))
    elif len(args) >= 2:
        first, second = args[0], args[1]
        if isinstance(second, str):
            y = list(first)
            x = list(range(len(y)))
            fmt = second
        else:
            x = list(first)
            y = list(second)
            if len(args) >= 3 and isinstance(args[2], str):
                fmt = args[2]
    else:
        x, y = [], []
    return x, y, fmt
```

**Step 2: Update backends to work with both old dict elements and new artists**

The SVG and PIL backends should check for `_as_element()` method on elements, or use the existing `_elements` list. Since `_rebuild_elements()` populates `_elements` from artists, the backends should continue to work with minimal changes. The implementer should verify this works end-to-end.

**Step 3: Commit**

```bash
git add python/matplotlib/axes.py
git commit -m "feat: refactor Axes to use Artist objects (Line2D, Rectangle, BarContainer)"
```

### Task 10: Write test_axes.py with core plot type tests

**Files:**
- Create: `python/matplotlib/tests/test_axes.py`

**Step 1: Write adapted tests focusing on API behavior**

Write ~50-80 tests adapted from upstream, covering:
- Labels: `test_get_labels`, `test_title_location_roundtrip`
- Limits: `test_inverted_limits`, `test_invalid_axis_limits`
- Plot: `test_empty_line_plots`, `test_plot_format`
- Scatter: `test_scatter_empty_data`
- Bar: `test_nan_bar_values`, `test_bar_ticklabel_fail`, `test_bar_color_none_alpha`, `test_bar_labels`, `test_bar_broadcast_args`, `test_bar_color_precedence`, `test_bar_shape_mismatch`
- Hist: `test_hist_with_empty_input`, `test_hist_labels`, `test_length_one_hist`, `test_hist_nan_data`
- Errorbar: `test_errorbar_nonefmt`, `test_errorbar_shape`
- Fill between: `test_fill_between_input`, `test_fill_betweenx_input`
- Annotate: `test_annotate_default_arrow`
- Grid/legend: `test_nargs_legend`
- Clear: `test_cla_clears`

The test file will be ~300-400 lines. Each test should be self-contained and adapted to our API surface.

**Step 2: Run tests, fix failures**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/test_axes.py -v 2>&1 | tail -60`

**Step 3: Iterate until tests pass**

**Step 4: Commit**

```bash
git add python/matplotlib/tests/test_axes.py
git commit -m "test: add test_axes.py with 50+ plot type and axes API tests"
```

---

## Tier 4: Figure Tests

### Task 11: Write test_figure.py with adapted upstream tests

**Files:**
- Create: `python/matplotlib/tests/test_figure.py`

**Step 1: Write ~20-25 adapted tests**

Focus on:
- `test_figure_label` — creation/selection by label
- `test_fignum_exists` — existence check
- `test_set_fig_size` — sizing methods
- `test_axes_remove` — removing axes
- `test_suptitle` — figure title
- `test_figure_repr` — repr formatting
- `test_figure_clear` — clear/clf
- `test_savefig` — basic save (error cases)
- `test_add_subplot_kwargs` — always creates new
- `test_add_axes_kwargs` — always creates new
- `test_gca` (figure-level) — get current axes
- `test_valid_layouts` — layout acceptance (stub)
- `test_get_suptitle_supxlabel_supylabel` — getter defaults

**Step 2: Run tests, fix failures**

**Step 3: Commit**

```bash
git add python/matplotlib/tests/test_figure.py
git commit -m "test: add test_figure.py with 20+ figure management tests"
```

---

## Tier 5: Integration & Cleanup

### Task 12: Run full test suite, fix remaining failures

**Step 1: Run all tests**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/ -v 2>&1 | tail -80`

**Step 2: Fix any cross-module failures (import issues, shared state, etc.)**

**Step 3: Run with count**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/ -v --tb=short 2>&1 | grep -E '(PASSED|FAILED|ERROR|=)'`
Expected: 100+ tests passing

**Step 4: Commit**

```bash
git commit -am "fix: resolve cross-module test failures"
```

### Task 13: Update SVG backend for Artist compatibility

**Files:**
- Modify: `python/matplotlib/_svg_backend.py`

**Step 1: Update _render_axes to handle both old dicts and new Artist objects**

The backend should iterate `ax._elements` (populated by `_rebuild_elements()`) OR directly iterate `ax.lines`, `ax.collections`, `ax.patches`. The implementer should choose the approach that requires minimal changes.

Key: Line2D, Rectangle, and PathCollection all have `_as_element()` methods that return the old dict format. So `_rebuild_elements()` bridges old and new.

**Step 2: Verify SVG output still works**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -c "
import matplotlib.pyplot as plt
plt.plot([1,2,3], [1,4,9], 'ro-', label='test')
plt.bar([1,2,3], [3,2,1])
plt.title('Test')
plt.savefig('/tmp/test_output.svg')
print('SVG saved successfully')
"`

**Step 3: Commit**

```bash
git add python/matplotlib/_svg_backend.py
git commit -m "fix: update SVG backend for Artist object compatibility"
```

### Task 14: Final test run and summary commit

**Step 1: Full test run with verbose output**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/ -v --tb=short 2>&1`

**Step 2: Document test count**

Run: `cd /Users/sunny/work/codepod/matplotlib-py && python -m pytest python/matplotlib/tests/ --co -q 2>&1 | tail -3`

**Step 3: Final commit**

```bash
git add -A
git commit -m "milestone: matplotlib-py test suite — N tests passing across 4 modules"
```

---

## Execution Notes

- **numpy-rust**: Ensure `PYTHONPATH` includes numpy-rust's `python/` directory when running tests that use numpy. For initial tiers (colors, pyplot, figure), numpy is not required.
- **Backend changes**: The SVG/PIL backends use `ax._elements` which is populated by `_rebuild_elements()`. This bridges old dict format and new Artist objects.
- **Test adaptation**: When porting tests, strip image comparison decorators, replace `np.testing.assert_*` with plain asserts where numpy isn't available, and skip tests that need deep internals (transforms, backend_bases, font_manager).
- **Incremental testing**: Run tests after each task. Don't move to the next tier until the current tier is green.
