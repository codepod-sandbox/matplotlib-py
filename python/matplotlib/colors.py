"""
matplotlib.colors — colour name resolution, hex conversion, normalization.

Provides color conversion utilities, named-color dictionaries, and
normalization classes for mapping data values to the [0, 1] interval.
"""

import math
import re

# ===================================================================
# Default colour cycle (matplotlib C0-C9)
# ===================================================================

DEFAULT_CYCLE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
]

# ===================================================================
# Named-colour dictionaries
# ===================================================================

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

BASE_COLORS = {
    'b': (0.0, 0.0, 1.0),
    'g': (0.0, 0.5019607843137255, 0.0),
    'r': (1.0, 0.0, 0.0),
    'c': (0.0, 0.7490196078431373, 0.7490196078431373),
    'm': (0.7490196078431373, 0.0, 0.7490196078431373),
    'y': (0.7490196078431373, 0.7490196078431373, 0.0),
    'k': (0.0, 0.0, 0.0),
    'w': (1.0, 1.0, 1.0),
}

CSS4_COLORS = {
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aqua': '#00ffff',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'black': '#000000',
    'blanchedalmond': '#ffebcd',
    'blue': '#0000ff',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgreen': '#006400',
    'darkgrey': '#a9a9a9',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'fuchsia': '#ff00ff',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'gray': '#808080',
    'green': '#008000',
    'greenyellow': '#adff2f',
    'grey': '#808080',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgray': '#d3d3d3',
    'lightgreen': '#90ee90',
    'lightgrey': '#d3d3d3',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'lime': '#00ff00',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'maroon': '#800000',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'navy': '#000080',
    'oldlace': '#fdf5e6',
    'olive': '#808000',
    'olivedrab': '#6b8e23',
    'orange': '#ffa500',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#db7093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'purple': '#800080',
    'rebeccapurple': '#663399',
    'red': '#ff0000',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'silver': '#c0c0c0',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'teal': '#008080',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'white': '#ffffff',
    'whitesmoke': '#f5f5f5',
    'yellow': '#ffff00',
    'yellowgreen': '#9acd32',
}


def _hex_to_rgba(h):
    """Convert a hex string to an RGBA float tuple."""
    h = h.lstrip('#')
    if len(h) == 3:
        r = int(h[0] * 2, 16) / 255.0
        g = int(h[1] * 2, 16) / 255.0
        b = int(h[2] * 2, 16) / 255.0
        return (r, g, b, 1.0)
    elif len(h) == 4:
        r = int(h[0] * 2, 16) / 255.0
        g = int(h[1] * 2, 16) / 255.0
        b = int(h[2] * 2, 16) / 255.0
        a = int(h[3] * 2, 16) / 255.0
        return (r, g, b, a)
    elif len(h) == 6:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    elif len(h) == 8:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        a = int(h[6:8], 16) / 255.0
        return (r, g, b, a)
    raise ValueError(f"Invalid hex color: #{h}")


def _build_colors_full_map():
    """Build a combined color lookup mapping names to RGBA float tuples."""
    mapping = {}

    # CSS4 colors (lowest priority — overridden by more specific dicts)
    for name, hexval in CSS4_COLORS.items():
        mapping[name] = _hex_to_rgba(hexval)

    # Tableau colors
    for name, hexval in TABLEAU_COLORS.items():
        mapping[name] = _hex_to_rgba(hexval)

    # Base single-char colors (highest priority for single chars)
    for name, rgb in BASE_COLORS.items():
        mapping[name] = (rgb[0], rgb[1], rgb[2], 1.0)

    # Add grey ↔ gray aliases so that every 'gray' name has a 'grey'
    # counterpart and vice versa.
    for name in list(mapping):
        if 'gray' in name:
            alt = name.replace('gray', 'grey')
            mapping.setdefault(alt, mapping[name])
        elif 'grey' in name:
            alt = name.replace('grey', 'gray')
            mapping.setdefault(alt, mapping[name])

    return mapping


