"""
matplotlib.backend_bases — abstract renderer and layout helpers.
"""


class AxesLayout:
    """Stores plot area geometry and provides data-to-pixel transforms."""

    def __init__(self, plot_x, plot_y, plot_w, plot_h,
                 xmin, xmax, ymin, ymax, xscale=None, yscale=None):
        self.plot_x = plot_x
        self.plot_y = plot_y
        self.plot_w = plot_w
        self.plot_h = plot_h
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        from matplotlib.scale import LinearScale
        import numpy as np
        self._xscale = xscale or LinearScale()
        self._yscale = yscale or LinearScale()

        def _fwd_scalar(scale, v):
            """Apply scale.forward() to a scalar and return a plain float.
            Bypasses numpy masked-array machinery for robustness in RustPython."""
            from matplotlib.scale import LinearScale, LogScale, SymmetricalLogScale
            import math
            v = float(v)
            if isinstance(scale, LinearScale):
                return v
            elif isinstance(scale, LogScale):
                return math.log(v) / math.log(scale.base) if v > 0 else float('nan')
            elif isinstance(scale, SymmetricalLogScale):
                # Inline _symlog for a scalar
                log_base = math.log(scale.base)
                sign = 1.0 if v >= 0 else -1.0
                abs_v = abs(v)
                if abs_v <= scale.linthresh:
                    return v / scale.linthresh * scale.linscale
                return sign * (scale.linscale + math.log(abs_v / scale.linthresh) / log_base)
            else:
                # FuncScale or unknown — forward returns a numpy scalar, try float()
                result = scale.forward(v)
                return float(result)

        self._fwd_scalar = _fwd_scalar
        self._fxmin = _fwd_scalar(self._xscale, xmin)
        self._fxmax = _fwd_scalar(self._xscale, xmax)
        self._fymin = _fwd_scalar(self._yscale, ymin)
        self._fymax = _fwd_scalar(self._yscale, ymax)

    def sx(self, v):
        """Map data x to pixel x via scale."""
        fv = self._fwd_scalar(self._xscale, v)
        return self.plot_x + (fv - self._fxmin) / (self._fxmax - self._fxmin) * self.plot_w

    def sy(self, v):
        """Map data y to pixel y (inverted) via scale."""
        fv = self._fwd_scalar(self._yscale, v)
        return self.plot_y + self.plot_h - (fv - self._fymin) / (self._fymax - self._fymin) * self.plot_h


class RendererBase:
    """Abstract base class for renderers."""

    def __init__(self, width, height, dpi):
        self.width = width
        self.height = height
        self.dpi = dpi

    def draw_line(self, xdata, ydata, color, linewidth, linestyle, opacity=1.0):
        raise NotImplementedError

    def draw_markers(self, xdata, ydata, color, size):
        raise NotImplementedError

    def draw_rect(self, x, y, width, height, stroke, fill):
        raise NotImplementedError

    def draw_circle(self, cx, cy, r, color):
        raise NotImplementedError

    def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
        raise NotImplementedError

    def draw_polygon(self, points, color, alpha):
        raise NotImplementedError

    def draw_text(self, x, y, text, fontsize, color, ha):
        raise NotImplementedError

    def set_clip_rect(self, x, y, width, height):
        raise NotImplementedError

    def clear_clip(self):
        raise NotImplementedError

    def draw_arrow(self, x1, y1, x2, y2, arrowstyle, color, linewidth):
        """Draw an arrow from (x1,y1) to (x2,y2).

        arrowstyle : str
            One of '->', '<-', '<->', '-', 'fancy'.
        """
        raise NotImplementedError

    def get_result(self):
        raise NotImplementedError
