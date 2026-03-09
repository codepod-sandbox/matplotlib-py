"""
matplotlib.axes --- Axes class that stores plot elements.
"""

import math

from matplotlib.colors import DEFAULT_CYCLE, to_hex, parse_fmt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.collections import PathCollection
from matplotlib.container import BarContainer, ErrorbarContainer
from matplotlib.text import Text, Annotation


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

        # Typed artist lists
        self.lines = []
        self.collections = []
        self.patches = []
        self.containers = []
        self.texts = []

        # Axis state
        self._x_inverted = False
        self._y_inverted = False
        self._xscale = 'linear'
        self._yscale = 'linear'
        self._aspect = 'auto'

        # Shared axes
        self._shared_x = []  # list of axes sharing x-limits
        self._shared_y = []  # list of axes sharing y-limits

        # Tick/label visibility (for label_outer)
        self._xticklabels_visible = True
        self._yticklabels_visible = True
        self._xlabel_visible = True
        self._ylabel_visible = True

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

        # Create Line2D artist
        line = Line2D(
            x, y,
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
            marker=marker if marker is not None else 'None',
            label=label,
        )
        line.axes = self
        line.figure = self.figure

        # Store in typed list
        self.lines.append(line)

        # Backend compatibility: append dict to _elements
        self._elements.append(line._as_element())

        return [line]

    def scatter(self, x, y, s=20, c=None, **kwargs):
        """Scatter plot."""
        color = c or kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')

        x_list = list(x)
        y_list = list(y)
        offsets = list(zip(x_list, y_list))

        # Validate sizes
        if isinstance(s, str):
            raise ValueError("'s' must be a float or array-like of float, "
                             "not a string")
        if hasattr(s, '__iter__'):
            sizes = list(s)
            if len(sizes) != len(x_list):
                raise ValueError("s must be the same size as x and y")
        else:
            sizes = [s]

        # Create PathCollection
        pc = PathCollection(
            offsets=offsets,
            sizes=sizes,
            facecolors=[color],
            label=label,
        )
        pc.axes = self
        pc.figure = self.figure

        # Store in typed list
        self.collections.append(pc)

        # Backend compatibility
        self._elements.append(pc._as_element())

        return pc

    def bar(self, x, height, width=0.8, **kwargs):
        """Bar chart."""
        # Color handling: facecolor takes precedence over color
        facecolor = kwargs.get('facecolor')
        edgecolor = kwargs.get('edgecolor')
        color = kwargs.get('color')
        alpha = kwargs.get('alpha')
        label = kwargs.get('label')
        bottom = kwargs.get('bottom', 0)

        if facecolor is None:
            if color is not None:
                facecolor = color
            else:
                facecolor = self._next_color()

        # Convert facecolor to hex for backend (handle 'none')
        if isinstance(facecolor, str) and facecolor.lower() == 'none':
            fc_hex = '#000000'  # transparent will be handled by alpha
        else:
            fc_hex = to_hex(facecolor)

        if edgecolor is None:
            edgecolor = 'black'

        # Convert x and height to lists (broadcast scalar height)
        if isinstance(x, (str, int, float)):
            x_vals = [x]
        else:
            x_vals = list(x)
        if not hasattr(height, '__iter__'):
            h_vals = [height] * len(x_vals)
        else:
            h_vals = list(height)

        # Handle label: list vs scalar
        if isinstance(label, list):
            if len(label) != len(x_vals):
                raise ValueError(
                    f"'label' must have the same length as 'x' "
                    f"({len(label)} != {len(x_vals)})")
            bar_labels = label
            container_label = '_nolegend_'
        else:
            bar_labels = ['_nolegend_'] * len(x_vals)
            container_label = label

        # Handle bottom as list or scalar
        if hasattr(bottom, '__iter__'):
            b_vals = list(bottom)
        else:
            b_vals = [bottom] * len(x_vals)

        # Map string x values to numeric positions
        if x_vals and isinstance(x_vals[0], str):
            x_numeric = list(range(len(x_vals)))
        else:
            x_numeric = x_vals

        # Create Rectangle patches for each bar
        rect_patches = []
        for i in range(len(x_vals)):
            x_center = x_numeric[i]
            h = h_vals[i]
            b = b_vals[i]
            rect = Rectangle(
                (x_center - width / 2, b),
                width,
                h,
                facecolor=facecolor,
                edgecolor=edgecolor,
            )
            if alpha is not None:
                rect.set_alpha(alpha)
            rect.set_label(bar_labels[i])
            rect.axes = self
            rect.figure = self.figure
            self.patches.append(rect)
            rect_patches.append(rect)

        # Create BarContainer
        bc = BarContainer(rect_patches, label=container_label)
        self.containers.append(bc)

        # Backend compatibility: append a single bar element dict
        elem = {
            'type': 'bar',
            'x': x_vals, 'height': h_vals, 'width': width,
            'color': fc_hex, 'label': label,
        }
        self._elements.append(elem)

        return bc

    def hist(self, x, bins=10, **kwargs):
        """Histogram --- compute bins, store as bar chart."""
        label = kwargs.get('label')

        # Check for list-of-lists (multiple datasets)
        if hasattr(x, '__iter__') and not isinstance(x, str):
            x_check = list(x)
            if x_check and hasattr(x_check[0], '__iter__') and not isinstance(x_check[0], str):
                # Multiple datasets
                results = []
                for dataset in x_check:
                    results.append(self.hist(dataset, bins, **kwargs))
                counts_list = [r[0] for r in results]
                edges = results[0][1] if results else list(range(bins + 1))
                bc = results[0][2] if results else BarContainer([], label=label)
                return counts_list, edges, bc

        data = list(x)

        # Handle empty data
        if not data:
            color = kwargs.get('color') or self._next_color()
            color = to_hex(color)
            counts = [0] * bins
            edges = list(range(bins + 1))
            bc = BarContainer([], label=label)
            self.containers.append(bc)
            return counts, edges, bc

        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        density = kwargs.get('density', False)

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

        # Normalize to probability density if requested
        if density:
            n = len(data)
            counts = [c / (n * bin_width) for c in counts]

        centers = [(edges[i] + edges[i + 1]) / 2 for i in range(bins)]

        # Create Rectangle patches
        bar_width = bin_width * 0.9
        rect_patches = []
        for i in range(bins):
            rect = Rectangle(
                (centers[i] - bar_width / 2, 0),
                bar_width,
                counts[i],
                facecolor=color,
                edgecolor='black',
            )
            rect.axes = self
            rect.figure = self.figure
            self.patches.append(rect)
            rect_patches.append(rect)

        bc = BarContainer(rect_patches, label=label)
        self.containers.append(bc)

        # Backend compatibility
        elem = {
            'type': 'bar',
            'x': centers, 'height': counts, 'width': bar_width,
            'color': color, 'label': label,
        }
        self._elements.append(elem)

        return counts, edges, bc

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
        fmt = kwargs.get('fmt', '')

        x_list = list(x)
        y_list = list(y)

        # Create the data line (suppressed when fmt='none' or 'None')
        if fmt.lower() == 'none':
            data_line = None
        else:
            data_line = Line2D(x_list, y_list, color=color, label=label)
            data_line.axes = self
            data_line.figure = self.figure
            self.lines.append(data_line)

        # Create ErrorbarContainer
        has_yerr = yerr is not None
        has_xerr = xerr is not None
        ec = ErrorbarContainer(
            (data_line, [], []),
            has_xerr=has_xerr,
            has_yerr=has_yerr,
            label=label,
        )
        self.containers.append(ec)

        # Backend compatibility
        elem = {
            'type': 'errorbar',
            'x': x_list, 'y': y_list,
            'yerr': list(yerr) if yerr is not None and hasattr(yerr, '__iter__') else yerr,
            'xerr': list(xerr) if xerr is not None and hasattr(xerr, '__iter__') else xerr,
            'color': color, 'label': label,
            'fmt': fmt,
        }
        self._elements.append(elem)

        return ec

    def fill_between(self, x, y1, y2=0, **kwargs):
        """Fill between two curves."""
        # Validate 2D inputs
        _validate_1d(x, 'x')
        _validate_1d(y1, 'y1')
        if hasattr(y2, '__iter__'):
            _validate_1d(y2, 'y2')

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

    def fill_betweenx(self, y, x1, x2=0, **kwargs):
        """Fill between two curves in the x-direction."""
        # Validate 2D inputs
        _validate_1d(y, 'y')
        _validate_1d(x1, 'x1')
        if hasattr(x2, '__iter__'):
            _validate_1d(x2, 'x2')

        color = kwargs.get('color') or self._next_color()
        color = to_hex(color)
        label = kwargs.get('label')
        alpha = kwargs.get('alpha', 0.5)
        x2_list = list(x2) if hasattr(x2, '__iter__') else [x2] * len(list(y))
        elem = {
            'type': 'fill_betweenx',
            'y': list(y), 'x1': list(x1), 'x2': x2_list,
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

        # Create a Line2D (with sentinel x-data for axhline)
        line = Line2D(
            [0], [y],
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
            label=label,
        )
        line.axes = self
        line.figure = self.figure
        self.lines.append(line)

        # Backend compatibility
        elem = {
            'type': 'axhline',
            'x': [], 'y': [y], 'color': color,
            'linestyle': linestyle, 'linewidth': linewidth,
            'label': label,
        }
        self._elements.append(elem)

        return line

    def axvline(self, x=0, **kwargs):
        """Add a vertical line across the axes."""
        color = kwargs.get('color') or kwargs.get('c', 'black')
        color = to_hex(color)
        linestyle = kwargs.get('linestyle', kwargs.get('ls', '-'))
        linewidth = kwargs.get('linewidth', kwargs.get('lw', 1.0))
        label = kwargs.get('label')

        # Create a Line2D (with sentinel y-data for axvline)
        line = Line2D(
            [x], [0],
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
            label=label,
        )
        line.axes = self
        line.figure = self.figure
        self.lines.append(line)

        # Backend compatibility
        elem = {
            'type': 'axvline',
            'x': [x], 'y': [], 'color': color,
            'linestyle': linestyle, 'linewidth': linewidth,
            'label': label,
        }
        self._elements.append(elem)

        return line

    def text(self, x, y, s, **kwargs):
        """Add text to the axes."""
        t = Text(x, y, str(s), **kwargs)
        t.axes = self
        t.figure = self.figure
        self.texts.append(t)

        # Backend compatibility (use list values so _data_range extend works)
        elem = {
            'type': 'text',
            'x': [x], 'y': [y], 's': str(s),
        }
        elem.update(kwargs)
        self._elements.append(elem)

        return t

    def annotate(self, text, xy, xytext=None, arrowprops=None, **kwargs):
        """Add an annotation to the axes."""
        ann = Annotation(text, xy, xytext=xytext, arrowprops=arrowprops,
                         **kwargs)
        ann.axes = self
        ann.figure = self.figure
        self.texts.append(ann)

        # Backend compatibility (use list values so _data_range extend works)
        elem = {
            'type': 'text',
            'x': [ann.xytext[0]], 'y': [ann.xytext[1]], 's': str(text),
        }
        self._elements.append(elem)

        return ann

    # ------------------------------------------------------------------
    # Artist management
    # ------------------------------------------------------------------

    def _remove_artist(self, artist):
        """Remove an artist from this axes' typed lists."""
        if artist in self.lines:
            self.lines.remove(artist)
        elif artist in self.collections:
            self.collections.remove(artist)
        elif artist in self.patches:
            self.patches.remove(artist)
        elif artist in self.texts:
            self.texts.remove(artist)
        artist.axes = None
        artist.figure = None

    def get_legend_handles_labels(self):
        """Return (handles, labels) for all artists with non-underscore labels."""
        handles = []
        labels = []

        # Collect from all artist lists
        all_artists = (
            list(self.lines) +
            list(self.collections) +
            list(self.containers) +
            list(self.patches)
        )

        seen_labels = set()
        for artist in all_artists:
            lbl = artist.get_label() if hasattr(artist, 'get_label') else ''
            if lbl and not lbl.startswith('_') and lbl not in seen_labels:
                handles.append(artist)
                labels.append(lbl)
                seen_labels.add(lbl)

        return handles, labels

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

    def set_xlim(self, left=None, right=None, _propagating=False):
        # Validate: reject NaN or Inf
        for val, name in [(left, 'left'), (right, 'right')]:
            if val is not None:
                if math.isnan(val):
                    raise ValueError(
                        f"Axis limits cannot be NaN: {name}={val}")
                if math.isinf(val):
                    raise ValueError(
                        f"Axis limits cannot be Inf: {name}={val}")
        self._xlim = (left, right)
        # Propagate to shared axes
        if not _propagating:
            for other in self._shared_x:
                if other is not self:
                    other.set_xlim(left, right, _propagating=True)

    def get_xlim(self):
        if self._xlim is not None and self._xlim[0] is not None and self._xlim[1] is not None:
            lo, hi = self._xlim
            if self._x_inverted:
                return (hi, lo)
            return (lo, hi)
        # Auto-calculate from data
        lo, hi = self._auto_xlim()
        if self._x_inverted:
            return (hi, lo)
        return (lo, hi)

    def set_ylim(self, bottom=None, top=None, _propagating=False):
        for val, name in [(bottom, 'bottom'), (top, 'top')]:
            if val is not None:
                if math.isnan(val):
                    raise ValueError(
                        f"Axis limits cannot be NaN: {name}={val}")
                if math.isinf(val):
                    raise ValueError(
                        f"Axis limits cannot be Inf: {name}={val}")
        self._ylim = (bottom, top)
        if not _propagating:
            for other in self._shared_y:
                if other is not self:
                    other.set_ylim(bottom, top, _propagating=True)

    def get_ylim(self):
        if self._ylim is not None and self._ylim[0] is not None and self._ylim[1] is not None:
            lo, hi = self._ylim
            if self._y_inverted:
                return (hi, lo)
            return (lo, hi)
        # Auto-calculate from data
        lo, hi = self._auto_ylim()
        if self._y_inverted:
            return (hi, lo)
        return (lo, hi)

    def _auto_xlim(self):
        """Auto-calculate x limits from data in lines and collections."""
        xs = []
        for line in self.lines:
            xs.extend(line.get_xdata())
        for coll in self.collections:
            for pt in coll.get_offsets():
                xs.append(pt[0])
        # Also check _elements for backward compat data
        if not xs:
            for e in self._elements:
                if 'x' in e:
                    val = e['x']
                    if isinstance(val, list):
                        xs.extend(val)
        if not xs:
            return (0.0, 1.0)
        return (min(xs), max(xs))

    def _auto_ylim(self):
        """Auto-calculate y limits from data in lines and collections."""
        ys = []
        for line in self.lines:
            ys.extend(line.get_ydata())
        for coll in self.collections:
            for pt in coll.get_offsets():
                ys.append(pt[1])
        if not ys:
            for e in self._elements:
                if e.get('type') == 'bar':
                    ys.extend(e.get('height', []))
                    ys.append(0)
                elif 'y' in e:
                    val = e['y']
                    if isinstance(val, list):
                        ys.extend(val)
        if not ys:
            return (0.0, 1.0)
        return (min(ys), max(ys))

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

    def legend(self, *args, **kwargs):
        if len(args) > 2:
            raise TypeError(
                f"legend() takes at most 2 positional arguments "
                f"({len(args)} given)")
        self._legend = True

    def grid(self, visible=True, **kwargs):
        self._grid = visible

    # ------------------------------------------------------------------
    # Axis inversion
    # ------------------------------------------------------------------

    def invert_xaxis(self):
        """Invert the x-axis."""
        self._x_inverted = not self._x_inverted

    def invert_yaxis(self):
        """Invert the y-axis."""
        self._y_inverted = not self._y_inverted

    def xaxis_inverted(self):
        """Return whether the x-axis is inverted."""
        return self._x_inverted

    def yaxis_inverted(self):
        """Return whether the y-axis is inverted."""
        return self._y_inverted

    # ------------------------------------------------------------------
    # Scale
    # ------------------------------------------------------------------

    def set_xscale(self, scale):
        """Set the x-axis scale (e.g. 'linear', 'log')."""
        self._xscale = scale

    def set_yscale(self, scale):
        """Set the y-axis scale (e.g. 'linear', 'log')."""
        self._yscale = scale

    def get_xscale(self):
        """Return the x-axis scale."""
        return self._xscale

    def get_yscale(self):
        """Return the y-axis scale."""
        return self._yscale

    # ------------------------------------------------------------------
    # Aspect
    # ------------------------------------------------------------------

    def set_aspect(self, aspect):
        """Set the axes aspect ratio."""
        self._aspect = aspect

    def get_aspect(self):
        """Return the axes aspect ratio."""
        return self._aspect

    # ------------------------------------------------------------------
    # Axis utility
    # ------------------------------------------------------------------

    def axis(self, option=None):
        """Set or get axis properties.

        Parameters
        ----------
        option : str, optional
            - 'square': set equal aspect with matched limits
            - 'equal': set equal aspect
            - 'off'/'on': toggle visibility
        """
        if option is None:
            xlim = self.get_xlim()
            ylim = self.get_ylim()
            return xlim + ylim
        if option == 'square':
            self.set_aspect('equal')
            xlim = self.get_xlim()
            ylim = self.get_ylim()
            lo = min(xlim[0], ylim[0])
            hi = max(xlim[1], ylim[1])
            self.set_xlim(lo, hi)
            self.set_ylim(lo, hi)
        elif option == 'equal':
            self.set_aspect('equal')
        elif option == 'off':
            pass  # axes visibility not implemented yet
        elif option == 'on':
            pass

    # ------------------------------------------------------------------
    # Label outer
    # ------------------------------------------------------------------

    def label_outer(self):
        """Only show outer labels and tick labels for subplots.

        Hides x-axis labels/ticks if this is not a bottom-row subplot,
        and y-axis labels/ticks if this is not a left-column subplot.
        """
        pos = self._position
        # Determine grid position from (nrows, ncols, index) tuple
        if isinstance(pos, tuple) and len(pos) == 3:
            nrows, ncols, index = pos
            row = (index - 1) // ncols
            col = (index - 1) % ncols
            is_bottom = (row == nrows - 1)
            is_left = (col == 0)
        else:
            # Non-grid axes — keep all labels
            is_bottom = True
            is_left = True

        if not is_bottom:
            self._xticklabels_visible = False
            self._xlabel_visible = False

        if not is_left:
            self._yticklabels_visible = False
            self._ylabel_visible = False

    # ------------------------------------------------------------------
    # Twin axes
    # ------------------------------------------------------------------

    def twinx(self):
        """Create a twin Axes sharing the x-axis."""
        ax2 = Axes(self.figure, self._position)
        self.figure._axes.append(ax2)
        # Share x-axis
        shared = self._shared_x if self._shared_x else [self]
        shared.append(ax2)
        for a in shared:
            a._shared_x = shared
        # Copy current x-limits
        if self._xlim is not None:
            ax2._xlim = self._xlim
        return ax2

    def twiny(self):
        """Create a twin Axes sharing the y-axis."""
        ax2 = Axes(self.figure, self._position)
        self.figure._axes.append(ax2)
        # Share y-axis
        shared = self._shared_y if self._shared_y else [self]
        shared.append(ax2)
        for a in shared:
            a._shared_y = shared
        # Copy current y-limits
        if self._ylim is not None:
            ax2._ylim = self._ylim
        return ax2

    # ------------------------------------------------------------------
    # Batch setter
    # ------------------------------------------------------------------

    def set(self, **kwargs):
        """Batch property setter."""
        for k, v in kwargs.items():
            setter = getattr(self, f'set_{k}', None)
            if setter is not None:
                if isinstance(v, (tuple, list)) and k in ('xlim', 'ylim'):
                    setter(*v)
                else:
                    setter(v)

    # ------------------------------------------------------------------
    # Remove
    # ------------------------------------------------------------------

    def remove(self):
        """Remove this axes from its figure."""
        if self.figure is not None:
            self.figure.delaxes(self)

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

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
        # Clear typed artist lists
        self.lines.clear()
        self.collections.clear()
        self.patches.clear()
        self.containers.clear()
        self.texts.clear()
        # Reset axis state
        self._x_inverted = False
        self._y_inverted = False
        self._xscale = 'linear'
        self._yscale = 'linear'
        self._aspect = 'auto'
        # Note: do NOT reset _shared_x/_shared_y — shared axes persist across cla()
        self._xticklabels_visible = True
        self._yticklabels_visible = True
        self._xlabel_visible = True
        self._ylabel_visible = True


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


def _validate_1d(data, name):
    """Raise ValueError if data has ndim > 1 (is a 2D array)."""
    if hasattr(data, 'ndim'):
        if data.ndim > 1:
            raise ValueError(
                f"'{name}' must be 1D, but has ndim={data.ndim}")
    elif hasattr(data, '__iter__') and not isinstance(data, str):
        # Check if it looks like a list of lists
        data_list = list(data)
        if data_list and hasattr(data_list[0], '__iter__') and not isinstance(data_list[0], str):
            raise ValueError(
                f"'{name}' must be 1D, but appears to be 2D")