_colors_full_map = _build_colors_full_map()


# ===================================================================
# Colour conversion functions
# ===================================================================

_CN_PATTERN = re.compile(r'^C(\d+)$', re.IGNORECASE)


def _check_alpha(alpha):
    """Validate alpha is in [0, 1] range."""
    if alpha is not None:
        alpha = float(alpha)
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(
                f"'alpha' must be between 0 and 1, inclusive, "
                f"but got {alpha}")
    return alpha


def to_rgba(c, alpha=None):
    """Convert colour specification *c* to an ``(r, g, b, a)`` tuple.

    All components are floats in 0-1.

    Parameters
    ----------
    c : str, tuple, or list
        A colour specification.  Accepted forms:

        - Named colour: ``'red'``, ``'tab:blue'``, ``'C0'``
        - Hex: ``'#ff0000'``, ``'#f00'``, ``'#ff000080'``
        - RGB tuple: ``(1.0, 0.0, 0.0)``
        - RGBA tuple: ``(1.0, 0.0, 0.0, 0.5)``
        - Grayscale string: ``'0.5'``
        - ``'none'`` for fully transparent

    alpha : float, optional
        Override the alpha component.

    Returns
    -------
    tuple
        ``(r, g, b, a)`` with floats in 0-1.

    Raises
    ------
    ValueError
        If *c* is not a recognised colour specification, or if *alpha*
        is outside [0, 1].
    """
    alpha = _check_alpha(alpha)

    if isinstance(c, tuple) and len(c) == 2:
        # (color, alpha) pair
        color_part, alpha_part = c
        if alpha is None:
            alpha = alpha_part
        return to_rgba(color_part, alpha=alpha)

    if isinstance(c, str):
        # 'none' → fully transparent — alpha is always 0
        if c.lower() == 'none':
            return (0.0, 0.0, 0.0, 0.0)

        # Hex
        if c.startswith('#'):
            rgba = _hex_to_rgba(c)
            if alpha is not None:
                rgba = (rgba[0], rgba[1], rgba[2], float(alpha))
            return rgba

        # CN cycle colours
        m = _CN_PATTERN.match(c)
        if m:
            idx = int(m.group(1))
            hex_color = DEFAULT_CYCLE[idx % len(DEFAULT_CYCLE)]
            rgba = _hex_to_rgba(hex_color)
            if alpha is not None:
                rgba = (rgba[0], rgba[1], rgba[2], float(alpha))
            return rgba

        # Named colour lookup
        key = c.lower()
        if key in _colors_full_map:
            rgba = _colors_full_map[key]
            if alpha is not None:
                rgba = (rgba[0], rgba[1], rgba[2], float(alpha))
            return rgba

        # Grayscale string: a float like '0.5'
        try:
            val = float(c)
            if 0.0 <= val <= 1.0:
                a = float(alpha) if alpha is not None else 1.0
                return (val, val, val, a)
        except ValueError:
            pass

        raise ValueError(f"Invalid RGBA argument: {c!r}")

    # Tuple / list of floats (or single-element list-of-list)
    if isinstance(c, (tuple, list)):
        # Handle list-of-one-list: [[r, g, b]] -> [r, g, b]
        if (len(c) == 1
                and isinstance(c[0], (tuple, list))
                and len(c[0]) in (3, 4)):
            return to_rgba(c[0], alpha=alpha)
        if len(c) == 3:
            r, g, b = [float(x) for x in c]
            a = float(alpha) if alpha is not None else 1.0
            return (r, g, b, a)
        elif len(c) == 4:
            r, g, b, a = [float(x) for x in c]
            if alpha is not None:
                a = float(alpha)
            return (r, g, b, a)
        else:
            raise ValueError(
                f"Invalid RGBA argument: {c!r} (expected 3 or 4 elements)")

    raise ValueError(f"Invalid RGBA argument: {c!r}")


