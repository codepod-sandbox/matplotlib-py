"""
matplotlib.figure — Figure class.
"""

import math

from matplotlib.axes import Axes
from matplotlib.gridspec import SubplotSpec
from matplotlib.text import Text


def _validate_figsize(w, h):
    for val, name in [(w, 'width'), (h, 'height')]:
        if math.isnan(val):
            raise ValueError(f"figure size must be finite, not {name}={val}")
        if math.isinf(val):
            raise ValueError(f"figure size must be finite, not {name}={val}")
        if val <= 0:
            raise ValueError(f"figure size must be positive, not {name}={val}")


class Figure:
    """Top-level container for a matplotlib plot."""

    def __init__(self, figsize=None, dpi=100):
        self.figsize = figsize or (6.4, 4.8)
        _validate_figsize(self.figsize[0], self.figsize[1])
        self.dpi = dpi
        self._axes = []
        self._suptitle = None
        self._supxlabel = None
        self._supylabel = None
        self._label = ''
        self.number = None
        self.stale = True
        self.texts = []
        self._current_ax = None

    # ------------------------------------------------------------------
    # Axes management
    # ------------------------------------------------------------------

    def add_subplot(self, *args, **kwargs):
        """Add an Axes to the figure.

        Accepts:
            add_subplot(nrows, ncols, index)
            add_subplot(SubplotSpec)
            add_subplot(existing_axes)
            add_subplot(NCI)  -- 3-digit integer
        """
        # Accept an existing Axes instance
        if len(args) == 1 and isinstance(args[0], Axes):
            ax = args[0]
            if ax in self._axes:
                self._current_ax = ax
                return ax
            self._axes.append(ax)
            self._current_ax = ax
            return ax

        if len(args) == 1 and isinstance(args[0], SubplotSpec):
            ss = args[0]
            pos = (ss.rowspan, ss.colspan)
        elif len(args) == 1 and isinstance(args[0], int) and args[0] >= 100:
            # 3-digit form: 211 -> (2, 1, 1)
            n = args[0]
            nrows, ncols, index = n // 100, (n % 100) // 10, n % 10
            pos = (nrows, ncols, index)
        elif len(args) == 3:
            nrows, ncols, index = args
            pos = (nrows, ncols, index)
        elif len(args) == 0:
            pos = (1, 1, 1)
        else:
            nrows = args[0] if len(args) > 0 else kwargs.get('nrows', 1)
            ncols = args[1] if len(args) > 1 else kwargs.get('ncols', 1)
            index = args[2] if len(args) > 2 else kwargs.get('index', 1)
            pos = (nrows, ncols, index)

        ax = Axes(self, pos)
        self._axes.append(ax)
        self._current_ax = ax
        return ax

    def add_axes(self, rect=None, **kwargs):
        """Add an Axes at position *rect* [left, bottom, width, height].

        If *rect* is an Axes instance, add it (or re-activate it).
        If *rect* is None, defaults to [0, 0, 1, 1].
        """
        if isinstance(rect, Axes):
            ax = rect
            if ax in self._axes:
                self._current_ax = ax
                return ax
            self._axes.append(ax)
            self._current_ax = ax
            return ax
        if rect is None:
            rect = [0, 0, 1, 1]
        ax = Axes(self, tuple(rect))
        self._axes.append(ax)
        self._current_ax = ax
        return ax

    def gca(self):
        """Get current axes, or create one if none exist."""
        if self._current_ax is not None and self._current_ax in self._axes:
            return self._current_ax
        if not self._axes:
            return self.add_subplot(1, 1, 1)
        return self._axes[-1]

    def sca(self, ax):
        """Set the current axes to *ax*.

        Sets _current_ax without reordering the axes list.
        """
        self._current_ax = ax

    def delaxes(self, ax):
        """Remove the Axes *ax* from this figure."""
        if ax in self._axes:
            self._axes.remove(ax)

    def get_axes(self):
        """Return a list of Axes in this figure."""
        return list(self._axes)

    @property
    def axes(self):
        return list(self._axes)

    # ------------------------------------------------------------------
    # Suptitle
    # ------------------------------------------------------------------

    def suptitle(self, t, **kwargs):
        """Set a centered suptitle for the figure.

        Returns the Text object.
        """
        self._suptitle = t
        txt = Text(0.5, 0.98, t, **kwargs)
        self.texts.append(txt)
        self.stale = True
        return txt

    def get_suptitle(self):
        """Return the figure suptitle string, or '' if not set."""
        return self._suptitle if self._suptitle is not None else ''

    def supxlabel(self, t, **kwargs):
        """Set the supxlabel for the figure."""
        self._supxlabel = t
        self.stale = True
        return t

    def get_supxlabel(self):
        """Return the figure supxlabel string, or '' if not set."""
        return self._supxlabel if self._supxlabel is not None else ''

    def supylabel(self, t, **kwargs):
        """Set the supylabel for the figure."""
        self._supylabel = t
        self.stale = True
        return t

    def get_supylabel(self):
        """Return the figure supylabel string, or '' if not set."""
        return self._supylabel if self._supylabel is not None else ''

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def set_size_inches(self, w, h=None):
        """Set the figure size in inches.

        Accepts ``set_size_inches(w, h)`` or ``set_size_inches((w, h))``.
        """
        if h is None:
            # w is a (w, h) tuple
            w, h = w
        _validate_figsize(float(w), float(h))
        self.figsize = (float(w), float(h))
        self.stale = True

    def get_size_inches(self):
        """Return the figure size as ``(width, height)`` in inches."""
        return tuple(self.figsize)

    def set_figwidth(self, val):
        """Set the figure width in inches."""
        self.figsize = (float(val), self.figsize[1])
        self.stale = True

    def set_figheight(self, val):
        """Set the figure height in inches."""
        self.figsize = (self.figsize[0], float(val))
        self.stale = True

    def get_figwidth(self):
        """Return the figure width in inches."""
        return self.figsize[0]

    def get_figheight(self):
        """Return the figure height in inches."""
        return self.figsize[1]

    # ------------------------------------------------------------------
    # DPI
    # ------------------------------------------------------------------

    def get_dpi(self):
        """Return the figure dpi."""
        return self.dpi

    def set_dpi(self, val):
        """Set the figure dpi."""
        self.dpi = val
        self.stale = True

    # ------------------------------------------------------------------
    # Label
    # ------------------------------------------------------------------

    def get_label(self):
        """Return the figure label."""
        return self._label

    def set_label(self, label):
        """Set the figure label."""
        self._label = str(label)

    # ------------------------------------------------------------------
    # Layout / clearing
    # ------------------------------------------------------------------

    def tight_layout(self, **kwargs):
        """Adjust subplot parameters for a tight layout.

        No-op placeholder in this implementation.
        """
        pass

    def text(self, x, y, s, **kwargs):
        """Add text to the figure at position (x, y).

        Returns the Text object.
        """
        txt = Text(x, y, s, **kwargs)
        self.texts.append(txt)
        return txt

    def clear(self):
        """Clear the figure — remove all axes and reset suptitle."""
        self._axes.clear()
        self._suptitle = None
        self.texts = []
        self._current_ax = None
        self.stale = True

    def clf(self):
        """Clear the figure (alias for :meth:`clear`)."""
        self.clear()

    def draw_without_rendering(self):
        """No-op placeholder for layout engine compatibility."""
        pass

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def savefig(self, fname, *, format=None, dpi=None):
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

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self):
        w, h = self.figsize
        # Format dimensions similarly to real matplotlib: WxH
        # Use integer representation when values are whole numbers
        w_str = str(int(w * self.dpi))
        h_str = str(int(h * self.dpi))
        n = len(self._axes)
        return f'<Figure size {w_str}x{h_str} with {n} Axes>'
