"""
matplotlib.axes — Axes class that stores plot elements.
"""

from matplotlib.colors import DEFAULT_CYCLE, to_hex, parse_fmt


class Axes:
    """A single set of axes in a Figure."""

    def __init__(self, fig, position):
        self.figure = fig
        self._position = position
        self._elements = []
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

    def _next_color(self):
        c = DEFAULT_CYCLE[self._color_idx % len(DEFAULT_CYCLE)]
        self._color_idx += 1
        return c

    # ------------------------------------------------------------------
    # Plot types
    # ------------------------------------------------------------------

    def plot(self, *args, **kwargs):
        """Line plot.  Accepts ``plot(y)``, ``plot(x, y)``, ``plot(x, y, fmt)``."""
        x, y, fmt = _parse_plot_args(args)
        color_fmt, marker, linestyle = parse_fmt(fmt)
        color = kwargs.get('color') or kwargs.get('c')
        if color is None:
            color = color_fmt
        if color is None:
            color = self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.5))
        if linestyle is None:
            linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        elem = {
            'type': 'line',
            'x': list(x), 'y': list(y),
            'color': color, 'linewidth': linewidth,
            'linestyle': linestyle, 'marker': marker,
            'label': label,
        }
        self._elements.append(elem)
        return [elem]

    def scatter(self, x, y, s=20, c=None, **kwargs):
        """Scatter plot."""
        color = c or kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        elem = {
            'type': 'scatter',
            'x': list(x), 'y': list(y),
            's': s, 'color': color, 'label': label,
        }
        self._elements.append(elem)
        return elem

    def bar(self, x, height, width=0.8, **kwargs):
        """Bar chart."""
        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        # Convert x to list of values
        x_vals = list(x)
        h_vals = list(height)
        elem = {
            'type': 'bar',
            'x': x_vals, 'height': h_vals, 'width': width,
            'color': color, 'label': label,
        }
        self._elements.append(elem)
        return elem

    def hist(self, x, bins=10, **kwargs):
        """Histogram — compute bins, store as bar chart."""
        data = list(x)
        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')

        # Compute histogram bins
        lo = min(data)
        hi = max(data)
        if lo == hi:
            hi = lo + 1
        bin_width = (hi - lo) / bins
        edges = [lo + i * bin_width for i in range(bins + 1)]
        counts = [0] * bins
        for v in data:
            idx = int((v - lo) / bin_width)
            if idx >= bins:
                idx = bins - 1
            counts[idx] += 1

        centers = [(edges[i] + edges[i + 1]) / 2 for i in range(bins)]
        elem = {
            'type': 'bar',
            'x': centers, 'height': counts, 'width': bin_width * 0.9,
            'color': color, 'label': label,
        }
        self._elements.append(elem)
        return counts, edges, None

    def barh(self, y, width, height=0.8, **kwargs):
        """Horizontal bar chart."""
        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        y_vals = list(y)
        w_vals = list(width)
        elem = {
            'type': 'barh',
            'y': y_vals, 'width': w_vals, 'height': height,
            'color': color, 'label': label,
        }
        self._elements.append(elem)
        return elem

    def errorbar(self, x, y, yerr=None, xerr=None, **kwargs):
        """Error bar plot."""
        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        elem = {
            'type': 'errorbar',
            'x': list(x), 'y': list(y),
            'yerr': list(yerr) if yerr is not None else None,
            'xerr': list(xerr) if xerr is not None else None,
            'color': color, 'label': label,
        }
        self._elements.append(elem)
        return elem

    def fill_between(self, x, y1, y2=0, **kwargs):
        """Fill between two curves."""
        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        alpha = kwargs.get('alpha', 0.5)
        y2_list = list(y2) if hasattr(y2, '__iter__') else [y2] * len(list(x))
        elem = {
            'type': 'fill_between',
            'x': list(x), 'y1': list(y1), 'y2': y2_list,
            'color': color, 'alpha': alpha, 'label': label,
        }
        self._elements.append(elem)
        return elem

    def axhline(self, y=0, **kwargs):
        """Add a horizontal line across the axes."""
        color = kwargs.get('color') or kwargs.get('c', 'black')
        color = to_hex(color)
        linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.0))
        label = kwargs.get('label')
        elem = {
            'type': 'axhline',
            'y': y, 'color': color,
            'linestyle': linestyle, 'linewidth': linewidth,
            'label': label,
        }
        self._elements.append(elem)
        return elem

    def axvline(self, x=0, **kwargs):
        """Add a vertical line across the axes."""
        color = kwargs.get('color') or kwargs.get('c', 'black')
        color = to_hex(color)
        linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.0))
        label = kwargs.get('label')
        elem = {
            'type': 'axvline',
            'x': x, 'color': color,
            'linestyle': linestyle, 'linewidth': linewidth,
            'label': label,
        }
        self._elements.append(elem)
        return elem

    def text(self, x, y, s, **kwargs):
        """Add text to the axes."""
        elem = {
            'type': 'text',
            'x': x, 'y': y, 's': str(s),
        }
        elem.update(kwargs)
        self._elements.append(elem)
        return elem

    # ------------------------------------------------------------------
    # Labels / config
    # ------------------------------------------------------------------

    def set_title(self, s):
        self._title = s

    def get_title(self):
        return self._title

    def set_xlabel(self, s):
        self._xlabel = s

    def get_xlabel(self):
        return self._xlabel

    def set_ylabel(self, s):
        self._ylabel = s

    def get_ylabel(self):
        return self._ylabel

    def set_xlim(self, left=None, right=None):
        self._xlim = (left, right)

    def get_xlim(self):
        return self._xlim

    def set_ylim(self, bottom=None, top=None):
        self._ylim = (bottom, top)

    def get_ylim(self):
        return self._ylim

    def set_xticks(self, ticks, labels=None, **kwargs):
        self._xticks = list(ticks)
        if labels is not None:
            self._xticklabels = list(labels)

    def get_xticks(self):
        return self._xticks if self._xticks is not None else []

    def set_yticks(self, ticks, labels=None, **kwargs):
        self._yticks = list(ticks)
        if labels is not None:
            self._yticklabels = list(labels)

    def get_yticks(self):
        return self._yticks if self._yticks is not None else []

    def legend(self, **kwargs):
        self._legend = True

    def grid(self, visible=True, **kwargs):
        self._grid = visible

    def cla(self):
        """Clear the axes."""
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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_plot_args(args):
    """Parse positional args for plot(): (y,), (x, y), (x, y, fmt)."""
    fmt = ''
    if len(args) == 1:
        y = list(args[0])
        x = list(range(len(y)))
    elif len(args) >= 2:
        first, second = args[0], args[1]
        if isinstance(second, str):
            # plot(y, fmt)
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
