"""matplotlib.patches --- Patch, Rectangle, and Circle artists."""

from matplotlib.artist import Artist
from matplotlib.colors import to_rgba, to_hex


class Patch(Artist):
    """Base class for 2-D filled shapes."""

    zorder = 1

    def __init__(self, facecolor=None, edgecolor=None, linewidth=None,
                 **kwargs):
        super().__init__()
        self._facecolor = facecolor if facecolor is not None else 'C0'
        self._edgecolor = edgecolor if edgecolor is not None else 'black'
        self._linewidth = linewidth if linewidth is not None else 1.0

        # Apply any remaining kwargs through the batch setter
        if kwargs:
            self.set(**kwargs)

    # --- facecolor ---
    def get_facecolor(self):
        """Return facecolor as an RGBA tuple, applying artist alpha."""
        fc = self._facecolor
        if isinstance(fc, str) and fc.lower() == 'none':
            return (0.0, 0.0, 0.0, 0.0)
        rgba = to_rgba(fc)
        if self._alpha is not None:
            rgba = (rgba[0], rgba[1], rgba[2], self._alpha)
        return rgba

    def set_facecolor(self, color):
        self._facecolor = color

    # --- edgecolor ---
    def get_edgecolor(self):
        """Return edgecolor as an RGBA tuple, applying artist alpha.

        If edgecolor is 'none', returns (0, 0, 0, 0) without applying alpha.
        """
        ec = self._edgecolor
        if isinstance(ec, str) and ec.lower() == 'none':
            return (0.0, 0.0, 0.0, 0.0)
        rgba = to_rgba(ec)
        if self._alpha is not None:
            rgba = (rgba[0], rgba[1], rgba[2], self._alpha)
        return rgba

    def set_edgecolor(self, color):
        self._edgecolor = color

    # --- linewidth ---
    def get_linewidth(self):
        return self._linewidth

    def set_linewidth(self, w):
        self._linewidth = w

    def _resolved_facecolor_hex(self):
        fc = self._facecolor
        if isinstance(fc, str) and fc.lower() == 'none':
            return 'none'
        return to_hex(fc)

    def _resolved_edgecolor_hex(self):
        ec = self._edgecolor
        if isinstance(ec, str) and ec.lower() == 'none':
            return 'none'
        return to_hex(ec)


class Rectangle(Patch):
    """A rectangle defined by an anchor point, width, and height."""

    def __init__(self, xy, width, height, **kwargs):
        self._xy = tuple(xy)
        self._width = width
        self._height = height
        super().__init__(**kwargs)

    def get_x(self):
        return self._xy[0]

    def get_y(self):
        return self._xy[1]

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def get_xy(self):
        return self._xy

    def set_xy(self, xy):
        self._xy = tuple(xy)

    def set_width(self, w):
        self._width = w

    def set_height(self, h):
        self._height = h

    def get_corners(self):
        """Return the four corners as a list of (x, y) tuples.

        Order: bottom-left, bottom-right, top-right, top-left.
        """
        x0, y0 = self._xy
        x1, y1 = x0 + self._width, y0 + self._height
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        x0, y0 = self._xy
        x1 = x0 + self._width
        y1 = y0 + self._height
        px_left = layout.sx(x0)
        px_right = layout.sx(x1)
        px_top = layout.sy(y1)      # top of data = smaller pixel y
        px_bottom = layout.sy(y0)   # bottom of data = larger pixel y
        pw = px_right - px_left
        ph = px_bottom - px_top
        if pw <= 0 or ph <= 0:
            return
        renderer.draw_rect(px_left, px_top, pw, ph,
                           self._resolved_edgecolor_hex(),
                           self._resolved_facecolor_hex())


class Circle(Patch):
    """A circle defined by a center point and radius."""

    def __init__(self, center=(0.0, 0.0), radius=0.5, **kwargs):
        self._center = tuple(center)
        self._radius = radius
        super().__init__(**kwargs)

    def get_center(self):
        return self._center

    def set_center(self, center):
        self._center = tuple(center)

    def get_radius(self):
        return self._radius

    def set_radius(self, radius):
        self._radius = radius

    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        cx_px = layout.sx(self._center[0])
        cy_px = layout.sy(self._center[1])
        r_px = abs(layout.sx(self._center[0] + self._radius) - cx_px)
        if r_px <= 0:
            return
        renderer.draw_circle(cx_px, cy_px, r_px,
                             self._resolved_facecolor_hex())


class Polygon(Patch):
    """A polygon defined by a list of (x, y) vertices."""

    def __init__(self, xy, closed=True, **kwargs):
        self._xy = [tuple(pt) for pt in xy]
        self._closed = closed
        super().__init__(**kwargs)

    def get_xy(self):
        return list(self._xy)

    def set_xy(self, xy):
        self._xy = [tuple(pt) for pt in xy]

    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        if len(self._xy) < 3:
            return
        x_px = [layout.sx(pt[0]) for pt in self._xy]
        y_px = [layout.sy(pt[1]) for pt in self._xy]
        alpha = self.get_alpha() if self.get_alpha() is not None else 1.0
        points = list(zip(x_px, y_px))
        renderer.draw_polygon(points,
                              self._resolved_facecolor_hex(),
                              alpha)


class Wedge(Patch):
    """A wedge (pie slice) defined by center, radius, and two angles."""

    def __init__(self, center, r, theta1, theta2, **kwargs):
        self._center = tuple(center)
        self._r = r
        self._theta1 = theta1  # start angle in degrees
        self._theta2 = theta2  # end angle in degrees
        super().__init__(**kwargs)

    def get_center(self):
        return self._center

    def set_center(self, center):
        self._center = tuple(center)

    def get_r(self):
        return self._r

    def get_theta1(self):
        return self._theta1

    def get_theta2(self):
        return self._theta2

    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        cx_px = layout.sx(self._center[0])
        cy_px = layout.sy(self._center[1])
        edge_px = layout.sx(self._center[0] + self._r)
        r_px = abs(edge_px - cx_px)
        if r_px <= 0:
            return
        renderer.draw_wedge(cx_px, cy_px, r_px,
                            self._theta1, self._theta2,
                            self._resolved_facecolor_hex())
