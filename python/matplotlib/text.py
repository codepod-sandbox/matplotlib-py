"""matplotlib.text --- Text and Annotation artists."""

from matplotlib.artist import Artist
from matplotlib.patches import Patch


class Text(Artist):
    """An artist for rendering text."""

    zorder = 3

    def __init__(self, x=0, y=0, text='', **kwargs):
        super().__init__()
        self._x = x
        self._y = y
        self._text = str(text)

        # fontsize: accept 'fontsize' or 'size'
        self._fontsize = kwargs.get('fontsize', kwargs.get('size', 12.0))

        # fontweight: accept 'fontweight' or 'weight'
        self._fontweight = kwargs.get('fontweight', kwargs.get('weight', 'normal'))

        # horizontal alignment: accept 'ha' or 'horizontalalignment'
        self._ha = kwargs.get('ha', kwargs.get('horizontalalignment', 'left'))

        # vertical alignment: accept 'va' or 'verticalalignment'
        self._va = kwargs.get('va', kwargs.get('verticalalignment', 'baseline'))

        # rotation
        rotation = kwargs.get('rotation', None)
        self.set_rotation(rotation)

        # antialiased
        if 'antialiased' in kwargs:
            self._antialiased = kwargs['antialiased']
        else:
            import matplotlib
            self._antialiased = matplotlib.rcParams.get('text.antialiased', True)

    # --- text ---
    def get_text(self):
        return self._text

    def set_text(self, s):
        self._text = str(s)

    # --- fontsize ---
    def get_fontsize(self):
        return self._fontsize

    def set_fontsize(self, size):
        self._fontsize = size

    set_size = set_fontsize

    # --- fontweight ---
    def get_weight(self):
        return self._fontweight

    def set_weight(self, weight):
        self._fontweight = weight

    def get_fontweight(self):
        return self._fontweight

    def set_fontweight(self, weight):
        self._fontweight = weight

    # --- horizontal alignment ---
    def get_horizontalalignment(self):
        return self._ha

    def set_horizontalalignment(self, align):
        self._ha = align

    set_ha = set_horizontalalignment

    # --- vertical alignment ---
    def get_verticalalignment(self):
        return self._va

    def set_verticalalignment(self, align):
        self._va = align

    set_va = set_verticalalignment

    # --- rotation ---
    def get_rotation(self):
        """Return the text angle in degrees between 0 and 360."""
        return self._rotation

    def set_rotation(self, s):
        """Set the rotation of the text.

        Parameters
        ----------
        s : float or {'vertical', 'horizontal'} or None
            The rotation angle in degrees. 'horizontal' equals 0,
            'vertical' equals 90. None is treated as 0.
        """
        if isinstance(s, (int, float)):
            self._rotation = float(s) % 360
        elif s is None or (isinstance(s, str) and s == 'horizontal'):
            self._rotation = 0.
        elif isinstance(s, str) and s == 'vertical':
            self._rotation = 90.
        else:
            raise ValueError(
                "rotation must be 'vertical', 'horizontal' or "
                f"a number, not {s!r}")

    # --- antialiased ---
    def get_antialiased(self):
        return self._antialiased

    def set_antialiased(self, aa):
        self._antialiased = aa

    # --- position ---
    def get_position(self):
        return (self._x, self._y)

    def set_position(self, xy):
        self._x, self._y = xy

    # --- draw (new renderer architecture) ---
    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        px = layout.sx(self._x)
        py = layout.sy(self._y)
        renderer.draw_text(px, py, self._text, self._fontsize, '#000000',
                           self._ha)

    # --- angle-based alignment helpers ---
    def _ha_for_angle(self, angle):
        """Determine horizontal alignment for rotation_mode 'xtick'."""
        if (angle <= 10 or 85 <= angle <= 95 or 350 <= angle or
                170 <= angle <= 190 or 265 <= angle <= 275):
            return 'center'
        anchor_at_bottom = self.get_verticalalignment() == 'bottom'
        if 10 < angle < 85 or 190 < angle < 265:
            return 'left' if anchor_at_bottom else 'right'
        return 'right' if anchor_at_bottom else 'left'

    def _va_for_angle(self, angle):
        """Determine vertical alignment for rotation_mode 'ytick'."""
        if (angle <= 10 or 350 <= angle or 170 <= angle <= 190
                or 80 <= angle <= 100 or 260 <= angle <= 280):
            return 'center'
        anchor_at_left = self.get_horizontalalignment() == 'left'
        if 190 < angle < 260 or 10 < angle < 80:
            return 'baseline' if anchor_at_left else 'top'
        return 'top' if anchor_at_left else 'baseline'


class Annotation(Text):
    """A Text with an optional arrow pointing to a data coordinate."""

    def __init__(self, text, xy, xytext=None, arrowprops=None, **kwargs):
        # xy is the point being annotated
        self.xy = tuple(xy)
        # xytext is where the text is placed; defaults to xy
        self.xytext = tuple(xytext) if xytext is not None else self.xy

        # Initialise Text at the xytext position
        super().__init__(x=self.xytext[0], y=self.xytext[1], text=text,
                         **kwargs)

        # arrow_patch: None when no arrowprops, otherwise a Patch placeholder
        if arrowprops is not None:
            self.arrow_patch = Patch()
        else:
            self.arrow_patch = None