def to_rgba_array(c, alpha=None):
    """Convert *c* to a list of ``(r, g, b, a)`` tuples.

    Parameters
    ----------
    c : color or list of colors
        A single colour or sequence of colour specifications.
    alpha : float or list of floats, optional
        Override alpha values.

    Returns
    -------
    list of tuple
        Each element is ``(r, g, b, a)`` with floats in 0-1.
    """
    # Handle "none" as a special case: returns empty (upstream compat)
    if isinstance(c, str) and c.lower() == 'none':
        return []

    # Handle (colors, alpha) tuple
    if isinstance(c, tuple) and len(c) == 2:
        first, second = c
        # Detect (color_str, alpha_float) — a single color with alpha
        if isinstance(first, str) and isinstance(second, (int, float)):
            _check_alpha(second)
            a = alpha if alpha is not None else second
            return [to_rgba(first, alpha=a)]
        # Detect (color_tuple, alpha_float) where color_tuple is an
        # RGB/RGBA tuple
        if (isinstance(first, (tuple, list))
                and len(first) in (3, 4)
                and isinstance(first[0], (int, float))
                and isinstance(second, (int, float))):
            _check_alpha(second)
            a = alpha if alpha is not None else second
            return [to_rgba(first, alpha=a)]
        # Detect (list_of_colors, alpha) — multiple colors with shared alpha
        if isinstance(first, (list, tuple)) and len(first) > 0:
            if not isinstance(first[0], (int, float)):
                # It's (list_of_colors, alpha)
                if alpha is None:
                    alpha = second
                c = first

    # Single colour
    if isinstance(c, str) or (isinstance(c, (tuple, list))
                               and len(c) in (3, 4)
                               and isinstance(c[0], (int, float))):
        return [to_rgba(c, alpha=alpha if not isinstance(alpha, (list, tuple)) else alpha[0])]

    # List of colours
    result = []
    colors = list(c)
    if isinstance(alpha, (list, tuple)):
        if len(alpha) != len(colors):
            raise ValueError(
                f"alpha length ({len(alpha)}) does not match "
                f"color length ({len(colors)})")
        for col, a in zip(colors, alpha):
            result.append(to_rgba(col, alpha=a))
    else:
        for col in colors:
            result.append(to_rgba(col, alpha=alpha))
    return result


def to_hex(color, keep_alpha=False):
    """Convert a colour specification to ``#rrggbb`` or ``#rrggbbaa`` hex.

    Parameters
    ----------
    color : color
        Any recognised colour specification.
    keep_alpha : bool, default False
        If True and the colour has alpha != 1, append the alpha hex digits.

    Returns
    -------
    str
        Hex string like ``'#1f77b4'`` or ``'#1f77b480'``.
    """
    r, g, b, a = to_rgba(color)
    ri, gi, bi = int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
    if keep_alpha and a < 1.0:
        ai = int(round(a * 255))
        return f'#{ri:02x}{gi:02x}{bi:02x}{ai:02x}'
    return f'#{ri:02x}{gi:02x}{bi:02x}'


def to_rgb(color):
    """Convert a colour specification to an ``(r, g, b)`` float tuple.

    All components are floats in 0-1.

    Parameters
    ----------
    color : color
        Any recognised colour specification.

    Returns
    -------
    tuple
        ``(r, g, b)`` with floats in 0-1.
    """
    r, g, b, _a = to_rgba(color)
    return (r, g, b)


def is_color_like(c):
    """Return True if *c* can be interpreted as a colour.

    Parameters
    ----------
    c : object
        Candidate colour value.

    Returns
    -------
    bool
    """
    try:
        to_rgba(c)
        return True
    except (ValueError, TypeError):
        return False


