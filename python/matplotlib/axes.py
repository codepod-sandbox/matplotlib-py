"""
matplotlib.axes --- Axes class that stores plot elements.
"""

import math

from matplotlib.colors import DEFAULT_CYCLE, to_hex, parse_fmt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Polygon, Wedge
from matplotlib.collections import PathCollection
from matplotlib.container import BarContainer, ErrorbarContainer, StemContainer
from matplotlib.text import Text, Annotation
from matplotlib.backend_bases import AxesLayout
from matplotlib.axis import XAxis, YAxis
from matplotlib.ticker import FixedFormatter


class Axes:
    """A single set of axes in a Figure."""

    def __init__(self, fig, position):
        self.figure = fig
        self._position = position
        self._title = ''
        self._xlabel = ''
        self._ylabel = ''
        self._xlim = None
        self._ylim = None
        self.xaxis = XAxis()
        self.yaxis = YAxis()
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

        poly = Polygon(verts, facecolor=color, edgecolor='none')
        poly.set_alpha(alpha)
        if label:
            poly.set_label(label)
        poly.axes = self
        poly.figure = self.figure
        self.patches.append(poly)

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

        poly = Polygon(verts, facecolor=color, edgecolor='none')
        poly.set_alpha(alpha)
        if label:
            poly.set_label(label)
        poly.axes = self
        poly.figure = self.figure
        self.patches.append(poly)

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

        return line

    def step(self, x, y, where='pre', **kwargs):
        """Step plot."""
        x_list = list(x)
        y_list = list(y)
        n = len(x_list)
        if n < 2:
            return self.plot(x_list, y_list, **kwargs)

        if where == 'pre':
            xs, ys = [x_list[0]], [y_list[0]]
            for i in range(1, n):
                xs.extend([x_list[i], x_list[i]])
                ys.extend([y_list[i - 1], y_list[i]])
        elif where == 'post':
            xs, ys = [x_list[0]], [y_list[0]]
            for i in range(1, n):
                xs.extend([x_list[i - 1], x_list[i]])
                ys.extend([y_list[i], y_list[i]])
        elif where == 'mid':
            xs, ys = [x_list[0]], [y_list[0]]
            for i in range(1, n):
                mid = (x_list[i - 1] + x_list[i]) / 2
                xs.extend([mid, mid, x_list[i]])
                ys.extend([y_list[i - 1], y_list[i], y_list[i]])
        else:
            raise ValueError(
                f"'where' must be 'pre', 'post', or 'mid', not {where!r}")

        return self.plot(xs, ys, **kwargs)

    def stairs(self, values, edges=None, **kwargs):
        """Staircase plot for pre-binned data."""
        vals = list(values)
        n = len(vals)
        if edges is None:
            edg = list(range(n + 1))
        else:
            edg = list(edges)

        xs, ys = [], []
        for i in range(n):
            xs.extend([edg[i], edg[i + 1]])
            ys.extend([vals[i], vals[i]])

        color = kwargs.pop('color', None) or self._next_color()
        line = Line2D(xs, ys,
                      color=color,
                      linewidth=kwargs.pop('linewidth', kwargs.pop('lw', 1.5)),
                      linestyle=kwargs.pop('linestyle', '-'),
                      label=kwargs.pop('label', None))
        line.axes = self
        line.figure = self.figure
        self.lines.append(line)
        return line

    def stackplot(self, x, *args, labels=None, colors=None, **kwargs):
        """Stacked area plot."""
        x_list = list(x)
        ys = [list(a) for a in args]
        n = len(x_list)

        if labels is None:
            labels = ['_nolegend_'] * len(ys)
        if colors is None:
            colors = [self._next_color() for _ in ys]
        else:
            colors = [to_hex(c) for c in colors]

        alpha = kwargs.get('alpha', 0.5)

        baseline = [0.0] * n
        polys = []
        for i, y_data in enumerate(ys):
            top = [baseline[j] + y_data[j] for j in range(n)]
            verts = []
            for j in range(n):
                verts.append((x_list[j], top[j]))
            for j in range(n - 1, -1, -1):
                verts.append((x_list[j], baseline[j]))

            poly = Polygon(verts, facecolor=colors[i], edgecolor='none')
            poly.set_alpha(alpha)
            poly.set_label(labels[i])
            poly.axes = self
            poly.figure = self.figure
            self.patches.append(poly)
            polys.append(poly)
            baseline = top

        return polys

    def stem(self, *args, linefmt=None, markerfmt=None, basefmt=None,
             bottom=0, label=None, **kwargs):
        """Stem plot (lollipop chart)."""
        if len(args) == 1:
            y_list = list(args[0])
            x_list = list(range(len(y_list)))
        elif len(args) == 2:
            x_list = list(args[0])
            y_list = list(args[1])
        else:
            raise TypeError(f"stem() takes 1-2 positional args, got {len(args)}")

        color = self._next_color()

        stemlines = []
        for i in range(len(x_list)):
            sl = Line2D([x_list[i], x_list[i]], [bottom, y_list[i]],
                        color=color, linewidth=1.0, linestyle='-')
            sl.set_label('_nolegend_')
            sl.axes = self
            sl.figure = self.figure
            self.lines.append(sl)
            stemlines.append(sl)

        markerline = Line2D(x_list, y_list, color=color,
                            linewidth=0, linestyle='None', marker='o')
        markerline.set_label('_nolegend_')
        markerline.axes = self
        markerline.figure = self.figure
        self.lines.append(markerline)

        baseline = Line2D([min(x_list), max(x_list)], [bottom, bottom],
                          color='C3', linewidth=1.0, linestyle='-')
        baseline.set_label('_nolegend_')
        baseline.axes = self
        baseline.figure = self.figure
        self.lines.append(baseline)

        sc = StemContainer((markerline, stemlines, baseline), label=label)
        self.containers.append(sc)
        return sc

    def pie(self, x, labels=None, colors=None, explode=None,
            autopct=None, startangle=0, counterclock=True, **kwargs):
        """Pie chart."""
        vals = list(x)
        total = sum(vals)
        if total == 0:
            return [], []

        n = len(vals)
        if colors is None:
            colors = [DEFAULT_CYCLE[i % len(DEFAULT_CYCLE)] for i in range(n)]
        if labels is None:
            labels = [None] * n
        if explode is None:
            explode = [0.0] * n

        self.set_aspect('equal')

        cx, cy = 0.0, 0.0
        radius = 1.0

        wedges = []
        texts = []
        autotexts = [] if autopct else None

        angle = startangle
        for i in range(n):
            frac = vals[i] / total
            sweep = frac * 360.0
            if not counterclock:
                sweep = -sweep

            theta1 = angle
            theta2 = angle + sweep

            # Explode offset
            if explode[i] != 0:
                mid_angle = math.radians((theta1 + theta2) / 2)
                dx = explode[i] * math.cos(mid_angle)
                dy = explode[i] * math.sin(mid_angle)
            else:
                dx, dy = 0, 0

            w = Wedge((cx + dx, cy + dy), radius, theta1, theta2,
                      facecolor=colors[i], edgecolor='white')
            w.axes = self
            w.figure = self.figure
            self.patches.append(w)
            wedges.append(w)

            # Label text at 1.2 * radius
            if labels[i] is not None:
                mid_angle = math.radians((theta1 + theta2) / 2)
                lx = cx + dx + 1.2 * radius * math.cos(mid_angle)
                ly = cy + dy + 1.2 * radius * math.sin(mid_angle)
                ha = 'left' if math.cos(mid_angle) >= 0 else 'right'
                t = Text(lx, ly, labels[i], ha=ha, va='center', fontsize=11)
                t.axes = self
                t.figure = self.figure
                self.texts.append(t)
                texts.append(t)

            # Autopct text at 0.6 * radius
            if autopct is not None:
                pct = frac * 100
                mid_angle = math.radians((theta1 + theta2) / 2)
                px = cx + dx + 0.6 * radius * math.cos(mid_angle)
                py = cy + dy + 0.6 * radius * math.sin(mid_angle)
                pct_text = autopct % pct
                at = Text(px, py, pct_text, ha='center', va='center',
                          fontsize=10)
                at.axes = self
                at.figure = self.figure
                self.texts.append(at)
                autotexts.append(at)

            angle = theta2

        if autopct is not None:
            return wedges, texts, autotexts
        return wedges, texts

    def boxplot(self, x, vert=True, widths=None, showfliers=True,
                showmeans=False, **kwargs):
        """Box-and-whisker plot."""
        if not x:
            return {'boxes': [], 'medians': [], 'whiskers': [],
                    'caps': [], 'fliers': [], 'means': []}
        # Normalize input: always a list of datasets
        if not hasattr(x[0], '__iter__'):
            datasets = [list(x)]
        else:
            datasets = [list(d) for d in x]

        n = len(datasets)
        if widths is None:
            widths = [0.5] * n
        elif not hasattr(widths, '__iter__'):
            widths = [widths] * n

        result = {
            'boxes': [],
            'medians': [],
            'whiskers': [],
            'caps': [],
            'fliers': [],
            'means': [],
        }

        for i, data in enumerate(datasets):
            pos = i + 1
            w = widths[i]
            sorted_data = sorted(data)

            q1 = _percentile(sorted_data, 25)
            med = _median(sorted_data)
            q3 = _percentile(sorted_data, 75)
            iqr = q3 - q1

            whisker_lo = q1 - 1.5 * iqr
            whisker_hi = q3 + 1.5 * iqr
            actual_lo = min(v for v in sorted_data if v >= whisker_lo)
            actual_hi = max(v for v in sorted_data if v <= whisker_hi)

            if vert:
                # Box
                box = Rectangle((pos - w / 2, q1), w, q3 - q1,
                                facecolor='white', edgecolor='black')
                box.set_label('_nolegend_')
                box.axes = self
                box.figure = self.figure
                self.patches.append(box)
                result['boxes'].append(box)

                # Median line
                med_line = Line2D([pos - w / 2, pos + w / 2], [med, med],
                                  color='orange', linewidth=2.0)
                med_line.set_label('_nolegend_')
                med_line.axes = self
                med_line.figure = self.figure
                self.lines.append(med_line)
                result['medians'].append(med_line)

                # Whiskers
                lo_whisker = Line2D([pos, pos], [actual_lo, q1],
                                    color='black', linewidth=1.0, linestyle='--')
                lo_whisker.set_label('_nolegend_')
                lo_whisker.axes = self
                lo_whisker.figure = self.figure
                self.lines.append(lo_whisker)

                hi_whisker = Line2D([pos, pos], [q3, actual_hi],
                                    color='black', linewidth=1.0, linestyle='--')
                hi_whisker.set_label('_nolegend_')
                hi_whisker.axes = self
                hi_whisker.figure = self.figure
                self.lines.append(hi_whisker)
                result['whiskers'].extend([lo_whisker, hi_whisker])

                # Caps
                lo_cap = Line2D([pos - w / 4, pos + w / 4],
                                [actual_lo, actual_lo],
                                color='black', linewidth=1.0)
                lo_cap.set_label('_nolegend_')
                lo_cap.axes = self
                lo_cap.figure = self.figure
                self.lines.append(lo_cap)

                hi_cap = Line2D([pos - w / 4, pos + w / 4],
                                [actual_hi, actual_hi],
                                color='black', linewidth=1.0)
                hi_cap.set_label('_nolegend_')
                hi_cap.axes = self
                hi_cap.figure = self.figure
                self.lines.append(hi_cap)
                result['caps'].extend([lo_cap, hi_cap])

                # Fliers
                if showfliers:
                    flier_pts = [v for v in sorted_data
                                 if v < actual_lo or v > actual_hi]
                    if flier_pts:
                        flier_x = [pos] * len(flier_pts)
                        pc = PathCollection(
                            offsets=list(zip(flier_x, flier_pts)),
                            sizes=[20], facecolors=['black'])
                        pc.set_label('_nolegend_')
                        pc.axes = self
                        pc.figure = self.figure
                        self.collections.append(pc)
                        result['fliers'].append(pc)

                # Means
                if showmeans:
                    mean_val = sum(data) / len(data)
                    mean_pc = PathCollection(
                        offsets=[(pos, mean_val)],
                        sizes=[50], facecolors=['green'])
                    mean_pc.set_label('_nolegend_')
                    mean_pc.axes = self
                    mean_pc.figure = self.figure
                    self.collections.append(mean_pc)
                    result['means'].append(mean_pc)

            else:
                # Horizontal boxplot: swap x and y
                box = Rectangle((q1, pos - w / 2), q3 - q1, w,
                                facecolor='white', edgecolor='black')
                box.set_label('_nolegend_')
                box.axes = self
                box.figure = self.figure
                self.patches.append(box)
                result['boxes'].append(box)

                med_line = Line2D([med, med], [pos - w / 2, pos + w / 2],
                                  color='orange', linewidth=2.0)
                med_line.set_label('_nolegend_')
                med_line.axes = self
                med_line.figure = self.figure
                self.lines.append(med_line)
                result['medians'].append(med_line)

                lo_whisker = Line2D([actual_lo, q1], [pos, pos],
                                    color='black', linewidth=1.0, linestyle='--')
                lo_whisker.set_label('_nolegend_')
                lo_whisker.axes = self
                lo_whisker.figure = self.figure
                self.lines.append(lo_whisker)

                hi_whisker = Line2D([q3, actual_hi], [pos, pos],
                                    color='black', linewidth=1.0, linestyle='--')
                hi_whisker.set_label('_nolegend_')
                hi_whisker.axes = self
                hi_whisker.figure = self.figure
                self.lines.append(hi_whisker)
                result['whiskers'].extend([lo_whisker, hi_whisker])

                lo_cap = Line2D([actual_lo, actual_lo],
                                [pos - w / 4, pos + w / 4],
                                color='black', linewidth=1.0)
                lo_cap.set_label('_nolegend_')
                lo_cap.axes = self
                lo_cap.figure = self.figure
                self.lines.append(lo_cap)

                hi_cap = Line2D([actual_hi, actual_hi],
                                [pos - w / 4, pos + w / 4],
                                color='black', linewidth=1.0)
                hi_cap.set_label('_nolegend_')
                hi_cap.axes = self
                hi_cap.figure = self.figure
                self.lines.append(hi_cap)
                result['caps'].extend([lo_cap, hi_cap])

                if showfliers:
                    flier_pts = [v for v in sorted_data
                                 if v < actual_lo or v > actual_hi]
                    if flier_pts:
                        flier_y = [pos] * len(flier_pts)
                        pc = PathCollection(
                            offsets=list(zip(flier_pts, flier_y)),
                            sizes=[20], facecolors=['black'])
                        pc.set_label('_nolegend_')
                        pc.axes = self
                        pc.figure = self.figure
                        self.collections.append(pc)
                        result['fliers'].append(pc)

        return result

    def violinplot(self, dataset, positions=None, vert=True, widths=0.5,
                   showmeans=False, showmedians=False, showextrema=True,
                   **kwargs):
        """Violin plot."""
        if not dataset:
            return {'bodies': [], 'cmeans': [], 'cmedians': [],
                    'cmins': [], 'cmaxes': [], 'cbars': []}
        # Normalize: always list of datasets
        if not hasattr(dataset[0], '__iter__'):
            datasets = [list(dataset)]
        else:
            datasets = [list(d) for d in dataset]

        n = len(datasets)
        if positions is None:
            positions = list(range(1, n + 1))

        if not hasattr(widths, '__iter__'):
            widths = [widths] * n

        result = {
            'bodies': [],
            'cmeans': [],
            'cmedians': [],
            'cmins': [],
            'cmaxes': [],
            'cbars': [],
        }

        for i, data in enumerate(datasets):
            pos = positions[i]
            w = widths[i]
            color = self._next_color()

            kde_pos, kde_dens = _gaussian_kde(data, n_points=50)
            if not kde_dens:
                continue

            max_d = max(kde_dens) if kde_dens else 1.0
            scale = (w / 2) / max_d if max_d > 0 else 1.0

            if vert:
                verts = []
                for j in range(len(kde_pos)):
                    verts.append((pos + kde_dens[j] * scale, kde_pos[j]))
                for j in range(len(kde_pos) - 1, -1, -1):
                    verts.append((pos - kde_dens[j] * scale, kde_pos[j]))
            else:
                verts = []
                for j in range(len(kde_pos)):
                    verts.append((kde_pos[j], pos + kde_dens[j] * scale))
                for j in range(len(kde_pos) - 1, -1, -1):
                    verts.append((kde_pos[j], pos - kde_dens[j] * scale))

            poly = Polygon(verts, facecolor=color, edgecolor='black')
            poly.set_alpha(0.5)
            poly.set_label('_nolegend_')
            poly.axes = self
            poly.figure = self.figure
            self.patches.append(poly)
            result['bodies'].append(poly)

            sorted_data = sorted(data)
            data_min = sorted_data[0]
            data_max = sorted_data[-1]
            data_mean = sum(data) / len(data)
            data_med = _median(data)

            if showextrema:
                if vert:
                    bar = Line2D([pos, pos], [data_min, data_max],
                                 color='black', linewidth=1.0)
                    bar.set_label('_nolegend_')
                    bar.axes = self
                    bar.figure = self.figure
                    self.lines.append(bar)
                    result['cbars'].append(bar)

                    min_line = Line2D([pos - w / 4, pos + w / 4],
                                     [data_min, data_min],
                                     color='black', linewidth=1.0)
                    min_line.set_label('_nolegend_')
                    min_line.axes = self
                    min_line.figure = self.figure
                    self.lines.append(min_line)
                    result['cmins'].append(min_line)

                    max_line = Line2D([pos - w / 4, pos + w / 4],
                                     [data_max, data_max],
                                     color='black', linewidth=1.0)
                    max_line.set_label('_nolegend_')
                    max_line.axes = self
                    max_line.figure = self.figure
                    self.lines.append(max_line)
                    result['cmaxes'].append(max_line)
                else:
                    bar = Line2D([data_min, data_max], [pos, pos],
                                 color='black', linewidth=1.0)
                    bar.set_label('_nolegend_')
                    bar.axes = self
                    bar.figure = self.figure
                    self.lines.append(bar)
                    result['cbars'].append(bar)

                    min_line = Line2D([data_min, data_min],
                                     [pos - w / 4, pos + w / 4],
                                     color='black', linewidth=1.0)
                    min_line.set_label('_nolegend_')
                    min_line.axes = self
                    min_line.figure = self.figure
                    self.lines.append(min_line)
                    result['cmins'].append(min_line)

                    max_line = Line2D([data_max, data_max],
                                     [pos - w / 4, pos + w / 4],
                                     color='black', linewidth=1.0)
                    max_line.set_label('_nolegend_')
                    max_line.axes = self
                    max_line.figure = self.figure
                    self.lines.append(max_line)
                    result['cmaxes'].append(max_line)

            if showmeans:
                if vert:
                    m = Line2D([pos - w / 4, pos + w / 4],
                               [data_mean, data_mean],
                               color='red', linewidth=1.5)
                else:
                    m = Line2D([data_mean, data_mean],
                               [pos - w / 4, pos + w / 4],
                               color='red', linewidth=1.5)
                m.set_label('_nolegend_')
                m.axes = self
                m.figure = self.figure
                self.lines.append(m)
                result['cmeans'].append(m)

            if showmedians:
                if vert:
                    m = Line2D([pos - w / 4, pos + w / 4],
                               [data_med, data_med],
                               color='blue', linewidth=1.5)
                else:
                    m = Line2D([data_med, data_med],
                               [pos - w / 4, pos + w / 4],
                               color='blue', linewidth=1.5)
                m.set_label('_nolegend_')
                m.axes = self
                m.figure = self.figure
                self.lines.append(m)
                result['cmedians'].append(m)

        return result

    def text(self, x, y, s, **kwargs):
        """Add text to the axes."""
        t = Text(x, y, str(s), **kwargs)
        t.axes = self
        t.figure = self.figure
        self.texts.append(t)

        return t

    def annotate(self, text, xy, xytext=None, arrowprops=None, **kwargs):
        """Add an annotation to the axes."""
        ann = Annotation(text, xy, xytext=xytext, arrowprops=arrowprops,
                         **kwargs)
        ann.axes = self
        ann.figure = self.figure
        self.texts.append(ann)

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
            elif hasattr(patch, '_center') and hasattr(patch, '_r'):
                # Wedge or Circle
                xs.append(patch._center[0] - patch._r)
                xs.append(patch._center[0] + patch._r)
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
            elif hasattr(patch, '_center') and hasattr(patch, '_r'):
                # Wedge or Circle
                ys.append(patch._center[1] - patch._r)
                ys.append(patch._center[1] + patch._r)
        # Bars typically start from 0
        if ys and any(hasattr(p, '_height') for p in self.patches):
            ys.append(0)
        if not ys:
            return (0.0, 1.0)
        return (min(ys), max(ys))

    def set_xticks(self, ticks, labels=None, **kwargs):
        self.xaxis.set_ticks(ticks, labels)

    def get_xticks(self):
        return self.xaxis.get_ticks()

    def set_yticks(self, ticks, labels=None, **kwargs):
        self.yaxis.set_ticks(ticks, labels)

    def get_yticks(self):
        return self.yaxis.get_ticks()

    def set_xticklabels(self, labels, **kwargs):
        self.xaxis.set_major_formatter(FixedFormatter(list(labels)))

    def set_yticklabels(self, labels, **kwargs):
        self.yaxis.set_major_formatter(FixedFormatter(list(labels)))

    def tick_params(self, **kwargs):
        # No-op compatibility shim.
        return None

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

    def set_xscale(self, scale, **kwargs):
        """Set the x-axis scale ('linear', 'log', 'symlog', or a Scale object)."""
        from matplotlib.scale import (LinearScale, LogScale,
                                       SymmetricalLogScale, FuncScale)
        if isinstance(scale, str):
            if scale == 'linear':
                scale_obj = LinearScale()
            elif scale == 'log':
                scale_obj = LogScale(base=kwargs.get('base', 10.0),
                                     nonpositive=kwargs.get('nonpositive', 'mask'))
            elif scale == 'symlog':
                scale_obj = SymmetricalLogScale(
                    base=kwargs.get('base', 10.0),
                    linthresh=kwargs.get('linthresh', 2.0),
                    linscale=kwargs.get('linscale', 1.0))
            else:
                raise ValueError(f"Unknown scale: {scale!r}")
        elif isinstance(scale, (LinearScale, LogScale,
                                 SymmetricalLogScale, FuncScale)):
            scale_obj = scale
        else:
            raise TypeError(f"scale must be a string or Scale object, "
                            f"got {type(scale)}")
        self._xscale = scale if isinstance(scale, str) else 'custom'
        self.xaxis.set_scale(scale_obj)

    def set_yscale(self, scale, **kwargs):
        """Set the y-axis scale ('linear', 'log', 'symlog', or a Scale object)."""
        from matplotlib.scale import (LinearScale, LogScale,
                                       SymmetricalLogScale, FuncScale)
        if isinstance(scale, str):
            if scale == 'linear':
                scale_obj = LinearScale()
            elif scale == 'log':
                scale_obj = LogScale(base=kwargs.get('base', 10.0),
                                     nonpositive=kwargs.get('nonpositive', 'mask'))
            elif scale == 'symlog':
                scale_obj = SymmetricalLogScale(
                    base=kwargs.get('base', 10.0),
                    linthresh=kwargs.get('linthresh', 2.0),
                    linscale=kwargs.get('linscale', 1.0))
            else:
                raise ValueError(f"Unknown scale: {scale!r}")
        elif isinstance(scale, (LinearScale, LogScale,
                                 SymmetricalLogScale, FuncScale)):
            scale_obj = scale
        else:
            raise TypeError(f"scale must be a string or Scale object, "
                            f"got {type(scale)}")
        self._yscale = scale if isinstance(scale, str) else 'custom'
        self.yaxis.set_scale(scale_obj)

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

        return AxesLayout(plot_x, plot_y, plot_w, plot_h, xmin, xmax, ymin, ymax,
                          xscale=self.xaxis.get_scale(),
                          yscale=self.yaxis.get_scale())

    def draw(self, renderer):
        layout = self._compute_layout(renderer.width, renderer.height)
        if layout is None:
            return

        px, py, pw, ph = layout.plot_x, layout.plot_y, layout.plot_w, layout.plot_h

        # Frame border
        renderer.draw_rect(px, py, pw, ph, '#000000', 'none')

        # Compute tick positions ONCE — used for both grid and tick marks
        xtick_vals = self.xaxis.tick_values(layout.xmin, layout.xmax)
        ytick_vals = self.yaxis.tick_values(layout.ymin, layout.ymax)
        xtick_labels = self.xaxis.format_ticks(xtick_vals)
        ytick_labels = self.yaxis.format_ticks(ytick_vals)

        # Grid
        if self._grid:
            for t in xtick_vals:
                tx = layout.sx(t)
                if px < tx < px + pw:
                    renderer.draw_line([tx, tx], [py, py + ph],
                                       '#dddddd', 0.5, '--')
            for t in ytick_vals:
                ty = layout.sy(t)
                if py < ty < py + ph:
                    renderer.draw_line([px, px + pw], [ty, ty],
                                       '#dddddd', 0.5, '--')

        # Tick marks + labels
        for t, label in zip(xtick_vals, xtick_labels):
            tx = layout.sx(t)
            if px <= tx <= px + pw:
                renderer.draw_line([tx, tx], [py + ph, py + ph + 5],
                                   '#000000', 1.0, '-')
                if self._xticklabels_visible:
                    renderer.draw_text(tx, py + ph + 18, label,
                                       11, '#333333', 'center')
        for t, label in zip(ytick_vals, ytick_labels):
            ty = layout.sy(t)
            if py <= ty <= py + ph:
                renderer.draw_line([px - 5, px], [ty, ty],
                                   '#000000', 1.0, '-')
                if self._yticklabels_visible:
                    renderer.draw_text(px - 8, ty + 4, label,
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
        self._title = ''
        self._xlabel = ''
        self._ylabel = ''
        self._xlim = None
        self._ylim = None
        self.xaxis = XAxis()
        self.yaxis = YAxis()
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

    def clear(self):
        self.cla()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _percentile(data, pct):
    """Simple percentile calculation (linear interpolation)."""
    sorted_d = sorted(data)
    n = len(sorted_d)
    if n == 0:
        return 0
    if n == 1:
        return sorted_d[0]
    k = (n - 1) * pct / 100.0
    f = int(k)
    c = f + 1
    if c >= n:
        return sorted_d[-1]
    return sorted_d[f] + (k - f) * (sorted_d[c] - sorted_d[f])


def _median(data):
    """Simple median calculation."""
    return _percentile(data, 50)


def _gaussian_kde(data, n_points=100):
    """Simple Gaussian kernel density estimate using Silverman's rule."""
    n = len(data)
    if n == 0:
        return [], []

    mean = sum(data) / n
    var = sum((v - mean) ** 2 for v in data) / n
    std = math.sqrt(var) if var > 0 else 1.0

    bw = 1.06 * std * (n ** -0.2) if std > 0 else 1.0

    lo = min(data) - 3 * bw
    hi = max(data) + 3 * bw
    step = (hi - lo) / (n_points - 1) if n_points > 1 else 1.0
    positions = [lo + i * step for i in range(n_points)]

    densities = []
    coeff = 1.0 / (n * bw * math.sqrt(2 * math.pi))
    for p in positions:
        total = 0.0
        for d in data:
            z = (p - d) / bw
            total += math.exp(-0.5 * z * z)
        densities.append(total * coeff)

    return positions, densities


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
