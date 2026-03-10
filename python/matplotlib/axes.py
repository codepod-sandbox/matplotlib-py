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
from matplotlib.backend_bases import AxesLayout
from matplotlib._svg_backend import _nice_ticks, _fmt_tick, _esc


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

        rect_patches = []
        for i in range(len(y_vals)):
            y_center = y_vals[i]
            w = w_vals[i]
            rect = Rectangle(
                (0, y_center - height / 2), w, height,
                facecolor=color, edgecolor='black',
            )
            rect.axes = self
            rect.figure = self.figure
            self.patches.append(rect)
            rect_patches.append(rect)

        bc = BarContainer(rect_patches, label=label)
        self.containers.append(bc)

        # Keep _elements for backward compat
        elem = {
            'type': 'barh',
            'y': y_vals, 'width': w_vals, 'height': height,
            'color': color, 'label': label,
        }
        self._elements.append(elem)
        return bc

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

        # Store error data on the container for rendering
        ec._yerr_data = (x_list, y_list, yerr) if yerr is not None else None
        ec._xerr_data = (x_list, y_list, xerr) if xerr is not None else None

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

        x_list = list(x)
        y1_list = list(y1)
        y2_list = list(y2) if hasattr(y2, '__iter__') else [y2] * len(x_list)

        # Build polygon: forward along y1, backward along y2
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

        # Keep _elements for backward compat (will be removed in Task 11)
        elem = {
            'type': 'fill_between',
            'x': x_list, 'y1': y1_list, 'y2': y2_list,
            'color': color, 'alpha': alpha, 'label': label,
        }
        self._elements.append(elem)
        return poly

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

        y_list = list(y)
        x1_list = list(x1)
        x2_list = list(x2) if hasattr(x2, '__iter__') else [x2] * len(y_list)

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
        line._spanning = 'horizontal'
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
        line._spanning = 'vertical'
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
        """Auto-calculate x limits from data in lines, collections, and patches."""
        xs = []
        for line in self.lines:
            spanning = getattr(line, '_spanning', None)
            if spanning == 'horizontal':
                continue  # axhline doesn't contribute to x range
            xs.extend(line.get_xdata())
        for coll in self.collections:
            for pt in coll.get_offsets():
                xs.append(pt[0])
        for patch in self.patches:
            if hasattr(patch, '_xy') and hasattr(patch, '_width'):
                # Rectangle
                xs.append(patch._xy[0])
                xs.append(patch._xy[0] + patch._width)
            elif hasattr(patch, '_xy') and isinstance(patch._xy, list):
                # Polygon
                for pt in patch._xy:
                    xs.append(pt[0])
        if not xs:
            return (0.0, 1.0)
        return (min(xs), max(xs))

    def _auto_ylim(self):
        """Auto-calculate y limits from data in lines, collections, and patches."""
        ys = []
        for line in self.lines:
            spanning = getattr(line, '_spanning', None)
            if spanning == 'vertical':
                continue  # axvline doesn't contribute to y range
            ys.extend(line.get_ydata())
        for coll in self.collections:
            for pt in coll.get_offsets():
                ys.append(pt[1])
        for patch in self.patches:
            if hasattr(patch, '_xy') and hasattr(patch, '_height'):
                # Rectangle
                ys.append(patch._xy[1])
                ys.append(patch._xy[1] + patch._height)
            elif hasattr(patch, '_xy') and isinstance(patch._xy, list):
                # Polygon
                for pt in patch._xy:
                    ys.append(pt[1])
        # Bars typically start from 0
        if ys and any(hasattr(p, '_height') for p in self.patches):
            ys.append(0)
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
    # Renderer draw path
    # ------------------------------------------------------------------

    def _compute_layout(self, fig_w_px, fig_h_px):
        ml, mr, mt, mb = 70, 20, 40, 50
        plot_x = ml
        plot_y = mt
        plot_w = fig_w_px - ml - mr
        plot_h = fig_h_px - mt - mb
        if plot_w <= 0 or plot_h <= 0:
            return None

        xmin, xmax = self.get_xlim()
        ymin, ymax = self.get_ylim()

        # Padding (same as current backends)
        dx = (xmax - xmin) or 1.0
        dy = (ymax - ymin) or 1.0
        xmin -= dx * 0.05
        xmax += dx * 0.05
        ymin -= dy * 0.05
        ymax += dy * 0.05

        return AxesLayout(plot_x, plot_y, plot_w, plot_h, xmin, xmax, ymin, ymax)

    def draw(self, renderer):
        layout = self._compute_layout(renderer.width, renderer.height)
        if layout is None:
            return

        px, py, pw, ph = layout.plot_x, layout.plot_y, layout.plot_w, layout.plot_h

        # Frame border
        renderer.draw_rect(px, py, pw, ph, '#000000', 'none')

        # Grid
        if self._grid:
            xticks = _nice_ticks(layout.xmin, layout.xmax, 8)
            yticks = _nice_ticks(layout.ymin, layout.ymax, 6)
            for t in xticks:
                tx = layout.sx(t)
                if px < tx < px + pw:
                    renderer.draw_line([tx, tx], [py, py + ph],
                                       '#dddddd', 0.5, '--')
            for t in yticks:
                ty = layout.sy(t)
                if py < ty < py + ph:
                    renderer.draw_line([px, px + pw], [ty, ty],
                                       '#dddddd', 0.5, '--')

        # Tick marks + labels
        xticks = _nice_ticks(layout.xmin, layout.xmax, 8)
        yticks = _nice_ticks(layout.ymin, layout.ymax, 6)
        for t in xticks:
            tx = layout.sx(t)
            if px <= tx <= px + pw:
                renderer.draw_line([tx, tx], [py + ph, py + ph + 5],
                                   '#000000', 1.0, '-')
                if self._xticklabels_visible:
                    renderer.draw_text(tx, py + ph + 18, _fmt_tick(t),
                                       11, '#333333', 'center')
        for t in yticks:
            ty = layout.sy(t)
            if py <= ty <= py + ph:
                renderer.draw_line([px - 5, px], [ty, ty],
                                   '#000000', 1.0, '-')
                if self._yticklabels_visible:
                    renderer.draw_text(px - 8, ty + 4, _fmt_tick(t),
                                       11, '#333333', 'right')

        # Clip for data area
        renderer.set_clip_rect(px, py, pw, ph)

        # Collect + sort all artists by zorder
        all_artists = []
        for line in self.lines:
            all_artists.append(line)
        for patch in self.patches:
            all_artists.append(patch)
        for coll in self.collections:
            all_artists.append(coll)
        for txt in self.texts:
            all_artists.append(txt)
        all_artists.sort(key=lambda a: a.get_zorder())

        for artist in all_artists:
            spanning = getattr(artist, '_spanning', None)
            if spanning:
                continue  # drawn separately below
            if hasattr(artist, 'draw') and callable(artist.draw):
                artist.draw(renderer, layout)

        # Spanning lines (axhline/axvline)
        for line in self.lines:
            if not line.get_visible():
                continue
            spanning = getattr(line, '_spanning', None)
            if spanning == 'horizontal':
                y_val = line._ydata[0]
                py_val = layout.sy(y_val)
                color = to_hex(line._color)
                renderer.draw_line([float(px), float(px + pw)], [py_val, py_val],
                                   color, float(line._linewidth), line._linestyle)
            elif spanning == 'vertical':
                x_val = line._xdata[0]
                px_val = layout.sx(x_val)
                color = to_hex(line._color)
                renderer.draw_line([px_val, px_val], [float(py), float(py + ph)],
                                   color, float(line._linewidth), line._linestyle)

        # Errorbar whiskers
        for container in self.containers:
            yerr_data = getattr(container, '_yerr_data', None)
            if yerr_data:
                x_list, y_list, yerr = yerr_data
                yerr_list = list(yerr) if hasattr(yerr, '__iter__') else [yerr] * len(x_list)
                color = '#000000'
                if hasattr(container, 'lines') and container.lines[0]:
                    color = to_hex(container.lines[0]._color)
                for i in range(len(x_list)):
                    err = yerr_list[i] if i < len(yerr_list) else yerr_list[-1]
                    cx = layout.sx(x_list[i])
                    y_lo = layout.sy(y_list[i] - err)
                    y_hi = layout.sy(y_list[i] + err)
                    renderer.draw_line([cx, cx], [y_lo, y_hi], color, 1.0, '-')
                    cap = 3
                    renderer.draw_line([cx - cap, cx + cap], [y_lo, y_lo], color, 1.0, '-')
                    renderer.draw_line([cx - cap, cx + cap], [y_hi, y_hi], color, 1.0, '-')

            xerr_data = getattr(container, '_xerr_data', None)
            if xerr_data:
                x_list, y_list, xerr = xerr_data
                xerr_list = list(xerr) if hasattr(xerr, '__iter__') else [xerr] * len(x_list)
                color = '#000000'
                if hasattr(container, 'lines') and container.lines[0]:
                    color = to_hex(container.lines[0]._color)
                for i in range(len(x_list)):
                    err = xerr_list[i] if i < len(xerr_list) else xerr_list[-1]
                    cy = layout.sy(y_list[i])
                    x_lo = layout.sx(x_list[i] - err)
                    x_hi = layout.sx(x_list[i] + err)
                    renderer.draw_line([x_lo, x_hi], [cy, cy], color, 1.0, '-')
                    cap = 3
                    renderer.draw_line([x_lo, x_lo], [cy - cap, cy + cap], color, 1.0, '-')
                    renderer.draw_line([x_hi, x_hi], [cy - cap, cy + cap], color, 1.0, '-')

        renderer.clear_clip()

        # Title
        if self._title:
            renderer.draw_text(px + pw / 2, py - 10, self._title,
                               14, '#000000', 'center')

        # Axis labels
        if self._xlabel and self._xlabel_visible:
            renderer.draw_text(px + pw / 2, renderer.height - 5,
                               self._xlabel, 12, '#333333', 'center')
        if self._ylabel and self._ylabel_visible:
            ty = py + ph / 2
            renderer.draw_text(15, ty, self._ylabel, 12, '#333333', 'center')

        # Legend
        if self._legend:
            self._draw_legend(renderer, px + pw - 10, py + 10)

    def _draw_legend(self, renderer, right_x, top_y):
        handles, labels = self.get_legend_handles_labels()
        if not labels:
            return
        lw = 120
        lh = len(labels) * 20 + 10
        lx = right_x - lw
        ly = top_y
        renderer.draw_rect(lx, ly, lw, lh, '#999999', '#ffffff')
        for i, (handle, label) in enumerate(zip(handles, labels)):
            iy = ly + 15 + i * 20
            color = '#000000'
            if hasattr(handle, 'get_color'):
                try:
                    color = to_hex(handle.get_color())
                except Exception:
                    pass
            renderer.draw_line([lx + 5, lx + 25], [iy, iy], color, 2.0, '-')
            renderer.draw_text(lx + 30, iy + 4, label, 11, '#333333', 'left')

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