def same_color(c1, c2):
    """Return True if *c1* and *c2* represent the same colour.

    Both arguments may be single colours or lists of colours.
    If both are lists, they must have the same length, and comparison
    is element-wise.

    Parameters
    ----------
    c1, c2 : color or list of colors
        Colour specifications to compare.

    Returns
    -------
    bool

    Raises
    ------
    ValueError
        If both are lists of different lengths.
    """
    # Check if either is a list of colours (not a single RGB/RGBA tuple)
    c1_is_seq = _is_color_sequence(c1)
    c2_is_seq = _is_color_sequence(c2)

    if c1_is_seq and c2_is_seq:
        list1 = list(c1)
        list2 = list(c2)
        if len(list1) != len(list2):
            raise ValueError(
                f"Color lists have different lengths: "
                f"{len(list1)} vs {len(list2)}")
        return all(same_color(a, b) for a, b in zip(list1, list2))

    if c1_is_seq or c2_is_seq:
        raise ValueError(
            "Cannot compare a color sequence to a single color. "
            "Use lists of the same length on both sides.")

    return to_rgba(c1) == to_rgba(c2)


def _is_color_sequence(c):
    """Return True if *c* is a sequence of colours (not a single colour)."""
    if isinstance(c, str):
        return False
    if isinstance(c, (tuple, list)):
        if len(c) == 0:
            return True
        # If the first element is a number, it's likely an RGB/RGBA tuple
        if isinstance(c[0], (int, float)):
            return False
        # If the first element is a string or tuple, it's a list of colours
        return True
    return False


def _has_alpha_channel(c):
    """Return True if colour *c* includes explicit alpha information.

    Parameters
    ----------
    c : color
        A colour specification.

    Returns
    -------
    bool
    """
    if isinstance(c, str):
        if c.startswith('#'):
            h = c.lstrip('#')
            return len(h) in (4, 8)
        return False
    if isinstance(c, (tuple, list)):
        if len(c) == 2 and not isinstance(c[0], (int, float)):
            # (color, alpha) form — but only if alpha is not None
            # and the inner color actually has 4 elements
            color_part, alpha_part = c
            if alpha_part is not None:
                return True
            # (color, None): check if inner color itself has alpha
            if isinstance(color_part, (tuple, list)):
                return len(color_part) == 4
            return False
        return len(c) == 4
    return False


# ===================================================================
# Format-string parsing
# ===================================================================

_COLOR_CHARS = set('bgrcmykw')

_MARKER_CHARS = {
    'o': 'circle',
    's': 'square',
    '^': 'triangle_up',
    'v': 'triangle_down',
    '<': 'triangle_left',
    '>': 'triangle_right',
    '1': 'tri_down',
    '2': 'tri_up',
    '3': 'tri_left',
    '4': 'tri_right',
    '+': 'plus',
    'x': 'x',
    'd': 'thin_diamond',
    'D': 'diamond',
    '|': 'vline',
    '_': 'hline',
    'p': 'pentagon',
    'h': 'hexagon1',
    'H': 'hexagon2',
    '*': 'star',
    '.': 'point',
}

_LINE_CHARS = {
    '-': 'solid',
    '--': 'dashed',
    ':': 'dotted',
    '-.': 'dashdot',
}


def parse_fmt(fmt):
    """Parse a matplotlib format string, return ``(color, marker, linestyle)``.

    Parameters
    ----------
    fmt : str
        A format string like ``'ro-'``, ``'b--'``, ``'g^:'``.

    Returns
    -------
    tuple
        ``(color, marker, linestyle)`` — each is a string or None.
    """
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
            linestyle = fmt[i:i + 2]
            i += 1
        elif ch in ('-', ':', '.'):
            if linestyle is None:
                linestyle = ch
        i += 1
    return color, marker, linestyle


# ===================================================================
# Normalization classes
# ===================================================================

class _CallbackRegistry:
    """Simple callback registry for normalization callbacks."""

    def __init__(self):
        self._callbacks = {}
        self._next_cid = 0

    def connect(self, signal, func):
        """Connect *func* to *signal*, return a connection id."""
        cid = self._next_cid
        self._next_cid += 1
        self._callbacks[cid] = (signal, func)
        return cid

    def disconnect(self, cid):
        """Disconnect the callback with id *cid*."""
        self._callbacks.pop(cid, None)

    def process(self, signal):
        """Call all callbacks registered for *signal*."""
        for _cid, (sig, func) in list(self._callbacks.items()):
            if sig == signal:
                func()


