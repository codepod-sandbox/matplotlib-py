"""matplotlib.lines --- Line2D artist for line/marker plots."""

from matplotlib.artist import Artist
from matplotlib.colors import to_hex, to_rgba


class Line2D(Artist):
    """A line and/or marker artist for 2-D data."""

    zorder = 2

    def __init__(self, xdata, ydata, color=None, linewidth=None,
                 linestyle=None, marker=None, label=None, **kwargs):
        super().__init__()

        self._xdata = list(xdata)
        self._ydata = list(ydata)

        self._color = color if color is not None else 'C0'
        self._linewidth = linewidth if linewidth is not None else 1.5
        self._linestyle = linestyle if linestyle is not None else '-'
        self._marker = marker if marker is not None else 'None'

        if label is not None:
            self.set_label(label)

        # Extra kwargs
        self._markersize = kwargs.get('markersize', kwargs.get('ms', 6.0))
        self._fillstyle = kwargs.get('fillstyle', 'full')
        self._drawstyle = kwargs.get('drawstyle', 'default')

    # --- xdata ---
    def get_xdata(self):
        return list(self._xdata)

    def set_xdata(self, x):
        self._xdata = list(x)

    # --- ydata ---
    def get_ydata(self):
        return list(self._ydata)

    def set_ydata(self, y):
        self._ydata = list(y)

    # --- data ---
    def get_data(self):
        return self.get_xdata(), self.get_ydata()

    def set_data(self, x, y):
        self.set_xdata(x)
        self.set_ydata(y)

    # --- color ---
    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = color

    set_c = set_color

    # --- linewidth ---
    def get_linewidth(self):
        return self._linewidth

    def set_linewidth(self, w):
        self._linewidth = w

    set_lw = set_linewidth

    # --- linestyle ---
    def get_linestyle(self):
        return self._linestyle

    def set_linestyle(self, ls):
        self._linestyle = ls

    set_ls = set_linestyle

    # --- marker ---
    def get_marker(self):
        return self._marker

    def set_marker(self, marker):
        self._marker = marker

    # --- markersize ---
    def get_markersize(self):
        return self._markersize

    def set_markersize(self, sz):
        self._markersize = sz

    set_ms = set_markersize

    # --- fillstyle ---
    def get_fillstyle(self):
        return self._fillstyle

    def set_fillstyle(self, fs):
        self._fillstyle = fs

    # --- drawstyle ---
    def get_drawstyle(self):
        return self._drawstyle

    def set_drawstyle(self, ds):
        self._drawstyle = ds

    # --- draw (new renderer architecture) ---
    def draw(self, renderer, layout):
        """Draw this line onto the renderer."""
        if not self.get_visible():
            return
        x_px = [layout.sx(v) for v in self._xdata]
        y_px = [layout.sy(v) for v in self._ydata]
        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        color = to_hex(self._color)

        # Draw line (skip if no-line style)
        if (self._linestyle not in ('None', 'none', '')
                and len(x_px) >= 2):
            renderer.draw_line(x_px, y_px, color,
                               float(self._linewidth), self._linestyle,
                               opacity=self._alpha if self._alpha is not None else 1.0)

        # Draw markers
        if self._marker and self._marker not in ('None', 'none', ''):
            renderer.draw_markers(x_px, y_px, color,
                                  float(self._markersize))