class Normalize:
    """Linearly normalize data to the [0, 1] interval.

    Parameters
    ----------
    vmin : float
        Data value that maps to 0.
    vmax : float
        Data value that maps to 1.
    clip : bool, default False
        If True, values outside [vmin, vmax] are clipped to [0, 1].
    """

    def __init__(self, vmin=None, vmax=None, clip=False):
        self.vmin = vmin
        self.vmax = vmax
        self.clip = clip
        self.callbacks = _CallbackRegistry()

    def __call__(self, value, clip=None):
        """Normalize *value* to [0, 1].

        Parameters
        ----------
        value : float or list of float
            Data value(s) to normalize.
        clip : bool, optional
            Override instance clip setting.

        Returns
        -------
        float or list of float
            Normalised value(s).
        """
        if clip is None:
            clip = self.clip
        if self.vmin is None or self.vmax is None:
            raise ValueError("Normalize requires vmin and vmax to be set")
        vmin, vmax = float(self.vmin), float(self.vmax)

        if isinstance(value, (list, tuple)):
            return [self._normalize_scalar(v, vmin, vmax, clip) for v in value]
        return self._normalize_scalar(value, vmin, vmax, clip)

    def _normalize_scalar(self, value, vmin, vmax, clip):
        if vmax == vmin:
            return 0.0
        result = (float(value) - vmin) / (vmax - vmin)
        if clip:
            result = max(0.0, min(1.0, result))
        return result

    def inverse(self, value):
        """Map normalised *value* back to data space.

        Parameters
        ----------
        value : float or list of float

        Returns
        -------
        float or list of float
        """
        if self.vmin is None or self.vmax is None:
            raise ValueError("Normalize requires vmin and vmax to be set")
        vmin, vmax = float(self.vmin), float(self.vmax)
        if isinstance(value, (list, tuple)):
            return [vmin + float(v) * (vmax - vmin) for v in value]
        return vmin + float(value) * (vmax - vmin)

    def autoscale(self, data):
        """Set *vmin* and *vmax* from *data*.

        Parameters
        ----------
        data : iterable of float
        """
        data = [float(v) for v in data]
        self.vmin = min(data)
        self.vmax = max(data)


class LogNorm(Normalize):
    """Logarithmic normalization to [0, 1].

    Parameters
    ----------
    vmin : float
        Minimum data value (must be > 0).
    vmax : float
        Maximum data value (must be > vmin).
    clip : bool, default False
        If True, clip values outside [vmin, vmax].

    Raises
    ------
    ValueError
        If *vmin* <= 0 or *vmin* >= *vmax*.
    """

    def __call__(self, value, clip=None):
        if clip is None:
            clip = self.clip
        if self.vmin is None or self.vmax is None:
            raise ValueError("LogNorm requires vmin and vmax to be set")
        vmin, vmax = float(self.vmin), float(self.vmax)
        if vmin <= 0:
            raise ValueError(
                f"LogNorm requires vmin > 0, got vmin={vmin}")
        if vmin >= vmax:
            raise ValueError(
                f"LogNorm requires vmin < vmax, got vmin={vmin}, vmax={vmax}")

        if isinstance(value, (list, tuple)):
            return [self._log_normalize(v, vmin, vmax, clip) for v in value]
        return self._log_normalize(value, vmin, vmax, clip)

    def _log_normalize(self, value, vmin, vmax, clip):
        value = float(value)
        if clip:
            value = max(vmin, min(vmax, value))
        if value <= 0:
            return 0.0
        result = (math.log10(value) - math.log10(vmin)) / \
                 (math.log10(vmax) - math.log10(vmin))
        if clip:
            result = max(0.0, min(1.0, result))
        return result

    def inverse(self, value):
        if self.vmin is None or self.vmax is None:
            raise ValueError("LogNorm requires vmin and vmax to be set")
        vmin, vmax = float(self.vmin), float(self.vmax)
        if vmin <= 0:
            raise ValueError(
                f"LogNorm requires vmin > 0, got vmin={vmin}")
        if vmin >= vmax:
            raise ValueError(
                f"LogNorm requires vmin < vmax, got vmin={vmin}, vmax={vmax}")
        log_vmin = math.log10(vmin)
        log_vmax = math.log10(vmax)
        if isinstance(value, (list, tuple)):
            return [10.0 ** (log_vmin + float(v) * (log_vmax - log_vmin))
                    for v in value]
        return 10.0 ** (log_vmin + float(value) * (log_vmax - log_vmin))


# ---------------------------------------------------------------------------
# Colormap class hierarchy
# Adapted from upstream matplotlib/colors.py (matplotlib 3.9.x)
# Masked array usage replaced with NaN-based approach for RustPython compat.
# Copyright (c) 2012- Matplotlib Development Team
# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
# ---------------------------------------------------------------------------
import numpy as np


def _interp(x_new, xp, fp):
    """Pure-Python piecewise-linear interpolation (replacement for np.interp)."""
    xp_list = xp.tolist() if hasattr(xp, 'tolist') else list(xp)
    fp_list = fp.tolist() if hasattr(fp, 'tolist') else list(fp)
    x_list = x_new.tolist() if hasattr(x_new, 'tolist') else list(x_new)
    result = []
    n = len(xp_list)
    for x in x_list:
        if x <= xp_list[0]:
            result.append(fp_list[0])
        elif x >= xp_list[-1]:
            result.append(fp_list[-1])
        else:
            # Binary search
            lo, hi = 0, n - 1
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if xp_list[mid] <= x:
                    lo = mid
                else:
                    hi = mid
            t = (x - xp_list[lo]) / (xp_list[hi] - xp_list[lo])
            result.append(fp_list[lo] + t * (fp_list[hi] - fp_list[lo]))
    return np.array(result, dtype=float)


class Colormap:
    """Base class for all colormaps."""

    def __init__(self, name, N=256):
        self.name = name
        self.N = int(N)
        self._rgba_bad = (0.0, 0.0, 0.0, 0.0)  # transparent black
        self._rgba_under = None
        self._rgba_over = None

    def __call__(self, X, alpha=None, bytes=False):
        """Map scalar or array X in [0, 1] to RGBA.

        Parameters
        ----------
        X : scalar or array-like
            Values in [0, 1]. NaN values map to the "bad" color.
        alpha : float, optional
            Alpha multiplier applied after LUT lookup.
        bytes : bool
            If True, return uint8 values in [0, 255].

        Returns
        -------
        tuple (4,) for scalar input; ndarray (…, 4) for array input.
        """
        if not hasattr(self, '_lut'):
            self._init()

        scalar_input = not hasattr(X, '__len__') and not hasattr(X, 'shape')
        if scalar_input:
            X = np.array([float(X)], dtype=float)
        else:
            X = np.asarray(X, dtype=float)

        orig_shape = X.shape
        X = X.flatten()

        bad_mask = np.isnan(X)
        under_mask = X < 0.0
        over_mask = X > 1.0

        # Clip to valid LUT range
        Xc = np.clip(X, 0.0, 1.0)

        # Map to LUT indices
        idx = (Xc * (self.N - 1) + 0.5).astype('int64')
        idx = np.clip(idx, 0, self.N - 1)

        # Index into LUT
        result = np.zeros((len(X), 4), dtype=float)
        idx_list = idx.tolist()
        for i, j in enumerate(idx_list):
            result[i] = self._lut[int(j)]

        # Apply special colors
        bad_list = bad_mask.tolist()
        under_list = under_mask.tolist()
        over_list = over_mask.tolist()

        bad_color = list(self._rgba_bad)
        under_color = self._lut[0].tolist() if self._rgba_under is None else list(self._rgba_under)
        over_color = self._lut[self.N - 1].tolist() if self._rgba_over is None else list(self._rgba_over)

        for i in range(len(X)):
            if bad_list[i]:
                result[i] = bad_color
            elif under_list[i]:
                result[i] = under_color
            elif over_list[i]:
                result[i] = over_color

        # Apply alpha multiplier
        if alpha is not None:
            result[:, 3] = result[:, 3] * float(alpha)

        # Clip final result to [0, 1]
        result = np.clip(result, 0.0, 1.0)

        # Reshape to original shape + (4,)
        if len(orig_shape) > 1:
            result = result.reshape(orig_shape + (4,))
        elif len(orig_shape) == 0:
            result = result.reshape((4,))
        # else: already (N, 4)

        if bytes:
            result_bytes = (result * 255 + 0.5).astype('int32')
            if scalar_input:
                return tuple(result_bytes[0].tolist())
            return result_bytes

        if scalar_input:
            return tuple(result[0].tolist())
        return result

    def reversed(self, name=None):
        """Return a reversed copy of this colormap."""
        raise NotImplementedError(f"{type(self).__name__} does not support reversed()")

    def set_bad(self, color='k', alpha=None):
        """Set the color for masked/NaN values."""
        self._rgba_bad = list(to_rgba(color, alpha=alpha))

    def set_under(self, color='k', alpha=None):
        """Set the color for out-of-range low values."""
        self._rgba_under = list(to_rgba(color, alpha=alpha))

    def set_over(self, color='k', alpha=None):
        """Set the color for out-of-range high values."""
        self._rgba_over = list(to_rgba(color, alpha=alpha))

    def is_gray(self):
        """Return True if the colormap is grayscale."""
        if not hasattr(self, '_lut'):
            self._init()
        lut_list = self._lut[:self.N].tolist()
        return all(
            abs(row[0] - row[1]) < 1e-9 and abs(row[0] - row[2]) < 1e-9
            for row in lut_list
        )

    def __repr__(self):
        return f"<{type(self).__name__} '{self.name}'>"

    def __eq__(self, other):
        if not isinstance(other, Colormap):
            return False
        return self.name == other.name

    def __copy__(self):
        cls = type(self)
        new = cls.__new__(cls)
        new.__dict__.update(self.__dict__.copy())
        if hasattr(self, '_lut'):
            new._lut = self._lut.copy()
        return new


class LinearSegmentedColormap(Colormap):
    """Colormap defined by piecewise-linear segment data.

    segmentdata : dict with keys 'red', 'green', 'blue' (and optionally 'alpha').
    Each value is either:
      - a list of (x, y0, y1) triples, or
      - a callable f(x) -> values in [0, 1].
    """

    def __init__(self, name, segmentdata, N=256, gamma=1.0):
        super().__init__(name, N)
        self._segmentdata = segmentdata
        self._gamma = float(gamma)

    def _init(self):
        """Build the LUT array from segmentdata. Called lazily on first use."""
        x = np.linspace(0.0, 1.0, self.N)
        self._lut = np.zeros((self.N, 4), dtype=float)

        for ch_idx, channel in enumerate(('red', 'green', 'blue')):
            seg = self._segmentdata[channel]
            if callable(seg):
                vals = seg(x)
                self._lut[:, ch_idx] = np.asarray(vals, dtype=float)
            else:
                # seg is a list of (x_i, y0_i, y1_i)
                xs = np.array([pt[0] for pt in seg], dtype=float)
                # Use y1 (right-hand side) for interpolation
                ys = np.array([pt[2] for pt in seg], dtype=float)
                self._lut[:, ch_idx] = _interp(x, xs, ys)

        # Alpha channel
        if 'alpha' in self._segmentdata:
            seg = self._segmentdata['alpha']
            if callable(seg):
                self._lut[:, 3] = np.asarray(seg(x), dtype=float)
            else:
                xs = np.array([pt[0] for pt in seg], dtype=float)
                ys = np.array([pt[2] for pt in seg], dtype=float)
                self._lut[:, 3] = _interp(x, xs, ys)
        else:
            self._lut[:, 3] = 1.0

        # Apply gamma
        if self._gamma != 1.0:
            self._lut[:, :3] = self._lut[:, :3] ** self._gamma

        self._lut = np.clip(self._lut, 0.0, 1.0)

    def set_gamma(self, gamma):
        """Recompute LUT with a new gamma."""
        self._gamma = float(gamma)
        if hasattr(self, '_lut'):
            del self._lut

    @classmethod
    def from_list(cls, name, colors, N=256):
        """Create a LinearSegmentedColormap from a list of colors.

        Parameters
        ----------
        name : str
        colors : list of color specs, or list of (value, color) pairs
        N : int, number of LUT entries
        """
        if len(colors) == 0:
            raise ValueError("colors must not be empty")

        # Normalize: accept plain list or list of (val, color)
        if isinstance(colors[0], (list, tuple)) and len(colors[0]) == 2 and not isinstance(colors[0][0], str):
            # List of (val, color)
            vals = [float(c[0]) for c in colors]
            cols = [c[1] for c in colors]
        else:
            # Plain list of colors — evenly spaced
            n = len(colors)
            vals = [i / (n - 1) for i in range(n)] if n > 1 else [0.0]
            cols = colors

        rgba = [to_rgba(c) for c in cols]

        # Build segmentdata
        r_seg = [(vals[i], rgba[i][0], rgba[i][0]) for i in range(len(vals))]
        g_seg = [(vals[i], rgba[i][1], rgba[i][1]) for i in range(len(vals))]
        b_seg = [(vals[i], rgba[i][2], rgba[i][2]) for i in range(len(vals))]
        a_seg = [(vals[i], rgba[i][3], rgba[i][3]) for i in range(len(vals))]

        segmentdata = {'red': r_seg, 'green': g_seg, 'blue': b_seg, 'alpha': a_seg}
        return cls(name, segmentdata, N=N)

    def reversed(self, name=None):
        if name is None:
            name = self.name + '_r'
        # Reverse segmentdata by flipping x coordinates: x -> 1-x, swap y0/y1
        new_sd = {}
        for channel, seg in self._segmentdata.items():
            if callable(seg):
                orig = seg
                new_sd[channel] = lambda x, f=orig: f(1.0 - x)
            else:
                new_seg = [(1.0 - pt[0], pt[2], pt[1]) for pt in reversed(seg)]
                new_sd[channel] = new_seg
        cmap = LinearSegmentedColormap(name, new_sd, N=self.N, gamma=self._gamma)
        return cmap


class ListedColormap(Colormap):
    """Colormap defined by a fixed list of colors.

    Parameters
    ----------
    colors : list of color specs
    name : str
    N : int or None — if None, defaults to len(colors)
    """

    def __init__(self, colors, name='from_list', N=None):
        if N is None:
            N = len(colors)
        super().__init__(name, N)
        self.colors = colors

    def _init(self):
        """Build LUT from the colors list."""
        rgba = to_rgba_array(self.colors)
        # Resample to N entries if needed
        # to_rgba_array may return a list or ndarray
        if hasattr(rgba, 'tolist'):
            rgba_list = rgba.tolist()
        else:
            rgba_list = [list(row) for row in rgba]
        n_src = len(rgba_list)
        if n_src != self.N:
            # Nearest-neighbor resample
            lut_list = []
            for i in range(self.N):
                src_idx = int(i * n_src / self.N)
                src_idx = min(src_idx, n_src - 1)
                lut_list.append(rgba_list[src_idx])
            self._lut = np.array(lut_list, dtype=float)
        else:
            self._lut = np.array(rgba_list, dtype=float)

    def reversed(self, name=None):
        if name is None:
            name = self.name + '_r'
        colors = self.colors[::-1] if isinstance(self.colors, list) else list(reversed(self.colors))
        return ListedColormap(colors, name=name, N=self.N)
